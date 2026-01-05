from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_restx import Api
from app.config import Config

db = SQLAlchemy()
api = Api()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    api.init_app(app)

    from app.routes.agencies import agencies_bp

    app.register_blueprint(agencies_bp, url_prefix='/v1')

    return app
