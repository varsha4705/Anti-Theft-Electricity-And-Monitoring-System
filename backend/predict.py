import os
import joblib
import pandas as pd

# ===========================================
# Load Saved Files
# ===========================================

MODEL_FOLDER = r"C:\Users\Dell\OneDrive\Desktop\Anti_Theft_Electricity_Monitoring_System\models"

model = joblib.load(os.path.join(MODEL_FOLDER, "random_forest.pkl"))

feature_columns = joblib.load(
    os.path.join(MODEL_FOLDER, "feature_columns.pkl")
)

label_encoder = joblib.load(
    os.path.join(MODEL_FOLDER, "label_encoder.pkl")
)

feature_encoders = joblib.load(
    os.path.join(MODEL_FOLDER, "feature_encoders.pkl")
)


# ===========================================
# Prediction Function
# ===========================================

def predict_theft(csv_path):

    df = pd.read_csv(csv_path)

    # Remove unwanted columns
    df = df.drop(columns=["CONS_NO", "FLAG"], errors="ignore")

    # Encode categorical columns
    for col, encoder in feature_encoders.items():

        if col in df.columns:
            df[col] = encoder.transform(df[col].astype(str))

    # Ensure correct column order
    df = df[feature_columns]

    # Prediction
    prediction = model.predict(df)

    probability = model.predict_proba(df)

    result = []

    for i in range(len(prediction)):

        label = label_encoder.inverse_transform([prediction[i]])[0]

        confidence = round(max(probability[i]) * 100, 2)

        result.append({

            "Prediction": int(label),

            "Confidence": confidence

        })

    return result


# ===========================================
# Test Prediction
# ===========================================

if __name__ == "__main__":

    DATASET = r"C:\Users\Dell\OneDrive\Desktop\Anti_Theft_Electricity_Monitoring_System\datasets\data set.csv"

    output = predict_theft(DATASET)

    print(output[:10])