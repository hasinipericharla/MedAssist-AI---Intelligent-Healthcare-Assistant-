# """
# Add this to your existing Flask app.py (or a blueprint file if you're
# already organizing routes that way).

# Assumes chat_assistant.py sits next to app.py -- adjust the import path
# to match your actual folder structure (e.g. `from ml.chat_assistant import ...`
# if you've already split into backend/ml/ per Module 19).
# """

# from flask import Flask, request, jsonify
# from chat_assistant import get_chat_response
# from dotenv import load_dotenv
# load_dotenv()

# app = Flask(__name__)  # remove this line if app already exists elsewhere


# @app.route("/api/chat", methods=["POST"])
# def chat():
#     """
#     Expected JSON body:
#     {
#         "disease": "Flu",
#         "question": "What foods should I eat?",
#         "symptoms": ["fever", "cough"]   # optional, improves LLM grounding
#     }
#     """
#     data = request.get_json(silent=True) or {}
#     disease = data.get("disease")
#     question = data.get("question")
#     symptoms = data.get("symptoms")

#     if not disease or not question:
#         return jsonify({"error": "'disease' and 'question' are required"}), 400

#     result = get_chat_response(question=question, disease=disease, symptoms=symptoms)
#     return jsonify(result), 200


# if __name__ == "__main__":
#     app.run(debug=True)

"""
app.py
------
The Flask entry point for MedAssist AI. Loads the models saved by
train_model.py and exposes:

  POST /api/predict  -> Module 1 (disease prediction, DT vs RF)
  POST /api/chat      -> Module 2 (AI health chat assistant)

Run with:
    python app.py
"""

import os
import json
import joblib
import numpy as np
from flask import Flask, request, jsonify
from dotenv import load_dotenv

from chat_assistant import get_chat_response

load_dotenv()

app = Flask(__name__)

MODELS_DIR = "models"

# Load models once at startup, not per-request -- reloading a pickle on
# every API call would be slow and pointless since they don't change.
rf_model = joblib.load(os.path.join(MODELS_DIR, "random_forest.pkl"))
dt_model = joblib.load(os.path.join(MODELS_DIR, "decision_tree.pkl"))

with open(os.path.join(MODELS_DIR, "symptom_columns.json")) as f:
    SYMPTOM_COLUMNS = json.load(f)

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "MedAssist AI server is running", "endpoints": ["/api/predict", "/api/chat"]}), 200


def symptoms_to_vector(symptoms):
    """
    Turn a list of symptom names (e.g. ['fever', 'cough']) into the exact
    one-hot vector the models were trained on -- same column order and
    same cleaning rule (lowercase, underscores) as convert_kaggle_dataset.py
    used when it built the training data.
    """
    cleaned = {s.strip().lower().replace(" ", "_") for s in symptoms}
    return [1 if col in cleaned else 0 for col in SYMPTOM_COLUMNS]


@app.route("/api/predict", methods=["POST"])
def predict():
    """
    Expected JSON body:
    { "symptoms": ["fever", "cough", "fatigue"] }
    """
    data = request.get_json(silent=True) or {}
    symptoms = data.get("symptoms")

    if not symptoms or not isinstance(symptoms, list):
        return jsonify({"error": "'symptoms' must be a non-empty list"}), 400

    unknown = [s for s in symptoms if s.strip().lower().replace(" ", "_") not in SYMPTOM_COLUMNS]
    if unknown:
        return jsonify({"error": f"Unrecognized symptoms: {unknown}"}), 400

    vector = [symptoms_to_vector(symptoms)]

    # Random Forest is the primary prediction -- calibrated, spread-out
    # confidence across related diseases (per your Module 1 findings).
    probs = rf_model.predict_proba(vector)[0]
    classes = rf_model.classes_
    top3_idx = np.argsort(probs)[::-1][:3]
    top3 = [
        {"disease": classes[i], "confidence": round(float(probs[i]) * 100, 1)}
        for i in top3_idx
    ]

    # Decision Tree included too, so the frontend can show the DT vs RF
    # comparison view from your Module 1 spec.
    dt_pred = dt_model.predict(vector)[0]

    return jsonify({
        "top3_predictions": top3,
        "random_forest_top_prediction": top3[0]["disease"],
        "decision_tree_prediction": dt_pred,
    }), 200


@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Expected JSON body:
    {
        "disease": "Flu",
        "question": "What foods should I eat?",
        "symptoms": ["fever", "cough"]   # optional, improves LLM grounding
    }
    """
    data = request.get_json(silent=True) or {}
    disease = data.get("disease")
    question = data.get("question")
    symptoms = data.get("symptoms")

    if not disease or not question:
        return jsonify({"error": "'disease' and 'question' are required"}), 400

    result = get_chat_response(question=question, disease=disease, symptoms=symptoms)
    return jsonify(result), 200


if __name__ == "__main__":
    app.run(debug=True)