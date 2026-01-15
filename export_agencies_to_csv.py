#!/usr/bin/env python
"""
Export all approved agencies to CSV for tracking and evaluation
"""

from app import create_app, db
from app.models import Agency, Review
from app.routes.agencies import _save_agencies_csv_to_file
import os

app = create_app()

def main():
    with app.app_context():
        # Get all approved agencies
        agencies = Agency.query.filter_by(status='approved').all()
        
        print(f"\n{'='*80}")
        print(f"  EXPORTING {len(agencies)} APPROVED AGENCIES TO CSV")
        print(f"{'='*80}\n")
        
        if not agencies:
            print("❌ No approved agencies found in database\n")
            return
        
        print(f"📊 Agencies to export: {len(agencies)}\n")
        
        # Show preview
        print("Sample agencies:")
        print(f"{'agency_id':<12} | {'company_name':<35} | {'tax_id':<15} | {'trust_score':<12}")
        print("-" * 80)
        
        for agency in agencies[:10]:
            reviews = Review.query.filter_by(agency_id=agency.agency_id, status='approved').count()
            print(f"{agency.agency_id or 'N/A':<12} | {agency.company_name:<35} | {agency.tax_id:<15} | {agency.trust_score:<12.0f}")
        
        if len(agencies) > 10:
            print(f"... and {len(agencies) - 10} more agencies")
        
        # Generate and save CSV
        print(f"\n📁 Saving to CSV...\n")
        
        csv_content = _save_agencies_csv_to_file()
        
        csv_path = os.path.join(app.root_path, '..', 'data', 'approved_agencies.csv')
        
        # Verify it was created
        if os.path.exists(csv_path):
            file_size = os.path.getsize(csv_path)
            print(f"✅ CSV file created successfully!")
            print(f"   Location: {csv_path}")
            print(f"   Size: {file_size} bytes")
            print(f"   Records: {len(agencies)} agencies")
            
            # Show column info
            print(f"\n📋 CSV Columns:")
            columns = ['agency_id', 'tax_id', 'company_name', 'official_name', 'category',
                      'email', 'phone', 'governorate', 'trust_score', 'status', 'created_at', 'updated_at']
            for i, col in enumerate(columns, 1):
                print(f"   {i:2d}. {col}")
            
            # Statistics
            trust_scores = [a.trust_score for a in agencies]
            avg_score = sum(trust_scores) / len(trust_scores) if trust_scores else 0
            
            print(f"\n📈 Trust Score Statistics:")
            print(f"   Minimum: {min(trust_scores):.0f}")
            print(f"   Average: {avg_score:.0f}")
            print(f"   Maximum: {max(trust_scores):.0f}")
            
            print(f"\n{'='*80}")
            print(f"  ✅ ALL {len(agencies)} AGENCIES EXPORTED AND READY FOR TRACKING")
            print(f"{'='*80}\n")
        else:
            print(f"❌ Error: CSV file was not created")

if __name__ == '__main__':
    main()
