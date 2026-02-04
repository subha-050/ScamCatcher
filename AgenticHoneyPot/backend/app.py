import os
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# The EXACT key for the portal
API_KEY = "sk_test_5f2a9b1c8e3d4f5a6b7c"

@app.route('/', methods=['GET', 'POST', 'HEAD'])
@app.route('/api/honeypot', methods=['GET', 'POST', 'HEAD'])
def test_endpoint():
    # 1. Handle Pings (GET/HEAD)
    if request.method in ['GET', 'HEAD']:
        return jsonify({"status": "success", "message": "Honeypot is live"}), 200

    # 2. Check the API Key
    if request.headers.get("x-api-key") != API_KEY:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    # 3. Force JSON Parsing
    data = request.get_json(force=True, silent=True) or {}
    session_id = data.get("sessionId") or data.get("session_id") or "test-session"

    # 4. Build Response with explicit headers
    response_data = {
        "status": "success",
        "reply": "I am very worried. Can you help me verify my account via UPI?",
        "sessionId": session_id,
        "scamDetected": True
    }
    
    res = make_response(jsonify(response_data), 200)
    res.headers["Content-Type"] = "application/json"
    return res

@app.route('/api/honeypot/final', methods=['POST'])
def final():
    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
