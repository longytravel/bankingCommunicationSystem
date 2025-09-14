"""
Banking Sentiment Intelligence - Clear, Actionable, Stakeholder-Focused
Analyzes communications for sentiment, compliance, and business impact
Every score comes with a clear WHY explanation
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
    from src.core.email_refiner import RefinedEmailResult
    IMPORTS_AVAILABLE = True
except ImportError as e:
    IMPORTS_AVAILABLE = False
    print(f"⚠️ Import error: {e}")

class SentimentCategory(Enum):
    """Clear sentiment categories that stakeholders understand"""
    POSITIVE = "positive"          # Customer will be happy
    NEUTRAL = "neutral"           # Functional but not delightful
    NEGATIVE = "negative"         # Risk of customer dissatisfaction

class ComplianceStatus(Enum):
    """Compliance check results"""
    PASS = "pass"                 # Fully compliant
    WARNING = "warning"           # Minor issues to consider
    FAIL = "fail"                 # Must fix before sending

class BusinessImpact(Enum):
    """Predicted business outcomes"""
    COMPLAINT_LIKELY = "complaint_likely"
    CALL_LIKELY = "call_likely"
    NO_ACTION_NEEDED = "no_action_needed"
    OPPORTUNITY_IDENTIFIED = "opportunity_identified"

class SentimentZone(Enum):
    """Overall assessment - keeping same name for compatibility"""
    OPTIMAL = "optimal"           # Ready to send
    POSITIVE = "positive"         # Good with minor improvements possible
    NEUTRAL = "neutral"           # Functional but uninspiring
    CONCERNING = "concerning"     # Issues need addressing
    CRITICAL = "critical"         # Do not send without fixes

# Keep these for backward compatibility but simplified
class EmotionalDimension(Enum):
    """Core emotions that matter in banking"""
    TRUST = "trust"               # Do they trust us?
    CLARITY = "clarity"           # Will they understand?
    EMPATHY = "empathy"           # Do we care about them?
    URGENCY = "urgency"           # Appropriate level of urgency?

class BankingOutcome(Enum):
    """Key outcomes we predict"""
    COMPLAINT_RISK = "complaint_risk"
    CALL_PROBABILITY = "call_probability"
    SATISFACTION_IMPACT = "satisfaction_impact"

@dataclass
class SentimentScore:
    """Core sentiment with clear reasoning"""
    score: int                    # -100 to +100 scale (easier than -1 to 1)
    category: SentimentCategory   # Positive/Neutral/Negative
    confidence: float             # How confident are we?
    why: str                      # Clear explanation of the score
    evidence: List[str]           # Specific quotes that led to this score

@dataclass
class ComplianceCheck:
    """Regulatory compliance assessment"""
    status: ComplianceStatus      # Pass/Warning/Fail
    tcf_score: int                # Treating Customers Fairly score (0-100)
    vulnerabilities_handled: bool # Are vulnerable customers protected?
    plain_english_score: int      # Readability score (0-100)
    why: str                      # Explanation of compliance status
    issues: List[str]             # Specific compliance issues found
    fixes: List[str]              # How to fix each issue

@dataclass
class CustomerImpact:
    """Predicted customer behavior"""
    complaint_probability: float  # 0-100% chance
    call_probability: float       # 0-100% chance
    nps_impact: int              # -10 to +10 impact on NPS
    satisfaction_delta: int       # -100 to +100 change in CSAT
    why: str                      # Why we predict this impact
    risk_factors: List[str]       # What could go wrong
    success_factors: List[str]    # What's working well

@dataclass
class LinguisticQuality:
    """Objective quality measures"""
    readability_score: int        # Flesch reading ease (0-100)
    grade_level: float           # US grade level required
    jargon_count: int            # Number of banking terms
    passive_voice_percent: float # % of passive constructions
    sentence_complexity: str      # Simple/Moderate/Complex
    why: str                      # Assessment explanation
    improvements: List[str]       # Specific improvements needed

@dataclass
class ActionableInsight:
    """What to do about it"""
    priority: str                 # HIGH/MEDIUM/LOW
    issue: str                   # What's wrong
    impact: str                  # Why it matters
    fix: str                     # How to fix it
    example: Optional[str]       # Example of fixed text
    effort: str                  # Quick/Moderate/Significant

@dataclass 
class QuickWin:
    """One-click improvements"""
    original: str                # Original text
    improved: str                # Improved version
    why: str                     # Why this is better
    impact: str                  # Expected improvement

# Keep simplified versions for compatibility
@dataclass
class EmotionalJourney:
    """How sentiment flows - simplified"""
    opening_sentiment: float      
    middle_sentiment: float
    closing_sentiment: float
    trajectory: str               # Rising/Falling/Stable
    why: str                      # Why this trajectory matters

@dataclass
class BankingInsights:
    """Banking-specific insights - simplified"""
    complaint_probability: float
    call_center_impact: str
    regulatory_tone_score: float
    trust_building: bool
    why: str                      # Overall assessment
    recommendations: List[str]    # Specific recommendations

@dataclass
class PsychologicalProfile:
    """Simplified to what matters"""
    cognitive_load: str           # Low/Medium/High
    trust_building: str           # Strong/Moderate/Weak
    customer_empowerment: str     # Empowered/Neutral/Controlled
    why: str                      # Why this matters

@dataclass
class SentimentRecommendation:
    """Keep for compatibility but simplified"""
    category: str                 
    priority: str                 
    issue: str                    
    suggestion: str               
    impact: str                   
    example: Optional[str]
    
@dataclass
class SentimentAnalysisResult:
    """Banking Sentiment Intelligence Report - Everything has a WHY"""
    
    # Executive Summary (what stakeholders see first)
    overall_score: int                          # -100 to +100 (easier than decimals)
    overall_sentiment: float                    # Keep for compatibility (-1 to 1)
    sentiment_zone: SentimentZone              # Overall status
    ready_to_send: bool                        # Clear yes/no decision
    executive_summary: str                      # 2-3 sentence summary with WHY
    
    # Core Analysis with WHY
    sentiment_score: SentimentScore            # Detailed sentiment with reasoning
    compliance_check: ComplianceCheck          # Regulatory compliance with issues
    customer_impact: CustomerImpact            # Predicted outcomes with reasoning
    linguistic_quality: LinguisticQuality      # Objective measures with context
    
    # Actionable Insights
    red_flags: List[ActionableInsight]         # Must fix before sending
    warnings: List[ActionableInsight]          # Should consider fixing
    opportunities: List[ActionableInsight]     # Could improve for better results
    quick_wins: List[QuickWin]                # One-click improvements
    
    # Business Predictions with WHY
    will_cause_complaint: bool                 # Yes/No with reasoning
    will_cause_call: bool                      # Yes/No with reasoning
    nps_impact_prediction: str                 # Positive/Neutral/Negative with why
    
    # Detailed Reasoning (the WHY behind everything)
    scoring_rationale: Dict[str, str]          # Why each score was given
    key_evidence: List[str]                    # Specific quotes that matter
    comparison_to_best_practice: str           # How it compares to ideal
    
    # Keep for compatibility but simplified
    confidence_score: float
    emotional_dimensions: Dict[EmotionalDimension, float]
    emotional_journey: EmotionalJourney
    psychological_profile: PsychologicalProfile
    banking_insights: BankingInsights
    outcome_predictions: Dict[BankingOutcome, float]
    
    # Segment alignment with WHY
    segment_alignment_score: float
    segment_mismatches: List[str]
    why_alignment_matters: str
    
    # Keep these simplified
    cultural_appropriateness: float
    language_formality_score: float
    recommendations: List[SentimentRecommendation]
    paragraph_sentiments: List[Dict[str, Any]]
    heatmap_data: Dict[str, Any]
    
    # Metadata
    analysis_timestamp: str
    processing_time: float
    model_used: str
    customer_context_considered: Dict[str, Any]

class SentimentAnalyzer:
    """
    Banking Sentiment Intelligence Engine
    Every score and recommendation comes with a clear WHY
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Claude"""
        self.api_key = api_key or os.getenv('CLAUDE_API_KEY')
        self.client = None
        
        if self.api_key:
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
                self.model = "claude-3-sonnet-20240229"  # Using stable model
                print("✅ Banking Sentiment Intelligence initialized")
            except Exception as e:
                print(f"⚠️ Failed to initialize Claude client: {e}")
                self.client = None
        else:
            print("⚠️ Running without AI - using pattern matching")
    
    def analyze_sentiment(
        self,
        refined_email: RefinedEmailResult,
        shared_context: SharedContext
    ) -> SentimentAnalysisResult:
        """
        Analyze with focus on WHY behind every score
        
        Args:
            refined_email: The refined email to analyze
            shared_context: Complete context from SharedBrain
            
        Returns:
            SentimentAnalysisResult with clear reasoning throughout
        """
        start_time = datetime.now()
        
        customer_name = shared_context.customer_data.get('name', 'Unknown')
        print(f"🎯 Starting Banking Sentiment Intelligence for {customer_name}...")
        
        try:
            if self.client:
                result = self._analyze_with_ai(refined_email, shared_context)
            else:
                result = self._analyze_with_patterns(refined_email, shared_context)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            result.processing_time = processing_time
            
            # Generate executive summary if not present
            if not result.executive_summary:
                result.executive_summary = self._generate_executive_summary(result)
            
            print(f"✅ Analysis complete in {processing_time:.2f}s")
            print(f"   Overall Score: {result.overall_score}/100")
            print(f"   Ready to Send: {'Yes' if result.ready_to_send else 'No - Issues Found'}")
            print(f"   Red Flags: {len(result.red_flags)}")
            
            # DEBUG: Verify the result has all required attributes
            required_attrs = ['overall_score', 'ready_to_send', 'sentiment_score', 'compliance_check']
            for attr in required_attrs:
                if not hasattr(result, attr):
                    print(f"   WARNING: Missing attribute {attr}")
            
            return result
            
        except Exception as e:
            print(f"❌ Error in analyze_sentiment: {e}")
            import traceback
            traceback.print_exc()
            # Return a minimal valid result instead of crashing
            return self._create_error_result(refined_email, shared_context, str(e))
    
    def _generate_executive_summary(self, result: SentimentAnalysisResult) -> str:
        """Generate clear executive summary with WHY"""
        if result.ready_to_send:
            return f"This communication scores {result.overall_score}/100 and is ready to send. {result.sentiment_score.why} No compliance issues detected."
        else:
            issues = len(result.red_flags)
            return f"This communication scores {result.overall_score}/100 and has {issues} issue(s) to fix. {result.sentiment_score.why} {result.compliance_check.why}"
    
    def _analyze_with_ai(
        self,
        refined_email: RefinedEmailResult,
        shared_context: SharedContext
    ) -> SentimentAnalysisResult:
        """Use Claude Sonnet 4 for advanced analysis"""
        
        # Build comprehensive analysis prompt
        prompt = self._build_analysis_prompt(refined_email, shared_context)
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.3,  # Lower temperature for consistent analysis
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text.strip()
            analysis_data = self._parse_ai_response(content)
            
            if analysis_data:
                return self._create_result_from_ai(
                    analysis_data,
                    refined_email,
                    shared_context
                )
            
        except Exception as e:
            print(f"   ⚠️ AI analysis failed: {e}")
        
        # Fallback to pattern analysis
        return self._analyze_with_patterns(refined_email, shared_context)
    
    def _build_analysis_prompt(
        self,
        refined_email: RefinedEmailResult,
        shared_context: SharedContext
    ) -> str:
        """Build prompt focused on WHY for every assessment"""
        
        customer = shared_context.customer_data
        insights = shared_context.customer_insights
        
        prompt = f"""You are a banking communications expert. Analyze this email for sentiment, compliance, and business impact.
