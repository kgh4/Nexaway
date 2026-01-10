from app import create_app, db
from app.models import Agency

app = create_app()
app.app_context().push()

# SHOW ALL AGENCIES
agencies = Agency.query.all()
print("ALL AGENCIES:")
for a in agencies:
    print(f"  id: {a.id}, tax_id: {a.tax_id}, company_name: {a.company_name}")

# TEST LOOKUP
test_id = "12345678"  # Your POST data
agency = Agency.query.filter_by(tax_id=test_id).first()
print(f"Found '{test_id}': {agency is not None}")
