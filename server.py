from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_cors import CORS
import sqlite3
import random
import time
from flask_socketio import SocketIO, emit
import datetime

def generate_user_id():
    return random.randint(100000000, 999999999)

app = Flask(__name__)
CORS(app) 
socketio = SocketIO(app, cors_allowed_origins="*")

app.secret_key = '123abc'

def user_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            creation_time DATETIME NOT NULL
        )
    ''')

    conn.commit()
    cursor.close()
    conn.close()
user_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/about')
def about():
    return render_template('about.html')
#def init_db():
#    conn = sqlite3.connect('auctions.db')
#    cursor = conn.cursor()
#    
#    cursor.execute('''
#        CREATE TABLE IF NOT EXISTS auctions (
#            id INTEGER PRIMARY KEY AUTOINCREMENT,
#            item_name TEXT NOT NULL,
#            start_time DATETIME NOT NULL,
#            end_time DATETIME NOT NULL,
#            starting_bid REAL NOT NULL,
#            current_bid REAL
#        )
#    ''')
#
#    conn.commit()
#    cursor.close()
#    conn.close()
#init_db()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        # Check if the user exists
        cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()

        if user:
            session['user_id'] = user[0]  # Store user ID in session
        else:
            # Auto-register the user
            new_id = generate_user_id()
            creation_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("INSERT INTO users (id, username, password, creation_time) VALUES (?, ?, ?, ?)", 
                           (new_id, username, password, creation_time))
            conn.commit()
            session['user_id'] = new_id

        conn.close()
        return redirect(f'/account/{session["user_id"]}')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')
@app.route('/account/<int:user_id>')
def account(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, creation_time FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return "User not found", 404

    return render_template('account.html', username=user[0], creation_time=user[1], user_id=user_id)

if __name__ == '__main__':
    app.run(debug=True, port=8080)
