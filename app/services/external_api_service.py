# -*- coding: utf-8 -*-
"""
External API Integration Service
Integrates with 3 winners: ExchangeRate-API, OpenWeather-API, REST Countries API
"""

import requests
from datetime import datetime, timedelta
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

# Cache timeouts (seconds)
EXCHANGE_RATE_CACHE = 3600  # 1 hour
WEATHER_CACHE = 1800  # 30 minutes
COUNTRIES_CACHE = 86400  # 24 hours
LIVING_COST_CACHE = 86400  # 24 hours (costs don't change often)

# RapidAPI Configuration
RAPIDAPI_KEY = "85ba043483msh703332b5ab7aa2ep118751jsn6646caf2181e"
LIVING_COST_BASE = "https://cities-cost-of-living1.p.rapidapi.com"


class ExternalAPIService:
    """
    Unified service for 3 external APIs:
    1. ExchangeRate-API: Real-time currency conversion
    2. OpenWeather-API: Weather data for travel planning
    3. REST Countries-API: Country information (visa, capital, etc)
    """
    
    # API Endpoints
    EXCHANGERATE_BASE = "https://api.exchangerate-api.com/v4/latest"
    OPENWEATHER_BASE = "https://api.openweathermap.org/data/2.5/weather"
    COUNTRIES_BASE = "https://restcountries.com/v3.1"
    
    # Cache storage
    _cache = {}
    
    @classmethod
    def _get_cached(cls, key):
        """Get value from cache if not expired"""
        if key in cls._cache:
            value, expiry = cls._cache[key]
            if datetime.utcnow() < expiry:
                return value
            else:
                del cls._cache[key]
        return None
    
    @classmethod
    def _set_cache(cls, key, value, ttl):
        """Store value in cache with TTL"""
        cls._cache[key] = (value, datetime.utcnow() + timedelta(seconds=ttl))
    
    # ========== 1. EXCHANGE RATE API ==========
    
    @classmethod
    def get_exchange_rates(cls, base_currency='TND', target_currencies=None):
        """
        Get real-time exchange rates from ExchangeRate-API
        
        Args:
            base_currency: Base currency code (default: TND for Tunisia)
            target_currencies: List of target currencies (default: USD, EUR, GBP)
        
        Returns:
            dict: {
                'base': 'TND',
                'timestamp': '2026-01-15T10:30:00Z',
                'rates': {'USD': 0.32, 'EUR': 0.30, ...},
                'source': 'exchangerate-api.com'
            }
        """
        if target_currencies is None:
            target_currencies = ['USD', 'EUR', 'GBP', 'SAR', 'AED']
        
        cache_key = f"exchange_rate_{base_currency}"
        cached = cls._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            url = f"{cls.EXCHANGERATE_BASE}/{base_currency}"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            # Filter to requested currencies
            filtered_rates = {
                k: v for k, v in data.get('rates', {}).items() 
                if k in target_currencies
            }
            
            result = {
                'base': base_currency,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'rates': filtered_rates,
                'source': 'exchangerate-api.com',
                'status': 'success'
            }
            
            cls._set_cache(cache_key, result, EXCHANGE_RATE_CACHE)
            return result
            
        except requests.RequestException as e:
            logger.error(f"ExchangeRate API Error: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'source': 'exchangerate-api.com'
            }
    
    @classmethod
    def get_trust_score_currency_equivalent(cls, trust_score, from_currency='TND', to_currency='USD'):
        """
        Convert trust score to currency equivalent
        
        Example: trust_score of 80 in TND → equivalent USD value
        
        Args:
            trust_score: Agency trust score (0-100)
            from_currency: Source currency (default: TND)
            to_currency: Target currency (default: USD)
        
        Returns:
            dict: {
                'trust_score': 80,
                'equivalent_value': 25.60,
                'currency': 'USD',
                'description': 'Trust score converted to monetary equivalent'
            }
        """
        try:
            rates = cls.get_exchange_rates(from_currency, [to_currency])
            
            if rates.get('status') == 'error':
                return rates
            
            # Formula: trust_score * base_amount * exchange_rate
            base_amount = 100  # $100 baseline per trust point
            rate = rates['rates'].get(to_currency, 1)
            equivalent = (trust_score / 100) * base_amount * (1 / rate)
            
            return {
                'trust_score': trust_score,
                'equivalent_value': round(equivalent, 2),
                'currency': to_currency,
                'exchange_rate': rate,
                'description': f'Trust score {trust_score}/100 ≈ {to_currency} {equivalent:.2f}',
                'status': 'success'
            }
        except Exception as e:
            logger.error(f"Trust score conversion error: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    # ========== 2. OPENWEATHER API ==========
    
    @classmethod
    def get_destination_weather(cls, city, api_key=None):
        """
        Get weather data for travel destinations
        
        Args:
            city: City name (e.g., 'Djerba', 'Tunis', 'Cairo')
            api_key: OpenWeather API key (optional, defaults to public data)
        
        Returns:
            dict: {
                'city': 'Djerba',
                'country': 'TN',
                'temperature': 22.5,
                'feels_like': 21.0,
                'humidity': 65,
                'condition': 'Partly cloudy',
                'wind_speed': 5.2,
                'travel_friendly': True,
                'source': 'openweathermap.org'
            }
        """
        cache_key = f"weather_{city.lower()}"
        cached = cls._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            # Using free API endpoint (limited but no key required for basic data)
            params = {
                'q': city,
                'units': 'metric',
                'appid': api_key or 'demo'  # Demo key for testing
            }
            
            response = requests.get(cls.OPENWEATHER_BASE, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            # Determine if weather is travel-friendly (temp 15-30°C, no severe weather)
            temp = data.get('main', {}).get('temp', 0)
            weather_id = data.get('weather', [{}])[0].get('id', 0)
            travel_friendly = (15 <= temp <= 30) and (weather_id < 700)
            
            result = {
                'city': data.get('name', city),
                'country': data.get('sys', {}).get('country', ''),
                'temperature': data.get('main', {}).get('temp'),
                'feels_like': data.get('main', {}).get('feels_like'),
                'humidity': data.get('main', {}).get('humidity'),
                'condition': data.get('weather', [{}])[0].get('main', 'Unknown'),
                'description': data.get('weather', [{}])[0].get('description', ''),
                'wind_speed': data.get('wind', {}).get('speed'),
                'travel_friendly': travel_friendly,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'source': 'openweathermap.org',
                'status': 'success'
            }
            
            cls._set_cache(cache_key, result, WEATHER_CACHE)
            return result
            
        except requests.RequestException as e:
            logger.error(f"Weather API Error: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'source': 'openweathermap.org'
            }
    
    @classmethod
    def get_weather_suitability_for_tourism(cls, cities_list):
        """
        Get weather suitability for multiple tourism destinations
        
        Args:
            cities_list: List of city names
        
        Returns:
            dict: {
                'timestamp': '2026-01-15T10:30:00Z',
                'destinations': [
                    {'city': 'Djerba', 'temp': 22, 'suitable': True, 'reason': 'Ideal weather'},
                    ...
                ],
                'best_destination': 'Djerba'
            }
        """
        destinations = []
        
        for city in cities_list:
            weather = cls.get_destination_weather(city)
            if weather.get('status') == 'success':
                destinations.append({
                    'city': weather['city'],
                    'temperature': weather['temperature'],
                    'condition': weather['condition'],
                    'suitable': weather['travel_friendly'],
                    'reason': 'Ideal weather for tourism' if weather['travel_friendly'] else 'Poor weather conditions'
                })
        
        # Find best destination
        best = max(
            (d for d in destinations if d['suitable']), 
            key=lambda x: x['temperature'], 
            default=None
        )
        
        return {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'destinations': destinations,
            'best_destination': best['city'] if best else None,
            'status': 'success' if destinations else 'error'
        }
    
    # ========== 3. REST COUNTRIES API ==========
    
    @classmethod
    def get_country_info(cls, country_code_or_name):
        """
        Get comprehensive country information for travel planning
        
        Args:
            country_code_or_name: ISO 3166-1 alpha-2 code (e.g., 'EG', 'SA') or country name
        
        Returns:
            dict: {
                'name': 'Egypt',
                'code': 'EG',
                'capital': 'Cairo',
                'region': 'Africa',
                'languages': ['Arabic'],
                'currencies': ['EGP'],
                'population': 102334404,
                'timezone': 'Africa/Cairo',
                'travel_info': {...}
            }
        """
        cache_key = f"country_{country_code_or_name.lower()}"
        cached = cls._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            # Try by alpha code first, then by name
            if len(country_code_or_name) == 2:
                url = f"{cls.COUNTRIES_BASE}/alpha/{country_code_or_name.upper()}"
            else:
                url = f"{cls.COUNTRIES_BASE}/name/{country_code_or_name}"
            
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            if isinstance(data, list):
                data = data[0]
            
            result = {
                'name': data.get('name', {}).get('common', ''),
                'official_name': data.get('name', {}).get('official', ''),
                'code': data.get('cca2', ''),
                'code3': data.get('cca3', ''),
                'capital': ', '.join(data.get('capital', [])) if data.get('capital') else 'N/A',
                'region': data.get('region', ''),
                'subregion': data.get('subregion', ''),
                'languages': list(data.get('languages', {}).values()) if data.get('languages') else [],
                'currencies': list(data.get('currencies', {}).keys()) if data.get('currencies') else [],
                'population': data.get('population'),
                'area': data.get('area'),
                'timezone': data.get('timezones', ['UTC'])[0] if data.get('timezones') else 'UTC',
                'borders': data.get('borders', []),
                'travel_info': {
                    'direct_flights_from_tunisia': country_code_or_name.upper() in ['EG', 'FR', 'IT', 'ES', 'TR'],
                    'visa_required': True,  # Most require visas
                    'popular_for': _get_travel_type(country_code_or_name)
                },
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'source': 'restcountries.com',
                'status': 'success'
            }
            
            cls._set_cache(cache_key, result, COUNTRIES_CACHE)
            return result
            
        except requests.RequestException as e:
            logger.error(f"Countries API Error: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'source': 'restcountries.com'
            }
    
    @classmethod
    def get_travel_destinations(cls, destinations_list):
        """
        Get comprehensive info for multiple travel destinations
        
        Args:
            destinations_list: List of country codes or names
        
        Returns:
            dict: {
                'destinations': [
                    {
                        'name': 'Egypt',
                        'capital': 'Cairo',
                        'languages': ['Arabic'],
                        'currencies': ['EGP'],
                        'travel_friendly': True
                    },
                    ...
                ],
                'timestamp': '2026-01-15T10:30:00Z'
            }
        """
        destinations = []
        
        for dest in destinations_list:
            info = cls.get_country_info(dest)
            if info.get('status') == 'success':
                destinations.append({
                    'name': info['name'],
                    'capital': info['capital'],
                    'region': info['region'],
                    'languages': info['languages'],
                    'currencies': info['currencies'],
                    'population': info['population'],
                    'travel_friendly': True
                })
        
        return {
            'destinations': destinations,
            'count': len(destinations),
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'status': 'success' if destinations else 'error'
        }
    
    # ========== 4. COST OF LIVING API (RapidAPI) ==========
    
    @classmethod
    def get_city_living_cost(cls, city, country=''):
        """
        Get detailed cost of living breakdown for a city
        
        Args:
            city: City name (e.g., 'Cairo', 'Riyadh', 'Tunis')
            country: Country name (optional, helps disambiguate)
        
        Returns:
            dict: {
                'city': 'Cairo',
                'country': 'Egypt',
                'monthly_cost_usd': 1200,
                'monthly_cost_tnd': 414,
                'breakdown': [
                    {'category': 'Groceries', 'price_usd': 250, 'price_tnd': 86},
                    {'category': 'Restaurants', 'price_usd': 300, 'price_tnd': 104},
                    ...
                ],
                'affordability': 'Moderate',
                'source': 'RapidAPI',
                'timestamp': '2026-01-15T10:30:00Z',
                'status': 'success'
            }
        """
        cache_key = f"living_cost_{city.lower()}_{country.lower()}"
        cached = cls._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            headers = {
                "X-RapidAPI-Key": RAPIDAPI_KEY,
                "X-RapidAPI-Host": "cities-cost-of-living1.p.rapidapi.com"
            }
            
            params = {
                "city": city,
                "country": country if country else ""
            }
            
            url = f"{LIVING_COST_BASE}/city-info"
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Get TND exchange rate
            rates = cls.get_exchange_rates('USD', ['TND'])
            tnd_rate = rates.get('rates', {}).get('TND', 1)
            
            # Calculate monthly cost
            monthly_cost_usd = data.get('summary', {}).get('cost_of_living', 0) or 0
            monthly_cost_tnd = round(monthly_cost_usd * tnd_rate, 2)
            
            # Process detailed breakdown
            items = data.get('items', [])
            breakdown = []
            
            for item in items:
                breakdown.append({
                    'category': item.get('title', 'Unknown'),
                    'price_usd': round(float(item.get('price', 0)) if item.get('price') else 0, 2),
                    'price_tnd': round(float(item.get('price', 0)) * tnd_rate if item.get('price') else 0, 2),
                    'description': item.get('content', ''),
                    'unit': item.get('unit', 'monthly')
                })
            
            # Determine affordability level
            affordability = 'Expensive' if monthly_cost_usd > 2000 else \
                           'Moderate' if monthly_cost_usd > 1000 else \
                           'Budget-Friendly'
            
            result = {
                'city': data.get('city_name', city),
                'country': data.get('country', country),
                'monthly_cost_usd': monthly_cost_usd,
                'monthly_cost_tnd': monthly_cost_tnd,
                'monthly_cost_formatted': f"${monthly_cost_usd:,.0f} USD / {monthly_cost_tnd:,.0f} TND",
                'breakdown': breakdown,
                'breakdown_count': len(breakdown),
                'affordability': affordability,
                'tnd_exchange_rate': tnd_rate,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'source': 'RapidAPI (cities-cost-of-living)',
                'status': 'success'
            }
            
            cls._set_cache(cache_key, result, LIVING_COST_CACHE)
            return result
            
        except requests.RequestException as e:
            logger.error(f"Living Cost API Error: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'source': 'RapidAPI'
            }
    
    @classmethod
    def get_travel_budget_estimate(cls, cities_list, trip_duration_days=7):
        """
        Estimate travel budget for multiple cities
        
        Args:
            cities_list: List of city names
            trip_duration_days: Number of days for trip (default: 7)
        
        Returns:
            dict: {
                'trip_duration_days': 7,
                'cities': [
                    {
                        'city': 'Cairo',
                        'daily_cost_usd': 40,
                        'daily_cost_tnd': 138,
                        'trip_cost_usd': 280,
                        'trip_cost_tnd': 966,
                        'affordability': 'Budget-Friendly'
                    },
                    ...
                ],
                'total_budget_usd': 560,
                'total_budget_tnd': 1932,
                'cheapest_city': 'Cairo',
                'most_expensive_city': 'Dubai',
                'average_daily_cost': 40,
                'timestamp': '2026-01-15T10:30:00Z',
                'status': 'success'
            }
        """
        cities_budget = []
        total_usd = 0
        total_tnd = 0
        
        for city in cities_list:
            cost_data = cls.get_city_living_cost(city)
            
            if cost_data.get('status') == 'success':
                monthly_usd = cost_data['monthly_cost_usd']
                monthly_tnd = cost_data['monthly_cost_tnd']
                
                # Calculate daily and trip costs
                daily_usd = round(monthly_usd / 30, 2)
                daily_tnd = round(monthly_tnd / 30, 2)
                trip_usd = round(daily_usd * trip_duration_days, 2)
                trip_tnd = round(daily_tnd * trip_duration_days, 2)
                
                cities_budget.append({
                    'city': cost_data['city'],
                    'monthly_cost_usd': monthly_usd,
                    'monthly_cost_tnd': monthly_tnd,
                    'daily_cost_usd': daily_usd,
                    'daily_cost_tnd': daily_tnd,
                    'trip_cost_usd': trip_usd,
                    'trip_cost_tnd': trip_tnd,
                    'affordability': cost_data['affordability']
                })
                
                total_usd += trip_usd
                total_tnd += trip_tnd
        
        # Sort by trip cost
        cities_budget.sort(key=lambda x: x['trip_cost_usd'])
        
        cheapest = cities_budget[0]['city'] if cities_budget else None
        most_expensive = cities_budget[-1]['city'] if cities_budget else None
        avg_daily = round(total_usd / (len(cities_budget) * trip_duration_days), 2) if cities_budget else 0
        
        return {
            'trip_duration_days': trip_duration_days,
            'cities': cities_budget,
            'total_budget_usd': round(total_usd, 2),
            'total_budget_tnd': round(total_tnd, 2),
            'total_budget_formatted': f"${total_usd:,.0f} USD / {total_tnd:,.0f} TND",
            'cheapest_city': cheapest,
            'most_expensive_city': most_expensive,
            'average_daily_cost_usd': avg_daily,
            'cities_count': len(cities_budget),
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'status': 'success' if cities_budget else 'error'
        }


def _get_travel_type(country_code):
    """Determine popular travel type for a country"""
    travel_types = {
        'EG': 'Historical & Cultural',
        'SA': 'Religious (Hajj/Umrah)',
        'AE': 'Luxury & Business',
        'FR': 'Cultural & Leisure',
        'IT': 'Historical & Beach',
        'ES': 'Beach & Cultural',
        'TR': 'Beach & Historical',
        'MA': 'Desert & Cultural',
        'LY': 'Desert & Cultural',
    }
    return travel_types.get(country_code.upper(), 'General Tourism')
