import os
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

from preprocess import preprocess_data

# ==========================================================
# Dataset Path
# ==========================================================

DATASET_PATH = r"C:\Users\Dell\OneDrive\Desktop\Anti_Theft_Electricity_Monitoring_System\datasets\data set.csv"

print("=" * 60)
print("ANTI THEFT ELECTRICITY MONITORING SYSTEM")
print("=" * 60)

print("\nLoading Dataset...")

df = preprocess_data(DATASET_PATH)

print("Dataset Loaded Successfully")
print("Dataset Shape :", df.shape)

# ==========================================================
# Target Column
# ==========================================================

TARGET = "FLAG"

# Remove Consumer Number from features
if "CONS_NO" in df.columns:
    X = df.drop(columns=["CONS_NO", TARGET])
else:
    X = df.drop(columns=[TARGET])

y = df[TARGET]

print("\nNumber of Features :", X.shape[1])

# ==========================================================
# Encode Categorical Columns
# ==========================================================

print("\nEncoding Categorical Columns...")

feature_encoders = {}

for col in X.columns:

    if X[col].dtype == "object":

        encoder = LabelEncoder()

        X[col] = encoder.fit_transform(X[col].astype(str))

        feature_encoders[col] = encoder

# ==========================================================
# Encode Target
# ==========================================================

target_encoder = LabelEncoder()

y = target_encoder.fit_transform(y.astype(str))

# ==========================================================
# Train Test Split
# ==========================================================

print("\nSplitting Dataset...")

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("Training Samples :", len(X_train))
print("Testing Samples  :", len(X_test))

# ==========================================================
# Build Model
# ==========================================================

print("\nTraining Random Forest Model...")

model = RandomForestClassifier(

    n_estimators=50,

    max_depth=20,

    random_state=42,

    n_jobs=-1

)

model.fit(X_train, y_train)

print("Training Completed Successfully!")

# ==========================================================
# Evaluate Model
# ==========================================================

print("\nEvaluating Model...")

prediction = model.predict(X_test)

accuracy = accuracy_score(y_test, prediction)

print("\nAccuracy : {:.2f}%".format(accuracy * 100))

print("\nClassification Report\n")

print(classification_report(y_test, prediction))

# ==========================================================
# Feature Importance
# ==========================================================

importance = pd.DataFrame({

    "Feature": X.columns,

    "Importance": model.feature_importances_

})

importance = importance.sort_values(
    by="Importance",
    ascending=False
)

print("\nTop 10 Important Features\n")

print(importance.head(10))

# ==========================================================
# Save Model
# ==========================================================

MODEL_FOLDER = r"C:\Users\Dell\OneDrive\Desktop\Anti_Theft_Electricity_Monitoring_System\models"

os.makedirs(MODEL_FOLDER, exist_ok=True)

joblib.dump(
    model,
    os.path.join(MODEL_FOLDER, "random_forest.pkl")
)

joblib.dump(
    target_encoder,
    os.path.join(MODEL_FOLDER, "label_encoder.pkl")
)

joblib.dump(
    feature_encoders,
    os.path.join(MODEL_FOLDER, "feature_encoders.pkl")
)

joblib.dump(
    list(X.columns),
    os.path.join(MODEL_FOLDER, "feature_columns.pkl")
)

print("\nModel Saved Successfully!")

print("\nGenerated Files")

print("-------------------------------------")
print("random_forest.pkl")
print("label_encoder.pkl")
print("feature_encoders.pkl")
print("feature_columns.pkl")
print("-------------------------------------")

print("\nProject Training Completed Successfully!")