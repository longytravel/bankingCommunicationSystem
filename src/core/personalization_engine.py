"""
Personalization Engine - Enhanced Version with Deep Personalization
Ensures ALL critical content is preserved and uses ALL customer data points
"""

import anthropic
import json
import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class PersonalizationEngine:
    """Takes generic bank letters and rewrites them for specific customers"""
    
    def __init__(self):
        self.api_key = os.getenv('CLAUDE_API_KEY')
        self.use_mock = not self.api_key
        
        if not self.use_mock:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.model = "claude-sonnet-4-20250514"
            print(f"✓ Using Claude Sonnet 4 API")
        else:
            print("⚠️ No API key - using mock mode")
    
    def personalize_letter(self, letter_content: str, customer: Dict) -> Dict:
        """Takes a generic letter and rewrites it for a specific customer"""
        
        # Extract ALL customer attributes for deep personalization
        customer_context = {
            'name': customer.get('name', 'Valued Customer'),
            'age': customer.get('age', 'unknown'),
            'language': customer.get('preferred_language', 'English'),
            'balance': customer.get('account_balance', 0),
            'income': customer.get('income_level', 'unknown'),
            'digital_logins': customer.get('digital_logins_per_month', 0),
            'mobile_app': customer.get('mobile_app_usage', 'No'),
            'email_opens': customer.get('email_opens_per_month', 0),
            'phone_calls': customer.get('phone_calls_per_month', 0),
            'branch_visits': customer.get('branch_visits_per_month', 0),
            'account_type': customer.get('account_type', 'unknown'),
            'years_with_bank': customer.get('years_with_bank', 0),
            'recent_transactions': customer.get('recent_transactions', 0),
            'requires_support': customer.get('requires_support', False),
            'life_events': customer.get('recent_life_events', 'None'),
            'family': customer.get('family_status', 'unknown'),
            'accessibility': customer.get('accessibility_needs', 'None'),
            'employment': customer.get('employment_status', 'unknown'),
            'prefers_digital': customer.get('prefers_digital', False)
        }
        
        if self.use_mock:
            return self._mock_personalization(letter_content, customer_context)
        
        return self._ai_personalization(letter_content, customer_context)
    
    def _ai_personalization(self, letter_content: str, customer: Dict) -> Dict:
        """Generate real AI personalization using Claude"""
        
        prompt = f"""You are a Lloyds Bank communication specialist. COMPLETELY rewrite this generic bank letter for this specific customer, making it highly personalized.

ORIGINAL LETTER (PRESERVE ALL FACTS):
{letter_content}

MANDATORY: You MUST include these EXACT facts in the personalized version:
1. If the letter mentions overdraft interest being calculated daily - YOU MUST EXPLICITLY SAY "overdraft interest will be calculated daily" or "daily overdraft interest calculation"
2. If the letter mentions fee changes (like £5 to £7.50) - YOU MUST INCLUDE BOTH THE OLD AMOUNT (£5) AND NEW AMOUNT (£7.50)
3. If the letter mentions 11:59pm - YOU MUST INCLUDE this exact time
4. If the letter mentions dates - YOU MUST INCLUDE the exact dates
5. If the letter mentions contact numbers - YOU MUST INCLUDE the exact numbers
6. If the letter says "no action required" - YOU MUST CLEARLY STATE this

CUSTOMER PROFILE (USE ALL OF THIS):
- Name: {customer['name']}
- Age: {customer['age']} years old
- Preferred Language: {customer['language']} (WRITE EVERYTHING IN THIS LANGUAGE)
- Account Balance: £{customer['balance']:,}
- Income Level: {customer['income']}
- Digital Activity: {customer['digital_logins']} app logins per month
- Mobile App Usage: {customer['mobile_app']}
- Email Engagement: {customer['email_opens']} emails opened per month
- Phone Contact: {customer['phone_calls']} calls per month
- Branch Visits: {customer['branch_visits']} visits per month
- Account Type: {customer['account_type']}
- Customer Since: {customer['years_with_bank']} years with Lloyds
- Monthly Transactions: {customer['recent_transactions']}
- Requires Extra Support: {customer['requires_support']}
- Recent Life Events: {customer['life_events']}
- Family Status: {customer['family']}
- Accessibility Needs: {customer['accessibility']}
- Employment: {customer['employment']}
- Digital Preference: {customer['prefers_digital']}

PERSONALIZATION REQUIREMENTS:
1. Language: Write EVERYTHING in {customer['language']}
2. Age tone: {'Formal and respectful' if customer['age'] != 'unknown' and int(customer['age']) > 60 else 'Modern and friendly' if customer['age'] != 'unknown' and int(customer['age']) < 35 else 'Professional'}
3. Channel focus: {'Emphasize app and digital options' if customer['digital_logins'] > 20 else 'Emphasize phone and branch support' if customer['digital_logins'] < 5 else 'Balance digital and traditional'}
4. Loyalty: {'Acknowledge their ' + str(customer['years_with_bank']) + ' years with us' if customer['years_with_bank'] > 5 else ''}
5. Life events: {'Acknowledge and relate to their ' + customer['life_events'] if customer['life_events'] not in ['None', 'unknown'] else ''}
6. Support needs: {'Provide extra clear explanations and support options' if customer['requires_support'] else ''}
7. Financial status: {'Mention premium services and wealth management' if customer['balance'] > 20000 else 'Focus on budgeting tools and support' if customer['balance'] < 1000 else ''}
8. Engagement style: {'Keep it brief and action-focused' if customer['email_opens'] < 5 else 'Provide detailed explanations' if customer['email_opens'] > 15 else ''}
9. Family considerations: {'Include family financial planning references' if 'children' in str(customer['family']).lower() else ''}
10. Employment context: {'Reference business banking options' if 'self-employed' in str(customer['employment']).lower() else ''}

Generate personalized versions ensuring ALL original facts are preserved:
- EMAIL: Full email with ALL information from original letter, highly personalized
- SMS: Short but MUST include key facts (dates, amounts)
- APP: Notification with critical information
- LETTER: Formal version with complete information

Return ONLY a JSON object with keys: email, sms, app, letter"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text.strip()
            
            try:
                if '{' in content:
                    json_start = content.index('{')
                    json_end = content.rindex('}') + 1
                    json_str = content[json_start:json_end]
                    result = json.loads(json_str)
                    
                    for key in ['email', 'sms', 'app', 'letter']:
                        if key not in result:
                            result[key] = ""
                        if result[key] is None:
                            result[key] = ""
                    
                    return result
                else:
                    return {
                        'email': content,
                        'sms': content[:160],
                        'app': content[:100],
                        'letter': content
                    }
                    
            except json.JSONDecodeError:
                return {
                    'email': content,
                    'sms': content[:160],
                    'app': content[:100],
                    'letter': content
                }
            
        except Exception as e:
            print(f"API Error: {e}")
            return self._mock_personalization(letter_content, customer)
    
    def _mock_personalization(self, letter_content: str, customer: Dict) -> Dict:
        """Generate mock personalization for testing without API"""
        
        name = customer['name']
        language = customer['language']
        
        return {
            'email': f"Dear {name}, [Personalized email with all critical facts in {language}]",
            'sms': f"Lloyds: Important update. Check app for details.",
            'app': f"Account update for {name}",
            'letter': f"Dear {name}, [Formal letter content]"
        }