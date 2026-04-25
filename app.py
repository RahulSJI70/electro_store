
from flask import session
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, redirect, url_for, request, session, flash
from models import Notification, db, Product, Order, User, OrderItem, ProductImage
import razorpay
import os
from werkzeug.utils import secure_filename
from models import Address
from models import Offer
from flask_migrate import Migrate
import json
from sqlalchemy import func, or_
from flask import request, redirect
client = razorpay.Client(auth=("rzp_test_SWuzgvEZgXmpwd", "cJJaXLIf7cm8tgt0b8Fl5YPC"))
app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

migrate = Migrate(app, db)

# 🔐 LOGIN PROTECTION FUNCTION
from functools import wraps

def load_translations(lang):
    path = os.path.join("translations", f"{lang.lower()}.json")

    if not os.path.exists(path):
        path = os.path.join("translations", "en.json")

    print("👉 Loading file:", path)     

    with open(path, encoding="utf-8") as f:
        return json.load(f)





@app.context_processor
def inject_language():
    lang = session.get("language", "EN")
    data = load_translations(lang)

    return dict(t=lambda key: data.get(key, key))

@app.before_request
def detect_language():
    if 'language' not in session:
        browser_lang = request.headers.get('Accept-Language', 'en')[:2]

        if browser_lang == 'hi':
            session['language'] = 'HI'
        elif browser_lang == 'ml':
            session['language'] = 'ML'
        else:
            session['language'] = 'EN'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = User.query.get(session.get('user_id'))
        if not user or not user.is_admin:
            return "Access denied ❌"
        return f(*args, **kwargs)
    return decorated

# ✅ CREATE DB + ADD PRODUCTS
with app.app_context():
    db.create_all()
     # TEMP: disable this block
    # if not Product.query.first():
    #    
    
        # products = [
           # Product(name="OnePlus 15R", brand="OnePlus", price=55499, image="img/header-img.jpg", category="Mobiles", seller_id=2),
           # Product(name="iPhone 17", brand="Apple", price=134900, image="img/product-6.png", category="Mobiles", rating=4.5, seller_id=2),
           #Product(name="Samsung S23 Ultra", brand="Samsung", price=77000, image="img/product-3.png", category="Mobiles", rating=4.6, seller_id=2),
           # Product(name="Nothing Phone 2", brand="Nothing", price=38999, image="img/product-4.png", category="Mobiles", rating=4.3, seller_id=2),
           # Product(name="Vivo T4 Pro", brand="Vivo", price=26999, image="img/product-5.png", category="Mobiles", rating=4.2, seller_id=2),
           # Product(name="POCO X8 Pro", brand="POCO", price=42999, image="img/product-8.png", category="Mobiles", rating=4.4, seller_id=2),
           # Product(name="Infinix Zero 5G", brand="Infinix", price=17999, image="img/product-9.png", category="Mobiles", rating=4.1, seller_id=2),
           # Product(name="Samsung Tab A11+", brand="Samsung", price=21999, image="img/product-10.png", category="Tablets", rating=4.3, seller_id=2),
           # Product(name="Apple iPad A16", brand="Apple", price=58599, image="img/product-11.png", category="Tablets", rating=4.7, seller_id=2),
           # Product(name="Apple iPad Mini", brand="Apple", price=105000, image="img/product-3.png", category="Tablets", rating=4.6, seller_id=2),
           # Product(name="Smart Watch X", brand="Boat", price=4999, image="img/product-13.png", category="Watch", seller_id=2),
           # Product(name="Camera Pro Max", brand="Sony", price=55999, image="img/product-1.png", category="Camera", seller_id=2),
           # Product(name="LED Monitor 22 inch", brand="LG", price=5739, image="img/product-12.png", category="Computers", rating=4.2, seller_id=2),
           # Product(name="Zebronics Monitor", brand="Zebronics", price=3999, image="img/product-16.png", category="Computers", rating=4.1, seller_id=2),
           # Product(name="Xiaomi Smart TV", brand="Xiaomi", price=40990, image="img/product-17.png", category="Electronics", rating=4.6, seller_id=2),
           # Product(name="Lenovo Monitor", brand="Lenovo", price=13599, image="img/product-14.png", category="Computers", rating=4.3, seller_id=2),
           # Product(name="Gaming Monitor Pro", brand="Asus", price=16790, image="img/product-15.png", category="Computers", rating=4.4, seller_id=2)
        #]

        #db.session.bulk_save_objects(products)
        #db.session.commit()

