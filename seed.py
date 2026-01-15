#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Comprehensive database seeding script for Nexaway
Loads 541 real agencies from CSV + generates fake data (reviews, offers, users)
"""

import csv
import uuid
import random
from datetime import datetime, timedelta
from app import create_app, db
from app.models import Agency, Review, Offer, User

# Try to import Faker, install if needed
try:
    from faker import Faker
except ImportError:
    print("Installing faker...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'faker'])
    from faker import Faker

# Initialize app and Faker
app = create_app()
app.app_context().push()

fake = Faker('fr_FR')  # French locale for realistic names/addresses

# Configuration
REAL_AGENCIES_CSV = 'data/tunisia_agencies_real_dataset.csv'
NUM_TEST_USERS = 5          # Test agency users for JWT testing

def load_real_agencies():
    """Load 541 real agencies from CSV"""
    print("\n[*] Loading real agencies from CSV...")
    count = 0
    
    try:
        with open(REAL_AGENCIES_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Skip if already exists
                if Agency.query.filter_by(tax_id=row['tax_id'].strip()).first():
                    continue
                
                agency = Agency(
                    tax_id=row['tax_id'].strip(),
                    company_name=row['company_name'].strip(),
                    official_name=row.get('official_name', '').strip(),
                    governorate=row.get('governorate', '').strip(),
                    email=row.get('email', '').strip(),
                    phone=row.get('phone', '').strip(),
                    status='approved',
                    source='csv',
                    verification_status='verified'
                )
                db.session.add(agency)
                count += 1
                
                if count % 50 == 0:
                    db.session.commit()
                    print(f"  [+] Loaded {count} agencies...")
        
        db.session.commit()
        print(f"[+] Total agencies loaded: {count}")
        return count
    
    except FileNotFoundError:
        print(f"[!] CSV file not found: {REAL_AGENCIES_CSV}")
        return 0

def generate_reviews(agencies):
    """Generate fake reviews for agencies"""
    print("\n[*] Generating fake reviews...")
    review_count = 0
    
    for agency in agencies:
        # Random 0-5 reviews per agency
        num_reviews = random.randint(0, 5)
        
        for _ in range(num_reviews):
            review = Review(
                review_id=f"R-{uuid.uuid4().hex[:8].upper()}",
                agency_id=agency.tax_id,  # Use tax_id since agency_id is null from CSV
                customer_name=fake.name(),
                customer_email=fake.email(),
                rating=random.randint(1, 5),
                comment=fake.sentence(nb_words=20),
                status='approved',
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 90))
            )
            
            # 40% chance agency replied
            if random.random() < 0.4:
                review.reply = fake.sentence(nb_words=15)
                review.reply_at = review.created_at + timedelta(hours=random.randint(1, 48))
                review.re_rating = random.randint(3, 5)
            
            db.session.add(review)
            review_count += 1
    
    db.session.commit()
    print(f"[+] Generated {review_count} reviews")
    return review_count

def generate_offers(agencies):
    """Generate fake travel offers"""
    print("\n[*] Generating fake offers...")
    offer_count = 0
    
    OFFER_TYPES = ['flight', 'hotel', 'cruise', 'package', 'pilgrimage', 'business']
    SEGMENTS = ['economy', 'business', 'first']
    PILGRIMAGE_TYPES = ['umrah', 'hajj', None]
    CITIES = ['TUN', 'SFA', 'DJR', 'HMM', 'JED', 'CAI', 'PAR', 'LON', 'IST']
    
    for agency in agencies:
        # Random 0-3 offers per agency
        num_offers = random.randint(0, 3)
        
        for _ in range(num_offers):
            offer_type = random.choice(OFFER_TYPES)
            
            date_from = datetime.utcnow().date() + timedelta(days=random.randint(5, 90))
            date_to = date_from + timedelta(days=random.randint(3, 14))
            
            offer = Offer(
                offer_id=f"O-{uuid.uuid4().hex[:8].upper()}",
                agency_id=agency.tax_id,  # Foreign key to agencies.tax_id
                type=offer_type,
                title=f"{offer_type.capitalize()} to {random.choice(CITIES)}",
                price=round(random.uniform(150, 5000), 2),
                currency='TND',
                from_city=random.choice(CITIES),
                to_city=random.choice([c for c in CITIES if c != 'TUN']),
                date_from=date_from,
                date_to=date_to,
                seats_available=random.randint(5, 100),
                description=fake.sentence(nb_words=20),
                segment=random.choice(SEGMENTS) if random.random() < 0.5 else None,
                pilgrimage_type=random.choice(PILGRIMAGE_TYPES),
                domestic=random.random() < 0.3,
                capacity=random.randint(20, 200),
                tags='["featured"]' if random.random() < 0.2 else '[]'
            )
            db.session.add(offer)
            offer_count += 1
    
    db.session.commit()
    print(f"[+] Generated {offer_count} offers")
    return offer_count

def create_test_users(num_users=NUM_TEST_USERS):
    """Create test agency users for JWT testing"""
    print(f"\n[*] Creating {num_users} test agency users...")
    
    agencies = Agency.query.limit(num_users).all()
    user_count = 0
    
    for i, agency in enumerate(agencies):
        user = User(
            email=f"agency{i+1}@nexaway.tn",
            role='agency',
            agency_id=agency.tax_id
        )
        user.set_password('password123')
        db.session.add(user)
        user_count += 1
    
    # Create admin user
    admin = User(
        email='admin@nexaway.tn',
        role='admin'
    )
    admin.set_password('admin123')
    db.session.add(admin)
    user_count += 1
    
    # Create test client user
    client = User(
        email='client@nexaway.tn',
        role='client'
    )
    client.set_password('client123')
    db.session.add(client)
    user_count += 1
    
    db.session.commit()
    print(f"[+] Created {user_count} test users")
    return user_count

def seed_database():
    """Complete database seeding"""
    print("\n" + "="*60)
    print("[*] NEXAWAY DATABASE SEEDING")
    print("="*60)
    
    # Drop and recreate all tables
    print("\n[*] Dropping existing database...")
    db.drop_all()
    db.create_all()
    print("[+] Database tables created")
    
    # Load real agencies
    agency_count = load_real_agencies()
    if agency_count == 0:
        print("[!] No agencies loaded. Exiting.")
        return
    
    # Get all agencies for generating related data
    agencies = Agency.query.all()
    
    # Generate fake data
    review_count = generate_reviews(agencies)
    offer_count = generate_offers(agencies)
    user_count = create_test_users()
    
    # Print summary
    print("\n" + "="*60)
    print("[+] SEEDING COMPLETE")
    print("="*60)
    print(f"  Agencies:  {agency_count}")
    print(f"  Reviews:   {review_count}")
    print(f"  Offers:    {offer_count}")
    print(f"  Users:     {user_count}")
    print("\n[*] Test Credentials:")
    print("  Admin:    admin@nexaway.tn / admin123")
    print("  Agency 1: agency1@nexaway.tn / password123")
    print("  Client:   client@nexaway.tn / client123")
    print("\n[*] Start server: python run.py")
    print("="*60 + "\n")

if __name__ == '__main__':
    try:
        seed_database()
    except Exception as e:
        print(f"\n[!] Seeding failed: {e}")
        import traceback
        traceback.print_exc()
