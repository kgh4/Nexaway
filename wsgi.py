"""
WSGI entry point for Gunicorn
Ensures proper application creation and configuration
"""
import os
from app import create_app, db

# Create Flask app instance
app = create_app()

# Set production configuration
if os.environ.get('FLASK_ENV') == 'production':
    from app.config import ProductionConfig
    app.config.from_object(ProductionConfig)

# Initialize database tables on startup
with app.app_context():
    try:
        db.create_all()
        print("[✓] Database tables initialized")
    except Exception as e:
        print(f"[!] Database initialization error: {str(e)}")

if __name__ == '__main__':
    # Development only
    app.run(debug=True, host='0.0.0.0', port=8000)
