"""
Advanced Sentiment Analyzer - Multi-Dimensional Emotional & Banking Intelligence
Analyzes refined emails for emotional impact, business outcomes, and customer satisfaction
Uses Claude Sonnet 4 for state-of-the-art analysis
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

class EmotionalDimension(Enum):
    """Emotional dimensions we analyze"""
    WARMTH = "warmth"
    ANXIETY = "anxiety"
    TRUST = "trust"
    URGENCY = "urgency"
    EMPATHY = "empathy"
    CLARITY = "clarity"
    AUTHORITY = "authority"
    REASSURANCE = "reassurance"

class BankingOutcome(Enum):
    """Banking-specific outcomes we predict"""
    COMPLAINT_RISK = "complaint_risk"
    CALL_PROBABILITY = "call_probability"
    CROSS_SELL_READINESS = "cross_sell_readiness"
    CHURN_RISK = "churn_risk"
    SATISFACTION_IMPACT = "satisfaction_impact"
    DIGITAL_ADOPTION = "digital_adoption"
    REFERRAL_LIKELIHOOD = "referral_likelihood"

class SentimentZone(Enum):
    """Overall sentiment classification"""
    OPTIMAL = "optimal"           # Perfect for customer and context
    POSITIVE = "positive"          # Good but could be improved
    NEUTRAL = "neutral"           # Functional but uninspiring
    CONCERNING = "concerning"     # Some issues to address
    CRITICAL = "critical"         # High risk of negative outcome

@dataclass
class EmotionalJourney:
    """How sentiment flows through the email"""
    opening_sentiment: float      # -1 to 1 scale
    middle_sentiment: float
    closing_sentiment: float
    volatility: float             # How much sentiment swings
    trajectory: str               # rising, falling, stable, volatile
    dead_zones: List[str]         # Parts with no emotional engagement
    peak_moments: List[str]       # Highest emotional points
    
@dataclass
class BankingInsights:
    """Banking-specific insights from sentiment"""
    complaint_probability: float
    call_center_impact: str
    cross_sell_opportunities: List[str]
    identified_vulnerabilities: List[str]
    regulatory_tone_score: float
    fee_mention_sensitivity: float
    trust_markers_present: List[str]
    risk_flags: List[str]
    
@dataclass
class PsychologicalProfile:
    """Deep psychological analysis"""
    cognitive_load: float         # How hard to understand (0-1)
    psychological_safety: float   # Feeling of security (0-1)
    autonomy_support: float       # Empowers vs controls (0-1)
    social_connection: float      # Human vs corporate (0-1)
    competence_building: float    # Educates vs confuses (0-1)
    
@dataclass
class SentimentRecommendation:
    """Specific improvement recommendation"""
    category: str                 # emotional, banking, compliance, etc.
    priority: str                 # high, medium, low
    issue: str                    # What's wrong
    suggestion: str               # How to fix it
    impact: str                   # What improvement to expect
    example: Optional[str]        # Example of improved text
    
@dataclass
class SentimentAnalysisResult:
    """Complete sentiment analysis result"""
    # Core scores
    overall_sentiment: float      # -1 to 1 scale
    sentiment_zone: SentimentZone
    confidence_score: float
    
    # Multi-dimensional analysis
    emotional_dimensions: Dict[EmotionalDimension, float]
    emotional_journey: EmotionalJourney
    psychological_profile: PsychologicalProfile
    
    # Banking specific
    banking_insights: BankingInsights
    outcome_predictions: Dict[BankingOutcome, float]
    
    # Segment alignment
    segment_alignment_score: float
    segment_mismatches: List[str]
    
    # Cultural sensitivity
    cultural_appropriateness: float
    language_formality_score: float
    
    # Actionable insights
    recommendations: List[SentimentRecommendation]
    quick_wins: List[str]
    
    # Detailed analysis
    paragraph_sentiments: List[Dict[str, Any]]
    heatmap_data: Dict[str, Any]
    
    # Metadata
    analysis_timestamp: str
    processing_time: float
    model_used: str
    customer_context_considered: Dict[str, Any]

class SentimentAnalyzer:
    """
    Advanced Sentiment Analysis Engine
    Combines emotional intelligence with banking-specific insights
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Claude Sonnet 4"""
        self.api_key = api_key or os.getenv('CLAUDE_API_KEY')
        self.client = None
        
        if self.api_key:
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
                self.model = "claude-sonnet-4-20250514"  # Latest model as of Sept 2025
                print("✅ Sentiment Analyzer initialized with Claude Sonnet 4")
            except Exception as e:
                print(f"⚠️ Failed to initialize Claude client: {e}")
                self.client = None
        else:
            print("⚠️ Sentiment Analyzer running without AI")
    
    def analyze_sentiment(
        self,
        refined_email: RefinedEmailResult,
        shared_context: SharedContext
    ) -> SentimentAnalysisResult:
        """
        Perform comprehensive sentiment analysis on refined email
        
        Args:
            refined_email: The refined email to analyze
            shared_context: Complete context from SharedBrain
            
        Returns:
            SentimentAnalysisResult with deep insights
        """
        start_time = datetime.now()
        
        customer_name = shared_context.customer_data.get('name', 'Unknown')
        print(f"🧠 Starting advanced sentiment analysis for {customer_name}...")
        
        if self.client:
            result = self._analyze_with_ai(refined_email, shared_context)
        else:
            result = self._analyze_with_patterns(refined_email, shared_context)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        result.processing_time = processing_time
        
        print(f"✅ Sentiment analysis complete in {processing_time:.2f}s")
        print(f"   Overall sentiment: {result.overall_sentiment:.2f} ({result.sentiment_zone.value})")
        print(f"   Complaint risk: {result.banking_insights.complaint_probability:.0%}")
        print(f"   Recommendations: {len(result.recommendations)}")
        
        return result
    
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
        """Build comprehensive prompt for sentiment analysis"""
        
        customer = shared_context.customer_data
        insights = shared_context.customer_insights
        
        prompt = f"""You are an expert in psycholinguistics and banking customer experience. Perform a comprehensive sentiment analysis of this refined bank email.

