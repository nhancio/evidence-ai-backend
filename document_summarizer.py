import os
import tempfile
import PyPDF2
import docx2txt
import google.generativeai as genai

class DocumentSummarizer:
    def __init__(self):
        self.model = None
        
    def set_google_api_key(self, api_key: str):
        """Set Google API key for Gemini"""
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        except Exception as e:
            print(f"Error setting up Gemini: {e}")
            self.model = None
    
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
        """Summarize a document using Gemini"""
        try:
            # Extract text from document
            text_content = self.extract_text_from_file(file_path)
            
            if not text_content or text_content.startswith("Error"):
                return text_content
            
            # Truncate text if too long (Gemini has token limits)
            if len(text_content) > 10000:
                text_content = text_content[:10000] + "..."
            
            # Create prompt
            prompt = f"""Please provide a comprehensive summary of the following document:

{text_content}

Please provide a clear, well-structured summary that covers the main points, key concepts, and important details from the document."""

            # Generate summary using Gemini
            if self.model:
                try:
                    response = self.model.generate_content(prompt)
                    return response.text
                except Exception as e:
                    return f"Error generating summary with Gemini: {str(e)}"
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
