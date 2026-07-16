"""
train_model.py
---------------
Trains a Decision Tree and a Random Forest on the symptom-disease dataset,
compares their performance, and saves both models (plus the symptom list
and label classes) so predict.py can load them later.
"""

import json
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report
)

DATA_PATH = "data/symptoms_disease.csv"
MODELS_DIR = "models"


def load_data():
    df = pd.read_csv(DATA_PATH)
    symptom_cols = [c for c in df.columns if c != "disease"]
    X = df[symptom_cols]
    y = df["disease"]
    return X, y, symptom_cols


def evaluate(name, model, X_test, y_test):
    preds = model.predict(X_test)
    metrics = {
        "accuracy": round(accuracy_score(y_test, preds), 4),
        "precision_macro": round(precision_score(y_test, preds, average="macro", zero_division=0), 4),
        "recall_macro": round(recall_score(y_test, preds, average="macro", zero_division=0), 4),
        "f1_macro": round(f1_score(y_test, preds, average="macro", zero_division=0), 4),
    }
    print(f"\n--- {name} ---")
    for k, v in metrics.items():
        print(f"{k}: {v}")
    print(classification_report(y_test, preds, zero_division=0))
    return metrics


def main():
    X, y, symptom_cols = load_data()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    dt = DecisionTreeClassifier(random_state=42)
    dt.fit(X_train, y_train)
    dt_metrics = evaluate("Decision Tree", dt, X_test, y_test)

    rf = RandomForestClassifier(n_estimators=200, random_state=42)
    rf.fit(X_train, y_train)
    rf_metrics = evaluate("Random Forest", rf, X_test, y_test)

    # Save both models so the app can offer a live "DT vs RF" comparison view
    joblib.dump(dt, f"{MODELS_DIR}/decision_tree.pkl")
    joblib.dump(rf, f"{MODELS_DIR}/random_forest.pkl")

    with open(f"{MODELS_DIR}/symptom_columns.json", "w") as f:
        json.dump(symptom_cols, f, indent=2)

    with open(f"{MODELS_DIR}/model_comparison.json", "w") as f:
        json.dump({"decision_tree": dt_metrics, "random_forest": rf_metrics}, f, indent=2)

    better = "Random Forest" if rf_metrics["f1_macro"] >= dt_metrics["f1_macro"] else "Decision Tree"
    print(f"\nModels saved to '{MODELS_DIR}/'. Better model on this run: {better}")


if __name__ == "__main__":
    main()