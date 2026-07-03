"""
generate_dataset.py
--------------------
Creates a synthetic symptom -> disease dataset for MedAssist AI.

In a real project you would replace this with a proper public dataset
(e.g. a Kaggle "Disease Symptom Prediction" dataset). This script exists
so Module 1 can be trained and tested end-to-end right away, and you can
swap in real data later without changing train_model.py or predict.py.
"""

import random
import pandas as pd

random.seed(42)

# Master list of symptoms used as feature columns
SYMPTOMS = [
    "fever", "dry_cough", "wet_cough", "fatigue", "headache",
    "sore_throat", "runny_nose", "body_ache", "shortness_of_breath",
    "loss_of_taste_smell", "nausea", "vomiting", "diarrhea",
    "abdominal_pain", "chills", "sneezing", "chest_pain",
    "loss_of_appetite", "rash", "joint_pain"
]

# Each disease has a set of "core" symptoms (high probability of appearing)
# and the rest are "noise" symptoms (low probability), so the model has
# something meaningful to learn from.
DISEASE_PROFILES = {
    "Flu": {
        "core": ["fever", "body_ache", "fatigue", "chills", "headache", "dry_cough"],
    },
    "COVID": {
        "core": ["fever", "dry_cough", "fatigue", "loss_of_taste_smell", "shortness_of_breath", "headache"],
    },
    "Common Cold": {
        "core": ["runny_nose", "sneezing", "sore_throat", "wet_cough", "headache"],
    },
    "Migraine": {
        "core": ["headache", "nausea", "fatigue"],
    },
    "Food Poisoning": {
        "core": ["nausea", "vomiting", "diarrhea", "abdominal_pain", "fever"],
    },
    "Allergy": {
        "core": ["sneezing", "runny_nose", "rash", "sore_throat"],
    },
    "Dengue": {
        "core": ["fever", "joint_pain", "rash", "headache", "fatigue"],
    },
    "Typhoid": {
        "core": ["fever", "abdominal_pain", "loss_of_appetite", "fatigue", "chills"],
    },
}

CORE_PROB = 0.80   # chance a core symptom is present for that disease
NOISE_PROB = 0.06  # chance a non-core symptom is present anyway
SAMPLES_PER_DISEASE = 150


def generate_row(disease):
    core_symptoms = set(DISEASE_PROFILES[disease]["core"])
    row = {}
    for symptom in SYMPTOMS:
        if symptom in core_symptoms:
            row[symptom] = 1 if random.random() < CORE_PROB else 0
        else:
            row[symptom] = 1 if random.random() < NOISE_PROB else 0
    row["disease"] = disease
    return row


def main():
    rows = []
    for disease in DISEASE_PROFILES:
        for _ in range(SAMPLES_PER_DISEASE):
            rows.append(generate_row(disease))

    df = pd.DataFrame(rows)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)  # shuffle
    df.to_csv("data/symptoms_disease.csv", index=False)
    print(f"Dataset created: {len(df)} rows, {len(SYMPTOMS)} symptoms, "
          f"{len(DISEASE_PROFILES)} diseases -> data/symptoms_disease.csv")


if __name__ == "__main__":
    main()