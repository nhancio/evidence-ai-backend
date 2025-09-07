from flask import Flask, request, jsonify
from flask_cors import CORS
import PyPDF2
import docx2txt
import tempfile
import os
import google.generativeai as genai

app = Flask(__name__)

# CORS configuration - Allow all origins for now
CORS(app, origins=["*"])

# Global variables
MODEL = None

# Load model when app starts
load_model()

def load_model():
    """Load the Gemini model"""
    global MODEL
    try:
        api_key = os.environ.get('GOOGLE_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
            MODEL = genai.GenerativeModel('gemini-pro')
            print("✅ Gemini model loaded successfully")
        else:
            print("⚠️ No Google API key found, summarization will use fallback")
    except Exception as e:
        print(f"❌ Error loading model: {e}")

def extract_text_from_file(file_path):
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

def simple_sentiment_analysis(text):
    """Simple sentiment analysis using keyword matching"""
    positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love', 'happy', 'pleased', 'satisfied']
    negative_words = ['bad', 'terrible', 'awful', 'horrible', 'hate', 'angry', 'disappointed', 'frustrated', 'sad', 'upset']
    
    text_lower = text.lower()
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    if positive_count > negative_count:
        return "Positive", 75
    elif negative_count > positive_count:
        return "Negative", 75
    else:
        return "Neutral", 50

def summarize_with_gemini(text):
    """Summarize text using Gemini"""
    if not MODEL:
        return "Summarization requires Google API key. Please set GOOGLE_API_KEY environment variable."
    
    try:
        prompt = f"Please provide a comprehensive summary of the following text:\n\n{text[:5000]}"
        response = MODEL.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating summary: {str(e)}"

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        "message": "Verdict AI Backend is running",
        "status": "ok"
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        return jsonify({
            "status": "healthy",
            "message": "Verdict AI Backend is running",
            "model_loaded": MODEL is not None
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/analyze_sms', methods=['POST'])
def analyze_sms():
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({"error": "No text provided"}), 400
        
        # Simple sentiment analysis
        sentiment, confidence = simple_sentiment_analysis(text)
        
        return jsonify({
            "Predicted_Sentiment": sentiment,
            "cd": confidence,
            "emotions": [
                {"emotion": sentiment, "prob": confidence}
            ]
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze_document', methods=['POST'])
def analyze_document():
    try:
        file = request.files['file']
        
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as tmp_file:
            file.save(tmp_file.name)
            
            # Extract text
            text = extract_text_from_file(tmp_file.name)
            
            # Clean up
            os.unlink(tmp_file.name)
            
            if text.startswith("Error"):
                return jsonify({"error": text}), 400
            
            # Simple sentiment analysis
            sentiment, confidence = simple_sentiment_analysis(text)
            
            return jsonify({
                "Predicted_Sentiment": sentiment,
                "cd": confidence,
                "emotions": [
                    {"emotion": sentiment, "prob": confidence}
                ]
            })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/summarize_document', methods=['POST'])
def summarize_document():
    try:
        file = request.files['file']
        
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as tmp_file:
            file.save(tmp_file.name)
            
            # Extract text
            text = extract_text_from_file(tmp_file.name)
            
            # Clean up
            os.unlink(tmp_file.name)
            
            if text.startswith("Error"):
                return jsonify({"error": text}), 400
            
            # Summarize
            summary = summarize_with_gemini(text)
            
            return jsonify({
                "summary": summary,
                "status": "success"
            })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    load_model()
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
