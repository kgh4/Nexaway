import uuid
from flask import Blueprint, request, abort
from app.models import Review, Agency
from app.extensions import db

reviews_bp = Blueprint('reviews', __name__)

@reviews_bp.route('/reviews', methods=['POST'])
def create_review():
    """Submit a new review (pending status)"""
    data = request.get_json()
    if not data:
        return {"error": "JSON payload required"}, 400

    required_fields = ['agency_id', 'customer_name', 'customer_email', 'rating']
    for field in required_fields:
        if field not in data:
            return {"error": f"{field} is required"}, 400

    # UNIQUE CHECK 👇
    existing = Review.query.filter_by(
        customer_email=data['customer_email'],
        agency_id=data['agency_id']
    ).first()

    if existing:
        return {"error": f"{data['customer_email']} already reviewed this agency! (R-{existing.review_id})"}, 409

    # Validate agency exists
    agency = Agency.query.filter_by(tax_id=data['agency_id']).first()
    if not agency:
        return {"error": "Agency not found"}, 404

    # Validate rating
    if not (1 <= data['rating'] <= 5):
        return {"error": "Rating must be between 1 and 5"}, 400

    # Generate review ID
    review_id = f"R-{uuid.uuid4().hex[:8].upper()}"

    # Create review
    review = Review(
        review_id=review_id,
        agency_id=data['agency_id'],
        customer_name=data['customer_name'],
        customer_email=data['customer_email'],
        rating=data['rating'],
        comment=data.get('comment', ''),
        status='pending'
    )

    db.session.add(review)
    db.session.commit()

    return review.to_dict(), 201

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
