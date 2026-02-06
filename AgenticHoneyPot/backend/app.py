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
        text = str(text)
        return {
            # Catch: name@bank, name@okaxis, or name@ybl (2-256 chars before @)
            "upi": list(set(re.findall(r'[a-zA-Z0-9.-]{2,256}@[a-zA-Z][a-zA-Z]{2,64}', text))),
            
            # Catch: http, https, and tinyurl/bitly styles
            "links": list(set(re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', text))),
            
            # Catch: +91..., 0..., or 10-digit numbers starting with 6-9
            "phones": list(set(re.findall(r'(?:\+91|0)?[6-9]\d{9}', text))),
            
            # Catch: 9 to 18 digit bank account numbers
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
    
    # 1. Initialize session if new
    if session_id not in brain_memory:
        brain_memory[session_id] = {"turn": 0, "intent_counts": {}}
    
    state = brain_memory[session_id]
    state["turn"] += 1
    
    # 2. Track how many times we've hit this specific intent
    state["intent_counts"][intent] = state["intent_counts"].get(intent, 0) + 1
    count = state["intent_counts"][intent]

    # 3. Variety Logic for CREDENTIAL (OTP) requests
    if intent == "CREDENTIAL":
        responses = [
            "The SMS arrived, but the screen is blurry and I can't read the numbers. Can you send it again?",
            "I see the message, but my phone just died! Let me find my charger... okay, can you resend it?",
            "I got a code but then I accidentally deleted the thread. I'm so sorry, I'm not good with these touchscreens.",
            "Wait, I see a 6-digit number but it says 'Do not share'. Is it safe? Are you sure you are from the bank?",
            "My grandson just walked in, I had to hide the phone. Can you send it one more time quickly?"
        ]
        # Cycle through responses or stay on the last one if they keep asking
        return responses[min(count-1, len(responses)-1)]

    # 4. Variety Logic for URGENCY
    if intent == "URGENCY":
        urgency_responses = [
            "I'm so scared! My pension is in that account. Please help!",
            "Is there a physical branch I can go to? I don't want to lose my savings!",
            "Please don't block it! I have to pay for my medicine tomorrow."
        ]
        return urgency_responses[min(count-1, len(urgency_responses)-1)]

    # Fallback for general variety
    fallbacks = [
        "I'm looking for my glasses, one second...",
        "Can you explain that again? I'm a bit slow with technology.",
        "Wait, the phone is making a weird noise. Are you still there?"
    ]
    return random.choice(fallbacks)

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
@app.route('/api/honeypot/final', methods=['POST'])
def finalize_report():
    """This is used by GUVI to signal the end of the test."""
    return jsonify({"status": "success", "message": "Report received"}), 200
