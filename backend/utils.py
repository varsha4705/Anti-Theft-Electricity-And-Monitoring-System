import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Theft detection threshold (in Amps)
THEFT_THRESHOLD = float(os.getenv("THEFT_THRESHOLD", "2.0"))


def current_time():
    """Return formatted current timestamp."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def is_theft_detected(i_in, i_out, threshold=None):
    """
    Check if the difference between incoming and outgoing
    current exceeds the theft threshold.
    """
    if threshold is None:
        threshold = THEFT_THRESHOLD

    difference = abs(i_in - i_out)
    return difference > threshold


def calculate_power(current, voltage=230.0):
    """Calculate power in watts."""
    return round(current * voltage, 2)


def format_consumer(row):
    """Format a consumer database row to dictionary."""
    return {
        "id": row[0],
        "cons_no": row[1],
        "name": row[2],
        "address": row[3],
        "area": row[4],
        "meter_id": row[5],
        "phone": row[6],
        "status": row[7],
        "created_at": str(row[8]) if row[8] else None
    }


def format_sensor_reading(row):
    """Format a sensor reading database row to dictionary."""
    return {
        "id": row[0],
        "consumer_id": row[1],
        "i_in": row[2],
        "i_out": row[3],
        "difference": row[4],
        "voltage": row[5],
        "power": row[6],
        "is_theft": row[7],
        "timestamp": str(row[8]) if row[8] else None
    }


def format_alert(row):
    """Format an alert database row to dictionary."""
    return {
        "id": row[0],
        "consumer_id": row[1],
        "alert_type": row[2],
        "severity": row[3],
        "message": row[4],
        "i_in": row[5],
        "i_out": row[6],
        "difference": row[7],
        "is_read": row[8],
        "created_at": str(row[9]) if row[9] else None
    }


def format_prediction(row):
    """Format a prediction database row to dictionary."""
    return {
        "id": row[0],
        "consumer_id": row[1],
        "prediction": row[2],
        "confidence": row[3],
        "input_data": row[4],
        "model_version": row[5],
        "created_at": str(row[6]) if row[6] else None
    }