@app.route('/')
def home():

    count = 0
    if 'user_id' in session:
        count = Notification.query.filter_by(
            user_id=session['user_id'],
            is_read=False
        ).count()

    cart_data = session.get('cart', {})
    cart_ids = [int(pid) for pid in cart_data.keys()]
    cart_products = Product.query.filter(Product.id.in_(cart_ids)).all()

    # CATEGORY COUNT
    categories = db.session.query(
        Product.category,
        func.count(Product.id)
    ).group_by(Product.category).all()

    # USER
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])

    # 🔥 ADD THIS LINE
    products = Product.query.order_by(Product.id.desc()).limit(12).all()

    return render_template(
        'index.html',
        products=products,   # 👈 VERY IMPORTANT
        cart=cart_products,
        wishlist=session.get('wishlist', []),
        notification_count=count,
        categories=categories,
        user=user
    )

from sqlalchemy import func, or_

@app.route('/shop')
def shop():
    search = request.args.get('search')
    category = request.args.get('category')
    brand = request.args.get('brand')
    sort = request.args.get('sort')
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')
    


    query = Product.query

    # 🔍 SEARCH
    if search:
        query = query.filter(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.category.ilike(f"%{search}%")
            )
        )

    # CATEGORY
    if category:
        query = query.filter_by(category=category)

    # BRAND FILTER
    if brand:
        query = query.filter_by(brand=brand)

    # PRICE
    if min_price:
        query = query.filter(Product.price >= int(min_price))
    if max_price:
        query = query.filter(Product.price <= int(max_price))

    # SORT
    if sort == "low":
        query = query.order_by(Product.price.asc())
    elif sort == "high":
        query = query.order_by(Product.price.desc())

    products = query.all()

    # 🔥 ADD THIS (CATEGORY COUNTS)
    categories = db.session.query(
        Product.category,
        func.count(Product.id)
    ).group_by(Product.category).all()

    return render_template(
        "shop.html",
        products=products,
        categories=categories   # 👈 IMPORTANT
    )

@app.route('/cart')
@login_required
def cart():

    cart_data = session.get('cart', {})

    products = []
    total = 0
    original_total = 0

    for pid, qty in cart_data.items():
        product = Product.query.get(int(pid))

        if product:
           product.quantity = qty   # attach quantity
           products.append(product)

           original_total += product.price * qty
           total += product.get_discounted_price() * qty

    savings = original_total - total

   

    return render_template(
        'cart.html',
        cart=products,
        total=total,
        original_total=original_total,
        savings=savings,
        wishlist=wishlist_items
    )

# ✅ REMOVE
@app.route('/remove-from-cart/<int:id>')
@login_required
def remove_from_cart(id):

    cart = session.get('cart', {})
    pid = str(id)
    
    if pid in cart:
        del cart[pid]   # remove one item

    session['cart'] = cart
    session.modified = True

    return redirect(url_for('cart'))

# ✅ LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    next_page = request.args.get('next')

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.name

            # 1️⃣ FIRST: handle next (seller flow, etc.)
            if next_page:
                return redirect(url_for(next_page))

            # 2️⃣ SECOND: handle seller role
            if user.role == "seller":
                return redirect(url_for('my_products'))

            # 3️⃣ DEFAULT: normal user
            return redirect(url_for('home'))

        else:
            return "Invalid email or password ❌"

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        raw_password = request.form['password']       # 👈 take plain password
        confirm = request.form['confirm_password']

        # ✅ compare BEFORE hashing
        if raw_password != confirm:
            return "Passwords do not match ❌"

        # 🔍 check if user exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return "Email already registered ❌"

        # 🔐 hash AFTER checking
        password = generate_password_hash(raw_password)

        # ✅ save user
        new_user = User(name=name, email=email, password=password , phone=phone)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/payment')
