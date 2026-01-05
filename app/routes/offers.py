from flask import Blueprint, request
from app.services.offer_service import OfferService

offers_bp = Blueprint('offers', __name__)

@offers_bp.route('/', methods=['GET'])
def list_offers():
    return OfferService.get_offers(request.args)

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
