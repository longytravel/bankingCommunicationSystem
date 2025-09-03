"""
Smart Voice Note Generator - Self-contained with configuration
Uses SharedContext for Consistent, Natural Voice Messages
FIXED: Proper language support and personalization following SMS/Letter structure
"""

import os
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import base64
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

# TTS imports (for actual voice generation)
try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("⚠️ pyttsx3 not available - voice synthesis disabled")

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
    audio_data: Optional[str] = None  # Base64 encoded audio if available

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
                'greeting': {
                    'English': 'Hi {first_name}, this is {bank_rep} from Lloyds',
                    'Spanish': 'Hola {first_name}, soy {bank_rep} de Lloyds',
                    'French': 'Bonjour {first_name}, c\'est {bank_rep} de Lloyds',
                    'Chinese': '你好 {first_name}，我是来自劳埃德银行的 {bank_rep}'
                },
                'closing': {
                    'English': 'Thanks for being with Lloyds. Have a great day!',
                    'Spanish': '¡Gracias por estar con Lloyds. Que tengas un gran día!',
                    'French': 'Merci d\'être avec Lloyds. Bonne journée!',
                    'Chinese': '感谢您选择劳埃德银行。祝您愉快！'
                },
                'tone': 'friendly',
                'pace': 'normal'
            },
            'ASSISTED': {
                'style': 'professional_warm',
                'greeting': {
                    'English': 'Hello {first_name}, this is {bank_rep} calling from Lloyds Bank',
                    'Spanish': 'Hola {first_name}, le habla {bank_rep} del Banco Lloyds',
                    'French': 'Bonjour {first_name}, c\'est {bank_rep} qui vous appelle de la Banque Lloyds',
                    'Chinese': '您好 {first_name}，我是劳埃德银行的 {bank_rep}'
                },
                'closing': {
                    'English': 'Thank you for your time. If you need anything, we\'re here to help.',
                    'Spanish': 'Gracias por su tiempo. Si necesita algo, estamos aquí para ayudarle.',
                    'French': 'Merci pour votre temps. Si vous avez besoin de quoi que ce soit, nous sommes là pour vous aider.',
                    'Chinese': '感谢您的时间。如果您需要任何帮助，我们随时为您服务。'
                },
                'tone': 'professional_friendly',
                'pace': 'normal'
            },
            'TRADITIONAL': {
                'style': 'formal_respectful',
                'greeting': {
                    'English': 'Good {time_of_day} {title} {last_name}, this is {bank_rep} from Lloyds Banking Group',
                    'Spanish': 'Buenos {time_of_day} {title} {last_name}, le habla {bank_rep} del Grupo Bancario Lloyds',
                    'French': 'Bonjour {title} {last_name}, c\'est {bank_rep} du Groupe Bancaire Lloyds',
                    'Chinese': '您好 {title} {last_name}，我是劳埃德银行集团的 {bank_rep}'
                },
                'closing': {
                    'English': 'Thank you for your attention. Please don\'t hesitate to contact your branch if you need assistance.',
                    'Spanish': 'Gracias por su atención. Por favor, no dude en contactar con su sucursal si necesita ayuda.',
                    'French': 'Merci pour votre attention. N\'hésitez pas à contacter votre agence si vous avez besoin d\'aide.',
                    'Chinese': '感谢您的关注。如需帮助，请随时联系您的分行。'
                },
                'tone': 'formal',
                'pace': 'slow'
            }
        },
        'time_of_day': {
            'English': {'morning': 'morning', 'afternoon': 'afternoon', 'evening': 'evening'},
            'Spanish': {'morning': 'días', 'afternoon': 'tardes', 'evening': 'tardes'},
            'French': {'morning': 'jour', 'afternoon': 'après-midi', 'evening': 'soir'},
            'Chinese': {'morning': '早上', 'afternoon': '下午', 'evening': '晚上'}
        },
        'titles': {
            'English': {'M': 'Mr', 'F': 'Ms', 'U': ''},
            'Spanish': {'M': 'Sr.', 'F': 'Sra.', 'U': ''},
            'French': {'M': 'M.', 'F': 'Mme', 'U': ''},
            'Chinese': {'M': '先生', 'F': '女士', 'U': ''}
        },
        'callback_text': {
            'English': 'If you have any questions or need to discuss this, please call us back on 0345 300 0000.',
            'Spanish': 'Si tiene alguna pregunta o necesita discutir esto, por favor llámenos al 0345 300 0000.',
            'French': 'Si vous avez des questions ou besoin de discuter, veuillez nous rappeler au 0345 300 0000.',
            'Chinese': '如果您有任何问题或需要讨论，请致电 0345 300 0000。'
        },
        'natural_speech_patterns': {
            'use_contractions': True,  # "we're" instead of "we are"
            'add_filler_words': False,  # Avoid "um", "uh"
            'conversational_tone': True,
            'personal_anecdotes': False
        },
        'content_structure': {
            'include_purpose_upfront': True,
            'use_signposting': True,
            'summarize_key_points': True,
            'offer_callback': True,
            'mention_other_channels': True
        },
        'quality_thresholds': {
            'min_clarity_score': 0.8,
            'max_information_density': 0.7,
            'min_personalization': 2,
            'optimal_sentence_length': 15
        }
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the smart voice generator"""
        self.api_key = api_key or os.getenv('CLAUDE_API_KEY')
        self.client = None
        self.config = self.VOICE_CONFIG
        
        print(f"🎙️ Initializing Smart Voice Generator...")
        
        if self.api_key and ANTHROPIC_AVAILABLE:
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
                self.model = "claude-3-5-sonnet-20241022"
                print(f"   ✅ Claude AI client initialized (key: {self.api_key[:10]}...)")
            except Exception as e:
                print(f"   ❌ Failed to initialize Claude client: {e}")
                self.client = None
        else:
            if not ANTHROPIC_AVAILABLE:
                print("   ⚠️ Anthropic library not available - install with: pip install anthropic")
            if not self.api_key:
                print("   ⚠️ No API key found - set CLAUDE_API_KEY environment variable")
            print("   ⚠️ Smart Voice Generator running in simulation mode")
        
        # Initialize TTS engine if available
        self.tts_engine = None
        if TTS_AVAILABLE:
            try:
                self.tts_engine = pyttsx3.init()
                # Configure TTS settings
                self.tts_engine.setProperty('rate', 150)  # Words per minute
                self.tts_engine.setProperty('volume', 1.0)  # Volume level (0.0 to 1.0)
                print("   ✅ Text-to-speech engine initialized")
            except:
                print("   ⚠️ TTS engine initialization failed")
    
    def generate_voice_note(self, shared_context: SharedContext) -> VoiceResult:
        """
        Generate a perfectly personalized voice note script using the Shared Brain's intelligence
        """
        start_time = datetime.now()
        
        print(f"🎙️ Generating smart voice note for {shared_context.customer_data.get('name')}...")
        
        # Check if voice is enabled
        if not shared_context.channel_decisions['enabled_channels'].get('voice', True):
            return self._create_disabled_result(shared_context, "Voice disabled by rules")
        
        if self.client:
            result = self._generate_with_ai(shared_context)
        else:
            result = self._generate_fallback(shared_context)
        
        # Generate actual audio if TTS is available
        if self.tts_engine and result.content:
            result.audio_data = self._generate_audio(result.content, result.language)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        result.processing_time = processing_time
        
        print(f"✅ Smart voice note generated in {processing_time:.2f}s")
        print(f"   Duration: {result.duration_estimate:.1f}s, Language: {result.language}, Quality: {result.quality_score:.2%}")
        
        return result
    
    def _generate_with_ai(self, shared_context: SharedContext) -> VoiceResult:
        """Generate voice note using AI with proper language support"""
        
        # Extract intelligence
        customer = shared_context.customer_data
        insights = shared_context.customer_insights
        strategy = shared_context.personalization_strategy
        content_strategy = shared_context.content_strategy
        
        # Get language preference
        language = customer.get('preferred_language', 'English')
        
        # Get configuration
        segment = insights.segment
        greeting_config = self.config['greeting_styles'].get(segment, self.config['greeting_styles']['ASSISTED'])
        
        # Determine if callback needed
        doc_type = shared_context.document_classification.get('primary_classification', 'INFORMATIONAL')
        urgency = shared_context.document_classification.get('urgency_level', 'LOW')
        requires_callback = (
            doc_type in ['URGENT', 'REGULATORY'] or
            urgency == 'HIGH' or
            shared_context.document_classification.get('customer_action_required', False)
        )
        
        # Build prompt with language support
        generation_prompt = self._build_generation_prompt(
            shared_context.original_letter,
            customer,
            insights,
            strategy,
            content_strategy,
            greeting_config,
            doc_type,
            requires_callback,
            language
        )
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.6,  # Balanced for natural speech
                messages=[{"role": "user", "content": generation_prompt}]
            )
            
            content = response.content[0].text.strip()
            voice_data = self._parse_ai_response(content)
            
            if voice_data:
                return self._create_voice_result(
                    voice_data, 
                    shared_context, 
                    "ai_generation", 
                    requires_callback,
                    language
                )
            else:
                print("⚠️ Failed to parse AI response, using fallback")
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
        doc_type: str,
        requires_callback: bool,
        language: str
    ) -> str:
        """Build the voice generation prompt with language support"""
        
        # Get critical and important points for voice
        critical_points = [p.content for p in content_strategy.critical_points[:2]]
        important_points = [p.content for p in content_strategy.important_points[:1]]
        
        # Format greeting based on language
        first_name = customer.get('name', '').split()[0] if customer.get('name') else customer.get('name', 'there')
        last_name = customer.get('name', '').split()[-1] if customer.get('name') and len(customer.get('name', '').split()) > 1 else ''
        
        # Get time of day
        hour = datetime.now().hour
        if hour < 12:
            time_period = 'morning'
        elif hour < 17:
            time_period = 'afternoon'
        else:
            time_period = 'evening'
        
        time_of_day = self.config['time_of_day'].get(language, {}).get(time_period, time_period)
        title = self.config['titles'].get(language, {}).get(customer.get('gender', 'U'), '')
        
        # Get greeting and closing in the correct language
        greeting_template = greeting_config['greeting'].get(language, greeting_config['greeting']['English'])
        closing = greeting_config['closing'].get(language, greeting_config['closing']['English'])
        callback_text = self.config['callback_text'].get(language, self.config['callback_text']['English'])
        
        greeting = greeting_template.format(
            first_name=first_name,
            bank_rep="Sarah",  # Could be dynamic based on language
            time_of_day=time_of_day,
            title=title,
            last_name=last_name
        )
        
        # Calculate target duration
        pace = greeting_config['pace']
        wpm = self.config['speaking_rates'][pace]
        target_words = int(self.config['optimal_duration'] * wpm / 60)
        
        # Get personalization hooks in natural language
        hooks = strategy.must_mention[:2] if strategy.must_mention else []
        life_events = insights.special_factors[:1] if insights.special_factors else []
        
        prompt = f"""Generate a natural, conversational VOICE NOTE SCRIPT for a phone message to a bank customer.

