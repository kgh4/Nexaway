from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app.decorators import admin_required
from app.models import PendingAgency, Agency, Review
from app.extensions import db

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/pending_agencies', methods=['GET'])
@jwt_required()
@admin_required
def get_pending_agencies():
    """Get all pending agencies for admin review"""
    pending_agencies = PendingAgency.query.filter_by(status='pending').all()
    return jsonify([agency.to_dict() for agency in pending_agencies]), 200

@admin_bp.route('/bulk_approve_agencies', methods=['POST'])
@jwt_required()
@admin_required
def bulk_approve_agencies():
    """Bulk approve all pending agencies"""
    pending_agencies = Agency.query.filter_by(status='pending').all()
    count = 0
    for agency in pending_agencies:
        agency.status = 'approved'
        count += 1
    db.session.commit()
    return jsonify({
        'message': f'Bulk approved {count} agencies',
        'approved_count': count
    }), 200

@admin_bp.route('/approve-review/<review_id>', methods=['POST'])
@jwt_required()
@admin_required
def approve_review(review_id):
    """Approve a pending review"""
    review = Review.query.filter_by(review_id=review_id).first()
    if not review:
        return jsonify({"error": "Review not found"}), 404

    if review.status != 'pending':
        return jsonify({"error": "Review is not pending"}), 400

    review.status = 'approved'
    db.session.commit()

    return jsonify({"message": "Review approved successfully"}), 200
