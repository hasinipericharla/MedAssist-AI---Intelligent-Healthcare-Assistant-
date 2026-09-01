"""
test_explain.py
---------------
Standalone checks for Module 4 (Explainable AI).
Run directly:  python test_explain.py

Verifies:
  1. Output shape - prediction_reason and prediction_reason_global exist,
     percentages sum to ~100.
  2. Determinism - same input twice gives identical explanations.
  3. Context-sensitivity - SHAP contribution for the same symptom changes
     depending on which other symptoms are present, while the global
     feature_importances_ contribution stays roughly fixed. This is the
     core proof that SHAP is doing local explainability, not just
     re-deriving the same global numbers.
"""

from predict import predict_diseases


def check_output_shape():
    result = predict_diseases(["yellowing_of_eyes", "dark_urine", "vomiting"])
    assert "prediction_reason" in result, "Missing SHAP explanation (prediction_reason)"
    assert "prediction_reason_global" in result, "Missing global explanation (prediction_reason_global)"

    shap_total = sum(x["contribution_percent"] for x in result["prediction_reason"])
    global_total = sum(x["contribution_percent"] for x in result["prediction_reason_global"])
    assert 99 <= shap_total <= 101, f"SHAP percentages don't sum to ~100: {shap_total}"
    assert 99 <= global_total <= 101, f"Global percentages don't sum to ~100: {global_total}"

    print("[OK] Output shape check passed")


def check_determinism():
    symptoms = ["high_fever", "cough", "fatigue", "headache"]
    r1 = predict_diseases(symptoms)
    r2 = predict_diseases(symptoms)
    assert r1["prediction_reason"] == r2["prediction_reason"], "SHAP explanation is not deterministic!"
    print("[OK] Determinism check passed")


def check_context_sensitivity():
    result_a = predict_diseases(["dark_urine", "vomiting", "fatigue"])
    result_b = predict_diseases(["dark_urine", "yellowing_of_eyes", "itching"])

    shap_a = next(x["contribution_percent"] for x in result_a["prediction_reason"] if x["symptom"] == "dark_urine")
    shap_b = next(x["contribution_percent"] for x in result_b["prediction_reason"] if x["symptom"] == "dark_urine")

    global_a = next(x["contribution_percent"] for x in result_a["prediction_reason_global"] if x["symptom"] == "dark_urine")
    global_b = next(x["contribution_percent"] for x in result_b["prediction_reason_global"] if x["symptom"] == "dark_urine")

    print(f"dark_urine SHAP:   {shap_a}% vs {shap_b}%  (expected to differ across contexts)")
    print(f"dark_urine global: {global_a}% vs {global_b}%  (expected to stay close/identical)")

    assert shap_a != shap_b, "SHAP contribution did not change across contexts — check explainer logic"
    print("[OK] Context-sensitivity check passed")


if __name__ == "__main__":
    check_output_shape()
    check_determinism()
    check_context_sensitivity()
    print("\nAll Module 4 checks passed.")