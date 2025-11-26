from flask import Flask, request, jsonify
import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, text
from sqlalchemy.orm import declarative_base, Session
from datetime import datetime

app = Flask(__name__)

# Подключение к БД через SQLAlchemy
DATABASE_URL = os.environ.get('DATABASE_URL')
engine = None
Base = declarative_base()


class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


if DATABASE_URL:
    try:
        # Используем SQLAlchemy для подключения
        engine = create_engine(DATABASE_URL)

        # Создаем таблицу
        Base.metadata.create_all(engine)
        print("✅ Database connected successfully!")
        print("✅ Table 'messages' ready!")

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        engine = None


@app.route('/')
def hello():
    db_status = "connected" if engine else "disconnected"
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
    if not engine:
        return jsonify({"error": "Database not connected"}), 500

    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"error": "Missing 'message' in request"}), 400

    message_text = data.get('message', '')

    try:
        with Session(engine) as session:
            # Используем raw SQL для совместимости
            result = session.execute(
                text("INSERT INTO messages (content) VALUES (:content) RETURNING id"),
                {"content": message_text}
            )
            message_id = result.scalar()
            session.commit()

        return jsonify({
            "status": "saved",
            "message": message_text,
            "id": message_id
        })
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500


@app.route('/messages')
def get_messages():
    if not engine:
        return jsonify({"error": "Database not connected"}), 500

    try:
        with Session(engine) as session:
            result = session.execute(
                text("SELECT id, content, created_at FROM messages ORDER BY created_at DESC LIMIT 10")
            )
            rows = result.fetchall()

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