

# """
# predict.py
# ----------
# Loads the trained models and, given a list of symptoms, returns:
#   1. Top-3 disease predictions with confidence scores
#   2. A per-symptom "why" explanation for the top prediction
#      - SHAP-based (per-prediction, local explainability)
#      - feature_importances_-based (global explainability, kept for comparison)
#   3. A side-by-side Decision Tree vs Random Forest comparison

# This is deliberately framework-agnostic (no Flask here) so you can
# import `predict_diseases()` directly into your Flask route later.
# """

# import json
# import joblib
# import numpy as np
# import pandas as pd
# import shap

# MODELS_DIR = "models"

# # Load once at import time so repeated predictions are fast
# _dt = joblib.load(f"{MODELS_DIR}/decision_tree.pkl")
# _rf = joblib.load(f"{MODELS_DIR}/random_forest.pkl")
# with open(f"{MODELS_DIR}/symptom_columns.json") as f:
#     SYMPTOM_COLUMNS = json.load(f)

# # Build SHAP explainers once at import time (same pattern as the models above)
# _rf_explainer = shap.TreeExplainer(_rf)
# _dt_explainer = shap.TreeExplainer(_dt)


# def _symptoms_to_vector(selected_symptoms):
#     """Turn a list like ['fever', 'dry_cough'] into the 0/1 feature vector
#     the model expects, in the exact column order used during training."""
#     unknown = [s for s in selected_symptoms if s not in SYMPTOM_COLUMNS]
#     if unknown:
#         raise ValueError(
#             f"Unknown symptom(s): {unknown}. "
#             f"Valid options: {SYMPTOM_COLUMNS}"
#         )
#     vector = [1 if col in selected_symptoms else 0 for col in SYMPTOM_COLUMNS]
#     return pd.DataFrame([vector], columns=SYMPTOM_COLUMNS)


# def _top_k_predictions(model, X, k=3):
#     """Return [(disease, confidence_percent), ...] sorted descending."""
#     proba = model.predict_proba(X)[0]
#     classes = model.classes_
#     ranked = sorted(zip(classes, proba), key=lambda x: x[1], reverse=True)
#     top_k = ranked[:k]
#     return [(disease, round(prob * 100, 1)) for disease, prob in top_k]


# def _explain_prediction(model, selected_symptoms, predicted_disease):
#     """
#     GLOBAL explainability using the model's feature_importances_, scoped to
#     only the symptoms the user actually reported (since an absent symptom
#     can't have "contributed" to this specific prediction).

#     Limitation: feature_importances_ reflects importance across the WHOLE
#     training set, not this specific prediction — so the same symptom gets
#     the same contribution % regardless of which disease was predicted or
#     what else was reported. Kept here for comparison against the SHAP
#     (local) explanation below.

#     Returns a list of {symptom, contribution_percent} sorted descending.
#     """
#     importances = model.feature_importances_
#     symptom_importance = {
#         col: importances[i]
#         for i, col in enumerate(SYMPTOM_COLUMNS)
#         if col in selected_symptoms
#     }

#     total = sum(symptom_importance.values())
#     if total == 0:
#         # Fallback: split evenly if none of the reported symptoms are
#         # informative for this model (edge case with unusual inputs)
#         equal_share = round(100 / len(selected_symptoms), 1) if selected_symptoms else 0
#         return [{"symptom": s, "contribution_percent": equal_share} for s in selected_symptoms]

#     explanation = [
#         {
#             "symptom": symptom,
#             "contribution_percent": round((importance / total) * 100, 1),
#         }
#         for symptom, importance in symptom_importance.items()
#     ]
#     explanation.sort(key=lambda x: x["contribution_percent"], reverse=True)
#     return explanation


# def _explain_prediction_shap(model, explainer, X, selected_symptoms, predicted_disease):
#     """
#     LOCAL explainability using SHAP TreeExplainer. Unlike feature_importances_,
#     SHAP values are specific to THIS input and THIS predicted class — matching
#     the spec's "Fever contributed 35%" style, where the contribution changes
#     based on which disease was predicted and what else the patient reported.

#     Returns a list of {symptom, contribution_percent} sorted descending.
#     """
#     class_index = list(model.classes_).index(predicted_disease)
#     shap_values = explainer.shap_values(X)

