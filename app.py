# app.py
# The main file of the You Mocha Me Crazy Coffee Ordering System.
# It runs the website: login, the order screen, payment, receipts,
# sales records, and menu management.

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

# Categories that have drink options (size, hot or iced, add-ons)
DRINK_CATEGORIES = ['Coffee', 'Non Coffee']

# Choices on the order screen
ORDER_TYPES = ['Dine-in', 'Take-out']
DISCOUNT_TYPES = ['None', 'Senior Citizen', 'PWD']
PAYMENT_METHODS = ['Cash', 'GCash', 'Maya', 'Card']

# Brown shades used as the background of each item picture
COLORS = ['#6B4430', '#AE7A50', '#9C6A45', '#C99B6C', '#5A3524', '#C8874B']


# ----- CONNECT TO THE DATABASE -----
def connect():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row   # give results as named columns, for example row['name']
    return db


# ----- CREATE THE DATABASE THE FIRST TIME -----
# If the database file does not exist yet, create the tables and add the
# accounts, menu items, and drink options from database.sql
def create_database():
    if not os.path.exists(DB_PATH):
        db = connect()
        with open(os.path.join(FOLDER, 'database.sql')) as sql_file:
            db.executescript(sql_file.read())
        db.commit()
        db.close()


create_database()


# ----- CHECK WHO IS LOGGED IN -----
def is_logged_in():
    return 'user_id' in session


def is_owner():
    return session.get('role') == 'Owner'


# ----- COMPUTE THE TOTAL OF AN ORDER -----
# Menu prices already include 12% VAT.
# Senior Citizens and PWDs get 20% off and do not pay VAT:
#   1. Remove the VAT:      price without VAT = subtotal / 1.12
#   2. Take 20% off that:   discount = price without VAT x 0.20
#   3. Total to pay:        price without VAT - discount
def compute_totals(subtotal, discount_type):
    if discount_type == 'None':
        vat = subtotal - subtotal / 1.12      # the VAT already inside the price
        discount = 0
        total = subtotal
    else:
        price_without_vat = subtotal / 1.12
        vat = 0                               # VAT exempt
        discount = price_without_vat * 0.20
        total = price_without_vat - discount
    return round(vat, 2), round(discount, 2), round(total, 2)


# ----- LOGIN PAGE -----
@app.route('/', methods=['GET', 'POST'])
def login():
    # If someone is already logged in, go straight to the order screen
    if is_logged_in():
        return redirect('/order')

    error = ''
    username = ''

    # This part runs only when the Sign In button is pressed
    if request.method == 'POST':
        # Step 1: Get what the user typed
        username = request.form['username'].strip()
        password = request.form['password']

        # Step 2: Look for that username in the users table
        db = connect()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        db.close()

        # Step 3: Check if the user exists and the password is correct
        if user and check_password_hash(user['password'], password):
            # Correct: remember the user and their role, then open the order screen
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            session['role'] = user['role']
            return redirect('/order')
        else:
            # Wrong: show a message and let them try again
            error = 'Wrong username or password. Please try again.'

    return render_template('login.html', error=error, username=username)


# ----- ORDER SCREEN -----
@app.route('/order')
def order():
    # Only logged in users can open this page
    if not is_logged_in():
        return redirect('/')

    db = connect()
    rows = db.execute('SELECT * FROM products ORDER BY product_id').fetchall()
    options = [dict(row) for row in db.execute('SELECT * FROM options ORDER BY option_id').fetchall()]
    db.close()

    # Give each product a brown shade for its picture
    products = []
    number = 0
    for row in rows:
        product = dict(row)
        product['color'] = COLORS[number % len(COLORS)]
        product['is_drink'] = product['category'] in DRINK_CATEGORIES
        products.append(product)
        number = number + 1

    return render_template('order.html', products=products, options=options,
                           categories=CATEGORIES, order_types=ORDER_TYPES,
                           discount_types=DISCOUNT_TYPES, payment_methods=PAYMENT_METHODS)


