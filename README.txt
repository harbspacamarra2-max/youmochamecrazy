YOU MOCHA ME CRAZY COFFEE ORDERING SYSTEM (Python + Flask)

Accounts
  cashier / mocha123
  owner   / crazy123

Run on your own computer
  1. Install Python, then run:  pip install flask
  2. In this folder run:  python app.py
     (the database file coffee_shop.db is created automatically)
  3. Open http://127.0.0.1:5000

Put it online (Render)
  Build command:  pip install -r requirements.txt
  Start command:  gunicorn app:app

Files
  app.py               the whole system (login, order screen, pay, sales, logout)
  requirements.txt     Python packages the system needs
  config.py            settings (database file name)
  database.sql         tables and sample data
  templates/           login.html, order.html, sales.html, cup.svg
  static/              style.css, app.js
