"""
All API routes organized as Flask Blueprints.
"""

import os
import json
import joblib
import pandas as pd
from flask import Blueprint, request, jsonify
from backend.database import get_connection, release_connection
from backend.authentication import (
    register_user, login_user, token_required, get_user_profile
)
from backend.utils import (
    is_theft_detected, calculate_power, THEFT_THRESHOLD,
    format_consumer, format_sensor_reading, format_alert, format_prediction
)

# ======================================================
# Blueprint
# ======================================================

api = Blueprint("api", __name__, url_prefix="/api")

# ======================================================
# Load ML Model
# ======================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models")

try:
    ml_model = joblib.load(os.path.join(MODEL_PATH, "random_forest.pkl"))
    label_encoder = joblib.load(os.path.join(MODEL_PATH, "label_encoder.pkl"))
    feature_columns = joblib.load(os.path.join(MODEL_PATH, "feature_columns.pkl"))
    feature_encoders = joblib.load(os.path.join(MODEL_PATH, "feature_encoders.pkl"))
    print("[OK] ML Model loaded successfully")
except Exception as e:
    print(f"[NOTE] ML Model not loaded: {e}")
    ml_model = None
    label_encoder = None
    feature_columns = None
    feature_encoders = None


# ╔══════════════════════════════════════════════════════╗
# ║                  AUTH ROUTES                         ║
# ╚══════════════════════════════════════════════════════╝

@api.route("/auth/register", methods=["POST"])
def api_register():
    """Register a new user."""
    data = request.get_json()

    required = ["full_name", "username", "email", "password"]
    for field in required:
        if field not in data or not data[field]:
            return jsonify({
                "status": "error",
                "message": f"'{field}' is required"
            }), 400

    user, error = register_user(
        data["full_name"], data["username"],
        data["email"], data["password"]
    )

    if error:
        return jsonify({"status": "error", "message": error}), 400

    return jsonify({"status": "success", "user": user}), 201


@api.route("/auth/login", methods=["POST"])
def api_login():
    """Login and get JWT token."""
    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({
            "status": "error",
            "message": "Username and password are required"
        }), 400

    result, error = login_user(username, password)

    if error:
        return jsonify({"status": "error", "message": error}), 401

    return jsonify({"status": "success", **result})


@api.route("/auth/profile", methods=["GET"])
@token_required
def api_profile():
    """Get current user profile."""
    user = get_user_profile(request.user_id)

    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    return jsonify({"status": "success", "user": user})


# ╔══════════════════════════════════════════════════════╗
# ║                DASHBOARD ROUTES                      ║
# ╚══════════════════════════════════════════════════════╝

