from flask import Flask
from app.config import Config
from app.extensions import db, api, limiter, jwt, bcrypt

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    with app.app_context():
        db.create_all()
    api.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)

    from app.routes.agencies import agencies_bp
    from app.routes.offers import offers_bp
    from app.routes.reviews import reviews_bp
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.external import external_bp, living_cost_shortcut

    app.register_blueprint(agencies_bp, url_prefix='/v1')
    app.register_blueprint(offers_bp, url_prefix='/v1/offers')
    app.register_blueprint(reviews_bp, url_prefix='/v1')
    app.register_blueprint(auth_bp, url_prefix='/v1/auth')
    app.register_blueprint(admin_bp, url_prefix='/v1/admin')
    app.register_blueprint(external_bp)
    app.register_blueprint(living_cost_shortcut)  # Convenience routes at root level

    return app
