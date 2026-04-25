from app import app, db
from models import Offer, Product

with app.app_context():
    product = Product.query.first()

    print("Using product:", product.name)

    offer = Offer(
        title="Festival Sale",
        description="Limited time offer",
        discount_percentage=20,
        product_id=product.id,
        is_active=True
    )

    db.session.add(offer)
    db.session.commit()

    print("Offer added ✅")