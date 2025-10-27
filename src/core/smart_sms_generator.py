"""
Smart SMS Generator - Self-contained with configuration
Uses SharedContext for Consistent, Concise SMS Messages
"""

import os
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# Environment setup
from dotenv import load_dotenv
load_dotenv()

# AI imports
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("⚠️ Anthropic not available - using simulation mode")

# Add the project root to Python path
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import the SharedContext types
try:
    from src.core.shared_brain import SharedContext, PersonalizationLevel
    SHARED_BRAIN_AVAILABLE = True
except ImportError:
    SHARED_BRAIN_AVAILABLE = False
    print("⚠️ Could not import SharedContext - make sure shared_brain.py is available")

@dataclass
class SMSResult:
    """Result from SMS generation"""
    content: str
    character_count: int
    is_multipart: bool
    segments: int
    personalization_elements: List[str]
    critical_points_included: List[str]
    tone_achieved: str
    language: str
    generation_method: str
    processing_time: float
    quality_score: float
    abbreviations_used: Dict[str, str]
    requires_regulatory_footer: bool

class SmartSMSGenerator:
    """
    Smart SMS Generator - Self-contained with all configuration
    Takes a SharedContext and generates perfectly aligned SMS content
    """
    
    # ============== SMS CONFIGURATION ==============
    # All SMS-specific configuration in one place
    SMS_CONFIG = {
        'max_length': 400,  # Modern phones support longer SMS
        'multipart_threshold': 350,  # When to warn about splitting
        'encoding': {
            'default': 'GSM',  # 160 chars per segment
            'unicode': 'UCS-2'  # 70 chars per segment
        },
        'regulatory_footer': ' Reply STOP to opt out.',
        'regulatory_footer_length': 25,
        'url_shortener': {
            'enabled': True,
            'domain': 'lloyds.link',
            'max_length': 20
        },
        'personalization': {
            'include_name': True,
            'use_first_name_only': True,
            'abbreviations': {
                'account': 'a/c',
                'balance': 'bal',
                'available': 'avail',
                'transaction': 'trans',
                'payment': 'pymt',
                'transfer': 'tfr',
                'pounds': '£',
                'approximately': '~',
                'number': '#',
                'information': 'info',
                'tomorrow': 'tmrw',
                'today': 'tdy',
                'yesterday': 'yday',
                'message': 'msg',
                'reference': 'ref',
                'telephone': 'tel',
                'customer': 'cust',
                'service': 'svc',
                'department': 'dept',
                'account number': 'a/c no.',
                'please': 'pls',
                'thanks': 'thx',
                'regards': 'rgds'
            }
        },
        'priority_indicators': {
            'urgent': '🚨 URGENT: ',
            'action_required': '⚠️ ACTION: ',
            'reminder': '🔔 REMINDER: ',
            'info': 'ℹ️ ',
            'secure': '🔒 SECURE: '
        },
        'tone_adaptations': {
            'DIGITAL': {
                'style': 'concise_modern',
                'greeting': 'Hi',
                'closing': None,  # No closing for digital
                'use_emojis': True
            },
            'ASSISTED': {
                'style': 'friendly_clear',
                'greeting': 'Hello',
                'closing': 'Thanks',
                'use_emojis': False
            },
            'TRADITIONAL': {
                'style': 'formal_complete',
                'greeting': 'Dear',
                'closing': 'Regards',
                'use_emojis': False
            }
        },
        'quality_thresholds': {
            'min_length': 30,
            'max_segments': 3,
            'personalization_required': 1,  # Min personalization elements
            'critical_points_required': 1   # Min critical points
        }
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the smart SMS generator"""
        self.api_key = api_key or os.getenv('CLAUDE_API_KEY')
        self.client = None
        self.config = self.SMS_CONFIG  # Use local config
        
        if self.api_key and ANTHROPIC_AVAILABLE:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.model = "claude-haiku-4-5-20251001"
            print("✅ Smart SMS Generator initialized with Claude AI")
        else:
            print("⚠️ Smart SMS Generator running in simulation mode")
    
    def generate_sms(self, shared_context: SharedContext) -> SMSResult:
        """
        Generate a perfectly personalized SMS using the Shared Brain's intelligence
        
        Args:
            shared_context: The complete intelligence from SharedBrain.analyze_everything()
            
        Returns:
            SMSResult with the generated SMS and metadata
        """
        
        start_time = datetime.now()
        
        print(f"📱 Generating smart SMS for {shared_context.customer_data.get('name')}...")
        
        # Check if SMS is enabled
        if not shared_context.channel_decisions['enabled_channels'].get('sms', False):
            return self._create_disabled_result(shared_context, "SMS disabled by rules")
        
        if self.client:
            result = self._generate_with_ai(shared_context)
        else:
            result = self._generate_simulation(shared_context)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        result.processing_time = processing_time
        
        print(f"✅ Smart SMS generated in {processing_time:.2f}s")
        print(f"   Characters: {result.character_count}/{self.config['max_length']}, Quality: {result.quality_score:.2%}")
        
        return result
    
    def _generate_with_ai(self, shared_context: SharedContext) -> SMSResult:
        """Generate SMS using AI with the shared context intelligence"""
        
        # Extract intelligence from shared context
        customer = shared_context.customer_data
        insights = shared_context.customer_insights
        strategy = shared_context.personalization_strategy
        content_strategy = shared_context.content_strategy
        
        # Get segment-specific tone configuration
        segment = insights.segment
        tone_config = self.config['tone_adaptations'].get(segment, self.config['tone_adaptations']['ASSISTED'])
        
        # Check if regulatory footer is needed
        doc_type = shared_context.document_classification.get('primary_classification', 'INFORMATIONAL')
        requires_regulatory = doc_type == 'PROMOTIONAL' or doc_type == 'TRANSACTIONAL'
        
        # Calculate available space
        max_length = self.config['max_length']
        if requires_regulatory:
            max_length -= self.config['regulatory_footer_length']
        
        # Build the SMS generation prompt
        generation_prompt = self._build_generation_prompt(
            shared_context.original_letter,
            customer,
            insights,
            strategy,
            content_strategy,
            max_length,
            requires_regulatory,
            tone_config
        )
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.4,
                messages=[{"role": "user", "content": generation_prompt}]
            )
            
            content = response.content[0].text.strip()
            sms_data = self._parse_ai_response(content)
            
            if sms_data:
                return self._create_sms_result(sms_data, shared_context, "ai_generation", requires_regulatory)
            else:
                return self._generate_fallback(shared_context)
                
        except Exception as e:
            print(f"AI SMS generation error: {e}")
            return self._generate_fallback(shared_context)
    
    def _build_generation_prompt(
        self, 
        original_letter: str,
        customer: Dict[str, Any],
        insights,
        strategy,
        content_strategy,
        max_length: int,
        requires_regulatory: bool,
        tone_config: Dict[str, Any]
    ) -> str:
        """Build the SMS generation prompt using shared context intelligence"""
        
        # Get critical points (SMS only includes critical)
        critical_points = [p.content for p in content_strategy.critical_points[:3]]
        
        # Get abbreviations
        abbreviations = self.config['personalization']['abbreviations']
        
        # Determine greeting based on segment
        greeting = tone_config['greeting']
        use_emojis = tone_config.get('use_emojis', False)
        
        prompt = f"""You are writing a personalized SMS for a Lloyds Bank customer. You have complete intelligence about the customer and must create a CONCISE message.

ORIGINAL LETTER KEY POINTS:
{original_letter[:500]}

CUSTOMER INTELLIGENCE:
- Name: {customer.get('name')}
- Segment: {insights.segment}
- Life Stage: {insights.life_stage}
- Digital Persona: {insights.digital_persona}
- Communication Style: {insights.communication_style}
- Language: {customer.get('preferred_language', 'English')}

PERSONALIZATION STRATEGY:
- Level: {strategy.level.value}
- Customer Story: {strategy.customer_story}
- Tone: {tone_config['style']}

CRITICAL POINTS TO INCLUDE (priority order):
{chr(10).join(['• ' + point for point in critical_points])}

SMS REQUIREMENTS:
- Start with: "{greeting} [First Name],"
- Maximum {max_length} characters
- Tone: {tone_config['style']}
{'- Use emojis sparingly for emphasis' if use_emojis else '- No emojis'}
{'- End with: "Reply STOP to opt out."' if requires_regulatory else ''}
- Include ONE personalization element: {strategy.must_mention[0] if strategy.must_mention else 'customer context'}

ABBREVIATIONS YOU CAN USE:
{json.dumps(abbreviations, indent=2)}

Generate the SMS as JSON:
{{
    "sms_content": "Complete SMS under {max_length} chars",
    "personalization_elements": ["what personalization was applied"],
    "critical_points_included": ["which critical points made it"],
    "abbreviations_used": {{"full": "abbrev"}},
    "character_count": actual_count,
    "tone_achieved": "tone description"
}}

Write in {customer.get('preferred_language', 'English')}. Be natural and action-oriented."""

        return prompt
    
    def _parse_ai_response(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse the AI response to extract SMS data"""
        
        content = content.replace('```json', '').replace('```', '').strip()
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            if '{' in content and '}' in content:
                try:
                    json_start = content.index('{')
                    json_end = content.rindex('}') + 1
                    json_str = content[json_start:json_end]
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
        return None
    
    def _create_sms_result(
        self, 
        sms_data: Dict[str, Any], 
        shared_context: SharedContext,
        method: str,
        requires_regulatory: bool
    ) -> SMSResult:
        """Create SMSResult from parsed SMS data"""
        
        sms_content = sms_data.get('sms_content', '')
        
        # Add regulatory footer if needed
        if requires_regulatory and 'STOP' not in sms_content.upper():
            sms_content += self.config['regulatory_footer']
        
        # Calculate segments
        char_count = len(sms_content)
        segments = self._calculate_segments(char_count)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(
            sms_content,
            sms_data.get('personalization_elements', []),
            sms_data.get('critical_points_included', []),
            shared_context
        )
        
        return SMSResult(
            content=sms_content,
            character_count=char_count,
            is_multipart=segments > 1,
            segments=segments,
            personalization_elements=sms_data.get('personalization_elements', []),
            critical_points_included=sms_data.get('critical_points_included', []),
            tone_achieved=sms_data.get('tone_achieved', 'professional'),
            language=shared_context.customer_data.get('preferred_language', 'English'),
            generation_method=method,
            processing_time=0.0,
            quality_score=quality_score,
            abbreviations_used=sms_data.get('abbreviations_used', {}),
            requires_regulatory_footer=requires_regulatory
        )
    
    def _calculate_segments(self, char_count: int) -> int:
        """Calculate number of SMS segments"""
        if char_count <= 160:
            return 1
        else:
            return ((char_count - 1) // 153) + 1
    
    def _calculate_quality_score(
        self, 
        sms_content: str, 
        personalization_elements: List[str],
        critical_points: List[str],
        shared_context: SharedContext
    ) -> float:
        """Calculate quality score for SMS"""
        
        score = 0.5  # Base score
        
        # Check personalization
        if len(personalization_elements) >= self.config['quality_thresholds']['personalization_required']:
            score += 0.2
        
        # Check critical content
        if len(critical_points) >= self.config['quality_thresholds']['critical_points_required']:
            score += 0.2
        
        # Check length efficiency
        if self.config['quality_thresholds']['min_length'] <= len(sms_content) <= self.config['max_length']:
            score += 0.1
        
        return min(1.0, score)
    
    def _generate_fallback(self, shared_context: SharedContext) -> SMSResult:
        """Generate fallback SMS when AI fails"""
        
        customer = shared_context.customer_data
        insights = shared_context.customer_insights
        name = customer.get('name', 'Customer').split()[0]
        
        # Get tone config for segment
        tone_config = self.config['tone_adaptations'].get(
            insights.segment, 
            self.config['tone_adaptations']['ASSISTED']
        )
        greeting = tone_config['greeting']
        
        doc_type = shared_context.document_classification.get('primary_classification', 'INFORMATIONAL')
        
        if doc_type == 'URGENT':
            sms_content = f"{greeting} {name}, urgent action required on your Lloyds account. Check your email or app for details."
        else:
            sms_content = f"{greeting} {name}, new update for your Lloyds account. Check your app or email for details."
        
        return SMSResult(
            content=sms_content,
            character_count=len(sms_content),
            is_multipart=False,
            segments=1,
            personalization_elements=["customer_name"],
            critical_points_included=["account_update"],
            tone_achieved=tone_config['style'],
            language=customer.get('preferred_language', 'English'),
            generation_method="fallback",
            processing_time=0.0,
            quality_score=0.5,
            abbreviations_used={},
            requires_regulatory_footer=False
        )
    
    def _generate_simulation(self, shared_context: SharedContext) -> SMSResult:
        """Generate simulation SMS for testing without AI"""
        
        customer = shared_context.customer_data
        insights = shared_context.customer_insights
        strategy = shared_context.personalization_strategy
        
        name = customer.get('name', 'Customer').split()[0]
        
        simulation_content = f"[SIM] Hi {name}, {insights.segment} SMS. Level: {strategy.level.value}. Check app."
        
        return SMSResult(
            content=simulation_content,
            character_count=len(simulation_content),
            is_multipart=False,
            segments=1,
            personalization_elements=["simulation_mode"],
            critical_points_included=["test_message"],
            tone_achieved=insights.communication_style,
            language=customer.get('preferred_language', 'English'),
            generation_method="simulation",
            processing_time=0.0,
            quality_score=0.8,
            abbreviations_used={},
            requires_regulatory_footer=False
        )
    
    def _create_disabled_result(self, shared_context: SharedContext, reason: str) -> SMSResult:
        """Create result when SMS is disabled"""
        
        return SMSResult(
            content="",
            character_count=0,
            is_multipart=False,
            segments=0,
            personalization_elements=[],
            critical_points_included=[],
            tone_achieved="",
            language=shared_context.customer_data.get('preferred_language', 'English'),
            generation_method="disabled",
            processing_time=0.0,
            quality_score=0.0,
            abbreviations_used={},
            requires_regulatory_footer=False
        )
    
    def validate_sms(self, sms_result: SMSResult, shared_context: SharedContext) -> Dict[str, Any]:
        """Validate that the SMS meets requirements"""
        
        validation = {
            'is_valid': True,
            'quality_score': sms_result.quality_score,
            'issues': [],
            'achievements': [],
            'metrics': {
                'character_count': sms_result.character_count,
                'max_length': self.config['max_length'],
                'segments': sms_result.segments,
                'critical_points': len(sms_result.critical_points_included),
                'personalization': len(sms_result.personalization_elements)
            }
        }
        
        # Check length
        if sms_result.character_count > self.config['max_length']:
            validation['issues'].append(f"Exceeds max length ({sms_result.character_count}/{self.config['max_length']})")
            validation['is_valid'] = False
        elif sms_result.character_count < self.config['quality_thresholds']['min_length']:
            validation['issues'].append("Too short")
            validation['is_valid'] = False
        else:
            validation['achievements'].append(f"Optimal length: {sms_result.character_count} chars")
        
        # Check critical content
        if len(sms_result.critical_points_included) < self.config['quality_thresholds']['critical_points_required']:
            validation['issues'].append("Missing critical points")
        else:
            validation['achievements'].append(f"Included {len(sms_result.critical_points_included)} critical points")
        
        # Check personalization
        if len(sms_result.personalization_elements) < self.config['quality_thresholds']['personalization_required']:
            validation['issues'].append("Insufficient personalization")
        else:
            validation['achievements'].append(f"Applied {len(sms_result.personalization_elements)} personalizations")
        
        return validation

# Convenience function
def generate_smart_sms(shared_context: SharedContext, api_key: Optional[str] = None) -> SMSResult:
    """
    Convenience function to generate a smart SMS from shared context
    
    Args:
        shared_context: Complete intelligence from SharedBrain
        api_key: Optional API key
        
    Returns:
        SMSResult with generated SMS
    """
    generator = SmartSMSGenerator(api_key=api_key)
    return generator.generate_sms(shared_context)