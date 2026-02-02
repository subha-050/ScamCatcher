# 🎣 Scam-Baiter 3000 (Scam catcher HoneyPot Ai)
### *Helping scammers waste their time since 2026.*

Hey everyone! 👋 This is my project for the GUVI Hackathon. 

The idea is simple: Scammers are annoying. So, I built an AI "Honey-Pot" that acts like a clueless target to keep scammers talking. While they think they're about to get paid, my bot is secretly stealing their **UPI IDs**, **phishing links**, and **phone numbers**. 

## 🧠 What’s under the hood?
I didn't just want a bot that says "Hello." I wanted a bot with a brain.
* **Drama Meter (Threat Scoring):** My bot calculates how "scammy" a message is. If the scammer sends a link, the bot starts acting "scared" and "confused" to keep the scammer hooked.
* **Never Forgets:** I added a persistence layer (`session_store.json`). Even if the server crashes, the bot remembers everything the scammer said.
* **Indian Tech Support:** Tuned the regex specifically to catch Indian UPI IDs and +91 phone numbers. 🇮🇳
* **Auto-Snitch:** Once the conversation is done, it automatically sends a full report to the GUVI servers. 🚔

## 🛠️ How to mess with it (Testing)
If you want to test it out, hit these endpoints:

1. **The Chat:** `POST /api/honeypot`
   (Send it something like: "Hey, give me your bank login!")
2. **The Receipt:** `POST /api/honeypot/final`
   (This shows you all the "intelligence" the bot gathered.)

## 💻 Tech Stack
* **Flask** (The backbone)
* **Regex** (The detective work)
* **JSON** (The memory)
* **Coffee** (The fuel)

Built with ☕ and ❤️ for the GUVI Hackathon!!
