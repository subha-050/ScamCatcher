import re, os, json, requests
from flask import Flask, request, jsonify
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configuration - Priority to Environment Variable
API_KEY = os.getenv("HONEYPOT_API_KEY", "sk_test_5f2a9b1c8e3d4f5a6b7c")

# --- ADVANCED ANALYTICS (The "Intelligence") ---
def analyze_scam(text):
    text = str(text) if text else ""
    # Detection for Indian Scam Patterns
    intel = {
        "upi_ids": re.findall(r'[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}', text),
        "links": re.findall(r'https?://[^\s]+', text),
        "phones": re.findall(r'(?:\+91|0)?[6-9]\d{9}', text),
    }
    keywords = ["block", "verify", "urgent", "kyc", "bank", "account", "otp", "win"]
    found_keywords = [w for w in keywords if w in text.lower()]
    
    # Logic to determine if we should act scared or suspicious
    is_high_threat = len(intel["upi_ids"]) > 0 or len(found_keywords) >= 2
    return intel, found_keywords, is_high_threat

# --- ROUTES ---

@app.route('/', methods=['GET', 'POST'])
@app.route('/api/honeypot', methods=['GET', 'POST'])
def handle_honeypot():
    # 1. Health check for browser/tester
    if request.method == 'GET':
        return jsonify({"status": "online", "agent": "ScamCatcher v2.0"})

    # 2. Authentication
    if request.headers.get("x-api-key") != API_KEY:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    # 3. Flexible Data Extraction (Fixes "INVALID_REQUEST_BODY")
    data = request.get_json(force=True, silent=True) or {}
    msg_input = data.get("message", "")
    msg_text = msg_input.get("text", "") if isinstance(msg_input, dict) else str(msg_input)
    session_id = data.get("sessionId") or data.get("session_id") or "test-session"

    # 4. Run Intelligence
    intel, keywords, high_threat = analyze_scam(msg_text)

    # 5. Persona-based Response
    if high_threat:
        reply = "I'm very scared about my account. How do I pay via UPI to verify my KYC?"
    else:
        reply = "I'm not sure I understand. Is this my official bank branch?"

    # 6. Response structured for GUVI Validation
    return jsonify({
        "status": "success",
        "reply": reply,
        "sessionId": session_id,
        "scamDetected": high_threat,
        "intelligence": {
            "upi_ids": intel["upi_ids"],
            "keywords": keywords
        }
    })

@app.route('/api/honeypot/final', methods=['POST'])
def final_report():
    if request.headers.get("x-api-key") != API_KEY:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    return jsonify({"status": "success", "message": "Session Closed"})

if __name__ == '__main__':
    # Use port 10000 for Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
