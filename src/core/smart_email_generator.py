"""
Smart Email Generator - Hallucination-Free Version (HOTFIX)
FIXED: 'segment' is not defined error
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

# ============== UNIVERSAL ANTI-HALLUCINATION CONSTRAINTS ==============
UNIVERSAL_CONSTRAINTS = """
CRITICAL ANTI-HALLUCINATION RULES - APPLY TO EVERY EMAIL:

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
    hallucination_check_passed: bool  # NEW: Track if we avoided hallucinations

class SmartEmailGenerator:
    """
    Smart Email Generator - Hallucination-Free Version
    Takes a SharedContext and generates perfectly aligned email content WITHOUT inventing details
    """
    
    # ============== EMAIL CONFIGURATION ==============
    EMAIL_CONFIG = {
        'max_length': 5000,
        'min_length': 200,
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
            'use_verified_facts_only': True,
            'check_forbidden_list': True,
            'use_pattern_language': True,
            'reference_data_gaps': False
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
            'include_summary': True,
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
            'min_personalization': 2,
            'min_content_preservation': 0.9,
            'readability_score': 60,
            'max_paragraphs': 8,
            'ideal_paragraph_length': 100
        }
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the smart email generator"""
        self.api_key = api_key or os.getenv('CLAUDE_API_KEY')
        self.client = None
        self.config = self.EMAIL_CONFIG
        
        if self.api_key and ANTHROPIC_AVAILABLE:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.model = "claude-3-5-sonnet-20241022"
            print("✅ Smart Email Generator initialized (Hallucination-Free Mode)")
        else:
            print("⚠️ Smart Email Generator running in simulation mode")
    
    def generate_email(self, shared_context: SharedContext) -> EmailResult:
        """
        Generate a perfectly personalized email using the Shared Brain's intelligence
        WITHOUT any hallucinations or invented details
        """
        
        start_time = datetime.now()
        
        print(f"📧 Generating hallucination-free email for {shared_context.customer_data.get('name')}...")
        
        # Check if email is enabled
        if not shared_context.channel_decisions['enabled_channels'].get('email', True):
            return self._create_disabled_result(shared_context, "Email disabled by rules")
        
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
        
        print(f"✅ Smart email generated in {processing_time:.2f}s")
        print(f"   Words: {result.word_count}, Quality: {result.quality_score:.2%}")
        print(f"   🛡️ Hallucination Check: {'PASSED' if result.hallucination_check_passed else 'FAILED'}")
        
        return result
    
    def _generate_with_ai(self, shared_context: SharedContext) -> EmailResult:
        """Generate email using AI with strict anti-hallucination measures"""
        
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
        tone_adaptation = self.config.get('tone_adaptations', {}).get(doc_type.lower(), {})
        
        # Build the SAFE email generation prompt - PASS SEGMENT
        generation_prompt = self._build_safe_generation_prompt(
            shared_context.original_letter,
            customer,
            insights,
            strategy,
            content_strategy,
            greeting_config,
            tone_adaptation,
            doc_type,
            segment  # FIXED: Pass segment parameter
        )
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.3,
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
    
    def _build_safe_generation_prompt(
        self, 
        original_letter: str,
        customer: Dict[str, Any],
        insights,
        strategy,
        content_strategy,
        greeting_config: Dict[str, Any],
        tone_adaptation: Dict[str, Any],
        doc_type: str,
        segment: str  # FIXED: Added segment parameter
    ) -> str:
        """Build email generation prompt with STRONG anti-hallucination measures"""
        
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
        last_name = customer.get('name', '').split()[-1] if customer.get('name') and len(customer.get('name', '').split()) > 1 else customer.get('name', 'Customer')
        
        # Safe greeting based on what we actually know
        if segment == 'TRADITIONAL' and customer.get('name'):
            greeting = greeting_config['greeting'].format(
                title='Mr/Ms',  # Generic title unless we know gender
                last_name=last_name
            )
        elif customer.get('name'):
            greeting = greeting_config['greeting'].format(first_name=first_name)
        else:
            greeting = greeting_config['greeting'].replace('{first_name}', 'Valued Customer')
        
        # Get verified facts, data gaps, etc. with safe defaults
        verified_facts = getattr(insights, 'verified_facts', [])
        data_gaps = getattr(insights, 'data_gaps', [])
        forbidden_specifics = getattr(strategy, 'forbidden_specifics', [])
        pattern_language = getattr(strategy, 'pattern_language', {})
        
        # Build the prompt with STRONG constraints
        prompt = f"""{UNIVERSAL_CONSTRAINTS}

