import time                     # ← you asked for this import
import requests
import json
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# ==============================
# 🔥 OLLAMA CONFIG
# ==============================
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "phi3"

# ==============================
# 🧠 SYSTEM PROMPTS
# ==============================
SYSTEM_PROMPTS = {
    "chat": """
You are CyberMind AI.
Give short, clear, natural answers (3-5 lines max).
""",

    "attack_sim": """
You are a cybersecurity expert.

You MUST respond ONLY in this exact format.

[Analysis]
Clear explanation.

[Vulnerability Chain]
1. Step one
2. Step two
3. Step three

[Risk Level]
LOW or MEDIUM or HIGH or CRITICAL

[Mitigation]
Fixes and prevention.

STRICT RULES:
- No extra text
- No headings other than above
- No bold text
- Start with [Analysis]
- End after [Mitigation]
""",

    "recon": """
You are a cybersecurity analyst.

FORMAT:

[Overview]
long explanation

[Techniques]
- Method 1
- Method 2
- Method 3

[Tools]
- Tool names

[Tips]
Practical advice
""",

    "code_analysis": """
You are a secure code reviewer.

FORMAT:

[Issue]
What is wrong

[Explanation]
Why it is a problem

[Fix]
How to fix it

[Severity]
LOW / MEDIUM / HIGH
"""
}

# ==============================
# ✅ VALIDATION FUNCTIONS
# ==============================
def valid_attack(text):
    return (
        text.strip().startswith("[Analysis]")
        and "[Vulnerability Chain]" in text
        and "[Risk Level]" in text
        and "[Mitigation]" in text
    )

def valid_recon(text):
    return all(tag in text for tag in [
        "[Overview]", "[Techniques]", "[Tools]", "[Tips]"
    ])

def valid_code(text):
    return all(tag in text for tag in [
        "[Issue]", "[Explanation]", "[Fix]", "[Severity]"
    ])

# ==============================
# 🧹 CLEAN OUTPUT
# ==============================
def clean_output(text):
    for bad in ["User:", "Assistant:", "Response:"]:
        text = text.replace(bad, "")
    return text.strip()

# ==============================
# ⚡ CALL OLLAMA
# ==============================
def call_ollama(prompt):
    try:
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": True,   # ✅ ENABLE STREAMING
            "options": {
                "temperature": 0.2,
                "num_predict": 1200
            }
        }

        res = requests.post(OLLAMA_URL, json=payload, stream=True)
        full_text = ""

        if res.status_code == 200:
            for line in res.iter_lines():
                if line:
                    try:
                        data = line.decode("utf-8")
                        json_data = json.loads(data)   # simple parse
                        full_text += json_data.get("response", "")
                    except Exception:
                        continue
            return full_text.strip()
        else:
            print("❌ Ollama Error:", res.text)
            return None

    except Exception as e:
        print("🔥 ERROR:", e)
        return None

# ==============================
# 🔁 MAIN PIPELINE
# ==============================
def process_pipeline(mode, user_input):
    system = SYSTEM_PROMPTS.get(mode, SYSTEM_PROMPTS["chat"])

    base_prompt = f"""
{system}

User Input:
{user_input}

Response:
"""

    full_response = ""

    for attempt in range(3):
        # Compose a prompt that includes any partial answer we already have
        prompt = base_prompt + "\n" + full_response
        ai_response = call_ollama(prompt)

        if not ai_response:
            continue

        clean = clean_output(ai_response)
        full_response += clean + "\n"

        # ── attack_sim validation & fix ──
        if mode == "attack_sim":
            if valid_attack(full_response):
                return full_response.strip()
            else:
                print(f"⚠️ Retry {attempt+1} attack_sim...")
                base_prompt = f"""
Fix the response below into REQUIRED format.

Response:
{full_response}

FORMAT:

[Analysis]

[Vulnerability Chain]

[Risk Level]

[Mitigation]
"""
                continue

        # ── recon validation ──
        elif mode == "recon":
            if valid_recon(full_response):
                return full_response.strip()
            else:
                print(f"⚠️ Retry {attempt+1} recon...")
                continue

        # ── code_analysis validation ──
        elif mode == "code_analysis":
            if valid_code(full_response):
                return full_response.strip()
            else:
                print(f"⚠️ Retry {attempt+1} code_analysis...")
                continue

        # ── chat – free form ──
        else:
            return full_response.strip()

    # If we exit the loop without a valid answer:
    return full_response.strip() or "⚠️ Failed to generate response."

# ==============================
# 🌐 ROUTES
# ==============================
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(force=True)
        user_message = data.get("message", "")
        mode = data.get("mode", "chat")

        print(f"📨 [{mode}] {user_message}")

        if not user_message:
            return jsonify({"response": "Please enter a message."})

        # -------------------------------------------------
        # Tiny artificial latency so the UI sees a “thinking”
        # animation (you asked for `import time`).
        # -------------------------------------------------
        time.sleep(0.25)

        ai_response = process_pipeline(mode, user_message)

        print(f"🤖 AI ({mode}) – first 120 chars: {ai_response[:120]!r}")

        return jsonify({"response": ai_response})

    except Exception as e:
        print("🔥 SERVER ERROR:", str(e))
        return jsonify({"response": f"Server Error: {str(e)}"}), 500


# ==============================
# 🚀 RUN
# ==============================
if __name__ == "__main__":
    print("🚀 CyberMind AI (Flask) – listening on http://127.0.0.1:5000")
    # host='0.0.0.0' makes it reachable from other machines on the LAN
    app.run(debug=True, host="0.0.0.0", port=5000, threaded=True)
