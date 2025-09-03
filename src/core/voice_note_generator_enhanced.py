"""
Smart Voice Note Generator - With Audio Generation and Multi-Language Support
Generates actual audio files that can be played in the app
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

class SmartVoiceGenerator:
    """
    Smart Voice Note Generator with Audio Generation
    Creates both scripts and playable audio files
    """
    
    # ============== VOICE CONFIGURATION WITH AUDIO ==============
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
                'voices': {
                    'English': {'DIGITAL': 'nova', 'ASSISTED': 'alloy', 'TRADITIONAL': 'onyx'},
                    'Spanish': {'DIGITAL': 'nova', 'ASSISTED': 'alloy', 'TRADITIONAL': 'onyx'},
                    'French': {'DIGITAL': 'nova', 'ASSISTED': 'alloy', 'TRADITIONAL': 'onyx'},
                    'German': {'DIGITAL': 'nova', 'ASSISTED': 'alloy', 'TRADITIONAL': 'onyx'},
                    'Italian': {'DIGITAL': 'nova', 'ASSISTED': 'alloy', 'TRADITIONAL': 'onyx'},
                    'Portuguese': {'DIGITAL': 'nova', 'ASSISTED': 'alloy', 'TRADITIONAL': 'onyx'},
                    'Polish': {'DIGITAL': 'nova', 'ASSISTED': 'alloy', 'TRADITIONAL': 'onyx'},
                    'Dutch': {'DIGITAL': 'nova', 'ASSISTED': 'alloy', 'TRADITIONAL': 'onyx'},
                    'Russian': {'DIGITAL': 'nova', 'ASSISTED': 'alloy', 'TRADITIONAL': 'onyx'},
                    'Japanese': {'DIGITAL': 'nova', 'ASSISTED': 'alloy', 'TRADITIONAL': 'onyx'},
                    'Chinese': {'DIGITAL': 'nova', 'ASSISTED': 'alloy', 'TRADITIONAL': 'onyx'},
                    'Korean': {'DIGITAL': 'nova', 'ASSISTED': 'alloy', 'TRADITIONAL': 'onyx'},
                    'Arabic': {'DIGITAL': 'nova', 'ASSISTED': 'alloy', 'TRADITIONAL': 'onyx'},
                    'Hindi': {'DIGITAL': 'nova', 'ASSISTED': 'alloy', 'TRADITIONAL': 'onyx'},
                    'Turkish': {'DIGITAL': 'nova', 'ASSISTED': 'alloy', 'TRADITIONAL': 'onyx'}
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
            'English': {
                'DIGITAL': 'Hi {name}, this is {bank_rep} from Lloyds',
                'ASSISTED': 'Hello {name}, this is {bank_rep} calling from Lloyds Bank',
                'TRADITIONAL': 'Good {time_of_day} {title} {last_name}, this is {bank_rep} from Lloyds Banking Group'
            },
            'Spanish': {
                'DIGITAL': 'Hola {name}, soy {bank_rep} de Lloyds',
                'ASSISTED': 'Buenos días {name}, le llama {bank_rep} del Banco Lloyds',
                'TRADITIONAL': 'Buenos {time_of_day} {title} {last_name}, le habla {bank_rep} del Grupo Bancario Lloyds'
            },
            'French': {
                'DIGITAL': 'Salut {name}, c\'est {bank_rep} de Lloyds',
                'ASSISTED': 'Bonjour {name}, c\'est {bank_rep} de la Banque Lloyds',
                'TRADITIONAL': 'Bonjour {title} {last_name}, c\'est {bank_rep} du Groupe Bancaire Lloyds'
            },
            'German': {
                'DIGITAL': 'Hallo {name}, hier ist {bank_rep} von Lloyds',
                'ASSISTED': 'Guten Tag {name}, hier spricht {bank_rep} von der Lloyds Bank',
                'TRADITIONAL': 'Guten {time_of_day} {title} {last_name}, hier spricht {bank_rep} von der Lloyds Banking Group'
            },
            'Italian': {
                'DIGITAL': 'Ciao {name}, sono {bank_rep} di Lloyds',
                'ASSISTED': 'Buongiorno {name}, sono {bank_rep} della Banca Lloyds',
                'TRADITIONAL': 'Buongiorno {title} {last_name}, sono {bank_rep} del Gruppo Bancario Lloyds'
            },
            'Portuguese': {
                'DIGITAL': 'Olá {name}, aqui é {bank_rep} do Lloyds',
                'ASSISTED': 'Bom dia {name}, fala {bank_rep} do Banco Lloyds',
                'TRADITIONAL': 'Bom {time_of_day} {title} {last_name}, fala {bank_rep} do Grupo Bancário Lloyds'
            },
            'Polish': {
                'DIGITAL': 'Cześć {name}, tu {bank_rep} z Lloyds',
                'ASSISTED': 'Dzień dobry {name}, mówi {bank_rep} z Banku Lloyds',
                'TRADITIONAL': 'Dzień dobry {title} {last_name}, mówi {bank_rep} z Grupy Bankowej Lloyds'
            },
            'Dutch': {
                'DIGITAL': 'Hoi {name}, met {bank_rep} van Lloyds',
                'ASSISTED': 'Goedendag {name}, u spreekt met {bank_rep} van Lloyds Bank',
                'TRADITIONAL': 'Goedendag {title} {last_name}, u spreekt met {bank_rep} van Lloyds Banking Group'
            },
            'Chinese': {
                'DIGITAL': '你好{name}，我是劳埃德银行的{bank_rep}',
                'ASSISTED': '您好{name}，我是劳埃德银行的{bank_rep}',
                'TRADITIONAL': '您好{title}{last_name}，我是劳埃德银行集团的{bank_rep}'
            },
            'Japanese': {
                'DIGITAL': 'こんにちは{name}さん、ロイズの{bank_rep}です',
                'ASSISTED': 'こんにちは{name}様、ロイズ銀行の{bank_rep}と申します',
                'TRADITIONAL': '{name}様、ロイズ・バンキング・グループの{bank_rep}と申します'
            },
            'Arabic': {
                'DIGITAL': 'مرحباً {name}، أنا {bank_rep} من لويدز',
                'ASSISTED': 'أهلاً {name}، معك {bank_rep} من بنك لويدز',
                'TRADITIONAL': 'السلام عليكم {title} {last_name}، معك {bank_rep} من مجموعة لويدز المصرفية'
            },
            'Hindi': {
                'DIGITAL': 'नमस्ते {name}, मैं लॉयड्स से {bank_rep} बोल रहा हूं',
                'ASSISTED': 'नमस्ते {name}, मैं लॉयड्स बैंक से {bank_rep} बोल रहा हूं',
                'TRADITIONAL': 'नमस्कार {title} {last_name}, मैं लॉयड्स बैंकिंग समूह से {bank_rep} बोल रहा हूं'
            }
        },
        'closings': {
            'English': {
                'DIGITAL': 'Thanks for being with Lloyds. Have a great day!',
                'ASSISTED': 'Thank you for your time. If you need anything, we\'re here to help.',
                'TRADITIONAL': 'Thank you for your attention. Please don\'t hesitate to contact us.'
            },
            'Spanish': {
                'DIGITAL': '¡Gracias por estar con Lloyds. Que tengas un gran día!',
                'ASSISTED': 'Gracias por su tiempo. Si necesita algo, estamos aquí para ayudar.',
                'TRADITIONAL': 'Gracias por su atención. No dude en contactarnos.'
            },
            'French': {
                'DIGITAL': 'Merci d\'être avec Lloyds. Bonne journée!',
                'ASSISTED': 'Merci pour votre temps. Si vous avez besoin de quoi que ce soit, nous sommes là.',
                'TRADITIONAL': 'Merci pour votre attention. N\'hésitez pas à nous contacter.'
            },
            'German': {
                'DIGITAL': 'Danke, dass Sie bei Lloyds sind. Einen schönen Tag noch!',
                'ASSISTED': 'Vielen Dank für Ihre Zeit. Wenn Sie etwas brauchen, sind wir für Sie da.',
                'TRADITIONAL': 'Vielen Dank für Ihre Aufmerksamkeit. Zögern Sie nicht, uns zu kontaktieren.'
            },
            'Italian': {
                'DIGITAL': 'Grazie per essere con Lloyds. Buona giornata!',
                'ASSISTED': 'Grazie per il suo tempo. Se ha bisogno di qualcosa, siamo qui.',
                'TRADITIONAL': 'Grazie per la sua attenzione. Non esiti a contattarci.'
            },
            'Portuguese': {
                'DIGITAL': 'Obrigado por estar com o Lloyds. Tenha um ótimo dia!',
                'ASSISTED': 'Obrigado pelo seu tempo. Se precisar de algo, estamos aqui.',
                'TRADITIONAL': 'Obrigado pela sua atenção. Não hesite em contactar-nos.'
            },
            'Polish': {
                'DIGITAL': 'Dziękujemy za bycie z Lloyds. Miłego dnia!',
                'ASSISTED': 'Dziękuję za poświęcony czas. Jeśli potrzebujesz czegoś, jesteśmy tutaj.',
                'TRADITIONAL': 'Dziękuję za uwagę. Proszę się z nami kontaktować.'
            },
            'Dutch': {
                'DIGITAL': 'Bedankt dat u bij Lloyds bent. Fijne dag!',
                'ASSISTED': 'Bedankt voor uw tijd. Als u iets nodig heeft, staan we voor u klaar.',
                'TRADITIONAL': 'Bedankt voor uw aandacht. Aarzel niet om contact met ons op te nemen.'
            },
            'Chinese': {
                'DIGITAL': '感谢您选择劳埃德。祝您有美好的一天！',
                'ASSISTED': '感谢您的时间。如果您需要任何帮助，我们随时为您服务。',
                'TRADITIONAL': '感谢您的关注。请随时联系我们。'
            },
            'Japanese': {
                'DIGITAL': 'ロイズをご利用いただきありがとうございます。良い一日を！',
                'ASSISTED': 'お時間をいただきありがとうございます。何かございましたらお手伝いいたします。',
                'TRADITIONAL': 'ご清聴ありがとうございました。ご不明な点がございましたらお問い合わせください。'
            },
            'Arabic': {
                'DIGITAL': 'شكراً لكونك مع لويدز. أتمنى لك يوماً رائعاً!',
                'ASSISTED': 'شكراً لوقتك. إذا احتجت إلى أي شيء، نحن هنا للمساعدة.',
                'TRADITIONAL': 'شكراً لاهتمامكم. لا تترددوا في الاتصال بنا.'
            },
            'Hindi': {
                'DIGITAL': 'लॉयड्स के साथ होने के लिए धन्यवाद। आपका दिन शुभ हो!',
                'ASSISTED': 'आपके समय के लिए धन्यवाद। अगर आपको कुछ चाहिए, हम यहाँ हैं।',
                'TRADITIONAL': 'आपके ध्यान के लिए धन्यवाद। कृपया हमसे संपर्क करने में संकोच न करें।'
            }
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
            print("✅ Voice Generator: Claude AI ready")
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
        """Generate voice note with script AND audio file"""
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
        
        # Generate the script
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
                shared_context.customer_insights.segment,
                result.speaking_pace,
                shared_context.customer_data
            )
            if audio_path:
                result.audio_file_path = audio_path
                print(f"  🎵 Audio file created: {audio_path}")
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        result.processing_time = processing_time
        
        print(f"✅ Voice note complete in {processing_time:.2f}s")
        if result.audio_file_path:
            print(f"   Audio: {result.audio_file_path}")
        print(f"   Language: {result.language}, Duration: {result.duration_estimate:.1f}s")
        
        return result
    
    def _generate_audio(
        self, 
        script: str, 
        language: str, 
        segment: str,
        pace: str,
        customer_data: Dict[str, Any]
    ) -> Optional[str]:
        """Generate audio file from script"""
        
        # Create unique filename
        customer_id = customer_data.get('customer_id', 'unknown')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"voice_{customer_id}_{language}_{timestamp}.mp3"
        filepath = self.output_dir / filename
        
        # Try OpenAI TTS first
        if self.openai_client:
            try:
                # Get voice for this language/segment
                voice = self.config['tts']['openai']['voices'].get(
                    language, {}
                ).get(segment, 'alloy')
                
                # Get speed setting
                speed = self.config['tts']['openai']['speed_settings'].get(pace, 1.0)
                
                # Generate audio
                response = self.openai_client.audio.speech.create(
                    model=self.config['tts']['openai']['model'],
                    voice=voice,
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
        """Generate voice script with AI"""
        
        customer = shared_context.customer_data
        insights = shared_context.customer_insights
        strategy = shared_context.personalization_strategy
        content_strategy = shared_context.content_strategy
        
        # Get language and segment
        language = customer.get('preferred_language', 'English')
        segment = insights.segment
        
        # Get greetings and closings for the language
        greeting_template = self.config['greetings'].get(
            language, self.config['greetings']['English']
        ).get(segment, self.config['greetings']['English']['ASSISTED'])
        
        closing_text = self.config['closings'].get(
            language, self.config['closings']['English']
        ).get(segment, self.config['closings']['English']['ASSISTED'])
        
        # Format greeting
        first_name = customer.get('name', '').split()[0] if customer.get('name') else 'there'
        last_name = customer.get('name', '').split()[-1] if customer.get('name') and len(customer.get('name').split()) > 1 else ''
        
        greeting = greeting_template.format(
            name=first_name,
            first_name=first_name,
            last_name=last_name,
            bank_rep="Sarah",
            time_of_day="morning",
            title="Mr" if customer.get('gender') == 'M' else "Ms"
        )
        
        # Build AI prompt
        prompt = self._build_ai_prompt(
            shared_context.original_letter,
            customer,
            insights,
            strategy,
            content_strategy,
            greeting,
            closing_text,
            language
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
                    "ai_generation"
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
        language: str
    ) -> str:
        """Build AI prompt for voice script generation"""
        
        # Get critical points
        critical_points = [p.content for p in content_strategy.critical_points[:3]]
        
        return f"""Generate a NATURAL VOICE SCRIPT in {language} for a phone message.

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
- Start: "{greeting}"
- End: "{closing}"
- Length: 50-80 words (30-45 seconds spoken)
- Natural conversational tone in {language}
- Reference ONE personal detail
- Sound warm and human