You are writing a personalized email for a Lloyds Bank customer using ONLY verified information.

ORIGINAL LETTER (preserve ALL information):
{original_letter}

VERIFIED CUSTOMER FACTS (ONLY use these for personalization):
{chr(10).join(['• ' + fact for fact in verified_facts]) if verified_facts else '• Customer name: ' + customer.get('name', 'Unknown')}

DATA WE DON'T HAVE (NEVER invent details about these):
{chr(10).join(['• ' + gap for gap in data_gaps]) if data_gaps else '• No data gaps identified'}

FORBIDDEN SPECIFICS (NEVER mention these):
{chr(10).join(['• ' + item for item in forbidden_specifics]) if forbidden_specifics else '• No specific items forbidden'}

SAFE PATTERN LANGUAGE (use these for missing information):
{chr(10).join([f'• Instead of {k}: use "{v}"' for k, v in pattern_language.items()]) if pattern_language else '• No pattern language defined'}

CUSTOMER SEGMENT: {segment}
LANGUAGE: {customer.get('preferred_language', 'English')}
TONE: {greeting_config['tone']}

EMAIL REQUIREMENTS:
- Start with: "{greeting},"
- End with: "{greeting_config['closing']}"
- Length: {self.config['min_length']}-{self.config['max_length']} characters
- Preserve ALL information from original letter
- Use bullet points for clarity where appropriate

PERSONALIZATION RULES:
1. Reference ONLY the verified facts listed above
2. For anything not in verified facts, use general language
3. NEVER mention specific:
   - Branch names or locations
   - Staff member names
   - Dates/times of interactions not in data
   - Previous conversations not documented
4. Use pattern language for missing information
5. Focus on what we KNOW, not what we guess

Generate the email as JSON:
{{
    "subject_line": "Subject under {self.config['subject_line']['max_length']} chars using ONLY verified info",
    "email_content": "Complete email with greeting, body preserving all letter content, and closing. Use ONLY verified facts for personalization.",
    "personalization_elements": ["list exactly which verified facts were referenced"],
    "tone_achieved": "description of tone used"
}}

CRITICAL: If you cannot verify a detail, use general language instead. Better to say "your local branch" than invent "Baker Street branch".

