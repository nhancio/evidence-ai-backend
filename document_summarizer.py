import os
import tempfile
import PyPDF2
import docx2txt
import requests

class DocumentSummarizer:
    def __init__(self):
        self.api_key = None
        
    def set_google_api_key(self, api_key: str):
        """Set Hugging Face API key"""
        self.api_key = api_key
    
    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text from various file types"""
        try:
            if file_path.endswith('.pdf'):
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                    return text
            elif file_path.endswith('.docx'):
                return docx2txt.process(file_path)
            elif file_path.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as file:
                    return file.read()
            else:
                return "Unsupported file type"
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    def summarize_document(self, file_path: str, question: str = "Summarize this document") -> str:
        """Summarize a document using Hugging Face LLM with proper system prompt"""
        try:
            # Extract text from document
            text_content = self.extract_text_from_file(file_path)
            
            if not text_content or text_content.startswith("Error"):
                return text_content
            
            # Truncate text if too long (handle ~8000 characters for better context)
            if len(text_content) > 8000:
                text_content = text_content[:8000]
            
            # Generate summary using Hugging Face BART - raw API
            if self.api_key:
                try:
                    # Using BART Large CNN - optimized for summarization
                    API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                    
                    # Raw BART API - just pass the document content
                    payload = {
                        "inputs": text_content,
                        "parameters": {
                            "max_length": 250,
                            "min_length": 80,
                            "do_sample": False
                        }
                    }
                    
                    response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # BART returns [{'summary_text': '...'}]
                        if isinstance(result, list) and len(result) > 0:
                            summary = result[0].get('summary_text', '')
                            if summary:
                                return summary.strip()
                        
                        # Fallback for dict response
                        if isinstance(result, dict):
                            summary = result.get('summary_text', '')
                            if summary:
                                return summary.strip()
                        
                        return "Could not extract summary from response"
                    else:
                        error_msg = response.text
                        # Check if model is loading
                        if 'loading' in error_msg.lower() or 'estimated_time' in error_msg.lower():
                            return "⏳ Model is loading (first-time use). Please try again in 20-30 seconds."
                        return f"Error from Hugging Face: {response.status_code} - {error_msg}"
                        
                except Exception as e:
                    return f"Error generating summary: {str(e)}"
            else:
                # Fallback to simple summarization
                return self._simple_summarize(text_content)
                
        except Exception as e:
            return f"Error summarizing document: {str(e)}"
    
    def _simple_summarize(self, text: str) -> str:
        """Simple fallback summarization"""
        sentences = text.split('. ')
        if len(sentences) <= 3:
            return text
        
        # Take first few sentences as summary
        summary_sentences = sentences[:3]
        return '. '.join(summary_sentences) + '...'

# Global instance
summarizer = DocumentSummarizer()
