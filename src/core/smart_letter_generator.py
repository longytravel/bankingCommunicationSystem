"""
Smart Letter Generator - Self-contained with configuration
Uses SharedContext for Consistent, Formal Letter Generation
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
class LetterResult:
    """Result from letter generation - MUST match pattern of EmailResult/SMSResult"""
    content: str
    word_count: int
    page_count: int  # Letter-specific
    personalization_elements: List[str]
    formality_level: str  # Letter-specific
    includes_return_envelope: bool  # Letter-specific
    tone_achieved: str
    language: str
    generation_method: str
    processing_time: float
    quality_score: float

class SmartLetterGenerator:
    """
    Smart Letter Generator - Self-contained with all configuration
    Takes a SharedContext and generates perfectly aligned letter content
    """
    
    # ============== LETTER CONFIGURATION ==============
    # All letter-specific configuration in one place (MUST BE SELF-CONTAINED)
    LETTER_CONFIG = {
        'max_length': 10000,  # Maximum letter length in characters
        'min_length': 500,    # Minimum for a proper letter
        'format': {
            'paper_size': 'A4',
            'margins': {'top': 2.5, 'bottom': 2.5, 'left': 3, 'right': 3},  # cm
            'font': 'Arial',
            'font_size': 11,
            'line_spacing': 1.5,
            'words_per_page': 500  # Approximate words per page
        },
        'structure': {
            'include_letterhead': True,
            'include_date': True,
            'include_reference': True,
            'include_footer': True,
            'include_page_numbers': True
        },
        'addressing': {
            'DIGITAL': {
                'style': 'modern_personal',
                'salutation': 'Dear {first_name}',
                'closing': 'Kind regards',
                'formality': 'professional_friendly',
                'include_ps': False
            },
            'ASSISTED': {
                'style': 'balanced_formal',
                'salutation': 'Dear {title} {last_name}',
                'closing': 'Yours sincerely',
                'formality': 'professional',
                'include_ps': False
            },
            'TRADITIONAL': {
                'style': 'traditional_formal',
                'salutation': 'Dear {title} {last_name}',
                'closing': 'Yours faithfully',
                'formality': 'formal',
                'include_ps': True  # P.S. for branch contact
            }
        },
        'letterhead_template': """Lloyds Banking Group
25 Gresham Street
London EC2V 7HN

{date}

{customer_name}
{customer_address}

Reference: {reference_number}
""",
        'footer_template': """
