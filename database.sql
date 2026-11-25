-- You Mocha Me Crazy Coffee Ordering System
-- Database: coffee_shop (SQLite)

-- Table of cashier accounts
CREATE TABLE users (
  user_id  INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  password TEXT NOT NULL
);

-- Table of menu items
CREATE TABLE products (
  product_id INTEGER PRIMARY KEY AUTOINCREMENT,
  name       TEXT NOT NULL,
  category   TEXT NOT NULL CHECK (category IN ('Coffee', 'Non Coffee', 'Pastry')),
  price      REAL NOT NULL
);

-- Table of finished orders
CREATE TABLE orders (
  order_id   INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id    INTEGER NOT NULL,
  order_date TEXT NOT NULL,
  total      REAL NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Table of the items inside each order
CREATE TABLE order_items (
  item_id    INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id   INTEGER NOT NULL,
  product_id INTEGER NOT NULL,
  quantity   INTEGER NOT NULL,
  subtotal   REAL NOT NULL,
  FOREIGN KEY (order_id) REFERENCES orders(order_id),
  FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Cashier accounts (the passwords are saved as hashes)
INSERT INTO users (username, password) VALUES
('cashier', 'pbkdf2:sha256:1000000$IxCc6dfXedcrnhMI$53bf3bdd5804457c9edffcc9baa51c9dc0793a4191003145484a50ce2ec06bc9'),
('owner',   'pbkdf2:sha256:1000000$3Hpy4wdG535LGdAm$b7c5582967d15b51c911f9fa93fcb7a4a21e0f6809930464bc0f01c9e47cfe86');

-- Menu items
INSERT INTO products (name, category, price) VALUES
('Americano',        'Coffee',     110),
('Cafe Latte',       'Coffee',     140),
('Cappuccino',       'Coffee',     140),
('Spanish Latte',    'Coffee',     160),
('Mocha',            'Coffee',     150),
('Caramel Latte',    'Coffee',     170),
('Matcha Latte',     'Non Coffee', 150),
('Chocolate',        'Non Coffee', 130),
('Strawberry Milk',  'Non Coffee', 140),
('Croissant',        'Pastry',      90),
('Blueberry Muffin', 'Pastry',      85),
('Ensaymada',        'Pastry',      70);