@login_required
def payment():

    cart_data = session.get('cart', {})

    total = 0

    for pid, qty in cart_data.items():
        product = Product.query.get(int(pid))
        if product:
            total += product.get_discounted_price() * qty

    total_paisa = int(total * 100)

    order = client.order.create({
        "amount": total_paisa,
        "currency": "INR",
        "payment_capture": 1,
        
    
    
    })

    return render_template("payment.html", order=order, total=total)

@app.route('/payment_success', methods=['POST'])
@login_required
def payment_success():

    # 👉 Create Order here (you may already add later)
    
    # 🔔 ADD NOTIFICATION HERE
    new_notification = Notification(
        user_id=session['user_id'],
        message="Payment successful! Your order is confirmed ✅"
    )

    db.session.add(new_notification)
    db.session.commit()

    return redirect(url_for('orders'))

@app.route('/verify', methods=['POST'])
@login_required
def verify():

    cart_data = session.get('cart', {})

    if not cart_data:
        return "Cart is empty"

    total = 0

    # calculate total
    for pid, qty in cart_data.items():
        product = Product.query.get(int(pid))
        if product:
            total += product.get_discounted_price() * qty

    # create order
    new_order = Order(
        user_id=session['user_id'],
        price=total,
        status="Placed"
    )

    db.session.add(new_order)
    db.session.commit()

    # add items
    for pid, qty in cart_data.items():
        product = Product.query.get(int(pid))

        if product:
            item = OrderItem(
                order_id=new_order.id,
                product_id=product.id,
                quantity=qty,
                price=product.get_discounted_price()
            )
            db.session.add(item)

    # clear cart
    session['cart'] = {}

    db.session.commit()

    return redirect(url_for('orders'))

@app.route('/returns')
def returns():
    return render_template('returns.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/track-order', methods=['GET', 'POST'])
def track_order():

    order = None

    if request.method == 'POST':
        order_id = request.form.get('order_id')

        order = Order.query.get(order_id)

    return render_template('track_order.html', order=order)


@app.route('/add-product', methods=['GET', 'POST'])
def add_product():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    if not user:
        session.clear()
        return redirect(url_for('login'))

    if user.role != "seller":
        return "Access denied"

    if request.method == 'POST':

        files = request.files.getlist('images')  # ✅ multiple files

        # create product first
        product = Product(
            short_name=request.form.get('short_name'),
            name=request.form['name'],
            price=float(request.form['price']),
            category=request.form['category'],
            seller_id=user.id
        )

        db.session.add(product)
        db.session.commit()  # 🔥 must commit first

        # save images
        for file in files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join('static/img', filename))

                img = ProductImage(
                    image=f"img/{filename}",
                    product_id=product.id
                )
                db.session.add(img)

        db.session.commit()

        return redirect(url_for('my_products'))

    return render_template('add_product.html')

@app.route('/seller')
def seller_page():

    if 'user_id' not in session:
        return render_template('seller.html')  # show login/start page

    user = User.query.get(session['user_id'])

    if user.role == "seller":
        return redirect(url_for('my_products'))   # seller dashboard

    elif user.is_seller_request:
        return render_template('seller.html', status="pending")

    return render_template('seller.html', status="not_seller")


@app.route('/become-seller')
@login_required
def become_seller():

    user = User.query.get(session['user_id'])

    user.is_seller_request = True
    db.session.commit()

    return redirect(url_for('seller_page'))   # 👈 IMPORTANT CHANGE

@app.route('/approve-seller/<int:id>')
@admin_required
def approve_seller(id):

    user = User.query.get_or_404(id)

    # ✅ Make seller
    user.role = "seller"
    user.is_seller_request = False

    # 🔔 Add notification
    new_notification = Notification(
        user_id=user.id,
        message="🎉 Your seller request has been approved! You can start selling now."
    )

    db.session.add(new_notification)
    db.session.commit()

    return redirect(url_for('admin_dashboard'))

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        print("CONTACT:", name, email, message)  # debug

        flash("Message sent successfully! ✅", "success")
        return redirect(url_for('contact'))

    return render_template('contact.html')

