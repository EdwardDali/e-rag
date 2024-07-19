# -*- coding: utf-8 -*-

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from src.api_model import EragAPI
from src.settings import settings
from src.look_and_feel import error, success, warning, info, highlight
from src.print_pdf import PDFReportGenerator

# Define RGB values for custom colors
SAGE_GREEN_RGB = (125/255, 169/255, 133/255)
DUSTY_PINK_RGB = (173/255, 142/255, 148/255)

class ExploratoryDataAnalysis:
    def __init__(self, erag_api, db_path):
        self.erag_api = erag_api
        self.db_path = db_path
        self.technique_counter = 0
        self.total_techniques = 5
        self.output_folder = os.path.join(settings.output_folder, "xda_output")
        os.makedirs(self.output_folder, exist_ok=True)
        self.text_output = ""
        self.pdf_content = []
        self.findings = []
        self.llm_name = self.erag_api.model
        self.toc_entries = []
        self.executive_summary = ""
        self.image_paths = []

    def run(self):
        print(info(f"Starting Exploratory Data Analysis on {self.db_path}"))
        tables = self.get_tables()
        for table in tables:
            self.analyze_table(table)
        
        print(info("Generating Executive Summary..."))
        self.generate_executive_summary()
        
        self.save_text_output()
        self.generate_pdf_report()
        print(success(f"Exploratory Data Analysis completed. Results saved in {self.output_folder}"))

    def get_tables(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            return [table[0] for table in cursor.fetchall()]

    def analyze_table(self, table_name):
        print(highlight(f"\nAnalyzing table: {table_name}"))
        self.text_output += f"\nAnalyzing table: {table_name}\n"
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)

        self.basic_statistics(df, table_name)
        self.data_types_and_missing_values(df, table_name)
        self.numerical_features_distribution(df, table_name)
        self.correlation_analysis(df, table_name)
        self.categorical_features_analysis(df, table_name)

    def basic_statistics(self, df, table_name):
        self.technique_counter += 1
        print(info(f"Performing test {self.technique_counter}/{self.total_techniques} - Basic Statistics"))
        stats = df.describe()
        self.interpret_results(f"{self.technique_counter}. Basic Statistics", stats, table_name)

    def data_types_and_missing_values(self, df, table_name):
        self.technique_counter += 1
        print(info(f"Performing test {self.technique_counter}/{self.total_techniques} - Data Types and Missing Values"))
        data_types = df.dtypes.to_frame(name='Data Type')
        missing_values = df.isnull().sum().to_frame(name='Missing Values')
        missing_percentage = (df.isnull().sum() / len(df) * 100).to_frame(name='Missing Percentage')
        results = pd.concat([data_types, missing_values, missing_percentage], axis=1)
        self.interpret_results(f"{self.technique_counter}. Data Types and Missing Values", results, table_name)

    def numerical_features_distribution(self, df, table_name):
        self.technique_counter += 1
        print(info(f"Performing test {self.technique_counter}/{self.total_techniques} - Numerical Features Distribution"))
        numerical_columns = df.select_dtypes(include=['float64', 'int64']).columns
        if len(numerical_columns) > 0:
            results = []
            for col in numerical_columns:
                plt.figure(figsize=(10, 6))
                
                # Plot histogram for all data
                sns.histplot(df[col], kde=True, color=SAGE_GREEN_RGB)
                
                # Get top 10 most frequent values for text labels
                top_10_values = df[col].value_counts().nlargest(10)
                
                # Add text labels only for top 10 values
                for value, count in top_10_values.items():
                    plt.text(value, count, f'{count}', ha='center', va='bottom')
                
                plt.title(f'Distribution of {col}')
                plt.xlabel(col)
                plt.ylabel('Count')
                plt.xticks(rotation=45, ha='right')
                img_path = os.path.join(self.output_folder, f"{table_name}_{col}_distribution.png")
                plt.savefig(img_path, dpi=300, bbox_inches='tight')
                plt.close()
                results.append((f"Distribution stats for {col}:\n{df[col].describe().to_string()}", img_path))
        else:
            results = "N/A - No numerical features found"
        self.interpret_results(f"{self.technique_counter}. Numerical Features Distribution", results, table_name)


    def correlation_analysis(self, df, table_name):
        self.technique_counter += 1
        print(info(f"Performing test {self.technique_counter}/{self.total_techniques} - Correlation Analysis"))
        numerical_columns = df.select_dtypes(include=['float64', 'int64']).columns
        if len(numerical_columns) > 1:
            correlation_matrix = df[numerical_columns].corr()
            plt.figure(figsize=(12, 10))
            sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1, center=0)
            plt.title('Correlation Matrix Heatmap')
            img_path = os.path.join(self.output_folder, f"{table_name}_correlation_matrix.png")
            plt.savefig(img_path, dpi=300, bbox_inches='tight')
            plt.close()
            results = (correlation_matrix, img_path)
        else:
            results = "N/A - Not enough numerical features for correlation analysis"
        self.interpret_results(f"{self.technique_counter}. Correlation Analysis", results, table_name)

    def categorical_features_analysis(self, df, table_name):
        self.technique_counter += 1
        print(info(f"Performing test {self.technique_counter}/{self.total_techniques} - Categorical Features Analysis"))
        categorical_columns = df.select_dtypes(include=['object']).columns
        if len(categorical_columns) > 0:
            results = []
            for col in categorical_columns:
                plt.figure(figsize=(10, 6))
                value_counts = df[col].value_counts()
                
                # Plot bar chart for all data
                sns.barplot(x=value_counts.index, y=value_counts.values, color=DUSTY_PINK_RGB)
                
                # Add text labels only for top 10 values
                for i, (value, count) in enumerate(value_counts.nlargest(10).items()):
                    plt.text(i, count, f'{count}', ha='center', va='bottom')
                
                plt.title(f'Distribution of {col}')
                plt.xlabel(col)
                plt.ylabel('Count')
                plt.xticks(rotation=45, ha='right')
                img_path = os.path.join(self.output_folder, f"{table_name}_{col}_distribution.png")
                plt.savefig(img_path, dpi=300, bbox_inches='tight')
                plt.close()
                results.append((f"Value counts for {col} (Top 10):\n{value_counts.nlargest(10).to_string()}", img_path))
        else:
            results = "N/A - No categorical features found"
        self.interpret_results(f"{self.technique_counter}. Categorical Features Analysis", results, table_name)


    def interpret_results(self, analysis_type, results, table_name):
        if isinstance(results, pd.DataFrame):
            results_str = f"DataFrame with shape {results.shape}:\n{results.to_string()}"
        elif isinstance(results, tuple) and isinstance(results[0], pd.DataFrame):
            results_str = f"DataFrame with shape {results[0].shape}:\n{results[0].to_string()}\nImage path: {results[1]}"
        elif isinstance(results, list):
            results_str = "\n".join([str(item) for item in results])
        else:
            results_str = str(results)

        prompt = f"""
        Analysis type: {analysis_type}
        Table name: {table_name}
        Results:
        {results_str}

        Please provide a detailed interpretation of these results, highlighting any noteworthy patterns, anomalies, or insights. Focus on the most important aspects that would be valuable for data analysis.

        Structure your response in Markdown format, following this example structure:

        ```markdown
        # {analysis_type}

        ## Analysis
        [Provide a detailed description of the analysis performed]

        ### Important: [Any crucial point about the analysis]
        [Details about the important point]

        ## Positive Findings
        - [Positive finding 1]
        - [Positive finding 2]
        - [N/A if no positive findings]

        ## Negative Findings
        - [Negative finding 1]
        - [Negative finding 2]
        - [N/A if no negative findings]

        ## Conclusion
        [Summarize the key takeaways and implications of this analysis]
        ```

        If there are no significant findings, state "No significant findings" in the appropriate sections and briefly explain why.

        Interpretation:
        """
        interpretation = self.erag_api.chat([{"role": "system", "content": "You are a data analyst providing insights on exploratory data analysis results. Respond in Markdown format."}, 
                                             {"role": "user", "content": prompt}])
        
        # Updated second LLM call to focus on direct improvements
        check_prompt = f"""
        Please review and improve the following interpretation:

        {interpretation}

        Enhance the text by:
        1. Ensuring the Markdown formatting is correct.
        2. Making the interpretation more narrative and detailed by adding context and explanations.
        3. Addressing any important aspects of the data that weren't covered.

        Provide your response in the same Markdown format, maintaining the original structure. 
        Do not add comments, questions, or explanations about the changes - simply provide the improved version.
        """

        enhanced_interpretation = self.erag_api.chat([
            {"role": "system", "content": "You are a data analyst improving interpretations of exploratory data analysis results. Provide direct enhancements without adding meta-comments."},
            {"role": "user", "content": check_prompt}
        ])

        print(success(f"AI Interpretation for {analysis_type}:"))
        print(enhanced_interpretation.strip())
        
        self.text_output += f"\n{enhanced_interpretation.strip()}\n\n"
        
        self.pdf_content.append((analysis_type, results, enhanced_interpretation.strip()))
        
        for line in enhanced_interpretation.strip().split('\n'):
            if "### Important:" in line:
                self.findings.append(f"{analysis_type}: {line}")

        # Add image paths to the list
        if isinstance(results, tuple) and len(results) == 2 and isinstance(results[1], str) and results[1].endswith('.png'):
            self.image_paths.append(results[1])
        elif isinstance(results, list):
            for item in results:
                if isinstance(item, tuple) and len(item) == 2 and isinstance(item[1], str) and item[1].endswith('.png'):
                    self.image_paths.append(item[1])

    def generate_executive_summary(self):
        if not self.findings:
            self.executive_summary = "No significant findings were identified during the analysis. This could be due to a lack of data, uniform data distribution, or absence of notable patterns or anomalies in the dataset."
            return

        summary_prompt = f"""
        Based on the following findings from the Exploratory Data Analysis:
        
        {self.findings}
        
        Please provide an executive summary of the analysis. The summary should:
        1. Briefly introduce the purpose of the analysis.
        2. Highlight the most significant insights and patterns discovered.
        3. Mention any potential issues or areas that require further investigation.
        4. Conclude with recommendations for next steps or areas to focus on.

        Structure the summary in multiple paragraphs for readability.
        Please format your response in Markdown, using appropriate headers, bullet points, and emphasis where necessary.
        """
        
        try:
            interpretation = self.erag_api.chat([
                {"role": "system", "content": "You are a data analyst providing an executive summary of an exploratory data analysis. Respond in Markdown format."},
                {"role": "user", "content": summary_prompt}
            ])
            
            if interpretation is not None:
                # Updated second LLM call to focus on direct improvements
                check_prompt = f"""
                Please review and improve the following executive summary:

                {interpretation}

                Enhance the summary by:
                1. Ensuring the Markdown formatting is correct.
                2. Making it more comprehensive and narrative by adding context and explanations.
                3. Addressing any important aspects of the analysis that weren't covered.
                4. Ensuring it includes a clear introduction, highlights of significant insights, mention of potential issues, and recommendations for next steps.

                Provide your response in the same Markdown format, maintaining the original structure.
                Do not add comments, questions, or explanations about the changes - simply provide the improved version.
                """

                enhanced_summary = self.erag_api.chat([
                    {"role": "system", "content": "You are a data analyst improving an executive summary of an exploratory data analysis. Provide direct enhancements without adding meta-comments."},
                    {"role": "user", "content": check_prompt}
                ])

                self.executive_summary = enhanced_summary.strip()
            else:
                self.executive_summary = "Error: Unable to generate executive summary."
        except Exception as e:
            print(error(f"An error occurred while generating the executive summary: {str(e)}"))
            self.executive_summary = "Error: Unable to generate executive summary due to an exception."


        print(success("Enhanced Executive Summary generated successfully."))
        print(self.executive_summary)

    def save_text_output(self):
        output_file = os.path.join(self.output_folder, "xda_results.txt")
        with open(output_file, "w", encoding='utf-8') as f:
            f.write(self.text_output)

    def generate_pdf_report(self):
        pdf_generator = PDFReportGenerator(self.output_folder, self.llm_name)
        pdf_file = pdf_generator.create_enhanced_pdf_report(
            self.executive_summary,
            self.findings,
            self.pdf_content,
            self.image_paths
        )
        if pdf_file:
            print(success(f"PDF report generated successfully: {pdf_file}"))
        else:
            print(error("Failed to generate PDF report"))