#     # shap_values shape depends on sklearn/shap version:
#     # newer shap returns a single array of shape (1, n_features, n_classes)
#     # older shap returns a list of arrays, one per class
#     if isinstance(shap_values, list):
#         class_shap_values = shap_values[class_index][0]
#     else:
#         class_shap_values = shap_values[0, :, class_index]

#     symptom_contributions = {
#         col: class_shap_values[i]
#         for i, col in enumerate(SYMPTOM_COLUMNS)
#         if col in selected_symptoms and class_shap_values[i] > 0
#     }

#     total = sum(symptom_contributions.values())
#     if total == 0:
#         # Fallback: none of the reported symptoms pushed toward this class
#         # (can happen with unusual inputs) — split evenly instead of
#         # returning an empty explanation.
#         equal_share = round(100 / len(selected_symptoms), 1) if selected_symptoms else 0
#         return [{"symptom": s, "contribution_percent": equal_share} for s in selected_symptoms]

#     explanation = [
#         {"symptom": symptom, "contribution_percent": round((value / total) * 100, 1)}
#         for symptom, value in symptom_contributions.items()
#     ]
#     explanation.sort(key=lambda x: x["contribution_percent"], reverse=True)
#     return explanation


# def predict_diseases(selected_symptoms, model_choice="random_forest"):
#     """
#     Main entry point for Module 1 + Module 4.

#     Args:
#         selected_symptoms: list[str], e.g. ["fever", "dry_cough", "fatigue", "headache"]
#         model_choice: "random_forest" (default, recommended) or "decision_tree"

#     Returns:
#         dict with top-3 predictions, SHAP + global explanations for the
#         #1 prediction, and a DT-vs-RF comparison for the same input.
#     """
#     X = _symptoms_to_vector(selected_symptoms)
#     model = _rf if model_choice == "random_forest" else _dt
#     explainer = _rf_explainer if model_choice == "random_forest" else _dt_explainer

#     top3 = _top_k_predictions(model, X, k=3)
#     top_disease = top3[0][0]

#     explanation = _explain_prediction_shap(model, explainer, X, selected_symptoms, top_disease)
#     explanation_global = _explain_prediction(model, selected_symptoms, top_disease)

#     # Always compute both, so the frontend can show a comparison view
#     rf_top3 = _top_k_predictions(_rf, X, k=3)
#     dt_top3 = _top_k_predictions(_dt, X, k=3)

#     return {
#         "input_symptoms": selected_symptoms,
#         "model_used": model_choice,
#         "top_3_predictions": [
#             {"disease": disease, "confidence_percent": conf} for disease, conf in top3
#         ],
        
#         "prediction_reason": explanation,                  # SHAP: local/per-prediction
#         "prediction_reason_global": explanation_global,     # feature_importances_: global
#         "model_comparison": {
#             "random_forest_top_3": [
#                 {"disease": d, "confidence_percent": c} for d, c in rf_top3
#             ],
#             "decision_tree_top_3": [
#                 {"disease": d, "confidence_percent": c} for d, c in dt_top3
#             ],
#         },
#     }


# if __name__ == "__main__":
#     # Example matching the spec: Fever, dry cough, fatigue, headache -> Flu/COVID/Cold
#     # example_symptoms = ["fever", "dry_cough", "fatigue", "headache"]
#     example_symptoms = ["continuous_sneezing", "chills", "fatigue", "cough",
#                          "high_fever", "headache", "runny_nose", "congestion"]
#     # result = predict_diseases(example_symptoms)
#     result = predict_diseases(["yellowing_of_eyes", "dark_urine", "vomiting"])
#     print(json.dumps(result, indent=2))

"""
predict.py
----------
Loads the trained models and, given a list of symptoms, returns:
  1. Top-3 disease predictions with confidence scores
  2. A per-symptom "why" explanation for the top prediction
     - SHAP-based (per-prediction, local explainability), showing
       symptoms that both support AND argue against the prediction
     - feature_importances_-based (global explainability, kept for comparison)
  3. A side-by-side Decision Tree vs Random Forest comparison
  4. Confidence / reliability signals: low-confidence flag, model
     disagreement flag, and a severity flag that is decoupled from
     "whatever happened to rank #1"

This is deliberately framework-agnostic (no Flask here) so you can
import `predict_diseases()` directly into your Flask route later.
"""

import json
import joblib
import numpy as np
import pandas as pd
import shap

MODELS_DIR = "models"

