"""
Smart Voice Note Generator - Complete Rewrite with OpenAI TTS
Uses SharedContext for Consistent, Natural Voice Messages with Proper Language Support
"""

import os
import json
import re
import time
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import OpenAI for TTS
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI not available - install with: pip install openai")

# Import Anthropic for script generation
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("⚠️ Anthropic not available - install with: pip install anthropic")

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
    """Result from voice note generation"""
    content: str  # The script/text for the voice note
    duration_estimate: float  # Estimated duration in seconds
    word_count: int
    speaking_pace: str  # slow, normal, fast
    tone_markers: List[str]  # Emotional tone markers
    personalization_elements: List[str]
    natural_pauses: List[int]  # Word positions where pauses should occur
    emphasis_words: List[str]  # Words to emphasize
    language: str
    generation_method: str
    processing_time: float
    quality_score: float
    requires_callback: bool
    audio_file_path: Optional[str] = None  # Path to generated audio file
    audio_data: Optional[str] = None  # Base64 encoded audio

class SmartVoiceGenerator:
    """
    Smart Voice Note Generator with OpenAI TTS Support
    Generates personalized, natural voice messages in multiple languages
    """
    
    # Voice Configuration
    VOICE_CONFIG = {
        'max_duration': 90,  # Maximum 90 seconds
        'optimal_duration': 45,  # Ideal 45 seconds
        'min_duration': 15,  # Minimum 15 seconds
        'speaking_rates': {
            'slow': 120,     # words per minute
            'normal': 150,   # words per minute  
            'fast': 180      # words per minute
        },
        'openai_voices': {
            # Voice selection by language and tone
            'English': {
                'professional': 'alloy',
                'friendly': 'nova',
                'warm': 'shimmer',
                'authoritative': 'onyx'
            },
            'Spanish': {
                'professional': 'alloy',
                'friendly': 'nova',  # Nova works well for Spanish
                'warm': 'shimmer',
                'authoritative': 'echo'
            },
            'French': {
                'professional': 'alloy',
                'friendly': 'shimmer',
                'warm': 'nova',
                'authoritative': 'onyx'
            },
            'Chinese': {
                'professional': 'alloy',
                'friendly': 'nova',
                'warm': 'shimmer',
                'authoritative': 'echo'
            }
        },
        'greetings': {
            'English': {
                'morning': 'Good morning',
                'afternoon': 'Good afternoon', 
                'evening': 'Good evening'
            },
            'Spanish': {
                'morning': 'Buenos días',
                'afternoon': 'Buenas tardes',
                'evening': 'Buenas tardes'
            },
            'French': {
                'morning': 'Bonjour',
                'afternoon': 'Bonjour',
                'evening': 'Bonsoir'
            },
            'Chinese': {
                'morning': '早上好',
                'afternoon': '下午好',
                'evening': '晚上好'
            }
        }
    }
    
    def __init__(self, api_key: Optional[str] = None, openai_key: Optional[str] = None):
        """Initialize the voice generator with both Claude and OpenAI"""
        
        print("🎙️ Initializing Smart Voice Generator...")
        
        # Initialize Claude for script generation
        self.claude_key = api_key or os.getenv('CLAUDE_API_KEY')
        self.claude_client = None
        
        if self.claude_key and ANTHROPIC_AVAILABLE:
            try:
                self.claude_client = anthropic.Anthropic(api_key=self.claude_key)
                self.claude_model = "claude-3-5-sonnet-20241022"
                print(f"   ✅ Claude initialized for script generation")
            except Exception as e:
                print(f"   ❌ Claude initialization failed: {e}")
        else:
            print("   ⚠️ Claude not available - will use fallback scripts")
        
        # Initialize OpenAI for TTS
        self.openai_key = openai_key or os.getenv('OPENAI_API_KEY')
        self.openai_client = None
        
        if self.openai_key and OPENAI_AVAILABLE:
            try:
                self.openai_client = OpenAI(api_key=self.openai_key)
                print(f"   ✅ OpenAI initialized for text-to-speech")
            except Exception as e:
                print(f"   ❌ OpenAI initialization failed: {e}")
        else:
            print("   ⚠️ OpenAI not available - audio generation disabled")
        
        # Create voice notes directory
        self.voice_notes_dir = Path("output/voice_notes")
        self.voice_notes_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_voice_note(self, shared_context: SharedContext) -> VoiceResult:
        """
        Main method: Generate a personalized voice note from SharedContext
        """
        start_time = datetime.now()
        
        # Extract customer info
        customer = shared_context.customer_data
        customer_name = customer.get('name', 'Customer')
        language = customer.get('preferred_language', 'English')
        
        print(f"🎙️ Generating voice note for {customer_name} in {language}...")
        
        # Check if voice is enabled
        if not shared_context.channel_decisions['enabled_channels'].get('voice', True):
            return self._create_disabled_result(shared_context)
        
        # Generate script
        if self.claude_client:
            script_result = self._generate_script_with_ai(shared_context)
        else:
            script_result = self._generate_fallback_script(shared_context)
        
        # Generate audio if OpenAI is available
        if self.openai_client and script_result.content:
            audio_path = self._generate_audio_with_openai(
                script_result.content,
                customer_name,
                language,
                shared_context.customer_insights.segment
            )
            script_result.audio_file_path = audio_path
        
        # Calculate final metrics
        processing_time = (datetime.now() - start_time).total_seconds()
        script_result.processing_time = processing_time
        
        print(f"✅ Voice note completed in {processing_time:.2f}s")
        print(f"   Language: {script_result.language}")
        print(f"   Duration: {script_result.duration_estimate:.1f}s")
        print(f"   Quality: {script_result.quality_score:.1%}")
        if script_result.audio_file_path:
            print(f"   Audio: {script_result.audio_file_path}")
        
        return script_result
    
    def _generate_script_with_ai(self, shared_context: SharedContext) -> VoiceResult:
        """Generate voice script using Claude AI"""
        
        # Extract all needed information
        customer = shared_context.customer_data
        insights = shared_context.customer_insights
        strategy = shared_context.personalization_strategy
        content_strategy = shared_context.content_strategy
        
        language = customer.get('preferred_language', 'English')
        name = customer.get('name', 'Customer')
        
        # Build the prompt
        prompt = self._build_ai_prompt(
            shared_context.original_letter,
            customer,
            insights,
            strategy,
            content_strategy,
            language
        )
        
        try:
            # Call Claude
            response = self.claude_client.messages.create(
                model=self.claude_model,
                max_tokens=2000,
                temperature=0.7,  # Higher for more natural speech
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse response
            content = response.content[0].text.strip()
            parsed = self._parse_ai_response(content)
            
            if parsed and 'script' in parsed:
                return self._create_voice_result(parsed, language, "ai_generation")
            else:
                print("   ⚠️ Failed to parse AI response, using fallback")
                return self._generate_fallback_script(shared_context)
                
        except Exception as e:
            print(f"   ❌ AI generation error: {e}")
            return self._generate_fallback_script(shared_context)
    
    def _build_ai_prompt(self, letter: str, customer: Dict, insights: Any, 
                         strategy: Any, content_strategy: Any, language: str) -> str:
        """Build the prompt for Claude to generate voice script"""
        
        # Get critical points
        critical_points = []
        if hasattr(content_strategy, 'critical_points'):
            critical_points = [p.content for p in content_strategy.critical_points[:3]]
        
        # Get time-based greeting
        hour = datetime.now().hour
        if hour < 12:
            time_period = 'morning'
        elif hour < 17:
            time_period = 'afternoon'
        else:
            time_period = 'evening'
        
        greeting = self.VOICE_CONFIG['greetings'].get(language, {}).get(time_period, 'Hello')
        
        prompt = f"""Create a natural, conversational voice message script for a bank customer.

LANGUAGE: {language} - Write ENTIRELY in {language}

CUSTOMER INFO:
- Name: {customer.get('name')}
- Age: {customer.get('age')}
- Segment: {insights.segment}
- Life Stage: {insights.life_stage}
- Recent Events: {', '.join(insights.special_factors[:2]) if insights.special_factors else 'None'}
- Financial Profile: {insights.financial_profile}

PERSONALIZATION REQUIREMENTS:
- Must mention: {', '.join(strategy.must_mention[:2]) if strategy.must_mention else 'general update'}
- Customer story: {strategy.customer_story}
- Tone: {insights.communication_style}

ORIGINAL LETTER KEY CONTENT:
{letter[:500]}

CRITICAL POINTS TO INCLUDE:
{chr(10).join(['• ' + point for point in critical_points])}

REQUIREMENTS:
1. Start with: "{greeting} [name], this is [bank representative] from Lloyds Bank"
2. Write in natural, conversational {language}
3. Length: 80-120 words (about 45 seconds when spoken)
4. Include personal touches based on their life stage/events
5. Sound warm and human, not robotic
6. End with callback offer if action is required

Generate a JSON response:
{{
    "script": "Complete voice script in {language}",
    "personalization_used": ["list", "of", "personal", "elements"],
    "tone": "friendly/professional/warm",
    "emphasis_words": ["important", "words", "to", "stress"]
}}

Write the script as someone would naturally speak on the phone in {language}."""
        
        return prompt
    
    def _generate_fallback_script(self, shared_context: SharedContext) -> VoiceResult:
        """Generate fallback script when AI is not available"""
        
        customer = shared_context.customer_data
        insights = shared_context.customer_insights
        language = customer.get('preferred_language', 'English')
        name = customer.get('name', 'Customer').split()[0]
        
        # Extract key message from letter
        letter_sentences = shared_context.original_letter.split('.')
        key_message = '. '.join(letter_sentences[:2]).strip()
        
        # Clean up template markers
        key_message = re.sub(r'\[.*?\]', '', key_message)
        key_message = re.sub(r'Dear.*?,\s*', '', key_message, count=1)
        
        # Build script based on language
        scripts = {
            'English': f"""Hello {name}, this is Sarah from Lloyds Bank.

I'm calling with an important update about your account. {key_message}.

We've sent you a letter with all the details, but wanted to make sure you received this important information.

If you have any questions, please call us back on 0345 300 0000. Thank you for banking with Lloyds.""",
            
            'Spanish': f"""Hola {name}, soy Sarah del Banco Lloyds.

Le llamo con una actualización importante sobre su cuenta. {key_message}.

Le hemos enviado una carta con todos los detalles, pero queríamos asegurarnos de que recibiera esta información importante.

Si tiene alguna pregunta, por favor llámenos al 0345 300 0000. Gracias por confiar en Lloyds.""",
            
            'French': f"""Bonjour {name}, c'est Sarah de la Banque Lloyds.

Je vous appelle avec une mise à jour importante concernant votre compte. {key_message}.

Nous vous avons envoyé une lettre avec tous les détails, mais nous voulions nous assurer que vous receviez cette information importante.

Si vous avez des questions, veuillez nous rappeler au 0345 300 0000. Merci de faire confiance à Lloyds.""",
            
            'Chinese': f"""您好 {name}，我是劳埃德银行的Sarah。

我打电话是要告诉您关于您账户的重要更新。{key_message}。

我们已经寄给您一封包含所有详细信息的信件，但想确保您收到这个重要信息。

如有任何问题，请致电0345 300 0000。感谢您选择劳埃德银行。"""
        }
        
        script = scripts.get(language, scripts['English'])
        
        return self._create_voice_result(
            {
                'script': script,
                'personalization_used': ['customer_name', 'key_message'],
                'tone': 'friendly',
                'emphasis_words': ['important', 'importante', 'important', '重要']
            },
            language,
            "fallback"
        )
    
    def _parse_ai_response(self, content: str) -> Optional[Dict]:
        """Parse the JSON response from Claude"""
        try:
            # Remove markdown if present
            content = content.replace('```json', '').replace('```', '').strip()
            
            # Try to find JSON
            if '{' in content and '}' in content:
                start = content.index('{')
                end = content.rindex('}') + 1
                json_str = content[start:end]
                return json.loads(json_str)
        except Exception as e:
            print(f"   Failed to parse JSON: {e}")
        return None
    
    def _create_voice_result(self, data: Dict, language: str, method: str) -> VoiceResult:
        """Create VoiceResult from parsed data"""
        
        script = data.get('script', '')
        word_count = len(script.split())
        duration = (word_count / 150) * 60  # seconds
        
        # Calculate quality score
        quality = 0.5  # Base
        if method == "ai_generation":
            quality += 0.3
        if len(data.get('personalization_used', [])) > 2:
            quality += 0.1
        if language != 'English':  # Bonus for handling other languages
            quality += 0.1
        
        return VoiceResult(
            content=script,
            duration_estimate=duration,
            word_count=word_count,
            speaking_pace='normal',
            tone_markers=[data.get('tone', 'friendly')],
            personalization_elements=data.get('personalization_used', []),
            natural_pauses=[],
            emphasis_words=data.get('emphasis_words', []),
            language=language,
            generation_method=method,
            processing_time=0.0,
            quality_score=min(1.0, quality),
            requires_callback=True
        )
    
    def _generate_audio_with_openai(self, script: str, customer_name: str, 
                                   language: str, segment: str) -> Optional[str]:
        """Generate audio file using OpenAI TTS"""
        
        if not self.openai_client:
            return None
        
        try:
            # Select voice based on language and segment
            voice_map = self.VOICE_CONFIG['openai_voices'].get(language, {})
            
            # Choose tone based on segment
            if segment == 'DIGITAL':
                tone = 'friendly'
            elif segment == 'TRADITIONAL':
                tone = 'professional'
            else:
                tone = 'warm'
            
            voice = voice_map.get(tone, 'nova')
            
            print(f"   🎵 Generating audio with OpenAI TTS (voice: {voice})...")
            
            # Generate speech
            response = self.openai_client.audio.speech.create(
                model="tts-1",  # or "tts-1-hd" for better quality
                voice=voice,
                input=script
            )
            
            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            customer_id = customer_name.replace(' ', '_')
            filename = f"{customer_id}_{language}_{timestamp}.mp3"
            file_path = self.voice_notes_dir / filename
            
            response.stream_to_file(str(file_path))
            
            print(f"   ✅ Audio saved: {file_path}")
            return str(file_path)
            
        except Exception as e:
            print(f"   ❌ OpenAI TTS error: {e}")
            return None
    
    def _create_disabled_result(self, shared_context: SharedContext) -> VoiceResult:
        """Create empty result when voice is disabled"""
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
    
    def validate_voice_note(self, result: VoiceResult, shared_context: SharedContext) -> Dict[str, Any]:
        """Validate the generated voice note"""
        
        validation = {
            'is_valid': True,
            'quality_score': result.quality_score,
            'issues': [],
            'achievements': [],
            'metrics': {
                'duration': f"{result.duration_estimate:.1f}s",
                'word_count': result.word_count,
                'language': result.language,
                'has_audio': result.audio_file_path is not None
            }
        }
        
        # Check duration
        if result.duration_estimate < self.VOICE_CONFIG['min_duration']:
            validation['issues'].append("Too short")
        elif result.duration_estimate > self.VOICE_CONFIG['max_duration']:
            validation['issues'].append("Too long")
        else:
            validation['achievements'].append(f"Good duration: {result.duration_estimate:.0f}s")
        
        # Check language
        expected_lang = shared_context.customer_data.get('preferred_language', 'English')
        if result.language == expected_lang:
            validation['achievements'].append(f"Correct language: {expected_lang}")
        else:
            validation['issues'].append(f"Language mismatch")
        
        # Check audio
        if result.audio_file_path:
            validation['achievements'].append("Audio file generated")
        
        return validation

# Convenience function
def generate_smart_voice_note(shared_context: SharedContext, 
                             claude_key: Optional[str] = None,
                             openai_key: Optional[str] = None) -> VoiceResult:
    """Generate a voice note from shared context"""
    generator = SmartVoiceGenerator(claude_key, openai_key)
    return generator.generate_voice_note(shared_context)