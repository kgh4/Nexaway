from flask_restx import Namespace, Resource, abort
from flask import request
import os
import csv

agencies_bp = Namespace('agencies', description='Tunisian Travel Agencies operations')

class AgencyLiveCSV(Resource):
    """Helper class - loads 41 agencies from CSV"""
    def get(self):
        csv_path = 'data/tunisia_agencies_real_dataset.csv'
        if not os.path.exists(csv_path):
            abort(404, message="CSV file not found at data/tunisia_agencies_real_dataset.csv")
        
        agencies = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, 1):
                agency = {
                    'id': i,
                    'tax_id': row.get('tax_id', ''),
                    'company_name': row.get('company_name', ''),
                    'official_name': row.get('official_name', ''),
                    'governorate': row.get('governorate', 'Tunis'),
                    'email': row.get('email', ''),
                    'phone': row.get('phone', ''),
                    'trust_score': int(float(row.get('trust_score', 50))),
                    'status': row.get('status', 'active'),
                    'source': 'csv_live'
                }
                agencies.append(agency)
        return {'items': agencies, 'total': len(agencies)}

@agencies_bp.route('')
class AgencyList(Resource):
    @agencies_bp.doc(description='Get all agencies with pagination')
    def get(self):
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        csv_data = AgencyLiveCSV().get()
        agencies = csv_data['items']
        total = csv_data['total']
        
        start = (page - 1) * page_size
        end = start + page_size
        paginated = agencies[start:end]
        
        return {
            'items': paginated,
            'total': total,
            'page': page,
            'page_size': page_size,
            'pages': (total + page_size - 1) // page_size
        }

@agencies_bp.route('/<int:id>')
class AgencyDetail(Resource):
    @agencies_bp.doc(description='Get single agency by ID (1-41)')
    @agencies_bp.doc(params={'id': 'Agency ID from 1 to 41'})
    def get(self, id):
        csv_data = AgencyLiveCSV().get()
        agencies = csv_data['items']
        total = csv_data['total']
        
        if not (1 <= id <= total):
            abort(404, f"Agency #{id} not found. Valid IDs: 1-{total}")
        
        agency = agencies[id-1]
        return agency

@agencies_bp.route('/search')
class AgencySearch(Resource):
    @agencies_bp.doc(description='Search agencies by governorate or min trust score')
    def get(self):
        governorate = request.args.get('governorate')
        min_trust = request.args.get('min_trust', type=int)
        
        csv_data = AgencyLiveCSV().get()
        agencies = csv_data['items']
        
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
        csv_data = AgencyLiveCSV().get()
        agencies = csv_data['items']
        
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

@agencies_bp.route('/live-csv')
class AgencyLiveCSVEndpoint(Resource):
    @agencies_bp.doc(description="Raw CSV data - 41 Tunisian agencies direct from file")
    def get(self):
        return AgencyLiveCSV().get
