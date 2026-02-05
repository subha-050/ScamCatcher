import re, os, json, requests, random
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Use Environment Variables for Security
API_KEY = os.getenv("HONEYPOT_API_KEY", "sk_test_5f2a9b1c8e3d4f5a6b7c")

# In-memory store (Better for Hackathon speed; for production, use Redis)
store = {}

class IntelligenceEngine:
    @staticmethod
    def extract(text):
        """Deep extraction of Indian financial scam entities."""
        return {
            "upi_ids": list(set(re.findall(r'[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}', text))),
            "phishing_links": list(set(re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', text))),
            "phone_numbers": list(set(re.findall(r'(?:\+91|0)?[6-9]\d{9}', text))),
            "account_numbers": list(set(re.findall(r'\b\d{9,18}\b', text))),
            "ifsc_codes": list(set(re.findall(r'[A-Z]{4}0[A-Z0-9]{6}', text)))
        }

class AgentPersona:
    @staticmethod
    def get_reply(text, session_data):
        t = text.lower()
        count = session_data["msg_count"]
        
        # KEYWORD-BASED INTENT DETECTION
        is_upi = any(x in t for x in ["upi", "pay", "vpa", "transfer"])
        is_otp = any(x in t for x in ["otp", "code", "sms", "verify"])
        is_urgency = any(x in t for x in ["urgent", "block", "limit", "police"])

        # TURN-BASED EVOLUTION (The "Clever" Part)
        if is_upi:
            replies = [
                "I'm at the payment screen, but it says 'Recipient Limit Exceeded'. Do you have another UPI ID?",
                "Wait, the name on the UPI ID shows 'Global Services' and not SBI. Is this correct?",
                "I tried to pay but my bank app is asking for a 'Verification Remark'. What should I type?"
            ]
            return replies[min(count // 2, len(replies)-1)]
        
        if is_otp:
            return "I see the SMS, but my screen is cracked and I can't read the last two digits. One second..."

        if is_urgency:
            return "Oh no! Please don't block it, my daughter's school fees are in there! Tell me exactly what to do."

        return "I'm a bit old and slow with these phones. Can you explain that again very simply?"

@app.route('/api/honeypot', methods=['POST', 'OPTIONS'])
def handle_message():
    # Handle Pre-flight for Browser/Tester
    if request.method == 'OPTIONS':
        return make_response("", 200)

    if request.headers.get("x-api-key") != API_KEY:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    data = request.get_json(force=True, silent=True) or {}
    session_id = data.get("sessionId", "test_default")
    msg_text = data.get("message", {}).get("text", "")

    # Initialize session
    if session_id not in store:
        store[session_id] = {
            "intel": {"upi_ids": [], "links": [], "phones": [], "accounts": [], "ifsc": []},
            "msg_count": 0,
            "history": []
        }

    s_data = store[session_id]
    s_data["msg_count"] += 1
    
    # Extract and store
    new_intel = IntelligenceEngine.extract(msg_text)
    for key, val in new_intel.items():
        # Cleanly map our internal names to the storage keys
        store_key = "upi_ids" if key == "upi_ids" else "links" if key == "phishing_links" else "phones" if key == "phone_numbers" else "accounts"
        if store_key in s_data["intel"]:
            s_data["intel"][store_key] = list(set(s_data["intel"][store_key] + val))

    # Get clever reply
    reply = AgentPersona.get_reply(msg_text, s_data)

    return jsonify({"status": "success", "reply": reply, "sessionId": session_id})

@app.route('/api/honeypot/final', methods=['POST'])
def final_report():
    data = request.get_json(force=True, silent=True) or {}
    session_id = data.get("sessionId")
    
    if session_id not in store:
        return jsonify({"status": "error", "message": "No session found"}), 404

    s_data = store[session_id]
    
    # Callback payload formatted for GUVI requirements
    payload = {
        "sessionId": session_id,
        "scamDetected": True,
        "extractedIntelligence": {
            "bankAccounts": s_data["intel"]["accounts"],
            "upiIds": s_data["intel"]["upi_ids"],
            "phishingLinks": s_data["intel"]["links"],
            "phoneNumbers": s_data["intel"]["phones"]
        },
        "totalMessagesExchanged": s_data["msg_count"]
    }

    # Attempt GUVI Callback
    try:
        requests.post("https://hackathon.guvi.in/api/updateHoneyPotFinalResult", json=payload, timeout=5)
    except:
        pass

    return jsonify({"status": "success", "data": payload})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
