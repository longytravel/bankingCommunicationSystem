"""
Smart Voice Note Generator - Self-contained with configuration
Uses SharedContext for Consistent, Natural Voice Messages
UPDATED: Proper channel checking and LANGUAGE SUPPORT
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
                'greeting': {
                    'English': 'Hi {first_name}, this is {bank_rep} from Lloyds',
                    'Spanish': 'Hola {first_name}, soy {bank_rep} de Lloyds',
                    'French': 'Bonjour {first_name}, c\'est {bank_rep} de Lloyds',
                    'German': 'Hallo {first_name}, hier ist {bank_rep} von Lloyds',
                    'Italian': 'Ciao {first_name}, sono {bank_rep} di Lloyds',
                    'Portuguese': 'Olá {first_name}, aqui é {bank_rep} do Lloyds',
                    'Polish': 'Cześć {first_name}, tu {bank_rep} z Lloyds',
                    'Chinese': '你好 {first_name}, 我是劳埃德银行的 {bank_rep}',
                    'Arabic': 'مرحباً {first_name}, أنا {bank_rep} من لويدز'
                },
                'closing': {
                    'English': 'Thanks for being with Lloyds. Have a great day!',
                    'Spanish': '¡Gracias por estar con Lloyds. Que tengas un gran día!',
                    'French': 'Merci d\'être avec Lloyds. Bonne journée!',
                    'German': 'Danke, dass Sie bei Lloyds sind. Einen schönen Tag noch!',
                    'Italian': 'Grazie per essere con Lloyds. Buona giornata!',
                    'Portuguese': 'Obrigado por estar com o Lloyds. Tenha um ótimo dia!',
                    'Polish': 'Dziękujemy za bycie z Lloyds. Miłego dnia!',
                    'Chinese': '感谢您选择劳埃德银行。祝您有美好的一天！',
                    'Arabic': 'شكراً لكونك مع لويدز. أتمنى لك يوماً رائعاً!'
                },
                'tone': 'friendly',
                'pace': 'normal'
            },
            'ASSISTED': {
                'style': 'professional_warm',
                'greeting': {
                    'English': 'Hello {first_name}, this is {bank_rep} calling from Lloyds Bank',
                    'Spanish': 'Buenos días {first_name}, le llama {bank_rep} del Banco Lloyds',
                    'French': 'Bonjour {first_name}, c\'est {bank_rep} de la Banque Lloyds',
                    'German': 'Guten Tag {first_name}, hier spricht {bank_rep} von der Lloyds Bank',
                    'Italian': 'Buongiorno {first_name}, sono {bank_rep} della Banca Lloyds',
                    'Portuguese': 'Bom dia {first_name}, fala {bank_rep} do Banco Lloyds',
                    'Polish': 'Dzień dobry {first_name}, mówi {bank_rep} z Banku Lloyds',
                    'Chinese': '您好 {first_name}, 我是劳埃德银行的 {bank_rep}',
                    'Arabic': 'أهلاً {first_name}, معك {bank_rep} من بنك لويدز'
                },
                'closing': {
                    'English': 'Thank you for your time. If you need anything, we\'re here to help.',
                    'Spanish': 'Gracias por su tiempo. Si necesita algo, estamos aquí para ayudar.',
                    'French': 'Merci pour votre temps. Si vous avez besoin de quoi que ce soit, nous sommes là pour vous aider.',
                    'German': 'Vielen Dank für Ihre Zeit. Wenn Sie etwas brauchen, sind wir für Sie da.',
                    'Italian': 'Grazie per il suo tempo. Se ha bisogno di qualcosa, siamo qui per aiutare.',
                    'Portuguese': 'Obrigado pelo seu tempo. Se precisar de algo, estamos aqui para ajudar.',
                    'Polish': 'Dziękuję za poświęcony czas. Jeśli potrzebujesz czegoś, jesteśmy tutaj, aby pomóc.',
                    'Chinese': '感谢您的时间。如果您需要任何帮助，我们随时为您服务。',
                    'Arabic': 'شكراً لوقتك. إذا احتجت إلى أي شيء، نحن هنا للمساعدة.'
                },
                'tone': 'professional_friendly',
                'pace': 'normal'
            },
            'TRADITIONAL': {
                'style': 'formal_respectful',
                'greeting': {
                    'English': 'Good {time_of_day} {title} {last_name}, this is {bank_rep} from Lloyds Banking Group',
                    'Spanish': 'Buenos {time_of_day} {title} {last_name}, le habla {bank_rep} del Grupo Bancario Lloyds',
                    'French': 'Bon{time_of_day} {title} {last_name}, c\'est {bank_rep} du Groupe Bancaire Lloyds',
                    'German': 'Guten {time_of_day} {title} {last_name}, hier spricht {bank_rep} von der Lloyds Banking Group',
                    'Italian': 'Buon{time_of_day} {title} {last_name}, le parlo {bank_rep} del Gruppo Bancario Lloyds',
                    'Portuguese': 'Bom {time_of_day} {title} {last_name}, fala {bank_rep} do Grupo Bancário Lloyds',
                    'Polish': '{time_of_day} {title} {last_name}, mówi {bank_rep} z Grupy Bankowej Lloyds',
                    'Chinese': '{time_of_day}好 {title} {last_name}, 我是劳埃德银行集团的 {bank_rep}',
                    'Arabic': '{time_of_day} {title} {last_name}, معك {bank_rep} من مجموعة لويدز المصرفية'
                },
                'closing': {
                    'English': 'Thank you for your attention. Please don\'t hesitate to contact your branch if you need assistance.',
                    'Spanish': 'Gracias por su atención. No dude en contactar con su sucursal si necesita ayuda.',
                    'French': 'Merci pour votre attention. N\'hésitez pas à contacter votre agence si vous avez besoin d\'aide.',
                    'German': 'Vielen Dank für Ihre Aufmerksamkeit. Zögern Sie nicht, Ihre Filiale zu kontaktieren, wenn Sie Hilfe benötigen.',
                    'Italian': 'Grazie per la sua attenzione. Non esiti a contattare la sua filiale se ha bisogno di assistenza.',
                    'Portuguese': 'Obrigado pela sua atenção. Não hesite em contactar a sua agência se precisar de assistência.',
                    'Polish': 'Dziękuję za uwagę. Proszę nie wahać się skontaktować z oddziałem, jeśli potrzebuje Pan/Pani pomocy.',
                    'Chinese': '感谢您的关注。如需帮助，请随时联系您的分行。',
                    'Arabic': 'شكراً لاهتمامك. لا تتردد في الاتصال بفرعك إذا كنت بحاجة إلى المساعدة.'
                },
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
            'engaging': {
                'energy': 'high',
                'warmth': 'very_warm',
                'formality': 'casual',
                'accent': 'neutral'
            },
            'warm_personal': {
                'energy': 'medium',
                'warmth': 'very_warm',
                'formality': 'friendly',
                'accent': 'neutral'
            },
            'premium': {
                'energy': 'medium',
                'warmth': 'warm',
                'formality': 'professional',
                'accent': 'neutral'
            },
            'clear_and_slow': {
                'energy': 'calm',
                'warmth': 'cordial',
                'formality': 'formal',
                'accent': 'received_pronunciation'
            },
            'urgent': {
                'energy': 'high',
                'warmth': 'professional',
                'formality': 'direct',
                'accent': 'neutral'
            }
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
        
        customer_name = shared_context.customer_data.get('name', 'Customer')
        customer_language = shared_context.customer_data.get('preferred_language', 'English')
        
        print(f"🎙️ Generating smart voice note for {customer_name} in {customer_language}...")
        
        # Check if voice is enabled in channel decisions
        voice_enabled = shared_context.channel_decisions['enabled_channels'].get('voice', False)
        voice_reason = shared_context.channel_decisions['reasons'].get('voice', 'Not evaluated')
        
        if not voice_enabled:
            print(f"  ⏭️ Voice disabled by rules: {voice_reason}")
            return self._create_disabled_result(shared_context, f"Voice disabled by rules: {voice_reason}")
        
        # Get voice metadata from channel decisions if available
        voice_style = shared_context.channel_decisions.get('voice_style', 'engaging')
        voice_speed = shared_context.channel_decisions.get('voice_speed', 1.0)
        
        print(f"  ✅ Voice enabled: {voice_reason}")
        print(f"  🎭 Style: {voice_style}, Speed: {voice_speed}")
        print(f"  🌍 Language: {customer_language}")
        
        if self.client:
            result = self._generate_with_ai(shared_context, voice_style, voice_speed)
        else:
            result = self._generate_simulation(shared_context)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        result.processing_time = processing_time
        
        print(f"✅ Smart voice note generated in {processing_time:.2f}s")
        print(f"   Duration: {result.duration_estimate:.1f}s, Quality: {result.quality_score:.2%}")
        print(f"   Language: {result.language}")
        
        return result
    
    def _generate_with_ai(self, shared_context: SharedContext, voice_style: str, voice_speed: float) -> VoiceResult:
        """Generate voice note using AI with language support"""
        
        # Extract intelligence
        customer = shared_context.customer_data
        insights = shared_context.customer_insights
        strategy = shared_context.personalization_strategy
        content_strategy = shared_context.content_strategy
        
        # Get customer's preferred language
        customer_language = customer.get('preferred_language', 'English')
        
        # Get segment and greeting config
        segment = insights.segment
        greeting_config = self.config['greeting_styles'].get(segment, self.config['greeting_styles']['ASSISTED'])
        
        # Get language-specific greetings and closings
        greeting_template = greeting_config['greeting'].get(customer_language, greeting_config['greeting']['English'])
        closing_text = greeting_config['closing'].get(customer_language, greeting_config['closing']['English'])
        
        # Get voice characteristics based on style from rules
        voice_chars = self.config['voice_characteristics'].get(
            voice_style, 
            self.config['voice_characteristics']['engaging']
        )
        
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
            greeting_template,
            closing_text,
            voice_chars,
            doc_type,
            requires_callback,
            customer_language,
            voice_style
        )
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.7,
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
                    customer_language,
                    voice_speed
                )
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
        greeting_template: str,
        closing_text: str,
        voice_chars: Dict[str, Any],
        doc_type: str,
        requires_callback: bool,
        customer_language: str,
        voice_style: str
    ) -> str:
        """Build the voice generation prompt with language support"""
        
        # Get only critical points for voice
        critical_points = [p.content for p in content_strategy.critical_points[:3]]
        
        # Format greeting with customer details
        first_name = customer.get('name', '').split()[0] if customer.get('name') else 'there'
        last_name = customer.get('name', '').split()[-1] if customer.get('name') and len(customer.get('name', '').split()) > 1 else ''
        
        # Determine appropriate title based on language
        title_map = {
            'English': 'Mr' if customer.get('gender') == 'M' else 'Ms',
            'Spanish': 'Sr.' if customer.get('gender') == 'M' else 'Sra.',
            'French': 'M.' if customer.get('gender') == 'M' else 'Mme',
            'German': 'Herr' if customer.get('gender') == 'M' else 'Frau',
            'Italian': 'Sig.' if customer.get('gender') == 'M' else 'Sig.ra',
            'Portuguese': 'Sr.' if customer.get('gender') == 'M' else 'Sra.',
            'Polish': 'Pan' if customer.get('gender') == 'M' else 'Pani',
            'Chinese': '先生' if customer.get('gender') == 'M' else '女士',
            'Arabic': 'السيد' if customer.get('gender') == 'M' else 'السيدة'
        }
        
        title = title_map.get(customer_language, title_map['English'])
        
        # Get time of day greeting based on language
        time_greetings = {
            'English': 'morning',
            'Spanish': 'días',
            'French': 'jour',
            'German': 'Tag',
            'Italian': 'giorno',
            'Portuguese': 'dia',
            'Polish': 'Dzień dobry',
            'Chinese': '早上',
            'Arabic': 'صباح الخير'
        }
        
        time_of_day = time_greetings.get(customer_language, 'morning')
        
        # Format the greeting
        greeting = greeting_template.format(
            first_name=first_name,
            bank_rep="Sarah",  # Could be dynamic
            time_of_day=time_of_day,
            title=title,
            last_name=last_name
        )
        
        # Calculate target duration
        target_words = int(self.config['optimal_duration'] * self.config['speaking_rates']['normal'] / 60)
        
        prompt = f"""Generate a natural, conversational VOICE NOTE SCRIPT for a phone message to a bank customer.

