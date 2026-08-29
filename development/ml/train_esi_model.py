import pandas as pd
import joblib
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

DATA = "esi_training_data.csv"
MODEL_OUT = "esi_baseline_model.joblib"

NUMERIC = ["temperature","heartrate","resprate","o2sat","sbp","dbp","pain"]
CATEGORICAL = ["gender"]
TEXT = "chiefcomplaint"
TARGET = "acuity"

df = pd.read_csv(DATA).dropna(subset=[TARGET])
df[TARGET] = df[TARGET].astype(int)

X = df[NUMERIC + CATEGORICAL + [TEXT]]
y = df[TARGET]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42, stratify=y
)

preprocessor = ColumnTransformer([
    ("numeric", SimpleImputer(strategy="median"), NUMERIC),
    ("gender", Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore"))
    ]), CATEGORICAL),
    ("text", TfidfVectorizer(
        lowercase=True, ngram_range=(1,2), max_features=1000
    ), TEXT)
])

model = Pipeline([
    ("features", preprocessor),
    ("classifier", RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        class_weight="balanced",
        min_samples_leaf=2
    ))
])

model.fit(X_train, y_train)
pred = model.predict(X_test)

print("=" * 60)
print("PATIENTTRIAGE.AI - ESI BASELINE")
print("=" * 60)
print("Train samples:", len(X_train))
print("Test samples :", len(X_test))
print("Classes      :", sorted(y.unique()))
print("Accuracy     :", round(accuracy_score(y_test, pred), 3))
print("\nClassification report:")
print(classification_report(y_test, pred, zero_division=0))
print("Confusion matrix:")
print(confusion_matrix(y_test, pred))

joblib.dump(model, MODEL_OUT)
print("\nSaved:", MODEL_OUT)

probs = model.predict_proba(X_test)
classes = model.named_steps["classifier"].classes_
print("\nExample predictions:")
for i in range(min(5, len(X_test))):
    j = probs[i].argmax()
    print(
        f"predicted ESI={classes[j]}, "
        f"confidence={probs[i][j]:.3f}, "
        f"actual={y_test.iloc[i]}"
    )
