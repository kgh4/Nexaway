from app import create_app
from app.models import Agency
from app.extensions import db

app = create_app()
with app.app_context():
    pending = Agency.query.filter_by(status='pending').all()
    print(f'Found {len(pending)} pending agencies')
    count = 0
    for agency in pending:
        agency.status = 'approved'
        count += 1
    db.session.commit()
    print(f'Approved {count} agencies')
