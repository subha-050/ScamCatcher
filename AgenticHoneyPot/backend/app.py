import re
import os
import json
import requests
from flask import Flask, request, jsonify
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- CONFIGURATION ---
# Defaulting to your test key if the environment variable isn't found
API_KEY = os.getenv("HONEYPOT_API_KEY", "sk_test_5f2a9b1c8e3d4f5a6b7c")
DATA_FILE = "session_store.json"


# --- PERSISTENCE LAYER ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_data(data):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving to file: {e}")


# --- ADVANCED ANALYTICS & EXTRACTION ---
def extract_intel(text):
    """
    Detects UPI, Indian Mobile Numbers, URLs, and calculates a Threat Score.
    """
    if not text:
        return {"upi_ids":[], "phishing_links":[], "phone_numbers":[]}, [], "LOW"

    patterns = {
        "upi_ids": re.findall(r'[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}', text),
        "phishing_links": re.findall(r'https?://[^\s]+', text),
        "phone_numbers": re.findall(r'(?:\+91|0)?[6-9]\d{9}', text),
    }

    keywords = ["block", "verify", "urgent", "kyc", "bank", "account", "transfer", "otp", "win"]
    found_keywords = [word for word in keywords if word in text.lower()]

    # Calculate Threat Level
    threat_score = (len(patterns["upi_ids"]) * 40) + (len(patterns["phishing_links"]) * 30) + (len(found_keywords) * 10)
    threat_level = "HIGH" if threat_score > 50 else "MEDIUM" if threat_score > 0 else "LOW"

    return patterns, found_keywords, threat_level


# --- ROUTES ---

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "message": "ScamCatcher Honeypot API is live and running.",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "process_message": "/api/honeypot",
            "final_report": "/api/honeypot/final"
        }
    })

@app.route('/api/honeypot', methods=['POST'])
def handle_message():
    # Verify API Key
    incoming_key = request.headers.get("x-api-key")
    if incoming_key != API_KEY:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    # Flexible JSON parsing to prevent "INVALID_REQUEST_BODY"
    data = request.get_json(force=True, silent=True) or {}
    
    # Extract session and message with fallbacks
    session_id = data.get("sessionId", "test-session-101")
    message_obj = data.get("message", {})
    
    # Handle both {"message": {"text": "..."}} and {"message": "..."}
    if isinstance(message_obj, dict):
        msg_text = message_obj.get("text", "")
    else:
        msg_text = str(message_obj)

    store = load_data()

    if session_id not in store:
        store[session_id] = {
            "upi_ids": [], "phishing_links": [], "phone_numbers": [],
            "keywords": [], "msg_count": 0, "start_time": datetime.now().isoformat()
        }

    # Extract & Merge
    intel, keywords, level = extract_intel(msg_text)
    store[session_id]["msg_count"] += 1

    for key in intel:
        store[session_id][key] = list(set(store[session_id][key] + intel[key]))
    store[session_id]["keywords"] = list(set(store[session_id]["keywords"] + keywords))
    store[session_id]["threat_level"] = level

    save_data(store)

    # Response Logic
    if level == "HIGH":
        reply = "I'm very scared about my account being blocked. I tried the link but it's slow. Can I pay via UPI directly?"
    else:
        reply = "I'm not sure I understand. Is this from my official bank branch?"

    return jsonify({"status": "success", "reply": reply})


@app.route('/api/honeypot/final', methods=['POST'])
def final_report():
    if request.headers.get("x-api-key") != API_KEY:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    req_data = request.get_json(force=True, silent=True) or {}
    session_id = req_data.get("sessionId")
    
    store = load_data()

    if not session_id or session_id not in store:
        return jsonify({"status": "error", "message": "Invalid Session"}), 404

    s_data = store[session_id]

    # CALLBACK TO GUVI
    payload = {
        "sessionId": session_id,
        "scamDetected": True,
        "totalMessagesExchanged": s_data["msg_count"],
        "extractedIntelligence": {
            "bankAccounts": [],
            "upiIds": s_data["upi_ids"],
            "phishingLinks": s_data["phishing_links"],
            "phoneNumbers": s_data["phone_numbers"],
            "suspiciousKeywords": s_data["keywords"]
        },
        "agentNotes": f"Threat Level: {s_data['threat_level']}. Turns: {s_data['msg_count']}."
    }

    try:
        res = requests.post("https://hackathon.guvi.in/api/updateHoneyPotFinalResult", json=payload, timeout=5)
        callback_status = res.status_code
    except Exception:
        callback_status = "Failed"

    return jsonify({
        "status": "success",
        "callback_status": callback_status,
        "extractedIntelligence": s_data
    })


if __name__ == '__main__':
    # Render uses the PORT environment variable
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
