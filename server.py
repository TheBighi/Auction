from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
from flask_socketio import SocketIO, emit
import time
from flask import request

app = Flask(__name__)
CORS(app) 
#socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def home():
    return render_template('index.html')

def init_db():
    conn = sqlite3.connect('auctions.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS auctions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            start_time DATETIME NOT NULL,
            end_time DATETIME NOT NULL,
            starting_bid REAL NOT NULL,
            current_bid REAL
        )
    ''')
    
    conn.commit()
    cursor.close()
    conn.close()
init_db()