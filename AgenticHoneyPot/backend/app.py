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

import random

# Persistent memory for the bot's narrative state
brain_memory = {}

def get_agentic_reply(session_id, text):
    t = text.lower()
    
    # 1. Initialize session with a specific "Persona" and "Stage"
    if session_id not in brain_memory:
        brain_memory[session_id] = {
            "turn": 0,
            "stage": "CONFUSION", # Transitions: CONFUSION -> STALLING -> PANIC -> SUSPICION
            "persona": random.choice(["elderly", "anxious", "busy"]),
            "extracted_data": []
        }
    
    state = brain_memory[session_id]
    state["turn"] += 1
    turn = state["turn"]

    # 2. Update Narrative Stage based on turn count
    if turn <= 2:
        state["stage"] = "CONFUSION"
    elif 3 <= turn <= 5:
        state["stage"] = "STALLING"
    elif 6 <= turn <= 8:
        state["stage"] = "PANIC"
    else:
        state["stage"] = "SUSPICION"

    # 3. NARRATIVE ENGINE: Response Selection
    
    # STAGE 1: THE "CONFUSED TARGET" (Builds Trust)
    if state["stage"] == "CONFUSION":
        replies = [
            "I'm so sorry, my eyes aren't what they used to be. Is that an 8 or a 0 in the code you sent?",
            "Wait, I see the message! But I accidentally clicked something and it disappeared. Can you send it one more time?"
        ]
        return replies[(turn - 1) % len(replies)]

    # STAGE 2: THE "TECHNICAL FAULT" (Stalls for Time)
    if state["stage"] == "STALLING":
        excuses = [
            "Oh dear, my phone just started a software update! It says 'Restarting...' please don't hang up!",
            "I'm looking for my glasses, I can't find them anywhere. Let me check the kitchen...",
            "The phone is at 1% battery! I'm running to find the charger, stay on the line!"
        ]
        # Offset by 3 since this stage starts at turn 3
        return excuses[min(turn - 3, len(excuses) - 1)]

    # STAGE 3: THE "PANICKED VICTIM" (High Engagement)
    if state["stage"] == "PANIC":
        panic_responses = [
            "I found the wire but it's not charging! I'm shaking, please don't block my pension account!",
            "It's finally turning back on! Okay, I see a 6-digit number... wait, is this for GPay or the Bank?",
            "I'm typing it in now! But it says 'Incorrect PIN'. Are you sure this is the right code for SBI?"
        ]
        return panic_responses[min(turn - 6, len(panic_responses) - 1)]

    # STAGE 4: THE "SKEPTICAL PUSHBACK" (Final Intel Extraction)
    # This stage wastes the scammer's time by making them "prove" themselves
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
