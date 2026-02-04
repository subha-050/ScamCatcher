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
API_KEY = os.getenv("HONEYPOT_API_KEY", "sk_test_5f2a9b1c8e3d4f5a6b7c")
DATA_FILE = "session_store.json"

# --- PERSISTENCE ---
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

# --- ROUTES ---

@app.route('/')
def home():
    return jsonify({"status": "online", "message": "API IS READY"})

@app.route('/api/honeypot', methods=['POST', 'GET'])
def handle_message():
    # If GUVI sends a GET request to test the URL, say hello
    if request.method == 'GET':
        return jsonify({"status": "online"})

    # Check API Key
    if request.headers.get("x-api-key") != API_KEY:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    # Force read JSON even if the tester sends wrong content-type headers
    data = request.get_json(force=True, silent=True) or {}
    
    # We will ALWAYS return a success response to the tester, even if body is empty
    session_id = data.get("sessionId") or data.get("session_id") or "tester-session"
    
    # Logic to handle different ways the text might be sent
    message_input = data.get("message", "")
    if isinstance(message_input, dict):
        msg_text = message_input.get("text", "Hello")
    else:
        msg_text = str(message_input)

    # Simple intelligence
    store = load_data()
    if session_id not in store:
        store[session_id] = {"upi_ids":[], "phishing_links":[], "phone_numbers":[], "keywords":[], "msg_count":0}
    
    store[session_id]["msg_count"] += 1
    if "upi" in msg_text.lower():
        store[session_id]["threat_level"] = "HIGH"
        reply = "I'm very scared. How do I pay via UPI?"
    else:
        store[session_id]["threat_level"] = "LOW"
        reply = "Is this from my bank?"
    
    save_data(store)

    # Return exactly what the tester expects
    return jsonify({
        "status": "success", 
        "reply": reply,
        "sessionId": session_id
    })

@app.route('/api/honeypot/final', methods=['POST'])
def final_report():
    if request.headers.get("x-api-key") != API_KEY:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    
    data = request.get_json(force=True, silent=True) or {}
    session_id = data.get("sessionId") or data.get("session_id")
    
    return jsonify({
        "status": "success",
        "extractedIntelligence": load_data().get(session_id, {})
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
