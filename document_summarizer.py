import os
import tempfile
from typing import List
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain.chat_models import init_chat_model
import faiss
from langchain_community.docstore.in_memory import InMemoryDocstore

class DocumentSummarizer:
    def __init__(self):
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2"
        )
        
        # Initialize LLM (will be set when API key is available)
        self.llm = None
        
    def set_google_api_key(self, api_key: str):
        """Set Google API key for Gemini"""
        os.environ["GOOGLE_API_KEY"] = api_key
        self.llm = init_chat_model("gemini-2.5-flash", model_provider="google_genai")
    
    def create_vector_store(self, documents: List[Document]):
        """Create FAISS vector store from documents"""
        # Split documents into chunks
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=200
        )
        splits = splitter.split_documents(documents)
        
        # Create FAISS index
        embedding_dim = len(self.embeddings.embed_query("hello world"))
        index = faiss.IndexFlatL2(embedding_dim)
        
        vector_store = FAISS(
            embedding_function=self.embeddings,
            index=index,
            docstore=InMemoryDocstore(),
            index_to_docstore_id={},
        )
        
        vector_store.add_documents(splits)
        return vector_store, splits
    
    def summarize_document(self, file_path: str, question: str = "Summarize this document") -> str:
        """Summarize a document using RAG"""
        try:
            # Load document
            if file_path.endswith('.pdf'):
                loader = PyPDFLoader(file_path)
                documents = loader.load()
            else:
                # For other file types, create a simple document
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                documents = [Document(page_content=content)]
            
            if not documents:
                return "Error: Could not load document content."
            
            # Create vector store
            vector_store, splits = self.create_vector_store(documents)
            
            # Retrieve relevant chunks
            retrieved_docs = vector_store.similarity_search(question, k=5)
            
            # Combine context
            context = "\n\n".join(doc.page_content for doc in retrieved_docs)
            
            # Create prompt
            prompt = f"""Based on the following document content, please provide a comprehensive summary:

Document Content:
{context}

Please provide a clear, well-structured summary that covers the main points, key concepts, and important details from the document."""

            # Generate summary
            if self.llm:
                response = self.llm.invoke(prompt)
                return response.content
            else:
                # Fallback to simple summarization if no LLM
                return self._simple_summarize(context)
                
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
