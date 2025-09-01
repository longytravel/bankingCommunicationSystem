"""
Smart Email Generator - Self-contained with configuration
Uses SharedContext for Consistent, Deeply Personalized Emails
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
class EmailResult:
    """Result from email generation"""
    content: str
    subject_line: str
    word_count: int
    character_count: int
    personalization_elements: List[str]
    tone_achieved: str
    language: str
    generation_method: str
    processing_time: float
    quality_score: float

class SmartEmailGenerator:
    """
    Smart Email Generator - Self-contained with all configuration
    Takes a SharedContext and generates perfectly aligned email content
    """
    
    # ============== EMAIL CONFIGURATION ==============
    # All email-specific configuration in one place (matches SMS structure)
    EMAIL_CONFIG = {
        'max_length': 5000,  # Maximum email length in characters
        'min_length': 200,   # Minimum for a proper email
        'format': {
            'default': 'html',
            'plain_text_option': True
        },
        'subject_line': {
            'max_length': 100,
            'personalize': True,
            'include_urgency': True,
            'templates': {
                'URGENT': '🔴 Urgent: {topic} - Action Required',
                'REGULATORY': 'Important Changes to Your {account_type} Account',
                'PROMOTIONAL': '💰 {name}, Special Offer for You',
                'INFORMATIONAL': 'Your Lloyds Account Update - {topic}',
                'DEFAULT': 'Important Information About Your Account'
            }
        },
        'personalization': {
            'include_full_name': True,
            'use_preferred_name': True,
            'reference_history': True,
            'mention_life_events': True
        },
        'greeting_styles': {
            'DIGITAL': {
                'style': 'modern_friendly',
                'greeting': 'Hi {first_name}',
                'closing': 'Best,\nThe Lloyds Team',
                'tone': 'conversational'
            },
            'ASSISTED': {
                'style': 'balanced_professional',
                'greeting': 'Hello {first_name}',
                'closing': 'Best regards,\nLloyds Bank',
                'tone': 'friendly_professional'
            },
            'TRADITIONAL': {
                'style': 'formal_respectful',
                'greeting': 'Dear {title} {last_name}',
                'closing': 'Yours sincerely,\nLloyds Banking Group',
                'tone': 'formal'
            }
        },
        'content_structure': {
            'include_summary': True,  # TL;DR at the top
            'use_bullet_points': True,
            'highlight_actions': True,
            'include_next_steps': True,
            'add_contact_info': True
        },
        'footer_templates': {
            'standard': """
---
Lloyds Bank plc. Registered Office: 25 Gresham Street, London EC2V 7HN.
Registered in England and Wales no. 2065. Telephone: 0345 300 0000.
""",
            'security': """
🔒 This email is from Lloyds Bank. We'll never ask for your full password or PIN.
If you're unsure this email is genuine, please call us on 0345 300 0000.
""",
            'promotional': """