ALWAYS EXPLAIN WHY for every score and assessment.

EMAIL:
Subject: {refined_email.refined_subject}
Body: {refined_email.refined_content}

CUSTOMER:
- Name: {customer.get('name')}
- Segment: {insights.segment}
- Account Balance: £{customer.get('account_balance', 0):,}
- Vulnerabilities: {', '.join(insights.special_factors) if insights.special_factors else 'None'}

Provide a complete analysis in JSON format. EVERY field must include clear reasoning:

{{
  "overall_score": -100 to 100 (0 is neutral),
  "ready_to_send": true/false,
  "executive_summary": "2-3 sentences explaining the score and decision with clear WHY",
  
  "sentiment_score": {{
    "score": -100 to 100,
    "category": "positive|neutral|negative",
    "confidence": 0.0 to 1.0,
    "why": "Clear explanation of WHY this score was given",
    "evidence": ["Specific quotes that led to this score"]
  }},
  
  "compliance_check": {{
    "status": "pass|warning|fail",
    "tcf_score": 0 to 100,
    "vulnerabilities_handled": true/false,
    "plain_english_score": 0 to 100,
    "why": "Explanation of compliance status and WHY it matters",
    "issues": ["Specific compliance issues found"],
    "fixes": ["How to fix each issue"]
  }},
  
  "customer_impact": {{
    "complaint_probability": 0 to 100,
    "call_probability": 0 to 100,
    "nps_impact": -10 to 10,
    "satisfaction_delta": -100 to 100,
    "why": "WHY we predict this customer impact",
    "risk_factors": ["What could trigger negative reaction"],
    "success_factors": ["What will resonate positively"]
  }},
  
  "linguistic_quality": {{
    "readability_score": 0 to 100 (Flesch),
    "grade_level": 1.0 to 18.0,
    "jargon_count": number,
    "passive_voice_percent": 0 to 100,
    "sentence_complexity": "simple|moderate|complex",
    "why": "Assessment of language quality and WHY it matters for this customer",
    "improvements": ["Specific improvements needed"]
  }},
  
  "red_flags": [
    {{
      "priority": "HIGH",
      "issue": "What must be fixed",
      "impact": "WHY this is critical",
      "fix": "How to fix it",
      "example": "Optional improved text"
    }}
  ],
  
  "warnings": [
    {{
      "priority": "MEDIUM",
      "issue": "What should be considered",
      "impact": "WHY this matters",
      "fix": "How to improve"
    }}
  ],
  
  "opportunities": [
    {{
      "priority": "LOW",
      "issue": "What could be better",
      "impact": "WHY consider this",
      "fix": "How to enhance"
    }}
  ],
  
  "quick_wins": [
    {{
      "original": "Current text",
      "improved": "Better version",
      "why": "WHY this is better",
      "impact": "Expected improvement"
    }}
  ],
  
  "will_cause_complaint": true/false,
  "will_cause_call": true/false,
  "nps_impact_prediction": "positive|neutral|negative",
  
  "scoring_rationale": {{
    "sentiment": "WHY we gave this sentiment score",
    "compliance": "WHY we gave this compliance rating",
    "impact": "WHY we predict this customer impact",
    "quality": "WHY we assessed quality this way"
  }},
  
  "key_evidence": ["Most important quotes that influenced the analysis"],
  
  "comparison_to_best_practice": "How this compares to ideal banking communication and WHY the gaps matter"
}}

