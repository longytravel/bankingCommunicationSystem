"""
Email Refiner - Intelligent Email Refinement Engine
Removes hallucinations while enhancing personalization through smart inference
Uses Claude Sonnet 4 for more powerful analysis
"""

import os
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import anthropic
from dotenv import load_dotenv

load_dotenv()

# Import necessary types
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.core.shared_brain import SharedContext
    from src.core.smart_email_generator import EmailResult
    from src.core.hallucination_detector import HallucinationReport, HallucinationFinding, SeverityLevel
    IMPORTS_AVAILABLE = True
except ImportError as e:
    IMPORTS_AVAILABLE = False
    print(f"⚠️ Import error: {e}")

class InferenceConfidence(Enum):
    """Confidence levels for demographic inferences"""
    HIGH = "high"       # Very safe, widely applicable
    MEDIUM = "medium"   # Reasonable, mostly safe
    LOW = "low"        # Possible but needs care

@dataclass
class InferenceRule:
    """A single inference that can be made"""
    demographic: str              # student, young_family, retiree, etc.
    inference: str               # The actual inference text
    confidence: InferenceConfidence
    category: str                # financial, lifestyle, behavioral, emotional
    
@dataclass
class RefinementMetrics:
    """Metrics to track refinement success"""
    hallucinations_removed: int
    inferences_added: int
    personalization_score_before: float
    personalization_score_after: float
    quality_score_before: float
    quality_score_after: float
    word_count_before: int
    word_count_after: int
    processing_time: float
    
@dataclass
class RefinedEmailResult:
    """Result from email refinement"""
    original_email: EmailResult
    refined_content: str
    refined_subject: str
    hallucinations_addressed: List[Dict[str, Any]]
    inferences_applied: List[InferenceRule]
    personalization_elements: List[str]
    metrics: RefinementMetrics
    confidence_score: float
    generation_method: str
    language: str

