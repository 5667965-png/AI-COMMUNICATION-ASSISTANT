import pandas as pd
import numpy as np
import os
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report


# ==========================================
# PATHS
# ==========================================

DATA_FILE = r"C:\communcation\backend\model\dataset\sign_landmarks.csv"

MODEL_DIR = r"C:\communcation\backend\model\trained_model"

MODEL_FILE = os.path.join(
    MODEL_DIR,
    "isl_sign_model.pkl"
)

LABEL_FILE = r"C:\communcation\backend\model\labels\labels.txt"


# ==========================================
# HEADER
# ==========================================

print("======================================")
print("   ADVANCED REAL ISL MODEL TRAINING")
print("======================================")
print()


# ==========================================
# CHECK DATASET
# ==========================================

if not os.path.exists(DATA_FILE):

    print("ERROR: Dataset CSV not found!")
    print(DATA_FILE)
    exit()


print("Loading normalized landmark dataset...")
print()


# ==========================================
# LOAD DATA
# ==========================================

df = pd.read_csv(DATA_FILE)


print("Dataset loaded successfully!")
print()

print(f"Total samples : {len(df)}")
print(f"Total columns : {len(df.columns)}")
print()


# ==========================================
# FEATURES + LABEL
# ==========================================

X = df.drop("label", axis=1)

y = df["label"]


X = X.values.astype(np.float32)
y = y.values


# ==========================================
# DATA CHECK
# ==========================================

if X.shape[1] != 63:

    print("ERROR: Expected 63 landmark features.")

    print(
        f"Found features: {X.shape[1]}"
    )

    exit()


print("Feature validation passed!")
print("63 normalized landmark features detected.")
print()


# ==========================================
# SIGN INFORMATION
# ==========================================

unique_labels = sorted(set(y))


print("Signs found:")
print()


for label in unique_labels:

    count = np.sum(y == label)

    print(
        f"{label:15} : {count}"
    )


print()

print(
    f"Total sign classes : {len(unique_labels)}"
)

print()


# ==========================================
# TRAIN / TEST SPLIT
# ==========================================

print("Creating training and validation sets...")
print()


X_train, X_test, y_train, y_test = train_test_split(

    X,
    y,

    test_size=0.20,

    random_state=42,

    stratify=y
)


print(
    f"Training samples : {len(X_train)}"
)

print(
    f"Testing samples  : {len(X_test)}"
)

print()


# ==========================================
# CREATE ADVANCED RANDOM FOREST
# ==========================================

print("Creating advanced Random Forest...")
print()


model = RandomForestClassifier(

    n_estimators=200,

    max_depth=24,

    min_samples_split=3,

    min_samples_leaf=1,

    max_features="sqrt",

    class_weight="balanced",

    random_state=42,

    n_jobs=-1
)


# ==========================================
# TRAIN MODEL
# ==========================================

print("======================================")
print(" TRAINING STARTED")
print("======================================")
print()

print("Please wait...")
print()


model.fit(
    X_train,
    y_train
)


print()
print("TRAINING COMPLETED!")
print()


# ==========================================
# PREDICTIONS
# ==========================================

print("Testing trained model...")
print()


predictions = model.predict(
    X_test
)


# ==========================================
# ACCURACY
# ==========================================

accuracy = accuracy_score(
    y_test,
    predictions
)


print("======================================")
print("        ADVANCED MODEL RESULTS")
print("======================================")
print()


print(
    f"Accuracy : {accuracy * 100:.2f}%"
)

print()


# ==========================================
# CLASSIFICATION REPORT
# ==========================================

print("Classification Report:")
print()


print(
    classification_report(
        y_test,
        predictions,
        zero_division=0
    )
)


# ==========================================
# MODEL DIRECTORY
# ==========================================

os.makedirs(
    MODEL_DIR,
    exist_ok=True
)


# ==========================================
# SAVE MODEL
# ==========================================

print()
print("Saving trained model...")
print()


joblib.dump(
    model,
    MODEL_FILE,
    compress=3
)


print("======================================")
print(" MODEL SAVED SUCCESSFULLY")
print("======================================")
print()

print("Model file:")
print(MODEL_FILE)

print()


# ==========================================
# SAVE LABELS
# ==========================================

os.makedirs(
    os.path.dirname(LABEL_FILE),
    exist_ok=True
)


with open(
    LABEL_FILE,
    "w",
    encoding="utf-8"
) as file:

    for label in unique_labels:

        file.write(
            str(label) + "\n"
        )


print("Labels saved successfully!")
print()

print("Label file:")
print(LABEL_FILE)

print()


# ==========================================
# FINAL
# ==========================================

print("======================================")
print("    ADVANCED REAL ISL MODEL READY")
print("======================================")
print()

print("Features:")
print(" - Wrist-relative landmarks")
print(" - Hand-size normalization")
print(" - Balanced Random Forest")
print(" - 200 trees")
print(" - Confidence probabilities")
print(" - Compressed model storage")
print()

print("Next step:")
print("Connect the normalized feature pipeline")
print("to the FastAPI camera prediction.")
print()