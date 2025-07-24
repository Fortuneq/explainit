import time, secrets, threading
from flask import Flask, request, jsonify
from g4f.client import Client
from g4f.Provider import OpenaiChat, Yqcloud, You

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
client = Client()
lock = threading.Lock()

RATE_LIMIT_SECONDS = 1
last_request_time = 0

def build_prompt(text: str) -> str:
    return f"""Ты помощник, который объясняет сложные вещи простыми словами.

Вот текст:
\"\"\"{text}\"\"\"

1. Найди термины и фразы, которые могут быть непонятны обычному человеку.
2. Объясни их как другу, без жаргона.
3. Избегай насилия, политики, оскорблений.
4. Формат:
- Термин: [термин]
- Объяснение: [простое объяснение]
"""

def get_response(prompt: str):
    providers = [OpenaiChat, Yqcloud, You]
    for provider in providers:
        try:
            with lock:
                response = client.chat.completions.create(
                    model="gpt-4",
                    provider=provider,
                    messages=[{"role": "user", "content": prompt}],
                    web_search=False,
                )
            return response.choices[0].message.content.strip()
        except Exception:
            continue
    raise Exception("Все провайдеры недоступны.")

@app.route('/explain', methods=['POST'])
def explain():
    global last_request_time
    now = time.time()
    if now - last_request_time < RATE_LIMIT_SECONDS:
        return jsonify({"error": "Слишком частые запросы."}), 429
    last_request_time = now

    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "Нужен 'text'."}), 400

    if any(w in data['text'].lower() for w in ["убить", "террор", "бомба"]):
        return jsonify({"error": "Запрещённый текст."}), 400

    try:
        prompt = build_prompt(data["text"])
        explanation = get_response(prompt)
        return jsonify({"result": explanation})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
