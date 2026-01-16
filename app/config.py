import os

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'nexaway-dev-secret-2025'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'nexaway-jwt-secret-2025'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///nexaway.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask-RESTX Configuration
    RESTX_MASK_SWAGGER = False
    JSON_SORT_KEYS = False

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

__all__ = ['Config', 'DevelopmentConfig', 'ProductionConfig']