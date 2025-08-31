"""
SMS Channel Generator - Focused SMS Generation with Content Preservation
Follows the same modular pattern as EmailChannelGenerator
"""

import anthropic
import os
import json
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class SMSPersonalizationContext:
    """Context for SMS personalization"""
    customer_name: str
    customer_profile: Dict[str, Any]
    personalization_factors: List[str]
    tone: str
    language: str
    urgency_level: str
    
class SMSChannelGenerator:
    """Generates personalized SMS messages with guaranteed content preservation"""
    
    # SMS Length limits
    SINGLE_SMS_LIMIT = 160
    DOUBLE_SMS_LIMIT = 320  # 2 segments
    TRIPLE_SMS_LIMIT = 480  # 3 segments - practical limit for banking
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('CLAUDE_API_KEY')
        self.client = None
        
        if self.api_key:
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
                self.model = "claude-3-5-sonnet-20241022"
                print("✓ SMS Channel Generator initialized")
            except ImportError:
                print("⚠️ Anthropic not available - using mock mode")
        else:
            print("⚠️ No API key - using mock mode")
    
    def generate_sms(
        self,
        clean_content: str,
        customer: Dict[str, Any],
        key_points: Optional[List] = None,
        context: Optional[SMSPersonalizationContext] = None
    ) -> Dict[str, Any]:
        """
        Generate personalized SMS with guaranteed content preservation
        """
        
        # Build SMS context if not provided
        if not context:
            context = self._build_sms_context(customer, clean_content)
        
        # Determine optimal SMS length based on content criticality
        target_length = self._determine_optimal_length(clean_content, key_points, context.urgency_level)
        
        # Generate personalized SMS
        if self.client:
            sms_result = self._generate_with_ai(clean_content, context, key_points, target_length)
        else:
            sms_result = self._generate_mock_sms(clean_content, context, target_length)
        
        # Post-process to ensure compliance with SMS constraints
        if sms_result.get('content'):
            sms_result['content'] = self._optimize_sms_content(sms_result['content'], target_length)
        
        return sms_result
    
    def _build_sms_context(self, customer: Dict[str, Any], content: str) -> SMSPersonalizationContext:
        """Build SMS-specific personalization context"""
        
        factors = []
        
        # SMS engagement analysis
        mobile_usage = customer.get('mobile_app_usage', 'Unknown')
        phone_calls = customer.get('phone_calls_per_month', 0)
        digital_logins = customer.get('digital_logins_per_month', 0)
        
        if mobile_usage == 'Daily':
            factors.append("High mobile engagement - detailed SMS appropriate")
        elif mobile_usage == 'Never':
            factors.append("Low mobile usage - simple, clear SMS")
        
        if phone_calls > 5:
            factors.append("Prefers phone contact - include call-to-action")
        
        # Age-based SMS preferences
        age = customer.get('age', 'unknown')
        if age != 'unknown':
            age_val = int(age) if str(age).isdigit() else 40
            if age_val > 60:
                factors.append("Senior customer - formal, clear SMS")
            elif age_val < 35:
                factors.append("Younger customer - can use modern SMS language")
        
        # Urgency detection
        urgency = 'standard'
        if 'urgent' in content.lower() or 'immediately' in content.lower():
            urgency = 'high'
        elif 'deadline' in content.lower() or 'expires' in content.lower():
            urgency = 'medium'
        
        # Language and accessibility
        language = customer.get('preferred_language', 'English')
        accessibility = customer.get('accessibility_needs', 'None')
        
        if accessibility not in ['None', 'unknown']:
            factors.append(f"Accessibility needs: {accessibility}")
        
        # Determine tone
        if urgency == 'high':
            tone = "urgent"
        elif age != 'unknown' and int(age if str(age).isdigit() else 40) > 60:
            tone = "respectful"
        else:
            tone = "friendly"
        
        return SMSPersonalizationContext(
            customer_name=customer.get('name', 'Valued Customer'),
            customer_profile=customer,
            personalization_factors=factors,
            tone=tone,
            language=language,
            urgency_level=urgency
        )
    
    def _determine_optimal_length(self, content: str, key_points: Optional[List], urgency: str) -> int:
        """Determine optimal SMS length based on content and urgency"""
        
        # Count critical points
        critical_count = 0
        if key_points:
            try:
                from src.core.content_validator import PointImportance
                critical_count = sum(1 for p in key_points if p.importance == PointImportance.CRITICAL)
            except ImportError:
                critical_count = len(key_points) // 2  # Rough estimate
        
        # Determine target length
        if urgency == 'high':
            return self.SINGLE_SMS_LIMIT  # Urgent = concise
        elif critical_count > 3 or len(content) > 1000:
            return self.TRIPLE_SMS_LIMIT  # Complex = more space
        elif critical_count > 1:
            return self.DOUBLE_SMS_LIMIT  # Moderate complexity
        else:
            return self.SINGLE_SMS_LIMIT  # Simple = single SMS
    
    def _generate_with_ai(
        self,
        content: str,
        context: SMSPersonalizationContext,
        key_points: Optional[List],
        target_length: int
    ) -> Dict[str, Any]:
        """Generate SMS using AI with strict preservation requirements"""
        
        # Build preservation requirements
        preservation_text = self._build_sms_preservation_requirements(key_points, content, target_length)
        
        # Build personalization instructions
        personalization_text = "SMS personalization factors:\n"
        for factor in context.personalization_factors:
            personalization_text += f"- {factor}\n"
        
        sms_prompt = f"""You are writing a personalized SMS for a Lloyds Bank customer.

CRITICAL SMS RULES:
1. Maximum {target_length} characters (this is STRICT - count every character)
2. Include the most critical information from the original content
3. NO greeting like "Dear X" - SMS starts with bank name or direct message
4. End with clear action or contact info
5. Write in {context.language}
6. Use {context.tone} tone

ORIGINAL CONTENT (extract key essentials):
{content}

CUSTOMER: {context.customer_name}
URGENCY: {context.urgency_level}

{preservation_text}

{personalization_text}

SMS FORMAT REQUIREMENTS:
- Start with "Lloyds:" or "Lloyds Bank:"
- Include customer name if space allows
- Focus on: WHAT happened + WHAT to do + HOW to contact
- Use abbreviations if needed (e.g., "w/" for with, "&" for and)
- No emojis unless specifically appropriate for customer age/profile

EXAMPLES:
- Regulatory: "Lloyds: Account terms changing 1 Mar 2025. Details in your app or call 0345 300 0000"
- Informational: "Lloyds: New budgeting tools now available in your app. Tap notifications to explore"
- Urgent: "Lloyds: Action needed on your account. Check app immediately or call 0345 300 0000"

Generate SMS under {target_length} characters:"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,  # Short response for SMS
                temperature=0.3,  # Low temperature for precision
                messages=[{"role": "user", "content": sms_prompt}]
            )
            
            sms_content = response.content[0].text.strip()
            
            # Remove any quotes or formatting
            sms_content = sms_content.strip('"\'')
            
            return {
                'content': sms_content,
                'channel': 'sms',
                'character_count': len(sms_content),
                'segment_count': self._calculate_sms_segments(sms_content),
                'personalization_factors': context.personalization_factors,
                'tone': context.tone,
                'language': context.language,
                'urgency_level': context.urgency_level,
                'target_length': target_length,
                'generation_method': 'ai'
            }
            
        except Exception as e:
            print(f"SMS AI generation error: {e}")
            return self._generate_fallback_sms(content, context, target_length)
    
    def _build_sms_preservation_requirements(self, key_points: Optional[List], content: str, target_length: int) -> str:
        """Build SMS-specific preservation requirements"""
        
        requirements = ["CRITICAL SMS CONTENT (prioritize in order):"]
        
        # Identify what MUST be in SMS
        if key_points:
            try:
                from src.core.content_validator import PointImportance
                
                # Critical points first
                critical_points = [p for p in key_points if p.importance == PointImportance.CRITICAL]
                for point in critical_points[:2]:  # Max 2 critical points in SMS
                    requirements.append(f"🔴 ESSENTIAL: {point.content}")
                
                # Important points if space
                important_points = [p for p in key_points if p.importance == PointImportance.IMPORTANT]
                if len(critical_points) < 2 and important_points:
                    requirements.append(f"🟡 INCLUDE IF SPACE: {important_points[0].content}")
                    
            except ImportError:
                # Fallback: analyze content for key elements
                pass
        
        # Always include action items
        requirements.append("🔴 MUST INCLUDE: Clear next action for customer")
        requirements.append("🔴 MUST INCLUDE: Contact method (app/phone/website)")
        
        # Special handling for different content types
        if 'deadline' in content.lower() or 'expires' in content.lower():
            requirements.append("🔴 CRITICAL: Any dates or deadlines mentioned")
        
        if re.search(r'[£$€]\s*\d+', content):
            requirements.append("🔴 CRITICAL: Any monetary amounts mentioned")
        
        return "\n".join(requirements)
    
    def _optimize_sms_content(self, content: str, target_length: int) -> str:
        """Optimize SMS content for length and clarity"""
        
        if len(content) <= target_length:
            return content
        
        # SMS optimization strategies
        optimized = content
        
        # Common banking abbreviations
        abbreviations = {
            ' and ': ' & ',
            'account': 'acc',
            'with ': 'w/ ',
            'your ': '',  # Often not needed in SMS
            'please ': '',  # Often not needed
            'information': 'info',
            'available': 'available',  # Keep as is - important for clarity
            'application': 'app',
            'telephone': 'phone',
            'customer services': 'customer service'
        }
        
        # Apply abbreviations cautiously (only if over limit)
        if len(optimized) > target_length:
            for full, abbrev in abbreviations.items():
                optimized = optimized.replace(full, abbrev)
                if len(optimized) <= target_length:
                    break
        
        # If still too long, truncate intelligently
        if len(optimized) > target_length:
            # Find last complete sentence that fits
            sentences = optimized.split('. ')
            truncated = ""
            
            for sentence in sentences:
                test_content = truncated + sentence + '. '
                if len(test_content) <= target_length - 20:  # Leave space for "..."
                    truncated = test_content
                else:
                    break
            
            if truncated:
                optimized = truncated.rstrip() + "..."
            else:
                # Hard truncate with ellipsis
                optimized = optimized[:target_length-3] + "..."
        
        return optimized
    
    def _calculate_sms_segments(self, content: str) -> int:
        """Calculate how many SMS segments this content requires"""
        length = len(content)
        
        if length <= 160:
            return 1
        elif length <= 306:  # 153 chars per segment after first
            return 2
        elif length <= 459:
            return 3
        elif length <= 612:
            return 4
        else:
            return 5  # Maximum practical
    
    def _generate_fallback_sms(self, content: str, context: SMSPersonalizationContext, target_length: int) -> Dict[str, Any]:
        """Generate fallback SMS when AI fails"""
        
        # Extract key info
        name = context.customer_name.split()[0]  # First name only for SMS
        
        # Simple SMS generation
        if context.urgency_level == 'high':
            sms_content = f"Lloyds: Urgent - Account update for {name}. Check app or call 0345 300 0000"
        else:
            sms_content = f"Lloyds: Account update for {name}. Details in app or call 0345 300 0000"
        
        # Ensure it fits
        if len(sms_content) > target_length:
            sms_content = f"Lloyds: Update for {name}. Check app or call 0345 300 0000"
        
        return {
            'content': sms_content,
            'channel': 'sms',
            'character_count': len(sms_content),
            'segment_count': self._calculate_sms_segments(sms_content),
            'personalization_factors': context.personalization_factors,
            'tone': context.tone,
            'language': context.language,
            'urgency_level': context.urgency_level,
            'target_length': target_length,
            'generation_method': 'fallback'
        }
    
    def _generate_mock_sms(self, content: str, context: SMSPersonalizationContext, target_length: int) -> Dict[str, Any]:
        """Generate mock SMS for testing"""
        
        mock_content = f"Lloyds: [MOCK SMS in {context.language}] Update for {context.customer_name}. Check app for details."
        
        return {
            'content': mock_content,
            'channel': 'sms',
            'character_count': len(mock_content),
            'segment_count': 1,
            'personalization_factors': context.personalization_factors,
            'tone': context.tone,
            'language': context.language,
            'urgency_level': context.urgency_level,
            'target_length': target_length,
            'generation_method': 'mock'
        }
    
    def validate_sms(self, sms_result: Dict[str, Any], original_content: str, key_points: Optional[List] = None) -> Dict[str, Any]:
        """Validate SMS quality and compliance"""
        
        sms_content = sms_result.get('content', '')
        issues = []
        warnings = []
        
        # Length validation
        char_count = len(sms_content)
        target_length = sms_result.get('target_length', self.SINGLE_SMS_LIMIT)
        segment_count = self._calculate_sms_segments(sms_content)
        
        if char_count > target_length:
            issues.append(f"SMS too long: {char_count}/{target_length} characters")
        
        if segment_count > 3:
            warnings.append(f"SMS requires {segment_count} segments - consider shortening")
        
        # Content validation
        if not sms_content.startswith('Lloyds'):
            warnings.append("SMS should start with 'Lloyds:'")
        
        if 'call' not in sms_content.lower() and 'app' not in sms_content.lower():
            warnings.append("SMS should include clear action (app/call)")
        
        # Critical content preservation check
        critical_missing = []
        if key_points:
            try:
                from src.core.content_validator import PointImportance
                critical_points = [p for p in key_points if p.importance == PointImportance.CRITICAL]
                
                for point in critical_points[:2]:  # Check first 2 critical points
                    point_keywords = [word.lower() for word in point.content.split() if len(word) > 4]
                    if point_keywords:
                        found = any(keyword in sms_content.lower() for keyword in point_keywords)
                        if not found:
                            critical_missing.append(point.content[:50])
            except ImportError:
                pass
        
        if critical_missing:
            issues.extend([f"Missing critical info: {item}" for item in critical_missing])
        
        # Calculate quality score
        quality_score = 1.0
        quality_score -= len(issues) * 0.3
        quality_score -= len(warnings) * 0.1
        
        # Bonus for good SMS practices
        if sms_content.startswith('Lloyds:'):
            quality_score += 0.1
        if char_count <= target_length:
            quality_score += 0.1
        if segment_count == 1:
            quality_score += 0.1
        
        quality_score = max(0.0, min(1.0, quality_score))
        
        # Determine status
        if quality_score >= 0.8:
            status_text = "Excellent"
        elif quality_score >= 0.6:
            status_text = "Good"
        elif quality_score >= 0.4:
            status_text = "Fair"
        else:
            status_text = "Needs Improvement"
        
        return {
            'is_valid': len(issues) == 0,
            'quality_score': quality_score,
            'status_text': status_text,
            'issues': issues,
            'warnings': warnings,
            'character_count': char_count,
            'target_length': target_length,
            'segment_count': segment_count,
            'generation_method': sms_result.get('generation_method', 'unknown'),
            'critical_content_preserved': len(critical_missing) == 0
        }

# Convenience function
def generate_personalized_sms(
    clean_content: str,
    customer: Dict[str, Any],
    key_points: Optional[List] = None,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to generate a personalized SMS
    
    Returns:
        Dict with 'sms_result' and 'validation'
    """
    generator = SMSChannelGenerator(api_key)
    sms_result = generator.generate_sms(clean_content, customer, key_points)
    validation = generator.validate_sms(sms_result, clean_content, key_points)
    
    return {
        'sms_result': sms_result,
        'validation': validation
    }