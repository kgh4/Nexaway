from flask import Flask
from flask_cors import CORS
from app.config import Config
from app.extensions import db, api, limiter, jwt, bcrypt

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    with app.app_context():
        db.create_all()
    
    jwt.init_app(app)
    bcrypt.init_app(app)
    limiter.init_app(app)
    CORS(app)
    
    # Initialize API with Swagger at /swagger
    api.init_app(app)

    # Register namespaced routes (Flask-RESTX)
    from app.routes.auth_restx import auth_ns
    from app.routes.reviews_restx import reviews_ns
    from app.routes.agencies_restx import agencies_ns
    from app.routes.external_restx import external_ns
    from app.routes.offers_restx import offers_ns
    from app.routes.client_restx import client_ns
    
    # Namespaces are auto-registered via api.namespace() calls in route files
    
    # Register legacy home blueprint
    from app.routes.home import home_bp
    app.register_blueprint(home_bp)

    return app