@api.route("/dashboard/stats", methods=["GET"])
@token_required
def api_dashboard_stats():
    """Get dashboard statistics."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Total consumers
        cur.execute("SELECT COUNT(*) FROM consumers")
        total_consumers = cur.fetchone()[0]

        # Theft detected (unique consumers with theft readings in last 7 days)
        cur.execute("""
            SELECT COUNT(DISTINCT consumer_id)
            FROM sensor_readings
            WHERE is_theft = TRUE
            AND timestamp > NOW() - INTERVAL '7 days'
        """)
        theft_detected = cur.fetchone()[0]

        # Normal consumers
        normal_users = total_consumers - theft_detected

        # Total readings
        cur.execute("SELECT COUNT(*) FROM sensor_readings")
        total_readings = cur.fetchone()[0]

        # Unread alerts
        cur.execute("SELECT COUNT(*) FROM alerts WHERE is_read = FALSE")
        unread_alerts = cur.fetchone()[0]

        # Critical alerts
        cur.execute("""
            SELECT COUNT(*) FROM alerts
            WHERE severity = 'critical' AND is_read = FALSE
        """)
        critical_alerts = cur.fetchone()[0]

        # Recent alerts (last 5)
        cur.execute("""
            SELECT a.id, a.consumer_id, a.alert_type, a.severity, a.message,
                   a.i_in, a.i_out, a.difference, a.is_read, a.created_at,
                   c.name, c.cons_no
            FROM alerts a
            LEFT JOIN consumers c ON a.consumer_id = c.id
            ORDER BY a.created_at DESC
            LIMIT 5
        """)
        recent_alerts = []
        for row in cur.fetchall():
            alert = format_alert(row[:10])
            alert["consumer_name"] = row[10]
            alert["cons_no"] = row[11]
            recent_alerts.append(alert)

        return jsonify({
            "status": "success",
            "stats": {
                "total_consumers": total_consumers,
                "theft_detected": theft_detected,
                "normal_users": normal_users,
                "total_readings": total_readings,
                "unread_alerts": unread_alerts,
                "critical_alerts": critical_alerts,
                "model_accuracy": "97.8%",
                "threshold": THEFT_THRESHOLD
            },
            "recent_alerts": recent_alerts
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cur.close()
        release_connection(conn)


@api.route("/dashboard/chart-data", methods=["GET"])
@token_required
def api_chart_data():
    """Get chart data for dashboard visualizations."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Theft trend over last 7 days
        cur.execute("""
            SELECT DATE(timestamp) as day,
                   COUNT(*) FILTER (WHERE is_theft = TRUE) as theft_count,
                   COUNT(*) FILTER (WHERE is_theft = FALSE) as normal_count,
                   COUNT(*) as total_count
            FROM sensor_readings
            WHERE timestamp > NOW() - INTERVAL '7 days'
            GROUP BY DATE(timestamp)
            ORDER BY day
        """)
        daily_trends = []
        for row in cur.fetchall():
            daily_trends.append({
                "date": str(row[0]),
                "theft_count": row[1],
                "normal_count": row[2],
                "total_count": row[3]
            })

        # Theft by area
        cur.execute("""
            SELECT c.area, COUNT(*) as theft_count
            FROM sensor_readings sr
            JOIN consumers c ON sr.consumer_id = c.id
            WHERE sr.is_theft = TRUE
            AND sr.timestamp > NOW() - INTERVAL '7 days'
            GROUP BY c.area
            ORDER BY theft_count DESC
            LIMIT 10
        """)
        area_data = []
        for row in cur.fetchall():
            area_data.append({
                "area": row[0] if row[0] else "Unknown",
                "theft_count": row[1]
            })

        # Hourly distribution
        cur.execute("""
            SELECT EXTRACT(HOUR FROM timestamp) as hour,
                   COUNT(*) FILTER (WHERE is_theft = TRUE) as theft_count,
                   COUNT(*) as total_count
            FROM sensor_readings
            WHERE timestamp > NOW() - INTERVAL '7 days'
            GROUP BY hour
            ORDER BY hour
        """)
        hourly_data = []
        for row in cur.fetchall():
            hourly_data.append({
                "hour": int(row[0]),
                "theft_count": row[1],
                "total_count": row[2]
            })

        # Overall theft ratio
        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE is_theft = TRUE) as theft,
                COUNT(*) FILTER (WHERE is_theft = FALSE) as normal
            FROM sensor_readings
        """)
        ratio = cur.fetchone()
        theft_ratio = {
            "theft": ratio[0] if ratio[0] else 0,
            "normal": ratio[1] if ratio[1] else 0
        }

        return jsonify({
            "status": "success",
            "daily_trends": daily_trends,
            "area_data": area_data,
            "hourly_data": hourly_data,
            "theft_ratio": theft_ratio
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cur.close()
        release_connection(conn)


# ╔══════════════════════════════════════════════════════╗
# ║               CONSUMER ROUTES                        ║
# ╚══════════════════════════════════════════════════════╝

@api.route("/consumers", methods=["GET"])
@token_required
def api_get_consumers():
    """Get all consumers with optional filters."""
    area = request.args.get("area")
    status = request.args.get("status")
    search = request.args.get("search")

    conn = get_connection()
    cur = conn.cursor()

    try:
        query = "SELECT * FROM consumers WHERE 1=1"
        params = []

        if area:
            query += " AND area = %s"
            params.append(area)
        if status:
            query += " AND status = %s"
            params.append(status)
        if search:
            query += " AND (name ILIKE %s OR cons_no ILIKE %s OR area ILIKE %s)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])

        query += " ORDER BY created_at DESC"

        cur.execute(query, params)
        consumers = [format_consumer(row) for row in cur.fetchall()]

        return jsonify({"status": "success", "consumers": consumers})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cur.close()
        release_connection(conn)


@api.route("/consumers/<int:consumer_id>", methods=["GET"])
@token_required
def api_get_consumer(consumer_id):
    """Get a single consumer with recent readings."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT * FROM consumers WHERE id = %s", (consumer_id,))
        row = cur.fetchone()

        if not row:
            return jsonify({"status": "error", "message": "Consumer not found"}), 404

        consumer = format_consumer(row)

        # Get recent readings
        cur.execute("""
            SELECT * FROM sensor_readings
            WHERE consumer_id = %s
            ORDER BY timestamp DESC
            LIMIT 50
        """, (consumer_id,))
        readings = [format_sensor_reading(r) for r in cur.fetchall()]

        # Get recent alerts
        cur.execute("""
            SELECT * FROM alerts
            WHERE consumer_id = %s
            ORDER BY created_at DESC
            LIMIT 10
        """, (consumer_id,))
        alerts = [format_alert(r) for r in cur.fetchall()]

        consumer["readings"] = readings
        consumer["alerts"] = alerts

        return jsonify({"status": "success", "consumer": consumer})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cur.close()
        release_connection(conn)