# --- Tunable thresholds -----------------------------------------------
# Below this top-1 confidence, the result is treated as inconclusive.
CONFIDENCE_THRESHOLD = 35.0

# A high-severity disease is only flagged as "High Risk" if it appears
# in the top-3 AND clears this (higher) bar on its own confidence.
HIGH_SEVERITY_THRESHOLD = 40.0

# Below this many reported symptoms, always show a "add more symptoms"
# nudge regardless of confidence.
MIN_RELIABLE_SYMPTOM_COUNT = 4

# Diseases you consider high-severity / "see a doctor now" tier.
# Edit this list to match your dataset's actual disease names.
HIGH_SEVERITY_DISEASES = {
    "AIDS",
    "Tuberculosis",
    "Hepatitis A",
    "Hepatitis B",
    "Hepatitis C",
    "Hepatitis D",
    "Hepatitis E",
    "Heart attack",
    "Paralysis (brain hemorrhage)",
    "Dengue",
    "Malaria",
    "Typhoid",
}

# Load once at import time so repeated predictions are fast
_dt = joblib.load(f"{MODELS_DIR}/decision_tree.pkl")
_rf = joblib.load(f"{MODELS_DIR}/random_forest.pkl")
with open(f"{MODELS_DIR}/symptom_columns.json") as f:
    SYMPTOM_COLUMNS = json.load(f)

