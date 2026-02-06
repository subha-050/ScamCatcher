import re, os, random, json
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS

app = Flask(__name__)
# Enable CORS to prevent any browser-based testing blocks
CORS(app)

# --- CONFIGURATION ---
# Note: In production, keep this in Render Environment Variables
API_KEY = os.environ.get("HONEYPOT_API_KEY", "sk_test_5f2a9b1c8e3d4f5a6b7c")

# State management for agentic behavior
brain_memory = {}

class CognitiveEngine:
    @staticmethod
    def extract_intel(text):
        """Regex to identify Indian scam entities."""
        text = str(text)
        return {
            "upi": list(set(re.findall(r'[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}', text))),
            "links": list(set(re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', text))),
            "phones": list(set(re.findall(r'(?:\+91|0)?[6-9]\d{9}', text))),
            "accounts": list(set(re.findall(r'\b\d{9,18}\b', text)))
        }

    @staticmethod
    def analyze_scammer_intent(text):
        t = str(text).lower()
        if any(x in t for x in ["upi", "pay", "vpa", "transfer"]): return "FINANCIAL"
        if any(x in t for x in ["otp", "code", "sms", "verify"]): return "CREDENTIAL"
        if any(x in t for x in ["block", "kyc", "urgent", "police", "sbi", "bank"]): return "URGENCY"
        return "GENERAL"

def get_agentic_reply(session_id, text):
    intent = CognitiveEngine.analyze_scammer_intent(text)
    
    if session_id not in brain_memory:
        brain_memory[session_id] = {"turn": 0, "fear": 0.5, "trust": 0.9}
    
    state = brain_memory[session_id]
    state["turn"] += 1
    
    if intent == "URGENCY":
        return "I'm so scared! My pension is in that account. Please tell me exactly what to do!"
    if intent == "FINANCIAL":
        return "I have my UPI app open. It's asking for a '6-digit Security Pin'. Should I type that in now?"
    if intent == "CREDENTIAL":
        return "The SMS arrived, but the screen is blurry and I can't read the numbers. Can you send it again?"
    
    return "I'm a bit old and slow with these phones. Can you explain that again very simply?"

# --- ROUTES ---

@app.route('/', methods=['GET', 'HEAD'])
def health_check():
    return jsonify({"status": "active"}), 200

@app.route('/api/honeypot', methods=['POST', 'OPTIONS'])
def main_handler():
    if request.method == 'OPTIONS':
        return make_response("", 200)

    # 1. MANDATORY: Verify API Key
    if request.headers.get("x-api-key") != API_KEY:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    # 2. MANDATORY: Safe JSON Parsing
    # The 'char 0' error often happens if get_json() fails silently
    data = request.get_json(force=True, silent=True)
    if data is None:
        return jsonify({"status": "error", "message": "Invalid JSON"}), 400

    session_id = data.get("sessionId", "eval_session")
    
    # Safely navigate the nested message object from the sample request
    message_obj = data.get("message", {})
    if isinstance(message_obj, dict):
        msg_text = message_obj.get("text", "")
    else:
        msg_text = str(message_obj)

    # 3. Logic Processing
    intel = CognitiveEngine.extract_intel(msg_text)
    reply = get_agentic_reply(session_id, msg_text)

    # 4. FINAL RESPONSE (Matches the Evaluator's Requirements)
    # We include 'status' and 'reply' at the top level as required
    response_body = {
        "status": "success",
        "reply": reply,
        "sessionId": session_id,
        "extractedIntelligence": {
            "upiIds": intel["upi"],
            "phishingLinks": intel["links"],
            "phoneNumbers": intel["phones"],
            "bankAccounts": intel["accounts"]
        }
    }
    
    return jsonify(response_body), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
