from flask_restx import Namespace, Resource, abort, fields
from flask import request
from app.services.agency_service import AgencyService

agencies_bp = Namespace('agencies', description='Tunisian Travel Agencies operations')

@agencies_bp.route('')
class AgencyList(Resource):
    @agencies_bp.doc(description='Get all agencies sorted by trust_score DESC')
    def get(self):
        agencies = AgencyService.get_agencies_sorted_by_trust()
        return {
            'data': agencies,
            'total': len(agencies)
        }

    @agencies_bp.doc(description='Create new agency with AI trust scoring')
    def post(self):
        data = request.get_json()
        if not data:
            abort(400, "JSON payload required")

        try:
            result = AgencyService.add_agency(data)
            return result, 201
        except Exception as e:
            abort(400, str(e))

@agencies_bp.route('/<int:id>')
class AgencyDetail(Resource):
    @agencies_bp.doc(description='Get single agency by ID')
    @agencies_bp.doc(params={'id': 'Agency ID'})
    def get(self, id):
        agencies = AgencyService.get_agencies_sorted_by_trust()
        if not (1 <= id <= len(agencies)):
            abort(404, f"Agency #{id} not found")

        return agencies[id-1]

@agencies_bp.route('/search')
class AgencySearch(Resource):
    @agencies_bp.doc(description='Search agencies by governorate or min trust score')
    def get(self):
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

@agencies_bp.route('/stats')
class AgencyStats(Resource):
    @agencies_bp.doc(description='Get analytics: governorates, total, avg trust')
    def get(self):
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
