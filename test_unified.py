import requests
import json

# Test data
test_data = {
    "tax_id": "12345678",
    "company_name": "TEST AGENCY SARL",
    "governorate": "Tunis",
    "email": "test@test.tn",
    "phone": "+21651234567"
}

# Test the unified endpoint
url = "http://127.0.0.1:8000/v1/agencies"
headers = {"Content-Type": "application/json"}

try:
    response = requests.post(url, data=json.dumps(test_data), headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
