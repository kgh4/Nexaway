from app import create_app, db
from app.models import Agency

# Create app context
app = create_app()
app.app_context().push()

# Create tables
db.create_all()

print("✅ Database created! instance/agencies.db")
print("✅ Run: python run.py")
