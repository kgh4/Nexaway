# -*- coding: utf-8 -*-
from .extensions import db
from datetime import datetime

class Agency(db.Model):
    """Tunisian Travel Agency Model - Matches CSV exactly"""
    
    __tablename__ = 'agencies'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Core Business Data 
    tax_id = db.Column(db.String(8), unique=True, nullable=False, index=True)
    company_name = db.Column(db.String(200), nullable=False)
    official_name = db.Column(db.String(200))
    category = db.Column(db.String(1))  # A, B, C
    email = db.Column(db.String(150))
    phone = db.Column(db.String(50))
    address = db.Column(db.String(255))
    governorate = db.Column(db.String(80), index=True)  # Tunis, Sfax, etc.
    website = db.Column(db.String(200))
    sectors = db.Column(db.String(100))  # 'business,umrah,religious'
    tourism_license = db.Column(db.String(50))
    registry_number = db.Column(db.String(50))
    
    # Nexaway Features
    verification_status = db.Column(db.String(20), default='pending', index=True)
    trust_score = db.Column(db.Integer, default=50, index=True)
    status = db.Column(db.String(20), default='active', index=True)
    source = db.Column(db.String(20), default='csv')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for fast queries
    __table_args__ = (
        db.Index('ix_agencies_trust_governorate', 'trust_score', 'governorate'),
    )
    
    def to_dict(self):
        """JSON serialization"""
        return {
            'id': self.id,
            'tax_id': self.tax_id,
            'company_name': self.company_name,
            'official_name': self.official_name,
            'category': self.category,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'governorate': self.governorate,
            'website': self.website,
            'sectors': self.sectors,
            'tourism_license': self.tourism_license,
            'registry_number': self.registry_number,
            'verification_status': self.verification_status,
            'trust_score': self.trust_score,
            'status': self.status,
            'source': self.source,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create from dict (POST/PUT)"""
        return cls(**data)
    
    def __repr__(self):
        return f'<Agency {self.company_name} ({self.tax_id})>'


class Offer(db.Model):
    """Travel Offer Model"""

    __tablename__ = 'offers'

    id = db.Column(db.Integer, primary_key=True)
    offer_id = db.Column(db.String(20), unique=True, nullable=False, index=True)

    # Required fields
    agency_tax_id = db.Column(db.String(8), db.ForeignKey('agencies.tax_id'), nullable=False, index=True)
    type = db.Column(db.String(20), nullable=False)  # hotel, cruise, flight, package, pilgrimage, business
    title = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), nullable=False)  # DT, EUR, USD

    # Optional fields
    from_city = db.Column(db.String(10))
    to_city = db.Column(db.String(10))
    depart_date = db.Column(db.Date)
    return_date = db.Column(db.Date)
    seats_available = db.Column(db.Integer)
    description = db.Column(db.Text)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    agency = db.relationship('Agency', backref=db.backref('offers', lazy=True))

    def to_dict(self):
        """JSON serialization"""
        return {
            'id': self.id,
            'offer_id': self.offer_id,
            'agency_tax_id': self.agency_tax_id,
            'type': self.type,
            'title': self.title,
            'price': self.price,
            'currency': self.currency,
            'from_city': self.from_city,
            'to_city': self.to_city,
            'depart_date': self.depart_date.isoformat() if self.depart_date else None,
            'return_date': self.return_date.isoformat() if self.return_date else None,
            'seats_available': self.seats_available,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @classmethod
    def from_dict(cls, data):
        """Create from dict (POST)"""
        return cls(**data)

    def __repr__(self):
        return f'<Offer {self.offer_id} ({self.title})>'
