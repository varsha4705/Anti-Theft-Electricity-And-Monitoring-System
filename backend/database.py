import os
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv

# Load .env file
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Connection pool
connection_pool = None


def init_pool():
    """Initialize connection pool."""
    global connection_pool
    try:
        connection_pool = pool.SimpleConnectionPool(
            1, 10,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        print("[OK] Database connection pool created")
    except Exception as e:
        print(f"[ERROR] Failed to create connection pool: {e}")
        raise



def get_connection():
    """Get a connection from the pool."""
    global connection_pool
    if connection_pool is None:
        init_pool()
    return connection_pool.getconn()


def release_connection(conn):
    """Return a connection to the pool."""
    global connection_pool
    if connection_pool and conn:
        connection_pool.putconn(conn)


def init_db():
    """Create all required tables if they don't exist."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Migration: Ensure column 'password_hash' exists (rename from legacy 'password' if needed)
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='password';
        """)
        if cur.fetchone():
            cur.execute("ALTER TABLE users RENAME COLUMN password TO password_hash;")

        # ============================================
        # Users table
        # ============================================
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                full_name VARCHAR(100) NOT NULL,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'admin',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # ============================================
        # Consumers table
        # ============================================
        cur.execute("""
            CREATE TABLE IF NOT EXISTS consumers (
                id SERIAL PRIMARY KEY,
                cons_no VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                address TEXT,
                area VARCHAR(100),
                meter_id VARCHAR(50),
                phone VARCHAR(20),
                status VARCHAR(20) DEFAULT 'normal',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # ============================================
        # Sensor readings table
        # ============================================
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id SERIAL PRIMARY KEY,
                consumer_id INTEGER REFERENCES consumers(id) ON DELETE CASCADE,
                i_in FLOAT NOT NULL,
                i_out FLOAT NOT NULL,
                difference FLOAT NOT NULL,
                voltage FLOAT DEFAULT 230.0,
                power FLOAT,
                is_theft BOOLEAN DEFAULT FALSE,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # ============================================
        # Alerts table
        # ============================================
        cur.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id SERIAL PRIMARY KEY,
                consumer_id INTEGER REFERENCES consumers(id) ON DELETE CASCADE,
                alert_type VARCHAR(50) NOT NULL,
                severity VARCHAR(20) DEFAULT 'warning',
                message TEXT NOT NULL,
                i_in FLOAT,
                i_out FLOAT,
                difference FLOAT,
                is_read BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # ============================================
        # Predictions table
        # ============================================
        cur.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id SERIAL PRIMARY KEY,
                consumer_id INTEGER REFERENCES consumers(id) ON DELETE SET NULL,
                prediction INTEGER NOT NULL,
                confidence FLOAT NOT NULL,
                input_data JSONB,
                model_version VARCHAR(50) DEFAULT 'v1.0',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # ============================================
        # Create indexes for performance
        # ============================================
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_sensor_readings_consumer
            ON sensor_readings(consumer_id);
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_sensor_readings_timestamp
            ON sensor_readings(timestamp);
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_alerts_consumer
            ON alerts(consumer_id);
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_alerts_is_read
            ON alerts(is_read);
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_predictions_consumer
            ON predictions(consumer_id);
        """)

        conn.commit()
        print("[OK] All database tables created successfully")

    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Failed to create tables: {e}")
        raise
    finally:
        cur.close()
        release_connection(conn)