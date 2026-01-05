import os
import csv
from datetime import datetime
from flask import abort
from app.services.agency_service import AgencyService

class OfferService:
    CSV_PATH = 'data/offers.csv'

    @staticmethod
    def load_csv():
        """Load all offers from CSV as List[dict]"""
        if not os.path.exists(OfferService.CSV_PATH):
            return []

        offers = []
        with open(OfferService.CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                offers.append({
                    'offer_id': row.get('offer_id', ''),
                    'agency_tax_id': row.get('agency_tax_id', ''),
                    'agency_name': row.get('agency_name', ''),
                    'type': row.get('type', ''),
                    'title': row.get('title', ''),
                    'price': float(row.get('price', 0)),
                    'currency': row.get('currency', 'DT'),
                    'from_city': row.get('from_city', ''),
                    'to_city': row.get('to_city', ''),
                    'depart_date': row.get('depart_date', ''),
                    'return_date': row.get('return_date', ''),
                    'seats_available': int(row.get('seats_available', 0)) if row.get('seats_available') else None,
                    'description': row.get('description', ''),
                    'created_at': row.get('created_at', '')
                })
        return offers

    @staticmethod
    def save_csv(offers):
        """Write all offers to CSV"""
        if not offers:
            return

        fieldnames = ['offer_id', 'agency_tax_id', 'agency_name', 'type', 'title', 'price', 'currency', 'from_city', 'to_city', 'depart_date', 'return_date', 'seats_available', 'description', 'created_at']

        with open(OfferService.CSV_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for offer in offers:
                writer.writerow({
                    'offer_id': offer['offer_id'],
                    'agency_tax_id': offer['agency_tax_id'],
                    'agency_name': offer.get('agency_name', ''),
                    'type': offer['type'],
                    'title': offer['title'],
                    'price': offer['price'],
                    'currency': offer['currency'],
                    'from_city': offer.get('from_city', ''),
                    'to_city': offer.get('to_city', ''),
                    'depart_date': offer.get('depart_date', ''),
                    'return_date': offer.get('return_date', ''),
                    'seats_available': offer.get('seats_available'),
                    'description': offer.get('description', ''),
                    'created_at': offer.get('created_at', datetime.utcnow().isoformat())
                })

    @staticmethod
    def add_offer(offer_data):
        # Validate agency
        agency = AgencyService.get_agency_by_tax_id(offer_data['agency_tax_id'])
        if not agency or agency['trust_score'] < 40:
            abort(400, f"Agency invalid (score: {agency.get('trust_score',0)})")

        offers = OfferService.load_csv()
        offer_id = f"O{len(offers)+1:04d}"

        # Complete offer dict
        offer = {
            'offer_id': offer_id,
            'agency_tax_id': offer_data['agency_tax_id'],
            'agency_name': agency['company_name'],
            'type': offer_data['type'],
            'title': offer_data['title'],
            'price': offer_data['price'],
            'currency': offer_data.get('currency', 'DT'),
            'from_city': offer_data.get('from_city', ''),
            'to_city': offer_data.get('to_city', ''),
            'depart_date': offer_data.get('depart_date', ''),
            'return_date': offer_data.get('return_date', ''),
            'seats_available': offer_data.get('seats_available'),
            'description': offer_data.get('description', ''),
            'created_at': datetime.utcnow().isoformat()
        }

        offers.append(offer)
        OfferService.save_csv(offers)
        return offer

    @staticmethod
    def get_offers(filters=None):
        offers = OfferService.load_csv()
        if filters:
            # from_city, type=flight, price_lt=300
            if 'from_city' in filters:
                offers = [o for o in offers if o.get('from_city') == filters['from_city']]
            if 'type' in filters:
                offers = [o for o in offers if o.get('type') == filters['type']]
            if 'price_lt' in filters:
                offers = [o for o in offers if o.get('price', 0) < float(filters['price_lt'])]
        return sorted(offers, key=lambda x: x['price'])

    @staticmethod
    def get_offer(offer_id):
        for o in OfferService.load_csv():
            if o['offer_id'] == offer_id:
                return o
        raise ValueError("Not found")

    @staticmethod
    def update_offer(offer_id, data):
        offers = OfferService.load_csv()
        for o in offers:
            if o['offer_id'] == offer_id:
                o.update(data)
                OfferService.save_csv(offers)
                return o
        raise ValueError("Not found")

    @staticmethod
    def delete_offer(offer_id):
        offers = [o for o in OfferService.load_csv() if o['offer_id'] != offer_id]
        OfferService.save_csv(offers)