CRITICAL: This will be SPOKEN ALOUD in {customer_language}, so write exactly how someone would naturally speak on the phone in that language.

CUSTOMER CONTEXT:
- Name: {customer.get('name')}
- Language: {customer_language}
- Segment: {insights.segment} 
- Life Stage: {insights.life_stage}
- Communication Style: {insights.communication_style}
- Special Context: {insights.special_factors[0] if insights.special_factors else 'None'}
- Recent Life Event: {customer.get('recent_life_events', 'None')}

KEY INFORMATION TO CONVEY (pick most important for voice):
{chr(10).join(['• ' + point for point in critical_points])}

VOICE REQUIREMENTS:
- Language: {customer_language} (ENTIRE SCRIPT MUST BE IN {customer_language.upper()})
- Start: "{greeting}"
- Tone: {voice_chars['formality']} and {voice_chars['warmth']}
- Style: {voice_style}
- Length: {target_words} words (about {self.config['optimal_duration']} seconds when spoken)
- End: "{closing_text}"
- Natural speech: Use contractions appropriate for {customer_language}
- Be CONCISE: This is a voice message, not a letter
{"- MUST offer callback option due to importance" if requires_callback else ""}

PERSONALIZATION:
- Reference their recent life event: {customer.get('recent_life_events', 'None')}
- Sound like you know them personally
- Use their name once more in the middle
- Make it warm and engaging for this valuable customer

