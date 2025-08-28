"""
Personalization Engine - Final Clean Version
Takes generic letters and personalizes them for each customer
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
        
        customer_context = {
            'name': customer.get('name', 'Valued Customer'),
            'age': customer.get('age', 'unknown'),
            'language': customer.get('preferred_language', 'English'),
            'balance': customer.get('account_balance', 0),
            'income': customer.get('income_level', 'unknown'),
            'digital_usage': customer.get('digital_logins_per_month', 0),
            'mobile_app': customer.get('mobile_app_usage', 'No'),
            'life_events': customer.get('recent_life_events', 'None'),
            'family': customer.get('family_status', 'unknown'),
            'accessibility': customer.get('accessibility_needs', 'None'),
            'employment': customer.get('employment_status', 'unknown')
        }
        
        if self.use_mock:
            return self._mock_personalization(letter_content, customer_context)
        
        return self._ai_personalization(letter_content, customer_context)
    
    def _ai_personalization(self, letter_content: str, customer: Dict) -> Dict:
        """Generate real AI personalization using Claude"""
        
        prompt = f"""You are a Lloyds Bank communication specialist. Completely rewrite this generic bank letter for this specific customer.

ORIGINAL LETTER:
{letter_content}

CRITICAL: You MUST preserve ALL of these key facts from the original letter:
- Any dates mentioned (effective dates, deadlines)
- ALL fee amounts (both old and new amounts)
- Specific times (like 11:59pm)
- Contact numbers
- Whether action is required or not
- The core message/purpose of the letter

CUSTOMER PROFILE:
- Name: {customer['name']}
- Age: {customer['age']}
- Preferred Language: {customer['language']}
- Account Balance: £{customer['balance']:,}
- Income Level: {customer['income']}
- Digital Engagement: {customer['digital_usage']} logins/month
- Uses Mobile App: {customer['mobile_app']}
- Recent Life Events: {customer['life_events']}
- Family Status: {customer['family']}
- Accessibility Needs: {customer['accessibility']}
- Employment: {customer['employment']}

REQUIREMENTS:
1. Write ALL content in {customer['language']} language
2. MUST include ALL specific facts from the original (dates, amounts, times, numbers)
3. Adjust tone based on age and profile
4. Consider their financial situation
5. Optimize for their digital engagement level
6. Acknowledge life events if relevant
7. Be extra clear if they have accessibility needs

Generate personalized versions for these channels:
- EMAIL: Full personalized email with ALL key information (max 300 words)
- SMS: Short but include critical facts (max 160 characters) 
- APP: In-app notification with key points (max 100 words)
- LETTER: Formal postal letter with complete information

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
            'email': f"Dear {name}, [Personalized email content in {language}]",
            'sms': f"Lloyds: Important update. Check app for details.",
            'app': f"Account update for {name}",
            'letter': f"Dear {name}, [Formal letter content]"
        }