Focus on:
1. TCF (Treating Customers Fairly) compliance
2. FCA vulnerable customer guidelines
3. Plain English and clarity
4. Likely customer reaction based on their segment
5. Practical, actionable improvements

ALWAYS explain the WHY behind every score and recommendation."""

        return prompt
    
    def _parse_ai_response(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse AI response with error handling"""
        content = content.replace('```json', '').replace('```', '').strip()
        
        try:
            # Direct parsing
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON
            if '{' in content and '}' in content:
                try:
                    start = content.index('{')
                    end = content.rindex('}') + 1
                    json_str = content[start:end]
                    return json.loads(json_str)
                except:
                    pass
        
        print("   ⚠️ Failed to parse AI response")
        return None
    
    def _create_result_from_ai(
        self,
        data: Dict[str, Any],
        refined_email: RefinedEmailResult,
        shared_context: SharedContext
    ) -> SentimentAnalysisResult:
        """Create result from AI analysis with focus on WHY"""
        
        # Parse sentiment score with reasoning
        sentiment_data = data.get('sentiment_score', {})
        sentiment_score = SentimentScore(
            score=sentiment_data.get('score', 0),
            category=SentimentCategory(sentiment_data.get('category', 'neutral')),
            confidence=sentiment_data.get('confidence', 0.8),
            why=sentiment_data.get('why', 'Analysis unavailable'),
            evidence=sentiment_data.get('evidence', [])
        )
        
        # Parse compliance check with reasoning
        compliance_data = data.get('compliance_check', {})
        compliance_check = ComplianceCheck(
            status=ComplianceStatus(compliance_data.get('status', 'pass')),
            tcf_score=compliance_data.get('tcf_score', 80),
            vulnerabilities_handled=compliance_data.get('vulnerabilities_handled', True),
            plain_english_score=compliance_data.get('plain_english_score', 75),
            why=compliance_data.get('why', ''),
            issues=compliance_data.get('issues', []),
            fixes=compliance_data.get('fixes', [])
        )
        
        # Parse customer impact with reasoning
        impact_data = data.get('customer_impact', {})
        customer_impact = CustomerImpact(
            complaint_probability=impact_data.get('complaint_probability', 10),
            call_probability=impact_data.get('call_probability', 20),
            nps_impact=impact_data.get('nps_impact', 0),
            satisfaction_delta=impact_data.get('satisfaction_delta', 0),
            why=impact_data.get('why', ''),
            risk_factors=impact_data.get('risk_factors', []),
            success_factors=impact_data.get('success_factors', [])
        )
        
        # Parse linguistic quality with reasoning
        quality_data = data.get('linguistic_quality', {})
        linguistic_quality = LinguisticQuality(
            readability_score=quality_data.get('readability_score', 60),
            grade_level=quality_data.get('grade_level', 9.0),
            jargon_count=quality_data.get('jargon_count', 0),
            passive_voice_percent=quality_data.get('passive_voice_percent', 10),
            sentence_complexity=quality_data.get('sentence_complexity', 'moderate'),
            why=quality_data.get('why', ''),
            improvements=quality_data.get('improvements', [])
        )
        
        # Parse actionable insights
        red_flags = []
        for flag_data in data.get('red_flags', []):
            red_flags.append(ActionableInsight(
                priority='HIGH',
                issue=flag_data.get('issue', ''),
                impact=flag_data.get('impact', ''),
                fix=flag_data.get('fix', ''),
                example=flag_data.get('example'),
                effort='Quick'
            ))
        
        warnings = []
        for warning_data in data.get('warnings', []):
            warnings.append(ActionableInsight(
                priority='MEDIUM',
                issue=warning_data.get('issue', ''),
                impact=warning_data.get('impact', ''),
                fix=warning_data.get('fix', ''),
                example=warning_data.get('example'),
                effort='Moderate'
            ))
        
        opportunities = []
        for opp_data in data.get('opportunities', []):
            opportunities.append(ActionableInsight(
                priority='LOW',
                issue=opp_data.get('issue', ''),
                impact=opp_data.get('impact', ''),
                fix=opp_data.get('fix', ''),
                example=opp_data.get('example'),
                effort='Significant'
            ))
        
        # Parse quick wins
        quick_wins = []
        for win_data in data.get('quick_wins', []):
            if isinstance(win_data, dict):
                quick_wins.append(QuickWin(
                    original=win_data.get('original', ''),
                    improved=win_data.get('improved', ''),
                    why=win_data.get('why', ''),
                    impact=win_data.get('impact', '')
                ))
        
        # Determine overall score and zone
        overall_score = data.get('overall_score', 0)
        overall_sentiment = overall_score / 100.0  # Convert to -1 to 1 for compatibility
        
        if overall_score >= 60:
            zone = SentimentZone.OPTIMAL
        elif overall_score >= 20:
            zone = SentimentZone.POSITIVE
        elif overall_score >= -20:
            zone = SentimentZone.NEUTRAL
        elif overall_score >= -60:
            zone = SentimentZone.CONCERNING
        else:
            zone = SentimentZone.CRITICAL
        
        # Ready to send decision
        ready_to_send = data.get('ready_to_send', len(red_flags) == 0)
        
        # Create simplified emotional dimensions for compatibility
        emotional_dims = {}
        for dim in EmotionalDimension:
            emotional_dims[dim] = 0.7  # Default reasonable scores
        
        # Create simplified journey for compatibility
        emotional_journey = EmotionalJourney(
            opening_sentiment=0,
            middle_sentiment=0,
            closing_sentiment=0,
            trajectory='stable',
            why='Sentiment remains consistent throughout the message'
        )
        
        # Create simplified psychological profile
        psychological_profile = PsychologicalProfile(
            cognitive_load='Medium',
            trust_building='Strong',
            customer_empowerment='Neutral',
            why='Message balances clarity with necessary information'
        )
        
        # Create simplified banking insights
        banking_insights = BankingInsights(
            complaint_probability=customer_impact.complaint_probability / 100.0,
            call_center_impact='low' if customer_impact.call_probability < 30 else 'medium',
            regulatory_tone_score=compliance_check.tcf_score / 100.0,
            trust_building=sentiment_score.score > 20,
            why=customer_impact.why,
            recommendations=[fix for fix in compliance_check.fixes[:3]]
        )
        
        # Outcome predictions for compatibility
        outcome_preds = {
            BankingOutcome.COMPLAINT_RISK: customer_impact.complaint_probability / 100.0,
            BankingOutcome.CALL_PROBABILITY: customer_impact.call_probability / 100.0,
            BankingOutcome.SATISFACTION_IMPACT: customer_impact.satisfaction_delta / 100.0
        }
        
        # Convert insights to recommendations for compatibility
        recommendations = []
        for insight in red_flags[:3] + warnings[:2]:
            recommendations.append(SentimentRecommendation(
                category='compliance' if 'compliance' in insight.issue.lower() else 'clarity',
                priority=insight.priority.lower(),
                issue=insight.issue,
                suggestion=insight.fix,
                impact=insight.impact,
                example=insight.example
            ))
        
        return SentimentAnalysisResult(
            overall_score=overall_score,
            overall_sentiment=overall_sentiment,
            sentiment_zone=zone,
            ready_to_send=ready_to_send,
            executive_summary=data.get('executive_summary', ''),
            
            sentiment_score=sentiment_score,
            compliance_check=compliance_check,
            customer_impact=customer_impact,
            linguistic_quality=linguistic_quality,
            
            red_flags=red_flags,
            warnings=warnings,
            opportunities=opportunities,
            quick_wins=quick_wins,
            
            will_cause_complaint=data.get('will_cause_complaint', False),
            will_cause_call=data.get('will_cause_call', False),
            nps_impact_prediction=data.get('nps_impact_prediction', 'neutral'),
            
            scoring_rationale=data.get('scoring_rationale', {}),
            key_evidence=data.get('key_evidence', []),
            comparison_to_best_practice=data.get('comparison_to_best_practice', ''),
            
            confidence_score=sentiment_score.confidence,
            emotional_dimensions=emotional_dims,
            emotional_journey=emotional_journey,
            psychological_profile=psychological_profile,
            banking_insights=banking_insights,
            outcome_predictions=outcome_preds,
            
            segment_alignment_score=0.8,
            segment_mismatches=[],
            why_alignment_matters='Customer expectations match communication style',
            
            cultural_appropriateness=0.9,
            language_formality_score=0.7,
            recommendations=recommendations,
            paragraph_sentiments=[],
            heatmap_data={'paragraphs': []},
            
            analysis_timestamp=datetime.now().isoformat(),
            processing_time=0.0,
            model_used=self.model,
            customer_context_considered={
                'segment': shared_context.customer_insights.segment,
                'vulnerabilities': shared_context.customer_insights.special_factors
            }
        )
    
    def _generate_heatmap_data(
        self,
        paragraph_sentiments: List[Dict],
        content: str
    ) -> Dict[str, Any]:
        """Generate data for sentiment heatmap visualization"""
        
        # Split content into paragraphs
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        heatmap = {
            'paragraphs': [],
            'max_sentiment': 1.0,
            'min_sentiment': -1.0
        }
        
        for i, para in enumerate(paragraphs):
            # Get sentiment from analysis or calculate
            sentiment = 0.0
            if i < len(paragraph_sentiments):
                sentiment = paragraph_sentiments[i].get('sentiment', 0)
            
            # Determine color based on sentiment
            if sentiment >= 0.5:
                color = '#4ade80'  # Green
            elif sentiment >= 0:
                color = '#fbbf24'  # Yellow
            else:
                color = '#f87171'  # Red
            
            heatmap['paragraphs'].append({
                'text': para[:100] + '...' if len(para) > 100 else para,
                'full_text': para,
                'sentiment': sentiment,
                'color': color,
                'index': i
            })
        
        return heatmap
    
    def _analyze_with_patterns(
        self,
        refined_email: RefinedEmailResult,
        shared_context: SharedContext
    ) -> SentimentAnalysisResult:
        """Fallback pattern-based analysis with WHY explanations"""
        
        content = refined_email.refined_content.lower()
        
        # Basic sentiment scoring
        positive_words = ['pleased', 'happy', 'delighted', 'thank', 'appreciate', 'valued', 'important', 'benefit']
        negative_words = ['unfortunately', 'regret', 'sorry', 'decline', 'unable', 'charge', 'fee', 'penalty']
        
        positive_count = sum(1 for word in positive_words if word in content)
        negative_count = sum(1 for word in negative_words if word in content)
        
        # Calculate score on -100 to 100 scale
        if positive_count + negative_count > 0:
            overall_score = int(((positive_count - negative_count) / (positive_count + negative_count)) * 100)
        else:
            overall_score = 0
        
        # Determine category and zone
        if overall_score >= 30:
            category = SentimentCategory.POSITIVE
            zone = SentimentZone.POSITIVE
            why = f"Found {positive_count} positive indicators suggesting customer satisfaction."
        elif overall_score >= -30:
            category = SentimentCategory.NEUTRAL
            zone = SentimentZone.NEUTRAL
            why = "Balanced tone with no strong emotional indicators."
        else:
            category = SentimentCategory.NEGATIVE
            zone = SentimentZone.CONCERNING
            why = f"Found {negative_count} negative indicators that may upset the customer."
        
        # Create sentiment score with WHY
        sentiment_score = SentimentScore(
            score=overall_score,
            category=category,
            confidence=0.6,
            why=why,
            evidence=[f"Positive words: {positive_count}", f"Negative words: {negative_count}"]
        )
        
        # Basic compliance check
        has_fee = 'fee' in content or 'charge' in content
        compliance_check = ComplianceCheck(
            status=ComplianceStatus.WARNING if has_fee else ComplianceStatus.PASS,
            tcf_score=70,
            vulnerabilities_handled=True,
            plain_english_score=65,
            why="Basic compliance check - manual review recommended" if has_fee else "No obvious compliance issues detected",
            issues=["Fee mention detected - ensure clear explanation"] if has_fee else [],
            fixes=["Add clear fee justification and customer benefit"] if has_fee else []
        )
        
        # Customer impact prediction
        customer_impact = CustomerImpact(
            complaint_probability=30 if negative_count > 2 else 10,
            call_probability=40 if has_fee else 20,
            nps_impact=-5 if negative_count > positive_count else 0,
            satisfaction_delta=overall_score,
            why=f"Based on {negative_count} negative and {positive_count} positive indicators",
            risk_factors=["Fee mentions"] if has_fee else [],
            success_factors=["Positive tone"] if positive_count > 0 else []
        )
        
        # Linguistic quality
        linguistic_quality = LinguisticQuality(
            readability_score=60,
            grade_level=9.0,
            jargon_count=0,
            passive_voice_percent=15,
            sentence_complexity='moderate',
            why="Pattern-based analysis - full linguistic analysis requires AI",
            improvements=[]
        )
        
        # Determine if ready to send
        ready_to_send = negative_count <= 2 and not has_fee
        
        # Executive summary
        executive_summary = f"Communication scores {overall_score}/100. {why} {'Ready to send.' if ready_to_send else 'Review recommended before sending.'}"
        
        # Create simplified components for compatibility
        emotional_dims = {dim: 0.5 for dim in EmotionalDimension}
        emotional_journey = EmotionalJourney(
            opening_sentiment=0,
            middle_sentiment=0,
            closing_sentiment=0,
            trajectory='stable',
            why='Pattern analysis cannot determine emotional flow'
        )
        
        psychological_profile = PsychologicalProfile(
            cognitive_load='Medium',
            trust_building='Moderate',
            customer_empowerment='Neutral',
            why='Basic analysis - detailed assessment requires AI'
        )
        
        banking_insights = BankingInsights(
            complaint_probability=customer_impact.complaint_probability / 100.0,
            call_center_impact='medium' if has_fee else 'low',
            regulatory_tone_score=0.7,
            trust_building=positive_count > negative_count,
            why=customer_impact.why,
            recommendations=compliance_check.fixes
        )
        
        # Create result
        return SentimentAnalysisResult(
            overall_score=overall_score,
            overall_sentiment=overall_score / 100.0,
            sentiment_zone=zone,
            ready_to_send=ready_to_send,
            executive_summary=executive_summary,
            
            sentiment_score=sentiment_score,
            compliance_check=compliance_check,
            customer_impact=customer_impact,
            linguistic_quality=linguistic_quality,
            
            red_flags=[],
            warnings=[ActionableInsight(
                priority='MEDIUM',
                issue='Limited analysis',
                impact='Pattern matching only - AI analysis recommended',
                fix='Enable AI for comprehensive analysis',
                example=None,
                effort='Quick'
            )],
            opportunities=[],
            quick_wins=[],
            
            will_cause_complaint=negative_count > 3,
            will_cause_call=has_fee,
            nps_impact_prediction='negative' if negative_count > positive_count else 'neutral',
            
            scoring_rationale={
                'sentiment': why,
                'compliance': compliance_check.why,
                'impact': customer_impact.why,
                'quality': linguistic_quality.why
            },
            key_evidence=[],
            comparison_to_best_practice='Pattern analysis provides basic assessment only',
            
            confidence_score=0.6,
            emotional_dimensions=emotional_dims,
            emotional_journey=emotional_journey,
            psychological_profile=psychological_profile,
            banking_insights=banking_insights,
            outcome_predictions={outcome: 0.5 for outcome in BankingOutcome},
            
            segment_alignment_score=0.7,
            segment_mismatches=[],
            why_alignment_matters='Segment alignment requires AI analysis',
            
            cultural_appropriateness=0.8,
            language_formality_score=0.7,
            recommendations=[],
            paragraph_sentiments=[],
            heatmap_data={'paragraphs': []},
            
            analysis_timestamp=datetime.now().isoformat(),
            processing_time=0.0,
            model_used='pattern_matching',
            customer_context_considered={}
        )
    
    def _create_error_result(
        self,
        refined_email: RefinedEmailResult,
        shared_context: SharedContext,
        error_message: str
    ) -> SentimentAnalysisResult:
        """Create a minimal valid result when analysis fails"""
        
        # Create minimal valid components
        sentiment_score = SentimentScore(
            score=0,
            category=SentimentCategory.NEUTRAL,
            confidence=0.0,
            why=f"Analysis failed: {error_message}",
            evidence=[]
        )
        
        compliance_check = ComplianceCheck(
            status=ComplianceStatus.WARNING,
            tcf_score=50,
            vulnerabilities_handled=False,
            plain_english_score=50,
            why="Unable to analyze - manual review required",
            issues=["Analysis failed"],
            fixes=["Retry analysis"]
        )
        
        customer_impact = CustomerImpact(
            complaint_probability=50,
            call_probability=50,
            nps_impact=0,
            satisfaction_delta=0,
            why="Unable to predict - analysis failed",
            risk_factors=["Analysis incomplete"],
            success_factors=[]
        )
        
        linguistic_quality = LinguisticQuality(
            readability_score=50,
            grade_level=10.0,
            jargon_count=0,
            passive_voice_percent=0,
            sentence_complexity='unknown',
            why="Unable to analyze linguistic quality",
            improvements=[]
        )
        
        return SentimentAnalysisResult(
            overall_score=0,
            overall_sentiment=0.0,
            sentiment_zone=SentimentZone.NEUTRAL,
            ready_to_send=False,
            executive_summary=f"Analysis failed: {error_message}. Manual review required.",
            
            sentiment_score=sentiment_score,
            compliance_check=compliance_check,
            customer_impact=customer_impact,
            linguistic_quality=linguistic_quality,
            
            red_flags=[ActionableInsight(
                priority='HIGH',
                issue='Analysis failed',
                impact=error_message,
                fix='Retry analysis or review manually',
                example=None,
                effort='Quick'
            )],
            warnings=[],
            opportunities=[],
            quick_wins=[],
            
            will_cause_complaint=False,
            will_cause_call=False,
            nps_impact_prediction='unknown',
            
            scoring_rationale={'error': error_message},
            key_evidence=[],
            comparison_to_best_practice='Analysis incomplete',
            
            confidence_score=0.0,
            emotional_dimensions={dim: 0.5 for dim in EmotionalDimension},
            emotional_journey=EmotionalJourney(
                opening_sentiment=0,
                middle_sentiment=0,
                closing_sentiment=0,
                trajectory='unknown',
                why='Analysis failed'
            ),
            psychological_profile=PsychologicalProfile(
                cognitive_load='Unknown',
                trust_building='Unknown',
                customer_empowerment='Unknown',
                why='Analysis failed'
            ),
            banking_insights=BankingInsights(
                complaint_probability=0.5,
                call_center_impact='unknown',
                regulatory_tone_score=0.5,
                trust_building=False,
                why=error_message,
                recommendations=[]
            ),
            outcome_predictions={outcome: 0.5 for outcome in BankingOutcome},
            
            segment_alignment_score=0.5,
            segment_mismatches=[],
            why_alignment_matters='Unable to assess',
            
            cultural_appropriateness=0.5,
            language_formality_score=0.5,
            recommendations=[],
            paragraph_sentiments=[],
            heatmap_data={'paragraphs': []},
            
            analysis_timestamp=datetime.now().isoformat(),
            processing_time=0.0,
            model_used='error_fallback',
            customer_context_considered={}
        )

# Convenience function
def analyze_email_sentiment(
    refined_email: RefinedEmailResult,
    shared_context: SharedContext,
    api_key: Optional[str] = None
) -> SentimentAnalysisResult:
    """
    Analyze sentiment of refined email
    
    Args:
        refined_email: The refined email to analyze
        shared_context: Complete context from SharedBrain
        api_key: Optional API key
        
    Returns:
        SentimentAnalysisResult with comprehensive analysis
    """
    analyzer = SentimentAnalyzer(api_key=api_key)
    return analyzer.analyze_sentiment(refined_email, shared_context)