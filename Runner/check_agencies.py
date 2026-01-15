from app import create_app
from app.models import Agency
from app.extensions import db

app = create_app()
with app.app_context():
    agencies = Agency.query.all()
    print(f"Total agencies: {len(agencies)}")
    for agency in agencies:
        print(f"ID: {agency.id}, Tax ID: {agency.tax_id}, Status: {agency.status}, Company: {agency.company_name}")
