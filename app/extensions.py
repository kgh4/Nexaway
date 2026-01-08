from flask_sqlalchemy import SQLAlchemy
from flask_restx import Api
<<<<<<< HEAD

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
=======
from flask_caching import Cache
>>>>>>> 53fd9a4764b0db131c900e6dd905f6e3fd0e14e5

# Extensions
db = SQLAlchemy()
api = Api(title='Nexaway API - Tunisia Travel Marketplace',
          version='1.0',
          description='Verified Tunisian travel agencies API',
          doc='/swagger')
<<<<<<< HEAD

limiter = Limiter(get_remote_address, default_limits=["200 per day", "50 per hour"])
=======
cache = Cache(config={'CACHE_TYPE': 'simple'})  # Memory-based cache
>>>>>>> 53fd9a4764b0db131c900e6dd905f6e3fd0e14e5
