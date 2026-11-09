import os
import datetime
import importlib
from functools import wraps
from flask import request, jsonify
from dotenv import load_dotenv
from backend.database import get_connection, release_connection

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "AntiTheft2026")

try:
    jwt = importlib.import_module("jwt")
except ImportError:
    jwt = None

try:
    flask_bcrypt = importlib.import_module("flask_bcrypt")
    bcrypt = flask_bcrypt.Bcrypt()
except ImportError:
    bcrypt = None



def init_bcrypt(app):
    """Initialize bcrypt with Flask app."""
    if bcrypt:
        bcrypt.init_app(app)



# ======================================================
# User Registration
# ======================================================

def register_user(full_name, username, email, password):
    """Register a new user with hashed password."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Check if username or email already exists
        cur.execute(
            "SELECT id FROM users WHERE username=%s OR email=%s",
            (username, email)
        )
        if cur.fetchone():
            return None, "Username or email already exists"

        # Hash password
        if bcrypt:
            password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
        else:
            import hashlib
            password_hash = hashlib.sha256(password.encode()).hexdigest()

        cur.execute(
            """
            INSERT INTO users (full_name, username, email, password_hash)
            VALUES (%s, %s, %s, %s)
            RETURNING id, full_name, username, email, role, created_at
            """,
            (full_name, username, email, password_hash)
        )

        user = cur.fetchone()
        conn.commit()

        return {
            "id": user[0],
            "full_name": user[1],
            "username": user[2],
            "email": user[3],
            "role": user[4],
            "created_at": str(user[5])
        }, None

    except Exception as e:
        conn.rollback()
        return None, str(e)
    finally:
        cur.close()
        release_connection(conn)


# ======================================================
# User Login
# ======================================================

def login_user(username, password):
    """Authenticate user and return JWT token."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT id, full_name, username, email, password_hash, role
            FROM users
            WHERE LOWER(username) = LOWER(%s) OR LOWER(email) = LOWER(%s)
            """,
            (username, username)
        )

        user = cur.fetchone()

        if not user:
            return None, "Invalid username or password"

        # Verify password (support bcrypt, sha256, and legacy plaintext)
        stored_hash = user[4]
        valid = False

        if bcrypt and (stored_hash.startswith("$2b$") or stored_hash.startswith("$2a$")):
            try:
                valid = bcrypt.check_password_hash(stored_hash, password)
            except Exception:
                valid = False

        if not valid:
            import hashlib
            sha256_hash = hashlib.sha256(password.encode()).hexdigest()
            if stored_hash == password or stored_hash == sha256_hash:
                valid = True
                # Automatically upgrade legacy/plaintext password to bcrypt hash
                if bcrypt:
                    try:
                        new_hash = bcrypt.generate_password_hash(password).decode("utf-8")
                        cur.execute("UPDATE users SET password_hash=%s WHERE id=%s", (new_hash, user[0]))
                        conn.commit()
                    except Exception:
                        conn.rollback()

        if not valid:
            return None, "Invalid username or password"

        # Generate JWT token
        if jwt:
            token = jwt.encode(
                {
                    "user_id": user[0],
                    "username": user[2],
                    "role": user[5],
                    "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
                },
                SECRET_KEY,
                algorithm="HS256"
            )
        else:
            token = f"demo-token-{user[0]}-{user[2]}"

        return {
            "token": token,
            "user": {
                "id": user[0],
                "full_name": user[1],
                "username": user[2],
                "email": user[3],
                "role": user[5]
            }
        }, None

    except Exception as e:
        return None, str(e)
    finally:
        cur.close()
        release_connection(conn)


# ======================================================
# Token Verification Decorator
# ======================================================

def token_required(f):
    """Decorator to protect routes with JWT authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Get token from header
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

        if not token:
            return jsonify({
                "status": "error",
                "message": "Authentication token is missing"
            }), 401

        try:
            if jwt:
                data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
                request.user_id = data["user_id"]
                request.username = data["username"]
                request.user_role = data["role"]
            else:
                # Fallback token parsing
                parts = token.split("-")
                request.user_id = int(parts[2]) if len(parts) > 2 else 1
                request.username = parts[3] if len(parts) > 3 else "admin"
                request.user_role = "admin"
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Invalid or expired token: {e}"
            }), 401

        return f(*args, **kwargs)
    return decorated



# ======================================================
# Get User Profile
# ======================================================

def get_user_profile(user_id):
    """Get user profile by ID."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT id, full_name, username, email, role, created_at
            FROM users
            WHERE id=%s
            """,
            (user_id,)
        )

        user = cur.fetchone()
        if not user:
            return None

        return {
            "id": user[0],
            "full_name": user[1],
            "username": user[2],
            "email": user[3],
            "role": user[4],
            "created_at": str(user[5])
        }

    finally:
        cur.close()
        release_connection(conn)