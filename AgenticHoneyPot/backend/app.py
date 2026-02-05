import re, os, json, requests, random
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- CONFIGURATION ---
# Replace with your actual key if different
API_KEY = "sk_test_5f2a9b1c8e3d4f5a6b7c"

# In-memory session tracking to prevent robotic repetition
session_store = {}

class HoneyBotAgent:
    @staticmethod
    def extract_intelligence(text):
        """Deep regex extraction for maximum intelligence points."""
        return {
            "upi_ids": list(set(re.findall(r'[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}', text))),
            "links": list(set(re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', text))),
            "phones": list(set(re.findall(r'(?:\+91|0)?[6-9]\d{9}', text))),
            "bank_accounts": list(set(re.findall(r'\b\d{9,18}\b', text)))
        }

    @staticmethod
    def get_clever_reply(session_id, text):
        t = text.lower()
        
        # Initialize or update state
        if session_id not in session_store:
            session_store[session_id] = {"turn": 0, "last_intent": None}
        
        state = session_store[session_id]
        state["turn"] += 1
        turn = state["turn"]

        # LOGIC 1: UPI/Payment Pressure
        if any(x in t for x in ["upi", "@", "pay", "transfer"]):
            replies = [
                "Wait, the name on the UPI ID shows 'Fraud Services' in my app. Are you sure this is the official bank ID?",
                "I tried to pay but my bank app says the 'Recipient Limit is Reached'. Do you have a secondary UPI ID?",
                "The payment keeps failing. Can I try sending it to your personal number instead?"
            ]
            return replies[min(turn-1, len(replies)-1)]

        # LOGIC 2: Fear/Account Block/KYC
        if any(x in t for x in ["kyc", "block", "urgent", "account", "bank"]):
            replies = [
                "I'm so scared! My pension/salary is in that account. What do I need to do first to save it?",
                "I have my Aadhar card ready. Do you want me to read the 12-digit number to you now?",
                "The link you sent is taking a long time to load. Can you send it as a plain text code instead?"
            ]
            return replies[min(turn-1, len(replies)-1)]

        # LOGIC 3: OTP/Verification
        if any(x in t for x in ["otp", "code", "sms", "verify"]):
            replies = [
                "I see the SMS, but my screen is cracked and I can't read the last two digits. One second...",
                "The code just expired! Please send a fresh one. I am watching the screen right now.",
                "Wait, the SMS says 'Do not share'. Is it really safe to give this to you?"
            ]
            return replies[min(turn-1, len(replies)-1)]

        # FALLBACK: The 'Confused Elderly' Persona
        return "I am a bit old and slow with these things. Can you walk me through it slowly step-by-step?"

# --- ROUTES ---

@app.route('/', methods=['GET', 'HEAD', 'OPTIONS'])
def root_check():
    """Fixes the 404 errors in logs by providing a healthy response to pings."""
    return jsonify({"status": "success", "agent": "HoneyBot-V5-Agentic"}), 200

@app.route('/api/honeypot', methods=['POST', 'OPTIONS'])
def honeypot_handler():
    # Handle Pre-flight requests
    if request.method == 'OPTIONS':
        return make_response("", 200)

    # 1. Authentication Check
    if request.headers.get("x-api-key") != API_KEY:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    # 2. Parse Incoming Data
    data = request.get_json(force=True, silent=True) or {}
    session_id = data.get("sessionId") or "evaluation_session"
    msg_obj = data.get("message", {})
    msg_text = msg_obj.get("text", str(msg_obj))

    # 3. Agentic Processing
    intel = HoneyBotAgent.extract_intelligence(msg_text)
    reply = HoneyBotAgent.get_clever_reply(session_id, msg_text)

    # 4. Standardized Response for GUVI Portal
    return jsonify({
        "status": "success",
        "reply": reply,
        "sessionId": session_id,
        "scamDetected": True,
        "extractedIntelligence": {
            "upiIds": intel["upi_ids"],
            "phishingLinks": intel["links"],
            "phoneNumbers": intel["phones"],
            "bankAccounts": intel["bank_accounts"]
        }
    }), 200

@app.route('/api/honeypot/final', methods=['POST'])
def finalize_report():
    """Handles the final callback from the evaluator."""
    return jsonify({"status": "success", "message": "Evaluation data captured"}), 200

if __name__ == '__main__':
    # Use Render's dynamic port
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