Generate JSON:
{{
    "script": "Complete script in {language}",
    "pace": "slow|normal|fast",
    "emphasis": ["key", "words"],
    "personalizations": ["what was personalized"]
}}

CRITICAL: Write the ENTIRE script in {language}, not English!"""
    
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
        method: str
    ) -> VoiceResult:
        """Create VoiceResult from parsed data"""
        
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
            tone_markers=['warm', 'professional'],
            personalization_elements=data.get('personalizations', []),
            emphasis_words=data.get('emphasis', []),
            language=language,
            generation_method=method,
            processing_time=0.0,
            quality_score=0.8,
            audio_file_path=None,
            tts_engine_used="pending"
        )
    
    def _generate_fallback(self, shared_context: SharedContext) -> VoiceResult:
        """Generate fallback script when AI unavailable"""
        
        customer = shared_context.customer_data
        name = customer.get('name', '').split()[0] if customer.get('name') else 'there'
        language = customer.get('preferred_language', 'English')
        segment = shared_context.customer_insights.segment
        
        # Get appropriate greeting and closing
        greeting = self.config['greetings'].get(
            language, self.config['greetings']['English']
        ).get(segment, self.config['greetings']['English']['ASSISTED']).format(
            name=name,
            first_name=name,
            bank_rep="Sarah",
            time_of_day="day",
            title="",
            last_name=""
        )
        
        closing = self.config['closings'].get(
            language, self.config['closings']['English']
        ).get(segment, self.config['closings']['English']['ASSISTED'])
        
        # Build simple script in the appropriate language
        if language == 'Spanish':
            middle = "Tenemos información importante sobre su cuenta. Por favor, revise su correo para los detalles completos."
        elif language == 'French':
            middle = "Nous avons des informations importantes concernant votre compte. Veuillez vérifier votre courrier pour les détails complets."
        elif language == 'German':
            middle = "Wir haben wichtige Informationen zu Ihrem Konto. Bitte überprüfen Sie Ihre Post für die vollständigen Details."
        elif language == 'Italian':
            middle = "Abbiamo informazioni importanti sul suo conto. Per favore, controlli la sua posta per i dettagli completi."
        elif language == 'Portuguese':
            middle = "Temos informações importantes sobre sua conta. Por favor, verifique seu correio para os detalhes completos."
        elif language == 'Chinese':
            middle = "我们有关于您账户的重要信息。请查看您的邮件以获取完整详情。"
        else:
            middle = "We have important information about your account. Please check your mail for the full details."
        
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
            tts_engine_used="none"
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
            tts_engine_used="none"
        )
    
    def validate_voice_note(self, result: VoiceResult, shared_context: SharedContext) -> Dict:
        """Validate the generated voice note"""
        validation = {
            'is_valid': True,
            'issues': [],
            'achievements': [],
            'metrics': {
                'duration': f"{result.duration_estimate:.1f}s",
                'language': result.language,
                'has_audio': result.audio_file_path is not None
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
        
        # Check audio generation
        if result.audio_file_path:
            validation['achievements'].append(f"Audio generated: {result.tts_engine_used}")
        elif result.generation_method != 'disabled':
            validation['issues'].append("No audio file generated")
        
        return validation

# Convenience function
def generate_smart_voice_note(shared_context: SharedContext, api_key: Optional[str] = None) -> VoiceResult:
    """Generate voice note with audio"""
    generator = SmartVoiceGenerator(api_key=api_key)
    return generator.generate_voice_note(shared_context)