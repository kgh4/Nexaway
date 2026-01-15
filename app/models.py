# -*- coding: utf-8 -*-
from .extensions import db
from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import func, CheckConstraint

class Agency(db.Model):
    """Tunisian Travel Agency Model - Matches CSV exactly"""

    __tablename__ = 'agencies'

    id = db.Column(db.Integer, primary_key=True)
    agency_id = db.Column(db.String(20), unique=True, index=True)  # A-xxx for approved agencies

    # Core Business Data
    tax_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
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
    status = db.Column(db.String(20), default='pending', index=True)  # pending, approved
    source = db.Column(db.String(20), default='csv')

    # Password for claiming approved agencies
    password_hash = db.Column(db.String(128))

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
    
    def set_password(self, password):
        """Hash and set password"""
        from app.extensions import bcrypt
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Check password against hash"""
        from app.extensions import bcrypt
        return bcrypt.check_password_hash(self.password_hash, password)

    @hybrid_property
    def norm_tax_id(self):
        return self.tax_id.upper()

    @norm_tax_id.expression
    def norm_tax_id(cls):
        return func.upper(cls.tax_id)

    @property
    def trust_score(self):
        """
        Dynamic trust score calculated from weighted factors:
        - recency (0.3): Recent reviews weighted more
        - volume (0.2): Review count (capped at 100)
        - avg_rating (0.25): Average rating (1-5 normalized)
        - reply_rate (0.15): % of reviews with <24h replies
        - spam_reject (0.1): % of non-spam reviews
        - verified (0.05): Bonus for approved status (1.1x vs 0.9x)
        
        Returns: Score on 0-100 scale
        """
        from datetime import timedelta
        from sqlalchemy import func
        
        if not self.agency_id:
            return 50  # Base for unapproved agencies
        
        # Get all approved reviews for this agency
        reviews = Review.query.filter(
            Review.agency_id == self.agency_id,
            Review.status == 'approved'
        ).all()
        
        total_reviews = len(reviews)
        
        # Factor 1: Recency weight (30%) - Recent > Old
        if total_reviews > 0:
            recent_cutoff = datetime.utcnow() - timedelta(days=30)
            recent_count = sum(1 for r in reviews if r.created_at >= recent_cutoff)
            recency = min(recent_count / max(total_reviews, 1) * 1.2, 1.0)
        else:
            recency = 0.5  # Neutral if no reviews
        
        # Factor 2: Volume weight (20%) - More reviews = higher score
        volume = min(total_reviews / 100, 1.0)
        
        # Factor 3: Average rating (25%) - 1-5 normalized to 0-1
        if total_reviews > 0:
            avg_rating = sum(r.rating for r in reviews) / total_reviews
            avg_rating_normalized = (avg_rating - 1) / 4  # Convert 1-5 to 0-1
        else:
            avg_rating_normalized = 0.6  # Neutral
        
        # Factor 4: Reply rate (15%) - % with <24h replies
        if total_reviews > 0:
            replied_fast = sum(
                1 for r in reviews 
                if r.reply and r.reply_at and 
                (r.reply_at - r.created_at) <= timedelta(hours=24)
            )
            reply_rate = replied_fast / total_reviews
        else:
            reply_rate = 0.5  # Neutral
        
        # Factor 5: Spam rejection (10%) - % of reviews that aren't spam
        if total_reviews > 0:
            spam_count = sum(1 for r in reviews if r.status == 'rejected')
            spam_reject = 1 - (spam_count / total_reviews)
        else:
            spam_reject = 1.0  # No spam if no reviews
        
        # Factor 6: Verification bonus (5%) - Approved vs Pending
        verified_multiplier = 1.1 if self.status == 'approved' else 0.9
        
        # Calculate weighted score (0-1 scale)
        weighted_score = (
            recency * 0.3 +
            volume * 0.2 +
            avg_rating_normalized * 0.25 +
            reply_rate * 0.15 +
            spam_reject * 0.1
        ) * verified_multiplier
        
        # Convert to 0-100 scale, round to 1 decimal
        final_score = round(weighted_score * 100, 1)
        
        return min(100, max(0, final_score))

    def __repr__(self):
        return f'<Agency {self.company_name} ({self.tax_id})>'


class Offer(db.Model):
    """Travel Offer Model"""

    __tablename__ = 'offers'

    id = db.Column(db.Integer, primary_key=True)
    offer_id = db.Column(db.String(20), unique=True, nullable=False, index=True)

    # Required fields
    agency_id = db.Column(db.String(20), db.ForeignKey('agencies.tax_id'), nullable=False, index=True)
    type = db.Column(db.String(20), nullable=False)  # hotel, cruise, flight, package, pilgrimage, business
    title = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), nullable=False)  # DT, EUR, USD

    # Optional fields
    from_city = db.Column(db.String(10))
    to_city = db.Column(db.String(10))
    date_from = db.Column(db.Date)
    date_to = db.Column(db.Date)
    seats_available = db.Column(db.Integer)
    description = db.Column(db.Text)

    # New fields
    segment = db.Column(db.String(20))  # economy, business, first
    pilgrimage_type = db.Column(db.String(20))  # umrah, hajj
    domestic = db.Column(db.Boolean, default=False)
    capacity = db.Column(db.Integer)  # Total seats
    tags = db.Column(db.Text)  # JSON array like ["vip", "family"]

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    agency = db.relationship('Agency', backref=db.backref('offers', lazy=True))

    def to_dict(self):
        """JSON serialization"""
        import json
        return {
            'offer_id': self.offer_id,
            'agency_tax_id': self.agency_id,  # Keep for compatibility
            'agency_name': self.agency.company_name if self.agency else None,
            'type': self.type,
            'title': self.title,
            'price': self.price,
            'currency': self.currency,
            'from_city': self.from_city,
            'to_city': self.to_city,
            'date_from': self.date_from.isoformat() if self.date_from else None,
            'date_to': self.date_to.isoformat() if self.date_to else None,
            'seats_available': self.seats_available,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'segment': self.segment,
            'pilgrimage_type': self.pilgrimage_type,
            'domestic': self.domestic,
            'capacity': self.capacity,
            'tags': json.loads(self.tags) if self.tags else []
        }

    @classmethod
    def from_dict(cls, data):
        """Create from dict (POST)"""
        return cls(**data)

    def __repr__(self):
        return f'<Offer {self.offer_id} ({self.title})>'


class Review(db.Model):
    """Customer Review Model"""

    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    agency_id = db.Column(db.String(20), db.ForeignKey('agencies.agency_id'), nullable=False, index=True)
    client_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)  # For authenticated clients
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(120), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 ⭐
    comment = db.Column(db.Text)
    reply = db.Column(db.Text)  # Agency reply to review
    reply_at = db.Column(db.DateTime)
    re_rating = db.Column(db.Integer)  # Re-rating after reply
    re_comment = db.Column(db.Text)  # Re-comment after reply
    trust_bonus = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='pending', index=True)  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    agency = db.relationship('Agency', backref=db.backref('reviews', lazy=True))
    client = db.relationship('User', backref=db.backref('reviews', lazy=True))

    def to_dict(self):
        """JSON serialization"""
        return {
            'id': self.id,
            'review_id': self.review_id,
            'agency_id': self.agency_id,
            'agency_name': self.agency.company_name if self.agency else None,
            'customer_name': self.customer_name,
            'customer_email': self.customer_email,
            'rating': self.rating,
            'comment': self.comment,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @classmethod
    def from_dict(cls, data):
        """Create from dict (POST)"""
        return cls(**data)

    def __repr__(self):
        return f'<Review {self.review_id} ({self.customer_name})>'


class PendingAgency(db.Model):
    """Pending Agency Registration Model"""

    __tablename__ = 'pending_agencies'

    id = db.Column(db.Integer, primary_key=True)
    pending_id = db.Column(db.String(20), unique=True, nullable=False, index=True)

    # Agency data
    agency_tax_id = db.Column(db.String(20), nullable=False, index=True)
    company_name = db.Column(db.String(200), nullable=False)
    official_name = db.Column(db.String(200))
    email = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(50))
    address = db.Column(db.String(255))
    governorate = db.Column(db.String(80))
    website = db.Column(db.String(200))
    sectors = db.Column(db.String(100))
    tourism_license = db.Column(db.String(50))
    registry_number = db.Column(db.String(50))

    # File upload
    license_image_url = db.Column(db.String(255), nullable=True)

    # Password for auth
    password_hash = db.Column(db.String(128))

    # Status
    status = db.Column(db.String(20), default='pending', index=True)  # pending, approved, rejected

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """JSON serialization"""
        return {
            'id': self.id,
            'pending_id': self.pending_id,
            'agency_tax_id': self.agency_tax_id,
            'company_name': self.company_name,
            'official_name': self.official_name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'governorate': self.governorate,
            'website': self.website,
            'sectors': self.sectors,
            'tourism_license': self.tourism_license,
            'registry_number': self.registry_number,
            'license_image_url': self.license_image_url,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_dict(cls, data):
        """Create from dict"""
        return cls(**data)

    def set_password(self, password):
        """Hash and set password"""
        from app.extensions import bcrypt
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Check password against hash"""
        from app.extensions import bcrypt
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<PendingAgency {self.pending_id} ({self.company_name})>'


