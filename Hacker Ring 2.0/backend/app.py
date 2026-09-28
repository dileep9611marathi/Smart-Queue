import os
import io
import json
import socket
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
import qrcode

from ai_assistant import VoiceQueueAssistant

app = Flask(__name__)
assistant = VoiceQueueAssistant()

# Database configuration
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "voicequeue.db")

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

DEFAULT_ORG_DATA = {
    "org_name": "VoiceQueue Service Center",
    "opening_hours": "Monday to Friday: 9:00 AM - 5:00 PM\nSaturday: 9:00 AM - 1:00 PM\nSunday: Closed",
    "counter_info": "Counter 1: Inquiries & Verification\nCounter 2: Payments & Document Submission\nCounter 3: Express Service & Pharmacy Pickup",
    "services": "Queue Token Issuance, Document Verification, Payments & Receipts, Certificate Collection",
    "faqs": json.dumps([
        {
            "question": "What documents do I need?",
            "answer": "Please bring a valid Government Photo ID and your service reference number or appointment slip."
        },
        {
            "question": "Where is the pharmacy?",
            "answer": "The pharmacy is located on the ground floor next to Counter 3."
        }
    ])
}

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create tokens table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token_number INTEGER NOT NULL,
            customer_name TEXT,
            status TEXT NOT NULL DEFAULT 'waiting', -- 'waiting', 'serving', 'completed', 'cancelled'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            served_at TIMESTAMP
        )
    """)
    
    # Create settings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('avg_service_time_mins', '5')")
    
    # Create organization_info table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS organization_info (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    
    for k, v in DEFAULT_ORG_DATA.items():
        cursor.execute("INSERT OR IGNORE INTO organization_info (key, value) VALUES (?, ?)", (k, v))
        
    conn.commit()
    conn.close()

def get_setting(key, default="5"):
    conn = get_db_connection()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    if row:
        return row["value"]
    return default

def set_setting(key, value):
    conn = get_db_connection()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

def get_org_info():
    conn = get_db_connection()
    rows = conn.execute("SELECT key, value FROM organization_info").fetchall()
    conn.close()
    info = {r["key"]: r["value"] for r in rows}
    
    # Parse FAQs if present
    if "faqs" in info and isinstance(info["faqs"], str):
        try:
            info["faqs"] = json.loads(info["faqs"])
        except Exception:
            info["faqs"] = []
    elif "faqs" not in info:
        info["faqs"] = []
        
    return info

def set_org_info(data):
    conn = get_db_connection()
    for k, v in data.items():
        if k == "faqs" and not isinstance(v, str):
            v = json.dumps(v)
        conn.execute("INSERT OR REPLACE INTO organization_info (key, value) VALUES (?, ?)", (k, str(v)))
    conn.commit()
    conn.close()

def get_currently_serving():
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM tokens WHERE status = 'serving' ORDER BY id ASC LIMIT 1").fetchone()
    conn.close()
    return dict(row) if row else None

def get_local_ip():
    """Detects the computer's local Wi-Fi / LAN IP address so phones on the same network can connect."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"

def calculate_token_stats(token_row, currently_serving, avg_service_time):
    """
    Calculates people ahead and estimated wait time for a given token.
    """
    token_number = token_row["token_number"]
    token_id = token_row["id"]
    status = token_row["status"]

    if status == "serving":
        return {
            "status": "serving",
            "people_ahead": 0,
            "estimated_wait_mins": 0,
            "message": "It's your turn! Please proceed to the service counter."
        }
    elif status == "completed":
        return {
            "status": "completed",
            "people_ahead": 0,
            "estimated_wait_mins": 0,
            "message": "Your token has been completed. Thank you!"
        }
    elif status == "cancelled":
        return {
            "status": "cancelled",
            "people_ahead": 0,
            "estimated_wait_mins": 0,
            "message": "This token was cancelled."
        }
    
    # Status is 'waiting'
    conn = get_db_connection()
    waiting_ahead_count = conn.execute(
        "SELECT COUNT(*) as count FROM tokens WHERE status = 'waiting' AND id < ?",
        (token_id,)
    ).fetchone()["count"]
    conn.close()
    
    # If someone is currently being served, they are ahead in line
    people_ahead = waiting_ahead_count + (1 if currently_serving is not None else 0)
    estimated_wait_mins = people_ahead * avg_service_time

    if people_ahead == 0:
        message = "You are next in line! Please be ready."
    else:
        message = f"There {'is' if people_ahead == 1 else 'are'} {people_ahead} {'person' if people_ahead == 1 else 'people'} ahead of you."

    return {
        "status": "waiting",
        "people_ahead": people_ahead,
        "estimated_wait_mins": estimated_wait_mins,
        "message": message
    }

