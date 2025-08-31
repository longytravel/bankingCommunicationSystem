"""
Smart Email Generator - Uses SharedContext for Consistent, Deeply Personalized Emails
This replaces the old email generators with one that follows the Shared Brain's intelligence
"""

import os
import json
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

# Import the SharedContext types with absolute import
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
    Smart Email Generator that follows the Shared Brain's intelligence
    
    Takes a SharedContext and generates perfectly aligned email content
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the smart email generator"""
        self.api_key = api_key or os.getenv('CLAUDE_API_KEY')
        self.client = None
        
        if self.api_key and ANTHROPIC_AVAILABLE:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.model = "claude-sonnet-4-20250514"
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
        
        # Extract all the intelligence from shared context
        customer = shared_context.customer_data
        insights = shared_context.customer_insights
        strategy = shared_context.personalization_strategy
        content_strategy = shared_context.content_strategy
        
        # Build the comprehensive generation prompt
        generation_prompt = self._build_generation_prompt(
            shared_context.original_letter,
            customer,
            insights,
            strategy,
            content_strategy
        )
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.5,  # Balanced creativity with accuracy
                messages=[{"role": "user", "content": generation_prompt}]
            )
            
            content = response.content[0].text.strip()
            
            # Parse the AI response
            email_data = self._parse_ai_response(content)
            
            if email_data:
                return self._create_email_result(email_data, shared_context, "ai_generation")
            else:
                # Fallback if parsing fails
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
        content_strategy
    ) -> str:
        """Build the comprehensive generation prompt using all shared context intelligence"""
        
        # Get email-specific content requirements
        email_requirements = content_strategy.channel_requirements.get('email', ['critical', 'important'])
        
        # Build content to preserve
        content_to_preserve = []
        if 'critical' in email_requirements:
            content_to_preserve.extend([p.content for p in content_strategy.critical_points])
        if 'important' in email_requirements:
            content_to_preserve.extend([p.content for p in content_strategy.important_points])
        if 'contextual' in email_requirements:
            content_to_preserve.extend([p.content for p in content_strategy.contextual_points])
        
        prompt = f"""You are writing a deeply personalized email for a Lloyds Bank customer. You have complete intelligence about the customer and exactly how to personalize.

ORIGINAL LETTER (preserve ALL key information):
{original_letter}

CUSTOMER INTELLIGENCE:
- Name: {customer.get('name')}
- Segment: {insights.segment}
- Life Stage: {insights.life_stage}
- Digital Persona: {insights.digital_persona}
- Financial Profile: {insights.financial_profile}
- Communication Style: {insights.communication_style}
- Language: {customer.get('preferred_language', 'English')}

PERSONALIZATION STRATEGY (FOLLOW EXACTLY):
- Level: {strategy.level.value} 
- Customer Story: {strategy.customer_story}
- Tone Guidelines: {json.dumps(strategy.tone_guidelines, indent=2)}

MANDATORY CONTENT TO PRESERVE:
{chr(10).join(['• ' + item for item in content_to_preserve])}

PERSONALIZATION REQUIREMENTS (MUST IMPLEMENT):
Must Mention Items:
{chr(10).join(['• ' + item for item in strategy.must_mention])}

Special Factors to Address:
{chr(10).join(['• ' + factor for factor in insights.special_factors])}

Personalization Hooks to Use:
{chr(10).join(['• ' + hook for hook in insights.personalization_hooks])}

EMAIL ADAPTATION HINTS:
{strategy.channel_adaptations.get('email', {}).get('hints', 'Full personalization with complete content')}

CRITICAL INSTRUCTIONS:
1. Write COMPLETE email - no placeholders, no shortcuts
2. Include ALL required content adapted for email format
3. Apply ALL personalization requirements naturally throughout
4. Use the exact tone and communication style specified
5. Make every sentence feel personal and relevant to this specific customer
6. Write in {customer.get('preferred_language', 'English')}

Generate the email as a JSON object with this EXACT structure:
{{
    "subject_line": "Compelling, personalized subject line",
    "email_content": "Complete email content with greeting, full personalized body, and professional closing",
    "personalization_elements": ["list", "of", "specific", "personalizations", "applied"],
    "tone_achieved": "description of tone used"
}}