@app.route('/faq')
def faq():
    return "FAQ Page"

@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form.get('email')

    print("New subscriber:", email)  # debug

    return redirect(request.referrer)
    

@app.route('/change-language', methods=['POST'])
def change_language():

    lang = request.form.get('language')
    country = request.form.get('country')

    session['language'] = lang
    session['country'] = country

    flash("Preferences updated 🌐", "success")

    return redirect(request.referrer)

@app.route('/orders')
@login_required
def orders():
    orders = Order.query.filter_by(user_id=session['user_id']).all()
    return render_template("orders.html", orders=orders)

@app.route('/cancel-order/<int:id>')
@login_required
def cancel_order(id):

    order = Order.query.get_or_404(id)

    # 🔒 security check
    if order.user_id != session['user_id']:
        return "Unauthorized", 403

    # ❌ cannot cancel delivered
    if order.status == "Delivered":
        return "Order already delivered. Cannot cancel ❌"

    order.status = "Cancelled"
    db.session.commit()

    return redirect(url_for('orders'))

# ✅ ADD TO CART
@app.route('/add-to-cart/<int:id>')
def add_to_cart(id):

    cart = session.get('cart', {})   # always dict

    pid = str(id)

    if pid in cart:
        cart[pid] += 1
    else:
        cart[pid] = 1

    session['cart'] = cart
    session.modified = True

    return redirect(url_for('cart'))


@app.route('/clear-cart')
def clear_cart():
    session['cart'] = {}
    return "Cart cleared"

@app.route('/increase/<int:id>')
def increase(id):
    cart = session.get('cart', {})
    pid = str(id)

    if pid in cart:
        cart[pid] += 1

    session['cart'] = cart
    session.modified = True

    return redirect(url_for('cart'))



@app.route('/decrease/<int:id>')
def decrease(id):
    cart = session.get('cart', {})
    pid = str(id)

    if pid in cart:
        cart[pid] -= 1
        if cart[pid] <= 0:
            del cart[pid]

    session['cart'] = cart
    session.modified = True

    return redirect(url_for('cart'))

@app.route('/track/<int:id>')
def track_order_by_id(id):
    order = Order.query.get_or_404(id)
    return render_template("track.html", order=order)

@app.route('/product/<int:id>')
def product_detail(id):

    product = Product.query.get_or_404(id)

    # 🔥 FIXED CART
    cart_data = session.get('cart', {})
    cart_ids = [int(pid) for pid in cart_data.keys()]

    cart_products = Product.query.filter(Product.id.in_(cart_ids)).all()

    return render_template(
        'product.html',
        product=product,
        cart=cart_products,
        wishlist=wishlist_items
    )

wishlist_items = []


@app.route('/add-to-wishlist/<int:id>')
def add_to_wishlist(id):

    wishlist = session.get('wishlist', [])

    if id in wishlist:
        wishlist.remove(id)   # toggle
    else:
        wishlist.append(id)

    session['wishlist'] = wishlist
    session.modified = True

    return redirect(request.referrer)

@app.route('/wishlist')
@login_required
def wishlist():
    wishlist = session.get('wishlist', [])
    products = Product.query.filter(Product.id.in_(wishlist)).all()
    return render_template('wishlist.html', products=products)

@app.route('/remove-from-wishlist/<int:id>')
def remove_from_wishlist(id):
    global wishlist_items
    wishlist_items = [item for item in wishlist_items if item != id]
    return redirect(url_for('wishlist'))
@app.route('/account')
def account():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    return render_template('account.html', user=user)

@app.route('/update_account', methods=['POST'])
def update_account():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    if not user:
        return redirect(url_for('login'))

    # 🔹 Update text fields
    user.name = request.form['name']
    user.email = request.form['email']
    user.phone = request.form['phone']

    # 🔹 HANDLE IMAGE UPLOAD
    file = request.files.get('image')

    if file and file.filename != "":
        filename = secure_filename(file.filename)

        # save file
        file.save(os.path.join('static/uploads', filename))

        # save filename to DB
        user.image = filename

    db.session.commit()

    return redirect(url_for('account'))
