from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from pathlib import Path
from io import BytesIO
# import docx
import PyPDF2
import docx2txt
from werkzeug.datastructures import FileStorage
import os
import tempfile
from document_summarizer import summarizer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

port = int(os.environ.get("PORT", 8000))




MODEL_NAME = "sangkm/go-emotions-fine-tuned-distilroberta"

def load_model():
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
        return tokenizer, model

tokenizer, model = load_model()

def extract_text_from_file(file: FileStorage) -> str:
    ext = file.filename.lower()
    if ext.endswith(".txt"):
        return file.read().decode('utf-8')
    elif ext.endswith(".docx"):
        return docx2txt.process(file)
    elif ext.endswith(".pdf"):
        text = []
        # Create a BytesIO object from the file content
        file_content = file.read()
        file.seek(0)  # Reset file pointer for future reads
        with BytesIO(file_content) as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text.append(page.extract_text() or "")
        return "\n".join(text)
    else:
        return " "



app = Flask(__name__)
# CORS configuration for production and development
allowed_origins = [
    "https://evidence-ai-frontend.vercel.app",  # Your actual Vercel URL
    "http://localhost:3000",
    "http://localhost:3001", 
    "http://localhost:3002"
]

CORS(app, origins=allowed_origins)

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        "message": "EvidenceAI Backend is running",
        "status": "ok"
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        return jsonify({
            "status": "healthy",
            "model": MODEL_NAME,
            "message": "EvidenceAI Backend is running",
            "timestamp": str(pd.Timestamp.now())
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/analyze_sms', methods=['POST'])
def analyze_sms():
    data = request.get_json()
    text = data.get('text', '')

    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    outputs = model(**inputs)

    probs = torch.softmax(outputs.logits, dim=1).flatten().tolist()
    probs = [round(i * 100, 2) for i in probs]
    emo_long = ["Admiration", "Amusement", "Anger", "Annoyance", "Approval", "Caring", "Confusion", "Curiosity",
                "Desire", "Disappointment", "Disapproval", "Disgust", "Embarrassment", "Excitement", "Fear",
                "Gratitude", "Grief", "Joy", "Love", "Nervousness", "Optimism", "Pride", "Realization", "Relief",
                "Remorse", "Sadness", "Surprise", "Neutral"]
    emo_dict_long = dict(zip(emo_long, probs))
    emo = pd.DataFrame(emo_dict_long, index=['Emotions']).T

    emo = emo.reset_index()
    emo.columns = ["Emotion", "Percentage"]

    emo_sorted = emo.sort_values(by='Percentage', ascending=False)
    emo_sorted = emo_sorted[emo_sorted['Percentage'] > 1]
    # print(emo_sorted)

    sentiment_score = emo.loc[emo['Percentage'].idxmax()]['Percentage']
    sentiment_label = emo.loc[emo['Percentage'].idxmax()]['Emotion']

    emotions = [
        {"emotion": row.Emotion, "prob": row.Percentage}
        for _, row in emo_sorted.iterrows()
    ]
    # emotions = dict(zip(emo_sorted['Emotion'], emo_sorted['Percentage']))
    # print(emotions)

    return jsonify({
        "Predicted_Sentiment": sentiment_label,
        "cd": sentiment_score,
        "emotions": emotions
    })

@app.route('/api/analyze_document', methods=['POST'])
def analyze_document():
    file = request.files['file']
    # raw = file.read()
    # encoding = chardet.detect(raw)['encoding']
    # text = raw.decode(encoding)
    print(file.filename)
    text=extract_text_from_file(file)

    # text = file.read().decode('utf-8')

    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    outputs = model(**inputs)

    probs = torch.softmax(outputs.logits, dim=1).flatten().tolist()
    probs = [round(i * 100, 2) for i in probs]
    emo_long = ["Admiration", "Amusement", "Anger", "Annoyance", "Approval", "Caring", "Confusion", "Curiosity",
                "Desire", "Disappointment", "Disapproval", "Disgust", "Embarrassment", "Excitement", "Fear",
                "Gratitude", "Grief", "Joy", "Love", "Nervousness", "Optimism", "Pride", "Realization", "Relief",
                "Remorse", "Sadness", "Surprise", "Neutral"]
    emo_dict_long = dict(zip(emo_long, probs))
    emo = pd.DataFrame(emo_dict_long, index=['Emotions']).T

    emo = emo.reset_index()
    emo.columns = ["Emotion", "Percentage"]

    emo_sorted = emo.sort_values(by='Percentage', ascending=False)
    emo_sorted = emo_sorted[emo_sorted['Percentage'] > 1]

    sentiment_score = emo.loc[emo['Percentage'].idxmax()]['Percentage']
    sentiment_label = emo.loc[emo['Percentage'].idxmax()]['Emotion']

    # emotions = dict(zip(emo_sorted['Emotion'], emo_sorted['Percentage']))
    emotions = [
        {"emotion": row.Emotion, "prob": row.Percentage}
        for _, row in emo_sorted.iterrows()
    ]

    return jsonify({
        "Predicted_Sentiment": sentiment_label,
        "cd": sentiment_score,
        "emotions": emotions
    })

@app.route('/api/summarize_document', methods=['POST'])
def summarize_document():
    try:
        file = request.files['file']
        question = request.form.get('question', 'Summarize this document')
        
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as tmp_file:
            file.save(tmp_file.name)
            
            # Get OpenAI API key from environment (always use from .env)
            openai_api_key = os.environ.get('OPENAI_API_KEY')
            
            if openai_api_key:
                summarizer.set_google_api_key(openai_api_key)
            else:
                return jsonify({
                    "error": "OpenAI API key not configured on server",
                    "status": "error"
                }), 500
            
            # Summarize document
            summary = summarizer.summarize_document(tmp_file.name, question)
            
            # Clean up temporary file
            os.unlink(tmp_file.name)
            
            return jsonify({
                "summary": summary,
                "question": question,
                "status": "success"
            })
            
    except Exception as e:
        return jsonify({
            "error": f"Error summarizing document: {str(e)}",
            "status": "error"
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False)