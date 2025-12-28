# -*- coding: utf-8 -*-
from flask import Flask, jsonify
from .config import Config
from .models import Agency
from .extensions import db, api
import os
import csv

def create_app(config_class=None):
    app = Flask(__name__)

    # Config (from config.py)
    app.config.from_object(Config)

    # Create instance folder
    os.makedirs('instance', exist_ok=True)

    # Init extensions
    db.init_app(app)
    api.init_app(app)

    # Import blueprint here to avoid circular import
    from .routes.agencies import agencies_bp
    api.add_namespace(agencies_bp, path='/v1/agencies')
    print("✅ Agencies blueprint registered! 🚀")
    
    # CLI Commands
    @app.cli.command()
    def db_create():
        """Create database tables."""
        db.create_all()
        print("✅ Database tables created!")
    
    @app.cli.command()
    def db_seed():
        """Seed database with 41 Tunisian agencies."""
        try:
            csv_path = os.path.join(os.path.dirname(__file__), '..', 'tunisia_agencies_real_dataset.csv')
            print(f"📁 Loading: {csv_path}")
            
            if not os.path.exists(csv_path):
                print("❌ CSV not found!")
                return
            
            # Clear existing data
            Agency.query.delete()
            db.session.commit()
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    agency = Agency(
                        tax_id=row.get('tax_id'),
                        company_name=row.get('company_name'),
                        official_name=row.get('official_name'),
                        category=row.get('category'),
                        email=row.get('email'),
                        phone=row.get('phone'),
                        address=row.get('address'),
                        governorate=row.get('governorate'),
                        website=row.get('website'),
                        sectors=row.get('sectors'),
                        tourism_license=row.get('tourism_license'),
                        registry_number=row.get('registry_number'),
                        verification_status=row.get('verification_status', 'pending'),
                        trust_score=int(float(row.get('trust_score') or 50)),
                        status=row.get('status', 'active'),
                        source='csv'
                    )
                    db.session.add(agency)
                    count += 1
            
            db.session.commit()
            print(f"✅ {count} Tunisian agencies imported! 🎉")
            print("🌟 Ready for API endpoints!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Seed error: {e}")
    
    # Health Check
    @app.route('/health')
    def health():
        return jsonify({'status': 'ok', 'version': '1.0'})
    
    # Landing Page
    @app.route('/')
    def index():
        return '''
        <h1>🚀 Nexaway API Ready!</h1>
        <p><a href="/health">Health Check</a> | 
           <a href="/swagger">Swagger Docs</a></p>
        <p>Next: Add API routes → flask db_create → flask db_seed → 41 agencies!</p>
        '''
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'message': 'Resource not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'message': 'Internal server error'}), 500
    
    print("🚀 Nexaway API Ready!")
    return app

__all__ = ['create_app', 'db']
