import re, os, random
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

API_KEY = "sk_test_5f2a9b1c8e3d4f5a6b7c"

# --- INTELLIGENCE ENGINE ---
class HoneyIntel:
    @staticmethod
    def extract(text):
        return {
            "upi": list(set(re.findall(r'[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}', text))),
            "urls": list(set(re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', text))),
            "phones": list(set(re.findall(r'(?:\+91|0)?[6-9]\d{9}', text))),
            "accounts": list(set(re.findall(r'\b\d{9,18}\b', text)))
        }

# --- CONVERSATION STATE ---
# In a real win-ready app, we track state by sessionId to avoid repeating
memory = {}

def get_agentic_reply(session_id, text):
    t = text.lower()
    
    # Initialize session state if new
    if session_id not in memory:
        memory[session_id] = {"turn": 0, "history": []}
    
    state = memory[session_id]
    state["turn"] += 1
    
    # Logic: Dynamic responses based on context + turn count to prevent repetition
    if "upi" in t or "pay" in t:
        replies = [
            "My UPI app is saying 'Security Risk' and won't let me pay. Is there another ID?",
            "I'm at the payment screen. It's asking for a 'Remark'. Should I type 'Security Check'?",
            "Wait, the name on the UPI ID doesn't match the bank. Are you sure this is correct?"
        ]
        return replies[min(state["turn"]-1, len(replies)-1)]

    if "kyc" in t or "block" in t or "suspend" in t:
        replies = [
            "I'm so scared! My salary is in that account. What do I need to do first?",
            "I'm trying to click the link but my phone says it's unsafe. Can you send it again?",
            "Is there a physical branch I can go to? I'm really panicking right now."
        ]
        return replies[min(state["turn"]-1, len(replies)-1)]

    if "otp" in t or "code" in t:
        replies = [
            "I see the SMS, but my screen is cracked and I can't read the last two digits. One sec...",
            "The code just expired. Can you trigger a new one for me?",
            "I got the code. It's 4... wait, my phone just restarted! Can we try again?"
        ]
        return replies[min(state["turn"]-1, len(replies)-1)]

    # Fallback to keep the scammer engaged
    return "I'm a bit old and slow with these things. Can you walk me through it slowly?"

@app.route('/', methods=['GET', 'POST', 'HEAD', 'OPTIONS'])
@app.route('/api/honeypot', methods=['GET', 'POST', 'HEAD', 'OPTIONS'])
def honeypot_v4():
    # 1. Seamless Connection Handler
    if request.method in ['GET', 'HEAD', 'OPTIONS']:
        res = make_response(jsonify({"status": "active"}), 200)
        res.headers["Access-Control-Allow-Origin"] = "*"
        return res

    # 2. Security Check
    if request.headers.get("x-api-key") != API_KEY:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    # 3. Data Processing
    data = request.get_json(force=True, silent=True) or {}
    session_id = data.get("sessionId") or "global_session"
    msg_obj = data.get("message", {})
    msg_text = msg_obj.get("text", str(msg_obj))

    # 4. Intelligence & Response
    intel = HoneyIntel.extract(msg_text)
    reply = get_agentic_reply(session_id, msg_text)

    return jsonify({
        "status": "success",
        "reply": reply,
        "sessionId": session_id,
        "scamDetected": True,
        "extractedIntelligence": {
            "upiIds": intel["upi"],
            "phishingLinks": intel["urls"],
            "phoneNumbers": intel["phones"],
            "bankAccounts": intel["accounts"]
        }
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