@app.route('/change_password', methods=['POST'])
def change_password():
    print("SESSION USER ID:", session.get('user_id'))

    if 'user_id' not in session:
        return redirect(url_for('login'))

    current = request.form['current_password']
    new = request.form['new_password']
    confirm = request.form['confirm_password']

    # ✅ GET USER FROM SQLAlchemy
    user = User.query.get(session['user_id'])

    print("DB USER:", user)

    if not user:
        return "User not found"

    # 🔐 CHECK HASHED PASSWORD
    if not check_password_hash(user.password, current):
        return "Current password incorrect"

    if new != confirm:
        return "Passwords do not match"

    # 🔐 UPDATE PASSWORD (HASHED)
    user.password = generate_password_hash(new)
    db.session.commit()

    return redirect(url_for('account'))

@app.route('/addresses')
@login_required
def addresses():
    user_id = session['user_id']
    addresses = Address.query.filter_by(user_id=user_id).all()

    return render_template('addresses.html', addresses=addresses)

@app.route('/add_address', methods=['GET', 'POST'])
@login_required
def add_address():
    if request.method == 'POST':

        new_address = Address(
            user_id=session['user_id'],
            name=request.form['name'],
            phone=request.form['phone'],
            address=request.form['address'],
            city=request.form['city'],
            pincode=request.form['pincode']
        )

        db.session.add(new_address)
        db.session.commit()

        return redirect(url_for('addresses'))

    return render_template('add_address.html')

