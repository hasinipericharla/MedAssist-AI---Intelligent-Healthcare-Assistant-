"""
predict.py
----------
Loads the trained models and, given a list of symptoms, returns:
  1. Top-3 disease predictions with confidence scores
  2. A per-symptom "why" explanation for the top prediction
  3. A side-by-side Decision Tree vs Random Forest comparison

This is deliberately framework-agnostic (no Flask here) so you can
import `predict_diseases()` directly into your Flask route later.
"""

import json
import joblib
import numpy as np
import pandas as pd

MODELS_DIR = "models"

# Load once at import time so repeated predictions are fast
_dt = joblib.load(f"{MODELS_DIR}/decision_tree.pkl")
_rf = joblib.load(f"{MODELS_DIR}/random_forest.pkl")
with open(f"{MODELS_DIR}/symptom_columns.json") as f:
    SYMPTOM_COLUMNS = json.load(f)


def _symptoms_to_vector(selected_symptoms):
    """Turn a list like ['fever', 'dry_cough'] into the 0/1 feature vector
    the model expects, in the exact column order used during training."""
    unknown = [s for s in selected_symptoms if s not in SYMPTOM_COLUMNS]
    if unknown:
        raise ValueError(
            f"Unknown symptom(s): {unknown}. "
            f"Valid options: {SYMPTOM_COLUMNS}"
        )
    vector = [1 if col in selected_symptoms else 0 for col in SYMPTOM_COLUMNS]
    return pd.DataFrame([vector], columns=SYMPTOM_COLUMNS)


def _top_k_predictions(model, X, k=3):
    """Return [(disease, confidence_percent), ...] sorted descending."""
    proba = model.predict_proba(X)[0]
    classes = model.classes_
    ranked = sorted(zip(classes, proba), key=lambda x: x[1], reverse=True)
    top_k = ranked[:k]
    return [(disease, round(prob * 100, 1)) for disease, prob in top_k]


def _explain_prediction(model, selected_symptoms, predicted_disease):
    """
    Explainability using the model's global feature importances, scoped to
    only the symptoms the user actually reported (since an absent symptom
    can't have "contributed" to this specific prediction).
    Returns a list of {symptom, contribution_percent} sorted descending,
    matching the "Fever contributed 35%" style from the spec.
    """
    importances = model.feature_importances_
    symptom_importance = {
        col: importances[i]
        for i, col in enumerate(SYMPTOM_COLUMNS)
        if col in selected_symptoms
    }

    total = sum(symptom_importance.values())
    if total == 0:
        # Fallback: split evenly if none of the reported symptoms are
        # informative for this model (edge case with unusual inputs)
        equal_share = round(100 / len(selected_symptoms), 1) if selected_symptoms else 0
        return [{"symptom": s, "contribution_percent": equal_share} for s in selected_symptoms]

    explanation = [
        {
            "symptom": symptom,
            "contribution_percent": round((importance / total) * 100, 1),
        }
        for symptom, importance in symptom_importance.items()
    ]
    explanation.sort(key=lambda x: x["contribution_percent"], reverse=True)
    return explanation


def predict_diseases(selected_symptoms, model_choice="random_forest"):
    """
    Main entry point for Module 1.

    Args:
        selected_symptoms: list[str], e.g. ["fever", "dry_cough", "fatigue", "headache"]
        model_choice: "random_forest" (default, recommended) or "decision_tree"

    Returns:
        dict with top-3 predictions, explanation for the #1 prediction,
        and a DT-vs-RF comparison for the same input.
    """
    X = _symptoms_to_vector(selected_symptoms)
    model = _rf if model_choice == "random_forest" else _dt

    top3 = _top_k_predictions(model, X, k=3)
    top_disease = top3[0][0]
    explanation = _explain_prediction(model, selected_symptoms, top_disease)

    # Always compute both, so the frontend can show a comparison view
    rf_top3 = _top_k_predictions(_rf, X, k=3)
    dt_top3 = _top_k_predictions(_dt, X, k=3)

    return {
        "input_symptoms": selected_symptoms,
        "model_used": model_choice,
        "top_3_predictions": [
            {"disease": disease, "confidence_percent": conf} for disease, conf in top3
        ],
        "prediction_reason": explanation,
        "model_comparison": {
            "random_forest_top_3": [
                {"disease": d, "confidence_percent": c} for d, c in rf_top3
            ],
            "decision_tree_top_3": [
                {"disease": d, "confidence_percent": c} for d, c in dt_top3
            ],
        },
    }


if __name__ == "__main__":
    # Example matching the spec: Fever, dry cough, fatigue, headache -> Flu/COVID/Cold
    # example_symptoms = ["fever", "dry_cough", "fatigue", "headache"]
    example_symptoms = ["continuous_sneezing", "chills", "fatigue", "cough",
                         "high_fever", "headache", "runny_nose", "congestion"]
    # result = predict_diseases(example_symptoms)
    result=predict_diseases(["yellowing_of_eyes", "dark_urine", "vomiting"])
    print(json.dumps(result, indent=2))