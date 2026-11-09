import pandas as pd


def preprocess_data(file_path):
    """
    Load and preprocess the electricity theft dataset.
    """

    # Load dataset
    df = pd.read_csv(file_path)

    print("Dataset Loaded Successfully")
    print("Original Shape :", df.shape)

    # -----------------------------------------
    # Remove duplicate rows
    # -----------------------------------------

    df = df.drop_duplicates()

    # -----------------------------------------
    # Fill missing values
    # -----------------------------------------

    numeric_cols = df.select_dtypes(include=["number"]).columns

    df[numeric_cols] = df[numeric_cols].fillna(
        df[numeric_cols].mean()
    )

    categorical_cols = df.select_dtypes(include=["object"]).columns

    for col in categorical_cols:
        mode_value = df[col].mode()

        if not mode_value.empty:
            df[col] = df[col].fillna(mode_value[0])

    # -----------------------------------------
    # Remove completely empty columns
    # -----------------------------------------

    df = df.dropna(axis=1, how="all")

    # -----------------------------------------
    # Remove completely empty rows
    # -----------------------------------------

    df = df.dropna(axis=0, how="all")

    print("Processed Shape :", df.shape)

    return df


# =====================================================
# Run this file independently
# =====================================================

if __name__ == "__main__":

    DATASET_PATH = (
        r"C:\Users\Dell\OneDrive\Desktop"
        r"\Anti_Theft_Electricity_Monitoring_System"
        r"\datasets\data set.csv"
    )

    OUTPUT_PATH = (
        r"C:\Users\Dell\OneDrive\Desktop"
        r"\Anti_Theft_Electricity_Monitoring_System"
        r"\datasets\processed_data.csv"
    )

    processed_df = preprocess_data(DATASET_PATH)

    processed_df.to_csv(OUTPUT_PATH, index=False)

    print("\nDataset Preprocessed Successfully!")
    print("Saved to:", OUTPUT_PATH)