import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.rne_verification import RNEVerificationService

def test_rne_verification():
    print("Testing RNE Verification Service...")

    # Test with valid tax_id
    print("\nTesting valid tax_id: 01616343A")
    result = RNEVerificationService.verify_rne_sync("01616343A")
    print(f"Result: {result}")

    # Test with fake tax_id
    print("\nTesting fake tax_id: FAKE123")
    result = RNEVerificationService.verify_rne_sync("FAKE123")
    print(f"Result: {result}")

if __name__ == "__main__":
    test_rne_verification()
