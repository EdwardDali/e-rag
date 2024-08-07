import subprocess
from openai import OpenAI
from src.settings import settings
import requests
from src.look_and_feel import error, success, warning, info
import os
from dotenv import load_dotenv
from groq.types import Model, ModelDeleted, ModelListResponse
from groq import Groq
from dotenv import load_dotenv
import vertexai
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

class EragAPI:
    def __init__(self, api_type, model=None):
        self.api_type = api_type
        self.model = model

        if api_type == "ollama":
            self.client = OpenAI(base_url='http://localhost:11434/v1', api_key='ollama')
            self.model = model or settings.ollama_model
        elif api_type == "llama":
            self.client = LlamaClient()
            self.model = model or settings.llama_model
        elif api_type == "groq":
            self.client = GroqClient(model)
            self.model = self.client.model
        elif api_type == "gemini":
            self.client = GeminiClient(model)
            self.model = self.client.model
        else:
            raise ValueError(error("Invalid API type"))

    def chat(self, messages, temperature=0.7, max_tokens=None, stream=False):
        try:
            if self.api_type == "llama":
                response = self.client.chat(messages, temperature=temperature, max_tokens=max_tokens)
            elif self.api_type == "groq":
                response = self.client.chat(messages, temperature=temperature, max_tokens=max_tokens, stream=stream)
            elif self.api_type == "gemini":
                response = self.client.chat(messages, temperature=temperature, max_tokens=max_tokens, stream=stream)
            else:  # ollama
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=stream
                )
                if not stream:
                    response = response.choices[0].message.content
            return response
        except Exception as e:
            return error(f"An error occurred: {str(e)}")

    def complete(self, prompt, temperature=0.7, max_tokens=None, stream=False):
        try:
            if self.api_type == "llama":
                response = self.client.complete(prompt, temperature=temperature, max_tokens=max_tokens)
            elif self.api_type == "groq":
                response = self.client.complete(prompt, temperature=temperature, max_tokens=max_tokens, stream=stream)
            elif self.api_type == "gemini":
                response = self.client.complete(prompt, temperature=temperature, max_tokens=max_tokens, stream=stream)
            else:  # ollama
                response = self.client.completions.create(
                    model=self.model,
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=stream
                )
                if not stream:
                    response = response.choices[0].text
            return response
        except Exception as e:
            return error(f"An error occurred: {str(e)}")

    

def update_settings(settings, api_type, model):
        if api_type == "ollama":
            settings.update_setting("ollama_model", model)
        elif api_type == "llama":
            settings.update_setting("llama_model", model)
        elif api_type == "groq":
            settings.update_setting("groq_model", model)
        elif api_type == "gemini":
            settings.update_setting("gemini_model", model)
        else:
            print(error(f"Unknown API type: {api_type}"))
            return

        settings.apply_settings()
        print(success(f"Settings updated. Using {model} with {api_type} backend."))

