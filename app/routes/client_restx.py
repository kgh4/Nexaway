"""
Client API Routes using Flask-RESTX
Provides endpoints for authenticated client operations
"""

from flask import request
from flask_restx import Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Review, User
from app.extensions import db, api

# Create namespace with /v1 prefix
client_ns = api.namespace('v1/client', description='Client operations')


@client_ns.route('/my-reviews')
class ClientMyReviews(Resource):
    @client_ns.doc('get_client_reviews', security=['Bearer Token'])
    @client_ns.param('page', 'Page number', type=int, default=1)
    @client_ns.param('limit', 'Items per page', type=int, default=20)
    @client_ns.response(200, 'Success')
    @client_ns.response(401, 'Unauthorized')
    @jwt_required()
    def get(self):
        """Get all reviews submitted by authenticated client - requires JWT"""
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)

        # Get current client ID from JWT
        client_id = get_jwt_identity()
        user = User.query.get(client_id)
        if not user:
            client_ns.abort(404, "User not found")

        # Query reviews for this client (owned or by email)
        query = Review.query.filter(
            (Review.client_id == client_id) |
            ((Review.client_id.is_(None)) & (Review.customer_email == user.email))
        )
        total = query.count()
        reviews = query.offset((page-1)*limit).limit(limit).all()
        pages = (total + limit - 1) // limit

        return {
            'data': [r.to_dict() for r in reviews],
            'total': total,
            'page': page,
            'pages': pages
        }, 200
