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

port = int(os.environ.get("PORT", 5000))




MODEL_NAME = "sangkm/go-emotions-fine-tuned-distilroberta"

def load_model():
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
        return tokenizer, model

tokenizer, model = load_model()

def extract_text_from_file(file: FileStorage) -> str:
    # content = file.read()
    ext = file.filename.lower()
    if ext.endswith(".txt"):
        return file.read().decode('utf-8')
    elif ext.endswith(".docx"):
        return docx2txt.process(file)
    elif ext.endswith(".pdf"):
        text = []
        with open(file, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text.append(page.extract_text() or "")
        return "\n".join(text)
    else:
        return " "



app = Flask(__name__)
CORS(app,origins=["https://verdict-frontend-gamma.vercel.app"])

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=True)