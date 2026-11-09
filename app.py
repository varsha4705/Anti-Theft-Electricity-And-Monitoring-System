"""
Anti-Theft Electricity Monitoring System
Main Flask Application Entry Point
"""

import os
from flask import Flask, send_from_directory, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ======================================================
# Initialize Flask App
# ======================================================

app = Flask(
    __name__,
    static_folder="frontend",
    static_url_path=""
)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "AntiTheft2026")
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB upload limit

# Enable CORS (if available)
try:
    import importlib
    flask_cors = importlib.import_module("flask_cors")
    flask_cors.CORS(app)
except ImportError:
    print("[INFO] flask-cors not installed. CORS headers skipped.")


# ======================================================
# Initialize Extensions
# ======================================================

try:
    from backend.authentication import init_bcrypt
    init_bcrypt(app)
except Exception as e:
    print(f"[NOTE] Bcrypt init note: {e}")

# ======================================================
# Register Blueprints
# ======================================================

from backend.routes import api
app.register_blueprint(api)

# ======================================================
# Initialize Database
# ======================================================

try:
    from backend.database import init_db, init_pool
    init_pool()
    init_db()
    print("[OK] Database initialized")
except Exception as e:
    print(f"[NOTE] Database initialization note: {e}")
    print("   Note: Install PostgreSQL and configure .env for database features.")

# ======================================================
# Seed Demo Data (if enabled & DB working)
# ======================================================

if os.getenv("ENABLE_SIMULATOR", "true").lower() == "true":
    try:
        from backend.simulator import seed_all, start_simulator
        seed_all()
        start_simulator(interval=15)
    except Exception as e:
        print(f"[NOTE] Simulator start note: {e}")

# ======================================================
# Serve Frontend
# ======================================================

@app.route("/")
def serve_login():
    """Serve the login page."""
    return send_from_directory("frontend", "index.html")


@app.route("/<path:path>")
def serve_frontend(path):
    """Serve frontend static files."""
    file_path = os.path.join("frontend", path)
    if os.path.exists(file_path):
        return send_from_directory("frontend", path)
    return send_from_directory("frontend", "index.html")


# ======================================================
# Health Check
# ======================================================

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "success",
        "message": "Anti-Theft Electricity Monitoring System API Running",
        "version": "2.0.0"
    })


# ======================================================
# Run Server
# ======================================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "true").lower() == "true"

    print("\n" + "=" * 60)
    print("ANTI-THEFT ELECTRICITY MONITORING SYSTEM")
    print("=" * 60)
    print(f"Server: http://localhost:{port}")
    print(f"Dashboard: http://localhost:{port}/dashboard.html")
    print(f"API Docs: http://localhost:{port}/api/health")
    print("=" * 60 + "\n")

    app.run(host="0.0.0.0", port=port, debug=debug)