def internal_create_token(customer_name="Guest"):
    """Helper used both by HTTP endpoint and AI assistant action to create tokens."""
    conn = get_db_connection()
    cursor = conn.cursor()
    last_token_row = cursor.execute("SELECT MAX(token_number) as max_num FROM tokens").fetchone()
    if last_token_row and last_token_row["max_num"] is not None:
        next_token_number = last_token_row["max_num"] + 1
    else:
        next_token_number = 101

    cursor.execute(
        "INSERT INTO tokens (token_number, customer_name, status) VALUES (?, ?, 'waiting')",
        (next_token_number, customer_name)
    )
    new_id = cursor.lastrowid
    conn.commit()
    token_row = cursor.execute("SELECT * FROM tokens WHERE id = ?", (new_id,)).fetchone()
    conn.close()

    serving = get_currently_serving()
    avg_service_time = int(get_setting("avg_service_time_mins", "5"))
    stats = calculate_token_stats(token_row, serving, avg_service_time)

    return {
        "token_number": token_row["token_number"],
        "customer_name": token_row["customer_name"],
        "created_at": token_row["created_at"],
        "currently_serving": serving["token_number"] if serving else None,
        **stats
    }

# ----------------- HTML Pages -----------------

@app.route("/")
@app.route("/join")
def index():
    return render_template("index.html")

@app.route("/admin")
def admin():
    return render_template("admin.html")

@app.route("/kiosk")
def kiosk():
    return render_template("kiosk.html")

# ----------------- QR Code Endpoints -----------------

@app.route("/api/qr/info", methods=["GET"])
def qr_info():
    port = request.environ.get("SERVER_PORT", "5000")
    local_ip = get_local_ip()
    network_url = f"http://{local_ip}:{port}/join"
    host_url = f"{request.host_url.rstrip('/')}/join"
    
    return jsonify({
        "success": True,
        "network_url": network_url,
        "host_url": host_url,
        "recommended_url": network_url if local_ip != "127.0.0.1" else host_url
    })

@app.route("/api/qr", methods=["GET"])
def generate_qr():
    target_url = request.args.get("url")
    
    if not target_url:
        port = request.environ.get("SERVER_PORT", "5000")
        local_ip = get_local_ip()
        if local_ip and local_ip != "127.0.0.1":
            target_url = f"http://{local_ip}:{port}/join"
        else:
            target_url = f"{request.host_url.rstrip('/')}/join"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=3,
    )
    qr.add_data(target_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#1e1b4b", back_color="#ffffff")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return send_file(buf, mimetype="image/png")

# ----------------- Queue API Endpoints -----------------

@app.route("/api/queue/status", methods=["GET"])
def queue_status():
    conn = get_db_connection()
    serving = get_currently_serving()
    waiting_count = conn.execute("SELECT COUNT(*) as count FROM tokens WHERE status = 'waiting'").fetchone()["count"]
    completed_count = conn.execute("SELECT COUNT(*) as count FROM tokens WHERE status = 'completed'").fetchone()["count"]
    avg_service_time = int(get_setting("avg_service_time_mins", "5"))
    conn.close()

    return jsonify({
        "success": True,
        "currently_serving": serving["token_number"] if serving else None,
        "currently_serving_name": serving["customer_name"] if serving else None,
        "waiting_count": waiting_count,
        "completed_count": completed_count,
        "avg_service_time_mins": avg_service_time
    })

@app.route("/api/token/create", methods=["POST"])
def create_token():
    data = request.get_json(silent=True) or {}
    customer_name = data.get("name", "").strip() or "Guest"
    token_data = internal_create_token(customer_name)
    return jsonify({
        "success": True,
        "token": token_data
    })

@app.route("/api/token/<int:token_number>", methods=["GET"])
def get_token(token_number):
    conn = get_db_connection()
    token_row = conn.execute("SELECT * FROM tokens WHERE token_number = ? ORDER BY id DESC LIMIT 1", (token_number,)).fetchone()
    conn.close()

    if not token_row:
        return jsonify({"success": False, "error": f"Token #{token_number} not found"}), 404

    serving = get_currently_serving()
    avg_service_time = int(get_setting("avg_service_time_mins", "5"))
    stats = calculate_token_stats(token_row, serving, avg_service_time)

    return jsonify({
        "success": True,
        "token_number": token_row["token_number"],
        "customer_name": token_row["customer_name"],
        "created_at": token_row["created_at"],
        "currently_serving": serving["token_number"] if serving else None,
        "currently_serving_name": serving["customer_name"] if serving else None,
        **stats
    })

@app.route("/api/admin/call-next", methods=["POST"])
def admin_call_next():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. If someone is currently serving, mark them completed
    currently_serving = cursor.execute("SELECT * FROM tokens WHERE status = 'serving' ORDER BY id ASC LIMIT 1").fetchone()
    if currently_serving:
        cursor.execute(
            "UPDATE tokens SET status = 'completed', served_at = CURRENT_TIMESTAMP WHERE id = ?",
            (currently_serving["id"],)
        )

    # 2. Pick the next waiting token
    next_token = cursor.execute("SELECT * FROM tokens WHERE status = 'waiting' ORDER BY id ASC LIMIT 1").fetchone()
    if next_token:
        cursor.execute("UPDATE tokens SET status = 'serving' WHERE id = ?", (next_token["id"],))
        conn.commit()
        serving_data = {
            "token_number": next_token["token_number"],
            "customer_name": next_token["customer_name"]
        }
    else:
        conn.commit()
        serving_data = None

    conn.close()

    return jsonify({
        "success": True,
        "message": f"Now serving #{serving_data['token_number']}" if serving_data else "No more customers waiting",
        "currently_serving": serving_data
    })

@app.route("/api/admin/queue", methods=["GET"])
def admin_queue():
    conn = get_db_connection()
    serving = conn.execute("SELECT * FROM tokens WHERE status = 'serving' ORDER BY id ASC LIMIT 1").fetchone()
    waiting = conn.execute("SELECT * FROM tokens WHERE status = 'waiting' ORDER BY id ASC").fetchall()
    recent_completed = conn.execute("SELECT * FROM tokens WHERE status = 'completed' ORDER BY served_at DESC LIMIT 5").fetchall()
    avg_service_time = int(get_setting("avg_service_time_mins", "5"))
    conn.close()

    return jsonify({
        "success": True,
        "currently_serving": dict(serving) if serving else None,
        "waiting": [dict(w) for w in waiting],
        "completed": [dict(c) for c in recent_completed],
        "avg_service_time_mins": avg_service_time
    })

@app.route("/api/admin/settings", methods=["POST"])
def admin_settings():
    data = request.get_json(silent=True) or {}
    avg_time = data.get("avg_service_time_mins")

    try:
        avg_time = int(avg_time)
        if avg_time < 1:
            return jsonify({"success": False, "error": "Average service time must be at least 1 minute"}), 400
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Invalid time value"}), 400

    set_setting("avg_service_time_mins", avg_time)
    return jsonify({"success": True, "avg_service_time_mins": avg_time})

@app.route("/api/admin/reset", methods=["POST"])
def admin_reset():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tokens")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name = 'tokens'")
    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Queue has been reset successfully. Token numbers will restart at 101."
    })

