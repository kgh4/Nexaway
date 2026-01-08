from flask_sqlalchemy import SQLAlchemy
from flask_restx import Api

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Extensions
db = SQLAlchemy()
api = Api(title='Nexaway API - Tunisia Travel Marketplace',
          version='1.0',
          description='Verified Tunisian travel agencies API',
          doc='/swagger')

limiter = Limiter(get_remote_address, default_limits=["200 per day", "50 per hour"])