CRITICAL: This will be SPOKEN ALOUD in {language}, so write exactly how someone would naturally speak on the phone in {language}.

CUSTOMER CONTEXT:
- Name: {customer.get('name')}
- Segment: {insights.segment}
- Life Stage: {insights.life_stage}
- Financial Profile: {insights.financial_profile}
- Communication Style: {insights.communication_style}
- Special Context: {', '.join(life_events) if life_events else 'None'}
- Language: {language}

PERSONALIZATION MUST-MENTIONS:
{chr(10).join(['• ' + hook for hook in hooks]) if hooks else '• Reference their situation naturally'}

ORIGINAL LETTER CONTENT:
{original_letter[:800]}

KEY INFORMATION TO CONVEY (MUST include these):
CRITICAL:
{chr(10).join(['• ' + point for point in critical_points])}

IMPORTANT (include if space):
{chr(10).join(['• ' + point for point in important_points])}

VOICE REQUIREMENTS:
- Language: Write ENTIRELY in {language}
- Start: "{greeting}"
- Tone: {greeting_config['tone']} and warm
- Length: Around {target_words} words (about {self.config['optimal_duration']} seconds)
- End: "{closing}"
{"- MUST include: " + callback_text if requires_callback else ""}

PERSONALIZATION REQUIREMENTS:
- Reference specific things about the customer: {', '.join(hooks[:2]) if hooks else insights.customer_story}
- Make natural connections to their {insights.life_stage} life stage
- Sound like you know their situation
- Use their name naturally 2-3 times
- Reference their {insights.financial_profile} profile appropriately

