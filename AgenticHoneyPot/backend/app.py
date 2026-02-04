import os
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# The EXACT key for the portal
API_KEY = "sk_test_5f2a9b1c8e3d4f5a6b7c"

@app.route('/', methods=['GET', 'POST', 'HEAD'])
@app.route('/api/honeypot', methods=['GET', 'POST', 'HEAD'])
def test_endpoint():
    # FIX: Allow HEAD and GET requests without API key
    if request.method in ['GET', 'HEAD']:
        return jsonify({"status": "success", "message": "Honeypot is live"}), 200

    # 1. Check the API Key ONLY for POST requests
    if request.headers.get("x-api-key") != API_KEY:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    # 2. Extract JSON safely
    data = request.get_json(force=True, silent=True) or {}
    session_id = data.get("sessionId") or data.get("session_id") or "test-session"

    # 3. Standard Response Format for GUVI
    return jsonify({
        "status": "success",
        "reply": "I am very worried. Can you help me verify my account via UPI?",
        "sessionId": session_id,
        "scamDetected": True
    }), 200

@app.route('/api/honeypot/final', methods=['POST'])
def final():
    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
