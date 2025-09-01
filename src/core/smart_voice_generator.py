"""
Smart Voice Note Generator - Self-contained with configuration
Uses SharedContext for Consistent, Natural Voice Messages
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

# Import SharedContext
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.core.shared_brain import SharedContext, PersonalizationLevel
    SHARED_BRAIN_AVAILABLE = True
except ImportError:
    SHARED_BRAIN_AVAILABLE = False
    print("⚠️ Could not import SharedContext")

@dataclass
class VoiceResult:
    """Result from voice note generation - MUST match pattern of other results"""
    content: str  # The script/text for the voice note
    duration_estimate: float  # Estimated duration in seconds
    word_count: int
    speaking_pace: str  # slow, normal, fast
    tone_markers: List[str]  # Emotional tone markers for voice synthesis
    personalization_elements: List[str]
    natural_pauses: List[int]  # Word positions where pauses should occur
    emphasis_words: List[str]  # Words to emphasize
    language: str
    generation_method: str
    processing_time: float
    quality_score: float
    requires_callback: bool  # If true, offer callback option

class SmartVoiceGenerator:
    """
    Smart Voice Note Generator - Self-contained with all configuration
    Takes a SharedContext and generates perfectly aligned voice content
    """
    
    # ============== VOICE NOTE CONFIGURATION ==============
    VOICE_CONFIG = {
        'max_duration': 120,  # Maximum 2 minutes
        'min_duration': 15,   # Minimum 15 seconds
        'optimal_duration': 45,  # Ideal 45 seconds
        'speaking_rates': {
            'slow': 120,     # words per minute
            'normal': 150,   # words per minute  
            'fast': 180      # words per minute
        },
        'format': {
            'audio_format': 'mp3',
            'sample_rate': 22050,
            'bitrate': 128
        },
        'greeting_styles': {
            'DIGITAL': {
                'style': 'warm_casual',
                'greeting': 'Hi {first_name}, this is {bank_rep} from Lloyds',
                'closing': 'Thanks for being with Lloyds. Have a great day!',
                'tone': 'friendly',
                'pace': 'normal'
            },
            'ASSISTED': {
                'style': 'professional_warm',
                'greeting': 'Hello {first_name}, this is {bank_rep} calling from Lloyds Bank',
                'closing': 'Thank you for your time. If you need anything, we\'re here to help.',
                'tone': 'professional_friendly',
                'pace': 'normal'
            },
            'TRADITIONAL': {
                'style': 'formal_respectful',
                'greeting': 'Good {time_of_day} {title} {last_name}, this is {bank_rep} from Lloyds Banking Group',
                'closing': 'Thank you for your attention. Please don\'t hesitate to contact your branch if you need assistance.',
                'tone': 'formal',
                'pace': 'slow'
            }
        },
        'natural_speech_patterns': {
            'use_contractions': True,  # "we're" instead of "we are"
            'add_filler_words': False,  # Avoid "um", "uh"
            'conversational_tone': True,
            'personal_anecdotes': False
        },
        'voice_characteristics': {
            'DIGITAL': {
                'energy': 'high',
                'warmth': 'very_warm',
                'formality': 'casual',
                'accent': 'neutral'
            },
            'ASSISTED': {
                'energy': 'medium',
                'warmth': 'warm',
                'formality': 'professional',
                'accent': 'neutral'
            },
            'TRADITIONAL': {
                'energy': 'calm',
                'warmth': 'cordial',
                'formality': 'formal',
                'accent': 'received_pronunciation'
            }
        },
        'content_structure': {
            'include_purpose_upfront': True,  # State why calling immediately
            'use_signposting': True,  # "First..., Second..., Finally..."
            'summarize_key_points': True,
            'offer_callback': True,
            'mention_other_channels': True
        },
        'quality_thresholds': {
            'min_clarity_score': 0.8,
            'max_information_density': 0.7,  # Don't pack too much info
            'min_personalization': 2,  # Fewer than written due to brevity
            'optimal_sentence_length': 15  # words
        },
        'callback_triggers': {
            'URGENT': True,
            'REGULATORY': True,
            'complex_action_required': True,
            'vulnerable_customer': True
        }
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the smart voice generator"""
        self.api_key = api_key or os.getenv('CLAUDE_API_KEY')
        self.client = None
        self.config = self.VOICE_CONFIG
        
        if self.api_key and ANTHROPIC_AVAILABLE:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.model = "claude-3-5-sonnet-20241022"
            print("✅ Smart Voice Generator initialized with Claude AI")
        else:
            print("⚠️ Smart Voice Generator running in simulation mode")
    
    def generate_voice_note(self, shared_context: SharedContext) -> VoiceResult:
        """
        Generate a perfectly personalized voice note script using the Shared Brain's intelligence
        
        Args:
            shared_context: The complete intelligence from SharedBrain.analyze_everything()
            
        Returns:
            VoiceResult with the generated voice script and metadata
        """
        start_time = datetime.now()
        
        print(f"🎙️ Generating smart voice note for {shared_context.customer_data.get('name')}...")
        
        # Check if voice is enabled (might not be in channel_decisions yet)
        if not shared_context.channel_decisions['enabled_channels'].get('voice', True):
            return self._create_disabled_result(shared_context, "Voice disabled by rules")
        
        if self.client:
            result = self._generate_with_ai(shared_context)
        else:
            result = self._generate_simulation(shared_context)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        result.processing_time = processing_time
        
        print(f"✅ Smart voice note generated in {processing_time:.2f}s")
        print(f"   Duration: {result.duration_estimate:.1f}s, Quality: {result.quality_score:.2%}")
        
        return result
    
    def _generate_with_ai(self, shared_context: SharedContext) -> VoiceResult:
        """Generate voice note using AI"""
        
        # Extract intelligence
        customer = shared_context.customer_data
        insights = shared_context.customer_insights
        strategy = shared_context.personalization_strategy
        content_strategy = shared_context.content_strategy
        
        # Get configuration
        segment = insights.segment
        greeting_config = self.config['greeting_styles'].get(segment, self.config['greeting_styles']['ASSISTED'])
        voice_chars = self.config['voice_characteristics'].get(segment, self.config['voice_characteristics']['ASSISTED'])
        
        # Determine if callback needed
        doc_type = shared_context.document_classification.get('primary_classification', 'INFORMATIONAL')
        urgency = shared_context.document_classification.get('urgency_level', 'LOW')
        requires_callback = (
            doc_type in ['URGENT', 'REGULATORY'] or
            urgency == 'HIGH' or
            shared_context.document_classification.get('customer_action_required', False)
        )
        
        # Build prompt
        generation_prompt = self._build_generation_prompt(
            shared_context.original_letter,
            customer,
            insights,
            strategy,
            content_strategy,
            greeting_config,
            voice_chars,
            doc_type,
            requires_callback
        )
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.7,  # Higher for more natural speech
                messages=[{"role": "user", "content": generation_prompt}]
            )
            
            content = response.content[0].text.strip()
            voice_data = self._parse_ai_response(content)
            
            if voice_data:
                return self._create_voice_result(voice_data, shared_context, "ai_generation", requires_callback)
            else:
                return self._generate_fallback(shared_context)
                
        except Exception as e:
            print(f"AI voice generation error: {e}")
            return self._generate_fallback(shared_context)
    
    def _build_generation_prompt(
        self, 
        original_letter: str,
        customer: Dict[str, Any],
        insights,
        strategy,
        content_strategy,
        greeting_config: Dict[str, Any],
        voice_chars: Dict[str, Any],
        doc_type: str,
        requires_callback: bool
    ) -> str:
        """Build the voice generation prompt"""
        
        # Get only critical points for voice (brevity is key)
        critical_points = [p.content for p in content_strategy.critical_points[:3]]
        
        # Format greeting
        first_name = customer.get('name', '').split()[0] if customer.get('name') else 'there'
        greeting = greeting_config['greeting'].format(
            first_name=first_name,
            bank_rep="Sarah",  # Could be dynamic
            time_of_day="morning",  # Could be based on time
            title="Mr" if customer.get('gender') == 'M' else "Ms",
            last_name=customer.get('name', '').split()[-1] if customer.get('name') else ''
        )
        
        # Calculate target duration
        target_words = int(self.config['optimal_duration'] * self.config['speaking_rates']['normal'] / 60)
        
        prompt = f"""Generate a natural, conversational VOICE NOTE SCRIPT for a phone message to a bank customer.

CRITICAL: This will be SPOKEN ALOUD, so write exactly how someone would naturally speak on the phone.

CUSTOMER CONTEXT:
- Name: {customer.get('name')}
- Segment: {insights.segment} (speak {greeting_config['pace']} pace)
- Life Stage: {insights.life_stage}
- Communication Style: {insights.communication_style}
- Special Context: {insights.special_factors[0] if insights.special_factors else 'None'}

KEY INFORMATION TO CONVEY (pick most important for voice):
{chr(10).join(['• ' + point for point in critical_points])}

VOICE REQUIREMENTS:
- Start: "{greeting}"
- Tone: {greeting_config['tone']} and {voice_chars['warmth']}
- Length: {target_words} words (about {self.config['optimal_duration']} seconds when spoken)
- End: "{greeting_config['closing']}"
- Natural speech: Use contractions, sound conversational
- Be CONCISE: This is a voice message, not a letter
{"- MUST offer callback option due to importance" if requires_callback else ""}

PERSONALIZATION:
- Reference ONE specific thing about the customer
- Sound like you know them
- Use their name once more in the middle

SPEECH PATTERNS:
- Write as SPOKEN language, not written
- Use "we're", "you'll", "won't" etc.
- Break up long sentences
- Sound warm and human

Generate as JSON:
{{
    "voice_script": "Complete natural speech script with pauses indicated by '...'",
    "tone_markers": ["warm", "urgent", "friendly", etc],
    "emphasis_words": ["important", "deadline", etc - words to stress],
    "personalization_elements": ["what was personalized"],
    "natural_pauses": [15, 30, 45],  // Word positions for pauses
    "speaking_pace": "slow|normal|fast"
}}

Make it sound like a real person calling, not a robot reading a script."""
        
        return prompt
    
    def _parse_ai_response(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse the AI response - reusing the robust parsing from email/letter"""
        
        # Remove markdown formatting if present
        content = content.replace('```json', '').replace('```', '').strip()
        
        # Clean up common issues
        content = content.replace('\n', ' ')
        content = content.replace('\r', '')
        content = content.replace('\t', ' ')
        
        # Try direct JSON parsing first
        try:
            parsed = json.loads(content)
            if parsed and isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from content
        if '{' in content and '}' in content:
            try:
                json_start = content.index('{')
                json_end = content.rindex('}') + 1
                json_str = content[json_start:json_end]
                
                # Clean the extracted JSON
                json_str = re.sub(r'[\r\n\t]', ' ', json_str)
                json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
                
                parsed = json.loads(json_str)
                if parsed and isinstance(parsed, dict):
                    return parsed
            except (json.JSONDecodeError, ValueError) as e:
                print(f"JSON extraction failed: {e}")
        
        print("⚠️ All parsing attempts failed for voice response")
        return None
    
    def _create_voice_result(
        self, 
        voice_data: Dict[str, Any], 
        shared_context: SharedContext,
        method: str,
        requires_callback: bool
    ) -> VoiceResult:
        """Create VoiceResult from parsed data"""
        
        script = voice_data.get('voice_script', '')
        word_count = len(script.split())
        
        # Calculate duration based on pace
        pace = voice_data.get('speaking_pace', 'normal')
        wpm = self.config['speaking_rates'].get(pace, 150)
        duration_estimate = (word_count / wpm) * 60  # in seconds
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(
            script,
            voice_data.get('personalization_elements', []),
            duration_estimate,
            shared_context
        )
        
        return VoiceResult(
            content=script,
            duration_estimate=duration_estimate,
            word_count=word_count,
            speaking_pace=pace,
            tone_markers=voice_data.get('tone_markers', ['professional']),
            personalization_elements=voice_data.get('personalization_elements', []),
            natural_pauses=voice_data.get('natural_pauses', []),
            emphasis_words=voice_data.get('emphasis_words', []),
            language=shared_context.customer_data.get('preferred_language', 'English'),
            generation_method=method,
            processing_time=0.0,
            quality_score=quality_score,
            requires_callback=requires_callback
        )
    
    def _calculate_quality_score(
        self, 
        script: str,
        personalization_elements: List[str],
        duration: float,
        shared_context: SharedContext
    ) -> float:
        """Calculate quality score for voice note"""
        
        score = 0.5  # Base score
        
        # Check duration
        if self.config['min_duration'] <= duration <= self.config['max_duration']:
            if abs(duration - self.config['optimal_duration']) < 15:
                score += 0.2  # Close to optimal
            else:
                score += 0.1
        
        # Check personalization
        if len(personalization_elements) >= self.config['quality_thresholds']['min_personalization']:
            score += 0.2
        
        # Check conversational tone (contractions)
        contractions = ["we're", "you'll", "won't", "it's", "that's", "we've"]
        if any(cont in script.lower() for cont in contractions):
            score += 0.1
        
        # Check sentence length
        sentences = script.split('.')
        avg_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        if avg_length <= self.config['quality_thresholds']['optimal_sentence_length']:
            score += 0.1
        
        # Bonus for natural speech patterns
        if '...' in script:  # Has pauses
            score += 0.05
        
        return min(1.0, score)
    
    def _generate_fallback(self, shared_context: SharedContext) -> VoiceResult:
        """Generate fallback voice note when AI fails"""
        
        customer = shared_context.customer_data
        name = customer.get('name', 'there').split()[0]
        
        script = f"""Hi {name}, this is Sarah from Lloyds Bank. 

I'm calling with an important update about your account. We've sent you a letter with all the details, but I wanted to make sure you got the message.

{shared_context.original_letter[:100]}...

Please check your mail for the full information. If you have any questions or need to discuss this, just give us a call back on 0345 300 0000.

Thanks for being with Lloyds, {name}. Have a great day!"""
        
        word_count = len(script.split())
        duration = (word_count / 150) * 60
        
        return VoiceResult(
            content=script,
            duration_estimate=duration,
            word_count=word_count,
            speaking_pace='normal',
            tone_markers=['friendly', 'informative'],
            personalization_elements=['customer_name'],
            natural_pauses=[20, 40],
            emphasis_words=['important'],
            language='English',
            generation_method='fallback',
            processing_time=0.0,
            quality_score=0.5,
            requires_callback=False
        )
    
    def _generate_simulation(self, shared_context: SharedContext) -> VoiceResult:
        """Generate simulation voice note"""
        
        customer = shared_context.customer_data
        name = customer.get('name', 'Customer')
        
        script = f"""[SIMULATED VOICE NOTE]
        
Hi {name}, this is a test voice message from Lloyds.

Segment: {shared_context.customer_insights.segment}
Personalization: {shared_context.personalization_strategy.level.value}

[Voice script would be generated here]

Thanks for listening!"""
        
        return VoiceResult(
            content=script,
            duration_estimate=30.0,
            word_count=len(script.split()),
            speaking_pace='normal',
            tone_markers=['test'],
            personalization_elements=['simulation'],
            natural_pauses=[],
            emphasis_words=[],
            language='English',
            generation_method='simulation',
            processing_time=0.0,
            quality_score=0.8,
            requires_callback=False
        )
    
    def _create_disabled_result(self, shared_context: SharedContext, reason: str) -> VoiceResult:
        """Create result when voice is disabled"""
        return VoiceResult(
            content="",
            duration_estimate=0.0,
            word_count=0,
            speaking_pace='normal',
            tone_markers=[],
            personalization_elements=[],
            natural_pauses=[],
            emphasis_words=[],
            language='English',
            generation_method='disabled',
            processing_time=0.0,
            quality_score=0.0,
            requires_callback=False
        )
    
    def validate_voice_note(self, voice_result: VoiceResult, shared_context: SharedContext) -> Dict[str, Any]:
        """Validate voice note meets requirements"""
        
        validation = {
            'is_valid': True,
            'quality_score': voice_result.quality_score,
            'issues': [],
            'achievements': [],
            'metrics': {
                'duration': f"{voice_result.duration_estimate:.1f}s",
                'word_count': voice_result.word_count,
                'speaking_pace': voice_result.speaking_pace,
                'requires_callback': voice_result.requires_callback
            }
        }
        
        # Check duration
        if voice_result.duration_estimate < self.config['min_duration']:
            validation['issues'].append("Too short for voice note")
        elif voice_result.duration_estimate > self.config['max_duration']:
            validation['issues'].append("Too long - consider breaking up")
        else:
            validation['achievements'].append(f"Good length: {voice_result.duration_estimate:.0f}s")
        
        # Check personalization
        if len(voice_result.personalization_elements) >= self.config['quality_thresholds']['min_personalization']:
            validation['achievements'].append("Well personalized for voice")
        
        # Check natural speech
        if voice_result.tone_markers:
            validation['achievements'].append(f"Natural tone: {', '.join(voice_result.tone_markers[:2])}")
        
        return validation

# Convenience function
def generate_smart_voice_note(shared_context: SharedContext, api_key: Optional[str] = None) -> VoiceResult:
    """Generate a smart voice note from shared context"""
    generator = SmartVoiceGenerator(api_key=api_key)
    return generator.generate_voice_note(shared_context)