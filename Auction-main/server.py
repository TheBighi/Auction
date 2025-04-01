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
    conn = sqlite3.connect("auctions.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, item_name, start_time, end_time, current_bid FROM auctions")
    auctions = cursor.fetchall()
    conn.close()

    # Convert data into a list of dictionaries
    auction_list = [
        {"id": row[0], "item_name": row[1], "start_time": row[2], "end_time": row[3], "current_bid": row[4]}
        for row in auctions
    ]

    return render_template('auctions.html', auctions=auction_list)

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
                current_bidder TEXT NOT NULL,
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
                current_bidder TEXT NOT NULL,
                FOREIGN KEY (creator) REFERENCES users(id)
            )
        ''')

        cursor.execute('''
            INSERT INTO auctions (creator, item_name, start_time, end_time, starting_bid, current_bid, current_bidder)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (creator, itemname, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), enddate, startbid, startbid, 0))

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

    # Fetch only the auctions created by the user
    conn = sqlite3.connect("auctions.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, creator, item_name, start_time, end_time, current_bid FROM auctions WHERE creator = ?", (user_id,))
    user_auctions = cursor.fetchall()
    conn.close()

    auction_data = [
        {"id": row[0], "creator": row[1],"item_name": row[2], "start_time": row[3], "end_time": row[4], "current_bid": row[5]}
        for row in user_auctions
    ]
    return render_template(
        'account.html', 
        username=user[0], 
        creation_time=user[1], 
        user_id=user_id, 
        auction_data=auction_data
    )

def get_auction(auction_id):
    conn = sqlite3.connect("auctions.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, creator, item_name, start_time, end_time, current_bid FROM auctions WHERE id = ?", (auction_id,))
    auction = cursor.fetchone()
    conn.close()

    if auction:
        return {
            "id": auction[0],  # Include id here
            "creator": auction[1],
            "item_name": auction[2],
            "start_time": auction[3],
            "end_time": auction[4],
            "current_bid": auction[5]
        }
    return None

@app.route('/auction/<int:auction_id>')
def auction_page(auction_id):
    user_id = session.get('user_id')  # Use .get() to avoid KeyError if not set
    print("A")
    
    auction = get_auction(auction_id)
    conn = sqlite3.connect("auctions.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT creator FROM auctions WHERE id = ?", (auction_id,))
    creator = cursor.fetchone()
    
    conn.close()

    if creator:
        creator = creator[0]  # Extract value from tuple
        print(f"Creator: {creator}")
    else:
        print("No data found")
        creator = None

    print(f"Session ID: {user_id}")

    if auction:
        return render_template("auction.html", auction=auction, creator=creator, user_id=user_id)
    
    return "Auction not found", 404

@app.route('/auction/<int:auction_id>', methods=['GET', 'POST'])
def auction_detail(auction_id):  # Renamed from auction_page
    print("B")
    auction = get_auction(auction_id)
    user_id = session['user_id']

    if not auction:
        return "Auction not found", 404


    if request.method == 'POST':
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('login'))

        new_bid = float(request.form['bid'])

        if new_bid <= auction['current_bid']:
            return "Bid must be higher than the current bid.", 400

        conn = sqlite3.connect("auctions.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE auctions SET current_bid = ? WHERE id = ?", (new_bid, auction_id))
        cursor.execute("UPDATE auctions SET current_bidder = ? WHERE id = ?", (user_id, auction_id))
        conn.commit()
        conn.close()

        return redirect(url_for('auction_detail', auction_id=auction_id))

    return render_template("auction.html", auction=auction)

@app.route('/delete_auction/<int:auction_id>', methods=['POST'])
def delete_auction(auction_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    conn = sqlite3.connect('auctions.db')
    cursor = conn.cursor()

    # Check if the auction exists and if the current user is the creator
    cursor.execute("SELECT creator FROM auctions WHERE id = ?", (auction_id,))
    auction = cursor.fetchone()

    if not auction:
        conn.close()
        return "Auction not found", 404

    if auction[0] != user_id:
        conn.close()
        return "Unauthorized", 403

    # Delete the auction
    cursor.execute("DELETE FROM auctions WHERE id = ?", (auction_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('auctions'))
    
if __name__ == '__main__':
    app.run(debug=True, port=8080)
