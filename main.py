from flask import Flask, request, jsonify
from datetime import datetime
import os

app = Flask(__name__)

# Имитация базы данных в памяти
messages_storage = []
next_id = 1


@app.route('/')
def hello():
    return "Hello, Serverless! 🚀 Simple memory storage\n", 200, {'Content-Type': 'text/plain'}


@app.route('/echo', methods=['POST'])
def echo():
    data = request.get_json()
    return jsonify({
        "status": "received",
        "you_sent": data,
        "length": len(str(data)) if data else 0
    })


@app.route('/save', methods=['POST'])
def save_message():
    global next_id

    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"error": "Missing 'message' in request"}), 400

    message_text = data.get('message', '')

    message = {
        "id": next_id,
        "text": message_text,
        "time": datetime.now().isoformat()
    }
    messages_storage.append(message)
    next_id += 1

    return jsonify({
        "status": "saved",
        "message": message_text,
        "id": message["id"]
    })


@app.route('/messages')
def get_messages():
    recent_messages = messages_storage[-10:] if messages_storage else []
    return jsonify(recent_messages)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)