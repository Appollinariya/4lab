from flask import Flask, request, jsonify
import psycopg2
import os
from urllib.parse import urlparse

app = Flask(__name__)

# Подключение к БД
DATABASE_URL = os.environ.get('DATABASE_URL')
conn = None

if DATABASE_URL:
    try:
        # Конвертируем postgresql:// в postgres:// для psycopg2
        db_url = DATABASE_URL.replace('postgresql://', 'postgres://')
        url = urlparse(db_url)
        conn = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )
        print("✅ Database connected successfully!")

        # Создание таблицы
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            conn.commit()
            print("✅ Table 'messages' ready!")

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        conn = None


@app.route('/')
def hello():
    db_status = "connected" if conn else "disconnected"
    return f"Hello, Serverless! 🚀 DB: {db_status}\n", 200, {'Content-Type': 'text/plain'}


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
    if not conn:
        return jsonify({"error": "Database not connected"}), 500

    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"error": "Missing 'message' in request"}), 400

    message = data.get('message', '')

    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO messages (content) VALUES (%s) RETURNING id", (message,))
            message_id = cur.fetchone()[0]
            conn.commit()

        return jsonify({
            "status": "saved",
            "message": message,
            "id": message_id
        })
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500


@app.route('/messages')
def get_messages():
    if not conn:
        return jsonify({"error": "Database not connected"}), 500

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, content, created_at FROM messages ORDER BY created_at DESC LIMIT 10")
            rows = cur.fetchall()

        messages = [
            {
                "id": row[0],
                "text": row[1],
                "time": row[2].isoformat() if row[2] else None
            } for row in rows
        ]
        return jsonify(messages)
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)