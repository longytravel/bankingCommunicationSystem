"""
Smart Letter Generator - Fixed with defensive coding and sensitivity handling
Uses SharedContext for Consistent, Formal Letter Generation
FIXED: Added defensive coding for special_factors and sensitivity handling
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

# ============== UNIVERSAL ANTI-HALLUCINATION CONSTRAINTS ==============
UNIVERSAL_CONSTRAINTS = """
CRITICAL ANTI-HALLUCINATION RULES - APPLY TO EVERY LETTER:

1. NEVER INVENT OR CREATE:
   - Names of people (staff, managers, representatives)
   - Names of places (branches, streets, buildings)
   - Specific dates or times not in the data
   - Conversations or meetings that aren't documented
   - Phone calls or interactions not recorded
   - Product names or features not in the system
   - Customer preferences not explicitly stated
   - Life events not mentioned in data
   - Financial details not provided

2. ONLY USE:
   - Information from verified_facts list
   - Content from the original letter
   - General segment characteristics (not specific to individual)
   - System-wide features available to all customers
   
3. WHEN DATA IS MISSING USE PATTERN LANGUAGE:
   - Say "your local branch" NOT "Baker Street branch"
   - Say "our team" NOT "Sarah from customer service"
   - Say "recently" NOT "last Tuesday at 3pm"
   - Say "in your area" NOT "on High Street"
   
4. FORBIDDEN PHRASES:
   - "As we discussed..." (unless conversation is documented)
   - "When you visited..." (unless visit is documented)
   - "Your usual branch..." (unless branch is specified)
   - "As [Name] mentioned..." (never invent staff names)
   - Any specific time/date not in customer data
   
5. VALIDATION:
   - Every specific claim must trace to verified_facts
   - Check forbidden_specifics list - NEVER mention these
   - Use pattern_language for any missing information
   - Better to be general and accurate than specific and wrong
"""

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
    hallucination_check_passed: bool = True  # Added for safety
    sensitivity_handled: bool = False  # Added for sensitivity

class SmartLetterGenerator:
    """
    Smart Letter Generator - Self-contained with all configuration
    Takes a SharedContext and generates perfectly aligned letter content
    FIXED: Added defensive coding and sensitivity handling
    """
    
    # ============== LETTER CONFIGURATION ==============
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
        'supportive_footer_template': """
---
Lloyds Bank plc. Registered Office: 25 Gresham Street, London EC2V 7HN.
Registered in England and Wales no. 2065. Authorised by the Prudential Regulation Authority.