class EmailRefiner:
    """
    Intelligent Email Refinement Engine
    Removes hallucinations while enhancing personalization through demographic inference
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Claude Sonnet 4"""
        self.api_key = api_key or os.getenv('CLAUDE_API_KEY')
        self.client = None
        
        if self.api_key:
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
                # Updated to Claude Haiku 4.5 - Latest model
                self.model = "claude-haiku-4-5-20251001"
                print("✅ Email Refiner initialized with Claude Haiku 4.5")
            except Exception as e:
                print(f"⚠️ Failed to initialize Claude client: {e}")
                self.client = None
        else:
            print("⚠️ Email Refiner running without AI")
    
    def refine_email(
        self,
        original_email: EmailResult,
        hallucination_report: HallucinationReport,
        shared_context: SharedContext
    ) -> RefinedEmailResult:
        """
        Main refinement method - removes hallucinations and enhances personalization
        
        Args:
            original_email: The original generated email
            hallucination_report: Report of detected hallucinations
            shared_context: Complete context from SharedBrain
            
        Returns:
            RefinedEmailResult with improved email
        """
        start_time = datetime.now()
        
        print(f"🔧 Starting email refinement for {shared_context.customer_data.get('name')}...")
        print(f"   Hallucinations to fix: {hallucination_report.total_hallucinations}")
        print(f"   Original quality: {original_email.quality_score:.0%}")
        
        # Extract email-specific hallucinations
        email_hallucinations = [
            f for f in hallucination_report.findings 
            if f.channel == 'email'
        ]
        
        if not email_hallucinations and original_email.quality_score > 0.85:
            print("   ✅ Email already excellent, skipping refinement")
            return self._create_unchanged_result(original_email, shared_context, start_time)
        
        # Perform deep customer analysis for better inferences
        safe_inferences = self._generate_safe_inferences(shared_context)
        
        # Generate refined email
        if self.client:
            refined_result = self._refine_with_ai(
                original_email,
                email_hallucinations,
                safe_inferences,
                shared_context
            )
        else:
            refined_result = self._refine_with_rules(
                original_email,
                email_hallucinations,
                safe_inferences,
                shared_context
            )
        
        # Calculate metrics
        processing_time = (datetime.now() - start_time).total_seconds()
        refined_result.metrics.processing_time = processing_time
        
        print(f"✅ Refinement complete in {processing_time:.2f}s")
        print(f"   Hallucinations removed: {refined_result.metrics.hallucinations_removed}")
        print(f"   Inferences added: {refined_result.metrics.inferences_added}")
        print(f"   Quality: {refined_result.metrics.quality_score_before:.0%} → {refined_result.metrics.quality_score_after:.0%}")
        
        return refined_result
    
    def _generate_safe_inferences(self, shared_context: SharedContext) -> List[InferenceRule]:
        """
        Generate safe demographic-based inferences
        NOT hardcoded - uses AI to reason about the customer
        """
        
        customer = shared_context.customer_data
        insights = shared_context.customer_insights
        
        if not self.client:
            return self._get_fallback_inferences(insights)
        
        # Build inference generation prompt
        prompt = f"""You are analyzing a customer to make SAFE demographic inferences for personalization.

CUSTOMER DATA:
- Age: {customer.get('age', 'unknown')}
- Life Stage: {insights.life_stage}
- Financial Profile: {insights.financial_profile}
- Digital Persona: {insights.digital_persona}
- Recent Life Events: {customer.get('recent_life_events', 'none')}
- Employment: {customer.get('employment_status', 'unknown')}
- Account Balance: £{customer.get('account_balance', 0):,}
- Years with Bank: {customer.get('years_with_bank', 0)}

Generate SAFE inferences that are:
1. Based on demographic patterns, not specific facts
2. Broadly applicable to people in this situation
3. Respectful and not presumptuous
4. Valuable for personalization

Return as JSON array:
[
  {{
    "demographic": "life_stage_category",
    "inference": "inference text that could be used",
    "confidence": "high|medium|low",
    "category": "financial|lifestyle|behavioral|emotional",
    "reasoning": "why this is safe and appropriate"
  }}
]

Guidelines:
- HIGH confidence: Nearly universal for this demographic
- MEDIUM confidence: Common but not universal
- LOW confidence: Possible but use carefully

Generate 3-5 inferences:"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.4,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text.strip()
            return self._parse_inferences(content)
            
        except Exception as e:
            print(f"   ⚠️ Inference generation failed: {e}")
            return self._get_fallback_inferences(insights)
    
    def _refine_with_ai(
        self,
        original_email: EmailResult,
        hallucinations: List[HallucinationFinding],
        safe_inferences: List[InferenceRule],
        shared_context: SharedContext
    ) -> RefinedEmailResult:
        """Use AI to intelligently refine the email"""
        
        # Build the refinement prompt
        prompt = self._build_refinement_prompt(
            original_email.content,
            original_email.subject_line,
            hallucinations,
            safe_inferences,
            shared_context
        )
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=3000,
                temperature=0.5,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text.strip()
            refined_data = self._parse_refined_email(content)
            
            if refined_data:
                return self._create_refined_result(
                    original_email,
                    refined_data,
                    hallucinations,
                    safe_inferences,
                    shared_context,
                    "ai_refinement"
                )
            
        except Exception as e:
            print(f"   ⚠️ AI refinement failed: {e}")
        
        # Fallback to rule-based refinement
        return self._refine_with_rules(
            original_email,
            hallucinations,
            safe_inferences,
            shared_context
        )
    
    def _build_refinement_prompt(
        self,
        original_content: str,
        original_subject: str,
        hallucinations: List[HallucinationFinding],
        safe_inferences: List[InferenceRule],
        shared_context: SharedContext
    ) -> str:
        """Build the AI prompt for refinement"""
        
        # Format hallucinations for the prompt
        hallucination_list = []
        for h in hallucinations:
            hallucination_list.append(f"- Remove: '{h.text}' | Reason: {h.explanation} | Suggested: {h.suggested_fix}")
        
        # Format inferences for the prompt
        inference_list = []
        for inf in safe_inferences[:5]:  # Limit to top 5
            if inf.confidence in [InferenceConfidence.HIGH, InferenceConfidence.MEDIUM]:
                inference_list.append(f"- {inf.inference} (confidence: {inf.confidence.value})")
        
        customer = shared_context.customer_data
        insights = shared_context.customer_insights
        
        prompt = f"""You are refining an email to remove hallucinations while ENHANCING personalization.

