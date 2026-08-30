"""
app.py
------
The Flask entry point for MedAssist AI. Loads the models saved by
train_model.py and exposes:

  POST /api/predict  -> Module 1 (disease prediction, DT vs RF)
                         + Module 4 (SHAP-based explainability)
  POST /api/chat      -> Module 2 (AI health chat assistant)

Plus page routes for the sidebar app shell (predict, profile, history,
dashboard, hospitals, reminders, account, admin).

Run with:
    python app.py
"""

import os
import json
import joblib
import numpy as np
import shap
from flask import Flask, request, jsonify, render_template
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

# Built once at startup, same reasoning as loading the models themselves --
# SHAP TreeExplainer setup is not free, so we don't want to redo it per request.
rf_explainer = shap.TreeExplainer(rf_model)


def symptoms_to_vector(symptoms):
    """
    Turn a list of symptom names (e.g. ['fever', 'cough']) into the exact
    one-hot vector the models were trained on -- same column order and
    same cleaning rule (lowercase, underscores) as convert_kaggle_dataset.py
    used when it built the training data.
    """
    cleaned = {s.strip().lower().replace(" ", "_") for s in symptoms}
    return [1 if col in cleaned else 0 for col in SYMPTOM_COLUMNS]


def explain_prediction(vector_2d, predicted_disease, cleaned_symptoms):
    """
    Per-prediction (local) explainability using SHAP -- contribution values
    are specific to THIS input and THIS predicted disease, unlike
    rf_model.feature_importances_ which is a fixed global ranking.
    Returns [{"symptom": ..., "contribution_percent": ...}, ...] sorted desc.
    """
    class_index = list(rf_model.classes_).index(predicted_disease)
    shap_values = rf_explainer.shap_values(np.array(vector_2d))
    # Handles both shap output formats depending on installed version:
    # newer shap returns one array shaped (1, n_features, n_classes),
    # older shap returns a list of arrays, one per class.
    if isinstance(shap_values, list):
        class_shap_values = shap_values[class_index][0]
    else:
        class_shap_values = shap_values[0, :, class_index]

    contributions = {
        col: class_shap_values[i]
        for i, col in enumerate(SYMPTOM_COLUMNS)
        if col in cleaned_symptoms and class_shap_values[i] > 0
    }

    total = sum(contributions.values())
    if total == 0:
        # None of the reported symptoms pushed toward this class (rare
        # edge case) -- split evenly instead of returning an empty list.
        equal_share = round(100 / len(cleaned_symptoms), 1) if cleaned_symptoms else 0
        return [{"symptom": s, "contribution_percent": equal_share} for s in cleaned_symptoms]

    result = [
        {"symptom": symptom, "contribution_percent": round((value / total) * 100, 1)}
        for symptom, value in contributions.items()
    ]
    result.sort(key=lambda x: x["contribution_percent"], reverse=True)
    return result


# ---------------------------------------------------------------------
# Page routes (render the sidebar app shell templates)
# ---------------------------------------------------------------------

@app.route("/", methods=["GET"])
def home():
    return render_template("auth.html", active="auth")


@app.route("/predict", methods=["GET"])
def predict_page():
    return render_template("predict.html", active="predict")


@app.route("/profile", methods=["GET"])
def profile_page():
    return render_template("profile.html", active="profile")


@app.route("/history", methods=["GET"])
def history_page():
    return render_template("history.html", active="history")


@app.route("/dashboard", methods=["GET"])
def dashboard_page():
    return render_template("dashboard.html", active="dashboard")


@app.route("/hospitals", methods=["GET"])
def hospitals_page():
    return render_template("hospitals.html", active="hospitals")


@app.route("/reminders", methods=["GET"])
def reminders_page():
    return render_template("reminders.html", active="reminders")


# @app.route("/account", methods=["GET"])
# def auth_page():
#     return render_template("account.html", active="auth")
@app.route("/account", methods=["GET"])
def account_page():
    return render_template("account.html", active="account")


@app.route("/admin", methods=["GET"])
def admin_page():
    return render_template("admin.html", active="admin")

@app.route("/admin-login", methods=["GET"])
def admin_login_page():
    return render_template("admin-login.html")


# ---------------------------------------------------------------------
# API routes (the real backend logic)
# ---------------------------------------------------------------------

@app.route("/api/status", methods=["GET"])
def status():
    return jsonify({"status": "MedAssist AI server is running", "endpoints": ["/api/predict", "/api/chat", "/api/symptoms"]}), 200


@app.route("/api/symptoms", methods=["GET"])
def symptoms_list():
    """Lets the frontend build the symptom picker dynamically instead of
    hardcoding all 130+ symptom names in the HTML."""
    return jsonify({"symptoms": SYMPTOM_COLUMNS}), 200


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
    cleaned_symptoms = {s.strip().lower().replace(" ", "_") for s in symptoms}

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

    # Module 4: explain WHY the top RF prediction was made
    prediction_reason = explain_prediction(vector, top3[0]["disease"], cleaned_symptoms)

    return jsonify({
        "top3_predictions": top3,
        "random_forest_top_prediction": top3[0]["disease"],
        "decision_tree_prediction": dt_pred,
        "prediction_reason": prediction_reason,
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
