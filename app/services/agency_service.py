import os
import csv
import re
import shutil
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
        phone = re.sub(r'[\s\-]', '', phone)
        if not phone.startswith('+216') or len(phone) != 12:
            return False, "Format +216XXXXXXXX"
        digits = phone[4:]
        if len(digits) != 8 or not digits.isdigit():
            return False, "8 digits only"
        prefix = digits[0]
        if prefix in ['1','6','8','0']:
            return False, "Blocked prefix"
        return True, "OK"

    @staticmethod
    def calculate_trust_score(agency):
        score = 0
        reasons = []

        # STRICT PHONE (BLOCK 1,6,8,0)
        phone = agency.get('phone', '')
        valid, msg = AgencyService.validate_phone(phone)
        if valid:
            score += 25
            reasons.append("Valid phone (+25)")
        else:
            score -= 30
            reasons.append(f"Invalid phone {msg} (-30)")

        # EMAIL suspicious
        email = agency.get('email', '')
        if email and re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}$', email):
            if any(s in email.lower() for s in ['free','temp','spam','fake']):
                score -= 20; reasons.append("Suspicious email (-20)")
            elif email.endswith('.tn'):
                score += 10; reasons.append(".tn email (+10)")
            else:
                score += 10; reasons.append("Valid email (+10)")
        else:
            score -= 15; reasons.append("Bad email (-15)")

        # COMPANY NAME - TRAVEL KEYWORDS + SARL
        name = agency.get('company_name', '').upper()
        travel_keywords = ['VOYAGES', 'TRAVEL', 'BOOKING', 'AGENCE', 'AGENCY', 'TOURS']
        if any(kw in name for kw in travel_keywords):
            score += 20
            reasons.append("Travel keyword (+20)")
        if 'SARL' in name:
            score += 15
            reasons.append("SARL (+15)")
        if len(name) < 3:
            score -= 20; reasons.append("Name too short (-20)")

        # GOVERNORATE
        govs = ['TUNIS','ARINA','BEN AROUS','SOUSSE','SFAX']  # Top 5
        if agency.get('governorate') in govs:
            score += 15
            reasons.append("Valid gov (+15)")

        # TAX_ID format
        tax_id = agency.get('tax_id', '')
        if len(tax_id.replace(' ', '')) >= 8 and any(c.isalpha() for c in tax_id):
            score += 10
            reasons.append("Valid tax_id (+10)")

        score = min(100, max(0, score))
        fraud_risk = score < 40
        return score, fraud_risk, "; ".join(reasons)



    @staticmethod
    def is_duplicate(tax_id):
        """Check if tax_id already exists"""
        agencies = AgencyService.load_csv()
        return any(agency['tax_id'] == tax_id for agency in agencies)

    @staticmethod
    def validate_agency_data(agency_data):
        """Validate agency data fields"""
        required_fields = ['company_name', 'governorate', 'email', 'phone']
        for field in required_fields:
            if not agency_data.get(field):
                abort(400, f"{field} is required")

        # Validate governorate
        governorate = agency_data.get('governorate')
        if governorate not in AgencyService.TUNISIAN_GOVERNORATES:
            abort(400, f"Invalid governorate: {governorate}")

        # Validate email format
        email = agency_data.get('email')
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            abort(400, "Invalid email format")

        # Validate phone
        phone = agency_data.get('phone')
        valid, msg = AgencyService.validate_phone(phone)
        if not valid:
            abort(400, f"Invalid phone: {msg}")

    @staticmethod
    def add_agency(agency_data):
        # 1. Check for duplicates first
        tax_id = agency_data.get('tax_id')
        if not tax_id: abort(400, "tax_id required")

        tax_id = AgencyService.pad_rne(tax_id)

        if AgencyService.is_duplicate(tax_id):
            abort(409, "Duplicate tax_id")

        # 2. Validate form data
        AgencyService.validate_agency_data(agency_data)

        # Calculate trust score
        trust_score, fraud_risk, analysis = AgencyService.calculate_trust_score(agency_data)

        phone_valid, _ = AgencyService.validate_phone(agency_data.get('phone', ''))

        agencies = AgencyService.load_csv()
        new_agency = {
            'tax_id': tax_id,
            'company_name': agency_data.get('company_name', ''),
            'governorate': agency_data.get('governorate', ''),
            'email': agency_data.get('email', ''),
            'phone': agency_data.get('phone', ''),
            'phone_valid': phone_valid,
            'trust_score': trust_score,
            'fraud_risk': fraud_risk,
            'analysis': analysis,
            'last_verified': datetime.utcnow().isoformat() + 'Z'
        }

        # Backup + Save
        shutil.copy(AgencyService.CSV_PATH, 'data/tunisia_agencies_real_dataset_backup.csv')
        agencies.append(new_agency)
        AgencyService.save_csv(agencies)

        return {
            'tax_id': tax_id,
            'trust_score': trust_score,
            'fraud_risk': fraud_risk
        }

    @staticmethod
    def update_agency(tax_id, update_data):
        agencies = AgencyService.load_csv()
        for agency in agencies:
            if agency['tax_id'] == tax_id:
                # Update allowed fields
                for key, value in update_data.items():
                    if key in ['company_name', 'phone', 'email', 'governorate']:
                        agency[key] = value

                # Re-score!
                score, fraud, analysis = AgencyService.calculate_trust_score(agency)
                agency.update({
                    'trust_score': score,
                    'fraud_risk': fraud,
                    'analysis': analysis,
                    'last_verified': datetime.now().isoformat()
                })
                AgencyService.save_csv(agencies)
                return agency
        abort(404, f"Agency {tax_id} not found")

    @staticmethod
    def delete_agency(tax_id):
        agencies = [a for a in AgencyService.load_csv() if a['tax_id'] != tax_id]
        AgencyService.save_csv(agencies)



    @staticmethod
    def pad_rne(rne):
        """Auto-pad RNE with leading zeros"""
        rne = rne.strip()
        if len(rne) == 7 and rne[-1].isalpha():
            return rne  # "002412B" → "002412B" (no pad!)
        if any(c.isalpha() for c in rne):
            target_len = 9
        else:
            target_len = 8
        return rne.zfill(target_len)

    @staticmethod
    def get_agency_by_tax_id(tax_id):
        """Get agency by tax_id"""
        agencies = AgencyService.load_csv()
        return next((a for a in agencies if a['tax_id'] == tax_id), None)

    @staticmethod
    def get_agencies_sorted_by_trust():
        """Get all agencies sorted by trust_score DESC"""
        agencies = AgencyService.load_csv()
        return sorted(agencies, key=lambda x: x['trust_score'], reverse=True)

    @staticmethod
    def validate_rne_format(rne):
        """Validate RNE format - must be 8 digits"""
        rne = rne.replace(" ", "").strip()
        return len(rne) == 8 and rne.isdigit()
