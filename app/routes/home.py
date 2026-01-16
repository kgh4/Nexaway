from flask import Blueprint, jsonify, redirect, url_for
from flask_smorest import Blueprint as SmorestBlueprint
from marshmallow import Schema, fields

# Home blueprint for root endpoints
home_bp = Blueprint('home', __name__)

class MessageSchema(Schema):
    """Schema for API response messages"""
    status = fields.Str()
    message = fields.Str()
    version = fields.Str()
    docs_url = fields.Str()
    endpoints = fields.Dict()

@home_bp.route('/', methods=['GET'])
def homepage():
    """API homepage with documentation links"""
    return jsonify({
        'status': 'success',
        'message': 'Welcome to Nexaway API - Tunisian Diaspora Trust Platform',
        'version': '1.0.0',
        'docs_url': '/docs',
        'swagger_url': '/swagger',
        'redoc_url': '/redoc',
        'openapi_json': '/openapi.json',
        'endpoints': {
            'agencies': '/v1/agencies',
            'auth': '/v1/auth',
            'reviews': '/v1/reviews',
            'offers': '/v1/offers',
            'admin': '/v1/admin',
            'external': '/external'
        }
    })

@home_bp.route('/swagger', methods=['GET'])
def swagger_redirect():
    """Redirect /swagger to /docs (Swagger UI)"""
    return redirect('/docs', code=301)

@home_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'service': 'nexaway-api'
    }), 200
