"""
External API Routes using Flask-RESTX
Integrations: Currency exchange, Weather, Living costs
"""

from flask import request
from flask_restx import Resource, fields
import logging
from app.services.external_api_service import ExternalAPIService
from app.extensions import api

logger = logging.getLogger(__name__)

# Create namespace with /v1 prefix
external_ns = api.namespace('v1/external', description='External API integrations')

# Define response models
currency_response = api.model('CurrencyResponse', {
    'base': fields.String(),
    'rates': fields.Raw(),
    'timestamp': fields.String(),
    'status': fields.String()
})

weather_response = api.model('WeatherResponse', {
    'location': fields.String(),
    'temperature': fields.Float(),
    'condition': fields.String(),
    'status': fields.String()
})

cost_response = api.model('CostResponse', {
    'governorate': fields.String(),
    'avg_rent': fields.Float(),
    'avg_food': fields.Float(),
    'total_monthly': fields.Float(),
    'status': fields.String()
})


@external_ns.route('/currency')
class CurrencyExchange(Resource):
    @external_ns.doc('get_currency_rates')
    @external_ns.param('base', 'Base currency', default='TND')
    @external_ns.param('targets', 'Target currencies comma-separated', default='USD,EUR,GBP')
    @external_ns.response(200, 'Success', currency_response)
    @external_ns.response(400, 'Error')
    def get(self):
        """Get real-time currency exchange rates"""
        try:
            base = request.args.get('base', 'TND').upper()
            targets = request.args.get('targets', 'USD,EUR,GBP,SAR,AED').split(',')
            targets = [t.strip().upper() for t in targets]

            result = ExternalAPIService.get_exchange_rates(base, targets)
            status_code = 200 if result.get('status') == 'success' else 400
            return result, status_code
        except Exception as e:
            logger.error(f"Currency error: {str(e)}")
            return {'status': 'error', 'message': str(e)}, 500


@external_ns.route('/currency/trust-equivalent')
class TrustScoreCurrencyValue(Resource):
    @external_ns.doc('get_trust_score_value')
    @external_ns.response(200, 'Success')
    def get(self):
        """Get monetary equivalent of trust scores"""
        try:
            result = ExternalAPIService.get_trust_score_currency_value()
            return result, 200
        except Exception as e:
            logger.error(f"Trust value error: {str(e)}")
            return {'status': 'error', 'message': str(e)}, 500


@external_ns.route('/weather')
class Weather(Resource):
    @external_ns.doc('get_weather')
    @external_ns.param('location', 'City/Location name', required=True)
    @external_ns.response(200, 'Success', weather_response)
    @external_ns.response(404, 'Location not found')
    def get(self):
        """Get current weather for location"""
        try:
            location = request.args.get('location')
            if not location:
                external_ns.abort(400, "location parameter required")

            result = ExternalAPIService.get_weather(location)
            status_code = 200 if result.get('status') == 'success' else 400
            return result, status_code
        except Exception as e:
            logger.error(f"Weather error: {str(e)}")
            return {'status': 'error', 'message': str(e)}, 500


@external_ns.route('/living-cost')
class LivingCost(Resource):
    @external_ns.doc('get_living_cost')
    @external_ns.param('governorate', 'Governorate name')
    @external_ns.response(200, 'Success', cost_response)
    def get(self):
        """Get estimated living costs by governorate"""
        try:
            governorate = request.args.get('governorate')
            result = ExternalAPIService.get_living_costs(governorate)
            return result, 200
        except Exception as e:
            logger.error(f"Living cost error: {str(e)}")
            return {'status': 'error', 'message': str(e)}, 500


@external_ns.route('/countries')
class Countries(Resource):
    @external_ns.doc('get_countries')
    @external_ns.response(200, 'Success')
    def get(self):
        """Get countries data from REST Countries API"""
        try:
            result = ExternalAPIService.get_countries()
            return result, 200
        except Exception as e:
            logger.error(f"Countries error: {str(e)}")
            return {'status': 'error', 'message': str(e)}, 500
