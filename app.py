# app.py
# The main file of the You Mocha Me Crazy Coffee Ordering System.
# It runs the website: the login page, the order screen, paying, and the sales records.

import os
import sqlite3
from datetime import datetime, timezone, timedelta

from flask import Flask, render_template, request, redirect, session, jsonify
from werkzeug.security import check_password_hash

import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY   # needed so the system can remember who is logged in

# The folder of this project, and the full path of the database file
FOLDER = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(FOLDER, config.DB_FILE)

# Philippine time (UTC+8), used for the date and time of each order
PH_TIME = timezone(timedelta(hours=8))

# The three menu categories, shown as tabs
CATEGORIES = ['Coffee', 'Non Coffee', 'Pastry']

# Brown shades used as the background of each item picture
COLORS = ['#6B4430', '#AE7A50', '#9C6A45', '#C99B6C', '#5A3524', '#C8874B']


# ----- CONNECT TO THE DATABASE -----
def connect():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row   # give results as named columns, for example row['name']
    return db


# ----- CREATE THE DATABASE THE FIRST TIME -----
# If the database file does not exist yet, create the tables and add the
# cashier accounts and menu items from database.sql
def create_database():
    if not os.path.exists(DB_PATH):
        db = connect()
        with open(os.path.join(FOLDER, 'database.sql')) as sql_file:
            db.executescript(sql_file.read())
        db.commit()
        db.close()


create_database()


# ----- CHECK IF SOMEONE IS LOGGED IN -----
def is_logged_in():
    return 'user_id' in session


# ----- LOGIN PAGE -----
@app.route('/', methods=['GET', 'POST'])
def login():
    # If the cashier is already logged in, go straight to the order screen
    if is_logged_in():
        return redirect('/order')

    error = ''
    username = ''

    # This part runs only when the Sign In button is pressed
    if request.method == 'POST':
        # Step 1: Get what the cashier typed
        username = request.form['username'].strip()
        password = request.form['password']

        # Step 2: Look for that username in the users table
        db = connect()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        db.close()

        # Step 3: Check if the user exists and the password is correct
        if user and check_password_hash(user['password'], password):
            # Correct: remember the user and open the order screen
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            return redirect('/order')
        else:
            # Wrong: show a message and let them try again
            error = 'Wrong username or password. Please try again.'

    return render_template('login.html', error=error, username=username)


# ----- ORDER SCREEN -----
@app.route('/order')
def order():
    # Only logged in cashiers can open this page
    if not is_logged_in():
        return redirect('/')

    # Get all the products from the database
    db = connect()
    rows = db.execute('SELECT * FROM products ORDER BY product_id').fetchall()
    db.close()

    # Give each product a brown shade for its picture
    products = []
    number = 0
    for row in rows:
        product = dict(row)
        product['color'] = COLORS[number % len(COLORS)]
        products.append(product)
        number = number + 1

    return render_template('order.html', products=products, categories=CATEGORIES,
                           username=session['username'])


# ----- PAY (SAVE THE ORDER) -----
# The order screen sends the list of items here when Pay is pressed.
@app.route('/pay', methods=['POST'])
def pay():
    # Stop if the cashier is not logged in
    if not is_logged_in():
        return jsonify(ok=False, message='Please sign in again.')

    # Step 1: Read the items sent by the order screen
    # Example: [ {"product_id": 2, "quantity": 2}, {"product_id": 4, "quantity": 1} ]
    data = request.get_json()
    items = data.get('items', [])

    if len(items) == 0:
        return jsonify(ok=False, message='The order is empty.')

    db = connect()
    try:
        # Step 2: Get the real price of each item from the database
        # and compute the subtotal and the total.
        # We do not trust the price from the screen, we always use the database price.
        total = 0
        order_items = []

        for item in items:
            product_id = int(item['product_id'])
            quantity = int(item['quantity'])

            product = db.execute('SELECT price FROM products WHERE product_id = ?', (product_id,)).fetchone()

            # Skip items that do not exist or have a wrong quantity
            if product is None or quantity < 1:
                continue

            subtotal = product['price'] * quantity
            total = total + subtotal
            order_items.append({'product_id': product_id, 'quantity': quantity, 'subtotal': subtotal})

        # Stop if none of the items were valid
        if len(order_items) == 0:
            return jsonify(ok=False, message='The order is empty.')

        # Step 3: Save the order (who took it, the date and time, and the total)
        now = datetime.now(PH_TIME).strftime('%Y-%m-%d %H:%M:%S')
        cursor = db.execute('INSERT INTO orders (user_id, order_date, total) VALUES (?, ?, ?)',
                            (session['user_id'], now, total))
        order_id = cursor.lastrowid   # the new order number

        # Step 4: Save each item of the order
        for order_item in order_items:
            db.execute('INSERT INTO order_items (order_id, product_id, quantity, subtotal) VALUES (?, ?, ?, ?)',
                       (order_id, order_item['product_id'], order_item['quantity'], order_item['subtotal']))

        # Save everything together. If something failed above, nothing is saved.
        db.commit()
    except Exception:
        db.rollback()   # cancel everything if there was a problem
        return jsonify(ok=False, message='Could not save the order. Please try again.')
    finally:
        db.close()

    # Step 5: Tell the order screen it worked, with the order number and total
    return jsonify(ok=True, order_id=order_id, total=total)


# ----- SALES RECORDS -----
@app.route('/sales')
def sales():
    if not is_logged_in():
        return redirect('/')

    today = datetime.now(PH_TIME).strftime('%Y-%m-%d')

    db = connect()

    # Count today's orders and add up today's sales
    summary = db.execute('SELECT COUNT(*) AS order_count, SUM(total) AS sales FROM orders WHERE DATE(order_date) = ?',
                         (today,)).fetchone()

    # Get the 50 latest orders together with the name of the cashier who took them
    rows = db.execute('''
        SELECT orders.order_id, orders.order_date, orders.total, users.username
        FROM orders
        JOIN users ON users.user_id = orders.user_id
        ORDER BY orders.order_id DESC
        LIMIT 50
    ''').fetchall()

    orders = []
    for row in rows:
        each_order = dict(row)

        # Show the date like "Nov 25, 2026 06:09 PM"
        date = datetime.strptime(each_order['order_date'], '%Y-%m-%d %H:%M:%S')
        each_order['order_date'] = date.strftime('%b %d, %Y %I:%M %p')

        # Get the items inside the order, for example "2x Cafe Latte, 1x Mocha"
        items = db.execute('''
            SELECT order_items.quantity, products.name
            FROM order_items
            JOIN products ON products.product_id = order_items.product_id
            WHERE order_items.order_id = ?
        ''', (each_order['order_id'],)).fetchall()
        item_list = []
        for item in items:
            item_list.append(str(item['quantity']) + 'x ' + item['name'])
        each_order['item_names'] = ', '.join(item_list)

        orders.append(each_order)

    db.close()

    order_count = summary['order_count']
    total_sales = summary['sales'] or 0

    return render_template('sales.html', orders=orders, order_count=order_count, total_sales=total_sales)


# ----- LOGOUT -----
@app.route('/logout')
def logout():
    session.clear()   # forget who was logged in
    return redirect('/')


# Start the website when this file is run directly (for testing on our own computer)
if __name__ == '__main__':
    app.run(debug=True)
