#!/usr/bin/env python
"""
Trust Score Calculator - Comprehensive Evaluation Engine

Evaluates agencies based on:
1. Phone format validation
2. Email validation
3. RNE/Tax ID format
4. Reviews analysis (ratings, fast replies, resolutions)
5. Official name verification
"""

import re
from datetime import timedelta

class TrustScoreCalculator:
    """
    Unified trust score calculation for all agencies
    Used for both Tunisia agencies and Approved agencies
    """
    
    # Phone validation rules
    VALID_PHONE_PREFIX = {
        '+216 2': 'Orange',      # 2x
        '+216 5': 'Tunisiana',   # 5x, 59
        '+216 7': 'Ooredoo',     # 70-75
        '+216 9': 'Mixed',       # 9x
    }
    
    BLOCKED_PREFIXES = ['1', '6', '8', '0']  # Suspicious
    
    @staticmethod
    def validate_phone(phone):
        """
        Validate phone format
        Returns: (is_valid, message, score_change)
        """
        if not phone:
            return False, "Phone number missing", -20
        
        # Normalize phone
        normalized = phone.replace(' ', '').replace('-', '').strip()
        
        # Check format
        if not normalized.startswith('+216'):
            return False, "Must start with +216", -20
        
        if len(normalized) != 12:
            return False, "Invalid length (must be +216 + 8 digits)", -20
        
        # Check digits
        digits = normalized[4:]
        if not digits.isdigit():
            return False, "Non-digit characters after +216", -20
        
        if len(digits) != 8:
            return False, "Must have 8 digits", -20
        
        # Check first digit (prefix)
        first_digit = digits[0]
        if first_digit in TrustScoreCalculator.BLOCKED_PREFIXES:
            return False, f"Blocked prefix {first_digit}", -30
        
        return True, "Valid Tunisian phone", 15
    
    @staticmethod
    def validate_email(email):
        """
        Validate email format
        Returns: (is_valid, message, score_change)
        """
        if not email:
            return False, "Email missing", -20
        
        # Email regex pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(pattern, email):
            return False, "Invalid email format", -20
        
        # Check for suspicious domains
        suspicious = ['free', 'temp', 'spam', 'fake', 'test123', 'test456']
        email_lower = email.lower()
        
        for word in suspicious:
            if word in email_lower:
                return False, f"Suspicious domain ({word})", -25
        
        return True, "Valid email domain", 15
    
    @staticmethod
    def validate_rne(tax_id):
        """
        Validate RNE/Tax ID format (8 digits + 1 letter)
        Returns: (is_valid, message, score_change)
        """
        if not tax_id:
            return False, "Tax ID missing", -25
        
        # Remove spaces
        normalized = tax_id.replace(' ', '').strip().upper()
        
        # Check format: 8 digits + 1 letter
        if not re.match(r'^[0-9]{8}[A-Z]$', normalized):
            return False, "Invalid RNE format (must be 8 digits + 1 letter)", -25
        
        return True, "Valid RNE format", 20
    
    @staticmethod
    def validate_official_name(official_name):
        """
        Check if official name is provided
        Returns: (has_name, message, score_change)
        """
        if official_name and official_name.strip():
            return True, "Official name verified", 10
        return False, "No official name", 0
    
    @staticmethod
    def calculate_from_reviews(reviews):
        """
        Calculate score from reviews
        Reviews should be list of Review objects or dicts with:
        - rating: 1-5
        - reply: reply text (optional)
        - reply_at: datetime (optional)
        - created_at: datetime
        - re_rating: re-rating value (optional)
        
        Returns: (score_change, reasons_list)
        """
        score_change = 0
        reasons = []
        
        if not reviews:
            reasons.append("No reviews yet")
            return score_change, reasons
        
        # Filter approved reviews
        approved = [r for r in reviews if getattr(r, 'status', 'approved') == 'approved']
        
        if not approved:
            reasons.append("No approved reviews")
            return score_change, reasons
        
        # Average rating
        ratings = [float(r.rating) for r in approved if hasattr(r, 'rating')]
        if ratings:
            avg_rating = sum(ratings) / len(ratings)
            
            if avg_rating >= 4.0:
                score_change += 20
                reasons.append(f"High ratings ({avg_rating:.1f}★) (+20)")
            elif avg_rating >= 3.0:
                score_change += 10
                reasons.append(f"Good ratings ({avg_rating:.1f}★) (+10)")
            else:
                score_change -= 15
                reasons.append(f"Low ratings ({avg_rating:.1f}★) (-15)")
        
        # Fast replies (within 24 hours)
        fast_replies = 0
        for r in approved:
            if hasattr(r, 'reply') and r.reply and hasattr(r, 'reply_at') and r.reply_at:
                try:
                    time_diff = r.reply_at - r.created_at
                    if time_diff < timedelta(hours=24):
                        fast_replies += 1
                except:
                    pass
        
        if fast_replies > 0:
            score_change += 10
            reasons.append(f"Fast replies ({fast_replies}) (+10)")
        
        # Resolutions (re-rating >= 4)
        resolutions = 0
        for r in approved:
            if hasattr(r, 're_rating') and r.re_rating and r.re_rating >= 4:
                resolutions += 1
        
        if resolutions > 0:
            score_change += 15
            reasons.append(f"Good resolutions ({resolutions}) (+15)")
        
        return score_change, reasons
    
    @staticmethod
    def calculate_trust_score(agency, reviews=None):
        """
        Calculate comprehensive trust score for an agency
        
        Args:
            agency: Agency object or dict with fields:
                - phone
                - email
                - tax_id
                - official_name
            reviews: List of Review objects (optional)
        
        Returns: dict with:
            - score: 0-100 final score
            - reasons: list of evaluation reasons
            - details: dict with component scores
        """
        score = 50  # Base score
        reasons = []
        details = {}
        
        # Phone validation
        phone = getattr(agency, 'phone', None) or agency.get('phone', '') if isinstance(agency, dict) else getattr(agency, 'phone', '')
        valid, msg, phone_score = TrustScoreCalculator.validate_phone(phone)
        score += phone_score
        details['phone'] = {'valid': valid, 'message': msg, 'score': phone_score}
        if valid:
            reasons.append(f"Valid phone format (+{phone_score})")
        else:
            reasons.append(f"Invalid phone: {msg} ({phone_score})")
        
        # Email validation
        email = getattr(agency, 'email', None) or agency.get('email', '') if isinstance(agency, dict) else getattr(agency, 'email', '')
        valid, msg, email_score = TrustScoreCalculator.validate_email(email)
        score += email_score
        details['email'] = {'valid': valid, 'message': msg, 'score': email_score}
        if valid:
            reasons.append(f"Valid email domain (+{email_score})")
        else:
            reasons.append(f"Invalid email: {msg} ({email_score})")
        
        # RNE validation
        tax_id = getattr(agency, 'tax_id', None) or agency.get('tax_id', '') if isinstance(agency, dict) else getattr(agency, 'tax_id', '')
        valid, msg, rne_score = TrustScoreCalculator.validate_rne(tax_id)
        score += rne_score
        details['rne'] = {'valid': valid, 'message': msg, 'score': rne_score}
        if valid:
            reasons.append(f"Valid RNE format (+{rne_score})")
        else:
            reasons.append(f"Invalid RNE: {msg} ({rne_score})")
        
        # Official name
        official_name = getattr(agency, 'official_name', None) or agency.get('official_name', '') if isinstance(agency, dict) else getattr(agency, 'official_name', '')
        has_name, msg, name_score = TrustScoreCalculator.validate_official_name(official_name)
        if has_name:
            score += name_score
            reasons.append(f"Official name verified (+{name_score})")
        details['official_name'] = {'has_name': has_name, 'score': name_score}
        
        # Reviews analysis
        if reviews:
            review_score, review_reasons = TrustScoreCalculator.calculate_from_reviews(reviews)
            score += review_score
            reasons.extend(review_reasons)
            details['reviews'] = {'score': review_score, 'count': len(reviews)}
        else:
            details['reviews'] = {'score': 0, 'count': 0}
        
        # Normalize score (0-100)
        final_score = min(100, max(0, score))
        
        return {
            'score': int(final_score),
            'reasons': reasons,
            'details': details,
            'base_score': 50
        }
