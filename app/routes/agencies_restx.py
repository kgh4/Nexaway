"""
Agencies API Routes using Flask-RESTX
Provides endpoints for agency management and trust scoring
"""

import uuid
from flask import request
from flask_restx import Resource, fields, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from app.models import Agency, Review
from app.extensions import db, api
from app.services.agency_service import AgencyService
from app.services.trust_score_calculator import TrustScoreCalculator

# Create namespace with /v1 prefix
agencies_ns = api.namespace('v1/agencies', description='Agency management')

# Define models
agency_model = api.model('Agency', {
    'agency_name': fields.String(required=True),
    'official_name': fields.String(),
    'tax_id': fields.String(required=True),
    'email': fields.String(required=True),
    'phone': fields.String(),
    'governorate': fields.String(),
    'category': fields.String(),
    'sectors': fields.String()
})

agency_response = api.model('AgencyResponse', {
    'agency_id': fields.String(),
    'agency_name': fields.String(),
    'tax_id': fields.String(),
    'email': fields.String(),
    'trust_score': fields.Float(),
    'status': fields.String(),
    'reviews_count': fields.Integer()
})


@agencies_ns.route('')
class AgencyList(Resource):
    @agencies_ns.doc('list_agencies')
    @agencies_ns.param('status', 'Filter by status: approved/pending/rejected')
    @agencies_ns.param('category', 'Filter by category')
    @agencies_ns.response(200, 'Success')
    def get(self):
        """Get all approved agencies with trust scores"""
        status = request.args.get('status', 'approved')
        approved_agencies = Agency.query.filter_by(status=status).all()

        agencies_data = []
        for agency in approved_agencies:
            reviews = Review.query.filter_by(
                agency_id=agency.agency_id, 
                status='approved'
            ).all()

            result = TrustScoreCalculator.calculate_trust_score(agency, reviews)
            agencies_data.append({
                'agency_id': agency.agency_id,
                'tax_id': agency.tax_id,
                'agency_name': agency.company_name,
                'official_name': agency.official_name,
                'category': agency.category,
                'email': agency.email,
                'phone': agency.phone,
                'governorate': agency.governorate,
                'trust_score': result['score'],
                'status': agency.status,
                'reviews_count': len(reviews)
            })

        agencies_data.sort(key=lambda x: x['trust_score'], reverse=True)

        return {
            'data': agencies_data,
            'total': len(agencies_data),
            'status': status
        }, 200


@agencies_ns.route('/register')
class AgencyRegister(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('agency_name', type=str, required=True, location='form')
        self.parser.add_argument('tax_id', type=str, required=True, location='form')
        self.parser.add_argument('email', type=str, required=True, location='form')
        self.parser.add_argument('governorate', type=str, required=True, location='form')
        self.parser.add_argument('phone', type=str, required=True, location='form')
        self.parser.add_argument('official_name', type=str, required=False, location='form')
        self.parser.add_argument('category', type=str, required=False, location='form')
        self.parser.add_argument('sectors', type=str, required=False, location='form')

    @agencies_ns.doc('register_agency')
    @agencies_ns.response(201, 'Created')
    @agencies_ns.response(400, 'Bad Request')
    def post(self):
        """Register new agency with form data (pending approval). Required: agency_name, tax_id, email, governorate, phone"""
        args = self.parser.parse_args()
        
        # Convert to dict format expected by AgencyService
        data = {
            'company_name': args.agency_name,
            'tax_id': args.tax_id,
            'email': args.email,
            'governorate': args.governorate,
            'phone': args.phone,
            'official_name': args.official_name,
            'category': args.category,
            'sectors': args.sectors
        }
        
        try:
            result = AgencyService.add_agency(data)
            return result, 201
        except Exception as e:
            agencies_ns.abort(400, str(e))


@agencies_ns.route('/<agency_id>')
class AgencyDetail(Resource):
    @agencies_ns.doc('get_agency')
    @agencies_ns.response(200, 'Success', agency_response)
    @agencies_ns.response(404, 'Not Found')
    def get(self, agency_id):
        """Get agency details by ID"""
        agency = Agency.query.filter_by(agency_id=agency_id).first_or_404()
        reviews = Review.query.filter_by(
            agency_id=agency.agency_id,
            status='approved'
        ).all()

        result = TrustScoreCalculator.calculate_trust_score(agency, reviews)
        return {
            'agency_id': agency.agency_id,
            'tax_id': agency.tax_id,
            'agency_name': agency.company_name,
            'official_name': agency.official_name,
            'category': agency.category,
            'email': agency.email,
            'phone': agency.phone,
            'governorate': agency.governorate,
            'website': agency.website,
            'trust_score': result['score'],
            'status': agency.status,
            'reviews_count': len(reviews),
            'evaluation_reasons': result['reasons']
        }, 200


@agencies_ns.route('/<agency_id>/reviews')
class AgencyReviews(Resource):
    @agencies_ns.doc('get_agency_reviews')
    @agencies_ns.param('status', 'Filter by status: approved/pending/rejected')
    @agencies_ns.response(200, 'Success')
    def get(self, agency_id):
        """Get all reviews for an agency"""
        agency = Agency.query.filter_by(agency_id=agency_id).first_or_404()
        status = request.args.get('status', 'approved')

        reviews = Review.query.filter_by(
            agency_id=agency.agency_id,
            status=status
        ).all()

        return {
            'agency_id': agency_id,
            'reviews': [r.to_dict() for r in reviews],
            'total': len(reviews)
        }, 200


@agencies_ns.route('/stats')
class AgencyStats(Resource):
    @agencies_ns.doc('get_agency_stats')
    @agencies_ns.response(200, 'Success')
    def get(self):
        """Get aggregate statistics about all agencies"""
        total_agencies = Agency.query.count()
        approved_agencies = Agency.query.filter_by(status='approved').count()
        pending_agencies = Agency.query.filter_by(status='pending').count()
        rejected_agencies = Agency.query.filter_by(status='rejected').count()
        
        total_reviews = Review.query.count()
        approved_reviews = Review.query.filter_by(status='approved').count()
        pending_reviews = Review.query.filter_by(status='pending').count()
        rejected_reviews = Review.query.filter_by(status='rejected').count()
        
        # Get average trust score
        agencies = Agency.query.filter_by(status='approved').all()
        trust_scores = []
        for agency in agencies:
            reviews = Review.query.filter_by(agency_id=agency.agency_id, status='approved').all()
            result = TrustScoreCalculator.calculate_trust_score(agency, reviews)
            trust_scores.append(result['score'])
        
        avg_trust_score = sum(trust_scores) / len(trust_scores) if trust_scores else 0
        
        # Get statistics by governorate
        governorates = db.session.query(Agency.governorate, func.count(Agency.agency_id)).filter_by(status='approved').group_by(Agency.governorate).all()
        governorate_stats = {gov: count for gov, count in governorates if gov}
        
        # Get average rating
        avg_rating = db.session.query(func.avg(Review.rating)).filter_by(status='approved').scalar() or 0
        
        return {
            'total_agencies': total_agencies,
            'agencies_by_status': {
                'approved': approved_agencies,
                'pending': pending_agencies,
                'rejected': rejected_agencies
            },
            'total_reviews': total_reviews,
            'reviews_by_status': {
                'approved': approved_reviews,
                'pending': pending_reviews,
                'rejected': rejected_reviews
            },
            'average_trust_score': round(avg_trust_score, 2),
            'average_rating': round(float(avg_rating), 2) if avg_rating else 0,
            'agencies_by_governorate': governorate_stats
        }, 200
