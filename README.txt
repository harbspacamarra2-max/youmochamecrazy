YOU MOCHA ME CRAZY COFFEE ORDERING SYSTEM (Python + Flask)

Accounts
  owner   / crazy123   (Order, Sales, Menu)
  cashier / mocha123   (Order only)

Run on your own computer
  1. Install Python, then run:  pip install flask
  2. In this folder run:  python app.py
     (the database file coffee_shop.db is created automatically)
  3. Open http://127.0.0.1:5000

Put it online (Render)
  Build command:  pip install -r requirements.txt
  Start command:  gunicorn app:app

Files
  app.py               the whole system (login, ordering, payment, receipt,
                       sales, menu management, logout)
  requirements.txt     Python packages the system needs
  config.py            settings (database file name)
  database.sql         tables and sample data
  templates/           base.html, nav.html, login.html, order.html,
                       receipt.html, sales.html, menu.html, cup.svg
  static/              style.css, app.js
