from flask_sqlalchemy import SQLAlchemy
from flask_restx import Api

# Extensions
db = SQLAlchemy()
api = Api(title='Nexaway API - Tunisia Travel Marketplace',
          version='1.0',
          description='Verified Tunisian travel agencies API',
          doc='/swagger')
