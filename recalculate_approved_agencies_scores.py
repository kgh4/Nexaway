#!/usr/bin/env python
"""
Recalculate and update approved_agencies.csv with comprehensive trust scores
Uses the TrustScoreCalculator for standardized evaluation
"""

import os
import csv
from app import create_app, db
from app.models import Agency, Review
from app.services.trust_score_calculator import TrustScoreCalculator

app = create_app()

def main():
    with app.app_context():
        approved_agencies = Agency.query.filter_by(status='approved').all()
        
        print(f"\n{'='*100}")
        print(f"  RECALCULATING TRUST SCORES FOR {len(approved_agencies)} APPROVED AGENCIES")
        print(f"{'='*100}\n")
        
        if not approved_agencies:
            print("❌ No approved agencies found\n")
            return
        
        # Recalculate scores
        print("Calculating comprehensive trust scores...\n")
        
        scores_before = []
        scores_after = []
        
        for idx, agency in enumerate(approved_agencies, 1):
            # Old score (base)
            old_score = 50
            scores_before.append(old_score)
            
            # Get reviews
            reviews = Review.query.filter_by(agency_id=agency.agency_id, status='approved').all()
            
            # Calculate new score
            result = TrustScoreCalculator.calculate_trust_score(agency, reviews)
            new_score = result['score']
            scores_after.append(new_score)
            
            # Show some details
            if idx <= 10 or new_score != old_score:
                change = new_score - old_score
                change_str = f"+{change}" if change >= 0 else f"{change}"
                print(f"  {idx:2d}. {agency.company_name:<40} | {old_score} → {new_score} ({change_str})")
                if result['reasons']:
                    for reason in result['reasons']:
                        print(f"      └─ {reason}")
        
        # No database commit needed - we only update CSV
        
        print(f"\n{'='*100}")
        print(f"  UPDATING CSV FILE")
        print(f"{'='*100}\n")
        
        # Update CSV
        csv_path = os.path.join(app.root_path, '..', 'data', 'approved_agencies.csv')
        
        output = []
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'agency_id', 'tax_id', 'company_name', 'official_name', 'category',
                'email', 'phone', 'governorate', 'trust_score', 'status',
                'created_at', 'updated_at'
            ])
            
            # Data rows with NEW trust scores
            for agency in approved_agencies:
                reviews = Review.query.filter_by(agency_id=agency.agency_id, status='approved').all()
                result = TrustScoreCalculator.calculate_trust_score(agency, reviews)
                
                writer.writerow([
                    agency.agency_id or '',
                    agency.tax_id,
                    agency.company_name,
                    agency.official_name or '',
                    agency.category or '',
                    agency.email or '',
                    agency.phone or '',
                    agency.governorate or '',
                    result['score'],  # NEW CALCULATED SCORE
                    agency.status,
                    agency.created_at.isoformat() if agency.created_at else '',
                    agency.updated_at.isoformat() if agency.updated_at else ''
                ])
        
        # Statistics
        print(f"✅ CSV updated successfully!")
        print(f"   Location: {csv_path}\n")
        
        print(f"📊 Score Statistics:")
        print(f"   Before (Base): min={min(scores_before)}, avg={sum(scores_before)/len(scores_before):.1f}, max={max(scores_before)}")
        print(f"   After (Eval): min={min(scores_after)}, avg={sum(scores_after)/len(scores_after):.1f}, max={max(scores_after)}")
        print(f"   Improvement: {sum(scores_after) - sum(scores_before):+d} total points")
        
        # Show top agencies
        print(f"\n📈 Top 10 Agencies by Trust Score:")
        print(f"{'rank':<6} | {'agency_id':<10} | {'company_name':<35} | {'trust_score':<12}")
        print("-" * 75)
        
        top_agencies = sorted(
            [(a.agency_id, a.company_name, TrustScoreCalculator.calculate_trust_score(a, 
             Review.query.filter_by(agency_id=a.agency_id, status='approved').all())['score']) 
             for a in approved_agencies],
            key=lambda x: x[2],
            reverse=True
        )
        
        for rank, (agency_id, company_name, score) in enumerate(top_agencies[:10], 1):
            print(f"{rank:<6} | {agency_id:<10} | {company_name:<35} | {score:<12}")
        
        print(f"\n{'='*100}")
        print(f"  ✅ TRUST SCORES STANDARDIZED AND CSV UPDATED")
        print(f"{'='*100}\n")

if __name__ == '__main__':
    main()