SPEECH PATTERNS for {language}:
- Write as NATURAL SPOKEN {language}, not formal written text
- Use appropriate contractions/informal speech for {language}
- Break up long sentences for breathing
- Sound warm and human, not robotic
- Include natural transitions
- Use culturally appropriate expressions

Generate as JSON (but with content in {language}):
{{
    "voice_script": "Complete natural speech script in {language} with '...' for pauses",
    "tone_markers": ["warm", "urgent", "friendly", etc],
    "emphasis_words": ["words to stress in the language"],
    "personalization_elements": ["specific personalizations applied"],
    "natural_pauses": [15, 30, 45],
    "speaking_pace": "{pace}"
}}

IMPORTANT: The voice_script MUST be entirely in {language}, naturally incorporating ALL the key information and personalization."""
        
        return prompt
    
    def _parse_ai_response(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse the AI response with robust error handling"""
        
        # Remove markdown formatting if present
        content = content.replace('```json', '').replace('```', '').strip()
        
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
                
                # Clean JSON while preserving Unicode for other languages
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
        requires_callback: bool,
        language: str
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
            language=language,
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
                score += 0.2
            else:
                score += 0.1
        
        # Check personalization
        if len(personalization_elements) >= self.config['quality_thresholds']['min_personalization']:
            score += 0.2
        elif len(personalization_elements) >= 1:
            score += 0.1
        
        # Check for must-mention items
        must_mention_found = 0
        for item in shared_context.personalization_strategy.must_mention:
            # Check for key words from must-mention items
            item_words = item.lower().split()
            key_words = [w for w in item_words if len(w) > 3]
            if key_words and any(word in script.lower() for word in key_words):
                must_mention_found += 1
        
        if must_mention_found > 0:
            score += 0.1 + (must_mention_found * 0.05)
        
        # Check sentence structure
        sentences = re.split(r'[.!?]', script)
        if sentences:
            avg_length = sum(len(s.split()) for s in sentences if s.strip()) / len([s for s in sentences if s.strip()])
            if avg_length <= self.config['quality_thresholds']['optimal_sentence_length']:
                score += 0.05
        
        # Bonus for natural speech patterns
        if '...' in script:  # Has pauses
            score += 0.05
        
        return min(1.0, score)
    
    def _generate_fallback(self, shared_context: SharedContext) -> VoiceResult:
        """Generate fallback voice note with language support"""
        
        customer = shared_context.customer_data
        insights = shared_context.customer_insights
        name = customer.get('name', 'there').split()[0]
        language = customer.get('preferred_language', 'English')
        segment = insights.segment
        
        # Get greeting config
        greeting_config = self.config['greeting_styles'].get(segment, self.config['greeting_styles']['ASSISTED'])
        
        # Get language-specific templates
        greeting = greeting_config['greeting'].get(language, greeting_config['greeting']['English']).format(
            first_name=name,
            bank_rep="Sarah",
            time_of_day="",
            title="",
            last_name=""
        )
        closing = greeting_config['closing'].get(language, greeting_config['closing']['English'])
        callback_text = self.config['callback_text'].get(language, self.config['callback_text']['English'])
        
        # Extract key points from letter
        letter_preview = shared_context.original_letter[:200]
        
        # Build fallback script based on language
        if language == 'Spanish':
            script = f"""{greeting}

Tengo una actualización importante sobre su cuenta. {letter_preview}...

{callback_text}

{closing}"""
        elif language == 'French':
            script = f"""{greeting}

J'ai une mise à jour importante concernant votre compte. {letter_preview}...

{callback_text}

{closing}"""
        elif language == 'Chinese':
            script = f"""{greeting}

我有一个关于您账户的重要更新。{letter_preview}...

{callback_text}

{closing}"""
        else:  # English
            script = f"""{greeting}

I have an important update about your account. {letter_preview}...

{callback_text}

{closing}"""
        
        word_count = len(script.split())
        duration = (word_count / 150) * 60
        
        return VoiceResult(
            content=script,
            duration_estimate=duration,
            word_count=word_count,
            speaking_pace='normal',
            tone_markers=['friendly', 'informative'],
            personalization_elements=['customer_name', 'segment_appropriate'],
            natural_pauses=[20, 40],
            emphasis_words=['important', 'importante', 'important', '重要'],
            language=language,
            generation_method='fallback',
            processing_time=0.0,
            quality_score=0.6,
            requires_callback=True
        )
    
    def _generate_simulation(self, shared_context: SharedContext) -> VoiceResult:
        """Generate simulation voice note with language support"""
        
        customer = shared_context.customer_data
        insights = shared_context.customer_insights
        name = customer.get('name', 'Customer').split()[0]
        language = customer.get('preferred_language', 'English')
        
        # Create simulation in appropriate language
        if language == 'Spanish':
            script = f"""[SIMULACIÓN DE NOTA DE VOZ]
            
Hola {name}, este es un mensaje de voz de prueba de Lloyds.

Segmento: {insights.segment}
Personalización: {shared_context.personalization_strategy.level.value}

[El script de voz se generaría aquí]

¡Gracias por escuchar!"""
        else:  # Default to English for simulation
            script = f"""[SIMULATED VOICE NOTE]
            
Hi {name}, this is a test voice message from Lloyds.

Segment: {insights.segment}
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
            language=language,
            generation_method='simulation',
            processing_time=0.0,
            quality_score=0.8,
            requires_callback=False
        )
    
    def _generate_audio(self, text: str, language: str) -> Optional[str]:
        """Generate actual audio from text using TTS"""
        if not self.tts_engine:
            return None
        
        try:
            # Configure voice for language
            voices = self.tts_engine.getProperty('voices')
            
            # Try to select appropriate voice for language
            for voice in voices:
                if language == 'Spanish' and 'spanish' in voice.name.lower():
                    self.tts_engine.setProperty('voice', voice.id)
                    break
                elif language == 'French' and 'french' in voice.name.lower():
                    self.tts_engine.setProperty('voice', voice.id)
                    break
                elif language == 'Chinese' and ('chinese' in voice.name.lower() or 'mandarin' in voice.name.lower()):
                    self.tts_engine.setProperty('voice', voice.id)
                    break
            
            # Generate audio to temporary file
            temp_file = f"temp_voice_{hashlib.md5(text.encode()).hexdigest()}.mp3"
            self.tts_engine.save_to_file(text, temp_file)
            self.tts_engine.runAndWait()
            
            # Read and encode as base64
            with open(temp_file, 'rb') as f:
                audio_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Clean up temp file
            os.remove(temp_file)
            
            return audio_data
            
        except Exception as e:
            print(f"Audio generation error: {e}")
            return None
    
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
            language=shared_context.customer_data.get('preferred_language', 'English'),
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
                'language': voice_result.language,
                'requires_callback': voice_result.requires_callback
            }
        }
        
        # Check duration
        if voice_result.duration_estimate < self.config['min_duration']:
            validation['issues'].append("Too short for voice note")
            validation['is_valid'] = False
        elif voice_result.duration_estimate > self.config['max_duration']:
            validation['issues'].append("Too long - consider breaking up")
            validation['is_valid'] = False
        else:
            validation['achievements'].append(f"Good length: {voice_result.duration_estimate:.0f}s")
        
        # Check personalization
        if len(voice_result.personalization_elements) >= self.config['quality_thresholds']['min_personalization']:
            validation['achievements'].append(f"Well personalized ({len(voice_result.personalization_elements)} elements)")
        else:
            validation['issues'].append("Needs more personalization")
        
        # Check language
        expected_lang = shared_context.customer_data.get('preferred_language', 'English')
        if voice_result.language == expected_lang:
            validation['achievements'].append(f"Correct language: {expected_lang}")
        else:
            validation['issues'].append(f"Language mismatch: expected {expected_lang}, got {voice_result.language}")
            validation['is_valid'] = False
        
        # Check tone
        if voice_result.tone_markers:
            validation['achievements'].append(f"Natural tone: {', '.join(voice_result.tone_markers[:2])}")
        
        return validation

# Convenience function
def generate_smart_voice_note(shared_context: SharedContext, api_key: Optional[str] = None) -> VoiceResult:
    """Generate a smart voice note from shared context"""
    generator = SmartVoiceGenerator(api_key=api_key)
    return generator.generate_voice_note(shared_context)