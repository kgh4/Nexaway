"""
Offers API Routes using Flask-RESTX
Provides endpoints for travel offer management
"""

from flask import request
from flask_restx import Resource, fields
from app.extensions import api, limiter
from app.services.offer_service import OfferService

# Create namespace with /v1 prefix
offers_ns = api.namespace('v1/offers', description='Travel offers management')

# Define models
offer_model = api.model('Offer', {
    'type': fields.String(description='Offer type: travel/visa/insurance'),
    'domestic': fields.Boolean(description='Is domestic offer'),
    'segment': fields.String(description='Target segment'),
    'pilgrimage_type': fields.String(description='Type of pilgrimage'),
    'from_city': fields.String(description='Origin city'),
    'to_city': fields.String(description='Destination city'),
    'price': fields.Float(description='Offer price'),
    'description': fields.String(description='Offer description')
})

offer_response = api.model('OfferResponse', {
    'offer_id': fields.String(),
    'type': fields.String(),
    'from_city': fields.String(),
    'to_city': fields.String(),
    'price': fields.Float(),
    'status': fields.String()
})

offers_list_response = api.model('OffersListResponse', {
    'data': fields.List(fields.Raw()),
    'total': fields.Integer(),
    'page': fields.Integer(),
    'pages': fields.Integer()
})


@offers_ns.route('')
class OfferList(Resource):
    @offers_ns.doc('list_offers')
    @offers_ns.param('type', 'Offer type: travel/visa/insurance')
    @offers_ns.param('domestic', 'Filter by domestic (true/false)')
    @offers_ns.param('segment', 'Target segment')
    @offers_ns.param('from_city', 'Origin city')
    @offers_ns.param('to_city', 'Destination city')
    @offers_ns.param('min_price', 'Minimum price')
    @offers_ns.param('page', 'Page number', type=int, default=1)
    @offers_ns.param('limit', 'Items per page', type=int, default=10)
    @offers_ns.param('sort', 'Sort by: price_asc/price_desc/newest', default='price_asc')
    @offers_ns.response(200, 'Success', offers_list_response)
    @offers_ns.response(400, 'Bad Request')
    @limiter.limit("10/minute")
    def get(self):
        """Get all offers with filtering and pagination"""
        try:
            # Parse query params
            filters = {}
            for key in ['type', 'domestic', 'segment', 'pilgrimage_type', 'from_city', 'to_city', 'min_price']:
                value = request.args.get(key)
                if value is not None:
                    filters[key] = value

            page = request.args.get('page', 1, type=int)
            limit = request.args.get('limit', 10, type=int)
            sort = request.args.get('sort', 'price_asc')

            result = OfferService.get_offers(filters=filters, page=page, limit=limit, sort=sort)
            return result, 200
        except Exception as e:
            offers_ns.abort(400, f"Bad Request: {str(e)}")

    @offers_ns.doc('create_offer')
    @offers_ns.expect(offer_model)
    @offers_ns.response(201, 'Created', offer_response)
    @offers_ns.response(400, 'Bad Request')
    def post(self):
        """Create new offer"""
        try:
            result = OfferService.add_offer(request.get_json())
            return result, 201
        except Exception as e:
            offers_ns.abort(400, str(e))


@offers_ns.route('/<offer_id>')
class OfferDetail(Resource):
    @offers_ns.doc('get_offer')
    @offers_ns.response(200, 'Success', offer_response)
    @offers_ns.response(404, 'Not Found')
    def get(self, offer_id):
        """Get offer details by ID"""
        try:
            result = OfferService.get_offer(offer_id)
            return result, 200
        except Exception as e:
            offers_ns.abort(404, f"Offer not found: {str(e)}")

    @offers_ns.doc('update_offer')
    @offers_ns.expect(offer_model)
    @offers_ns.response(200, 'Success', offer_response)
    @offers_ns.response(404, 'Not Found')
    def patch(self, offer_id):
        """Update offer details"""
        try:
            result = OfferService.update_offer(offer_id, request.get_json())
            return result, 200
        except Exception as e:
            offers_ns.abort(404, str(e))

    @offers_ns.doc('delete_offer')
    @offers_ns.response(204, 'Deleted')
    @offers_ns.response(404, 'Not Found')
    def delete(self, offer_id):
        """Delete offer by ID"""
        try:
            OfferService.delete_offer(offer_id)
            return '', 204
        except Exception as e:
            offers_ns.abort(404, str(e))
