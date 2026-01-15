import csv
import bcrypt
from app import create_app
from app.models import Agency
from app.extensions import db

app = create_app()

def generate_unique_email(company_name, governorate):
    """Generate a unique email based on company name and governorate"""
    # Clean company name: lowercase, replace spaces with hyphens, remove special chars
    clean_name = ''.join(c for c in company_name.lower() if c.isalnum() or c == ' ').replace(' ', '-')
    return f"{clean_name}@{governorate.lower()}.tn.travel"

def seed_agencies_from_csv():
    with app.app_context():
        # Seed test agencies with new format
        test_agencies = [
            {"tax_id": "12345678A", "name": "Tunis Trust"},
            {"tax_id": "87654321B", "name": "Sousse Safe"},
        ]

        for agency_data in test_agencies:
            tax_id = agency_data['tax_id'].upper()  # Ensure uppercase
            if Agency.query.filter_by(tax_id=tax_id).first():
                continue

            agency = Agency(
                tax_id=tax_id,
                company_name=agency_data['name'],
                governorate='Tunis',
                email=f"{agency_data['name'].lower().replace(' ', '')}@test.tn",
                phone='71234567',
                status='pending',
                source='test',
                password_hash=bcrypt.hashpw('agency123'.encode(), bcrypt.gensalt()).decode()
            )

            db.session.add(agency)

        # Original CSV seeding (commented out for now)
        # csv_path = 'data/tunisia_agencies_real_dataset.csv'
        # with open(csv_path, 'r', encoding='utf-8') as file:
        #     reader = csv.DictReader(file)
        #     count = 0
        #     for row in reader:
        #         tax_id = row['tax_id'].strip()
        #         if not tax_id or len(tax_id) != 8:
        #             continue  # Skip invalid tax_ids (must be 8 characters)
        #
        #         # Check if agency already exists
        #         if Agency.query.filter_by(tax_id=tax_id).first():
        #             continue
        #
        #         company_name = row['company_name'].strip()
        #         governorate = row['governorate'].strip()
        #         email = generate_unique_email(company_name, governorate)
        #         phone = row['phone'].strip()
        #         trust_score = int(row['trust_score']) if row['trust_score'].isdigit() else 50
        #
        #         # Generate password hash for 'agency123'
        #         password_hash = bcrypt.hashpw('agency123'.encode(), bcrypt.gensalt()).decode()
        #
        #         agency = Agency(
        #             tax_id=tax_id,
        #             company_name=company_name,
        #             official_name=row['official_name'].strip() or None,
        #             governorate=governorate,
        #             email=email,
        #             phone=phone,
        #             trust_score=trust_score,
        #             status='pending',
        #             source='csv',
        #             password_hash=password_hash
        #         )
        #
        #         db.session.add(agency)
        #         count += 1

        db.session.commit()
        print("Seeded test agencies with new TN RNE format")

if __name__ == '__main__':
    seed_agencies_from_csv()
