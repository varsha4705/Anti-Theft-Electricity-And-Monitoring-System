from database import get_connection

try:
    conn = get_connection()
    print("[OK] Database Connected Successfully!")
    conn.close()
except Exception as e:
    print("[ERROR] Connection Failed:")
    print(e)