from flask import Blueprint, request, abort
from app.services.agency_service import AgencyService

agencies_bp = Blueprint('agencies', __name__)

@agencies_bp.route('/agencies', methods=['GET'])
def get_agencies():
    agencies = AgencyService.get_agencies_sorted_by_trust()
    return {
        'data': agencies,
        'total': len(agencies)
    }

@agencies_bp.route('/agencies', methods=['POST'])
def create_agency():
    data = request.get_json()
    if not data:
        return {"error": "JSON payload required"}, 400

    try:
        result = AgencyService.add_agency(data)
        return result, 201
    except Exception as e:
        return {"error": str(e)}, 400

@agencies_bp.route('/agencies/<int:id>', methods=['GET'])
def get_agency(id):
    agencies = AgencyService.get_agencies_sorted_by_trust()
    if not (1 <= id <= len(agencies)):
        return {"error": f"Agency #{id} not found"}, 404

    return agencies[id-1]

@agencies_bp.route('/agencies/<tax_id>', methods=['GET'])
def get_agency_by_tax_id(tax_id):
    agencies = AgencyService.load_csv()
    agency = next((a for a in agencies if a['tax_id'] == tax_id), None)
    if not agency:
        return {"error": "Agency not found"}, 404

    return agency

@agencies_bp.route('/agencies/search', methods=['GET'])
def search_agencies():
    governorate = request.args.get('governorate')
    min_trust = request.args.get('min_trust', type=int)

    agencies = AgencyService.get_agencies_sorted_by_trust()

    filtered = agencies
    if governorate:
        filtered = [a for a in filtered if a.get('governorate', '').lower() == governorate.lower()]
    if min_trust:
        filtered = [a for a in filtered if a.get('trust_score', 0) >= min_trust]

    return {
        'items': filtered,
        'total': len(filtered),
        'filters': {
            'governorate': governorate,
            'min_trust': min_trust
        }
    }

@agencies_bp.route('/agencies/stats', methods=['GET'])
def get_agency_stats():
    agencies = AgencyService.load_csv()

    # Governorate stats
    stats = {}
    for agency in agencies:
        gov = agency.get('governorate', 'Unknown')
        stats[gov] = stats.get(gov, 0) + 1

    # Calculations
    total = len(agencies)
    avg_trust = sum(float(a.get('trust_score', 50)) for a in agencies) / total if total > 0 else 0

    return {
        'stats': stats,
        'total': total,
        'avg_trust': round(avg_trust, 1),
        'top_governorate': max(stats.items(), key=lambda x: x[1], default=('None', 0))
    }

@agencies_bp.route('/v1/agencies', methods=['GET'])
def get_agencies_v1():
    agencies = AgencyService.get_agencies_sorted_by_trust()
    return {
        'data': agencies,
        'total': len(agencies)
    }

@agencies_bp.route('/v1/verify-agency', methods=['POST'])
def verify_agency():
    data = request.get_json()
    if not data:
        return {"error": "JSON payload required"}, 400

    try:
        result = AgencyService.add_agency(data)
        return {
            'trust_score': result['trust_score'],
            'fraud_risk': result['fraud_risk'],
            'analysis': result['analysis']
        }, 201
    except Exception as e:
        return {"error": str(e)}, 400

@agencies_bp.route('/v1/agencies/<tax_id>', methods=['PATCH'])
def update_agency_v1(tax_id):
    data = request.get_json()
    if not data:
        return {"error": "JSON payload required"}, 400

    try:
        result = AgencyService.update_agency(tax_id, data)
        return result, 200
    except Exception as e:
        return {"error": str(e)}, 400

@agencies_bp.route('/verify-agency/<tax_id>', methods=['PATCH'])
def update_verify_agency(tax_id):
    data = request.get_json()
    if not data:
        return {"error": "JSON payload required"}, 400

    try:
        result = AgencyService.update_agency(tax_id, data)
        return result, 200
    except Exception as e:
        return {"error": str(e)}, 400
