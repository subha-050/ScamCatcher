import re, os, random
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Configuration
API_KEY = "sk_test_5f2a9b1c8e3d4f5a6b7c"

class ScamIntelligence:
    @staticmethod
    def extract_all(text):
        """Advanced extraction using broad pattern matching."""
        return {
            "upi_ids": list(set(re.findall(r'[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}', text))),
            "urls": list(set(re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', text))),
            "phones": list(set(re.findall(r'(?:\+91|0)?[6-9]\d{9}', text))),
            "codes": list(set(re.findall(r'\b\d{4,8}\b', text))) # Potential OTPs or Pins
        }

def get_agentic_reply(text):
    """Dynamic Persona Engine based on Scammer Intent."""
    t = text.lower()
    
    # Intent: Financial Pressure (UPI/Transfer)
    if any(x in t for x in ["upi", "pay", "send", "transfer", "money"]):
        replies = [
            "My UPI app is saying 'Technical Error'. Can I try sending it to a different ID?",
            "I'm at the payment screen. It's asking for a 'Remark'. What should I type there?",
            "I tried the VPA but it says 'Receiver limit reached'. Do you have another one?"
        ]
        return random.choice(replies)

    # Intent: Fear/Urgency (KYC/Block/Bank)
    if any(x in t for x in ["kyc", "block", "verify", "suspend", "police"]):
        replies = [
            "Please don't block it, my gas bill is due today! Can I verify via this chat?",
            "I'm clicking the link but it just shows a white screen. Is there a manual way?",
            "I've got my Aadhar card ready. Do I need to send a photo of the front and back?"
        ]
        return random.choice(replies)

    # Intent: Greed (Win/Prize/Offer)
    if any(x in t for x in ["win", "lucky", "prize", "gift", "crore"]):
        replies = [
            "I can't believe I won! Do I need to pay the registration fee before I get the money?",
            "Is this the official KBC department? How do I transfer the winning amount to my savings?",
            "I'm so excited! My family really needs this. What is the first step?"
        ]
        return random.choice(replies)

    # Fallback: The 'Confused Elderly' Persona
    return "I am sorry, I am a bit slow with phones. Could you explain that again very simply?"

@app.route('/', methods=['GET', 'POST', 'HEAD', 'OPTIONS'])
@app.route('/api/honeypot', methods=['GET', 'POST', 'HEAD', 'OPTIONS'])
def honeypot_v3():
    # 1. Seamless Protocol Handling (Bypasses Portal Connection Errors)
    if request.method in ['GET', 'HEAD', 'OPTIONS']:
        res = make_response(jsonify({"status": "active", "version": "3.0-Advanced"}), 200)
        res.headers["Access-Control-Allow-Origin"] = "*"
        res.headers["Access-Control-Allow-Headers"] = "Content-Type,x-api-key"
        return res

    # 2. Authentication
    if request.headers.get("x-api-key") != API_KEY:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    # 3. Data Ingestion
    raw_data = request.get_json(force=True, silent=True) or {}
    message_obj = raw_data.get("message", {})
    message_text = message_obj.get("text", str(message_obj))
    session_id = raw_data.get("sessionId", "session_" + str(random.randint(100, 999)))

    # 4. Processing & Extraction
    intel = ScamIntelligence.extract_all(message_text)
    is_scam = len(intel["upi_ids"]) > 0 or len(intel["urls"]) > 0 or len(message_text) > 20
    
    # 5. Build Agentic Response
    response_payload = {
        "status": "success",
        "reply": get_agentic_reply(message_text),
        "sessionId": session_id,
        "scamDetected": is_scam,
        "metadata": {
            "threatLevel": "CRITICAL" if is_scam else "LOW",
            "entitiesExtracted": intel
        }
    }
    
    return jsonify(response_payload), 200

@app.route('/api/honeypot/final', methods=['POST'])
def finalize():
    return jsonify({"status": "success", "session_closed": True}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
