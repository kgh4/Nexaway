from flask import Flask
from app.config import Config
from app.extensions import db, api, limiter

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    with app.app_context():
        db.create_all()
    api.init_app(app)

    from app.routes.agencies import agencies_bp
    from app.routes.offers import offers_bp
    from app.routes.reviews import reviews_bp

    app.register_blueprint(agencies_bp, url_prefix='/v1')
    app.register_blueprint(offers_bp, url_prefix='/v1/offers')
    app.register_blueprint(reviews_bp, url_prefix='/v1')

    return app