class LlamaClient:
    def __init__(self, base_url='http://localhost:8080/v1'):
        self.base_url = base_url

    def chat(self, messages, temperature=0.7, max_tokens=None):
        url = f"{self.base_url}/chat/completions"
        data = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        response = requests.post(url, json=data)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            raise Exception(error(f"Error from llama.cpp server: {response.status_code} - {response.text}"))

    def complete(self, prompt, temperature=0.7, max_tokens=None):
        url = f"{self.base_url}/completions"
        data = {
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        response = requests.post(url, json=data)
        if response.status_code == 200:
            return response.json()['choices'][0]['text']
        else:
            raise Exception(error(f"Error from llama.cpp server: {response.status_code} - {response.text}"))

    def get_models(self):
        url = f"{self.base_url}/models"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                models = response.json()['data']
                return [model['id'] for model in models]
            else:
                raise Exception(error(f"Error fetching models: {response.status_code} - {response.text}"))
        except requests.RequestException as e:
            raise Exception(error(f"Error connecting to llama.cpp server: {e}"))

class GroqClient:
    def __init__(self, model=None):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError(error("GROQ_API_KEY not found in .env file"))
        self.client = Groq()
        self.model = model or self.get_default_model()

    def get_default_model(self):
        try:
            models = self.client.models.list()
            return models.data[0].id if models.data else None
        except Exception:
            return None

    def chat(self, messages, temperature=0.7, max_tokens=None, stream=False):
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )
            
            if stream:
                return completion  # Return the stream object
            else:
                return completion.choices[0].message.content
        except Exception as e:
            raise Exception(error(f"Error from Groq API: {str(e)}"))

    def complete(self, prompt, temperature=0.7, max_tokens=None, stream=False):
        try:
            completion = self.client.completions.create(
                model=self.model,
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )
            
            if stream:
                return completion  # Return the stream object
            else:
                return completion.choices[0].text
        except Exception as e:
            raise Exception(error(f"Error from Groq API: {str(e)}"))

    def stream_chat(self, messages, temperature=1, max_tokens=1024):
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            for chunk in completion:
                yield chunk.choices[0].delta.content or ""
        except Exception as e:
            raise Exception(error(f"Error streaming from Groq API: {str(e)}"))

class GeminiClient:
    def __init__(self, model=None):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(error("GEMINI_API_KEY not found in .env file"))
        genai.configure(api_key=self.api_key)
        self.model = model or self.get_default_model()

    def get_default_model(self):
        try:
            models = genai.list_models()
            return next((model.name for model in models if 'generateContent' in model.supported_generation_methods), None)
        except Exception:
            return None

    def chat(self, messages, temperature=0.7, max_tokens=None, stream=False):
        try:
            model = genai.GenerativeModel(self.model)
            chat = model.start_chat(history=[])
            
            for message in messages:
                if message['role'] == 'user':
                    response = chat.send_message(message['content'], generation_config=genai.types.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                    ))
                    
                    if stream:
                        return self._stream_response(response)
                    else:
                        return response.text
            
            return error("No user message found in the conversation.")
        except Exception as e:
            raise Exception(error(f"Error from Gemini API: {str(e)}"))

    def complete(self, prompt, temperature=0.7, max_tokens=None, stream=False):
        try:
            model = genai.GenerativeModel(self.model)
            response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ))
            
            if stream:
                return self._stream_response(response)
            else:
                return response.text
        except Exception as e:
            raise Exception(error(f"Error from Gemini API: {str(e)}"))

    def _stream_response(self, response):
        for chunk in response:
            yield chunk.text

def get_available_models(api_type, server_manager=None):
    if api_type == "ollama":
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
            models = result.stdout.strip().split('\n')[1:]  # Skip the header
            return [model.split()[0] for model in models if model.split()[0] not in ['failed', 'NAME']]
        except subprocess.CalledProcessError:
            print(error("Error running 'ollama list' command"))
            return []
    elif api_type == "llama":
        if server_manager:
            return server_manager.get_gguf_models()
        else:
            print(error("Server manager not provided for llama models"))
            return []
    elif api_type == "groq":
        try:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                print(error("GROQ_API_KEY not found in .env file"))
                return []
            
            client = Groq(api_key=api_key)
            models: ModelListResponse = client.models.list()
            
            return [model.id for model in models.data if isinstance(model, Model)]
        except Exception as e:
            print(error(f"Error fetching models from Groq API: {str(e)}"))
            return []
    elif api_type == "gemini":
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                print(error("GEMINI_API_KEY not found in .env file"))
                return []
            
            genai.configure(api_key=api_key)
            models = genai.list_models()
            
            return [model.name for model in models if 'generateContent' in model.supported_generation_methods]
        except Exception as e:
            print(error(f"Error fetching models from Gemini API: {str(e)}"))
            return []
    else:
        return []

# Factory function to create EragAPI instance
def create_erag_api(api_type, model=None):
    if model is None:
        model = settings.get_default_model(api_type)
    return EragAPI(api_type, model)
