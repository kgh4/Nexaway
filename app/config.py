import os

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'nexaway-dev-secret-2025'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///instance/nexaway.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    RESTX_MASK_SWAGGER = False

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

__all__ = ['Config', 'DevelopmentConfig', 'ProductionConfig']