ORIGINAL EMAIL:
Subject: {original_subject}
Content: {original_content}

ISSUES TO FIX (hallucinations to remove):
{chr(10).join(hallucination_list) if hallucination_list else 'None identified'}

SAFE INFERENCES YOU CAN ADD (use these EXACTLY or very close to exactly):
{chr(10).join(inference_list) if inference_list else 'None available'}

CUSTOMER CONTEXT:
- Name: {customer.get('name')}
- Life Stage: {insights.life_stage}
- Segment: {insights.segment}
- Financial Profile: {insights.financial_profile}
- Communication Style: {insights.communication_style}

REFINEMENT RULES:
1. REMOVE all hallucinated content (specific names, dates, facts not in evidence)
2. ADD the safe inferences listed above - use them verbatim or with minimal rewording
3. IMPORTANT: Include at least 2-3 of the safe inferences in the refined content
4. The inferences should flow naturally but keep their key phrases intact
5. MAINTAIN OR ENHANCE personalization level
6. PRESERVE all critical information from the original
7. KEEP the same friendly but professional tone
8. DO NOT introduce new specific facts not in evidence

Generate the refined email as JSON:
{{
  "refined_subject": "improved subject line",
  "refined_content": "complete refined email content with inferences included",
  "changes_made": ["list of specific changes"],
  "inferences_added": ["exact text of inferences you included"],
  "personalization_elements": ["all personalization elements in refined version"]
}}

