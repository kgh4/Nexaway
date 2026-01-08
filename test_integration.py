import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.agency_service import AgencyService
from app.services.rne_verification import verify_rne_sync

# Test data
test_agency = {
    "tax_id": "1234567A",
    "company_name": "Test Agency SARL",
    "email": "test@gmail.com",
    "phone": "+21650123456",
    "governorate": "Tunis"
}

print("Testing RNE verification function...")
rne_result = verify_rne_sync("1234567A")
print(f"RNE result: {rne_result}")

print("\nTesting add_agency function...")
try:
    result = AgencyService.add_agency(test_agency)
    print(f"Add agency result: {result}")
    print("Success: Agency added with RNE verification integrated.")
except Exception as e:
    print(f"Error: {e}")

print("\nTesting fraud_risk logic...")
# Test with low score agency
low_score_agency = {
    "tax_id": "9999999Z",
    "company_name": "Bad Agency",
    "email": "bad@bad.com",
    "phone": "+21612345678",
    "governorate": "Unknown"
}

try:
    result = AgencyService.add_agency(low_score_agency)
    print(f"Low score result: {result}")
except Exception as e:
    print(f"Expected rejection: {e}")

print("\nTesting CSV field names...")
agencies = AgencyService.load_csv()
if agencies:
    print(f"CSV fields: {list(agencies[0].keys())}")
    if 'rne_adjust' in agencies[0]:
        print("Success: rne_adjust field present")
    else:
        print("Error: rne_adjust field missing")
else:
    print("No agencies in CSV yet")
