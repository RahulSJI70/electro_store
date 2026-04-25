from app import app
from models import db, Product

with app.app_context():

    p1 = Product(
        name="iPhone 14",
        price=999,
        image="img/product-3.png",
        description="Apple smartphone"
    )

    p2 = Product(
        name="Smart Watch",
        price=199,
        image="img/product-4.png",
        description="Modern smartwatch"
    )

    p3 = Product(
        name="Camera",
        price=450,
        image="img/product-5.png",
        description="Professional camera"
    )

    db.session.add_all([p1, p2, p3])
    db.session.commit()

    print("Products added successfully!")