You're receiving this because you're a valued Lloyds customer.
Manage your preferences: lloydsbank.com/preferences
"""
        },
        'quality_thresholds': {
            'min_personalization': 3,  # Minimum personalization elements
            'min_content_preservation': 0.9,  # 90% of critical points must be included
            'readability_score': 60,  # Flesch reading ease target
            'max_paragraphs': 8,
            'ideal_paragraph_length': 100  # words
        },
        'tone_adaptations': {
            'urgent': {
                'emphasize_timeline': True,
                'use_active_voice': True,
                'highlight_consequences': True
            },
            'promotional': {
                'emphasize_benefits': True,
                'use_positive_language': True,
                'include_testimonials': False
            },
            'regulatory': {
                'use_precise_language': True,
                'include_references': True,
                'maintain_formal_tone': True
            }
        }
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the smart email generator"""
        self.api_key = api_key or os.getenv('CLAUDE_API_KEY')
        self.client = None
        self.config = self.EMAIL_CONFIG  # Use local config
        
        if self.api_key and ANTHROPIC_AVAILABLE:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.model = "claude-3-5-sonnet-20241022"
            print("✅ Smart Email Generator initialized with Claude AI")
        else:
            print("⚠️ Smart Email Generator running in simulation mode")
    
    def generate_email(self, shared_context: SharedContext) -> EmailResult:
        """
        Generate a perfectly personalized email using the Shared Brain's intelligence
        
        Args:
            shared_context: The complete intelligence from SharedBrain.analyze_everything()
            
        Returns:
            EmailResult with the generated email and metadata
        """
        
        start_time = datetime.now()
        
        print(f"📧 Generating smart email for {shared_context.customer_data.get('name')}...")
        
        # Check if email is enabled
        if not shared_context.channel_decisions['enabled_channels'].get('email', True):
            return self._create_disabled_result(shared_context, "Email disabled by rules")
        
        if self.client:
            result = self._generate_with_ai(shared_context)
        else:
            result = self._generate_simulation(shared_context)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        result.processing_time = processing_time
        
        print(f"✅ Smart email generated in {processing_time:.2f}s")
        print(f"   Words: {result.word_count}, Quality: {result.quality_score:.2%}")
        
        return result
    
    def _generate_with_ai(self, shared_context: SharedContext) -> EmailResult:
        """Generate email using AI with the shared context intelligence"""
        
        # Extract intelligence from shared context
        customer = shared_context.customer_data
        insights = shared_context.customer_insights
        strategy = shared_context.personalization_strategy
        content_strategy = shared_context.content_strategy
        
        # Get segment-specific configuration
        segment = insights.segment
        greeting_config = self.config['greeting_styles'].get(segment, self.config['greeting_styles']['ASSISTED'])
        
        # Determine document type for tone
        doc_type = shared_context.document_classification.get('primary_classification', 'INFORMATIONAL')
        tone_adaptation = self.config['tone_adaptations'].get(doc_type.lower(), {})
        
        # Build the email generation prompt
        generation_prompt = self._build_generation_prompt(
            shared_context.original_letter,
            customer,
            insights,
            strategy,
            content_strategy,
            greeting_config,
            tone_adaptation,
            doc_type
        )
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.5,
                messages=[{"role": "user", "content": generation_prompt}]
            )
            
            content = response.content[0].text.strip()
            email_data = self._parse_ai_response(content)
            
            if email_data:
                return self._create_email_result(email_data, shared_context, "ai_generation")
            else:
                return self._generate_fallback(shared_context)
                
        except Exception as e:
            print(f"AI email generation error: {e}")
            return self._generate_fallback(shared_context)
    
    def _build_generation_prompt(
        self, 
        original_letter: str,
        customer: Dict[str, Any],
        insights,
        strategy,
        content_strategy,
        greeting_config: Dict[str, Any],
        tone_adaptation: Dict[str, Any],
        doc_type: str
    ) -> str:
        """Build the email generation prompt using shared context intelligence"""
        
        # Get content requirements for email
        email_requirements = content_strategy.channel_requirements.get('email', ['critical', 'important'])
        
        # Build content to preserve
        content_to_preserve = []
        if 'critical' in email_requirements:
            content_to_preserve.extend([p.content for p in content_strategy.critical_points])
        if 'important' in email_requirements:
            content_to_preserve.extend([p.content for p in content_strategy.important_points])
        if 'contextual' in email_requirements:
            content_to_preserve.extend([p.content for p in content_strategy.contextual_points[:3]])
        
        # Format greeting with customer name
        first_name = customer.get('name', '').split()[0] if customer.get('name') else 'Customer'
        greeting = greeting_config['greeting'].format(first_name=first_name, title='Mr/Ms', last_name=customer.get('name', '').split()[-1] if customer.get('name') else 'Customer')
        
        # Build subject line template
        subject_template = self.config['subject_line']['templates'].get(doc_type, self.config['subject_line']['templates']['DEFAULT'])
        
        prompt = f"""You are writing a deeply personalized email for a Lloyds Bank customer. You have complete intelligence about the customer and must create an engaging, complete email.

CRITICAL REQUIREMENTS:
1. Include 100% of the information from the original letter - NOTHING can be omitted
2. Deeply personalize based on the customer's specific situation
3. NO PLACEHOLDERS - write complete, real content
4. Make natural connections between information and customer context

ORIGINAL LETTER (preserve ALL information):
{original_letter}

CUSTOMER PROFILE:
Name: {customer.get('name')}
Segment: {insights.segment}
Life Stage: {insights.life_stage}
Digital Persona: {insights.digital_persona}
Financial Profile: {insights.financial_profile}
Communication Style: {insights.communication_style}
Language: {customer.get('preferred_language', 'English')}
Special Factors: {', '.join(insights.special_factors[:3]) if insights.special_factors else 'None'}

PERSONALIZATION STRATEGY:
Level: {strategy.level.value}
Customer Story: {strategy.customer_story}
Tone: {greeting_config['tone']}
Must Mention: {', '.join(strategy.must_mention[:3]) if strategy.must_mention else 'None'}

CONTENT TO PRESERVE (ALL of these):
{chr(10).join(['• ' + item for item in content_to_preserve])}

EMAIL REQUIREMENTS:
- Start with: "{greeting},"
- Tone: {greeting_config['tone']}
- Style: {greeting_config['style']}
- End with: "{greeting_config['closing']}"
- Length: {self.config['min_length']}-{self.config['max_length']} characters
- Include summary paragraph at the beginning
- Use clear sections with headers if needed
- Highlight any actions required

PERSONALIZATION REQUIREMENTS:
- Weave in customer context naturally throughout
- Reference at least {self.config['quality_thresholds']['min_personalization']} personal elements
- Make connections between content and customer's situation
- Use language appropriate for their {insights.segment} segment

TONE ADAPTATIONS:
{json.dumps(tone_adaptation, indent=2) if tone_adaptation else 'Standard professional tone'}

Generate the email as JSON:
{{
    "subject_line": "Personalized subject under {self.config['subject_line']['max_length']} chars",
    "email_content": "Complete email text with greeting, full body preserving all content, and closing",
    "personalization_elements": ["list", "of", "specific", "personalizations", "applied"],
    "tone_achieved": "description of tone used"
}}

Write in {customer.get('preferred_language', 'English')}. Make it feel personally written for this specific customer."""

        return prompt
    
    def _parse_ai_response(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse the AI response to extract email data with robust handling"""
        
        # Remove markdown formatting if present
        content = content.replace('```json', '').replace('```', '').strip()
        
        # Clean up common issues
        content = content.replace('\n', ' ')  # Replace newlines with spaces
        content = content.replace('\r', '')   # Remove carriage returns
        content = content.replace('\t', ' ')  # Replace tabs with spaces
        
        # Try direct JSON parsing first
        try:
            parsed = json.loads(content)
            if parsed and isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
        
        # If direct parsing fails, try to extract JSON from the content
        if '{' in content and '}' in content:
            try:
                json_start = content.index('{')
                json_end = content.rindex('}') + 1
                json_str = content[json_start:json_end]
                
                # Clean the extracted JSON
                json_str = json_str.replace('\n', ' ')
                json_str = json_str.replace('\r', '')
                json_str = json_str.replace('\t', ' ')
                
                # Remove any trailing commas before closing braces/brackets
                json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
                
                parsed = json.loads(json_str)
                if parsed and isinstance(parsed, dict):
                    return parsed
            except (json.JSONDecodeError, ValueError) as e:
                print(f"JSON extraction failed: {e}")
        
        # Final attempt - try to fix common JSON issues
        try:
            # Try to extract just the content between first { and last }
            if '{' in content and '}' in content:
                start = content.find('{')
                end = content.rfind('}') + 1
                potential_json = content[start:end]
                
                # Aggressive cleaning
                potential_json = re.sub(r'[\r\n\t]', ' ', potential_json)  # Remove all control chars
                potential_json = re.sub(r'\s+', ' ', potential_json)  # Normalize whitespace
                potential_json = re.sub(r',\s*([}\]])', r'\1', potential_json)  # Remove trailing commas
                
                parsed = json.loads(potential_json)
                if parsed and isinstance(parsed, dict):
                    return parsed
        except Exception as e:
            print(f"Final parsing attempt failed: {e}")
        
        print("⚠️ All parsing attempts failed for email response")
        return None
    
    def _create_email_result(
        self, 
        email_data: Dict[str, Any], 
        shared_context: SharedContext,
        method: str
    ) -> EmailResult:
        """Create EmailResult from parsed email data"""
        
        email_content = email_data.get('email_content', '')
        subject_line = email_data.get('subject_line', 'Important Update')
        
        # Add appropriate footer based on document type
        doc_type = shared_context.document_classification.get('primary_classification', 'INFORMATIONAL')
        if doc_type == 'PROMOTIONAL':
            email_content += self.config['footer_templates']['promotional']
        elif doc_type == 'REGULATORY':
            email_content += self.config['footer_templates']['standard']
        else:
            email_content += self.config['footer_templates']['security']
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(
            email_content,
            email_data.get('personalization_elements', []),
            shared_context
        )
        
        return EmailResult(
            content=email_content,
            subject_line=subject_line,
            word_count=len(email_content.split()),
            character_count=len(email_content),
            personalization_elements=email_data.get('personalization_elements', []),
            tone_achieved=email_data.get('tone_achieved', 'professional'),
            language=shared_context.customer_data.get('preferred_language', 'English'),
            generation_method=method,
            processing_time=0.0,
            quality_score=quality_score
        )
    
    def _calculate_quality_score(
        self, 
        email_content: str, 
        personalization_elements: List[str],
        shared_context: SharedContext
    ) -> float:
        """Calculate quality score based on configuration thresholds"""
        
        score = 0.5  # Base score
        
        # Check personalization depth
        min_personal = self.config['quality_thresholds']['min_personalization']
        if len(personalization_elements) >= min_personal:
            score += 0.2
        
        # Check content length
        word_count = len(email_content.split())
        if self.config['min_length'] <= len(email_content) <= self.config['max_length']:
            score += 0.1
        
        # Check for must-mention items
        must_mention_found = 0
        for item in shared_context.personalization_strategy.must_mention:
            item_words = item.lower().split()
            key_words = [w for w in item_words if len(w) > 4]
            if key_words and any(word in email_content.lower() for word in key_words):
                must_mention_found += 1
        
        if must_mention_found > 0:
            score += 0.1 + (must_mention_found * 0.05)
        
        # Check personalization level achievement
        target_level = shared_context.personalization_strategy.level
        if target_level == PersonalizationLevel.HYPER and len(personalization_elements) >= 8:
            score += 0.1
        elif target_level == PersonalizationLevel.DEEP and len(personalization_elements) >= 6:
            score += 0.1
        elif target_level == PersonalizationLevel.MODERATE and len(personalization_elements) >= 4:
            score += 0.05
        
        return min(1.0, score)
    
    def _generate_fallback(self, shared_context: SharedContext) -> EmailResult:
        """Generate fallback email when AI fails"""
        
        customer = shared_context.customer_data
        insights = shared_context.customer_insights
        strategy = shared_context.personalization_strategy
        
        name = customer.get('name', 'Valued Customer')
        segment = insights.segment
        greeting_config = self.config['greeting_styles'].get(segment, self.config['greeting_styles']['ASSISTED'])
        
        # Format greeting
        first_name = name.split()[0] if name != 'Valued Customer' else name
        greeting = greeting_config['greeting'].format(first_name=first_name, title='', last_name='')
        
        # Build basic personalized email
        personal_intro = ""
        if insights.special_factors:
            factor = insights.special_factors[0]
            personal_intro = f"We hope everything is going well with {factor}. "
        elif strategy.customer_story:
            personal_intro = f"As someone who {strategy.customer_story.lower()}, we wanted to reach out personally. "
        
        email_content = f"""{greeting},

{personal_intro}We have important information about your account that requires your attention.

{shared_context.original_letter}

If you have any questions, please don't hesitate to contact us through your preferred channel.

{greeting_config['closing']}"""
        
        return EmailResult(
            content=email_content,
            subject_line=f"Important Update for {name}",
            word_count=len(email_content.split()),
            character_count=len(email_content),
            personalization_elements=["customer_name", "segment_adaptation", "personal_intro"],
            tone_achieved=greeting_config['tone'],
            language=customer.get('preferred_language', 'English'),
            generation_method="fallback",
            processing_time=0.0,
            quality_score=0.6
        )
    
    def _generate_simulation(self, shared_context: SharedContext) -> EmailResult:
        """Generate simulation email for testing without AI"""
        
        customer = shared_context.customer_data
        insights = shared_context.customer_insights
        strategy = shared_context.personalization_strategy
        
        name = customer.get('name', 'Customer')
        
        simulation_content = f"""Dear {name},

[SIMULATED EMAIL - {customer.get('preferred_language', 'English').upper()}]

Customer Segment: {insights.segment}
Personalization Level: {strategy.level.value}
Communication Style: {insights.communication_style}

This email would be deeply personalized using:
{chr(10).join(['• ' + hook for hook in insights.personalization_hooks[:3]])}

[Original letter content would appear here with full personalization woven throughout]

Best regards,
Lloyds Bank

[Generated by Smart Email Generator - Simulation Mode]"""
        
        return EmailResult(
            content=simulation_content,
            subject_line=f"[SIMULATION] Update for {name}",
            word_count=len(simulation_content.split()),
            character_count=len(simulation_content),
            personalization_elements=["simulation_mode", "customer_segment", "personalization_level"],
            tone_achieved=insights.communication_style,
            language=customer.get('preferred_language', 'English'),
            generation_method="simulation",
            processing_time=0.0,
            quality_score=0.8
        )
    
    def _create_disabled_result(self, shared_context: SharedContext, reason: str) -> EmailResult:
        """Create result when email is disabled"""
        
        return EmailResult(
            content="",
            subject_line="",
            word_count=0,
            character_count=0,
            personalization_elements=[],
            tone_achieved="",
            language=shared_context.customer_data.get('preferred_language', 'English'),
            generation_method="disabled",
            processing_time=0.0,
            quality_score=0.0
        )
    
    def validate_email(self, email_result: EmailResult, shared_context: SharedContext) -> Dict[str, Any]:
        """Validate that the email meets configuration requirements"""
        
        validation = {
            'is_valid': True,
            'quality_score': email_result.quality_score,
            'issues': [],
            'achievements': [],
            'metrics': {
                'word_count': email_result.word_count,
                'character_count': email_result.character_count,
                'personalization_elements': len(email_result.personalization_elements),
                'min_personalization_required': self.config['quality_thresholds']['min_personalization']
            }
        }
        
        # Check length
        if email_result.character_count < self.config['min_length']:
            validation['issues'].append("Email too short")
            validation['is_valid'] = False
        elif email_result.character_count > self.config['max_length']:
            validation['issues'].append("Email too long")
            validation['is_valid'] = False
        else:
            validation['achievements'].append(f"Optimal length: {email_result.word_count} words")
        
        # Check personalization
        min_personal = self.config['quality_thresholds']['min_personalization']
        if len(email_result.personalization_elements) < min_personal:
            validation['issues'].append(f"Insufficient personalization (need {min_personal})")
        else:
            validation['achievements'].append(f"Applied {len(email_result.personalization_elements)} personalizations")
        
        # Check personalization level achievement
        target_level = shared_context.personalization_strategy.level
        achieved_elements = len(email_result.personalization_elements)
        
        if target_level == PersonalizationLevel.HYPER and achieved_elements >= 8:
            validation['achievements'].append(f"Achieved HYPER personalization")
        elif target_level == PersonalizationLevel.DEEP and achieved_elements >= 6:
            validation['achievements'].append(f"Achieved DEEP personalization")
        elif target_level == PersonalizationLevel.MODERATE and achieved_elements >= 4:
            validation['achievements'].append(f"Achieved MODERATE personalization")
        else:
            validation['issues'].append(f"Did not achieve {target_level.value} personalization level")
        
        return validation

# Convenience function
def generate_smart_email(shared_context: SharedContext, api_key: Optional[str] = None) -> EmailResult:
    """
    Convenience function to generate a smart email from shared context
    
    Args:
        shared_context: Complete intelligence from SharedBrain
        api_key: Optional API key
        
    Returns:
        EmailResult with generated email
    """
    generator = SmartEmailGenerator(api_key=api_key)
    return generator.generate_email(shared_context)