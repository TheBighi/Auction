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
@app.route('/auctions')
def auctions():
    return render_template('auctions.html')
def init_db():
    conn = sqlite3.connect('auctions.db')
    cursor = conn.cursor()
    
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS auctions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                creator INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                start_time DATETIME NOT NULL,
                end_time DATETIME NOT NULL,
                starting_bid REAL NOT NULL,
                current_bid REAL,
                FOREIGN KEY (creator) REFERENCES users(id)
            )
        ''')

    conn.commit()
    cursor.close()
    conn.close()

init_db()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        # username exist?
        cursor.execute("SELECT id, password FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if user:
            stored_password = user[1]
            if stored_password == password:
                session['user_id'] = user[0]
                conn.close()
                return redirect(f'/account/{session["user_id"]}')
            else:
                conn.close()
                return "Invalid password. Login denied.", 403  # 403 kui vale password
        else:
            # reg username if not exist
            new_id = generate_user_id()
            creation_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("INSERT INTO users (id, username, password, creation_time) VALUES (?, ?, ?, ?)", 
                           (new_id, username, password, creation_time))
            conn.commit()
            session['user_id'] = new_id
            conn.close()
            return redirect(f'/account/{session["user_id"]}')

    return render_template('login.html')

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        # current userid getter
        creator = session.get('user_id')
        if not creator:
            return "You need to be logged in to create an auction.", 403

        itemname = request.form['itemname']
        enddate = request.form['enddate']
        startbid = request.form['startbid']

        conn = sqlite3.connect('auctions.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS auctions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                creator INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                start_time DATETIME NOT NULL,
                end_time DATETIME NOT NULL,
                starting_bid REAL NOT NULL,
                current_bid REAL,
                FOREIGN KEY (creator) REFERENCES users(id)
            )
        ''')

        cursor.execute('''
            INSERT INTO auctions (creator, item_name, start_time, end_time, starting_bid, current_bid)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (creator, itemname, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), enddate, startbid, startbid))

        conn.commit()
        conn.close()

        return redirect(f'/')

    return render_template('create.html')

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
