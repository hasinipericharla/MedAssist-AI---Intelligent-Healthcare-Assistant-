"""
convert_kaggle_dataset.py
--------------------------
Converts the raw Kaggle "Disease Symptom Prediction" dataset
(itachi9604/disease-symptom-description-dataset) into the same
one-hot format our pipeline already expects:

    symptom_1, symptom_2, ..., symptom_n, disease

Usage:
    1. Download the dataset zip from Kaggle and extract it.
    2. Put the main CSV (usually named "dataset.csv") at:
       data/raw/dataset.csv
    3. Run: python3 convert_kaggle_dataset.py
    4. This overwrites data/symptoms_disease.csv with the real data.

You do NOT need to touch train_model.py or predict.py after this —
they just read data/symptoms_disease.csv, whatever its origin.
"""

import os
import pandas as pd

RAW_PATH = "data/raw/dataset.csv"
OUTPUT_PATH = "data/symptoms_disease.csv"


def clean_symptom_name(name):
    """Kaggle's symptom text often has leading/trailing spaces and
    inconsistent casing, e.g. ' skin_rash' vs 'Skin_Rash'. Normalize it."""
    return str(name).strip().lower().replace(" ", "_")


def main():
    if not os.path.exists(RAW_PATH):
        raise FileNotFoundError(
            f"Couldn't find {RAW_PATH}. Download the Kaggle dataset, "
            f"extract it, and place the CSV at that path first."
        )

    df = pd.read_csv(RAW_PATH)
    print("Columns found in raw file:", list(df.columns))

    # The disease column is usually literally called "Disease"
    disease_col = next((c for c in df.columns if c.strip().lower() == "disease"), None)
    if disease_col is None:
        raise ValueError(
            f"Couldn't find a 'Disease' column automatically. "
            f"Found columns: {list(df.columns)}. "
            f"Update disease_col in this script manually."
        )

    # Every other column is treated as a "Symptom_N" slot holding a symptom name
    symptom_slot_cols = [c for c in df.columns if c != disease_col]

    # Collect the full universe of unique symptom names across all slot columns
    all_symptoms = set()
    for col in symptom_slot_cols:
        for val in df[col].dropna():
            all_symptoms.add(clean_symptom_name(val))
    all_symptoms = sorted(all_symptoms)
    print(f"Found {len(all_symptoms)} unique symptoms across the dataset.")

    # Build one-hot rows: for each patient row, mark 1 for every symptom
    # that appears in ANY of their Symptom_1..Symptom_17 slots
    rows = []
    for _, record in df.iterrows():
        present = set()
        for col in symptom_slot_cols:
            val = record[col]
            if pd.notna(val):
                present.add(clean_symptom_name(val))

        row = {symptom: (1 if symptom in present else 0) for symptom in all_symptoms}
        row["disease"] = str(record[disease_col]).strip()
        rows.append(row)

    out_df = pd.DataFrame(rows)
    os.makedirs("data", exist_ok=True)
    out_df.to_csv(OUTPUT_PATH, index=False)

    print(f"\nConverted dataset saved to {OUTPUT_PATH}")
    print(f"Shape: {out_df.shape[0]} rows, {out_df.shape[1] - 1} symptom columns, "
          f"{out_df['disease'].nunique()} unique diseases")


if __name__ == "__main__":
    main()