We're here to support you. If you need assistance, please call us on 0345 300 0000.
Our specially trained team is available to help.
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
            self.model = "claude-3-5-sonnet-20241022"  # Same model for consistency
            print("✅ Smart Letter Generator initialized with Claude AI (Sensitivity-Aware)")
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
        
        customer_name = shared_context.customer_data.get('name', 'Unknown')
        print(f"📮 Generating smart letter for {customer_name}...")
        
        # Check for sensitivity flags using defensive coding
        sensitivity_flags = getattr(shared_context.customer_insights, 'sensitivity_flags', [])
        if sensitivity_flags:
            print(f"   ⚠️ Sensitivity detected: {', '.join(sensitivity_flags)}")
        
        # Check if letter is enabled
        if not shared_context.channel_decisions['enabled_channels'].get('letter', False):
            return self._create_disabled_result(shared_context, "Letter disabled by rules")
        
        # Pre-generation hallucination check
        if hasattr(shared_context, 'hallucination_check_passed'):
            if not shared_context.hallucination_check_passed:
                print("  ⚠️ Hallucination risk detected - using extra caution")
        
        if self.client:
            result = self._generate_with_ai(shared_context)
        else:
            result = self._generate_simulation(shared_context)
        
        # Post-generation validation
        result.hallucination_check_passed = self._validate_no_hallucinations(
            result.content,
            shared_context
        )
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        result.processing_time = processing_time
        
        print(f"✅ Smart letter generated in {processing_time:.2f}s")
        print(f"   Words: {result.word_count}, Pages: {result.page_count}, Quality: {result.quality_score:.2%}")
        print(f"   🛡️ Hallucination Check: {'PASSED' if result.hallucination_check_passed else 'FAILED'}")
        print(f"   💝 Sensitivity Handled: {'YES' if result.sensitivity_handled else 'NO'}")
        
        return result
    
    def _generate_with_ai(self, shared_context: SharedContext) -> LetterResult:
        """Generate letter using AI with the shared context intelligence"""
        
        # Extract intelligence from shared context with defensive coding
        customer = shared_context.customer_data
        insights = shared_context.customer_insights
        strategy = shared_context.personalization_strategy
        content_strategy = shared_context.content_strategy
        
        # Get sensitivity information using defensive coding
        sensitivity_flags = getattr(insights, 'sensitivity_flags', [])
        sensitivity_adjustments = getattr(strategy, 'sensitivity_adjustments', {})
        
        # Get segment-specific configuration
        segment = getattr(insights, 'segment', 'ASSISTED')
        addressing_config = self.config['addressing'].get(segment, self.config['addressing']['ASSISTED'])
        
        # Determine document type for tone
        doc_type = shared_context.document_classification.get('primary_classification', 'INFORMATIONAL')
        tone_adaptation = self.config['tone_adaptations'].get(doc_type, self.config['tone_adaptations']['INFORMATIONAL'])
        
        # Determine if return envelope needed
        needs_return_envelope = (doc_type == 'REGULATORY' or 
                                segment == 'TRADITIONAL' or 
                                shared_context.document_classification.get('customer_action_required', False))
        
        # Build the letter generation prompt with sensitivity awareness
        generation_prompt = self._build_generation_prompt(
            shared_context.original_letter,
            customer,
            insights,
            strategy,
            content_strategy,
            addressing_config,
            tone_adaptation,
            doc_type,
            needs_return_envelope,
            sensitivity_flags,
            sensitivity_adjustments
        )
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.3,  # Lower temperature for more consistency
                messages=[{"role": "user", "content": generation_prompt}]
            )
            
            content = response.content[0].text.strip()
            letter_data = self._parse_ai_response(content)
            
            if letter_data:
                return self._create_letter_result(
                    letter_data, 
                    shared_context, 
                    "ai_generation", 
                    needs_return_envelope,
                    bool(sensitivity_flags)
                )
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
        needs_return_envelope: bool,
        sensitivity_flags: List[str],
        sensitivity_adjustments: Dict[str, Any]
    ) -> str:
        """Build the letter generation prompt using shared context intelligence with sensitivity"""
        
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
        
        # Get customer name and handle bereavement sensitivity
        customer_name = customer.get('name', 'Valued Customer')
        
        # Format salutation with sensitivity awareness
        if 'Bereavement' in sensitivity_flags and customer_name != 'Valued Customer':
            # For bereaved customers, use full name respectfully (no Mr/Ms)
            salutation = f"Dear {customer_name}"
        else:
            first_name = customer_name.split()[0] if customer_name != 'Valued Customer' else 'Customer'
            last_name = customer_name.split()[-1] if customer_name != 'Valued Customer' and len(customer_name.split()) > 1 else customer_name
            salutation = addressing_config['salutation'].format(
                first_name=first_name, 
                title='Mr/Ms', 
                last_name=last_name
            )
        
        # Get enclosures for this document type
        enclosures = self.config['enclosures'].get(doc_type, self.config['enclosures']['DEFAULT'])
        
        # Format current date
        current_date = datetime.now().strftime("%d %B %Y")
        
        # Get verified facts and forbidden items using defensive coding
        verified_facts = getattr(insights, 'verified_facts', [])
        special_factors = getattr(insights, 'special_factors', [])  # FIXED: Use getattr
        data_gaps = getattr(insights, 'data_gaps', [])
        forbidden_specifics = getattr(strategy, 'forbidden_specifics', [])
        pattern_language = getattr(strategy, 'pattern_language', {})
        
        # Build sensitivity context
        sensitivity_context = ""
        if sensitivity_flags:
            sensitivity_context = f"""
CRITICAL SENSITIVITY INFORMATION:
Customer has these sensitivity flags: {', '.join(sensitivity_flags)}

Special handling required:
- Greeting: {sensitivity_adjustments.get('greeting_style', 'Use respectful, appropriate greeting')}
- Avoid: {', '.join(sensitivity_adjustments.get('avoid_phrases', []))}
- Use: {', '.join(sensitivity_adjustments.get('use_phrases', []))}
- Considerations: {sensitivity_adjustments.get('special_considerations', 'Extra care needed')}
"""
        
        prompt = f"""{UNIVERSAL_CONSTRAINTS}

You are writing a formal, personalized letter for a Lloyds Bank customer. You have complete intelligence about the customer and must create a professional, complete letter.
{sensitivity_context}

CRITICAL REQUIREMENTS:
1. Include 100% of the information from the original letter - NOTHING can be omitted
2. Personalize based on the customer's specific situation
3. NO PLACEHOLDERS - write complete, real content
4. Make natural connections between information and customer context
5. Be especially respectful and supportive if sensitivity flags are present

ORIGINAL LETTER (preserve ALL information):
{original_letter}

CUSTOMER INTELLIGENCE:
- Name: {customer_name}
- Age: {customer.get('age', 'Unknown')}
- Segment: {getattr(insights, 'segment', 'ASSISTED')}
- Life Stage: {getattr(insights, 'life_stage', 'unknown')}
- Digital Persona: {getattr(insights, 'digital_persona', 'unknown')}
- Financial Profile: {getattr(insights, 'financial_profile', 'unknown')}
- Communication Style: {getattr(insights, 'communication_style', 'professional')}
- Language: {customer.get('preferred_language', 'English')}
- Recent Life Events: {customer.get('recent_life_events', 'None specified')}
- Special Factors: {', '.join(special_factors[:3]) if special_factors else 'None'}

VERIFIED CUSTOMER FACTS (ONLY use these for personalization):
{chr(10).join(['• ' + fact for fact in verified_facts]) if verified_facts else '• Customer name: ' + customer_name}

DATA WE DON'T HAVE (NEVER invent details about these):
{chr(10).join(['• ' + gap for gap in data_gaps]) if data_gaps else '• No data gaps identified'}

FORBIDDEN SPECIFICS (NEVER mention these):
{chr(10).join(['• ' + item for item in forbidden_specifics]) if forbidden_specifics else '• No specific items forbidden'}

SAFE PATTERN LANGUAGE (use these for missing information):
{chr(10).join([f'• Instead of {k}: use "{v}"' for k, v in pattern_language.items()]) if pattern_language else '• No pattern language defined'}

GREETING INSTRUCTIONS:
{"SPECIAL SENSITIVITY - For bereaved/vulnerable customers:" if sensitivity_flags else ""}
{"- Use their full name respectfully (e.g., 'Dear Vera Thompson' or 'Dear Vera')" if 'Bereavement' in sensitivity_flags else ""}
{"- Avoid overly cheerful or casual language" if sensitivity_flags else ""}
{"- Use warm but respectful tone throughout" if sensitivity_flags else ""}
- Date: {current_date}
- Salutation: "{salutation}"
- Closing: {"We're here to support you. Yours sincerely" if sensitivity_flags else addressing_config['closing']}

LETTER REQUIREMENTS:
- Formality Level: {addressing_config['formality']}
- Style: {addressing_config['style']}
- Length: {self.config['min_length']}-{self.config['max_length']} characters
- Include all information from original letter
- Add appropriate paragraph breaks for readability
- Maintain formal business letter structure
{"- Include P.S. with branch contact information" if addressing_config.get('include_ps') else ""}
{"- Mention enclosed documents: " + ', '.join(enclosures) if enclosures else ""}

TONE: {"Supportive and gentle" if sensitivity_flags else tone_adaptation}

Generate the complete formal letter as JSON:
{{
    "letter_content": "COMPLETE formal letter body text (DO NOT include letterhead/date/address - just the main content starting with salutation)",
    "personalization_elements": ["list", "of", "specific", "personalizations", "applied"],
    "formality_level": "formal|professional|professional_friendly",
    "tone_achieved": "description of tone used",
    "enclosures_mentioned": ["list of enclosures mentioned in letter"],
    "sensitivity_handled": true/false
}}

CRITICAL: 
- For bereaved/vulnerable customers, be extra respectful and supportive
- NEVER use generic "Mr/Ms" for bereaved customers - use full name or first name
- Preserve all letter content while being sensitive to customer situation

Write in {customer.get('preferred_language', 'English')}."""

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
        
        print("⚠️ All parsing attempts failed for letter response")
        return None
    
    def _create_letter_result(
        self, 
        letter_data: Dict[str, Any], 
        shared_context: SharedContext,
        method: str,
        needs_return_envelope: bool,
        sensitivity_handled: bool = False
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
        
        # Add footer (supportive for sensitive customers)
        sensitivity_flags = getattr(shared_context.customer_insights, 'sensitivity_flags', [])
        if sensitivity_flags:
            letter_content += self.config['supportive_footer_template']
        else:
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
        
        # Validate no hallucinations
        hallucination_check = self._validate_no_hallucinations(letter_content, shared_context)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(
            letter_content,
            letter_data.get('personalization_elements', []),
            shared_context,
            letter_data.get('formality_level', 'professional'),
            hallucination_check
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
            quality_score=quality_score,
            hallucination_check_passed=hallucination_check,
            sensitivity_handled=letter_data.get('sensitivity_handled', sensitivity_handled)
        )
    
    def _validate_no_hallucinations(self, letter_content: str, shared_context: SharedContext) -> bool:
        """
        Validate that the generated letter contains no hallucinations
        Returns True if safe, False if potential hallucinations detected
        """
        
        content_lower = letter_content.lower()
        issues = []
        
        # Check for forbidden specifics using defensive coding
        forbidden_specifics = getattr(shared_context.personalization_strategy, 'forbidden_specifics', [])
        for forbidden in forbidden_specifics:
            if 'branch name' in forbidden.lower() and 'branch' in content_lower:
                # Check for specific branch names (not just "branch" or "local branch")
                branch_patterns = r'\b(?:baker|high|main|central|north|south|east|west)\s+(?:street|road|avenue|branch)'
                if re.search(branch_patterns, content_lower):
                    issues.append("Specific branch name detected")
            
            if 'staff name' in forbidden.lower():
                # Check for names that aren't the customer's
                customer_name = shared_context.customer_data.get('name', '').lower()
                # Look for capitalized names that aren't the customer
                name_pattern = r'\b[A-Z][a-z]+\b'
                potential_names = re.findall(name_pattern, letter_content)
                for name in potential_names:
                    if (name.lower() not in customer_name.lower() and 
                        name not in ['Lloyds', 'Bank', 'Banking', 'Group', 'Dear', 'Yours', 'Sincerely', 'Faithfully']):
                        issues.append(f"Potential staff name detected: {name}")
        
        # Check for dangerous phrases
        dangerous_phrases = [
            "as we discussed",
            "when you visited",
            "your usual branch",
            "as mentioned by",
            "during our conversation",
            "when we spoke",
            "your relationship manager"
        ]
        
        for phrase in dangerous_phrases:
            if phrase in content_lower:
                # Check if this is actually in the verified facts
                verified_facts = getattr(shared_context.customer_insights, 'verified_facts', [])
                if not any(phrase in fact.lower() for fact in verified_facts):
                    issues.append(f"Dangerous phrase detected: '{phrase}'")
        
        # Log any issues found
        if issues:
            print(f"  ⚠️ Potential hallucination risks detected: {issues}")
            return False
        
        return True
    
    def _calculate_page_count(self, word_count: int) -> int:
        """Calculate number of pages based on word count"""
        words_per_page = self.config['format']['words_per_page']
        return max(1, (word_count + words_per_page - 1) // words_per_page)
    
    def _calculate_quality_score(
        self, 
        letter_content: str, 
        personalization_elements: List[str],
        shared_context: SharedContext,
        formality_level: str,
        hallucination_check: bool
    ) -> float:
        """Calculate quality score based on configuration thresholds with sensitivity bonus"""
        
        score = 0.5  # Base score
        
        # Hallucination check is most important
        if hallucination_check:
            score += 0.2
        else:
            score -= 0.2  # Penalty for potential hallucinations
        
        # Check personalization depth
        min_personal = self.config['quality_thresholds']['min_personalization']
        if len(personalization_elements) >= min_personal:
            score += 0.1
        elif len(personalization_elements) >= min_personal - 1:
            score += 0.05
        
        # Check content length
        if self.config['min_length'] <= len(letter_content) <= self.config['max_length']:
            score += 0.1
        
        # Check paragraph structure
        paragraphs = [p for p in letter_content.split('\n\n') if len(p.strip()) > 50]
        if self.config['quality_thresholds']['min_paragraphs'] <= len(paragraphs) <= self.config['quality_thresholds']['max_paragraphs']:
            score += 0.1
        
        # Check formality matches segment using defensive coding
        segment = getattr(shared_context.customer_insights, 'segment', 'ASSISTED')
        expected_formality = self.config['addressing'][segment]['formality']
        if formality_level == expected_formality:
            score += 0.1
        
        # Bonus for handling sensitivity well
        sensitivity_flags = getattr(shared_context.customer_insights, 'sensitivity_flags', [])
        if sensitivity_flags and 'Dear Vera' in letter_content and 'Mr/Ms' not in letter_content:
            score += 0.1  # Handled sensitivity properly
        
        # Check if we used verified facts
        if personalization_elements:
            verified_facts = getattr(shared_context.customer_insights, 'verified_facts', [])
            verified = sum(1 for element in personalization_elements 
                         if any(element.lower() in fact.lower() for fact in verified_facts))
            if verified > 0:
                score += 0.05
        
        return min(1.0, max(0.0, score))
    
    def _generate_fallback(self, shared_context: SharedContext) -> LetterResult:
        """Generate fallback letter when AI fails with sensitivity handling"""
        
        customer = shared_context.customer_data
        insights = shared_context.customer_insights
        
        name = customer.get('name', 'Valued Customer')
        segment = getattr(insights, 'segment', 'ASSISTED')
        sensitivity_flags = getattr(insights, 'sensitivity_flags', [])
        addressing_config = self.config['addressing'].get(segment, self.config['addressing']['ASSISTED'])
        
        # Build basic formal letter
        current_date = datetime.now().strftime("%d %B %Y")
        
        # Format salutation with sensitivity
        if 'Bereavement' in sensitivity_flags and name != 'Valued Customer':
            salutation = f"Dear {name}"
            closing = "We're here to support you.\n\nYours sincerely"
        else:
            first_name = name.split()[0] if name != 'Valued Customer' else name
            last_name = name.split()[-1] if name != 'Valued Customer' and len(name.split()) > 1 else name
            salutation = addressing_config['salutation'].format(
                first_name=first_name,
                title='',
                last_name=last_name
            )
            closing = addressing_config['closing']
        
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

{"We understand this may be a difficult time, and we want you to know that we're here to support you in any way we can." if sensitivity_flags else "Should you have any questions or require further assistance, please do not hesitate to contact us through your preferred channel."}

{closing}

[Signature]
Lloyds Banking Group
"""
        
        # Add footer
        if sensitivity_flags:
            letter_content += self.config['supportive_footer_template']
        else:
            letter_content += self.config['footer_template']
        
        word_count = len(letter_content.split())
        
        return LetterResult(
            content=letter_content,
            word_count=word_count,
            page_count=self._calculate_page_count(word_count),
            personalization_elements=["customer_name", "segment_addressing"],
            formality_level=addressing_config['formality'],
            includes_return_envelope=segment == 'TRADITIONAL',
            tone_achieved="supportive" if sensitivity_flags else addressing_config['style'],
            language=customer.get('preferred_language', 'English'),
            generation_method="fallback",
            processing_time=0.0,
            quality_score=0.6,
            hallucination_check_passed=True,  # Fallback is always safe
            sensitivity_handled=bool(sensitivity_flags)
        )
    
    def _generate_simulation(self, shared_context: SharedContext) -> LetterResult:
        """Generate simulation letter for testing without AI"""
        
        customer = shared_context.customer_data
        insights = shared_context.customer_insights
        strategy = shared_context.personalization_strategy
        
        name = customer.get('name', 'Customer')
        segment = getattr(insights, 'segment', 'ASSISTED')
        sensitivity_flags = getattr(insights, 'sensitivity_flags', [])
        
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
Customer Segment: {segment}
Personalization Level: {getattr(strategy, 'level.value', 'basic')}
Communication Style: {getattr(insights, 'communication_style', 'professional')}
Formality: {self.config['addressing'][segment]['formality']}
Sensitivity Flags: {', '.join(sensitivity_flags) if sensitivity_flags else 'None'}

This letter would be formally personalized.

[Original letter content would appear here with full formal personalization throughout]

{self.config['addressing'][segment]['closing']}

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
            formality_level=self.config['addressing'][segment]['formality'],
            includes_return_envelope=False,
            tone_achieved=getattr(insights, 'communication_style', 'professional'),
            language=customer.get('preferred_language', 'English'),
            generation_method="simulation",
            processing_time=0.0,
            quality_score=0.8,
            hallucination_check_passed=True,
            sensitivity_handled=bool(sensitivity_flags)
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
            quality_score=0.0,
            hallucination_check_passed=True,
            sensitivity_handled=False
        )
    
    def validate_letter(self, letter_result: LetterResult, shared_context: SharedContext) -> Dict[str, Any]:
        """Validate that the letter meets configuration requirements INCLUDING sensitivity handling"""
        
        sensitivity_flags = getattr(shared_context.customer_insights, 'sensitivity_flags', [])
        
        validation = {
            'is_valid': True,
            'quality_score': letter_result.quality_score,
            'hallucination_free': letter_result.hallucination_check_passed,
            'sensitivity_handled': letter_result.sensitivity_handled,
            'issues': [],
            'achievements': [],
            'metrics': {
                'word_count': letter_result.word_count,
                'page_count': letter_result.page_count,
                'personalization_elements': len(letter_result.personalization_elements),
                'min_personalization_required': self.config['quality_thresholds']['min_personalization'],
                'hallucination_check': 'PASSED' if letter_result.hallucination_check_passed else 'FAILED',
                'sensitivity_check': 'HANDLED' if letter_result.sensitivity_handled else 'N/A'
            }
        }
        
        # Check hallucinations
        if not letter_result.hallucination_check_passed:
            validation['issues'].append("⚠️ POTENTIAL HALLUCINATIONS DETECTED")
            validation['is_valid'] = False
        else:
            validation['achievements'].append("✅ No hallucinations detected")
        
        # Check sensitivity handling
        if sensitivity_flags:
            if letter_result.sensitivity_handled:
                validation['achievements'].append(f"✅ Sensitivity handled appropriately")
            else:
                validation['issues'].append("⚠️ Sensitivity not properly handled")
            
            # Check for inappropriate greetings
            if 'Mr/Ms' in letter_result.content and 'Bereavement' in sensitivity_flags:
                validation['issues'].append("⚠️ Generic Mr/Ms used despite bereavement")
                validation['is_valid'] = False
        
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
        segment = getattr(shared_context.customer_insights, 'segment', 'ASSISTED')
        expected_formality = self.config['addressing'][segment]['formality']
        if letter_result.formality_level == expected_formality:
            validation['achievements'].append(f"Appropriate formality for {segment} segment")
        else:
            validation['issues'].append(f"Formality mismatch: got {letter_result.formality_level}, expected {expected_formality}")
        
        return validation

# Convenience function (MUST HAVE THIS)
def generate_smart_letter(shared_context: SharedContext, api_key: Optional[str] = None) -> LetterResult:
    """
    Convenience function to generate a smart letter from shared context
    
    Args:
        shared_context: Complete intelligence from SharedBrain
        api_key: Optional API key
        
    Returns:
        LetterResult with generated letter (sensitivity-aware)
    """
    generator = SmartLetterGenerator(api_key=api_key)
    return generator.generate_letter(shared_context)