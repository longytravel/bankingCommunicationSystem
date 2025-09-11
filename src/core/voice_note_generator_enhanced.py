"""
Smart Voice Note Generator - With Audio Generation and Dynamic Voice/Name Matching
FIXED: Voice and representative name always match, sensitivity-aware voice selection
"""

import os
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
import hashlib

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

# TTS imports
try:
    from openai import OpenAI
    OPENAI_TTS_AVAILABLE = True
except ImportError:
    OPENAI_TTS_AVAILABLE = False
    print("⚠️ OpenAI TTS not available")

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    print("⚠️ pyttsx3 not available - no fallback TTS")

# Import SharedContext
import sys
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
    """Result from voice note generation with audio file"""
    content: str  # The script/text for the voice note
    duration_estimate: float  # Estimated duration in seconds
    word_count: int
    speaking_pace: str  # slow, normal, fast
    tone_markers: List[str]  # Emotional tone markers
    personalization_elements: List[str]
    emphasis_words: List[str]  # Words to emphasize
    language: str
    generation_method: str
    processing_time: float
    quality_score: float
    audio_file_path: Optional[str] = None  # Path to generated audio file
    audio_format: str = "mp3"
    tts_engine_used: str = "none"  # openai, pyttsx3, or none
    voice_used: str = "none"  # Which voice was used
    representative_name: str = ""  # Name of the representative in the script

