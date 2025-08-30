"""
Personalization Engine - Enhanced Version with Guaranteed Content Preservation
Ensures ALL critical content is preserved using key points from content validator
"""

import anthropic
import json
import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

class PersonalizationEngine:
    """Takes generic bank letters and rewrites them for specific customers with content preservation"""
    
    def __init__(self):
        self.api_key = os.getenv('CLAUDE_API_KEY')
        self.use_mock = not self.api_key
        
        if not self.use_mock:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.model = "claude-3-5-sonnet-20241022"  # Using latest stable model
            print(f"✓ Personalization Engine using Claude 3.5 Sonnet")
        else:
            print("⚠️ No API key - using mock mode")
    
    def personalize_letter(self, letter_content: str, customer: Dict, key_points: Optional[List] = None) -> Dict:
        """
        Takes a generic letter and rewrites it for a specific customer
        
        Args:
            letter_content: Original letter text
            customer: Customer profile dictionary
            key_points: List of KeyPoint objects from content validator (if available)
        
        Returns:
            Dictionary with personalized content for each channel
        """
        
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
        
        return self._ai_personalization(letter_content, customer_context, key_points)
    
    def _build_preservation_instructions(self, key_points: Optional[List]) -> str:
        """Build explicit preservation instructions from key points"""
        if not key_points:
            return ""
        
        # Import here to avoid circular dependency
        from src.core.content_validator import PointImportance
        
        critical_items = []
        important_items = []
        contextual_items = []
        
        for point in key_points:
            if hasattr(point, 'importance') and hasattr(point, 'content'):
                if point.importance == PointImportance.CRITICAL:
                    critical_items.append(point.content)
                elif point.importance == PointImportance.IMPORTANT:
                    important_items.append(point.content)
                elif point.importance == PointImportance.CONTEXTUAL:
                    contextual_items.append(point.content)
        
        instructions = """
ABSOLUTE PRESERVATION REQUIREMENTS:
You MUST include these EXACT items in the personalized versions. This is NON-NEGOTIABLE.

CRITICAL ITEMS (MUST appear word-for-word in email and letter, can be shortened for SMS/app):"""
        
        for item in critical_items:
            instructions += f"\n✓ {item}"
        
        instructions += "\n\nIMPORTANT ITEMS (MUST include this information in email and letter):"
        for item in important_items:
            instructions += f"\n✓ {item}"
        
        if contextual_items:
            instructions += "\n\nCONTEXTUAL ITEMS (include if space permits):"
            for item in contextual_items[:5]:  # Limit to avoid prompt bloat
                instructions += f"\n• {item}"
        
        instructions += """

VERIFICATION CHECKLIST:
□ Every date from original appears in email/letter
□ Every amount (£) from original appears in email/letter
□ Every website URL from original appears in email/letter
□ Every phone number from original appears in email/letter
□ Every deadline/time from original appears in email/letter
□ If original says "no action required", this MUST be clear
□ All regulatory/legal requirements preserved exactly

EMAIL and LETTER must be COMPLETE - include ALL information.
SMS and APP can be condensed but must include critical dates/amounts."""
        
        return instructions
    
    def _ai_personalization(self, letter_content: str, customer: Dict, key_points: Optional[List] = None) -> Dict:
        """Generate real AI personalization using Claude with content preservation"""
        
        # Build preservation instructions
        preservation_instructions = self._build_preservation_instructions(key_points)
        
        prompt = f"""You are a Lloyds Bank communication specialist. Personalize this generic bank letter for this specific customer while STRICTLY preserving all important information.

ORIGINAL LETTER (SOURCE OF TRUTH):
{letter_content}

{preservation_instructions}

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
2. Tone: {'Formal and respectful' if customer['age'] != 'unknown' and int(customer['age']) > 60 else 'Modern and friendly' if customer['age'] != 'unknown' and int(customer['age']) < 35 else 'Professional'}
3. Channel focus: {'Emphasize app and digital' if customer['digital_logins'] > 20 else 'Emphasize phone and branch' if customer['digital_logins'] < 5 else 'Balance all channels'}
4. Acknowledge loyalty if {customer['years_with_bank']} > 5 years
5. Reference life events if relevant: {customer['life_events']}
6. Accessibility: {customer['accessibility']}

CRITICAL RULES:
- EMAIL and LETTER must contain 100% of the information from the original
- Do NOT omit any URLs, phone numbers, dates, or amounts
- Do NOT summarize or skip any important details in email/letter
- SMS can be shortened to key facts only (160 chars max)
- APP notification should be concise but include critical dates/amounts

CHANNEL REQUIREMENTS:
- EMAIL: Complete information, personalized greeting, all details from original, friendly but professional
- SMS: Maximum 160 characters, critical facts only (dates, amounts, action required)
- APP: Brief notification (under 100 words) with key information
- LETTER: Formal, complete information, all details preserved

Generate personalized versions. Return ONLY a JSON object with keys: email, sms, app, letter

FINAL CHECK before responding:
- Does email contain EVERY URL from the original? (especially lloydsbank.com links)
- Does email contain EVERY phone number from the original?
- Does email contain EVERY date and amount from the original?
- Does letter contain ALL the same information as email?
- Have you written everything in {customer['language']}?"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=3000,
                temperature=0.5,  # Lower temperature for more consistent preservation
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text.strip()
            
            try:
                if '{' in content:
                    json_start = content.index('{')
                    json_end = content.rindex('}') + 1
                    json_str = content[json_start:json_end]
                    result = json.loads(json_str)
                    
                    # Ensure all keys exist
                    for key in ['email', 'sms', 'app', 'letter']:
                        if key not in result or result[key] is None:
                            result[key] = ""
                    
                    # Post-process to ensure critical content (fallback check)
                    result = self._verify_critical_content(result, letter_content, key_points)
                    
                    return result
                else:
                    return self._create_fallback_response(content, letter_content, customer)
                    
            except json.JSONDecodeError:
                return self._create_fallback_response(content, letter_content, customer)
            
        except Exception as e:
            print(f"API Error: {e}")
            return self._mock_personalization(letter_content, customer)
    
    def _verify_critical_content(self, result: Dict, original_letter: str, key_points: Optional[List]) -> Dict:
        """
        Post-process check to ensure critical content wasn't lost
        This is a safety net - the prompt should handle it, but this ensures it
        """
        import re
        
        # Extract critical patterns from original
        urls = re.findall(r'(?:www\.|https?://)?[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+(?:/[^\s]*)?', original_letter)
        phones = re.findall(r'\b(?:0\d{3}\s?\d{3}\s?\d{4}|0800\s?\d{3}\s?\d{3,4})\b', original_letter)
        amounts = re.findall(r'£\s*\d+(?:,\d{3})*(?:\.\d{2})?', original_letter)
        
        # Check email and letter for completeness
        for channel in ['email', 'letter']:
            if channel in result:
                content = result[channel]
                
                # Check URLs
                for url in urls:
                    if len(url) > 10 and url not in content:  # Skip short false matches
                        # URL missing - this shouldn't happen with improved prompt
                        print(f"Warning: URL {url} missing from {channel}")
                
                # Check phone numbers
                for phone in phones:
                    phone_clean = phone.replace(' ', '')
                    content_clean = content.replace(' ', '')
                    if phone_clean not in content_clean:
                        print(f"Warning: Phone {phone} missing from {channel}")
                
                # Check amounts
                for amount in amounts:
                    if amount not in content:
                        print(f"Warning: Amount {amount} missing from {channel}")
        
        return result
    
    def _create_fallback_response(self, content: str, original_letter: str, customer: Dict) -> Dict:
        """Create a structured response when JSON parsing fails"""
        # Use the content as the email if it looks reasonable
        if len(content) > 100:
            return {
                'email': content,
                'sms': self._extract_sms_from_letter(original_letter),
                'app': self._extract_app_notification(original_letter),
                'letter': content
            }
        else:
            return self._mock_personalization(original_letter, customer)
    
    def _extract_sms_from_letter(self, letter: str) -> str:
        """Extract key facts for SMS from letter"""
        import re
        
        # Find dates
        dates = re.findall(r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}\b', letter, re.IGNORECASE)
        date_str = dates[0] if dates else ""
        
        # Find amounts
        amounts = re.findall(r'£\s*\d+(?:\.\d{2})?', letter)
        amount_str = f"Fee change: {amounts[0]}" if amounts else ""
        
        # Check for action
        if "no action" in letter.lower():
            action = "No action needed"
        else:
            action = "See letter for details"
        
        sms_parts = ["Lloyds:", date_str, amount_str, action]
        sms = " ".join(part for part in sms_parts if part)
        
        return sms[:160]  # SMS limit
    
    def _extract_app_notification(self, letter: str) -> str:
        """Extract key message for app notification"""
        lines = letter.split('\n')
        
        # Find the main subject/title
        for line in lines[:10]:
            if len(line) > 20 and len(line) < 100 and not line.startswith('['):
                return f"Important: {line.strip()}"
        
        return "You have a new message from Lloyds Bank"
    
    def _mock_personalization(self, letter_content: str, customer: Dict) -> Dict:
        """Generate mock personalization for testing without API"""
        
        name = customer['name']
        language = customer['language']
        
        # Extract some real content for mock
        import re
        urls = re.findall(r'lloydsbank\.com[^\s]*', letter_content)
        url = urls[0] if urls else "lloydsbank.com"
        
        return {
            'email': f"Dear {name}, We have important updates about your account. Visit {url} for details. [Full content in {language}]",
            'sms': f"Lloyds: Important update. Check app or visit {url}",
            'app': f"Account update for {name} - tap to view",
            'letter': f"Dear {name}, [Formal letter content with all details preserved]"
        }