SPEECH PATTERNS FOR {customer_language.upper()}:
- Write as SPOKEN {customer_language}, not written
- Use natural contractions and idioms for {customer_language}
- Break up long sentences
- Sound warm and human
- Cultural appropriateness for {customer_language} speakers

Generate as JSON:
{{
    "voice_script": "Complete natural speech script IN {customer_language.upper()} with pauses indicated by '...'",
    "tone_markers": ["warm", "urgent", "friendly", etc],
    "emphasis_words": ["important", "deadline", etc - words to stress],
    "personalization_elements": ["what was personalized"],
    "natural_pauses": [15, 30, 45],  // Word positions for pauses
    "speaking_pace": "slow|normal|fast"
}}

REMEMBER: The ENTIRE voice script must be in {customer_language}, not English (unless English is the preferred language).
Make it sound like a real person calling, not a robot reading a script."""
        
        return prompt
    
    def _parse_ai_response(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse the AI response"""
        content = content.replace('```json', '').replace('```', '').strip()
        
        try:
            parsed = json.loads(content)
            if parsed and isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
        
        if '{' in content and '}' in content:
            try:
                json_start = content.index('{')
                json_end = content.rindex('}') + 1
                json_str = content[json_start:json_end]
                
                json_str = re.sub(r'[\r\n\t]', ' ', json_str)
                json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
                
                parsed = json.loads(json_str)
                if parsed and isinstance(parsed, dict):
                    return parsed
            except (json.JSONDecodeError, ValueError) as e:
                print(f"JSON extraction failed: {e}")
        
        return None
    
    def _create_voice_result(
        self, 
        voice_data: Dict[str, Any], 
        shared_context: SharedContext,
        method: str,
        requires_callback: bool,
        customer_language: str,
        voice_speed: float
    ) -> VoiceResult:
        """Create VoiceResult from parsed data"""
        
        script = voice_data.get('voice_script', '')
        word_count = len(script.split())
        
        # Calculate duration based on pace and speed setting
        pace = voice_data.get('speaking_pace', 'normal')
        base_wpm = self.config['speaking_rates'].get(pace, 150)
        adjusted_wpm = base_wpm * voice_speed  # Apply speed adjustment from rules
        duration_estimate = (word_count / adjusted_wpm) * 60  # in seconds
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(
            script,
            voice_data.get('personalization_elements', []),
            duration_estimate,
            shared_context,
            customer_language
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
            language=customer_language,
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
        shared_context: SharedContext,
        language: str
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
        
        # Check for conversational tone
        contractions = ["we're", "you'll", "won't", "it's", "that's", "we've"]
        if any(cont in script.lower() for cont in contractions):
            score += 0.1
        
        # Bonus for matching preferred language
        customer_language = shared_context.customer_data.get('preferred_language', 'English')
        if language == customer_language:
            score += 0.1
        
        # Check for natural speech patterns
        if '...' in script:  # Has pauses
            score += 0.05
        
        return min(1.0, score)
    
    def _generate_fallback(self, shared_context: SharedContext) -> VoiceResult:
        """Generate fallback voice note when AI fails"""
        
        customer = shared_context.customer_data
        name = customer.get('name', 'there').split()[0]
        language = customer.get('preferred_language', 'English')
        
        # Get appropriate greeting based on language
        if language == 'Spanish':
            script = f"""Hola {name}, soy Sarah del Banco Lloyds.

Te llamo con una actualización importante sobre tu cuenta. Te hemos enviado una carta con todos los detalles, pero quería asegurarme de que recibas el mensaje.

Por favor, revisa tu correo para obtener la información completa. Si tienes alguna pregunta o necesitas hablar sobre esto, llámanos al 0345 300 0000.

Gracias por estar con Lloyds, {name}. ¡Que tengas un gran día!"""
        else:
            script = f"""Hi {name}, this is Sarah from Lloyds Bank.

I'm calling with an important update about your account. We've sent you a letter with all the details, but I wanted to make sure you got the message.

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
            personalization_elements=['customer_name', 'language_appropriate'],
            natural_pauses=[20, 40],
            emphasis_words=['important'],
            language=language,
            generation_method='fallback',
            processing_time=0.0,
            quality_score=0.6,
            requires_callback=False
        )
    
    def _generate_simulation(self, shared_context: SharedContext) -> VoiceResult:
        """Generate simulation voice note"""
        
        customer = shared_context.customer_data
        name = customer.get('name', 'Customer')
        language = customer.get('preferred_language', 'English')
        
        script = f"""[SIMULATED VOICE NOTE - {language.upper()}]
        
Hi {name}, this is a test voice message from Lloyds.

Segment: {shared_context.customer_insights.segment}
Personalization: {shared_context.personalization_strategy.level.value}
Language: {language}

[Voice script would be generated here in {language}]

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
        elif voice_result.duration_estimate > self.config['max_duration']:
            validation['issues'].append("Too long - consider breaking up")
        else:
            validation['achievements'].append(f"Good length: {voice_result.duration_estimate:.0f}s")
        
        # Check personalization
        if len(voice_result.personalization_elements) >= self.config['quality_thresholds']['min_personalization']:
            validation['achievements'].append("Well personalized for voice")
        
        # Check language match
        customer_language = shared_context.customer_data.get('preferred_language', 'English')
        if voice_result.language == customer_language:
            validation['achievements'].append(f"Correct language: {customer_language}")
        else:
            validation['issues'].append(f"Language mismatch: expected {customer_language}, got {voice_result.language}")
        
        # Check natural speech
        if voice_result.tone_markers:
            validation['achievements'].append(f"Natural tone: {', '.join(voice_result.tone_markers[:2])}")
        
        return validation

# Convenience function
def generate_smart_voice_note(shared_context: SharedContext, api_key: Optional[str] = None) -> VoiceResult:
    """Generate a smart voice note from shared context"""
    generator = SmartVoiceGenerator(api_key=api_key)
    return generator.generate_voice_note(shared_context)