# Build SHAP explainers once at import time (same pattern as the models above)
_rf_explainer = shap.TreeExplainer(_rf)
_dt_explainer = shap.TreeExplainer(_dt)


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
    GLOBAL explainability using the model's feature_importances_, scoped to
    only the symptoms the user actually reported (since an absent symptom
    can't have "contributed" to this specific prediction).

    Limitation: feature_importances_ reflects importance across the WHOLE
    training set, not this specific prediction — so the same symptom gets
    the same contribution % regardless of which disease was predicted or
    what else was reported. Kept here for comparison against the SHAP
    (local) explanation below.

    Returns a list of {symptom, contribution_percent} sorted descending.
    """
    importances = model.feature_importances_
    symptom_importance = {
        col: importances[i]
        for i, col in enumerate(SYMPTOM_COLUMNS)
        if col in selected_symptoms
    }

    total = sum(symptom_importance.values())
    if total == 0:
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


def _explain_prediction_shap(model, explainer, X, selected_symptoms, predicted_disease):
    """
    LOCAL explainability using SHAP TreeExplainer. Unlike feature_importances_,
    SHAP values are specific to THIS input and THIS predicted class.

    IMPORTANT: unlike the old version, this keeps symptoms whose SHAP value
    is negative (i.e. symptoms that actually argue AGAINST the predicted
    disease) instead of silently dropping them. Hiding negative evidence
    makes a shaky prediction look artificially clean-cut.

    Returns a list of:
        {"symptom": str, "shap_value": float, "direction": "supports" | "against",
         "contribution_percent": float}
    sorted by absolute SHAP value descending. contribution_percent is the
    share of TOTAL POSITIVE evidence only (so it still sums to ~100% across
    the "supports" rows, matching the "Fever contributed 35%" style), while
    "against" rows are shown with their raw share for context, not netted in.
    """
    class_index = list(model.classes_).index(predicted_disease)
    shap_values = explainer.shap_values(X)

    # shap_values shape depends on sklearn/shap version:
    # newer shap returns a single array of shape (1, n_features, n_classes)
    # older shap returns a list of arrays, one per class
    if isinstance(shap_values, list):
        class_shap_values = shap_values[class_index][0]
    else:
        class_shap_values = shap_values[0, :, class_index]

    reported = {
        col: class_shap_values[i]
        for i, col in enumerate(SYMPTOM_COLUMNS)
        if col in selected_symptoms
    }

    if not reported:
        return []

    positive_total = sum(v for v in reported.values() if v > 0)
    negative_total = sum(abs(v) for v in reported.values() if v < 0)

    explanation = []
    for symptom, value in reported.items():
        if value > 0:
            pct = round((value / positive_total) * 100, 1) if positive_total > 0 else 0.0
            direction = "supports"
        elif value < 0:
            pct = round((abs(value) / negative_total) * 100, 1) if negative_total > 0 else 0.0
            direction = "against"
        else:
            pct = 0.0
            direction = "neutral"

        explanation.append(
            {
                "symptom": symptom,
                "shap_value": round(float(value), 4),
                "direction": direction,
                "contribution_percent": pct,
            }
        )

    explanation.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
    return explanation


def _severity_flag(top3_combined_diseases_with_conf):
    """
    Decide whether to show a "High Risk" banner. Decoupled from "whatever
    is ranked #1" — a high-severity disease only triggers the flag if it
    (a) appears in the combined top-3 list from EITHER model, and
    (b) individually clears HIGH_SEVERITY_THRESHOLD on its own confidence.

    top3_combined_diseases_with_conf: list of (disease, confidence_percent)
    """
    for disease, conf in top3_combined_diseases_with_conf:
        if disease in HIGH_SEVERITY_DISEASES and conf >= HIGH_SEVERITY_THRESHOLD:
            return True, disease
    return False, None


def predict_diseases(selected_symptoms, model_choice="random_forest"):
    """
    Main entry point for Module 1 + Module 4.

    Args:
        selected_symptoms: list[str], e.g. ["fever", "dry_cough", "fatigue", "headache"]
        model_choice: "random_forest" (default, recommended) or "decision_tree"

    Returns:
        dict with top-3 predictions, SHAP + global explanations for the
        #1 prediction, a DT-vs-RF comparison, and reliability flags:
          - "inconclusive": True if top-1 confidence < CONFIDENCE_THRESHOLD
          - "low_symptom_count": True if fewer than MIN_RELIABLE_SYMPTOM_COUNT reported
          - "models_disagree": True if DT and RF top-1 picks differ
          - "high_risk": (bool, disease_or_None) per _severity_flag rules
    """
    if not selected_symptoms:
        raise ValueError("selected_symptoms cannot be empty.")

    X = _symptoms_to_vector(selected_symptoms)
    model = _rf if model_choice == "random_forest" else _dt
    explainer = _rf_explainer if model_choice == "random_forest" else _dt_explainer

    top3 = _top_k_predictions(model, X, k=3)
    top_disease, top_confidence = top3[0]

    explanation = _explain_prediction_shap(model, explainer, X, selected_symptoms, top_disease)
    explanation_global = _explain_prediction(model, selected_symptoms, top_disease)

    # Always compute both, so the frontend can show a comparison view
    rf_top3 = _top_k_predictions(_rf, X, k=3)
    dt_top3 = _top_k_predictions(_dt, X, k=3)

    models_disagree = rf_top3[0][0] != dt_top3[0][0]
    inconclusive = top_confidence < CONFIDENCE_THRESHOLD
    low_symptom_count = len(selected_symptoms) < MIN_RELIABLE_SYMPTOM_COUNT

    # Check severity against the combined top-3 of both models, not just
    # whichever model_choice was requested, so a severe disease showing up
    # strongly in either model still gets flagged.
    combined_for_severity = rf_top3 + dt_top3
    high_risk, high_risk_disease = _severity_flag(combined_for_severity)

    return {
        "input_symptoms": selected_symptoms,
        "model_used": model_choice,
        "top_3_predictions": [
            {"disease": disease, "confidence_percent": conf} for disease, conf in top3
        ],
        "prediction_reason": explanation,                  # SHAP: local/per-prediction, supports + against
        "prediction_reason_global": explanation_global,     # feature_importances_: global
        "model_comparison": {
            "random_forest_top_3": [
                {"disease": d, "confidence_percent": c} for d, c in rf_top3
            ],
            "decision_tree_top_3": [
                {"disease": d, "confidence_percent": c} for d, c in dt_top3
            ],
        },
        "reliability": {
            "inconclusive": inconclusive,
            "confidence_threshold": CONFIDENCE_THRESHOLD,
            "low_symptom_count": low_symptom_count,
            "min_recommended_symptoms": MIN_RELIABLE_SYMPTOM_COUNT,
            "models_disagree": models_disagree,
            "high_risk": high_risk,
            "high_risk_disease": high_risk_disease,
        },
    }


if __name__ == "__main__":
    # Example matching the spec: Fever, dry cough, fatigue, headache -> Flu/COVID/Cold
    # example_symptoms = ["fever", "dry_cough", "fatigue", "headache"]
    example_symptoms = ["continuous_sneezing", "chills", "fatigue", "cough",
                         "high_fever", "headache", "runny_nose", "congestion"]
    # result = predict_diseases(example_symptoms)
    result = predict_diseases(["yellowing_of_eyes", "dark_urine", "vomiting"])
    print(json.dumps(result, indent=2))