---
Lloyds Bank plc. Registered Office: 25 Gresham Street, London EC2V 7HN.
Registered in England and Wales no. 2065. Authorised by the Prudential Regulation Authority.
""",
        'quality_thresholds': {
            'min_paragraphs': 3,
            'max_paragraphs': 8,
            'ideal_paragraph_length': 150,  # words
            'min_personalization': 4,  # More than email due to length
            'formality_check': True
        },
        'enclosures': {
            'REGULATORY': ['Terms and Conditions', 'Privacy Notice'],
            'PROMOTIONAL': ['Product Brochure', 'Reply Form'],
            'INFORMATIONAL': [],
            'DEFAULT': []
        },
        'tone_adaptations': {
            'URGENT': {
                'emphasize_timeline': True,
                'use_active_voice': True,
                'highlight_consequences': True
            },
            'REGULATORY': {
                'use_precise_language': True,
                'include_references': True,
                'maintain_formal_tone': True
            },
            'PROMOTIONAL': {
                'emphasize_benefits': True,
                'use_positive_language': True,
                'include_call_to_action': True
            },
            'INFORMATIONAL': {
                'clear_structure': True,
                'helpful_tone': True,
                'include_support_info': True
            }
        }
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the smart letter generator"""
        self.api_key = api_key or os.getenv('CLAUDE_API_KEY')
        self.client = None
        self.config = self.LETTER_CONFIG  # Use local config
        
        if self.api_key and ANTHROPIC_AVAILABLE:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.model = "claude-haiku-4-5-20251001"  # Same model for consistency
            print("✅ Smart Letter Generator initialized with Claude AI")
        else:
            print("⚠️ Smart Letter Generator running in simulation mode")
    
    def generate_letter(self, shared_context: SharedContext) -> LetterResult:
        """
        Generate a perfectly personalized letter using the Shared Brain's intelligence
        
        Args:
            shared_context: The complete intelligence from SharedBrain.analyze_everything()
            
        Returns:
            LetterResult with the generated letter and metadata
        """
        start_time = datetime.now()
        
        print(f"📮 Generating smart letter for {shared_context.customer_data.get('name')}...")
        
        # Check if letter is enabled
        if not shared_context.channel_decisions['enabled_channels'].get('letter', False):
            return self._create_disabled_result(shared_context, "Letter disabled by rules")
        
        if self.client:
            result = self._generate_with_ai(shared_context)
        else:
            result = self._generate_simulation(shared_context)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        result.processing_time = processing_time
        
        print(f"✅ Smart letter generated in {processing_time:.2f}s")
        print(f"   Words: {result.word_count}, Pages: {result.page_count}, Quality: {result.quality_score:.2%}")
        
        return result
    
    def _generate_with_ai(self, shared_context: SharedContext) -> LetterResult:
        """Generate letter using AI with the shared context intelligence"""
        
        # Extract intelligence from shared context
        customer = shared_context.customer_data
        insights = shared_context.customer_insights
        strategy = shared_context.personalization_strategy
        content_strategy = shared_context.content_strategy
        
        # Get segment-specific configuration
        segment = insights.segment
        addressing_config = self.config['addressing'].get(segment, self.config['addressing']['ASSISTED'])
        
        # Determine document type for tone
        doc_type = shared_context.document_classification.get('primary_classification', 'INFORMATIONAL')
        tone_adaptation = self.config['tone_adaptations'].get(doc_type, self.config['tone_adaptations']['INFORMATIONAL'])
        
        # Determine if return envelope needed
        needs_return_envelope = (doc_type == 'REGULATORY' or 
                                segment == 'TRADITIONAL' or 
                                shared_context.document_classification.get('customer_action_required', False))
        
        # Build the letter generation prompt
        generation_prompt = self._build_generation_prompt(
            shared_context.original_letter,
            customer,
            insights,
            strategy,
            content_strategy,
            addressing_config,
            tone_adaptation,
            doc_type,
            needs_return_envelope
        )
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.4,  # Lower temperature for more formal consistency
                messages=[{"role": "user", "content": generation_prompt}]
            )
            
            content = response.content[0].text.strip()
            letter_data = self._parse_ai_response(content)
            
            if letter_data:
                return self._create_letter_result(letter_data, shared_context, "ai_generation", needs_return_envelope)
            else:
                print("⚠️ Failed to parse AI response, using fallback")
                return self._generate_fallback(shared_context)
                
        except Exception as e:
            print(f"AI letter generation error: {e}")
            return self._generate_fallback(shared_context)
    
    def _build_generation_prompt(
        self, 
        original_letter: str,
        customer: Dict[str, Any],
        insights,
        strategy,
        content_strategy,
        addressing_config: Dict[str, Any],
        tone_adaptation: Dict[str, Any],
        doc_type: str,
        needs_return_envelope: bool
    ) -> str:
        """Build the letter generation prompt using shared context intelligence"""
        
        # Get content requirements for letter
        letter_requirements = content_strategy.channel_requirements.get('letter', ['critical', 'important', 'contextual'])
        
        # Build content to preserve
        content_to_preserve = []
        if 'critical' in letter_requirements:
            content_to_preserve.extend([p.content for p in content_strategy.critical_points])
        if 'important' in letter_requirements:
            content_to_preserve.extend([p.content for p in content_strategy.important_points])
        if 'contextual' in letter_requirements:
            content_to_preserve.extend([p.content for p in content_strategy.contextual_points])
        
        # Format salutation with customer name
        first_name = customer.get('name', '').split()[0] if customer.get('name') else 'Customer'
        last_name = customer.get('name', '').split()[-1] if customer.get('name') and len(customer.get('name', '').split()) > 1 else customer.get('name', 'Customer')
        salutation = addressing_config['salutation'].format(
            first_name=first_name, 
            title='Mr/Ms', 
            last_name=last_name
        )
        
        # Get enclosures for this document type
        enclosures = self.config['enclosures'].get(doc_type, self.config['enclosures']['DEFAULT'])
        
        # Format current date
        current_date = datetime.now().strftime("%d %B %Y")
        
        prompt = f"""You are writing a formal, personalized letter for a Lloyds Bank customer. You have complete intelligence about the customer and must create a professional, complete letter.

CRITICAL REQUIREMENTS:
1. Include 100% of the information from the original letter - NOTHING can be omitted
2. Deeply personalize based on the customer's specific situation
3. NO PLACEHOLDERS - write complete, real content
4. Make natural connections between information and customer context

ORIGINAL LETTER (preserve ALL information):
{original_letter}

CUSTOMER INTELLIGENCE:
- Name: {customer.get('name')}
- Segment: {insights.segment}
- Life Stage: {insights.life_stage}
- Digital Persona: {insights.digital_persona}
- Financial Profile: {insights.financial_profile}
- Communication Style: {insights.communication_style}
- Language: {customer.get('preferred_language', 'English')}
- Special Factors: {', '.join(insights.special_factors[:3]) if insights.special_factors else 'None'}

PERSONALIZATION STRATEGY:
- Level: {strategy.level.value}
- Customer Story: {strategy.customer_story}
- Formality: {addressing_config['formality']}
- Must Mention: {', '.join(strategy.must_mention[:3]) if strategy.must_mention else 'None'}

CONTENT TO PRESERVE (ALL of these):
{chr(10).join(['• ' + item for item in content_to_preserve])}

LETTER REQUIREMENTS:
- Date: {current_date}
- Salutation: "{salutation}"
- Closing: "{addressing_config['closing']}"
- Formality Level: {addressing_config['formality']}
- Style: {addressing_config['style']}
- Length: {self.config['min_length']}-{self.config['max_length']} characters
- Include all information from original letter
- Add appropriate paragraph breaks for readability
- Maintain formal business letter structure
{"- Include P.S. with branch contact information" if addressing_config.get('include_ps') else ""}
{"- Mention enclosed documents: " + ', '.join(enclosures) if enclosures else ""}

TONE ADAPTATIONS for {doc_type}:
{json.dumps(tone_adaptation, indent=2)}

PERSONALIZATION REQUIREMENTS:
- Weave in customer context naturally throughout
- Reference at least {self.config['quality_thresholds']['min_personalization']} personal elements
- Make connections between content and customer's situation
- Use formal language appropriate for their {insights.segment} segment and {insights.life_stage} life stage
- Maintain professional tone while showing understanding of their situation

Generate the complete formal letter as JSON:
{{
    "letter_content": "COMPLETE formal letter body text (DO NOT include letterhead/date/address - just the main content starting with salutation)",
    "personalization_elements": ["list", "of", "specific", "personalizations", "applied"],
    "formality_level": "formal|professional|professional_friendly",
    "tone_achieved": "description of tone used",
    "enclosures_mentioned": ["list of enclosures mentioned in letter"]
}}

Write in {customer.get('preferred_language', 'English')}. Ensure the letter is complete, formal, and professionally formatted."""

        return prompt
    
    def _parse_ai_response(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse the AI response to extract letter data with robust handling"""
        
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
        
        print("⚠️ All parsing attempts failed for letter response")
        return None
    
    def _create_letter_result(
        self, 
        letter_data: Dict[str, Any], 
        shared_context: SharedContext,
        method: str,
        needs_return_envelope: bool
    ) -> LetterResult:
        """Create LetterResult from parsed letter data"""
        
        letter_content = letter_data.get('letter_content', '')
        
        # Add letterhead
        customer_name = shared_context.customer_data.get('name', 'Valued Customer')
        customer_address = shared_context.customer_data.get('address', 'Customer Address')
        reference_number = f"LBG-{shared_context.customer_data.get('customer_id', 'XXXX')}-{datetime.now().strftime('%Y%m')}"
        
        letterhead = self.config['letterhead_template'].format(
            date=datetime.now().strftime("%d %B %Y"),
            customer_name=customer_name,
            customer_address=customer_address,
            reference_number=reference_number
        )
        
        # Combine letterhead with content
        letter_content = letterhead + "\n\n" + letter_content
        
        # Add footer
        letter_content += self.config['footer_template']
        
        # Add enclosures section if needed
        enclosures_mentioned = letter_data.get('enclosures_mentioned', [])
        if enclosures_mentioned:
            letter_content += f"\n\nEnclosures:\n"
            for enclosure in enclosures_mentioned:
                letter_content += f"- {enclosure}\n"
        
        # Calculate metrics
        word_count = len(letter_content.split())
        page_count = self._calculate_page_count(word_count)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(
            letter_content,
            letter_data.get('personalization_elements', []),
            shared_context,
            letter_data.get('formality_level', 'professional')
        )
        
        return LetterResult(
            content=letter_content,
            word_count=word_count,
            page_count=page_count,
            personalization_elements=letter_data.get('personalization_elements', []),
            formality_level=letter_data.get('formality_level', 'professional'),
            includes_return_envelope=needs_return_envelope,
            tone_achieved=letter_data.get('tone_achieved', 'formal'),
            language=shared_context.customer_data.get('preferred_language', 'English'),
            generation_method=method,
            processing_time=0.0,
            quality_score=quality_score
        )
    
    def _calculate_page_count(self, word_count: int) -> int:
        """Calculate number of pages based on word count"""
        words_per_page = self.config['format']['words_per_page']
        return max(1, (word_count + words_per_page - 1) // words_per_page)
    
    def _calculate_quality_score(
        self, 
        letter_content: str, 
        personalization_elements: List[str],
        shared_context: SharedContext,
        formality_level: str
    ) -> float:
        """Calculate quality score based on configuration thresholds"""
        
        score = 0.5  # Base score
        
        # Check personalization depth
        min_personal = self.config['quality_thresholds']['min_personalization']
        if len(personalization_elements) >= min_personal:
            score += 0.2
        elif len(personalization_elements) >= min_personal - 1:
            score += 0.1
        
        # Check content length
        word_count = len(letter_content.split())
        if self.config['min_length'] <= len(letter_content) <= self.config['max_length']:
            score += 0.1
        
        # Check paragraph structure
        paragraphs = [p for p in letter_content.split('\n\n') if len(p.strip()) > 50]
        if self.config['quality_thresholds']['min_paragraphs'] <= len(paragraphs) <= self.config['quality_thresholds']['max_paragraphs']:
            score += 0.1
        
        # Check formality matches segment
        segment = shared_context.customer_insights.segment
        expected_formality = self.config['addressing'][segment]['formality']
        if formality_level == expected_formality:
            score += 0.1
        
        # Check for must-mention items
        must_mention_found = 0
        for item in shared_context.personalization_strategy.must_mention:
            item_words = item.lower().split()
            key_words = [w for w in item_words if len(w) > 4]
            if key_words and any(word in letter_content.lower() for word in key_words):
                must_mention_found += 1
        
        if must_mention_found > 0:
            score += 0.05 * must_mention_found
        
        # Check personalization level achievement
        target_level = shared_context.personalization_strategy.level
        if target_level == PersonalizationLevel.HYPER and len(personalization_elements) >= 8:
            score += 0.1
        elif target_level == PersonalizationLevel.DEEP and len(personalization_elements) >= 6:
            score += 0.1
        elif target_level == PersonalizationLevel.MODERATE and len(personalization_elements) >= 4:
            score += 0.05
        
        return min(1.0, score)
    
    def _generate_fallback(self, shared_context: SharedContext) -> LetterResult:
        """Generate fallback letter when AI fails"""
        
        customer = shared_context.customer_data
        insights = shared_context.customer_insights
        strategy = shared_context.personalization_strategy
        
        name = customer.get('name', 'Valued Customer')
        segment = insights.segment
        addressing_config = self.config['addressing'].get(segment, self.config['addressing']['ASSISTED'])
        
        # Build basic formal letter
        current_date = datetime.now().strftime("%d %B %Y")
        
        # Format salutation
        first_name = name.split()[0] if name != 'Valued Customer' else name
        last_name = name.split()[-1] if name != 'Valued Customer' and len(name.split()) > 1 else name
        salutation = addressing_config['salutation'].format(
            first_name=first_name,
            title='',
            last_name=last_name
        )
        
        # Build letterhead
        reference_number = f"LBG-{customer.get('customer_id', 'XXXX')}-{datetime.now().strftime('%Y%m')}"
        letterhead = self.config['letterhead_template'].format(
            date=current_date,
            customer_name=name,
            customer_address=customer.get('address', 'Customer Address'),
            reference_number=reference_number
        )
        
        # Build letter body
        letter_content = f"""{letterhead}

{salutation}

We are writing to you with important information regarding your account with Lloyds Bank.

{shared_context.original_letter}

Should you have any questions or require further assistance, please do not hesitate to contact us through your preferred channel. Our team is available to support you.

{addressing_config['closing']}

[Signature]
Lloyds Banking Group
"""
        
        # Add footer
        letter_content += self.config['footer_template']
        
        word_count = len(letter_content.split())
        
        return LetterResult(
            content=letter_content,
            word_count=word_count,
            page_count=self._calculate_page_count(word_count),
            personalization_elements=["customer_name", "segment_addressing"],
            formality_level=addressing_config['formality'],
            includes_return_envelope=segment == 'TRADITIONAL',
            tone_achieved=addressing_config['style'],
            language=customer.get('preferred_language', 'English'),
            generation_method="fallback",
            processing_time=0.0,
            quality_score=0.5
        )
    
    def _generate_simulation(self, shared_context: SharedContext) -> LetterResult:
        """Generate simulation letter for testing without AI"""
        
        customer = shared_context.customer_data
        insights = shared_context.customer_insights
        strategy = shared_context.personalization_strategy
        
        name = customer.get('name', 'Customer')
        
        simulation_content = f"""[SIMULATED LETTER - {customer.get('preferred_language', 'English').upper()}]

Lloyds Banking Group
25 Gresham Street
London EC2V 7HN

{datetime.now().strftime("%d %B %Y")}

{name}
[Customer Address]

Reference: LBG-SIM-{datetime.now().strftime('%Y%m')}

Dear {name},

[SIMULATION MODE]
Customer Segment: {insights.segment}
Personalization Level: {strategy.level.value}
Communication Style: {insights.communication_style}
Formality: {self.config['addressing'][insights.segment]['formality']}

This letter would be formally personalized using:
{chr(10).join(['• ' + hook for hook in insights.personalization_hooks[:3]])}

[Original letter content would appear here with full formal personalization throughout]

{self.config['addressing'][insights.segment]['closing']}

[Signature]
Lloyds Banking Group

[Generated by Smart Letter Generator - Simulation Mode]
"""
        
        word_count = len(simulation_content.split())
        
        return LetterResult(
            content=simulation_content,
            word_count=word_count,
            page_count=self._calculate_page_count(word_count),
            personalization_elements=["simulation_mode", "customer_segment", "personalization_level"],
            formality_level=self.config['addressing'][insights.segment]['formality'],
            includes_return_envelope=False,
            tone_achieved=insights.communication_style,
            language=customer.get('preferred_language', 'English'),
            generation_method="simulation",
            processing_time=0.0,
            quality_score=0.8
        )
    
    def _create_disabled_result(self, shared_context: SharedContext, reason: str) -> LetterResult:
        """Create result when letter is disabled"""
        return LetterResult(
            content="",
            word_count=0,
            page_count=0,
            personalization_elements=[],
            formality_level="",
            includes_return_envelope=False,
            tone_achieved="",
            language=shared_context.customer_data.get('preferred_language', 'English'),
            generation_method="disabled",
            processing_time=0.0,
            quality_score=0.0
        )
    
    def validate_letter(self, letter_result: LetterResult, shared_context: SharedContext) -> Dict[str, Any]:
        """Validate that the letter meets configuration requirements"""
        
        validation = {
            'is_valid': True,
            'quality_score': letter_result.quality_score,
            'issues': [],
            'achievements': [],
            'metrics': {
                'word_count': letter_result.word_count,
                'page_count': letter_result.page_count,
                'personalization_elements': len(letter_result.personalization_elements),
                'min_personalization_required': self.config['quality_thresholds']['min_personalization']
            }
        }
        
        # Check length
        if len(letter_result.content) < self.config['min_length']:
            validation['issues'].append("Letter too short")
            validation['is_valid'] = False
        elif len(letter_result.content) > self.config['max_length']:
            validation['issues'].append("Letter too long")
            validation['is_valid'] = False
        else:
            validation['achievements'].append(f"Optimal length: {letter_result.word_count} words across {letter_result.page_count} pages")
        
        # Check personalization
        min_personal = self.config['quality_thresholds']['min_personalization']
        if len(letter_result.personalization_elements) < min_personal:
            validation['issues'].append(f"Insufficient personalization (need {min_personal})")
        else:
            validation['achievements'].append(f"Applied {len(letter_result.personalization_elements)} personalizations")
        
        # Check formality
        segment = shared_context.customer_insights.segment
        expected_formality = self.config['addressing'][segment]['formality']
        if letter_result.formality_level == expected_formality:
            validation['achievements'].append(f"Appropriate formality for {segment} segment")
        else:
            validation['issues'].append(f"Formality mismatch: got {letter_result.formality_level}, expected {expected_formality}")
        
        # Check personalization level achievement
        target_level = shared_context.personalization_strategy.level
        achieved_elements = len(letter_result.personalization_elements)
        
        if target_level == PersonalizationLevel.HYPER and achieved_elements >= 8:
            validation['achievements'].append(f"Achieved HYPER personalization")
        elif target_level == PersonalizationLevel.DEEP and achieved_elements >= 6:
            validation['achievements'].append(f"Achieved DEEP personalization")
        elif target_level == PersonalizationLevel.MODERATE and achieved_elements >= 4:
            validation['achievements'].append(f"Achieved MODERATE personalization")
        else:
            validation['issues'].append(f"Did not achieve {target_level.value} personalization level")
        
        return validation

# Convenience function (MUST HAVE THIS)
def generate_smart_letter(shared_context: SharedContext, api_key: Optional[str] = None) -> LetterResult:
    """
    Convenience function to generate a smart letter from shared context
    
    Args:
        shared_context: Complete intelligence from SharedBrain
        api_key: Optional API key
        
    Returns:
        LetterResult with generated letter
    """
    generator = SmartLetterGenerator(api_key=api_key)
    return generator.generate_letter(shared_context)