# ----------------- Organization & AI Assistant Endpoints -----------------

@app.route("/api/org-info", methods=["GET"])
def api_get_org_info():
    return jsonify({
        "success": True,
        "data": get_org_info()
    })

@app.route("/api/admin/org-info", methods=["POST"])
def api_update_org_info():
    data = request.get_json(silent=True) or {}
    set_org_info(data)
    return jsonify({
        "success": True,
        "message": "Organization information updated successfully.",
        "data": get_org_info()
    })

@app.route("/api/assistant/chat", methods=["POST"])
def api_assistant_chat():
    payload = request.get_json(silent=True) or {}
    user_message = payload.get("message", "").strip()
    token_number = payload.get("token_number")

    # Build real-time queue context
    conn = get_db_connection()
    serving = get_currently_serving()
    waiting_count = conn.execute("SELECT COUNT(*) as count FROM tokens WHERE status = 'waiting'").fetchone()["count"]
    avg_service_time = int(get_setting("avg_service_time_mins", "5"))

    queue_context = {
        "currently_serving": serving["token_number"] if serving else None,
        "currently_serving_name": serving["customer_name"] if serving else None,
        "waiting_count": waiting_count,
        "avg_service_time_mins": avg_service_time,
        "token_number": None
    }

    if token_number:
        try:
            token_number = int(token_number)
            token_row = conn.execute(
                "SELECT * FROM tokens WHERE token_number = ? ORDER BY id DESC LIMIT 1",
                (token_number,)
            ).fetchone()
            if token_row:
                stats = calculate_token_stats(token_row, serving, avg_service_time)
                queue_context["token_number"] = token_row["token_number"]
                queue_context["customer_name"] = token_row["customer_name"]
                queue_context.update(stats)
        except (ValueError, TypeError):
            pass

    conn.close()

    org_info = get_org_info()
    output_language = payload.get("output_language", "en")

    # Classify, retrieve data, and translate response
    res = assistant.classify_and_respond(
        user_message,
        queue_context,
        org_info,
        create_token_fn=internal_create_token,
        output_language=output_language
    )

    return jsonify({
        "success": True,
        "user_message": user_message,
        **res
    })

@app.route("/api/assistant/tts", methods=["GET"])
def api_assistant_tts():
    """Generates MP3 audio on-the-fly for any text and language."""
    text = request.args.get("text", "").strip()
    lang = request.args.get("lang", "en")
    if not text:
        return jsonify({"error": "No text provided"}), 400

    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang=lang)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return send_file(buf, mimetype="audio/mpeg")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/languages", methods=["GET"])
def api_languages():
    from multilingual_engine import SUPPORTED_LANGUAGES
    return jsonify({
        "success": True,
        "languages": SUPPORTED_LANGUAGES
    })

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
