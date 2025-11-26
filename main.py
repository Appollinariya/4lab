from flask import Flask, request, jsonify
import psycopg
import os
from datetime import datetime

app = Flask(__name__)

# Глобальное подключение к БД
db_connection = None


def init_database():
    """Инициализация подключения к базе данных"""
    global db_connection

    DATABASE_URL = os.environ.get('DATABASE_URL')

    if not DATABASE_URL:
        print("❌ DATABASE_URL not found in environment variables")
        return

    try:
        # Подключаемся к PostgreSQL используя psycopg
        db_connection = psycopg.connect(DATABASE_URL)
        print("✅ Successfully connected to PostgreSQL database!")

        # Создаем таблицу если её нет
        with db_connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db_connection.commit()
            print("✅ Table 'messages' is ready!")

    except Exception as error:
        print(f"❌ Database connection failed: {error}")
        db_connection = None


# Инициализируем базу при запуске
init_database()


@app.route('/')
def home():
    """Главная страница с статусом БД"""
    db_status = "connected" if db_connection else "disconnected"
    return f"Hello, Serverless! 🚀 PostgreSQL: {db_status}\n"


@app.route('/save', methods=['POST'])
def save_message():
    """Сохранить сообщение в базу данных"""
    if not db_connection:
        return jsonify({"error": "Database not available"}), 503

    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    message_content = data.get('message', '').strip()
    if not message_content:
        return jsonify({"error": "Message content is empty"}), 400

    try:
        with db_connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO messages (content) VALUES (%s) RETURNING id, created_at",
                (message_content,)
            )
            result = cursor.fetchone()
            db_connection.commit()

            message_id, created_at = result

            return jsonify({
                "status": "success",
                "message": "Message saved to database",
                "data": {
                    "id": message_id,
                    "content": message_content,
                    "created_at": created_at.isoformat()
                }
            })

    except Exception as error:
        return jsonify({"error": f"Database error: {str(error)}"}), 500


@app.route('/messages')
def get_messages():
    """Получить последние 10 сообщений из базы"""
    if not db_connection:
        return jsonify({"error": "Database not available"}), 503

    try:
        with db_connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, content, created_at 
                FROM messages 
                ORDER BY created_at DESC 
                LIMIT 10
            """)

            messages = []
            for row in cursor.fetchall():
                messages.append({
                    "id": row[0],
                    "content": row[1],
                    "created_at": row[2].isoformat()
                })

            return jsonify({
                "status": "success",
                "count": len(messages),
                "messages": messages
            })

    except Exception as error:
        return jsonify({"error": f"Database error: {str(error)}"}), 500


@app.route('/echo', methods=['POST'])
def echo():
    """Тестовый endpoint"""
    data = request.get_json()
    return jsonify({
        "status": "received",
        "you_sent": data,
        "timestamp": datetime.now().isoformat()
    })


@app.route('/health')
def health_check():
    """Проверка здоровья приложения и базы данных"""
    db_status = "healthy" if db_connection else "unhealthy"

    try:
        if db_connection:
            with db_connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM messages")
                message_count = cursor.fetchone()[0]
        else:
            message_count = 0

        return jsonify({
            "status": "ok",
            "database": db_status,
            "message_count": message_count,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as error:
        return jsonify({
            "status": "error",
            "database": "unhealthy",
            "error": str(error)
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)