class SmartVoiceGenerator:
    """
    Smart Voice Note Generator with Audio Generation
    FIXED: Dynamic voice-to-name matching, sensitivity-aware voice selection
    """
    
    # ============== VOICE CONFIGURATION WITH DYNAMIC MATCHING ==============
    VOICE_CONFIG = {
        'audio': {
            'output_dir': 'output/voice_notes',
            'format': 'mp3',
            'sample_rate': 24000,
            'quality': 'high'
        },
        'tts': {
            'openai': {
                'model': 'tts-1-hd',  # Higher quality model
                'voice_characteristics': {
                    # Voice characteristics and appropriate representative names
                    'nova': {
                        'gender': 'female',
                        'style': 'warm, professional',
                        'names': ['Emma', 'Sarah', 'Sophie', 'Claire', 'Rachel'],
                        'best_for': ['DIGITAL', 'ASSISTED'],
                        'sensitivity_appropriate': True
                    },
                    'alloy': {
                        'gender': 'neutral',
                        'style': 'balanced, clear',
                        'names': ['Alex', 'Jordan', 'Taylor', 'Morgan', 'Casey'],
                        'best_for': ['ASSISTED', 'DIGITAL'],
                        'sensitivity_appropriate': True
                    },
                    'onyx': {
                        'gender': 'male',
                        'style': 'deep, authoritative',
                        'names': ['James', 'Michael', 'David', 'Robert', 'William'],
                        'best_for': ['TRADITIONAL'],
                        'sensitivity_appropriate': False  # Too authoritative for sensitive situations
                    },
                    'echo': {
                        'gender': 'male',
                        'style': 'conversational, friendly',
                        'names': ['Tom', 'Daniel', 'Andrew', 'Peter', 'Mark'],
                        'best_for': ['DIGITAL', 'ASSISTED'],
                        'sensitivity_appropriate': True
                    },
                    'fable': {
                        'gender': 'male',
                        'style': 'warm, British',
                        'names': ['Oliver', 'George', 'Charles', 'Edward', 'Henry'],
                        'best_for': ['TRADITIONAL', 'ASSISTED'],
                        'sensitivity_appropriate': True
                    },
                    'shimmer': {
                        'gender': 'female',
                        'style': 'gentle, calming',
                        'names': ['Grace', 'Emily', 'Charlotte', 'Lucy', 'Hannah'],
                        'best_for': ['TRADITIONAL', 'ASSISTED'],
                        'sensitivity_appropriate': True  # Very good for sensitive situations
                    }
                },
                'segment_voice_preferences': {
                    # Primary voice selection by segment (can be overridden by sensitivity)
                    'DIGITAL': {
                        'primary': 'nova',
                        'fallback': 'echo',
                        'sensitive': 'shimmer'  # For sensitive situations
                    },
                    'ASSISTED': {
                        'primary': 'alloy',
                        'fallback': 'nova',
                        'sensitive': 'shimmer'
                    },
                    'TRADITIONAL': {
                        'primary': 'fable',  # Changed from onyx to fable (warmer)
                        'fallback': 'shimmer',
                        'sensitive': 'shimmer'
                    }
                },
                'speed_settings': {
                    'slow': 0.85,
                    'normal': 1.0,
                    'fast': 1.15
                }
            },
            'pyttsx3': {
                'rate': 150,  # Words per minute
                'volume': 0.9
            }
        },
        'durations': {
            'max': 120,  # Maximum 2 minutes
            'min': 15,   # Minimum 15 seconds
            'optimal': 45  # Ideal 45 seconds
        },
        'greetings': {
            # Greetings with placeholder for dynamic representative name
            'English': {
                'DIGITAL': 'Hi {customer_name}, this is {rep_name} from Lloyds',
                'ASSISTED': 'Hello {customer_name}, this is {rep_name} calling from Lloyds Bank',
                'TRADITIONAL': 'Good {time_of_day} {title} {last_name}, this is {rep_name} from Lloyds Banking Group'
            },
            'Spanish': {
                'DIGITAL': 'Hola {customer_name}, soy {rep_name} de Lloyds',
                'ASSISTED': 'Buenos días {customer_name}, le llama {rep_name} del Banco Lloyds',
                'TRADITIONAL': 'Buenos {time_of_day} {title} {last_name}, le habla {rep_name} del Grupo Bancario Lloyds'
            },
            # ... other languages follow same pattern with {rep_name} placeholder
        },
        'closings': {
            'English': {
                'DIGITAL': 'Thanks for being with Lloyds. Have a great day!',
                'ASSISTED': 'Thank you for your time. If you need anything, we\'re here to help.',
                'TRADITIONAL': 'Thank you for your attention. Please don\'t hesitate to contact us.',
                'SENSITIVE': 'We\'re here to support you. Please don\'t hesitate to reach out if you need anything.'
            },
            # ... other languages
        }
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with API keys for AI and TTS"""
        self.api_key = api_key or os.getenv('CLAUDE_API_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.client = None
        self.openai_client = None
        self.config = self.VOICE_CONFIG
        
        # Initialize Claude for script generation
        if self.api_key and ANTHROPIC_AVAILABLE:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.model = "claude-3-5-sonnet-20241022"
            print("✅ Voice Generator: Claude AI ready (with voice matching)")
        else:
            print("⚠️ Voice Generator: No Claude API")
        
        # Initialize OpenAI for TTS
        if self.openai_api_key and OPENAI_TTS_AVAILABLE:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
            print("✅ Voice Generator: OpenAI TTS ready")
        else:
            print("⚠️ Voice Generator: No OpenAI TTS")
        
        # Check pyttsx3 fallback
        if PYTTSX3_AVAILABLE:
            print("✅ Voice Generator: pyttsx3 fallback available")
        
        # Create output directory
        self.output_dir = Path(self.config['audio']['output_dir'])
        self.output_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Voice output directory: {self.output_dir}")
    
    def generate_voice_note(self, shared_context: SharedContext) -> VoiceResult:
        """Generate voice note with script AND audio file - FIXED with proper voice/name matching"""
        start_time = datetime.now()
        
        customer_name = shared_context.customer_data.get('name', 'Customer')
        customer_language = shared_context.customer_data.get('preferred_language', 'English')
        
        print(f"🎙️ Generating voice note for {customer_name} in {customer_language}...")
        
        # Check if voice is enabled
        voice_enabled = shared_context.channel_decisions['enabled_channels'].get('voice', False)
        if not voice_enabled:
            reason = shared_context.channel_decisions['reasons'].get('voice', 'Not enabled')
            print(f"  ⏭️ Voice disabled: {reason}")
            return self._create_disabled_result(shared_context)
        
        # Generate the script with proper voice/name matching
        if self.client:
            result = self._generate_with_ai(shared_context)
        else:
            print("  ⚠️ No AI available, using fallback script generation")
            result = self._generate_fallback(shared_context)
        
        # Generate audio file from script
        if result.content and result.generation_method != 'disabled':
            audio_path = self._generate_audio(
                result.content,
                result.language,
                result.voice_used,
                result.speaking_pace,
                shared_context.customer_data
            )
            if audio_path:
                result.audio_file_path = audio_path
                result.tts_engine_used = "openai" if self.openai_client else "pyttsx3" if PYTTSX3_AVAILABLE else "none"
                print(f"  🎵 Audio file created: {audio_path}")
                print(f"  🎤 Voice: {result.voice_used}, Representative: {result.representative_name}")
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        result.processing_time = processing_time
        
        print(f"✅ Voice note complete in {processing_time:.2f}s")
        if result.audio_file_path:
            print(f"   Audio: {result.audio_file_path}")
        print(f"   Language: {result.language}, Duration: {result.duration_estimate:.1f}s")
        print(f"   Voice Match: {result.voice_used} → {result.representative_name}")
        
        return result
    
    def _select_voice_and_name(
        self, 
        segment: str, 
        sensitivity_flags: List[str],
        language: str
    ) -> Tuple[str, str]:
        """
        Select appropriate voice and matching representative name
        Returns: (voice_id, representative_name)
        """
        
        # Get segment preferences
        segment_prefs = self.config['tts']['openai']['segment_voice_preferences'].get(
            segment, 
            self.config['tts']['openai']['segment_voice_preferences']['ASSISTED']
        )
        
        # Determine which voice to use based on sensitivity
        if sensitivity_flags and any(flag in ['Bereavement', 'Vulnerability'] for flag in sensitivity_flags):
            # Use sensitive voice option
            voice_id = segment_prefs.get('sensitive', 'shimmer')
            print(f"  💝 Using sensitive voice: {voice_id}")
        else:
            # Use primary voice for segment
            voice_id = segment_prefs.get('primary', 'alloy')
        
        # Get voice characteristics
        voice_info = self.config['tts']['openai']['voice_characteristics'].get(
            voice_id,
            self.config['tts']['openai']['voice_characteristics']['alloy']
        )
        
        # Select appropriate name from the voice's name pool
        # Could be random, but for consistency we'll use first name
        representative_name = voice_info['names'][0]
        
        # For non-English, might want to localize names
        if language == 'Spanish':
            name_mapping = {'Emma': 'Elena', 'James': 'Diego', 'Sarah': 'Sofia'}
            representative_name = name_mapping.get(representative_name, representative_name)
        elif language == 'French':
            name_mapping = {'Emma': 'Émilie', 'James': 'Jacques', 'Sarah': 'Sophie'}
            representative_name = name_mapping.get(representative_name, representative_name)
        
        return voice_id, representative_name
    
    def _generate_audio(
        self, 
        script: str, 
        language: str, 
        voice_id: str,
        pace: str,
        customer_data: Dict[str, Any]
    ) -> Optional[str]:
        """Generate audio file from script using the specified voice"""
        
        # Create unique filename
        customer_id = customer_data.get('customer_id', 'unknown')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"voice_{customer_id}_{language}_{timestamp}.mp3"
        filepath = self.output_dir / filename
        
        # Try OpenAI TTS first
        if self.openai_client:
            try:
                # Use the voice_id that was selected
                speed = self.config['tts']['openai']['speed_settings'].get(pace, 1.0)
                
                # Generate audio
                response = self.openai_client.audio.speech.create(
                    model=self.config['tts']['openai']['model'],
                    voice=voice_id,  # Use the selected voice
                    input=script,
                    speed=speed
                )
                
                # Save to file
                response.stream_to_file(str(filepath))
                return str(filepath)
                
            except Exception as e:
                print(f"  ❌ OpenAI TTS failed: {e}")
        
        # Fallback to pyttsx3
        if PYTTSX3_AVAILABLE:
            try:
                engine = pyttsx3.init()
                engine.setProperty('rate', self.config['tts']['pyttsx3']['rate'])
                engine.setProperty('volume', self.config['tts']['pyttsx3']['volume'])
                
                # Save to file
                engine.save_to_file(script, str(filepath))
                engine.runAndWait()
                
                return str(filepath)
                
            except Exception as e:
                print(f"  ❌ pyttsx3 TTS failed: {e}")
        
        print("  ⚠️ No TTS engine available - no audio file generated")
        return None
    
    def _generate_with_ai(self, shared_context: SharedContext) -> VoiceResult:
        """Generate voice script with AI - FIXED with proper voice/name matching"""
        
        customer = shared_context.customer_data
        insights = shared_context.customer_insights
        strategy = shared_context.personalization_strategy
        content_strategy = shared_context.content_strategy
        
        # Get language and segment
        language = customer.get('preferred_language', 'English')
        segment = insights.segment
        sensitivity_flags = getattr(insights, 'sensitivity_flags', [])
        
        # Select voice and matching representative name
        voice_id, representative_name = self._select_voice_and_name(
            segment, 
            sensitivity_flags,
            language
        )
        
        # Get appropriate greeting and closing
        greeting_template = self.config['greetings'].get(
            language, self.config['greetings']['English']
        ).get(segment, self.config['greetings']['English']['ASSISTED'])
        
        # Select closing based on sensitivity
        if sensitivity_flags:
            closing_text = self.config['closings'].get(
                language, self.config['closings']['English']
            ).get('SENSITIVE', self.config['closings']['English']['ASSISTED'])
        else:
            closing_text = self.config['closings'].get(
                language, self.config['closings']['English']
            ).get(segment, self.config['closings']['English']['ASSISTED'])
        
        # Format greeting with dynamic representative name
        first_name = customer.get('name', '').split()[0] if customer.get('name') else 'there'
        last_name = customer.get('name', '').split()[-1] if customer.get('name') and len(customer.get('name').split()) > 1 else ''
        
        greeting = greeting_template.format(
            customer_name=first_name,
            first_name=first_name,
            last_name=last_name,
            rep_name=representative_name,  # Use the matched representative name
            time_of_day="morning",
            title="Mr" if customer.get('gender') == 'M' else "Ms"
        )
        
        # Build AI prompt with voice/name information
        prompt = self._build_ai_prompt(
            shared_context.original_letter,
            customer,
            insights,
            strategy,
            content_strategy,
            greeting,
            closing_text,
            language,
            voice_id,
            representative_name,
            sensitivity_flags
        )
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text.strip()
            voice_data = self._parse_ai_response(content)
            
            if voice_data:
                return self._create_result_from_data(
                    voice_data, 
                    shared_context,
                    language,
                    "ai_generation",
                    voice_id,
                    representative_name
                )
            
        except Exception as e:
            print(f"  ❌ AI generation error: {e}")
        
        return self._generate_fallback(shared_context)
    
    def _build_ai_prompt(
        self,
        letter: str,
        customer: Dict,
        insights,
        strategy,
        content_strategy,
        greeting: str,
        closing: str,
        language: str,
        voice_id: str,
        representative_name: str,
        sensitivity_flags: List[str]
    ) -> str:
        """Build AI prompt for voice script generation with voice/name info"""
        
        # Get critical points
        critical_points = [p.content for p in content_strategy.critical_points[:3]]
        
        # Get voice characteristics for context
        voice_info = self.config['tts']['openai']['voice_characteristics'].get(voice_id, {})
        voice_style = voice_info.get('style', 'professional')
        
        sensitivity_context = ""
        if sensitivity_flags:
            sensitivity_context = f"""
SENSITIVITY: Customer has {', '.join(sensitivity_flags)}
- Use extra warm, supportive tone
- Speak slightly slower
- Be gentle and understanding
"""
        
        return f"""Generate a NATURAL VOICE SCRIPT in {language} for a phone message.

VOICE CONTEXT:
- Representative Name: {representative_name}
- Voice Style: {voice_style}
- Voice ID: {voice_id}
{sensitivity_context}

CUSTOMER:
- Name: {customer.get('name')}
- Language: {language} (ENTIRE SCRIPT MUST BE IN {language.upper()})
- Segment: {insights.segment}
- Life Stage: {insights.life_stage}
- Special Context: {customer.get('recent_life_events', 'None')}

KEY POINTS TO CONVEY:
{chr(10).join(['• ' + point for point in critical_points])}

REQUIREMENTS:
- Language: {language} (NOT ENGLISH unless that's the preferred language)
- Start EXACTLY with: "{greeting}"
- End with: "{closing}"
- Length: 50-80 words (30-45 seconds spoken)
- Natural conversational tone matching {voice_style}
- Reference ONE personal detail
- Sound warm and human
- The representative is {representative_name} (already in greeting)

Generate JSON:
{{
    "script": "Complete script in {language} starting with exact greeting",
    "pace": "slow|normal|fast",
    "emphasis": ["key", "words"],
    "personalizations": ["what was personalized"],
    "tone_markers": ["warm", "professional", etc]
}}

CRITICAL: 
- Start with the EXACT greeting provided
- Write the ENTIRE script in {language}, not English!
- Match the tone to {voice_style}"""
    
    def _parse_ai_response(self, content: str) -> Optional[Dict]:
        """Parse AI response"""
        content = content.replace('```json', '').replace('```', '').strip()
        
        try:
            return json.loads(content)
        except:
            if '{' in content and '}' in content:
                try:
                    start = content.index('{')
                    end = content.rindex('}') + 1
                    return json.loads(content[start:end])
                except:
                    pass
        return None
    
    def _create_result_from_data(
        self,
        data: Dict,
        shared_context: SharedContext,
        language: str,
        method: str,
        voice_id: str,
        representative_name: str
    ) -> VoiceResult:
        """Create VoiceResult from parsed data with voice/name info"""
        
        script = data.get('script', '')
        word_count = len(script.split())
        pace = data.get('pace', 'normal')
        
        # Calculate duration
        wpm = {'slow': 120, 'normal': 150, 'fast': 180}.get(pace, 150)
        duration = (word_count / wpm) * 60
        
        return VoiceResult(
            content=script,
            duration_estimate=duration,
            word_count=word_count,
            speaking_pace=pace,
            tone_markers=data.get('tone_markers', ['warm', 'professional']),
            personalization_elements=data.get('personalizations', []),
            emphasis_words=data.get('emphasis', []),
            language=language,
            generation_method=method,
            processing_time=0.0,
            quality_score=0.8,
            audio_file_path=None,  # Will be set after audio generation
            audio_format="mp3",
            tts_engine_used="pending",
            voice_used=voice_id,
            representative_name=representative_name
        )
    
    def _generate_fallback(self, shared_context: SharedContext) -> VoiceResult:
        """Generate fallback script when AI unavailable - FIXED with voice matching"""
        
        customer = shared_context.customer_data
        name = customer.get('name', '').split()[0] if customer.get('name') else 'there'
        language = customer.get('preferred_language', 'English')
        segment = shared_context.customer_insights.segment
        sensitivity_flags = getattr(shared_context.customer_insights, 'sensitivity_flags', [])
        
        # Select voice and name for fallback
        voice_id, representative_name = self._select_voice_and_name(
            segment,
            sensitivity_flags,
            language
        )
        
        # Build greeting with matched representative
        if language == 'English':
            greeting = f"Hello {name}, this is {representative_name} from Lloyds Bank."
            middle = "We have important information about your account. Please check your mail for the full details."
            closing = "Thank you for your time. We're here if you need us."
        else:
            # Other languages would have their own templates
            greeting = f"Hello {name}, this is {representative_name} from Lloyds Bank."
            middle = "We have important information about your account."
            closing = "Thank you."
        
        script = f"{greeting} {middle} {closing}"
        
        word_count = len(script.split())
        duration = (word_count / 150) * 60
        
        return VoiceResult(
            content=script,
            duration_estimate=duration,
            word_count=word_count,
            speaking_pace='normal',
            tone_markers=['professional'],
            personalization_elements=['customer_name', 'language'],
            emphasis_words=['important'],
            language=language,
            generation_method='fallback',
            processing_time=0.0,
            quality_score=0.6,
            audio_file_path=None,
            audio_format="mp3",
            tts_engine_used="none",
            voice_used=voice_id,
            representative_name=representative_name
        )
    
    def _create_disabled_result(self, shared_context: SharedContext) -> VoiceResult:
        """Create empty result when voice is disabled"""
        return VoiceResult(
            content="",
            duration_estimate=0.0,
            word_count=0,
            speaking_pace='normal',
            tone_markers=[],
            personalization_elements=[],
            emphasis_words=[],
            language=shared_context.customer_data.get('preferred_language', 'English'),
            generation_method='disabled',
            processing_time=0.0,
            quality_score=0.0,
            audio_file_path=None,
            audio_format="mp3",
            tts_engine_used="none",
            voice_used="none",
            representative_name=""
        )
    
    def validate_voice_note(self, result: VoiceResult, shared_context: SharedContext) -> Dict:
        """Validate the generated voice note including voice/name match"""
        validation = {
            'is_valid': True,
            'issues': [],
            'achievements': [],
            'metrics': {
                'duration': f"{result.duration_estimate:.1f}s",
                'language': result.language,
                'has_audio': result.audio_file_path is not None,
                'voice': result.voice_used,
                'representative': result.representative_name
            }
        }
        
        # Check duration
        if result.duration_estimate < self.config['durations']['min']:
            validation['issues'].append("Too short")
            validation['is_valid'] = False
        elif result.duration_estimate > self.config['durations']['max']:
            validation['issues'].append("Too long")
            validation['is_valid'] = False
        
        # Check language match
        expected_lang = shared_context.customer_data.get('preferred_language', 'English')
        if result.language == expected_lang:
            validation['achievements'].append(f"Correct language: {expected_lang}")
        else:
            validation['issues'].append(f"Wrong language: expected {expected_lang}, got {result.language}")
            validation['is_valid'] = False
        
        # Check voice/name matching
        if result.voice_used and result.representative_name:
            voice_info = self.config['tts']['openai']['voice_characteristics'].get(result.voice_used, {})
            if result.representative_name in voice_info.get('names', []):
                validation['achievements'].append(f"Voice/name match: {result.voice_used} → {result.representative_name}")
            else:
                validation['issues'].append(f"Voice/name mismatch: {result.voice_used} with {result.representative_name}")
        
        # Check audio generation
        if result.audio_file_path:
            validation['achievements'].append(f"Audio generated: {result.tts_engine_used}")
        elif result.generation_method != 'disabled':
            validation['issues'].append("No audio file generated")
        
        # Check sensitivity handling
        sensitivity_flags = getattr(shared_context.customer_insights, 'sensitivity_flags', [])
        if sensitivity_flags:
            if result.voice_used == 'shimmer' or 'gentle' in str(result.tone_markers):
                validation['achievements'].append("Appropriate voice for sensitive customer")
            else:
                validation['issues'].append("Could use more appropriate voice for sensitive situation")
        
        return validation

# Convenience function
def generate_smart_voice_note(shared_context: SharedContext, api_key: Optional[str] = None) -> VoiceResult:
    """Generate voice note with audio - properly matched voice and name"""
    generator = SmartVoiceGenerator(api_key=api_key)
    return generator.generate_voice_note(shared_context)