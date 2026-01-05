import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.agency_service import AgencyService
from app.services.rne_verification import verify_rne_sync
import time

def update_dataset_rne():
    """Update existing agencies in CSV with RNE verification"""
    print("Loading agencies from CSV...")
    agencies = AgencyService.load_csv()

    updated_count = 0
    verified_count = 0

    for i, agency in enumerate(agencies):
        tax_id = agency['tax_id']
        print(f"Verifying agency {i+1}/{len(agencies)}: {tax_id}")

        try:
            # Verify RNE
            rne_result = verify_rne_sync(tax_id)

            if rne_result.get('verified', False):
                agency['rne_status'] = "RNE_VERIFIED"
                agency['rne_adjust'] = 25
                verified_count += 1
                print(f"  ✓ VERIFIED: {tax_id}")
            else:
                agency['rne_status'] = "NOT_VERIFIED"
                agency['rne_adjust'] = 0  # No adjustment for existing agencies
                print(f"  ✗ NOT VERIFIED: {tax_id}")

            updated_count += 1

            # Add delay to avoid overwhelming the server
            time.sleep(2)

        except Exception as e:
            print(f"  Error verifying {tax_id}: {e}")
            agency['rne_status'] = "NOT_VERIFIED"
            agency['rne_adjust'] = 0

    print(f"\nSaving updated agencies to CSV...")
    AgencyService.save_csv(agencies)

    print(f"Update complete:")
    print(f"  Total agencies: {len(agencies)}")
    print(f"  Updated: {updated_count}")
    print(f"  Verified: {verified_count}")
    print(f"  Not verified: {updated_count - verified_count}")

if __name__ == "__main__":
    update_dataset_rne()
