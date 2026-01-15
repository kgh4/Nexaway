class ReviewGuardian:
    @staticmethod
    def is_suspicious(review_data):
        red_flags = 0
        
        # 1. Generic spam text
        spam_words = ['amazing', 'perfect', 'best ever', '5⭐⭐⭐⭐⭐']
        if sum(1 for word in spam_words if word in review_data['comment'].lower()) > 2:
            red_flags += 2
            
        # 2. Short review + 5⭐
        if len(review_data['comment']) < 20 and review_data['rating'] == 5:
            red_flags += 1
            
        # 3. Suspicious email patterns
        suspicious_domains = ['gmail.com', 'yahoo.com', 'hotmail.com','.tn','.fr']
        if any(domain in review_data['customer_email'] for domain in suspicious_domains):
            red_flags += 1
            
        return red_flags >= 3  # Suspicious!
    
    @staticmethod
    def calculate_trust_penalty(review):
        if ReviewGuardian.is_suspicious(review.to_dict()):
            return 5  # -5 trust points
        return 0
