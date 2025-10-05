import os
import tempfile
import PyPDF2
import docx2txt
import requests

class DocumentSummarizer:
    def __init__(self):
        self.api_key = None
        
    def set_google_api_key(self, api_key: str):
        """Set OpenAI API key"""
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
        """Summarize a document using OpenAI"""
        try:
            # Extract text from document
            text_content = self.extract_text_from_file(file_path)
            
            if not text_content or text_content.startswith("Error"):
                return text_content
            
            # Truncate text if too long (GPT-3.5 has 16k context)
            if len(text_content) > 12000:
                text_content = text_content[:12000] + "..."
            
            # Create prompt
            prompt = f"""Please provide a comprehensive summary of the following document:

{text_content}

Please provide a clear, well-structured summary that covers the main points, key concepts, and important details from the document."""

            # Generate summary using OpenAI
            if self.api_key:
                try:
                    response = requests.post(
                        url="https://api.openai.com/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "gpt-3.5-turbo",
                            "messages": [
                                {
                                    "role": "system",
                                    "content": "You are a helpful assistant that provides clear, concise, and well-structured document summaries."
                                },
                                {
                                    "role": "user",
                                    "content": prompt
                                }
                            ],
                            "temperature": 0.7,
                            "max_tokens": 1000
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        return result['choices'][0]['message']['content']
                    else:
                        return f"Error from OpenAI: {response.status_code} - {response.text}"
                        
                except Exception as e:
                    return f"Error generating summary with OpenAI: {str(e)}"
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
