import os
import csv
import re
from datetime import datetime
from flask import abort

class AgencyService:
    CSV_PATH = 'data/tunisia_agencies_real_dataset.csv'

    TUNISIAN_GOVERNORATES = [
        'Tunis', 'Ariana', 'Ben Arous', 'Manouba', 'Nabeul', 'Zaghouan', 'Bizerte',
        'Beja', 'Jendouba', 'Kef', 'Siliana', 'Sousse', 'Monastir', 'Mahdia', 'Sfax',
        'Kairouan', 'Kasserine', 'Sidi Bouzid', 'Gabes', 'Medenine', 'Tataouine',
        'Gafsa', 'Tozeur', 'Kebili'
    ]

    @staticmethod
    def load_csv():
        """Load all agencies from CSV as List[dict]"""
        if not os.path.exists(AgencyService.CSV_PATH):
            return []

        agencies = []
        with open(AgencyService.CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                agencies.append({
                    'tax_id': row.get('tax_id', ''),
                    'company_name': row.get('company_name', ''),
                    'official_name': row.get('official_name', ''),
                    'governorate': row.get('governorate', ''),
                    'email': row.get('email', ''),
                    'phone': row.get('phone', ''),
                    'phone_valid': row.get('phone_valid', 'False').lower() == 'true',
                    'trust_score': int(float(row.get('trust_score', 50))),
                    'fraud_risk': row.get('fraud_risk', 'False').lower() == 'true',
                    'analysis': row.get('analysis', ''),
                    'last_verified': row.get('last_verified', '')
                })
        return agencies

    @staticmethod
    def save_csv(agencies):
        """Write all agencies to CSV"""
        if not agencies:
            return

        fieldnames = ['tax_id', 'company_name', 'official_name', 'governorate', 'email', 'phone', 'phone_valid', 'trust_score', 'fraud_risk', 'analysis', 'last_verified']

        with open(AgencyService.CSV_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for agency in agencies:
                writer.writerow({
                    'tax_id': agency['tax_id'],
                    'company_name': agency['company_name'],
                    'official_name': agency.get('official_name', ''),
                    'governorate': agency['governorate'],
                    'email': agency['email'],
                    'phone': agency['phone'],
                    'phone_valid': agency.get('phone_valid', False),
                    'trust_score': agency['trust_score'],
                    'fraud_risk': str(agency['fraud_risk']).lower(),
                    'analysis': agency['analysis'],
                    'last_verified': agency['last_verified']
                })

    @staticmethod
    def validate_phone(phone):
        """Validate Tunisian phone number"""
        if not phone or not phone.startswith('+216'):
            return False, "Invalid format"

        digits = phone[4:]  # Remove +216
        if len(digits) != 8 or not digits.isdigit():
            return False, "Must be +216 + 8 digits"

        prefix = digits[0]
        if prefix in ['5', '7', '9']:
            return True, "Mobile"
        elif prefix in ['3', '4', '6', '8']:
            return True, "Landline"
        else:
            return False, "Invalid prefix"

    @staticmethod
    def calculate_trust_score(agency):
        """Calculate AI trust score based on input factors (0-100)"""
        score = 0
        reasons = []

        email = agency.get('email', '')
        phone = agency.get('phone', '')
        company_name = agency.get('company_name', '')
        governorate = agency.get('governorate', '')
        tax_id = agency.get('tax_id', '')

        # Phone validation
        if phone:
            valid, phone_type = AgencyService.validate_phone(phone)
            if valid:
                if phone_type == "Mobile":
                    score += 25
                    reasons.append("Valid mobile phone (+25)")
                else:
                    score += 15
                    reasons.append("Valid landline phone (+15)")
            else:
                score -= 20
                reasons.append("Invalid phone (-20)")
        else:
            reasons.append("No phone provided")

        # Email validation
        if email:
            if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                if email.endswith('.tn') or 'gmail' in email:
                    score += 20
                    reasons.append("Valid email domain (+20)")
                else:
                    score -= 15
                    reasons.append("Suspicious email domain (-15)")
            else:
                reasons.append("Invalid email format")
        else:
            reasons.append("No email provided")

        # Company name validation
        if company_name:
            if 'SARL' in company_name.upper() or 'travel' in company_name.lower() or 'agency' in company_name.lower():
                score += 30
                reasons.append("Legitimate company name (+30)")
            elif 'free' in company_name.lower() or 'money' in company_name.lower():
                score -= 25
                reasons.append("Suspicious company name (-25)")
        else:
            reasons.append("No company name provided")

        # Governorate validation
        if governorate and governorate in AgencyService.TUNISIAN_GOVERNORATES:
            score += 15
            reasons.append("Valid Tunisian governorate (+15)")
        else:
            score -= 10
            reasons.append("Invalid or missing governorate (-10)")

        # Tax ID validation
        if tax_id and len(tax_id) >= 8:
            digits = tax_id[:7]
            letter = tax_id[7] if len(tax_id) > 7 else ''
            if digits.isdigit() and (len(tax_id) == 7 or letter.isalpha()):
                score += 10
                reasons.append("Valid tax ID format (+10)")
            else:
                reasons.append("Invalid tax ID format")
        else:
            reasons.append("Invalid tax ID")

        score = max(0, min(100, score))
        fraud_risk = score < 50
        analysis = "; ".join(reasons)

        return score, fraud_risk, analysis

    @staticmethod
    def validate_rne_format(rne):
        """Validate RNE format: 7 digits + 1 letter"""
        if len(rne) == 8:
            digits = rne[:7]
            letter = rne[7]
            return digits.isdigit() and letter.isalpha()
        return False

    @staticmethod
    def is_duplicate(tax_id):
        """Check if tax_id already exists"""
        agencies = AgencyService.load_csv()
        return any(agency['tax_id'] == tax_id for agency in agencies)

    @staticmethod
    def add_agency(agency_data):
        """Add new agency with trust scoring and duplicate check"""
        tax_id = agency_data.get('tax_id')
        if not tax_id:
            abort(400, "tax_id is required")

        # Pad tax_id
        tax_id = AgencyService.pad_rne(tax_id)

        # Check duplicate
        if AgencyService.is_duplicate(tax_id):
            abort(409, "Duplicate tax_id: Agency already exists")

        # Calculate trust score
        trust_score, fraud_risk, analysis = AgencyService.calculate_trust_score(agency_data)

        # Reject if trust_score < 30
        if trust_score < 30:
            abort(400, f"Trust score too low ({trust_score}). Agency rejected. Analysis: {analysis}")

        # Load existing agencies
        agencies = AgencyService.load_csv()

        # Validate phone
        phone_valid, _ = AgencyService.validate_phone(agency_data.get('phone', ''))

        # Create new agency dict
        new_agency = {
            'tax_id': tax_id,
            'company_name': agency_data.get('company_name', ''),
            'official_name': agency_data.get('official_name', ''),
            'governorate': agency_data.get('governorate', ''),
            'email': agency_data.get('email', ''),
            'phone': agency_data.get('phone', ''),
            'phone_valid': phone_valid,
            'trust_score': trust_score,
            'fraud_risk': fraud_risk,
            'analysis': analysis,
            'last_verified': datetime.utcnow().isoformat() + 'Z'
        }

        # Append and save
        agencies.append(new_agency)
        AgencyService.save_csv(agencies)

        return {
            'trust_score': trust_score,
            'fraud_risk': fraud_risk,
            'analysis': analysis,
            'total': len(agencies),
            'premium_verified': trust_score > 80
        }

    @staticmethod
    def pad_rne(rne):
        """Auto-pad RNE with leading zeros"""
        if any(c.isalpha() for c in rne):
            target_len = 9
        else:
            target_len = 8
        return rne.zfill(target_len)

    @staticmethod
    def get_agencies_sorted_by_trust():
        """Get all agencies sorted by trust_score DESC"""
        agencies = AgencyService.load_csv()
        return sorted(agencies, key=lambda x: x['trust_score'], reverse=True)
