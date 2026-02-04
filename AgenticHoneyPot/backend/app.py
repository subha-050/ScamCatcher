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
# We'll check the ENV variable first, but fallback to your specific key
API_KEY = os.getenv("HONEYPOT_API_KEY", "sk_test_5f2a9b1c8e3d4f5a6b7c")
DATA_FILE = "session_store.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except: return {}
    return {}

def save_data(data):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except: pass

def extract_intel(text):
    text = str(text) if text else ""
    patterns = {
        "upi_ids": re.findall(r'[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}', text),
        "phishing_links": re.findall(r'https?://[^\s]+', text),
        "phone_numbers": re.findall(r'(?:\+91|0)?[6-9]\d{9}', text),
    }
    keywords = ["block", "verify", "urgent", "kyc", "bank", "account", "transfer", "otp", "win"]
    found_keywords = [word for word in keywords if word in text.lower()]
    threat_score = (len(patterns["upi_ids"]) * 40) + (len(patterns["phishing_links"]) * 30) + (len(found_keywords) * 10)
    threat_level = "HIGH" if threat_score > 50 else "MEDIUM" if threat_score > 0 else "LOW"
    return patterns, found_keywords, threat_level

@app.route('/')
def home():
    return jsonify({"status": "online", "message": "API is Live"})

@app.route('/api/honeypot', methods=['POST'])
def handle_message():
    # 1. AUTH CHECK
    if request.headers.get("x-api-key") != API_KEY:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    # 2. GET DATA (SUPER FLEXIBLE)
    data = request.get_json(force=True, silent=True) or {}
    
    # GUVI might send 'sessionId' or 'session_id'
    session_id = data.get("sessionId") or data.get("session_id") or "default-session"
    
    # GUVI might send {"message": {"text": "..."}} OR just {"message": "..."}
    message_input = data.get("message", "")
    if isinstance(message_input, dict):
        msg_text = message_input.get("text", "")
    else:
        msg_text = str(message_input)

    # 3. PROCESS
    store = load_data()
    if session_id not in store:
        store[session_id] = {"upi_ids":[], "phishing_links":[], "phone_numbers":[], "keywords":[], "msg_count":0}
    
    intel, keywords, level = extract_intel(msg_text)
    store[session_id]["msg_count"] += 1
    for key in intel:
        store[session_id][key] = list(set(store[session_id].get(key, []) + intel[key]))
    store[session_id]["keywords"] = list(set(store[session_id].get("keywords", []) + keywords))
    store[session_id]["threat_level"] = level
    save_data(store)

    # 4. REPLY
    reply = "I'm very scared. How do I verify my KYC?" if level == "HIGH" else "Is this official?"
    return jsonify({"status": "success", "reply": reply})

@app.route('/api/honeypot/final', methods=['POST'])
def final_report():
    if request.headers.get("x-api-key") != API_KEY:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    
    data = request.get_json(force=True, silent=True) or {}
    session_id = data.get("sessionId") or data.get("session_id")
    store = load_data()

    if not session_id or session_id not in store:
        return jsonify({"status": "error", "message": "Invalid Session"}), 404

    s_data = store[session_id]
    payload = {
        "sessionId": session_id,
        "scamDetected": True,
        "totalMessagesExchanged": s_data["msg_count"],
        "extractedIntelligence": {
            "bankAccounts": [],
            "upiIds": s_data.get("upi_ids", []),
            "phishingLinks": s_data.get("phishing_links", []),
            "phoneNumbers": s_data.get("phone_numbers", []),
            "suspiciousKeywords": s_data.get("keywords", [])
        }
    }

    try: requests.post("https://hackathon.guvi.in/api/updateHoneyPotFinalResult", json=payload, timeout=5)
    except: pass

    return jsonify({"status": "success", "extractedIntelligence": s_data})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