@app.route('/edit_address/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_address(id):

    address = Address.query.get_or_404(id)

    # security check
    if address.user_id != session['user_id']:
        return "Unauthorized", 403

    if request.method == 'POST':
        address.name = request.form['name']
        address.phone = request.form['phone']
        address.address = request.form['address']
        address.city = request.form['city']
        address.pincode = request.form['pincode']

        db.session.commit()
        return redirect(url_for('addresses'))

    return render_template('edit_address.html', address=address)

@app.route('/delete_address/<int:id>')
@login_required
def delete_address(id):

    address = Address.query.get_or_404(id)

    if address.user_id != session['user_id']:
        return "Unauthorized", 403

    db.session.delete(address)
    db.session.commit()

    return redirect(url_for('addresses'))

@app.route('/notifications')
@login_required
def notifications():

    user_notifications = Notification.query.filter_by(
        user_id=session['user_id']
    ).order_by(Notification.id.desc()).all()

    return render_template(
        'notifications.html',
        notifications=user_notifications
    )

@app.route('/mark_read/<int:id>')
@login_required
def mark_read(id):
    n = Notification.query.get(id)

    if n and n.user_id == session['user_id']:
        n.is_read = True
        db.session.commit()

    return redirect(url_for('notifications'))

@app.context_processor
def inject_notifications():

    if 'user_id' in session:
        count = Notification.query.filter_by(
            user_id=session['user_id'],
            is_read=False
        ).count()
    else:
        count = 0

    return dict(notification_count=count)

@app.route('/offers')
def offers():

    offers = Offer.query.filter_by(is_active=True).all()

    # 🔥 FIXED CART
    cart_data = session.get('cart', {})
    cart_ids = [int(pid) for pid in cart_data.keys()]

    cart_products = Product.query.filter(Product.id.in_(cart_ids)).all()

    return render_template(
        'offers.html',
        offers=offers,
        cart=cart_products,
        wishlist=wishlist_items
    )

@app.route('/settings')
@login_required
def settings():
    user = User.query.get(session['user_id'])
    return render_template('settings.html', user=user)

@app.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    user = User.query.get(session['user_id'])

    db.session.delete(user)
    db.session.commit()

    session.clear()
    return redirect(url_for('home'))

@app.route('/admin')
@admin_required
def admin_dashboard():

    user = User.query.get(session['user_id'])

    if not user or not user.is_admin:
        return "Access Denied ❌"

    orders = Order.query.all()
    users = User.query.all()
    products = Product.query.all()

    # 🔥 ADD THIS
    seller_requests = User.query.filter_by(is_seller_request=True).all()

    total_revenue = sum([o.price for o in orders if o.status == "Delivered"])
    total_orders = len(orders)

    return render_template(
        'admin.html',
        orders=orders,
        users=users,
        products=products,
        total_revenue=total_revenue,
        total_orders=total_orders,
        seller_requests=seller_requests   # 👈 VERY IMPORTANT
    )
@app.route('/admin/add-product', methods=['GET', 'POST'])
@admin_required
def admin_add_product():

    user = User.query.get(session.get('user_id'))
    if not user or not user.is_admin:
        return "Access denied ❌"

    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        image = request.form['image']
        category = request.form['category']

        new_product = Product(
            name=name,
            price=price,
            image=image,
            category=category
        )

        db.session.add(new_product)
        db.session.commit()

        return redirect(url_for('admin_dashboard'))

    return render_template('add_product.html')

@app.route('/admin/delete-product/<int:id>')
@admin_required
def admin_delete_product(id):

    user = User.query.get(session.get('user_id'))
    if not user or not user.is_admin:
       return "Access denied ❌"

    product = Product.query.get_or_404(id)

    db.session.delete(product)
    db.session.commit()

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit-product/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_product(id):

    user = User.query.get(session.get('user_id'))
    if not user or not user.is_admin:
       return "Access denied ❌"

    product = Product.query.get_or_404(id)

    if request.method == 'POST':
        product.name = request.form['name']
        product.price = request.form['price']
        product.image = request.form['image']
        product.category = request.form['category']

        db.session.commit()

        return redirect(url_for('admin_dashboard'))

    return render_template('edit_product.html', product=product)

@app.route('/my-products')
@login_required
def my_products():

    # ✅ check login
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    # ✅ check user exists
    if not user:
        session.clear()
        return redirect(url_for('login'))

    # ✅ check role
    if user.role != "seller":
        return "Access denied"

    products = Product.query.filter_by(seller_id=user.id).all()

    return render_template('my_products.html', products=products)

@app.route('/edit-product/<int:id>', methods=['GET', 'POST'])
@login_required
def seller_edit_product(id):

    user = User.query.get(session['user_id'])

    # ✅ only seller allowed
    if user.role != "seller":
        return "Access denied ❌"

    product = Product.query.get_or_404(id)

    # ✅ only own product
    if product.seller_id != user.id:
        return "Unauthorized ❌"

    if request.method == 'POST':
        product.short_name = request.form.get('short_name')
        product.name = request.form['name']
        product.price = request.form['price']
        product.category = request.form['category']
        product.image = request.form['image']

        db.session.commit()

        return redirect(url_for('my_products'))

    return render_template('edit_product.html', product=product)

@app.route('/delete-product/<int:id>')
@login_required
def delete_product(id):

    user = User.query.get(session['user_id'])

    # ✅ only seller allowed
    if user.role != "seller":
        return "Access denied"

    product = Product.query.get_or_404(id)

    # ✅ only own product
    if product.seller_id != user.id:
        return "Unauthorized ❌"

    db.session.delete(product)
    db.session.commit()

    return redirect(url_for('my_products'))

@app.route('/update-status/<int:id>/<status>')
@login_required
def update_status(id, status):

    user = User.query.get(session['user_id'])

    if not user or not user.is_admin:
        return "Access Denied ❌"

    order = Order.query.get_or_404(id)
    order.status = status

    db.session.commit()

    return redirect(url_for('admin_dashboard'))

@app.route('/update-settings', methods=['POST'])
@login_required
def update_settings():

    user = User.query.get(session['user_id'])

    if not user:
        session.clear()
        return redirect(url_for('login'))

    # ✅ SAVE PRIVACY
    user.privacy = request.form.get('privacy')

    # 🔥 FIX CHECKBOX (VERY IMPORTANT)
    user.dark_mode = True if request.form.get('dark_mode') else False

    db.session.commit()

    # 🔥 THIS IS THE MAIN LINE YOU ARE MISSING
    session['dark_mode'] = user.dark_mode

    print("Dark mode:", user.dark_mode)  # debug

    return redirect(url_for('settings'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)