Remember: Actually INCLUDE the safe inferences in your refined content, don't just mention them."""

        return prompt
    
    def _parse_refined_email(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse the AI response"""
        content = content.replace('```json', '').replace('```', '').strip()
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            if '{' in content and '}' in content:
                try:
                    start = content.index('{')
                    end = content.rindex('}') + 1
                    return json.loads(content[start:end])
                except:
                    pass
        return None
    
    def _create_refined_result(
        self,
        original_email: EmailResult,
        refined_data: Dict[str, Any],
        hallucinations: List[HallucinationFinding],
        safe_inferences: List[InferenceRule],
        shared_context: SharedContext,
        method: str
    ) -> RefinedEmailResult:
        """Create the refined result object"""
        
        refined_content = refined_data.get('refined_content', original_email.content)
        refined_subject = refined_data.get('refined_subject', original_email.subject_line)
        
        # Simple approach: Check which inferences actually appear in the refined content
        # We look for key phrases from each inference
        actually_applied_inferences = []
        
        for inf in safe_inferences:
            # Check if key parts of the inference appear in the refined content
            # Split inference into meaningful phrases (3+ words)
            inference_lower = inf.inference.lower()
            content_lower = refined_content.lower()
            
            # Extract key phrases (3-4 word chunks) from the inference
            words = inf.inference.split()
            found = False
            
            # Check for the whole inference first
            if inference_lower in content_lower:
                found = True
            else:
                # Check for significant chunks (at least 3 consecutive words)
                for i in range(len(words) - 2):
                    chunk = ' '.join(words[i:i+3]).lower()
                    # Skip common phrases
                    if chunk not in ['we value your', 'we understand that', 'you may be']:
                        if chunk in content_lower:
                            found = True
                            break
            
            if found:
                actually_applied_inferences.append(inf)
        
        # IMPORTANT: Both the count and the list come from the same source
        final_inferences_count = len(actually_applied_inferences)
        
        # If we found no inferences but AI claims it added some, 
        # it means they were paraphrased too much to detect
        # In this case, we report 0 to be consistent
        
        # Calculate metrics
        metrics = RefinementMetrics(
            hallucinations_removed=len(hallucinations),
            inferences_added=final_inferences_count,  # This will match the list length
            personalization_score_before=self._calculate_personalization_score(
                original_email.content,
                original_email.personalization_elements
            ),
            personalization_score_after=self._calculate_personalization_score(
                refined_content,
                refined_data.get('personalization_elements', [])
            ),
            quality_score_before=original_email.quality_score,
            quality_score_after=self._calculate_quality_score(
                refined_content,
                refined_data.get('personalization_elements', []),
                len(hallucinations) == 0
            ),
            word_count_before=original_email.word_count,
            word_count_after=len(refined_content.split()),
            processing_time=0.0
        )
        
        # Build hallucinations addressed list
        hallucinations_addressed = [
            {
                'text': h.text,
                'category': h.category.value,
                'fix_applied': h.suggested_fix
            }
            for h in hallucinations
        ]
        
        print(f"   DEBUG: Found {final_inferences_count} verifiable inferences in refined content")
        if final_inferences_count == 0 and refined_data.get('inferences_added'):
            print(f"   NOTE: AI reported adding inferences but they were too paraphrased to verify")
        
        return RefinedEmailResult(
            original_email=original_email,
            refined_content=refined_content,
            refined_subject=refined_subject,
            hallucinations_addressed=hallucinations_addressed,
            inferences_applied=actually_applied_inferences,  # This list determines the count
            personalization_elements=refined_data.get('personalization_elements', []),
            metrics=metrics,
            confidence_score=metrics.quality_score_after,
            generation_method=method,
            language=shared_context.customer_data.get('preferred_language', 'English')
        )
    
    def _calculate_personalization_score(self, content: str, elements: List[str]) -> float:
        """Calculate personalization score (0-1)"""
        base_score = 0.3
        
        # Points for personalization elements
        element_score = min(0.4, len(elements) * 0.05)
        
        # Points for personal pronouns
        personal_pronouns = ['you', 'your', "you're", "you've", "you'll"]
        pronoun_count = sum(content.lower().count(p) for p in personal_pronouns)
        pronoun_score = min(0.2, pronoun_count * 0.01)
        
        # Points for emotional/connecting language
        connecting_words = ['understand', 'appreciate', 'value', 'important', 'matter']
        connection_score = min(0.1, sum(1 for w in connecting_words if w in content.lower()) * 0.02)
        
        return min(1.0, base_score + element_score + pronoun_score + connection_score)
    
    def _calculate_quality_score(
        self, 
        content: str, 
        personalization_elements: List[str],
        hallucination_free: bool
    ) -> float:
        """Calculate overall quality score"""
        base_score = 0.5
        
        # Bonus for no hallucinations
        if hallucination_free:
            base_score += 0.2
        
        # Personalization quality
        if len(personalization_elements) >= 5:
            base_score += 0.2
        elif len(personalization_elements) >= 3:
            base_score += 0.1
        
        # Content completeness (word count)
        word_count = len(content.split())
        if 200 <= word_count <= 500:
            base_score += 0.1
        
        return min(1.0, base_score)
    
    def _refine_with_rules(
        self,
        original_email: EmailResult,
        hallucinations: List[HallucinationFinding],
        safe_inferences: List[InferenceRule],
        shared_context: SharedContext
    ) -> RefinedEmailResult:
        """Fallback rule-based refinement"""
        
        refined_content = original_email.content
        
        # Remove hallucinations
        for h in hallucinations:
            refined_content = refined_content.replace(h.text, h.suggested_fix)
        
        # Track which inferences we actually add
        added_inferences = []
        
        # Add a safe inference if possible
        if safe_inferences and len(safe_inferences) > 0:
            inference = safe_inferences[0]
            # Add inference after greeting
            if "Dear" in refined_content or "Hi" in refined_content or "Hello" in refined_content:
                lines = refined_content.split('\n')
                if len(lines) > 1:
                    lines.insert(2, f"\n{inference.inference}\n")
                    refined_content = '\n'.join(lines)
                    added_inferences.append(inference)  # Track that we added it
        
        # Use the actual count of added inferences
        actual_inferences_count = len(added_inferences)
        
        metrics = RefinementMetrics(
            hallucinations_removed=len(hallucinations),
            inferences_added=actual_inferences_count,  # Use actual count
            personalization_score_before=self._calculate_personalization_score(
                original_email.content,
                original_email.personalization_elements
            ),
            personalization_score_after=self._calculate_personalization_score(
                refined_content,
                original_email.personalization_elements
            ),
            quality_score_before=original_email.quality_score,
            quality_score_after=original_email.quality_score * 0.9,  # Slight decrease for fallback
            word_count_before=original_email.word_count,
            word_count_after=len(refined_content.split()),
            processing_time=0.0
        )
        
        return RefinedEmailResult(
            original_email=original_email,
            refined_content=refined_content,
            refined_subject=original_email.subject_line,
            hallucinations_addressed=[{
                'text': h.text,
                'category': h.category.value,
                'fix_applied': h.suggested_fix
            } for h in hallucinations],
            inferences_applied=added_inferences,  # Use the actual list
            personalization_elements=original_email.personalization_elements,
            metrics=metrics,
            confidence_score=0.7,
            generation_method="rule_based_refinement",
            language=shared_context.customer_data.get('preferred_language', 'English')
        )
    
    def _parse_inferences(self, content: str) -> List[InferenceRule]:
        """Parse AI-generated inferences"""
        try:
            # Clean and parse JSON
            if '[' in content and ']' in content:
                start = content.index('[')
                end = content.rindex(']') + 1
                json_str = content[start:end]
                data = json.loads(json_str)
                
                inferences = []
                for item in data:
                    inferences.append(InferenceRule(
                        demographic=item.get('demographic', 'general'),
                        inference=item.get('inference', ''),
                        confidence=InferenceConfidence(item.get('confidence', 'medium')),
                        category=item.get('category', 'general')
                    ))
                return inferences
        except:
            pass
        
        return self._get_fallback_inferences(None)
    
    def _get_fallback_inferences(self, insights) -> List[InferenceRule]:
        """Get basic fallback inferences"""
        inferences = []
        
        if insights:
            if insights.life_stage == 'student':
                inferences.append(InferenceRule(
                    demographic='student',
                    inference='Managing finances during your studies',
                    confidence=InferenceConfidence.HIGH,
                    category='lifestyle'
                ))
            elif insights.life_stage == 'young_family':
                inferences.append(InferenceRule(
                    demographic='young_family',
                    inference='Planning for your family\'s financial future',
                    confidence=InferenceConfidence.HIGH,
                    category='financial'
                ))
            elif insights.life_stage == 'retirement':
                inferences.append(InferenceRule(
                    demographic='retiree',
                    inference='Making the most of your retirement',
                    confidence=InferenceConfidence.HIGH,
                    category='lifestyle'
                ))
        
        # Add a safe general inference
        inferences.append(InferenceRule(
            demographic='general',
            inference='We value your relationship with Lloyds',
            confidence=InferenceConfidence.HIGH,
            category='emotional'
        ))
        
        return inferences
    
    def _create_unchanged_result(
        self,
        original_email: EmailResult,
        shared_context: SharedContext,
        start_time: datetime
    ) -> RefinedEmailResult:
        """Create result when no refinement needed"""
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        metrics = RefinementMetrics(
            hallucinations_removed=0,
            inferences_added=0,
            personalization_score_before=self._calculate_personalization_score(
                original_email.content,
                original_email.personalization_elements
            ),
            personalization_score_after=self._calculate_personalization_score(
                original_email.content,
                original_email.personalization_elements
            ),
            quality_score_before=original_email.quality_score,
            quality_score_after=original_email.quality_score,
            word_count_before=original_email.word_count,
            word_count_after=original_email.word_count,
            processing_time=processing_time
        )
        
        return RefinedEmailResult(
            original_email=original_email,
            refined_content=original_email.content,
            refined_subject=original_email.subject_line,
            hallucinations_addressed=[],
            inferences_applied=[],
            personalization_elements=original_email.personalization_elements,
            metrics=metrics,
            confidence_score=original_email.quality_score,
            generation_method="no_refinement_needed",
            language=shared_context.customer_data.get('preferred_language', 'English')
        )

# Convenience function
def refine_email(
    original_email: EmailResult,
    hallucination_report: HallucinationReport,
    shared_context: SharedContext,
    api_key: Optional[str] = None
) -> RefinedEmailResult:
    """
    Convenience function to refine an email
    
    Args:
        original_email: The original generated email
        hallucination_report: Report of detected hallucinations
        shared_context: Complete context from SharedBrain
        api_key: Optional API key
        
    Returns:
        RefinedEmailResult with improved email
    """
    refiner = EmailRefiner(api_key=api_key)
    return refiner.refine_email(original_email, hallucination_report, shared_context)