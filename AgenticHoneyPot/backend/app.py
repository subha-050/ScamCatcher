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

import time, random

# Internal memory to track the "Victim's" mental state
brain_memory = {}

def get_agentic_reply(session_id, text):
    # 1. Initialize a unique persona for this scammer
    if session_id not in brain_memory:
        brain_memory[session_id] = {
            "turn": 0,
            "fear_level": 0.2,  # 0 to 1
            "tech_confusion": 0.5,
            "persona": random.choice(["Elderly", "Busy Professional", "Naive Student"])
        }
    
    state = brain_memory[session_id]
    state["turn"] += 1
    t = text.lower()

    # 2. Simulate "Thinking Time" (Scammers don't trust instant replies)
    time.sleep(random.uniform(1.5, 3.5))

    # 3. Brain Logic: Intent-Based Emotional Shifting
    if any(x in t for x in ["police", "block", "jail", "urgent"]):
        state["fear_level"] += 0.2
    if any(x in t for x in ["otp", "pin", "password"]):
        state["tech_confusion"] += 0.1

    # 4. Generate Narrative Response based on Persona & State
    if state["fear_level"] > 0.7:
        return "Please don't block my account! I'm shaking right now. I'll get the code, just give me a minute to find my phone charger!"
    
    if state["turn"] > 6:
        return "Wait... my daughter just told me that banks never ask for OTPs over SMS. Are you really from the head office? What was your employee ID again?"

    # Turn-based variety for Credential requests
    if "otp" in t or "code" in t:
        excuses = [
            "I see the message but my screen is cracked, I can't tell if that's an 8 or a 0. Can you resend?",
            "My phone just did a software update right when the text came! It's restarting now, hang on.",
            "I think I found it... it's 6 digits, right? Oh wait, that was from my grocery delivery. One sec."
        ]
        return excuses[min(state["turn"]-1, len(excuses)-1)]

    return "I'm trying to follow along, but this new app is so confusing. Could you explain that last part one more time, very slowly?"
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