EMAIL CONTENT:
Subject: {refined_email.refined_subject}
Body: {refined_email.refined_content}

CUSTOMER CONTEXT:
- Name: {customer.get('name')}
- Segment: {insights.segment}
- Life Stage: {insights.life_stage}
- Financial Profile: {insights.financial_profile}
- Recent Events: {customer.get('recent_life_events', 'None')}
- Account Balance: £{customer.get('account_balance', 0):,}
- Digital Engagement: {customer.get('digital_logins_per_month', 0)} logins/month
- Vulnerability Indicators: {', '.join(insights.special_factors) if insights.special_factors else 'None'}

Perform a multi-dimensional analysis and return JSON:

{{
  "overall_sentiment": -1.0 to 1.0,
  "sentiment_zone": "optimal|positive|neutral|concerning|critical",
  "confidence_score": 0.0 to 1.0,
  
  "emotional_dimensions": {{
    "warmth": 0.0 to 1.0,
    "anxiety": 0.0 to 1.0,
    "trust": 0.0 to 1.0,
    "urgency": 0.0 to 1.0,
    "empathy": 0.0 to 1.0,
    "clarity": 0.0 to 1.0,
    "authority": 0.0 to 1.0,
    "reassurance": 0.0 to 1.0
  }},
  
  "emotional_journey": {{
    "opening_sentiment": -1.0 to 1.0,
    "middle_sentiment": -1.0 to 1.0,
    "closing_sentiment": -1.0 to 1.0,
    "volatility": 0.0 to 1.0,
    "trajectory": "rising|falling|stable|volatile",
    "dead_zones": ["sections with no emotional engagement"],
    "peak_moments": ["highest emotional impact sections"]
  }},
  
  "psychological_profile": {{
    "cognitive_load": 0.0 to 1.0,
    "psychological_safety": 0.0 to 1.0,
    "autonomy_support": 0.0 to 1.0,
    "social_connection": 0.0 to 1.0,
    "competence_building": 0.0 to 1.0
  }},
  
  "banking_insights": {{
    "complaint_probability": 0.0 to 1.0,
    "call_center_impact": "high|medium|low|none",
    "cross_sell_opportunities": ["identified product opportunities"],
    "identified_vulnerabilities": ["customer vulnerabilities noted"],
    "regulatory_tone_score": 0.0 to 1.0,
    "fee_mention_sensitivity": 0.0 to 1.0,
    "trust_markers_present": ["trust-building elements found"],
    "risk_flags": ["potential issues identified"]
  }},
  
  "outcome_predictions": {{
    "complaint_risk": 0.0 to 1.0,
    "call_probability": 0.0 to 1.0,
    "cross_sell_readiness": 0.0 to 1.0,
    "churn_risk": 0.0 to 1.0,
    "satisfaction_impact": -1.0 to 1.0,
    "digital_adoption": 0.0 to 1.0,
    "referral_likelihood": 0.0 to 1.0
  }},
  
  "segment_alignment": {{
    "alignment_score": 0.0 to 1.0,
    "mismatches": ["ways the tone doesn't match segment expectations"]
  }},
  
  "cultural_sensitivity": {{
    "appropriateness": 0.0 to 1.0,
    "formality_score": 0.0 to 1.0
  }},
  
  "recommendations": [
    {{
      "category": "emotional|banking|compliance|clarity",
      "priority": "high|medium|low",
      "issue": "specific problem identified",
      "suggestion": "specific fix",
      "impact": "expected improvement",
      "example": "optional rewritten text"
    }}
  ],
  
  "quick_wins": ["simple improvements with high impact"],
  
  "paragraph_sentiments": [
    {{
      "paragraph_index": 0,
      "text_preview": "first 50 chars...",
      "sentiment": -1.0 to 1.0,
      "dominant_emotion": "primary emotion",
      "banking_relevance": "what banking topic"
    }}
  ]
}}

