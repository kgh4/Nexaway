from app import create_app, db
from app.models import Agency, PendingAgency
from app.services.offer_service import OfferService

# Create app context
app = create_app()
app.app_context().push()

# Create tables
db.create_all()

# Seed sample offers
OfferService.seed_sample_data()

print("✅ Database created! instance/agencies.db")
print("✅ Run: python run.py")
