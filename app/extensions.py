from flask_sqlalchemy import SQLAlchemy
from flask_restx import Api
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS

db = SQLAlchemy()
api = Api(
    version='1.0',
    title='Nexaway API',
    description='Tunisian Diaspora Trust & Relocation Platform',
    doc='/swagger',
    prefix='',
    ordered=True
)
limiter = Limiter(key_func=get_remote_address)
jwt = JWTManager()
bcrypt = Bcrypt()
cors = CORS()
