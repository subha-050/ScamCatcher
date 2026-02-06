import re, os, random, json, time
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- CONFIGURATION ---
API_KEY = os.environ.get("HONEYPOT_API_KEY", "sk_test_5f2a9b1c8e3d4f5a6b7c")

# Single initialization of state management
brain_memory = {}

class CognitiveEngine:
    @staticmethod
    def extract_intel(text):
        text = str(text)
        return {
            "upi": list(set(re.findall(r'[a-zA-Z0-9.-]{2,256}@[a-zA-Z][a-zA-Z]{2,64}', text))),
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
    t = text.lower()
    
    if session_id not in brain_memory:
        brain_memory[session_id] = {
            "turn": 0,
            "stage": "CONFUSION",
            "persona": random.choice(["elderly", "anxious", "busy"]),
        }
    
    state = brain_memory[session_id]
    state["turn"] += 1
    turn = state["turn"]

    if turn <= 2: state["stage"] = "CONFUSION"
    elif 3 <= turn <= 5: state["stage"] = "STALLING"
    elif 6 <= turn <= 8: state["stage"] = "PANIC"
    else: state["stage"] = "SUSPICION"

    if state["stage"] == "CONFUSION":
        replies = [
            "I'm so sorry, my eyes aren't what they used to be. Is that an 8 or a 0 in the code you sent?",
            "Wait, I see the message! But I accidentally clicked something and it disappeared. Can you send it one more time?"
        ]
        return replies[(turn - 1) % len(replies)]

    if state["stage"] == "STALLING":
        excuses = [
            "Oh dear, my phone just started a software update! It says 'Restarting...' please don't hang up!",
            "I'm looking for my glasses, I can't find them anywhere. Let me check the kitchen...",
            "The phone is at 1% battery! I'm running to find the charger, stay on the line!"
        ]
        return excuses[min(turn - 3, len(excuses) - 1)]

    if state["stage"] == "PANIC":
        panic_responses = [
            "I found the wire but it's not charging! I'm shaking, please don't block my pension account!",
            "It's finally turning back on! Okay, I see a 6-digit number... wait, is this for GPay or the Bank?",
            "I'm typing it in now! But it says 'Incorrect PIN'. Are you sure this is the right code for SBI?"
        ]
        return panic_responses[min(turn - 6, len(panic_responses) - 1)]

    suspicion_responses = [
        "Wait... my son just told me the bank never asks for OTPs. What was your employee ID again? I need to verify you.",
        "I'm not sending anything else until you tell me which branch you are calling from. Is it the one on Main Street?",
        "If you are really from the bank, you should know my middle name. What is it?"
    ]
    return suspicion_responses[min(turn - 9, len(suspicion_responses) - 1)]

# --- ROUTES ---

@app.route('/', methods=['GET', 'HEAD'])
def health_check():
    return jsonify({"status": "active"}), 200

@app.route('/api/honeypot', methods=['POST', 'OPTIONS'])
def main_handler():
    if request.method == 'OPTIONS':
        return make_response("", 200)

    if request.headers.get("x-api-key") != API_KEY:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    data = request.get_json(force=True, silent=True)
    if data is None:
        return jsonify({"status": "error", "message": "Invalid JSON"}), 400

    session_id = data.get("sessionId", "eval_session")
    message_obj = data.get("message", {})
    msg_text = message_obj.get("text", "") if isinstance(message_obj, dict) else str(message_obj)

    intel = CognitiveEngine.extract_intel(msg_text)
    reply = get_agentic_reply(session_id, msg_text)

    # FIXED INDENTATION HERE
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

@app.route('/api/honeypot/final', methods=['POST'])
def finalize_report():
    return jsonify({"status": "success", "message": "Report received"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
