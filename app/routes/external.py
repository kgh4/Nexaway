# -*- coding: utf-8 -*-
"""
External API Integration Routes
Exposes 3 external API integrations: ExchangeRate, OpenWeather, REST Countries
"""

from flask import Blueprint, jsonify, request
from app.services.external_api_service import ExternalAPIService
from app.models import Agency
import logging

logger = logging.getLogger(__name__)

# Create blueprints
external_bp = Blueprint('external', __name__, url_prefix='/v1/external')
# Shortcut blueprints for convenience (without v1/external prefix)
living_cost_shortcut = Blueprint('living_cost_shortcut', __name__)


# ========== EXCHANGE RATE API ==========

@external_bp.route('/currency', methods=['GET'])
def get_currency_rates():
    """
    GET /v1/external/currency
    Get real-time currency exchange rates (TND base)
    
    Query Params:
        base: Base currency (default: TND)
        targets: Comma-separated target currencies (default: USD,EUR,GBP,SAR,AED)
    
    Example:
        GET /v1/external/currency
        GET /v1/external/currency?base=TND&targets=USD,EUR
    
    Response:
        {
            'base': 'TND',
            'rates': {'USD': 0.32, 'EUR': 0.30, ...},
            'timestamp': '2026-01-15T10:30:00Z',
            'source': 'exchangerate-api.com',
            'status': 'success'
        }
    """
    try:
        base = request.args.get('base', 'TND').upper()
        targets = request.args.get('targets', 'USD,EUR,GBP,SAR,AED').split(',')
        targets = [t.strip().upper() for t in targets]
        
        result = ExternalAPIService.get_exchange_rates(base, targets)
        return jsonify(result), 200 if result.get('status') == 'success' else 400
    
    except Exception as e:
        logger.error(f"Currency endpoint error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@external_bp.route('/currency/trust-equivalent', methods=['GET'])
def get_trust_score_currency_value():
    """
    GET /v1/external/currency/trust-equivalent
    Convert agency trust score to currency equivalent
    
    Query Params:
        agency_id: Agency ID (e.g., A-001)
        from_currency: Source currency (default: TND)
        to_currency: Target currency (default: USD)
    
    Example:
        GET /v1/external/currency/trust-equivalent?agency_id=A-001&to_currency=USD
    
    Response:
        {
            'agency_id': 'A-001',
            'trust_score': 80,
            'equivalent_value': 25.60,
            'currency': 'USD',
            'status': 'success'
        }
    """
    try:
        agency_id = request.args.get('agency_id')
        if not agency_id:
            return jsonify({'status': 'error', 'message': 'agency_id required'}), 400
        
        agency = Agency.query.filter_by(agency_id=agency_id).first()
        if not agency:
            return jsonify({'status': 'error', 'message': 'Agency not found'}), 404
        
        from_curr = request.args.get('from_currency', 'TND')
        to_curr = request.args.get('to_currency', 'USD')
        
        result = ExternalAPIService.get_trust_score_currency_equivalent(
            agency.trust_score, from_curr, to_curr
        )
        result['agency_id'] = agency_id
        result['agency_name'] = agency.company_name
        
        return jsonify(result), 200 if result.get('status') == 'success' else 400
    
    except Exception as e:
        logger.error(f"Trust equivalent error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ========== OPENWEATHER API ==========

@external_bp.route('/weather/<city>', methods=['GET'])
def get_city_weather(city):
    """
    GET /v1/external/weather/<city>
    Get weather data for a destination city
    
    Params:
        city: City name (e.g., 'Djerba', 'Cairo')
    
    Example:
        GET /v1/external/weather/Djerba
        GET /v1/external/weather/Cairo
    
    Response:
        {
            'city': 'Djerba',
            'country': 'TN',
            'temperature': 22.5,
            'condition': 'Partly cloudy',
            'humidity': 65,
            'travel_friendly': True,
            'source': 'openweathermap.org',
            'status': 'success'
        }
    """
    try:
        result = ExternalAPIService.get_destination_weather(city)
        return jsonify(result), 200 if result.get('status') == 'success' else 404
    
    except Exception as e:
        logger.error(f"Weather endpoint error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@external_bp.route('/weather/suitability', methods=['POST'])
def get_weather_suitability():
    """
    POST /v1/external/weather/suitability
    Get weather suitability for multiple destinations
    
    Request Body:
        {
            'cities': ['Cairo', 'Djerba', 'Tunis']
        }
    
    Example:
        POST /v1/external/weather/suitability
        {"cities": ["Cairo", "Djerba", "Dubai"]}
    
    Response:
        {
            'destinations': [
                {'city': 'Cairo', 'temp': 28, 'suitable': True, 'reason': 'Ideal weather'},
                {'city': 'Djerba', 'temp': 22, 'suitable': True, 'reason': 'Ideal weather'},
                ...
            ],
            'best_destination': 'Cairo',
            'timestamp': '2026-01-15T10:30:00Z',
            'status': 'success'
        }
    """
    try:
        data = request.get_json() or {}
        cities = data.get('cities', [])
        
        if not cities:
            return jsonify({'status': 'error', 'message': 'cities array required'}), 400
        
        result = ExternalAPIService.get_weather_suitability_for_tourism(cities)
        return jsonify(result), 200 if result.get('status') == 'success' else 400
    
    except Exception as e:
        logger.error(f"Weather suitability error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ========== REST COUNTRIES API ==========

@external_bp.route('/country/<country>', methods=['GET'])
def get_country_info(country):
    """
    GET /v1/external/country/<country>
    Get comprehensive country information for travel planning
    
    Params:
        country: Country code (e.g., 'EG', 'SA') or name (e.g., 'Egypt')
    
    Example:
        GET /v1/external/country/EG
        GET /v1/external/country/Egypt
        GET /v1/external/country/SA
    
    Response:
        {
            'name': 'Egypt',
            'code': 'EG',
            'capital': 'Cairo',
            'region': 'Africa',
            'languages': ['Arabic'],
            'currencies': ['EGP'],
            'population': 102334404,
            'timezone': 'Africa/Cairo',
            'travel_info': {
                'direct_flights_from_tunisia': True,
                'visa_required': True,
                'popular_for': 'Historical & Cultural'
            },
            'source': 'restcountries.com',
            'status': 'success'
        }
    """
    try:
        result = ExternalAPIService.get_country_info(country)
        return jsonify(result), 200 if result.get('status') == 'success' else 404
    
    except Exception as e:
        logger.error(f"Country info error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@external_bp.route('/destinations', methods=['POST'])
def get_destinations_info():
    """
    POST /v1/external/destinations
    Get comprehensive info for multiple travel destinations
    
    Request Body:
        {
            'destinations': ['EG', 'SA', 'AE', 'FR']
        }
    
    Example:
        POST /v1/external/destinations
        {"destinations": ["EG", "SA", "AE"]}
    
    Response:
        {
            'destinations': [
                {
                    'name': 'Egypt',
                    'capital': 'Cairo',
                    'region': 'Africa',
                    'languages': ['Arabic'],
                    'currencies': ['EGP'],
                    'travel_friendly': True
                },
                ...
            ],
            'count': 3,
            'timestamp': '2026-01-15T10:30:00Z',
            'status': 'success'
        }
    """
    try:
        data = request.get_json() or {}
        destinations = data.get('destinations', [])
        
        if not destinations:
            return jsonify({'status': 'error', 'message': 'destinations array required'}), 400
        
        result = ExternalAPIService.get_travel_destinations(destinations)
        return jsonify(result), 200 if result.get('status') == 'success' else 400
    
    except Exception as e:
        logger.error(f"Destinations error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@external_bp.route('/health', methods=['GET'])
def external_api_health():
    """
    GET /v1/external/health
    Check health of external API integrations
    
    Response:
        {
            'status': 'ok',
            'integrations': {
                'exchangerate': {'status': 'available', 'source': 'exchangerate-api.com'},
                'weather': {'status': 'available', 'source': 'openweathermap.org'},
                'countries': {'status': 'available', 'source': 'restcountries.com'},
                'living_cost': {'status': 'available', 'source': 'RapidAPI'}
            },
            'timestamp': '2026-01-15T10:30:00Z'
        }
    """
    from datetime import datetime
    
    # Quick test of each API
    status = 'ok'
    integrations = {}
    
    # Test ExchangeRate API
    try:
        rates = ExternalAPIService.get_exchange_rates('TND', ['USD'])
        integrations['exchangerate'] = {
            'status': 'available' if rates.get('status') == 'success' else 'error',
            'source': 'exchangerate-api.com'
        }
    except:
        integrations['exchangerate'] = {'status': 'error', 'source': 'exchangerate-api.com'}
        status = 'degraded'
    
    # Test Weather API
    try:
        weather = ExternalAPIService.get_destination_weather('Tunis')
        integrations['weather'] = {
            'status': 'available' if weather.get('status') == 'success' else 'error',
            'source': 'openweathermap.org'
        }
    except:
        integrations['weather'] = {'status': 'error', 'source': 'openweathermap.org'}
        status = 'degraded'
    
    # Test Countries API
    try:
        country = ExternalAPIService.get_country_info('EG')
        integrations['countries'] = {
            'status': 'available' if country.get('status') == 'success' else 'error',
            'source': 'restcountries.com'
        }
    except:
        integrations['countries'] = {'status': 'error', 'source': 'restcountries.com'}
        status = 'degraded'
    
    # Test Living Cost API
    try:
        cost = ExternalAPIService.get_city_living_cost('Cairo')
        integrations['living_cost'] = {
            'status': 'available' if cost.get('status') == 'success' else 'error',
            'source': 'RapidAPI (cities-cost-of-living)'
        }
    except:
        integrations['living_cost'] = {'status': 'error', 'source': 'RapidAPI'}
        status = 'degraded'
    
    return jsonify({
        'status': status,
        'integrations': integrations,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 200


# ========== COST OF LIVING API ==========

@external_bp.route('/living-cost/<city>', methods=['GET'])
def get_living_cost(city):
    """
    GET /v1/external/living-cost/{city}
    Get detailed cost of living breakdown for a city
    
    Query Params:
        country (optional) - Country name to disambiguate city
    
    Example:
        GET /v1/external/living-cost/Cairo
        GET /v1/external/living-cost/Tunis?country=Tunisia
    
    Response:
        {
            'city': 'Cairo',
            'country': 'Egypt',
            'monthly_cost_usd': 1200,
            'monthly_cost_tnd': 414,
            'monthly_cost_formatted': '$1,200 USD / 414 TND',
            'breakdown': [
                {
                    'category': 'Groceries',
                    'price_usd': 250,
                    'price_tnd': 86,
                    'description': 'Basic groceries...',
                    'unit': 'monthly'
                },
                ...
            ],
            'breakdown_count': 15,
            'affordability': 'Moderate',
            'tnd_exchange_rate': 0.345,
            'source': 'RapidAPI',
            'status': 'success'
        }
    """
    try:
        country = request.args.get('country', '')
        result = ExternalAPIService.get_city_living_cost(city, country)
        return jsonify(result), 200 if result.get('status') == 'success' else 400
    
    except Exception as e:
        logger.error(f"Living cost endpoint error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@external_bp.route('/travel-budget', methods=['POST'])
def get_travel_budget():
    """
    POST /v1/external/travel-budget
    Estimate total travel budget for multiple destinations
    
    Request Body:
        {
            'cities': ['Cairo', 'Giza', 'Luxor'],
            'trip_duration_days': 7
        }
    
    Example:
        POST /v1/external/travel-budget
        {
            "cities": ["Cairo", "Dubai", "Istanbul"],
            "trip_duration_days": 10
        }
    
    Response:
        {
            'trip_duration_days': 10,
            'cities': [
                {
                    'city': 'Cairo',
                    'monthly_cost_usd': 1200,
                    'daily_cost_usd': 40,
                    'trip_cost_usd': 400,
                    'trip_cost_tnd': 1380,
                    'affordability': 'Budget-Friendly'
                },
                ...
            ],
            'total_budget_usd': 1200,
            'total_budget_tnd': 4140,
            'total_budget_formatted': '$1,200 USD / 4,140 TND',
            'cheapest_city': 'Cairo',
            'most_expensive_city': 'Dubai',
            'average_daily_cost_usd': 40,
            'cities_count': 3,
            'status': 'success'
        }
    """
    try:
        data = request.get_json() or {}
        cities = data.get('cities', [])
        duration = data.get('trip_duration_days', 7)
        
        if not cities:
            return jsonify({'status': 'error', 'message': 'cities array required'}), 400
        
        result = ExternalAPIService.get_travel_budget_estimate(cities, duration)
        return jsonify(result), 200 if result.get('status') == 'success' else 400
    
    except Exception as e:
        logger.error(f"Travel budget error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ============================================================
# SHORTCUT ROUTES (convenience paths without /v1/external prefix)
# ============================================================

@living_cost_shortcut.route('/living-cost/<city>', methods=['GET'])
def get_living_cost_shortcut(city):
    """
    Shortcut: GET /living-cost/{city}
    Convenience alias for GET /v1/external/living-cost/{city}
    """
    country = request.args.get('country', '')
    result = ExternalAPIService.get_city_living_cost(city, country)
    return jsonify(result), 200 if result.get('status') == 'success' else 400


@living_cost_shortcut.route('/travel-budget', methods=['POST'])
def get_travel_budget_shortcut():
    """
    Shortcut: POST /travel-budget
    Convenience alias for POST /v1/external/travel-budget
    """
    try:
        data = request.get_json() or {}
        cities = data.get('cities', [])
        duration = data.get('trip_duration_days', 7)
        
        if not cities:
            return jsonify({'status': 'error', 'message': 'cities array required'}), 400
        
        result = ExternalAPIService.get_travel_budget_estimate(cities, duration)
        return jsonify(result), 200 if result.get('status') == 'success' else 400
    
    except Exception as e:
        logger.error(f"Travel budget shortcut error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500