Write in {customer.get('preferred_language', 'English')}."""

        return prompt
    
    def _parse_ai_response(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse the AI response to extract email data"""
        
        # Remove markdown formatting if present
        content = content.replace('```json', '').replace('```', '').strip()
        
        # Clean up common issues
        content = content.replace('\n', ' ')
        content = content.replace('\r', '')
        content = content.replace('\t', ' ')
        
        try:
            parsed = json.loads(content)
            if parsed and isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
        
        # If direct parsing fails, try to extract JSON
        if '{' in content and '}' in content:
            try:
                json_start = content.index('{')
                json_end = content.rindex('}') + 1
                json_str = content[json_start:json_end]
                
                # Clean and parse
                json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
                parsed = json.loads(json_str)
                if parsed and isinstance(parsed, dict):
                    return parsed
            except (json.JSONDecodeError, ValueError) as e:
                print(f"JSON extraction failed: {e}")
        
        return None
    
    def _validate_no_hallucinations(self, email_content: str, shared_context: SharedContext) -> bool:
        """
        Validate that the generated email contains no hallucinations
        Returns True if safe, False if potential hallucinations detected
        """
        
        content_lower = email_content.lower()
        issues = []
        
        # Check for forbidden specifics
        if hasattr(shared_context.personalization_strategy, 'forbidden_specifics'):
            for forbidden in shared_context.personalization_strategy.forbidden_specifics:
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
                    potential_names = re.findall(name_pattern, email_content)
                    for name in potential_names:
                        if name.lower() not in customer_name.lower() and name not in ['Lloyds', 'Bank', 'Dear', 'Best', 'Yours']:
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
        
        # Check for specific dates/times not in data
        date_patterns = [
            r'\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
            r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}',
            r'\b\d{1,2}:\d{2}\s*(?:am|pm)\b',
            r'\blast\s+(?:week|month|tuesday|monday)\b'
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, content_lower):
                # Check if this date/time is in verified facts
                verified_facts = getattr(shared_context.customer_insights, 'verified_facts', [])
                if not any(re.search(pattern, fact.lower()) for fact in verified_facts):
                    issues.append("Specific date/time not in verified data")
        
        # Log any issues found
        if issues:
            print(f"  ⚠️ Potential hallucination risks detected: {issues}")
            return False
        
        return True
    
    def _create_email_result(
        self, 
        email_data: Dict[str, Any], 
        shared_context: SharedContext,
        method: str
    ) -> EmailResult:
        """Create EmailResult from parsed email data"""
        
        email_content = email_data.get('email_content', '')
        subject_line = email_data.get('subject_line', 'Important Update')
        
        # Add appropriate footer
        doc_type = shared_context.document_classification.get('primary_classification', 'INFORMATIONAL')
        if doc_type == 'PROMOTIONAL':
            email_content += self.config['footer_templates']['promotional']
        elif doc_type == 'REGULATORY':
            email_content += self.config['footer_templates']['standard']
        else:
            email_content += self.config['footer_templates']['security']
        
        # Validate no hallucinations
        hallucination_check = self._validate_no_hallucinations(email_content, shared_context)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(
            email_content,
            email_data.get('personalization_elements', []),
            shared_context,
            hallucination_check
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
            quality_score=quality_score,
            hallucination_check_passed=hallucination_check
        )
    
    def _calculate_quality_score(
        self, 
        email_content: str, 
        personalization_elements: List[str],
        shared_context: SharedContext,
        hallucination_check: bool
    ) -> float:
        """Calculate quality score with hallucination check factor"""
        
        score = 0.5  # Base score
        
        # Hallucination check is most important
        if hallucination_check:
            score += 0.2
        else:
            score -= 0.2  # Penalty for potential hallucinations
        
        # Check personalization depth (less aggressive now)
        min_personal = self.config['quality_thresholds']['min_personalization']
        if len(personalization_elements) >= min_personal:
            score += 0.1
        
        # Check content length
        if self.config['min_length'] <= len(email_content) <= self.config['max_length']:
            score += 0.1
        
        # Check if we used verified facts
        if personalization_elements:
            # Check if personalizations are actually from verified facts
            verified_facts = getattr(shared_context.customer_insights, 'verified_facts', [])
            verified = 0
            for element in personalization_elements:
                if any(element.lower() in fact.lower() for fact in verified_facts):
                    verified += 1
            if verified > 0:
                score += 0.1
        
        # Check appropriate tone for segment
        segment = shared_context.customer_insights.segment
        if segment in email_content or segment.lower() in str(personalization_elements).lower():
            score += 0.05
        
        return min(1.0, max(0.0, score))
    
    def _generate_fallback(self, shared_context: SharedContext) -> EmailResult:
        """Generate fallback email when AI fails - SAFE version"""
        
        customer = shared_context.customer_data
        insights = shared_context.customer_insights
        
        name = customer.get('name', 'Valued Customer')
        segment = insights.segment
        greeting_config = self.config['greeting_styles'].get(segment, self.config['greeting_styles']['ASSISTED'])
        
        # Format SAFE greeting
        first_name = name.split()[0] if name != 'Valued Customer' else 'Valued Customer'
        if segment == 'TRADITIONAL' and name != 'Valued Customer':
            greeting = f"Dear Mr/Ms {name.split()[-1]}"
        elif name != 'Valued Customer':
            greeting = f"Hello {first_name}"
        else:
            greeting = "Dear Valued Customer"
        
        # Build SAFE email using only verified facts
        verified_facts = getattr(insights, 'verified_facts', [])
        verified_refs = []
        if verified_facts:
            # Use only the most basic verified facts
            for fact in verified_facts[:2]:
                if 'balance' in fact.lower():
                    verified_refs.append("your account")
                elif 'digital' in fact.lower():
                    verified_refs.append("your online banking")
        
        personal_note = ""
        if verified_refs:
            personal_note = f"Regarding {' and '.join(verified_refs)}, "
        
        email_content = f"""{greeting},

{personal_note}we have important information about your account that requires your attention.

{shared_context.original_letter}

If you have any questions, please don't hesitate to contact us at 0345 300 0000 or visit your local branch.

{greeting_config['closing']}"""
        
        return EmailResult(
            content=email_content,
            subject_line=f"Important Update for {name}",
            word_count=len(email_content.split()),
            character_count=len(email_content),
            personalization_elements=["customer_name", "segment_appropriate_greeting"],
            tone_achieved=greeting_config['tone'],
            language=customer.get('preferred_language', 'English'),
            generation_method="fallback",
            processing_time=0.0,
            quality_score=0.6,
            hallucination_check_passed=True  # Fallback is always safe
        )
    
    def _generate_simulation(self, shared_context: SharedContext) -> EmailResult:
        """Generate simulation email for testing without AI"""
        
        customer = shared_context.customer_data
        insights = shared_context.customer_insights
        
        name = customer.get('name', 'Customer')
        
        # Safe defaults with getattr
        verified_facts = getattr(insights, 'verified_facts', [])
        data_gaps = getattr(insights, 'data_gaps', [])
        
        simulation_content = f"""Dear {name},

[SIMULATED HALLUCINATION-FREE EMAIL - {customer.get('preferred_language', 'English').upper()}]

Customer Segment: {insights.segment}
Personalization Level: {shared_context.personalization_strategy.level.value}

USING ONLY VERIFIED FACTS:
{chr(10).join(['• ' + fact for fact in verified_facts[:3]]) if verified_facts else '• No verified facts available'}

AVOIDING THESE DATA GAPS:
{chr(10).join(['• ' + gap for gap in data_gaps[:3]]) if data_gaps else '• No data gaps identified'}

[Original letter content would appear here with personalization based ONLY on verified facts]

Best regards,
Lloyds Bank

[Generated by Smart Email Generator - Simulation Mode - Hallucination-Free]"""
        
        return EmailResult(
            content=simulation_content,
            subject_line=f"[SIMULATION] Update for {name}",
            word_count=len(simulation_content.split()),
            character_count=len(simulation_content),
            personalization_elements=["simulation_mode"],
            tone_achieved=insights.communication_style,
            language=customer.get('preferred_language', 'English'),
            generation_method="simulation",
            processing_time=0.0,
            quality_score=0.8,
            hallucination_check_passed=True
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
            quality_score=0.0,
            hallucination_check_passed=True
        )
    
    def validate_email(self, email_result: EmailResult, shared_context: SharedContext) -> Dict[str, Any]:
        """Validate that the email meets requirements AND contains no hallucinations"""
        
        validation = {
            'is_valid': True,
            'quality_score': email_result.quality_score,
            'hallucination_free': email_result.hallucination_check_passed,
            'issues': [],
            'achievements': [],
            'metrics': {
                'word_count': email_result.word_count,
                'character_count': email_result.character_count,
                'personalization_elements': len(email_result.personalization_elements),
                'min_personalization_required': self.config['quality_thresholds']['min_personalization'],
                'hallucination_check': 'PASSED' if email_result.hallucination_check_passed else 'FAILED'
            }
        }
        
        # FIRST AND MOST IMPORTANT: Check hallucinations
        if not email_result.hallucination_check_passed:
            validation['issues'].append("⚠️ POTENTIAL HALLUCINATIONS DETECTED")
            validation['is_valid'] = False
        else:
            validation['achievements'].append("✅ No hallucinations detected")
        
        # Check length
        if email_result.character_count < self.config['min_length']:
            validation['issues'].append("Email too short")
            validation['is_valid'] = False
        elif email_result.character_count > self.config['max_length']:
            validation['issues'].append("Email too long")
            validation['is_valid'] = False
        else:
            validation['achievements'].append(f"Optimal length: {email_result.word_count} words")
        
        # Check personalization (less strict now)
        min_personal = self.config['quality_thresholds']['min_personalization']
        if len(email_result.personalization_elements) < min_personal:
            validation['issues'].append(f"Could use more personalization (have {len(email_result.personalization_elements)}, want {min_personal})")
        else:
            validation['achievements'].append(f"Applied {len(email_result.personalization_elements)} safe personalizations")
        
        # Check if personalizations are from verified facts
        verified_facts = getattr(shared_context.customer_insights, 'verified_facts', [])
        verified_count = 0
        for element in email_result.personalization_elements:
            if any(element.lower() in fact.lower() for fact in verified_facts):
                verified_count += 1
        
        if verified_count > 0:
            validation['achievements'].append(f"Used {verified_count} verified facts")
        else:
            validation['issues'].append("No verified facts used in personalization")
        
        return validation

# Convenience function
def generate_smart_email(shared_context: SharedContext, api_key: Optional[str] = None) -> EmailResult:
    """
    Convenience function to generate a smart email from shared context
    
    Args:
        shared_context: Complete intelligence from SharedBrain
        api_key: Optional API key
        
    Returns:
        EmailResult with generated email (hallucination-free)
    """
    generator = SmartEmailGenerator(api_key=api_key)
    return generator.generate_email(shared_context)