@api.route("/consumers", methods=["POST"])
@token_required
def api_add_consumer():
    """Add a new consumer."""
    data = request.get_json()

    required = ["cons_no", "name"]
    for field in required:
        if field not in data or not data[field]:
            return jsonify({
                "status": "error",
                "message": f"'{field}' is required"
            }), 400

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO consumers (cons_no, name, address, area, meter_id, phone, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                data["cons_no"], data["name"],
                data.get("address", ""),
                data.get("area", ""),
                data.get("meter_id", ""),
                data.get("phone", ""),
                data.get("status", "normal")
            )
        )

        consumer = format_consumer(cur.fetchone())
        conn.commit()

        return jsonify({"status": "success", "consumer": consumer}), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400
    finally:
        cur.close()
        release_connection(conn)


@api.route("/consumers/<int:consumer_id>", methods=["PUT"])
@token_required
def api_update_consumer(consumer_id):
    """Update a consumer."""
    data = request.get_json()

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            UPDATE consumers
            SET name = COALESCE(%s, name),
                address = COALESCE(%s, address),
                area = COALESCE(%s, area),
                meter_id = COALESCE(%s, meter_id),
                phone = COALESCE(%s, phone),
                status = COALESCE(%s, status)
            WHERE id = %s
            RETURNING *
            """,
            (
                data.get("name"), data.get("address"),
                data.get("area"), data.get("meter_id"),
                data.get("phone"), data.get("status"),
                consumer_id
            )
        )

        row = cur.fetchone()
        if not row:
            return jsonify({"status": "error", "message": "Consumer not found"}), 404

        consumer = format_consumer(row)
        conn.commit()

        return jsonify({"status": "success", "consumer": consumer})

    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400
    finally:
        cur.close()
        release_connection(conn)


@api.route("/consumers/<int:consumer_id>", methods=["DELETE"])
@token_required
def api_delete_consumer(consumer_id):
    """Delete a consumer."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("DELETE FROM consumers WHERE id = %s RETURNING id", (consumer_id,))
        row = cur.fetchone()

        if not row:
            return jsonify({"status": "error", "message": "Consumer not found"}), 404

        conn.commit()
        return jsonify({"status": "success", "message": "Consumer deleted"})

    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400
    finally:
        cur.close()
        release_connection(conn)


# ╔══════════════════════════════════════════════════════╗
# ║              SENSOR DATA ROUTES                      ║
# ╚══════════════════════════════════════════════════════╝

@api.route("/sensor/data", methods=["POST"])
def api_sensor_data():
    """
    Receive sensor data from ESP32.
    No auth required — ESP32 posts directly.
    """
    data = request.get_json()

    required = ["consumer_id", "i_in", "i_out"]
    for field in required:
        if field not in data:
            return jsonify({
                "status": "error",
                "message": f"'{field}' is required"
            }), 400

    consumer_id = data["consumer_id"]
    i_in = float(data["i_in"])
    i_out = float(data["i_out"])
    voltage = float(data.get("voltage", 230.0))

    difference = round(abs(i_in - i_out), 2)
    power = calculate_power(i_out, voltage)
    theft = is_theft_detected(i_in, i_out)

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Insert reading
        cur.execute(
            """
            INSERT INTO sensor_readings
            (consumer_id, i_in, i_out, difference, voltage, power, is_theft)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (consumer_id, i_in, i_out, difference, voltage, power, theft)
        )
        reading_id = cur.fetchone()[0]

        # Create alert if theft detected
        if theft:
            severity = "critical" if difference > 8 else "warning"
            cur.execute(
                """
                INSERT INTO alerts
                (consumer_id, alert_type, severity, message, i_in, i_out, difference)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    consumer_id, "theft_detected", severity,
                    f"Current difference of {difference}A detected. "
                    f"I_in={i_in}A, I_out={i_out}A. Threshold={THEFT_THRESHOLD}A",
                    i_in, i_out, difference
                )
            )

            # Update consumer status
            cur.execute(
                "UPDATE consumers SET status = 'suspicious' WHERE id = %s",
                (consumer_id,)
            )

        conn.commit()

        return jsonify({
            "status": "success",
            "reading_id": reading_id,
            "is_theft": theft,
            "difference": difference,
            "threshold": THEFT_THRESHOLD
        })

    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400
    finally:
        cur.close()
        release_connection(conn)


