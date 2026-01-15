#!/usr/bin/env python
"""
Assign agency_id to all approved agencies that don't have one
Formats: A-001, A-002, A-003, etc.
"""

from app import create_app, db
from app.models import Agency

app = create_app()

def main():
    with app.app_context():
        # Get all approved agencies without agency_id
        agencies = Agency.query.filter_by(status='approved').all()
        
        print(f"\n{'='*80}")
        print(f"  ASSIGNING agency_id TO {len(agencies)} APPROVED AGENCIES")
        print(f"{'='*80}\n")
        
        if not agencies:
            print("❌ No approved agencies found\n")
            return
        
        # Filter those without agency_id
        agencies_without_id = [a for a in agencies if not a.agency_id]
        
        print(f"📊 Agencies requiring agency_id: {len(agencies_without_id)}")
        print(f"   Agencies with agency_id: {len(agencies) - len(agencies_without_id)}\n")
        
        if not agencies_without_id:
            print("✅ All agencies already have agency_id assigned!\n")
            return
        
        # Assign agency_id in format A-xxx
        print("Assigning agency_id...\n")
        
        for idx, agency in enumerate(agencies_without_id, 1):
            agency.agency_id = f"A-{agency.id:03d}"
            print(f"  {idx:2d}. {agency.company_name:<40} → {agency.agency_id}")
        
        # Commit changes
        db.session.commit()
        
        print(f"\n✅ Successfully assigned agency_id to {len(agencies_without_id)} agencies!")
        
        # Show summary
        print(f"\n{'='*80}")
        print(f"  ASSIGNMENT COMPLETE")
        print(f"{'='*80}\n")
        
        print(f"Sample of assigned agencies:")
        print(f"{'agency_id':<12} | {'company_name':<40} | {'tax_id':<15}")
        print("-" * 75)
        
        for agency in agencies_without_id[:10]:
            print(f"{agency.agency_id:<12} | {agency.company_name:<40} | {agency.tax_id:<15}")
        
        if len(agencies_without_id) > 10:
            print(f"... and {len(agencies_without_id) - 10} more\n")
        else:
            print()

if __name__ == '__main__':
    main()
