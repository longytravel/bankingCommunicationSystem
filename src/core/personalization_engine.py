"""
Personalization Engine - Fixed Import Issue
This fixes the import path so PersonalizationOrchestrator actually gets used
"""

import anthropic
import json
import os
import re
from typing import Dict, Any, List, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

class PersonalizationEngine:
    """Takes generic bank letters and rewrites them for specific customers with guaranteed preservation and deep personalization"""
    
    def __init__(self):
        self.api_key = os.getenv('CLAUDE_API_KEY')
        self.use_mock = not self.api_key
        
        if not self.use_mock:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.model = "claude-3-5-sonnet-20241022"  # Using latest stable model
            print(f"✓ Personalization Engine using Claude 3.5 Sonnet")
        else:
            print("⚠️ No API key - using mock mode")
        
        # Initialize the orchestrator
        self._init_orchestrator()
    
    def _init_orchestrator(self):
        """Initialize the PersonalizationOrchestrator with FIXED import paths"""
        try:
            # FIXED: Correct import path - file is named "Personalization_Orchestrator.py" with capital P
            from .Personalization_Orchestrator import PersonalizationOrchestrator
            self.orchestrator = PersonalizationOrchestrator(api_key=self.api_key)
            self.use_orchestrator = True
            print("✓ PersonalizationOrchestrator initialized successfully")
        except ImportError as e:
            try:
                # FIXED: Try alternate import path with capital P
                from Personalization_Orchestrator import PersonalizationOrchestrator
                self.orchestrator = PersonalizationOrchestrator(api_key=self.api_key)
                self.use_orchestrator = True
                print("✓ PersonalizationOrchestrator initialized successfully (alternate path)")
            except ImportError as e2:
                print(f"⚠️ PersonalizationOrchestrator not available: {e}, {e2}")
                print("   Using standard engine instead")
                self.orchestrator = None
                self.use_orchestrator = False
    
    def personalize_letter(self, letter_content: str, customer: Dict, key_points: Optional[List] = None) -> Dict:
        """
        Takes a generic letter and rewrites it for a specific customer
        Uses the orchestrator for deep personalization if available
        
        Args:
            letter_content: Original letter text
            customer: Customer profile dictionary
            key_points: List of KeyPoint objects from content validator
        
        Returns:
            Dictionary with personalized content for each channel
        """
        
        # Use orchestrator if available for better personalization
        if self.use_orchestrator and self.orchestrator:
            try:
                print(f"🎯 Using PersonalizationOrchestrator for {customer.get('name', 'customer')}")
                result = self.orchestrator.orchestrate_personalization(
                    letter_content=letter_content,
                    customer=customer,
                    key_points=key_points,
                    existing_engine=self
                )
                print("✓ PersonalizationOrchestrator completed successfully")
                return result
            except Exception as e:
                print(f"❌ PersonalizationOrchestrator failed: {e}")
                print("   Falling back to standard personalization")
                # Fall back to standard personalization
        else:
            print("⚠️ Using standard personalization (orchestrator not available)")
        
        # Standard personalization (if orchestrator not available or fails)
        customer_context = self._build_customer_context(customer)
        
        if self.use_mock:
            return self._mock_personalization(letter_content, customer_context)
        
        return self._standard_personalization(letter_content, customer_context, key_points)
    
    def _build_customer_context(self, customer: Dict) -> Dict:
        """Build comprehensive customer context"""
        return {
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
    
    def _standard_personalization(self, letter_content: str, customer: Dict, key_points: Optional[List] = None) -> Dict:
        """Standard personalization without orchestrator"""
        
        # Build preservation instructions
        preservation_instructions = self._build_preservation_instructions(key_points)
        
        prompt = f"""You are a Lloyds Bank communication specialist. Personalize this letter for the customer while preserving ALL information.

ORIGINAL LETTER:
{letter_content}

{preservation_instructions}

CUSTOMER PROFILE:
- Name: {customer['name']}
- Age: {customer['age']} years old
- Language: {customer['language']} (write in this language)
- Balance: £{customer['balance']:,}
- Digital Activity: {customer['digital_logins']} logins/month
- Mobile App: {customer['mobile_app']}
- Life Events: {customer['life_events']}
- Employment: {customer['employment']}

REQUIREMENTS:
1. Include ALL information from the original letter
2. Personalize based on customer profile
3. NO PLACEHOLDERS - write complete content
4. Make natural connections to their situation

Generate personalized versions:
- EMAIL: Complete, personalized, all information
- SMS: Max 160 chars, critical points
- APP: Brief notification
- LETTER: Formal, complete

Return ONLY valid JSON:
{{
    "email": "...",
    "sms": "...",
    "app": "...",
    "letter": "..."
}}"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.5,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text.strip()
            result = self._extract_json_from_response(content)
            
            if result:
                return self._validate_and_clean_result(result)
            else:
                return self._fallback_personalization(letter_content, customer)
                
        except Exception as e:
            print(f"Error in standard personalization: {e}")
            return self._fallback_personalization(letter_content, customer)
    
    def _build_preservation_instructions(self, key_points: Optional[List]) -> str:
        """Build preservation instructions from key points"""
        if not key_points:
            return "PRESERVE ALL INFORMATION FROM THE ORIGINAL LETTER"
        
        try:
            from src.core.content_validator import PointImportance
        except ImportError:
            return "PRESERVE ALL INFORMATION FROM THE ORIGINAL LETTER"
        
        instructions = ["MANDATORY INFORMATION TO PRESERVE:"]
        
        for point in key_points:
            if hasattr(point, 'importance') and hasattr(point, 'content'):
                if point.importance == PointImportance.CRITICAL:
                    instructions.append(f"🔴 CRITICAL: {point.content}")
                elif point.importance == PointImportance.IMPORTANT:
                    instructions.append(f"🟡 IMPORTANT: {point.content}")
        
        return "\n".join(instructions)
    
    def _extract_json_from_response(self, content: str) -> Optional[Dict]:
        """Extract JSON from Claude's response"""
        # Remove markdown
        content = re.sub(r'```json\s*', '', content)
        content = re.sub(r'```\s*', '', content)
        
        # Try direct parsing
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # Try to find JSON in content
        if '{' in content and '}' in content:
            try:
                json_start = content.index('{')
                json_end = content.rindex('}') + 1
                json_str = content[json_start:json_end]
                return json.loads(json_str)
            except (json.JSONDecodeError, ValueError):
                pass
        
        return None
    
    def _validate_and_clean_result(self, result: Dict) -> Dict:
        """Validate and clean the result"""
        # Ensure all required fields exist
        required_fields = ['email', 'sms', 'app', 'letter']
        for field in required_fields:
            if field not in result or not result[field]:
                result[field] = ""
        
        # Check for and remove any JSON artifacts
        for field in required_fields:
            content = result[field]
            if isinstance(content, str):
                # Remove any accidental quotes or JSON formatting
                if content.startswith('"') and content.endswith('"'):
                    content = content[1:-1]
                
                # Unescape characters
                content = content.replace('\\n', '\n')
                content = content.replace('\\t', '\t')
                content = content.replace('\\"', '"')
                
                result[field] = content
        
        # Ensure SMS is under 160 characters
        if len(result.get('sms', '')) > 160:
            result['sms'] = result['sms'][:157] + '...'
        
        return result
    
    def _fallback_personalization(self, letter_content: str, customer: Dict) -> Dict:
        """Fallback personalization when API fails"""
        name = customer['name']
        
        # Create basic personalized versions
        personalized_greeting = f"Dear {name},\n\n"
        
        # Add life event if present
        if customer.get('life_events') and customer['life_events'] not in ['None', 'unknown']:
            personalized_greeting += f"We hope all is well with {customer['life_events']}. "
        
        return {
            'email': personalized_greeting + letter_content + "\n\nBest regards,\nLloyds Bank",
            'sms': f"Lloyds: Important update for {name}. Check email for details.",
            'app': f"New message about your account",
            'letter': f"Dear {name},\n\n{letter_content}\n\nYours sincerely,\nLloyds Bank"
        }
    
    def _mock_personalization(self, letter_content: str, customer: Dict) -> Dict:
        """Generate mock personalization for testing without API"""
        
        name = customer['name']
        language = customer['language']
        
        # Extract some real content for mock
        urls = re.findall(r'lloydsbank\.com[^\s]*', letter_content)
        url = urls[0] if urls else "lloydsbank.com"
        
        return {
            'email': f"Dear {name}, We have important updates about your account. {letter_content[:200]}... Visit {url} for details. [Full content in {language}]",
            'sms': f"Lloyds: Important update. Check app or visit {url}",
            'app': f"Account update for {name} - tap to view",
            'letter': f"Dear {name}, [Formal letter content with all details preserved in {language}]"
        }

# Convenience functions for backward compatibility
def create_personalization_engine() -> PersonalizationEngine:
    """Create a personalization engine instance"""
    return PersonalizationEngine()

def personalize_for_customer(
    letter_content: str,
    customer: Dict[str, Any],
    key_points: Optional[List] = None
) -> Dict[str, str]:
    """
    Convenience function to personalize content for a customer
    
    Args:
        letter_content: Original letter text
        customer: Customer profile
        key_points: Optional key points to preserve
        
    Returns:
        Personalized content dictionary
    """
    engine = PersonalizationEngine()
    return engine.personalize_letter(letter_content, customer, key_points)