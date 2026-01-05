from flask_sqlalchemy import SQLAlchemy
from flask_restx import Api
from flask_caching import Cache

# Extensions
db = SQLAlchemy()
api = Api(title='Nexaway API - Tunisia Travel Marketplace',
          version='1.0',
          description='Verified Tunisian travel agencies API',
          doc='/swagger')
cache = Cache(config={'CACHE_TYPE': 'simple'})  # Memory-based cache