# ----- PAY (SAVE THE ORDER) -----
# The order screen sends the whole order here when Pay is pressed.
@app.route('/pay', methods=['POST'])
def pay():
    # Stop if no one is logged in
    if not is_logged_in():
        return jsonify(ok=False, message='Please sign in again.')

    # Step 1: Read the order sent by the order screen
    data = request.get_json()
    items = data.get('items', [])
    customer_name = data.get('customer_name', '').strip() or 'Walk-in'
    order_type = data.get('order_type', '')
    discount_type = data.get('discount_type', 'None')
    discount_id_no = data.get('discount_id_no', '').strip()
    payment_method = data.get('payment_method', '')

    # Step 2: Check the choices
    if len(items) == 0:
        return jsonify(ok=False, message='The order is empty.')
    if order_type not in ORDER_TYPES:
        return jsonify(ok=False, message='Please choose Dine-in or Take-out.')
    if discount_type not in DISCOUNT_TYPES:
        return jsonify(ok=False, message='Please choose a discount.')
    if discount_type != 'None' and discount_id_no == '':
        return jsonify(ok=False, message='Please enter the Senior Citizen or PWD ID number.')
    if payment_method not in PAYMENT_METHODS:
        return jsonify(ok=False, message='Please choose a payment method.')

    db = connect()
    try:
        # Step 3: Compute the price of each item using the prices in the database.
        # We do not trust the prices from the screen.
        subtotal = 0
        order_items = []

        for item in items:
            product_id = int(item['product_id'])
            quantity = int(item['quantity'])
            option_ids = item.get('option_ids', [])

            product = db.execute('SELECT * FROM products WHERE product_id = ?', (product_id,)).fetchone()

            # Skip items that do not exist, are sold out, or have a wrong quantity
            if product is None or product['is_available'] == 0 or quantity < 1:
                continue

            # Add the price of each chosen option (only drinks have options)
            unit_price = product['price']
            option_names = []
            if product['category'] in DRINK_CATEGORIES:
                for option_id in option_ids:
                    option = db.execute('SELECT * FROM options WHERE option_id = ?', (int(option_id),)).fetchone()
                    if option is not None:
                        unit_price = unit_price + option['extra_price']
                        option_names.append(option['name'])

            item_subtotal = unit_price * quantity
            subtotal = subtotal + item_subtotal
            order_items.append({
                'product_id': product_id,
                'options': ', '.join(option_names),
                'unit_price': unit_price,
                'quantity': quantity,
                'subtotal': item_subtotal,
            })

        # Stop if none of the items were valid
        if len(order_items) == 0:
            return jsonify(ok=False, message='The order is empty.')

        # Step 4: Compute the VAT, the discount, and the total
        vat, discount, total = compute_totals(subtotal, discount_type)

        # Step 5: Check the payment. For cash, the money received must cover the total.
        if payment_method == 'Cash':
            amount_paid = float(data.get('amount_paid') or 0)
            if amount_paid < total:
                return jsonify(ok=False, message='The cash received is less than the total.')
        else:
            amount_paid = total
        change_due = round(amount_paid - total, 2)

        # Step 6: Save the order
        now = datetime.now(PH_TIME).strftime('%Y-%m-%d %H:%M:%S')
        cursor = db.execute('''
            INSERT INTO orders (user_id, order_date, customer_name, order_type, subtotal, vat,
                                discount_type, discount_id_no, discount, total,
                                payment_method, amount_paid, change_due)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (session['user_id'], now, customer_name, order_type, subtotal, vat,
              discount_type, discount_id_no, discount, total,
              payment_method, amount_paid, change_due))
        order_id = cursor.lastrowid   # the new order number

        # Step 7: Save each item of the order
        for order_item in order_items:
            db.execute('''
                INSERT INTO order_items (order_id, product_id, options, unit_price, quantity, subtotal)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (order_id, order_item['product_id'], order_item['options'],
                  order_item['unit_price'], order_item['quantity'], order_item['subtotal']))

        # Save everything together. If something failed above, nothing is saved.
        db.commit()
    except Exception:
        db.rollback()   # cancel everything if there was a problem
        return jsonify(ok=False, message='Could not save the order. Please try again.')
    finally:
        db.close()

    # Step 8: Tell the order screen it worked, so it can open the receipt
    return jsonify(ok=True, order_id=order_id)


# ----- RECEIPT -----
@app.route('/receipt/<int:order_id>')
def receipt(order_id):
    if not is_logged_in():
        return redirect('/')

    db = connect()
    the_order = db.execute('''
        SELECT orders.*, users.full_name AS cashier
        FROM orders
        JOIN users ON users.user_id = orders.user_id
        WHERE orders.order_id = ?
    ''', (order_id,)).fetchone()
    items = db.execute('''
        SELECT order_items.*, products.name
        FROM order_items
        JOIN products ON products.product_id = order_items.product_id
        WHERE order_items.order_id = ?
    ''', (order_id,)).fetchall()
    db.close()

    if the_order is None:
        return redirect('/order')

    date = datetime.strptime(the_order['order_date'], '%Y-%m-%d %H:%M:%S')
    return render_template('receipt.html', order=the_order, items=items,
                           date=date.strftime('%b %d, %Y %I:%M %p'))