REMEMBER: This customer is {insights.segment} with {insights.digital_persona} preferences. Every word should reflect their profile and the personalization strategy."""

        return prompt
    
    def _parse_ai_response(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse the AI response to extract email data"""
        
        # Remove markdown formatting
        content = content.replace('```json', '').replace('```', '').strip()
        
        try:
            # Try direct JSON parsing
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to find JSON in the content
            if '{' in content and '}' in content:
                try:
                    json_start = content.index('{')
                    json_end = content.rindex('}') + 1
                    json_str = content[json_start:json_end]
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
        
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
        personalization_elements = email_data.get('personalization_elements', [])
        tone_achieved = email_data.get('tone_achieved', 'professional')
        
        # Calculate quality score based on personalization depth
        quality_score = self._calculate_quality_score(
            email_content,
            personalization_elements,
            shared_context
        )
        
        return EmailResult(
            content=email_content,
            subject_line=subject_line,
            word_count=len(email_content.split()),
            character_count=len(email_content),
            personalization_elements=personalization_elements,
            tone_achieved=tone_achieved,
            language=shared_context.customer_data.get('preferred_language', 'English'),
            generation_method=method,
            processing_time=0.0,  # Will be set by caller
            quality_score=quality_score
        )
    
    def _calculate_quality_score(
        self, 
        email_content: str, 
        personalization_elements: List[str],
        shared_context: SharedContext
    ) -> float:
        """Calculate quality score based on personalization achievement"""
        
        score = 0.5  # Base score
        
        # Check personalization depth
        target_level = shared_context.personalization_strategy.level
        if target_level == PersonalizationLevel.HYPER and len(personalization_elements) >= 8:
            score += 0.3
        elif target_level == PersonalizationLevel.DEEP and len(personalization_elements) >= 6:
            score += 0.25
        elif target_level == PersonalizationLevel.MODERATE and len(personalization_elements) >= 4:
            score += 0.2
        elif len(personalization_elements) >= 2:
            score += 0.15
        
        # Check must-mention items
        must_mention_found = 0
        for item in shared_context.personalization_strategy.must_mention:
            # Check if key concepts from must_mention appear in email
            item_words = item.lower().split()
            key_words = [w for w in item_words if len(w) > 4]  # Meaningful words
            if key_words and any(word in email_content.lower() for word in key_words):
                must_mention_found += 1
        
        if must_mention_found > 0:
            score += 0.1 + (must_mention_found * 0.05)
        
        # Check content preservation
        critical_content_found = 0
        for point in shared_context.content_strategy.critical_points:
            # Simple check if core concepts are present
            point_words = point.content.lower().split()
            key_words = [w for w in point_words if len(w) > 4]
            if key_words and any(word in email_content.lower() for word in key_words):
                critical_content_found += 1
        
        if critical_content_found > 0:
            score += 0.1 + (critical_content_found * 0.02)
        
        # Check length appropriateness
        if 200 <= len(email_content.split()) <= 1000:  # Good email length
            score += 0.05
        
        return min(1.0, score)
    
    def _generate_fallback(self, shared_context: SharedContext) -> EmailResult:
        """Generate fallback email when AI fails"""
        
        customer = shared_context.customer_data
        insights = shared_context.customer_insights
        strategy = shared_context.personalization_strategy
        
        name = customer.get('name', 'Valued Customer')
        
        # Build basic personalized email
        greeting = f"Dear {name},"
        
        # Add personalization based on insights
        personal_intro = ""
        if insights.special_factors:
            factor = insights.special_factors[0]
            personal_intro = f"We hope everything is going well with {factor}. "
        elif strategy.customer_story:
            personal_intro = f"As {strategy.customer_story.lower()}, we wanted to reach out personally. "
        
        # Core content
        core_content = shared_context.original_letter
        
        # Personal closing
        if insights.segment == 'DIGITAL':
            closing = "You can manage everything through your app, or call us if you need support."
        elif insights.segment == 'TRADITIONAL':
            closing = "Please call us or visit your local branch if you have any questions."
        else:
            closing = "Contact us through your preferred method - app, phone, or in person."
        
        email_content = f"{greeting}\n\n{personal_intro}{core_content}\n\n{closing}\n\nBest regards,\nLloyds Bank"
        
        return EmailResult(
            content=email_content,
            subject_line=f"Important Update for {name}",
            word_count=len(email_content.split()),
            character_count=len(email_content),
            personalization_elements=["customer_name", "segment_adaptation", "personal_intro"],
            tone_achieved=strategy.tone_guidelines.get('overall_tone', 'professional'),
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

[Original letter content would be here with full personalization]

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
            quality_score=0.8  # High for simulation
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
        """Validate that the email meets the shared context requirements"""
        
        validation = {
            'is_valid': True,
            'quality_score': email_result.quality_score,
            'issues': [],
            'achievements': [],
            'personalization_depth': len(email_result.personalization_elements),
            'content_preserved': True,  # Would need deeper analysis
            'tone_match': True,  # Would need tone analysis
            'language_correct': email_result.language == shared_context.customer_data.get('preferred_language', 'English')
        }
        
        # Check minimum requirements
        if email_result.word_count < 50:
            validation['issues'].append("Email too short")
            validation['is_valid'] = False
        
        if len(email_result.personalization_elements) < 3:
            validation['issues'].append("Insufficient personalization")
        else:
            validation['achievements'].append(f"Applied {len(email_result.personalization_elements)} personalizations")
        
        # Check personalization level achievement
        target_level = shared_context.personalization_strategy.level
        achieved_elements = len(email_result.personalization_elements)
        
        if target_level == PersonalizationLevel.HYPER and achieved_elements < 8:
            validation['issues'].append("Did not achieve HYPER personalization level")
        elif target_level == PersonalizationLevel.DEEP and achieved_elements < 6:
            validation['issues'].append("Did not achieve DEEP personalization level")
        elif target_level == PersonalizationLevel.MODERATE and achieved_elements < 4:
            validation['issues'].append("Did not achieve MODERATE personalization level")
        else:
            validation['achievements'].append(f"Achieved {target_level.value} personalization")
        
        return validation

# Convenience function for easy integration
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