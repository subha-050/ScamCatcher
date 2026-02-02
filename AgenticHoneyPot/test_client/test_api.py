import requests

API_URL = "http://localhost:5000/api/honeypot"
FINAL_URL = "http://localhost:5000/api/honeypot/final"
API_KEY = "your_secret_api_key_here"

session_id = "test-session-001"

messages = [
    "Your bank account will be blocked today. Verify immediately.",
    "Share your UPI ID to avoid account suspension."
]

conversation_history = []

for msg in messages:
    payload = {
        "sessionId": session_id,
        "message": {"sender": "scammer", "text": msg, "timestamp": "2026-01-31T10:00:00Z"},
        "conversationHistory": conversation_history,
        "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
    }
    response = requests.post(API_URL, json=payload, headers={"x-api-key": API_KEY})
    print(response.json())
    conversation_history.append({"sender": "scammer", "text": msg})

final_payload = {"sessionId": session_id}
response = requests.post(FINAL_URL, json=final_payload, headers={"x-api-key": API_KEY})
print(response.json())
