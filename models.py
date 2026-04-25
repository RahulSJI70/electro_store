from datetime import datetime
from flask_sqlalchemy import SQLAlchemy



db = SQLAlchemy()

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    price = db.Column(db.Float)
    image = db.Column(db.String(200))
    description = db.Column(db.String(200))
    category = db.Column(db.String(50))
    rating = db.Column(db.Float)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    seller = db.relationship('User', backref='products')
    images = db.relationship('ProductImage', backref='product', lazy=True)
    short_name = db.Column(db.String(150))
    brand = db.Column(db.String(100))
    # 🔥 ADD THIS
    def get_offer(self):
        return next((offer for offer in self.offers if offer.is_active), None)

    def get_discounted_price(self):
        offer = self.get_offer()

        if not offer:
            return self.price

        if offer.discount_percentage:
            return self.price * (1 - offer.discount_percentage / 100)

        if offer.discount_amount:
            return max(0, self.price - offer.discount_amount)

        return self.price

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    address_id = db.Column(db.Integer, db.ForeignKey('address.id'))

    product_name = db.Column(db.String(100))
    price = db.Column(db.Integer)
    status = db.Column(db.String(50), default="Placed")
    items = db.relationship('OrderItem', backref='order', lazy=True)
    address = db.relationship('Address')

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(200))
       
    phone = db.Column(db.String(20))           # ✅ ADD
    image = db.Column(db.String(200))
    role = db.Column(db.String(20), default="user")
    addresses = db.relationship('Address', backref='user', lazy=True)
    privacy = db.Column(db.String(20), default="Public")
    dark_mode = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_seller_request = db.Column(db.Boolean, default=False)
    language = db.Column(db.String(20), default="EN")

class Address(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(100), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)

from datetime import datetime

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    message = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Offer(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))

    discount_percentage = db.Column(db.Float, nullable=True)
    discount_amount = db.Column(db.Float, nullable=True)

    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)

    is_active = db.Column(db.Boolean, default=True)

    # Link to product
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))

    product = db.relationship('Product', backref='offers')    

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))

    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Float)

    product = db.relationship('Product')

class ProductImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(200))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))

    def __repr__(self):
        return f"<ProductImage {self.image}>"


  