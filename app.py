import logging
import os

from flask import Flask, jsonify, render_template, request
from flask_mysqldb import MySQL

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = 500


def require_env(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


app = Flask(__name__)

app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST', 'mysql')
app.config['MYSQL_USER'] = require_env('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = require_env('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = require_env('MYSQL_DB')
app.config['MYSQL_CHARSET'] = 'utf8mb4'  # supports emoji

mysql = MySQL(app)


def init_db():
    """Safety net: the table is normally created by message.sql."""
    try:
        with app.app_context():
            cur = mysql.connection.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    message TEXT
                ) DEFAULT CHARSET=utf8mb4
            ''')
            mysql.connection.commit()
            cur.close()
    except Exception:
        log.exception("init_db failed; will retry on first request")


init_db()  # runs under both `python app.py` and gunicorn


@app.route('/health')
def health():
    """Liveness: the app process is up."""
    return jsonify(status='ok'), 200


@app.route('/ready')
def ready():
    """Readiness: the app can reach the database."""
    try:
        cur = mysql.connection.cursor()
        cur.execute('SELECT 1')
        cur.close()
        return jsonify(status='ready'), 200
    except Exception:
        log.exception("readiness check failed")
        return jsonify(status='db unavailable'), 503


@app.route('/')
def hello():
    try:
        cur = mysql.connection.cursor()
        cur.execute('SELECT message FROM messages ORDER BY id')
        messages = cur.fetchall()
        cur.close()
    except Exception:
        log.exception("failed to load messages")
        return jsonify(error='Database unavailable'), 500
    return render_template('index.html', messages=messages)


@app.route('/submit', methods=['POST'])
def submit():
    new_message = (request.form.get('new_message') or '').strip()
    if not new_message:
        return jsonify(error='Message is required'), 400
    if len(new_message) > MAX_MESSAGE_LENGTH:
        return jsonify(error=f'Message must be at most {MAX_MESSAGE_LENGTH} characters'), 400
    try:
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO messages (message) VALUES (%s)', [new_message])
        mysql.connection.commit()
        cur.close()
    except Exception:
        log.exception("failed to save message")
        return jsonify(error='Database unavailable'), 500
    return jsonify(message=new_message)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
