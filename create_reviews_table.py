from app import create_app
from app.extensions import db

app = create_app()

with app.app_context():
    # Create reviews table
    db.create_all()
    print("✅ Reviews table created successfully!")
