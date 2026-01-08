from flask import Blueprint, request, jsonify
from app.extensions import limiter
from app.services.offer_service import OfferService

offers_bp = Blueprint('offers', __name__)

@offers_bp.route('/', methods=['GET'])
@limiter.limit("10/minute")
def list_offers():
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
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": "Bad Request", "message": str(e)}), 400

@offers_bp.route('/', methods=['POST'])
def create_offer():
    return OfferService.add_offer(request.json)

@offers_bp.route('/<offer_id>', methods=['GET', 'PATCH', 'DELETE'])
def offer_ops(offer_id):
    if request.method == 'GET':
        return OfferService.get_offer(offer_id)
    elif request.method == 'PATCH':
        return OfferService.update_offer(offer_id, request.json)
    elif request.method == 'DELETE':
        OfferService.delete_offer(offer_id)
        return '', 204
