import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.agency_service import AgencyService

# Test data
test_agency_verified = {
    "tax_id": "01616343A",  # This one was verified in the dataset
    "company_name": "ABC SARL",
    "governorate": "Tunis",
    "email": "info@abc.tn",
    "phone": "+21671234567"
}

test_agency_not_verified = {
    "tax_id": "99999999Z",  # Fake one that won't be verified
    "company_name": "Fake Agency",
    "governorate": "Tunis",
    "email": "fake@fake.com",
    "phone": "+21671234567"
}

print("Testing unified POST /v1/agencies endpoint logic...")

print("\n1. Testing verified agency...")
try:
    result = AgencyService.add_agency(test_agency_verified)
    print(f"Result: {result}")
    print("✓ Agency added successfully")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n2. Testing unverified agency...")
try:
    result = AgencyService.add_agency(test_agency_not_verified)
    print(f"Result: {result}")
    print("✓ Agency added successfully")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n3. Testing duplicate agency...")
try:
    result = AgencyService.add_agency(test_agency_verified)
    print(f"Result: {result}")
    print("✗ Should have failed with duplicate")
except Exception as e:
    print(f"✓ Correctly rejected duplicate: {e}")

print("\n4. Testing low trust score agency...")
low_trust_agency = {
    "tax_id": "11111111X",
    "company_name": "Bad Agency",
    "governorate": "Unknown",
    "email": "bad@bad.com",
    "phone": "+21612345678"
}
try:
    result = AgencyService.add_agency(low_trust_agency)
    print(f"Result: {result}")
    print("✗ Should have been rejected")
except Exception as e:
    print(f"✓ Correctly rejected low trust: {e}")

print("\nTesting complete!")
