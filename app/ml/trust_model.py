class AgencyTrustModel:
    def __init__(self):
        # Simple rule-based ML simulation
        pass

    def predict_risk(self, agency_data):
        """
        Predict fraud risk using simulated ML model
        Returns: risk_score (0-100, higher = more risky)
        """
        # Extract features
        trust_score = agency_data.get('trust_score', 50)
        phone_valid = agency_data.get('phone_valid', False)
        email_valid = agency_data.get('email_valid', False)
        rne_verified = agency_data.get('rne_status') == 'RNE_VERIFIED'
        gov_valid = agency_data.get('governorate') in [
            'Tunis', 'Ariana', 'Ben Arous', 'Manouba', 'Nabeul', 'Zaghouan',
            'Bizerte', 'Beja', 'Jendouba', 'Kef', 'Siliana', 'Sousse',
            'Monastir', 'Mahdia', 'Sfax', 'Kairouan', 'Kasserine',
            'Sidi Bouzid', 'Gabes', 'Medenine', 'Tataouine', 'Gafsa', 'Tozeur', 'Kebili'
        ]

        # Simple risk calculation (simulating ML model)
        risk_score = 0

        # High trust score reduces risk
        if trust_score > 80:
            risk_score -= 20
        elif trust_score < 50:
            risk_score += 20

        # Validations reduce risk
        if phone_valid:
            risk_score -= 10
        if email_valid:
            risk_score -= 10
        if rne_verified:
            risk_score -= 15
        if gov_valid:
            risk_score -= 5

        # Ensure risk is between 0-100
        return max(0, min(100, risk_score + 50))  # Base 50 + adjustments
