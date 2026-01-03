#!/usr/bin/env python3
"""
Test script for RNE verification using Playwright
"""

from app import create_app
from app.routes.agencies import AgencyCreate

def test_rne_verification():
    """Test RNE verification with sample data"""
    print("Testing RNE verification...")

    # Test with sample RNE
    rne = "01616343A"
    print(f"🔍 RNE: {rne}")

    # Test format validation
    padded = AgencyCreate.pad_rne(rne)
    format_ok = AgencyCreate.validate_rne_format(padded)
    print(f"✅ FORMAT OK: {format_ok}")

    if format_ok:
        print("🌐 Checking REAL registry.tn...")
        verified = AgencyCreate.verify_rne_online(rne)
        if verified:
            print(f"✅ COMPANY EXISTS: Nom: {verified.get('company_name', 'Unknown')}")
            print("✅ VERIFIED!")
        else:
            print("❌ NOT FOUND")
    else:
        print("❌ FORMAT INVALID")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        test_rne_verification()
