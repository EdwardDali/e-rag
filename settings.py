import json
import os
from typing import Dict, Any

class Settings:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # Upload Settings
        self.file_chunk_size: int = 500
        self.file_overlap_size: int = 200

        # Embeddings Settings
        self.batch_size = 32
        self.embeddings_file_path = "db_embeddings.pt"
        self.db_file_path = "db.txt"

        # Graph Settings
        self.graph_chunk_size: int = 5000
        self.graph_overlap_size: int = 200
        self.nlp_model = "en_core_web_sm"
        self.similarity_threshold = 0.7
        self.min_entity_occurrence = 1
        self.enable_semantic_edges = True
        self.knowledge_graph_file_path = "knowledge_graph.json"
        self.embeddings_file_path = "db_embeddings.pt"

        # Model Settings
        self.max_history_length = 5
        self.conversation_context_size = 3
        self.update_threshold = 10
        self.ollama_model = "phi3:instruct"
        self.temperature = 0.1
        self.model_name = "all-MiniLM-L6-v2"

        # Knol Creation Settings
        self.num_questions = 8

        # Web Sum Settings
        self.web_sum_urls_to_crawl = 5
        self.summary_size = 5000
        self.final_summary_size = 10000

        # Web RAG Settings
        self.web_rag_urls_to_crawl = 5
        self.initial_context_size = 5
        self.web_rag_file = "web_rag_qa.txt"
        self.web_rag_chunk_size = 500
        self.web_rag_overlap_size = 100

        # Search Settings
        self.top_k = 5
        self.entity_relevance_threshold = 0.5
        self.lexical_weight = 1.0
        self.semantic_weight = 1.0
        self.graph_weight = 1.0
        self.text_weight = 1.0
        self.enable_lexical_search = True
        self.enable_semantic_search = True
        self.enable_graph_search = True
        self.enable_text_search = True

        # File Settings
        self.knowledge_graph_file_path = "knowledge_graph.json"
        self.results_file_path = "results.txt"

        # Other Settings (if any)
        self.nlp_model = "en_core_web_sm"
        self.similarity_threshold = 0.7
        self.enable_family_extraction = True
        self.min_entity_occurrence = 1
        self.enable_semantic_edges = True

        self.config_file = "config.json"

    def load_settings(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                saved_settings = json.load(f)
            for key, value in saved_settings.items():
                if hasattr(self, key):
                    setattr(self, key, value)
        else:
            self.save_settings()  # Create default config file if it doesn't exist

    def save_settings(self):
        settings_dict = {key: value for key, value in self.__dict__.items() if not key.startswith('_')}
        with open(self.config_file, 'w') as f:
            json.dump(settings_dict, f, indent=4)

    def apply_settings(self):
        # This method remains unchanged as it applies settings to various components
        # You may need to update this method if you've changed how settings are applied in your application
        pass

    def get_all_settings(self) -> Dict[str, Any]:
        return {key: value for key, value in self.__dict__.items() if not key.startswith('_')}

    def update_setting(self, key: str, value: Any):
        if hasattr(self, key):
            setattr(self, key, value)
            self.save_settings()
        else:
            raise AttributeError(f"Setting '{key}' does not exist")

    def reset_to_defaults(self):
        self._initialize()
        self.save_settings()

# Singleton instance
settings = Settings()
