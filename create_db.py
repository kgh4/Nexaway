import csv
from app import create_app, db
from app.models import Agency, PendingAgency, Review
from app.services.offer_service import OfferService

# Create app context
app = create_app()
app.app_context().push()

# Create tables
db.create_all()

# Load agencies from CSV
print("Loading agencies from CSV...")
with open('data/tunisia_agencies_real_dataset.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Skip if tax_id already exists
        if Agency.query.filter_by(tax_id=row['tax_id']).first():
            continue

        agency = Agency(
            tax_id=row['tax_id'],
            company_name=row['company_name'],
            official_name=row.get('official_name', ''),
            governorate=row.get('governorate', ''),
            email=row.get('email', ''),
            phone=row.get('phone', ''),
            trust_score=int(row.get('trust_score', 50)),
            status='active',
            source='csv'
        )
        db.session.add(agency)

db.session.commit()
print("✅ Agencies loaded!")

# Seed sample offers
OfferService.seed_sample_data()

print("✅ Database created! instance/nexaway.db")
print("✅ Run: python run.py")
