"""PatientTriage.ai - Integrated ESI Model Training (vitals-only ML features).

ML uses measured vitals + sex/gender + chief complaint. Age-specific threshold
logic remains in the independent VitalInterpreter/Safety Engine.

Supported ESI classes: 1, 2, 3 (current demo dataset has no 4/5 labels).
Development/demo model, not clinically validated.
"""
from pathlib import Path
import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

DATA_PATH = Path("esi_training_data.csv")
MODEL_PATH = Path("esi_integrated_model.joblib")

RAW_NUMERIC = ["temperature", "heartrate", "resprate", "o2sat", "sbp", "dbp", "pain"]
CATEGORICAL = ["gender"]
TEXT_COLUMN = "chiefcomplaint"
TARGET = "acuity"
FEATURE_COLUMNS = RAW_NUMERIC + CATEGORICAL + [TEXT_COLUMN]
SUPPORTED_ESI_CLASSES = [1, 2, 3]


def normalize_gender(value):
    if pd.isna(value):
        return "UNKNOWN"
    value = str(value).strip().lower()
    if value in {"m", "male", "man", "boy"}:
        return "M"
    if value in {"f", "female", "woman", "girl"}:
        return "F"
    return "UNKNOWN"


def main():
    print("=" * 70)
    print("PATIENTTRIAGE.AI - VITALS-ONLY ESI MODEL")
    print("=" * 70)

    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Could not find {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    print(f"\nOriginal rows: {len(df)}")
    print("Columns:", list(df.columns))

    required = set(FEATURE_COLUMNS + [TARGET])
    missing = required - set(df.columns)
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(sorted(missing)))

    df = df.dropna(subset=[TARGET]).copy()
    df[TARGET] = pd.to_numeric(df[TARGET], errors="coerce")
    df = df.dropna(subset=[TARGET]).copy()
    df[TARGET] = df[TARGET].astype(int)
    df = df[df[TARGET].isin(SUPPORTED_ESI_CLASSES)].copy()

    print(f"Labeled rows: {len(df)}")
    print("\nClass distribution:")
    print(df[TARGET].value_counts().sort_index())

    for col in RAW_NUMERIC:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # MIMIC-IV-ED demo triage temperatures are Fahrenheit; live API uses C.
    median_temp = df["temperature"].median()
    if pd.notna(median_temp) and median_temp > 45:
        print("\nConverting MIMIC temperature from Fahrenheit to Celsius...")
        df["temperature"] = (df["temperature"] - 32.0) * (5.0 / 9.0)
        temperature_source_unit = "F"
    else:
        print("\nTraining temperature already appears to be Celsius.")
        temperature_source_unit = "C"

    invalid_pain = df["pain"].notna() & ~df["pain"].between(0, 10)
    invalid_pain_count = int(invalid_pain.sum())
    if invalid_pain_count:
        print(f"Warning: {invalid_pain_count} pain values outside 0-10 will be treated as missing.")
        df.loc[invalid_pain, "pain"] = pd.NA

    df["gender"] = df["gender"].apply(normalize_gender)
    df[TEXT_COLUMN] = df[TEXT_COLUMN].fillna("").astype(str)

    X = df[FEATURE_COLUMNS].copy()
    y = df[TARGET].copy()

    print(f"\nTotal ML input features: {len(FEATURE_COLUMNS)}")
    for i, feature in enumerate(FEATURE_COLUMNS):
        print(f"  {i:2d}: {feature}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    print(f"\nTraining samples: {len(X_train)}")
    print(f"Testing samples:  {len(X_test)}")

    preprocessor = ColumnTransformer([
        ("numeric", SimpleImputer(strategy="median"), RAW_NUMERIC),
        ("gender", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore"))
        ]), CATEGORICAL),
        ("text", TfidfVectorizer(lowercase=True, ngram_range=(1, 2), max_features=1000), TEXT_COLUMN)
    ])

    classifier = RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        class_weight="balanced",
        min_samples_leaf=2
    )

    model = Pipeline([
        ("features", preprocessor),
        ("classifier", classifier)
    ])

    print("\nTraining model...")
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)
    accuracy = accuracy_score(y_test, predictions)

    print("\n" + "=" * 70)
    print("MODEL RESULTS")
    print("=" * 70)
    print(f"\nAccuracy: {accuracy:.3f}")
    print("\nClassification Report:")
    print(classification_report(y_test, predictions, zero_division=0))
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, predictions))

    classes = model.named_steps["classifier"].classes_
    print("\nExample test probabilities:")
    for i in range(min(10, len(X_test))):
        j = probabilities[i].argmax()
        print(f"  predicted ESI={classes[j]}, confidence={probabilities[i][j]:.3f}, actual={y_test.iloc[i]}")

    # Metadata for reproducibility and downstream checks.
    model.training_feature_columns = FEATURE_COLUMNS
    model.raw_numeric_columns = RAW_NUMERIC
    model.flag_columns = []
    model.training_age_available = False
    model.training_temperature_unit = "C"
    model.source_temperature_unit = temperature_source_unit
    model.invalid_pain_values_treated_as_missing = invalid_pain_count
    model.supported_esi_classes = SUPPORTED_ESI_CLASSES
    model.model_version_note = (
        "Development/demo model. ML uses measured vitals, gender, and chief complaint only. "
        "Age-specific clinical interpretation is handled independently by VitalInterpreter."
    )

    joblib.dump(model, MODEL_PATH)
    print(f"\nModel saved to:\n{MODEL_PATH.resolve()}")
    print("\nSaved metadata:")
    print("  training_age_available:", model.training_age_available)
    print("  source_temperature_unit:", model.source_temperature_unit)
    print("  training_temperature_unit:", model.training_temperature_unit)
    print("  invalid_pain_values_treated_as_missing:", model.invalid_pain_values_treated_as_missing)
    print("  supported_esi_classes:", model.supported_esi_classes)
    print("\nDONE!")


if __name__ == "__main__":
    main()
