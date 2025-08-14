from flask import Flask, render_template, request, redirect, url_for
import sqlite3, csv, os
from datetime import datetime

app = Flask(__name__)
GST = 0.18

# Database setup
def init_db():
    conn = sqlite3.connect('restaurant.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS menu (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT,
        category TEXT,
        price REAL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_type TEXT,
        payment_method TEXT,
        total REAL,
        order_time TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        item_name TEXT,
        quantity INTEGER,
        price REAL
    )''')
    conn.commit()

    # Load menu from CSV if empty
    c.execute("SELECT COUNT(*) FROM menu")
    if c.fetchone()[0] == 0:
        with open("menu.csv", newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                c.execute("INSERT INTO menu (item_name, category, price) VALUES (?, ?, ?)",
                          (row['item_name'], row['category'], float(row['price'])))
        conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = sqlite3.connect('restaurant.db')
    menu = conn.execute("SELECT * FROM menu").fetchall()
    conn.close()
    return render_template("index.html", menu=menu)

@app.route('/bill', methods=['POST'])
def bill():
    selected = request.form.getlist('item')
    qtys = request.form.getlist('qty')
    cust_type = request.form['cust_type']
    payment = request.form['payment_method']

    items = []
    subtotal = 0
    for i, item_id in enumerate(selected):
        conn = sqlite3.connect('restaurant.db')
        item = conn.execute("SELECT item_name, price FROM menu WHERE id=?", (item_id,)).fetchone()
        conn.close()
        qty = int(qtys[i])
        price = item[1]
        items.append((item[0], qty, price))
        subtotal += qty * price

    gst = subtotal * GST
    total = subtotal + gst

    # Save order
    conn = sqlite3.connect('restaurant.db')
    c = conn.cursor()
    c.execute("INSERT INTO orders (customer_type, payment_method, total, order_time) VALUES (?, ?, ?, ?)",
              (cust_type, payment, total, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    order_id = c.lastrowid
    for name, qty, price in items:
        c.execute("INSERT INTO order_items (order_id, item_name, quantity, price) VALUES (?, ?, ?, ?)",
                  (order_id, name, qty, price))
    conn.commit()
    conn.close()

    return render_template("bill.html", items=items, subtotal=subtotal, gst=gst, total=total)

@app.route('/admin')
def admin():
    conn = sqlite3.connect('restaurant.db')
    menu = conn.execute("SELECT * FROM menu").fetchall()
    conn.close()
    return render_template("admin.html", menu=menu)

@app.route('/admin/add', methods=['POST'])
def add_item():
    name = request.form['name']
    cat = request.form['cat']
    price = float(request.form['price'])

    conn = sqlite3.connect('restaurant.db')
    conn.execute("INSERT INTO menu (item_name, category, price) VALUES (?, ?, ?)", (name, cat, price))
    conn.commit()
    conn.close()
    return redirect('/admin')

@app.route('/admin/delete/<int:id>')
def delete_item(id):
    conn = sqlite3.connect('restaurant.db')
    conn.execute("DELETE FROM menu WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/admin')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