@api.route("/sensor/readings/<int:consumer_id>", methods=["GET"])
@token_required
def api_sensor_readings(consumer_id):
    """Get sensor reading history for a consumer."""
    limit = request.args.get("limit", 100, type=int)

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT * FROM sensor_readings
            WHERE consumer_id = %s
            ORDER BY timestamp DESC
            LIMIT %s
        """, (consumer_id, limit))

        readings = [format_sensor_reading(r) for r in cur.fetchall()]

        return jsonify({"status": "success", "readings": readings})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cur.close()
        release_connection(conn)


@api.route("/sensor/live", methods=["GET"])
@token_required
def api_sensor_live():
    """Get latest reading for each consumer."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT DISTINCT ON (sr.consumer_id)
                sr.id, sr.consumer_id, sr.i_in, sr.i_out, sr.difference,
                sr.voltage, sr.power, sr.is_theft, sr.timestamp,
                c.name, c.cons_no, c.area, c.status
            FROM sensor_readings sr
            JOIN consumers c ON sr.consumer_id = c.id
            ORDER BY sr.consumer_id, sr.timestamp DESC
        """)

        live_data = []
        for row in cur.fetchall():
            reading = format_sensor_reading(row[:9])
            reading["consumer_name"] = row[9]
            reading["cons_no"] = row[10]
            reading["area"] = row[11]
            reading["consumer_status"] = row[12]
            live_data.append(reading)

        return jsonify({"status": "success", "live_data": live_data})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cur.close()
        release_connection(conn)


# ╔══════════════════════════════════════════════════════╗
# ║              PREDICTION ROUTES                       ║
# ╚══════════════════════════════════════════════════════╝

@api.route("/predict/single", methods=["POST"])
@token_required
def api_predict_single():
    """Predict theft for a single consumer record."""
    if ml_model is None:
        return jsonify({
            "status": "error",
            "message": "ML model not loaded"
        }), 500

    try:
        data = request.get_json()

        df = pd.DataFrame([data])

        # Remove unwanted columns
        df = df.drop(columns=["CONS_NO"], errors="ignore")

        # Encode categorical columns
        for col, encoder in feature_encoders.items():
            if col in df.columns:
                df[col] = encoder.transform(df[col].astype(str))

        # Ensure correct column order
        df = df.reindex(columns=feature_columns, fill_value=0)

        # Prediction
        prediction = ml_model.predict(df)[0]
        probability = max(ml_model.predict_proba(df)[0]) * 100
        result = label_encoder.inverse_transform([prediction])[0]

        # Save prediction if consumer_id provided
        consumer_id = data.get("consumer_id")
        if consumer_id:
            conn = get_connection()
            cur = conn.cursor()
            try:
                cur.execute(
                    """
                    INSERT INTO predictions (consumer_id, prediction, confidence, input_data)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (consumer_id, int(result), round(probability, 2),
                     json.dumps(data))
                )
                conn.commit()
            except Exception:
                conn.rollback()
            finally:
                cur.close()
                release_connection(conn)

        return jsonify({
            "status": "success",
            "prediction": int(result),
            "confidence": round(probability, 2),
            "label": "Theft Detected" if int(result) == 1 else "Normal"
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api.route("/predict/batch", methods=["POST"])
@token_required
def api_predict_batch():
    """Batch prediction from CSV file upload."""
    if ml_model is None:
        return jsonify({
            "status": "error",
            "message": "ML model not loaded"
        }), 500

    try:
        if "file" not in request.files:
            return jsonify({
                "status": "error",
                "message": "No file uploaded"
            }), 400

        file = request.files["file"]
        if not file.filename.endswith(".csv"):
            return jsonify({
                "status": "error",
                "message": "Only CSV files are supported"
            }), 400

        df = pd.read_csv(file)
        original_df = df.copy()

        # Remove unwanted columns
        df = df.drop(columns=["CONS_NO", "FLAG"], errors="ignore")

        # Encode categorical columns
        for col, encoder in feature_encoders.items():
            if col in df.columns:
                df[col] = encoder.transform(df[col].astype(str))

        # Ensure correct column order
        df = df.reindex(columns=feature_columns, fill_value=0)

        # Prediction
        predictions = ml_model.predict(df)
        probabilities = ml_model.predict_proba(df)

        results = []
        for i in range(len(predictions)):
            label = label_encoder.inverse_transform([predictions[i]])[0]
            confidence = round(max(probabilities[i]) * 100, 2)
            row_data = {
                "index": i,
                "prediction": int(label),
                "confidence": confidence,
                "label": "Theft Detected" if int(label) == 1 else "Normal"
            }
            if "CONS_NO" in original_df.columns:
                row_data["cons_no"] = str(original_df.iloc[i]["CONS_NO"])
            results.append(row_data)

        theft_count = sum(1 for r in results if r["prediction"] == 1)
        normal_count = len(results) - theft_count

        return jsonify({
            "status": "success",
            "total": len(results),
            "theft_count": theft_count,
            "normal_count": normal_count,
            "results": results
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api.route("/predict/history", methods=["GET"])
@token_required
def api_predict_history():
    """Get prediction history."""
    limit = request.args.get("limit", 50, type=int)

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT p.id, p.consumer_id, p.prediction, p.confidence,
                   p.input_data, p.model_version, p.created_at,
                   c.name, c.cons_no
            FROM predictions p
            LEFT JOIN consumers c ON p.consumer_id = c.id
            ORDER BY p.created_at DESC
            LIMIT %s
        """, (limit,))

        predictions = []
        for row in cur.fetchall():
            pred = format_prediction(row[:7])
            pred["consumer_name"] = row[7]
            pred["cons_no"] = row[8]
            predictions.append(pred)

        return jsonify({"status": "success", "predictions": predictions})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cur.close()
        release_connection(conn)


# ╔══════════════════════════════════════════════════════╗
# ║                ALERT ROUTES                          ║
# ╚══════════════════════════════════════════════════════╝

@api.route("/alerts", methods=["GET"])
@token_required
def api_get_alerts():
    """Get all alerts with optional filters."""
    severity = request.args.get("severity")
    is_read = request.args.get("is_read")
    limit = request.args.get("limit", 50, type=int)

    conn = get_connection()
    cur = conn.cursor()

    try:
        query = """
            SELECT a.id, a.consumer_id, a.alert_type, a.severity, a.message,
                   a.i_in, a.i_out, a.difference, a.is_read, a.created_at,
                   c.name, c.cons_no, c.area
            FROM alerts a
            LEFT JOIN consumers c ON a.consumer_id = c.id
            WHERE 1=1
        """
        params = []

        if severity:
            query += " AND a.severity = %s"
            params.append(severity)
        if is_read is not None:
            query += " AND a.is_read = %s"
            params.append(is_read.lower() == "true")

        query += " ORDER BY a.created_at DESC LIMIT %s"
        params.append(limit)

        cur.execute(query, params)

        alerts = []
        for row in cur.fetchall():
            alert = format_alert(row[:10])
            alert["consumer_name"] = row[10]
            alert["cons_no"] = row[11]
            alert["area"] = row[12]
            alerts.append(alert)

        return jsonify({"status": "success", "alerts": alerts})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cur.close()
        release_connection(conn)


@api.route("/alerts/<int:alert_id>/read", methods=["PUT"])
@token_required
def api_mark_alert_read(alert_id):
    """Mark an alert as read."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "UPDATE alerts SET is_read = TRUE WHERE id = %s RETURNING id",
            (alert_id,)
        )
        row = cur.fetchone()

        if not row:
            return jsonify({"status": "error", "message": "Alert not found"}), 404

        conn.commit()
        return jsonify({"status": "success", "message": "Alert marked as read"})

    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400
    finally:
        cur.close()
        release_connection(conn)


@api.route("/alerts/read-all", methods=["PUT"])
@token_required
def api_mark_all_read():
    """Mark all alerts as read."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("UPDATE alerts SET is_read = TRUE WHERE is_read = FALSE")
        count = cur.rowcount
        conn.commit()
        return jsonify({
            "status": "success",
            "message": f"{count} alerts marked as read"
        })

    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400
    finally:
        cur.close()
        release_connection(conn)


@api.route("/alerts/count", methods=["GET"])
@token_required
def api_alert_count():
    """Get unread alert count."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT COUNT(*) FROM alerts WHERE is_read = FALSE")
        count = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*) FROM alerts
            WHERE is_read = FALSE AND severity = 'critical'
        """)
        critical = cur.fetchone()[0]

        return jsonify({
            "status": "success",
            "unread": count,
            "critical": critical
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cur.close()
        release_connection(conn)