Consider:
1. How well the tone matches the customer segment
2. Banking-specific triggers (fees, charges, changes)
3. Vulnerable customer indicators
4. Psychological safety and trust building
5. Likelihood of customer contact or complaint
6. Cross-sell/upsell appropriateness
7. Regulatory compliance tone

Be specific and actionable in recommendations."""

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
        """Create result from AI analysis"""
        
        # Parse emotional dimensions
        emotional_dims = {}
        for dim in EmotionalDimension:
            score = data.get('emotional_dimensions', {}).get(dim.value, 0.5)
            emotional_dims[dim] = score
        
        # Parse emotional journey
        journey_data = data.get('emotional_journey', {})
        emotional_journey = EmotionalJourney(
            opening_sentiment=journey_data.get('opening_sentiment', 0),
            middle_sentiment=journey_data.get('middle_sentiment', 0),
            closing_sentiment=journey_data.get('closing_sentiment', 0),
            volatility=journey_data.get('volatility', 0),
            trajectory=journey_data.get('trajectory', 'stable'),
            dead_zones=journey_data.get('dead_zones', []),
            peak_moments=journey_data.get('peak_moments', [])
        )
        
        # Parse psychological profile
        psych_data = data.get('psychological_profile', {})
        psychological_profile = PsychologicalProfile(
            cognitive_load=psych_data.get('cognitive_load', 0.5),
            psychological_safety=psych_data.get('psychological_safety', 0.5),
            autonomy_support=psych_data.get('autonomy_support', 0.5),
            social_connection=psych_data.get('social_connection', 0.5),
            competence_building=psych_data.get('competence_building', 0.5)
        )
        
        # Parse banking insights
        banking_data = data.get('banking_insights', {})
        banking_insights = BankingInsights(
            complaint_probability=banking_data.get('complaint_probability', 0),
            call_center_impact=banking_data.get('call_center_impact', 'low'),
            cross_sell_opportunities=banking_data.get('cross_sell_opportunities', []),
            identified_vulnerabilities=banking_data.get('identified_vulnerabilities', []),
            regulatory_tone_score=banking_data.get('regulatory_tone_score', 0.8),
            fee_mention_sensitivity=banking_data.get('fee_mention_sensitivity', 0),
            trust_markers_present=banking_data.get('trust_markers_present', []),
            risk_flags=banking_data.get('risk_flags', [])
        )
        
        # Parse outcome predictions
        outcome_preds = {}
        for outcome in BankingOutcome:
            score = data.get('outcome_predictions', {}).get(outcome.value, 0.5)
            outcome_preds[outcome] = score
        
        # Parse recommendations
        recommendations = []
        for rec_data in data.get('recommendations', []):
            recommendations.append(SentimentRecommendation(
                category=rec_data.get('category', 'general'),
                priority=rec_data.get('priority', 'medium'),
                issue=rec_data.get('issue', ''),
                suggestion=rec_data.get('suggestion', ''),
                impact=rec_data.get('impact', ''),
                example=rec_data.get('example')
            ))
        
        # Determine sentiment zone
        overall_sentiment = data.get('overall_sentiment', 0)
        if overall_sentiment >= 0.6:
            zone = SentimentZone.OPTIMAL
        elif overall_sentiment >= 0.2:
            zone = SentimentZone.POSITIVE
        elif overall_sentiment >= -0.2:
            zone = SentimentZone.NEUTRAL
        elif overall_sentiment >= -0.6:
            zone = SentimentZone.CONCERNING
        else:
            zone = SentimentZone.CRITICAL
        
        # Create heatmap data
        heatmap_data = self._generate_heatmap_data(
            data.get('paragraph_sentiments', []),
            refined_email.refined_content
        )
        
        return SentimentAnalysisResult(
            overall_sentiment=overall_sentiment,
            sentiment_zone=zone,
            confidence_score=data.get('confidence_score', 0.85),
            emotional_dimensions=emotional_dims,
            emotional_journey=emotional_journey,
            psychological_profile=psychological_profile,
            banking_insights=banking_insights,
            outcome_predictions=outcome_preds,
            segment_alignment_score=data.get('segment_alignment', {}).get('alignment_score', 0.8),
            segment_mismatches=data.get('segment_alignment', {}).get('mismatches', []),
            cultural_appropriateness=data.get('cultural_sensitivity', {}).get('appropriateness', 0.9),
            language_formality_score=data.get('cultural_sensitivity', {}).get('formality_score', 0.7),
            recommendations=recommendations,
            quick_wins=data.get('quick_wins', []),
            paragraph_sentiments=data.get('paragraph_sentiments', []),
            heatmap_data=heatmap_data,
            analysis_timestamp=datetime.now().isoformat(),
            processing_time=0.0,
            model_used=self.model,
            customer_context_considered={
                'segment': shared_context.customer_insights.segment,
                'life_stage': shared_context.customer_insights.life_stage,
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
        """Fallback pattern-based analysis"""
        
        content = refined_email.refined_content.lower()
        
        # Basic sentiment scoring
        positive_words = ['pleased', 'happy', 'delighted', 'thank', 'appreciate', 'valued', 'important', 'benefit']
        negative_words = ['unfortunately', 'regret', 'sorry', 'decline', 'unable', 'charge', 'fee', 'penalty']
        
        positive_count = sum(1 for word in positive_words if word in content)
        negative_count = sum(1 for word in negative_words if word in content)
        
        overall_sentiment = (positive_count - negative_count) / max(positive_count + negative_count, 1)
        
        # Determine zone
        if overall_sentiment >= 0.3:
            zone = SentimentZone.POSITIVE
        elif overall_sentiment >= -0.3:
            zone = SentimentZone.NEUTRAL
        else:
            zone = SentimentZone.CONCERNING
        
        # Create basic result
        return SentimentAnalysisResult(
            overall_sentiment=overall_sentiment,
            sentiment_zone=zone,
            confidence_score=0.6,
            emotional_dimensions={dim: 0.5 for dim in EmotionalDimension},
            emotional_journey=EmotionalJourney(
                opening_sentiment=0,
                middle_sentiment=0,
                closing_sentiment=0,
                volatility=0,
                trajectory='stable',
                dead_zones=[],
                peak_moments=[]
            ),
            psychological_profile=PsychologicalProfile(
                cognitive_load=0.5,
                psychological_safety=0.5,
                autonomy_support=0.5,
                social_connection=0.5,
                competence_building=0.5
            ),
            banking_insights=BankingInsights(
                complaint_probability=0.2 if negative_count > 2 else 0.1,
                call_center_impact='low',
                cross_sell_opportunities=[],
                identified_vulnerabilities=[],
                regulatory_tone_score=0.7,
                fee_mention_sensitivity=1.0 if 'fee' in content else 0,
                trust_markers_present=[],
                risk_flags=[]
            ),
            outcome_predictions={outcome: 0.5 for outcome in BankingOutcome},
            segment_alignment_score=0.7,
            segment_mismatches=[],
            cultural_appropriateness=0.8,
            language_formality_score=0.7,
            recommendations=[],
            quick_wins=[],
            paragraph_sentiments=[],
            heatmap_data={'paragraphs': []},
            analysis_timestamp=datetime.now().isoformat(),
            processing_time=0.0,
            model_used='pattern_matching',
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