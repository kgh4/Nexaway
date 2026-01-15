import uuid
import re
from flask import Blueprint, request, abort, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.models import Review, Agency, User
from app.extensions import db
from app.decorators import role_required
from datetime import datetime

from app.services.review_guardian import ReviewGuardian

reviews_bp = Blueprint('reviews', __name__)

@reviews_bp.route('/reviews', methods=['POST'])
@jwt_required()
@role_required('client')
def create_review():
    """Submit a new review (pending status)"""
    data = request.get_json()
    if not data:
        return {"error": "JSON payload required"}, 400

    # Extract and normalize tax_id: Remove dashes + uppercase
    raw_tax = data.get('agency_tax_id', '').strip()
    norm_tax = re.sub(r'-', '', raw_tax).upper()
    if not norm_tax:
        return {"error": "agency_tax_id is required"}, 400

    # VALIDATE NORMALIZED FORMAT: 8DIGITS+1LETTER
    if not re.match(r'^[0-9]{8}[A-Z]$', norm_tax):
        return jsonify({
            "error": f"Invalid RNE: 8 digits + 1 letter\nGot: '{raw_tax}'\nNorm: '{norm_tax}'"
        }), 400

    # LOOKUP BY NORMALIZED TAX_ID
    from sqlalchemy import func
    agency = Agency.query.filter(
        func.upper(func.replace(Agency.tax_id, '-', '')) == norm_tax
    ).first_or_404("Agency not found")

    # Check for duplicate review (one per customer per agency)
    client_id = get_jwt_identity()
    existing_review = Review.query.filter_by(
        client_id=client_id,
        agency_id=agency.agency_id
    ).first()
    if existing_review:
        return {"error": "You have already submitted a review for this agency"}, 409

    # Validate rating
    if not (1 <= data['rating'] <= 5):
        return {"error": "Rating must be between 1 and 5"}, 400

    # Generate review ID
    review_id = f"R-{uuid.uuid4().hex[:8].upper()}"

    # Create review
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

    # Check for suspicious content
    if ReviewGuardian.is_suspicious(data):
        review.status = 'rejected'  # Auto-reject suspicious reviews

    db.session.add(review)
    db.session.commit()

    return jsonify({
        "msg": "Review created!",
        "review_id": review.id,
        "trust_impact": agency.trust_score
    }), 201


@reviews_bp.route('/reviews', methods=['GET'])
def get_reviews():
    """Get paginated list of reviews"""
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    status = request.args.get('status')  # pending, approved, rejected

    query = Review.query
    if status:
        query = query.filter_by(status=status)

    total = query.count()
    reviews = query.offset((page-1)*limit).limit(limit).all()

    return {
        'data': [r.to_dict() for r in reviews],
        'total': total,
        'page': page,
        'limit': limit
    }

@reviews_bp.route('/reviews/<review_id>', methods=['GET'])
def get_review(review_id):
    """Get single review by ID"""
    review = Review.query.filter_by(review_id=review_id).first()
    if not review:
        return {"error": "Review not found"}, 404

    return review.to_dict()

@reviews_bp.route('/agencies/<agency_id>/reviews', methods=['GET'])
def get_agency_reviews(agency_id):
    """Get reviews for a specific agency"""
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    status = request.args.get('status', 'approved')  # Default to approved only

    # Validate agency exists
    agency = Agency.query.filter_by(tax_id=agency_id).first()
    if not agency:
        return {"error": "Agency not found"}, 404

    query = Review.query.filter_by(agency_id=agency_id, status=status)
    total = query.count()
    reviews = query.offset((page-1)*limit).limit(limit).all()

    return {
        'data': [r.to_dict() for r in reviews],
        'total': total,
        'page': page,
        'limit': limit,
        'agency': agency.to_dict()
    }

@reviews_bp.route('/client/my-reviews', methods=['GET'])
@jwt_required()
@role_required('client')
def get_client_reviews():
    """Get reviews for the authenticated client"""
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)

    # Get current client ID from JWT
    claims = get_jwt()
    client_id = int(claims['sub'])

    # Get user email for fallback matching
    user = User.query.get(client_id)
    if not user:
        return {"error": "User not found"}, 404

    # Query reviews for this client (owned or by email if not claimed)
    query = Review.query.filter(
        (Review.client_id == client_id) |
        ((Review.client_id.is_(None)) & (Review.customer_email == user.email))
    )
    total = query.count()
    reviews = query.offset((page-1)*limit).limit(limit).all()

    # Format response as specified
    result = []
    for review in reviews:
        result.append({
            'review_id': review.review_id,
            'agency': {
                'name': review.agency.company_name if review.agency else None,
                'agency_id': review.agency_id
            },
            'stars': review.rating,
            'comment': review.comment,
            'created_at': review.created_at.strftime('%Y-%m-%d') if review.created_at else None,
            'status': review.status
        })

    return result

@reviews_bp.route('/client/review/<review_id>/re-review', methods=['PUT'])
@jwt_required()
@role_required('client')
def re_review(review_id):
    """Client re-reviews after agency reply"""
    data = request.get_json()
    if not data or 'stars' not in data:
        return {"error": "Stars rating required"}, 400

    # Get current client ID from JWT
    claims = get_jwt()
    client_id = int(claims['sub'])

    # Get review
    review = Review.query.filter_by(review_id=review_id, client_id=client_id).first()
    if not review:
        return {"error": "Review not found or not owned by you"}, 404

    # Check if agency has replied
    if not review.reply:
        return {"error": "Agency has not replied yet"}, 400

    # Update re-rating and re-comment
    review.re_rating = data['stars']
    review.re_comment = data.get('comment', '')
    review.updated_at = db.func.now()

    db.session.commit()

    return {"message": "Re-review submitted successfully"}, 200

@reviews_bp.route('/client/review/<review_id>', methods=['PATCH'])
@jwt_required()
@role_required('client')
def patch_review(review_id):
    """Client edits their own review"""
    # Get current client ID from JWT
    claims = get_jwt()
    client_id = int(claims['sub'])

    # Get user email for fallback matching
    user = User.query.get(client_id)
    if not user:
        return {"error": "User not found"}, 404

    # Get review owned by client (or by email if not claimed)
    review = Review.query.filter(
        (Review.review_id == review_id) &
        ((Review.client_id == client_id) |
         ((Review.client_id.is_(None)) & (Review.customer_email == user.email)))
    ).first()

    if not review:
        return {"error": "Review not found or not owned by you"}, 404

    # Check edit rules: before agency reply OR after re-review window
    # Assuming re-review window is after agency reply and re-rating
    if review.reply and review.re_rating is not None:
        return {"error": "Cannot edit review after re-review"}, 400

    data = request.get_json()
    if not data:
        return {"error": "JSON payload required"}, 400

    # Update rating if provided
    if 'stars' in data:
        stars = data['stars']
        if not (1 <= stars <= 5):
            return {"error": "Rating must be between 1 and 5"}, 400
        review.rating = stars

    # Update comment if provided
    if 'comment' in data:
        review.comment = data['comment']

    review.updated_at = datetime.utcnow()
    db.session.commit()

    return review.to_dict()
