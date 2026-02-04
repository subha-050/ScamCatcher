import re, os, json, requests
from flask import Flask, request, jsonify
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

API_KEY = os.getenv("HONEYPOT_API_KEY", "sk_test_5f2a9b1c8e3d4f5a6b7c")

def extract_intel(text):
    text = str(text) if text else ""
    patterns = {
        "upi_ids": re.findall(r'[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}', text),
        "phishing_links": re.findall(r'https?://[^\s]+', text),
        "phone_numbers": re.findall(r'(?:\+91|0)?[6-9]\d{9}', text),
    }
    keywords = ["block", "verify", "urgent", "kyc", "bank", "account", "transfer", "otp", "win"]
    found_keywords = [word for word in keywords if word in text.lower()]
    threat_level = "HIGH" if (len(patterns["upi_ids"]) > 0 or len(found_keywords) > 2) else "LOW"
    return patterns, found_keywords, threat_level

# --- THE ALL-IN-ONE ROUTE ---
@app.route('/', methods=['GET', 'POST'])
@app.route('/api/honeypot', methods=['GET', 'POST'])
def handle_everything():
    # If it's just a browser visit or a health check
    if request.method == 'GET':
        return jsonify({"status": "online", "message": "Honeypot Active"})

    # Check API Key
    if request.headers.get("x-api-key") != API_KEY:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    # Flexible JSON parsing
    data = request.get_json(force=True, silent=True) or {}
    
    # Extract data regardless of format
    session_id = data.get("sessionId") or data.get("session_id") or "guvi-test"
    msg_input = data.get("message", "")
    msg_text = msg_input.get("text", "") if isinstance(msg_input, dict) else str(msg_input)

    intel, keywords, level = extract_intel(msg_text)

    # Response for the tester
    reply = "I'm very scared. Please help me with the KYC." if level == "HIGH" else "Okay, I understand."
    
    return jsonify({
        "status": "success",
        "reply": reply,
        "sessionId": session_id,
        "threatLevel": level
    })

@app.route('/api/honeypot/final', methods=['POST'])
def final_report():
    if request.headers.get("x-api-key") != API_KEY:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    return jsonify({"status": "success", "message": "Report received"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
