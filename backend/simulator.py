"""
Data simulator for demo/testing purposes.
Generates realistic CT sensor readings and seeds the database
with sample consumers and readings.
"""

import random
import threading
import time
from datetime import datetime, timedelta
from backend.database import get_connection, release_connection
from backend.utils import is_theft_detected, THEFT_THRESHOLD


# ======================================================
# Sample Data
# ======================================================

SAMPLE_AREAS = [
    "Sector 12", "Sector 17", "Sector 22", "Old City",
    "Industrial Area", "Green Park", "Model Town",
    "Civil Lines", "Nehru Nagar", "Gandhi Road"
]

SAMPLE_NAMES = [
    "Rajesh Kumar", "Priya Sharma", "Amit Patel", "Sunita Devi",
    "Mohammad Ali", "Lakshmi Narayan", "Vikram Singh", "Anita Gupta",
    "Suresh Reddy", "Meena Kumari", "Ravi Shankar", "Deepa Joshi",
    "Ashok Verma", "Kavita Mishra", "Manish Tiwari", "Pooja Yadav",
    "Ramesh Chandra", "Sarita Pandey", "Gopal Krishna", "Neha Agarwal"
]


# ======================================================
# Seed Database with Sample Consumers
# ======================================================

def seed_consumers(count=20):
    """Insert sample consumers into the database."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Check if consumers already exist
        cur.execute("SELECT COUNT(*) FROM consumers")
        existing = cur.fetchone()[0]

        if existing >= count:
            print(f"[INFO] {existing} consumers already exist, skipping seed")
            return existing

        names = SAMPLE_NAMES[:count]

        for i, name in enumerate(names):
            cons_no = f"CONS-{1001 + i}"
            area = random.choice(SAMPLE_AREAS)
            meter_id = f"MTR-{random.randint(10000, 99999)}"
            phone = f"+91-{random.randint(7000000000, 9999999999)}"
            address = f"House {random.randint(1, 500)}, {area}"
            # Mark some consumers as suspicious for demo
            status = "suspicious" if i % 5 == 0 else "normal"

            cur.execute(
                """
                INSERT INTO consumers (cons_no, name, address, area, meter_id, phone, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (cons_no) DO NOTHING
                """,
                (cons_no, name, address, area, meter_id, phone, status)
            )

        conn.commit()
        print(f"[OK] Seeded {count} sample consumers")
        return count

    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Failed to seed consumers: {e}")
        return 0
    finally:
        cur.close()
        release_connection(conn)



# ======================================================
# Generate Sensor Readings
# ======================================================

def generate_reading(consumer_id, is_theft=False):
    """Generate a single realistic sensor reading."""
    if is_theft:
        # Theft scenario: I_in is significantly higher than I_out
        i_in = round(random.uniform(10.0, 25.0), 2)
        # Current is being tapped, so I_out is much lower
        i_out = round(i_in - random.uniform(3.0, 12.0), 2)
        i_out = max(i_out, 0.5)  # Minimum reading
    else:
        # Normal scenario: I_in ≈ I_out (small natural difference)
        i_in = round(random.uniform(2.0, 15.0), 2)
        i_out = round(i_in - random.uniform(-0.3, 0.5), 2)
        i_out = max(i_out, 0.1)

    difference = round(abs(i_in - i_out), 2)
    voltage = round(random.uniform(220.0, 240.0), 1)
    power = round(i_out * voltage, 2)
    theft_detected = is_theft_detected(i_in, i_out)

    return {
        "consumer_id": consumer_id,
        "i_in": i_in,
        "i_out": i_out,
        "difference": difference,
        "voltage": voltage,
        "power": power,
        "is_theft": theft_detected
    }


# ======================================================
# Seed Historical Readings
# ======================================================

def seed_readings(days=7):
    """Generate historical sensor readings for all consumers."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Check if readings already exist
        cur.execute("SELECT COUNT(*) FROM sensor_readings")
        existing = cur.fetchone()[0]

        if existing > 100:
            print(f"[INFO] {existing} readings already exist, skipping seed")
            return existing

        # Get all consumers
        cur.execute("SELECT id, status FROM consumers")
        consumers = cur.fetchall()

        if not consumers:
            print("[WARN] No consumers found, seed consumers first")
            return 0

        now = datetime.now()
        readings_count = 0

        for consumer_id, status in consumers:
            is_thief = status == "suspicious"

            # Generate readings for each day
            for day in range(days):
                # 4-8 readings per day
                readings_per_day = random.randint(4, 8)

                for _ in range(readings_per_day):
                    timestamp = now - timedelta(
                        days=day,
                        hours=random.randint(0, 23),
                        minutes=random.randint(0, 59)
                    )

                    # Theft consumers have ~70% theft readings
                    if is_thief:
                        reading = generate_reading(
                            consumer_id,
                            is_theft=random.random() < 0.7
                        )
                    else:
                        reading = generate_reading(
                            consumer_id,
                            is_theft=random.random() < 0.05
                        )

                    cur.execute(
                        """
                        INSERT INTO sensor_readings
                        (consumer_id, i_in, i_out, difference, voltage, power, is_theft, timestamp)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            reading["consumer_id"],
                            reading["i_in"],
                            reading["i_out"],
                            reading["difference"],
                            reading["voltage"],
                            reading["power"],
                            reading["is_theft"],
                            timestamp
                        )
                    )
                    readings_count += 1

                    # Create alert for theft readings
                    if reading["is_theft"]:
                        severity = "critical" if reading["difference"] > 8 else "warning"
                        cur.execute(
                            """
                            INSERT INTO alerts
                            (consumer_id, alert_type, severity, message, i_in, i_out, difference, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """,
                            (
                                consumer_id,
                                "theft_detected",
                                severity,
                                f"Suspicious current difference of {reading['difference']}A detected. "
                                f"I_in={reading['i_in']}A, I_out={reading['i_out']}A",
                                reading["i_in"],
                                reading["i_out"],
                                reading["difference"],
                                timestamp
                            )
                        )

        conn.commit()
        print(f"[OK] Seeded {readings_count} sensor readings with alerts")
        return readings_count

    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Failed to seed readings: {e}")
        return 0
    finally:
        cur.close()
        release_connection(conn)



# ======================================================
# Background Simulator Thread
# ======================================================

simulator_running = False
simulator_thread = None


def start_simulator(interval=10):
    """Start background thread that continuously generates sensor data."""
    global simulator_running, simulator_thread

    if simulator_running:
        print("ℹ️  Simulator already running")
        return

    simulator_running = True

    def simulate():
        while simulator_running:
            try:
                conn = get_connection()
                cur = conn.cursor()

                # Get random consumer
                cur.execute(
                    "SELECT id, status FROM consumers ORDER BY RANDOM() LIMIT 3"
                )
                consumers = cur.fetchall()

                for consumer_id, status in consumers:
                    is_thief = status == "suspicious"
                    reading = generate_reading(
                        consumer_id,
                        is_theft=is_thief and random.random() < 0.6
                    )

                    cur.execute(
                        """
                        INSERT INTO sensor_readings
                        (consumer_id, i_in, i_out, difference, voltage, power, is_theft)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            reading["consumer_id"],
                            reading["i_in"],
                            reading["i_out"],
                            reading["difference"],
                            reading["voltage"],
                            reading["power"],
                            reading["is_theft"]
                        )
                    )

                    if reading["is_theft"]:
                        severity = "critical" if reading["difference"] > 8 else "warning"
                        cur.execute(
                            """
                            INSERT INTO alerts
                            (consumer_id, alert_type, severity, message, i_in, i_out, difference)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """,
                            (
                                consumer_id,
                                "theft_detected",
                                severity,
                                f"⚡ Live: Current difference of {reading['difference']}A detected. "
                                f"I_in={reading['i_in']}A, I_out={reading['i_out']}A",
                                reading["i_in"],
                                reading["i_out"],
                                reading["difference"]
                            )
                        )

                conn.commit()
                cur.close()
                release_connection(conn)

            except Exception as e:
                print(f"Simulator error: {e}")

            time.sleep(interval)

    simulator_thread = threading.Thread(target=simulate, daemon=True)
    simulator_thread.start()
    print(f"[OK] Background simulator started (interval: {interval}s)")


def stop_simulator():
    """Stop the background simulator."""
    global simulator_running
    simulator_running = False
    print("[STOP] Simulator stopped")


# ======================================================
# Seed All Demo Data
# ======================================================

def seed_all():
    """Seed all demo data."""
    print("\n" + "=" * 50)
    print("SEEDING DEMO DATA")
    print("=" * 50)
    seed_consumers(20)
    seed_readings(7)
    print("=" * 50 + "\n")
