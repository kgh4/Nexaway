"""
Review API Routes using Flask-RESTX
Provides endpoints for submitting, viewing, and managing reviews
"""

import uuid
import re
from flask import request
from flask_restx import Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import func
from app.models import Review, Agency, User
from app.extensions import db, api
from app.decorators import role_required
from app.services.review_guardian import ReviewGuardian

# Create namespace with /v1 prefix
reviews_ns = api.namespace('v1/reviews', description='Review management')

# Define models for Swagger
review_model = api.model('Review', {
    'review_id': fields.String(description='Review ID'),
    'agency_tax_id': fields.String(required=True, description='Agency RNE/Tax ID'),
    'customer_name': fields.String(required=True, description='Reviewer name'),
    'customer_email': fields.String(required=True, description='Reviewer email'),
    'rating': fields.Integer(required=True, description='Rating 1-5'),
    'comment': fields.String(description='Review comment'),
    'status': fields.String(description='Review status')
})

review_response_model = api.model('ReviewResponse', {
    'msg': fields.String(),
    'review_id': fields.String(),
    'trust_impact': fields.Float()
})

reviews_list_model = api.model('ReviewsList', {
    'data': fields.List(fields.Raw),
    'total': fields.Integer(),
    'page': fields.Integer(),
    'pages': fields.Integer()
})


@reviews_ns.route('')
class ReviewList(Resource):
    @reviews_ns.doc('list_reviews')
    @reviews_ns.param('page', 'Page number', type=int, default=1)
    @reviews_ns.param('limit', 'Items per page', type=int, default=20)
    @reviews_ns.param('status', 'Filter by status: pending/approved/rejected')
    @reviews_ns.response(200, 'Success', reviews_list_model)
    def get(self):
        """Get paginated list of reviews - public endpoint"""
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        status = request.args.get('status')

        query = Review.query
        if status:
            query = query.filter_by(status=status)

        total = query.count()
        reviews = query.offset((page-1)*limit).limit(limit).all()
        pages = (total + limit - 1) // limit

        return {
            'data': [r.to_dict() for r in reviews],
            'total': total,
            'page': page,
            'pages': pages
        }, 200

    @reviews_ns.doc('create_review', security=['Bearer Token'])
    @reviews_ns.expect(review_model)
    @reviews_ns.response(201, 'Created', review_response_model)
    @reviews_ns.response(400, 'Bad Request')
    @reviews_ns.response(401, 'Unauthorized')
    @reviews_ns.response(409, 'Conflict')
    @jwt_required()
    def post(self):
        """Submit a new review (pending status) - requires JWT"""
        data = request.get_json()
        if not data:
            reviews_ns.abort(400, "JSON payload required")

        # Extract and normalize tax_id
        raw_tax = data.get('agency_tax_id', '').strip()
        norm_tax = re.sub(r'-', '', raw_tax).upper()
        if not norm_tax:
            reviews_ns.abort(400, "agency_tax_id is required")

        # Validate format: 7-8 digits + 1 letter (Tunisian RNE format)
        if not re.match(r'^[0-9]{7,8}[A-Z]$', norm_tax):
            reviews_ns.abort(400, f"Invalid RNE: 7-8 digits + 1 letter (Got: {raw_tax})")

        # Lookup agency
        agency = Agency.query.filter(
            func.upper(func.replace(Agency.tax_id, '-', '')) == norm_tax
        ).first()
        if not agency:
            reviews_ns.abort(404, "Agency not found")

        # Check duplicate
        client_id = get_jwt_identity()
        if Review.query.filter_by(client_id=client_id, agency_id=agency.agency_id).first():
            reviews_ns.abort(409, "You have already submitted a review for this agency")

        # Validate rating
        if not (1 <= data.get('rating', 0) <= 5):
            reviews_ns.abort(400, "Rating must be between 1 and 5")

        review_id = f"R-{uuid.uuid4().hex[:8].upper()}"
        review = Review(
            review_id=review_id,
            agency_id=agency.agency_id,
            client_id=client_id,
            customer_name=data['customer_name'],
            customer_email=data['customer_email'],
            rating=data['rating'],
            comment=data.get('comment', ''),
            status='pending'
        )

        if ReviewGuardian.is_suspicious(data):
            review.status = 'rejected'

        db.session.add(review)
        db.session.commit()

        return {
            "msg": "Review created!",
            "review_id": review.id,
            "trust_impact": agency.trust_score
        }, 201


@reviews_ns.route('/<int:review_id>')
class ReviewDetail(Resource):
    @reviews_ns.doc('get_review')
    @reviews_ns.response(200, 'Success')
    @reviews_ns.response(404, 'Not Found')
    def get(self, review_id):
        """Get review details by ID"""
        review = Review.query.get_or_404(review_id)
        return review.to_dict(), 200


@reviews_ns.route('/reply/<int:review_id>')
class ReviewReply(Resource):
    @reviews_ns.doc('reply_review', security=['Bearer Token'])
    @reviews_ns.expect(api.model('Reply', {
        'reply_text': fields.String(required=True, description='Agency reply')
    }))
    @reviews_ns.response(200, 'Success')
    @reviews_ns.response(401, 'Unauthorized')
    @reviews_ns.response(403, 'Forbidden')
    @reviews_ns.response(404, 'Not Found')
    @jwt_required()
    def post(self, review_id):
        """Add agency reply to review - requires JWT and agency role"""
        review = Review.query.get_or_404(review_id)
        user_id = get_jwt_identity()
        
        # Verify ownership
        user = User.query.get(user_id)
        if not user or user.agency_id != review.agency_id:
            reviews_ns.abort(403, "Not authorized to reply to this review")

        data = request.get_json()
        review.agency_reply = data.get('reply_text')
        review.reply_timestamp = func.now()
        db.session.commit()

        return {"msg": "Reply added successfully"}, 200

