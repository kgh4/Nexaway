import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.agency_service import AgencyService

def recalculate_all_scores():
    agencies = AgencyService.load_csv()
    updated_agencies = []

    for agency in agencies:
        # Recalculate trust score
        trust_score, fraud_risk, analysis = AgencyService.calculate_trust_score(agency)
        agency['trust_score'] = trust_score
        agency['fraud_risk'] = fraud_risk
        agency['analysis'] = analysis
        updated_agencies.append(agency)

    # Save back to CSV
    AgencyService.save_csv(updated_agencies)
    print(f"Recalculated scores for {len(updated_agencies)} agencies")

if __name__ == "__main__":
    recalculate_all_scores()
