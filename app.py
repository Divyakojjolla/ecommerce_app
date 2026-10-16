
from flask import Flask, render_template, request, redirect, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config['SECRET_KEY'] = 'ecommerce123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# -------------------
# DATABASE TABLES
# -------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='customer')


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100))
    quantity = db.Column(db.Integer)
    total_price = db.Column(db.Float)


# -------------------
# HOME PAGE
# -------------------

@app.route('/')
def home():
    if 'user' not in session:
        return redirect('/login')

    products = Product.query.all()
    return render_template('index.html', products=products)


# -------------------
# REGISTER
# -------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            error = 'Please enter both username and password.'

        elif User.query.filter_by(username=username).first():
            error = 'Username already exists. Please log in.'

        else:
            user = User(
                username=username,
                password=generate_password_hash(password),
                role='customer'
            )
            db.session.add(user)
            db.session.commit()

            session['user'] = username
            session['role'] = 'customer'
            return redirect('/')

    return render_template('register.html', error=error)


# -------------------
# LOGIN
# -------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user'] = user.username
            session['role'] = user.role
            return redirect('/')

        # Support accounts created by your original plain-text version.
        if user and user.password == password:
            user.password = generate_password_hash(password)
            db.session.commit()
            session['user'] = user.username
            session['role'] = user.role
            return redirect('/')

        error = 'Invalid username or password.'

    return render_template('login.html', error=error)


# -------------------
# LOGOUT
# -------------------

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# -------------------
# ADD TO CART
# -------------------

@app.route('/add_to_cart/<int:id>')
def add_to_cart(id):
    if 'user' not in session:
        return redirect('/login')

    product = db.session.get(Product, id)

    if product is None:
        return 'Product not found', 404

    cart = session.get('cart', [])
    cart.append({
        'id': product.id,
        'name': product.name,
        'price': product.price
    })
    session['cart'] = cart

    return redirect('/cart')


# -------------------
# VIEW CART
# -------------------

@app.route('/cart')
def view_cart():
    if 'user' not in session:
        return redirect('/login')

    cart = session.get('cart', [])
    total = sum(item['price'] for item in cart)

    return render_template(
        'cart.html',
        cart=cart,
        total=total
    )


# -------------------
# CHECKOUT
# -------------------

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user' not in session:
        return redirect('/login')

    cart = session.get('cart', [])

    if not cart:
        return 'Your cart is empty. <a href="/">Continue shopping</a>'

    total = sum(item['price'] for item in cart)

    for item in cart:
        order = Order(
            product_name=item['name'],
            quantity=1,
            total_price=item['price']
        )
        db.session.add(order)

    db.session.commit()
    session['cart'] = []

    return (
        f'Order placed successfully! Total = ₹{total:.2f}<br>'
        '<a href="/">Continue shopping</a>'
    )


# -------------------
# PRODUCT API
# -------------------

@app.route('/api/products')
def get_products():
    products = Product.query.all()

    return jsonify([
        {
            'id': p.id,
            'name': p.name,
            'price': p.price,
            'description': p.description
        }
        for p in products
    ])


# -------------------
# ORDER API
# -------------------

@app.route('/api/orders')
def get_orders():
    orders = Order.query.all()

    return jsonify([
        {
            'id': o.id,
            'product': o.product_name,
            'quantity': o.quantity,
            'amount': o.total_price
        }
        for o in orders
    ])


# -------------------
# INITIALIZE DATABASE
# -------------------

with app.app_context():
    db.create_all()

    if Product.query.count() == 0:
        db.session.add_all([
            Product(
                name='Laptop',
                price=55000,
                description='HP Laptop'
            ),
            Product(
                name='Mobile',
                price=15000,
                description='Samsung Mobile'
            ),
            Product(
                name='Headphones',
                price=2000,
                description='Wireless Headphones'
            )
        ])
        db.session.commit()


# -------------------
# RUN APPLICATION
# -------------------

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
