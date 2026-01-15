#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Seed 10,000 fake reviews for Nexaway agencies
Assumes 541 real agencies already exist in database
"""

import random
import uuid
from datetime import datetime, timedelta
from app import create_app, db
from app.models import Agency, Review

# Try to import Faker, install if needed
try:
    from faker import Faker
except ImportError:
    print("Installing faker...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'faker', '-q'])
    from faker import Faker

# Initialize app and Faker
app = create_app()
app.app_context().push()

fake = Faker('fr_FR')  # French locale for realistic names

# Configuration
NUM_REVIEWS = 10000
APPROVAL_RATE = 0.9  # 90% approved, 10% pending
REPLY_RATE = 0.75    # 75% of reviews get replies
MAX_REPLY_HOURS = 24 # Reply within 24 hours bonus

def generate_review_text():
    """Generate realistic review text using Faker"""
    templates = [
        fake.sentence(nb_words=15),
        fake.paragraph(nb_sentences=2),
        fake.text(max_nb_chars=150),
        f"Excellent service! {fake.sentence(nb_words=8)}",
        f"Good experience. {fake.sentence(nb_words=10)}",
        f"Could be better. {fake.sentence(nb_words=8)}",
        f"Not satisfied. {fake.sentence(nb_words=10)}",
    ]
    return random.choice(templates)[:200]

def generate_reply_text():
    """Generate realistic agency reply"""
    templates = [
        f"Thank you for your feedback! {fake.sentence(nb_words=8)}",
        f"We appreciate your comments. {fake.sentence(nb_words=10)}",
        f"Sorry to hear about your experience. {fake.sentence(nb_words=10)}",
        f"Glad we could serve you! {fake.sentence(nb_words=8)}",
        f"Your feedback helps us improve. {fake.sentence(nb_words=10)}",
    ]
    return random.choice(templates)[:150]

def seed_reviews():
    """Seed 10,000 fake reviews"""
    print("\n" + "="*70)
    print("[*] NEXAWAY REVIEWS SEEDING (10,000 fake reviews)")
    print("="*70)
    
    # Verify agencies exist
    agencies = Agency.query.all()
    if not agencies:
        print("[!] Error: No agencies found in database. Run seed.py first!")
        return
    
    print(f"\n[+] Found {len(agencies)} agencies")
    print(f"[*] Seeding {NUM_REVIEWS:,} reviews...")
    print(f"  - Approval rate: {APPROVAL_RATE*100:.0f}%")
    print(f"  - Reply rate: {REPLY_RATE*100:.0f}%")
    print(f"  - Max reply time: {MAX_REPLY_HOURS}h (for trust bonus)\n")
    
    batch_size = 1000
    created_reviews = 0
    created_replies = 0
    
    try:
        for i in range(NUM_REVIEWS):
            # Pick random agency
            agency = random.choice(agencies)
            
            # Generate review
            review = Review(
                review_id=f"R-{uuid.uuid4().hex[:8].upper()}",
                agency_id=agency.agency_id,  # Use agency_id field (the A-xxx code)
                customer_name=fake.name(),
                customer_email=fake.email(),
                rating=random.randint(1, 5),
                comment=generate_review_text(),
                status='approved' if random.random() < APPROVAL_RATE else 'pending',
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 180))
            )
            
            db.session.add(review)
            
            # 75% chance agency replies within 24h
            if random.random() < REPLY_RATE:
                hours_delay = random.randint(1, MAX_REPLY_HOURS)
                reply_time = review.created_at + timedelta(hours=hours_delay)
                
                review.reply = generate_reply_text()
                review.reply_at = reply_time
                
                # 50% chance customer re-rates after reply
                if random.random() < 0.5:
                    review.re_rating = random.randint(3, 5)  # Usually improves after reply
                    review.re_comment = fake.sentence(nb_words=10)
                
                created_replies += 1
            
            created_reviews += 1
            
            # Batch commit every 1000
            if (i + 1) % batch_size == 0:
                db.session.commit()
                percentage = ((i + 1) / NUM_REVIEWS) * 100
                print(f"  [+] {i + 1:,}/{NUM_REVIEWS:,} ({percentage:.1f}%) - "
                      f"{created_replies:,} replies created")
        
        # Final commit
        db.session.commit()
        
        # Print summary
        print("\n" + "="*70)
        print("[+] SEEDING COMPLETE")
        print("="*70)
        print(f"  Reviews created:  {created_reviews:,}")
        print(f"  Replies created:  {created_replies:,}")
        print(f"  Avg per agency:   {created_reviews / len(agencies):.1f} reviews")
        print(f"  Agencies replied: {created_replies / created_reviews * 100:.1f}%")
        
        # Show stats
        approved = Review.query.filter_by(status='approved').count()
        pending = Review.query.filter_by(status='pending').count()
        avg_rating = db.session.query(db.func.avg(Review.rating)).scalar()
        
        print(f"\n[*] Database Stats:")
        print(f"  Approved reviews: {approved:,} ({approved/created_reviews*100:.1f}%)")
        print(f"  Pending reviews:  {pending:,} ({pending/created_reviews*100:.1f}%)")
        print(f"  Average rating:   {avg_rating:.2f} stars")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n[!] Error during seeding: {e}")
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = seed_reviews()
    exit(0 if success else 1)
