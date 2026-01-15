import uuid
from datetime import datetime, date
from flask import abort
from app.extensions import db
from app.models import Offer
from app.services.agency_service import AgencyService

class OfferService:

    @staticmethod
    def get_offers(filters=None, page=1, limit=10, sort='price_asc'):
        """Get offers with filtering, pagination, and sorting"""
        query = Offer.query

        # Apply filters
        if filters:
            if 'type' in filters and filters['type']:
                query = query.filter(Offer.type == filters['type'])
            if 'domestic' in filters and filters['domestic'] is not None:
                domestic = filters['domestic'].lower() == 'true'
                query = query.filter(Offer.domestic == domestic)
            if 'segment' in filters and filters['segment']:
                query = query.filter(Offer.segment == filters['segment'])
            if 'pilgrimage_type' in filters and filters['pilgrimage_type']:
                query = query.filter(Offer.pilgrimage_type == filters['pilgrimage_type'])
            if 'from_city' in filters and filters['from_city']:
                query = query.filter(Offer.from_city == filters['from_city'])
            if 'to_city' in filters and filters['to_city']:
                query = query.filter(Offer.to_city == filters['to_city'])
            if 'min_price' in filters and filters['min_price']:
                query = query.filter(Offer.price >= float(filters['min_price']))

        # Apply sorting
        if sort == 'price_desc':
            query = query.order_by(Offer.price.desc())
        elif sort == 'date_from':
            query = query.order_by(Offer.date_from)
        else:
            query = query.order_by(Offer.price.asc())

        # Apply pagination
        offers = query.paginate(page=int(page), per_page=int(limit), error_out=False)

        return {
            'offers': [offer.to_dict() for offer in offers.items],
            'total': offers.total,
            'page': offers.page,
            'pages': offers.pages,
            'per_page': offers.per_page
        }

    @staticmethod
    def add_offer(offer_data):
        # Validate agency
        agency = AgencyService.get_agency_by_tax_id(offer_data['agency_id'])
        if not agency or agency['trust_score'] < 40:
            abort(400, f"Agency invalid (score: {agency.get('trust_score',0)})")

        # Generate offer_id
        offer_id = f"O-{uuid.uuid4()[:6].upper()}"

        offer = Offer(
            offer_id=offer_id,
            agency_id=offer_data['agency_id'],
            type=offer_data['type'],
            title=offer_data['title'],
            price=offer_data['price'],
            currency=offer_data.get('currency', 'TND'),
            from_city=offer_data.get('from_city'),
            to_city=offer_data.get('to_city'),
            date_from=offer_data.get('date_from'),
            date_to=offer_data.get('date_to'),
            seats_available=offer_data.get('seats_available'),
            segment=offer_data.get('segment'),
            pilgrimage_type=offer_data.get('pilgrimage_type'),
            domestic=offer_data.get('domestic', False),
            capacity=offer_data.get('capacity'),
            tags=offer_data.get('tags'),
            description=offer_data.get('description')
        )

        db.session.add(offer)
        db.session.commit()
        return offer.to_dict()

    @staticmethod
    def get_offer(offer_id):
        offer = Offer.query.filter_by(offer_id=offer_id).first()
        if not offer:
            abort(404, "Offer not found")
        return offer.to_dict()

    @staticmethod
    def update_offer(offer_id, data):
        offer = Offer.query.filter_by(offer_id=offer_id).first()
        if not offer:
            abort(404, "Offer not found")

        for key, value in data.items():
            if hasattr(offer, key):
                setattr(offer, key, value)

        db.session.commit()
        return offer.to_dict()

    @staticmethod
    def delete_offer(offer_id):
        offer = Offer.query.filter_by(offer_id=offer_id).first()
        if not offer:
            abort(404, "Offer not found")

        db.session.delete(offer)
        db.session.commit()

    @staticmethod
    def seed_sample_data():
        """Seed sample data if offers table is empty"""
        if Offer.query.count() > 0:
            return

        sample_offers = [
            {
                "offer_id": "O-000001",
                "type": "pilgrimage",
                "pilgrimage_type": "umrah",
                "from_city": "TUN",
                "to_city": "JED",
                "domestic": False,
                "title": "Umrah Gold 10D",
                "description": "Mecca+Medina 4*",
                "price": 3500,
                "currency": "TND",
                "date_from": "2026-02-10",
                "date_to": "2026-02-20",
                "agency_id": "TUN-123456",
                "capacity": 50,
                "tags": '["vip", "luxury"]'
            },
            {
                "offer_id": "O-000002",
                "type": "flight",
                "segment": "business",
                "from_city": "TUN",
                "to_city": "DJR",
                "domestic": True,
                "title": "Business TUN-DJR",
                "price": 450,
                "agency_id": "TUN-789012",
                "capacity": 100,
                "tags": '["business"]'
            },
            {
                "offer_id": "O-000003",
                "type": "hotel",
                "domestic": True,
                "to_city": "SFA",
                "title": "Sfax 4* Hotel",
                "price": 250,
                "currency": "TND",
                "agency_id": "TUN-345678",
                "capacity": 200,
                "tags": '["family"]'
            }
        ]

        for offer_data in sample_offers:
            # Convert date strings to date objects
            if 'date_from' in offer_data and offer_data['date_from']:
                offer_data['date_from'] = date.fromisoformat(offer_data['date_from'])
            if 'date_to' in offer_data and offer_data['date_to']:
                offer_data['date_to'] = date.fromisoformat(offer_data['date_to'])
            offer = Offer.from_dict(offer_data)
            db.session.add(offer)

        db.session.commit()
        print("Sample offers seeded!")
