from flask_sqlalchemy import SQLAlchemy
from flask_restx import Api
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
api = Api()
limiter = Limiter(key_func=get_remote_address)