# ----- SALES RECORDS (OWNER ONLY) -----
@app.route('/sales')
def sales():
    if not is_logged_in():
        return redirect('/')
    if not is_owner():
        return redirect('/order')

    today = datetime.now(PH_TIME).strftime('%Y-%m-%d')

    db = connect()

    # Count today's orders and add up today's sales and discounts
    summary = db.execute('''
        SELECT COUNT(*) AS order_count, SUM(total) AS sales, SUM(discount) AS discounts
        FROM orders WHERE DATE(order_date) = ?
    ''', (today,)).fetchone()

    # The 5 best selling items today
    best_sellers = db.execute('''
        SELECT products.name, SUM(order_items.quantity) AS sold
        FROM order_items
        JOIN orders ON orders.order_id = order_items.order_id
        JOIN products ON products.product_id = order_items.product_id
        WHERE DATE(orders.order_date) = ?
        GROUP BY products.name
        ORDER BY sold DESC
        LIMIT 5
    ''', (today,)).fetchall()

    # Today's sales for each payment method
    by_payment = db.execute('''
        SELECT payment_method, SUM(total) AS amount
        FROM orders WHERE DATE(order_date) = ?
        GROUP BY payment_method
    ''', (today,)).fetchall()

    # The 50 latest orders
    rows = db.execute('''
        SELECT orders.*, users.full_name AS cashier
        FROM orders
        JOIN users ON users.user_id = orders.user_id
        ORDER BY orders.order_id DESC
        LIMIT 50
    ''').fetchall()

    orders = []
    for row in rows:
        each_order = dict(row)
        date = datetime.strptime(each_order['order_date'], '%Y-%m-%d %H:%M:%S')
        each_order['order_date'] = date.strftime('%b %d, %Y %I:%M %p')
        orders.append(each_order)

    db.close()

    return render_template('sales.html', orders=orders,
                           order_count=summary['order_count'],
                           total_sales=summary['sales'] or 0,
                           total_discounts=summary['discounts'] or 0,
                           best_sellers=best_sellers, by_payment=by_payment)


# ----- MENU MANAGEMENT (OWNER ONLY) -----
@app.route('/menu')
def menu():
    if not is_logged_in():
        return redirect('/')
    if not is_owner():
        return redirect('/order')

    db = connect()
    products = db.execute('SELECT * FROM products ORDER BY category, name').fetchall()
    db.close()

    message = request.args.get('message', '')
    return render_template('menu.html', products=products, categories=CATEGORIES, message=message)


# Add a new menu item
@app.route('/menu/add', methods=['POST'])
def menu_add():
    if not is_owner():
        return redirect('/order')

    name = request.form['name'].strip()
    category = request.form['category']
    price = float(request.form['price'] or 0)

    if name != '' and category in CATEGORIES and price > 0:
        db = connect()
        db.execute('INSERT INTO products (name, category, price) VALUES (?, ?, ?)', (name, category, price))
        db.commit()
        db.close()
        return redirect('/menu?message=' + name + ' was added to the menu.')

    return redirect('/menu?message=Please fill in a name, a category, and a price above 0.')


# Save changes to a menu item (name, category, price, available or sold out)
@app.route('/menu/update/<int:product_id>', methods=['POST'])
def menu_update(product_id):
    if not is_owner():
        return redirect('/order')

    name = request.form['name'].strip()
    category = request.form['category']
    price = float(request.form['price'] or 0)
    is_available = 1 if request.form.get('is_available') else 0

    if name != '' and category in CATEGORIES and price > 0:
        db = connect()
        db.execute('UPDATE products SET name = ?, category = ?, price = ?, is_available = ? WHERE product_id = ?',
                   (name, category, price, is_available, product_id))
        db.commit()
        db.close()
        return redirect('/menu?message=' + name + ' was updated.')

    return redirect('/menu?message=Please fill in a name, a category, and a price above 0.')


# ----- LOGOUT -----
@app.route('/logout')
def logout():
    session.clear()   # forget who was logged in
    return redirect('/')


# Start the website when this file is run directly (for testing on our own computer)
if __name__ == '__main__':
    app.run(debug=True)