class User(db.Model):
    """User Model for Authentication"""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, index=True)  # admin, agency, client
    agency_id = db.Column(db.String(20), db.ForeignKey('agencies.tax_id'))

    # Relationships
    agency = db.relationship('Agency', backref=db.backref('users', lazy=True))

    def to_dict(self):
        """JSON serialization"""
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'agency_id': self.agency_id,
            'agency_name': self.agency.company_name if self.agency else None
        }

    def set_password(self, password):
        """Hash and set password"""
        from app.extensions import bcrypt
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Check password against hash"""
        from app.extensions import bcrypt
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'


def create_test_pending_agency():
    """Create test pending agency for Insomnia"""
    from app import db
    from . import PendingAgency
    from datetime import datetime

    # Check if exists
    if PendingAgency.query.filter_by(pending_id='P-7f3a2b').first():
        print("✅ P-7f3a2b exists!")
        return

    agency = PendingAgency(
        pending_id='P-7f3a2b',
        agency_tax_id='12345678',
        company_name='Elite Travel TN',
        official_name='Elite Travel SARL',
        email='contact@elitetravel.tn',
        phone='71234567',
        address='123 Avenue Habib Bourguiba',
        governorate='Tunis',
        website='www.elitetravel.tn',
        sectors='["Hotels", "Tours"]',
        tourism_license='LIC-2026-001',
        registry_number='RC-123456',
        license_image_url='https://nexaway.tn/licenses/lic001.jpg',
        status='pending',
        created_at=datetime.utcnow()
    )

    db.session.add(agency)
    db.session.commit()
    print("✅ P-7f3a2b CREATED!")
