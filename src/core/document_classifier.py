"""
AI-Powered Document Classifier Module
Uses Claude to intelligently classify documents with detailed insights
"""

import os
import json
import re
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# Try to import anthropic
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("Warning: Anthropic not available - using mock classification")

class DocumentType(Enum):
    """Document classification types"""
    REGULATORY = "REGULATORY"
    PROMOTIONAL = "PROMOTIONAL"
    INFORMATIONAL = "INFORMATIONAL"
    TRANSACTIONAL = "TRANSACTIONAL"
    SERVICE = "SERVICE"
    URGENT = "URGENT"

@dataclass
class ClassificationResult:
    """Detailed classification result with insights"""
    primary_classification: str
    confidence_score: float
    classification_scores: Dict[str, float]
    reasoning: str
    key_indicators: List[str]
    detected_patterns: Dict[str, List[str]]
    urgency_level: str
    compliance_required: bool
    customer_action_required: bool
    sentiment: str
    tone: str
    complexity_score: float
    ai_insights: Dict[str, Any]
    processing_time: float
    model_used: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

class AIDocumentClassifier:
    """AI-powered document classification with detailed analysis"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Claude API"""
        self.api_key = api_key or os.getenv('CLAUDE_API_KEY')
        self.client = None

    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Claude API"""
        self.api_key = api_key or os.getenv('CLAUDE_API_KEY')
    
    # DEBUG: Check what we're getting
        print(f"DEBUG: API key provided: {bool(api_key)}")
        print(f"DEBUG: API key from env: {bool(os.getenv('CLAUDE_API_KEY'))}")
        print(f"DEBUG: Final API key exists: {bool(self.api_key)}")
        print(f"DEBUG: Anthropic available: {ANTHROPIC_AVAILABLE}")
        
        if self.api_key and ANTHROPIC_AVAILABLE:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.model = "claude-haiku-4-5-20251001"  # Best balance of speed and intelligence
            print("✅ AI Document Classifier initialized with Claude")
        else:
            print("⚠️ AI Document Classifier in mock mode")
    
    def classify_document(self, document_text: str, include_visualization_data: bool = True) -> ClassificationResult:
        """
        Perform comprehensive AI-powered document classification
        
        Args:
            document_text: The document to classify
            include_visualization_data: Whether to include extra data for charts
            
        Returns:
            Detailed classification result with AI insights
        """
        start_time = datetime.now()
        
        if self.client:
            result = self._ai_classification(document_text, include_visualization_data)
        else:
            result = self._mock_classification(document_text)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        result.processing_time = processing_time
        
        return result
    
    def _ai_classification(self, document_text: str, include_viz: bool) -> ClassificationResult:
        """Use Claude for intelligent classification"""
        
        prompt = f"""You are an expert document analyst for Lloyds Bank. Analyze this document and provide a comprehensive classification with detailed insights.

DOCUMENT TO ANALYZE:
{document_text}

Provide a detailed analysis in the following JSON format:
{{
    "primary_classification": "REGULATORY|PROMOTIONAL|INFORMATIONAL|TRANSACTIONAL|SERVICE|URGENT",
    "confidence_score": 0.00 to 1.00,
    "classification_scores": {{
        "REGULATORY": 0.00 to 1.00,
        "PROMOTIONAL": 0.00 to 1.00,
        "INFORMATIONAL": 0.00 to 1.00,
        "TRANSACTIONAL": 0.00 to 1.00,
        "SERVICE": 0.00 to 1.00,
        "URGENT": 0.00 to 1.00
    }},
    "reasoning": "Detailed explanation of why this classification was chosen, mentioning specific evidence from the document",
    "key_indicators": [
        "List of specific phrases/elements that strongly influenced the classification",
        "Include quotes from the document",
        "At least 5-10 indicators"
    ],
    "detected_patterns": {{
        "regulatory_language": ["specific regulatory phrases found"],
        "promotional_elements": ["offers, discounts, benefits mentioned"],
        "action_items": ["what customer needs to do"],
        "dates_deadlines": ["important dates mentioned"],
        "financial_terms": ["amounts, fees, rates mentioned"],
        "contact_information": ["phone numbers, websites, emails"],
        "legal_requirements": ["compliance, mandatory elements"]
    }},
    "urgency_level": "HIGH|MEDIUM|LOW|NONE",
    "compliance_required": true/false,
    "customer_action_required": true/false,
    "sentiment": "POSITIVE|NEUTRAL|NEGATIVE|MIXED",
    "tone": "FORMAL|FRIENDLY|URGENT|INFORMATIVE|PROMOTIONAL|CAUTIONARY",
    "complexity_score": 0.00 to 1.00,
    "ai_insights": {{
        "primary_purpose": "What is the main goal of this communication",
        "target_audience": "Who is this intended for",
        "key_message": "Core message in one sentence",
        "hidden_implications": "Any subtle implications or between-the-lines meaning",
        "emotional_impact": "How this might make the customer feel",
        "recommended_channels": ["best channels for this type of content"],
        "personalization_opportunities": ["how this could be personalized"],
        "potential_concerns": ["what might worry or confuse customers"],
        "call_to_action": "Main action the customer should take",
        "regulatory_implications": "Any compliance or legal considerations"
    }},
    "alternative_classifications": {{
        "secondary_type": "Second most likely classification",
        "secondary_confidence": 0.00 to 1.00,
        "why_not_chosen": "Why the primary was chosen over this"
    }},
    "linguistic_analysis": {{
        "reading_level": "Grade level equivalent",
        "jargon_score": 0.00 to 1.00,
        "clarity_score": 0.00 to 1.00,
        "formality_level": 0.00 to 1.00
    }},
    "risk_assessment": {{
        "misunderstanding_risk": "HIGH|MEDIUM|LOW",
        "reputation_risk": "HIGH|MEDIUM|LOW",
        "compliance_risk": "HIGH|MEDIUM|LOW",
        "customer_satisfaction_risk": "HIGH|MEDIUM|LOW"
    }}
}}

Be thorough and insightful. Consider both obvious and subtle aspects of the document."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=3000,
                temperature=0.3,  # Low temperature for consistent analysis
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text.strip()
            
            # Parse JSON response
            if '{' in content:
                json_start = content.index('{')
                json_end = content.rindex('}') + 1
                json_str = content[json_start:json_end]
                data = json.loads(json_str)
                
                # Create ClassificationResult
                result = ClassificationResult(
                    primary_classification=data.get('primary_classification', 'INFORMATIONAL'),
                    confidence_score=float(data.get('confidence_score', 0.5)),
                    classification_scores=data.get('classification_scores', {}),
                    reasoning=data.get('reasoning', 'No reasoning provided'),
                    key_indicators=data.get('key_indicators', []),
                    detected_patterns=data.get('detected_patterns', {}),
                    urgency_level=data.get('urgency_level', 'LOW'),
                    compliance_required=data.get('compliance_required', False),
                    customer_action_required=data.get('customer_action_required', False),
                    sentiment=data.get('sentiment', 'NEUTRAL'),
                    tone=data.get('tone', 'INFORMATIVE'),
                    complexity_score=float(data.get('complexity_score', 0.5)),
                    ai_insights=data.get('ai_insights', {}),
                    processing_time=0.0,
                    model_used=self.model
                )
                
                # Add extra insights if available
                if 'alternative_classifications' in data:
                    result.ai_insights['alternative_classifications'] = data['alternative_classifications']
                if 'linguistic_analysis' in data:
                    result.ai_insights['linguistic_analysis'] = data['linguistic_analysis']
                if 'risk_assessment' in data:
                    result.ai_insights['risk_assessment'] = data['risk_assessment']
                
                return result
            else:
                return self._fallback_classification(document_text)
                
        except Exception as e:
            print(f"AI classification error: {e}")
            return self._fallback_classification(document_text)
    
    def _fallback_classification(self, document_text: str) -> ClassificationResult:
        """Fallback classification using enhanced pattern matching"""
        text_lower = document_text.lower()
        
        # Score each category
        scores = {
            'REGULATORY': 0.0,
            'PROMOTIONAL': 0.0,
            'INFORMATIONAL': 0.0,
            'TRANSACTIONAL': 0.0,
            'SERVICE': 0.0,
            'URGENT': 0.0
        }
        
        key_indicators = []
        detected_patterns = {
            'regulatory_language': [],
            'promotional_elements': [],
            'action_items': [],
            'dates_deadlines': [],
            'financial_terms': [],
            'contact_information': [],
            'legal_requirements': []
        }
        
        # Regulatory indicators
        regulatory_terms = [
            'terms and conditions', 'regulatory', 'compliance', 'legal requirement',
            'mandatory', 'required by law', 'payment services regulations',
            'important changes', 'notice of changes', 'must inform'
        ]
        for term in regulatory_terms:
            if term in text_lower:
                scores['REGULATORY'] += 0.15
                key_indicators.append(f"Found regulatory term: '{term}'")
                detected_patterns['regulatory_language'].append(term)
        
        # Promotional indicators
        promotional_terms = [
            'offer', 'save', 'exclusive', 'limited time', 'special rate',
            'earn rewards', 'bonus', 'discount', 'opportunity', 'benefit'
        ]
        for term in promotional_terms:
            if term in text_lower:
                scores['PROMOTIONAL'] += 0.12
                key_indicators.append(f"Found promotional term: '{term}'")
                detected_patterns['promotional_elements'].append(term)
        
        # Urgent indicators
        urgent_terms = [
            'urgent', 'immediate', 'action required', 'deadline', 'expires',
            'must act', 'time sensitive', 'asap', 'critical'
        ]
        for term in urgent_terms:
            if term in text_lower:
                scores['URGENT'] += 0.2
                key_indicators.append(f"Urgency indicator: '{term}'")
        
        # Detect dates and amounts
        dates = re.findall(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}', text_lower)
        if dates:
            detected_patterns['dates_deadlines'] = dates[:5]
            key_indicators.append(f"Contains {len(dates)} date reference(s)")
        
        amounts = re.findall(r'[£$€]\s*\d+(?:,\d{3})*(?:\.\d{2})?', document_text)
        if amounts:
            detected_patterns['financial_terms'] = amounts[:5]
            key_indicators.append(f"Contains {len(amounts)} financial amount(s)")
            scores['TRANSACTIONAL'] += 0.1
        
        # Determine primary classification
        if not any(scores.values()):
            scores['INFORMATIONAL'] = 0.6
        
        primary = max(scores.items(), key=lambda x: x[1])
        
        # Normalize scores
        total = sum(scores.values()) or 1
        normalized_scores = {k: v/total for k, v in scores.items()}
        
        # Determine urgency
        urgency = 'HIGH' if scores['URGENT'] > 0.3 else 'MEDIUM' if dates else 'LOW'
        
        # Determine if action required
        action_required = any(term in text_lower for term in ['action required', 'must', 'need to', 'please'])
        
        return ClassificationResult(
            primary_classification=primary[0],
            confidence_score=min(primary[1] / total, 1.0) if total > 0 else 0.5,
            classification_scores=normalized_scores,
            reasoning=f"Classification based on detected patterns: {len(key_indicators)} key indicators found",
            key_indicators=key_indicators[:10],
            detected_patterns=detected_patterns,
            urgency_level=urgency,
            compliance_required='regulatory' in text_lower or 'compliance' in text_lower,
            customer_action_required=action_required,
            sentiment='NEUTRAL',
            tone='FORMAL' if 'dear' in text_lower else 'INFORMATIVE',
            complexity_score=min(len(document_text) / 5000, 1.0),
            ai_insights={
                'primary_purpose': 'Document classification based on pattern analysis',
                'key_message': 'Automated classification without AI',
                'recommended_channels': ['email', 'letter'],
                'method': 'fallback_pattern_matching'
            },
            processing_time=0.0,
            model_used='pattern_matching'
        )
    
    def _mock_classification(self, document_text: str) -> ClassificationResult:
        """Mock classification for testing"""
        return ClassificationResult(
            primary_classification='INFORMATIONAL',
            confidence_score=0.92,
            classification_scores={
                'REGULATORY': 0.15,
                'PROMOTIONAL': 0.08,
                'INFORMATIONAL': 0.62,
                'TRANSACTIONAL': 0.05,
                'SERVICE': 0.07,
                'URGENT': 0.03
            },
            reasoning="This document appears to be informational based on its helpful tone and educational content about banking features.",
            key_indicators=[
                "Phrase: 'helpful tools and tips'",
                "Phrase: 'Here are a few features'",
                "Educational tone throughout",
                "No urgent action required",
                "Contact information provided for support"
            ],
            detected_patterns={
                'regulatory_language': [],
                'promotional_elements': ['features', 'tools'],
                'action_items': ['visit website', 'call for help'],
                'dates_deadlines': [],
                'financial_terms': [],
                'contact_information': ['Customer Services Number', 'lloydsbank.com'],
                'legal_requirements': []
            },
            urgency_level='LOW',
            compliance_required=False,
            customer_action_required=False,
            sentiment='POSITIVE',
            tone='FRIENDLY',
            complexity_score=0.3,
            ai_insights={
                'primary_purpose': 'Educate customers about available banking tools',
                'target_audience': 'All retail banking customers',
                'key_message': 'Lloyds provides helpful tools to manage your money',
                'emotional_impact': 'Reassuring and supportive',
                'recommended_channels': ['email', 'app', 'website'],
                'personalization_opportunities': ['Highlight tools based on usage', 'Language preference', 'Digital literacy level'],
                'potential_concerns': ['Some customers may not be digitally confident'],
                'call_to_action': 'Explore the tools available online or visit branch for help'
            },
            processing_time=0.1,
            model_used='mock'
        )
    
    def get_visualization_data(self, result: ClassificationResult) -> Dict[str, Any]:
        """
        Prepare data optimized for visualization in the UI
        
        Returns data structured for charts and visual displays
        """
        return {
            'classification_chart': {
                'labels': list(result.classification_scores.keys()),
                'values': list(result.classification_scores.values()),
                'colors': {
                    'REGULATORY': '#FF6B6B',
                    'PROMOTIONAL': '#4ECDC4',
                    'INFORMATIONAL': '#45B7D1',
                    'TRANSACTIONAL': '#96CEB4',
                    'SERVICE': '#FFEAA7',
                    'URGENT': '#FF4757'
                }
            },
            'confidence_meter': {
                'value': result.confidence_score * 100,
                'label': f"{result.confidence_score * 100:.1f}% Confident",
                'color': '#00A651' if result.confidence_score > 0.8 else '#FFA500' if result.confidence_score > 0.6 else '#FF4444'
            },
            'complexity_gauge': {
                'value': result.complexity_score * 100,
                'label': 'Simple' if result.complexity_score < 0.3 else 'Moderate' if result.complexity_score < 0.7 else 'Complex'
            },
            'pattern_breakdown': {
                category: len(items) for category, items in result.detected_patterns.items() if items
            },
            'risk_levels': result.ai_insights.get('risk_assessment', {}),
            'linguistic_metrics': result.ai_insights.get('linguistic_analysis', {}),
            'alternative_classification': result.ai_insights.get('alternative_classifications', {})
        }
    
    def explain_classification(self, result: ClassificationResult) -> str:
        """
        Generate a human-readable explanation of the classification
        
        Returns a formatted explanation suitable for display
        """
        explanation = f"""
📊 **Classification Analysis**

**Primary Classification:** {result.primary_classification}
**Confidence:** {result.confidence_score * 100:.1f}%

**Why this classification?**
{result.reasoning}

**Key Evidence Found:**
"""
        for indicator in result.key_indicators[:5]:
            explanation += f"• {indicator}\n"
        
        if result.ai_insights:
            explanation += f"""
**AI Insights:**
• **Purpose:** {result.ai_insights.get('primary_purpose', 'Not determined')}
• **Key Message:** {result.ai_insights.get('key_message', 'Not determined')}
• **Target Audience:** {result.ai_insights.get('target_audience', 'Not determined')}
• **Emotional Impact:** {result.ai_insights.get('emotional_impact', 'Not determined')}
"""
        
        if result.urgency_level != 'LOW':
            explanation += f"\n⚠️ **Urgency Level:** {result.urgency_level}"
        
        if result.compliance_required:
            explanation += f"\n⚖️ **Compliance Required:** Yes"
        
        if result.customer_action_required:
            explanation += f"\n✅ **Customer Action Required:** Yes"
        
        return explanation
    
    def get_classification_summary(self, result: ClassificationResult) -> Dict[str, Any]:
        """Get a brief summary for quick display"""
        return {
            'type': result.primary_classification,
            'confidence': f"{result.confidence_score * 100:.0f}%",
            'urgency': result.urgency_level,
            'action_required': result.customer_action_required,
            'compliance': result.compliance_required,
            'tone': result.tone,
            'sentiment': result.sentiment,
            'top_indicators': result.key_indicators[:3]
        }

# Convenience function for easy use
def classify_document(document_text: str, api_key: Optional[str] = None) -> ClassificationResult:
    """
    Quick function to classify a document
    
    Args:
        document_text: The document to classify
        api_key: Optional API key (uses env variable if not provided)
        
    Returns:
        ClassificationResult with comprehensive analysis
    """
    classifier = AIDocumentClassifier(api_key)
    return classifier.classify_document(document_text)

# Export visualization-ready data
def get_classification_with_viz(document_text: str, api_key: Optional[str] = None) -> Tuple[ClassificationResult, Dict[str, Any]]:
    """
    Classify document and get visualization data
    
    Returns:
        Tuple of (ClassificationResult, visualization_data)
    """
    classifier = AIDocumentClassifier(api_key)
    result = classifier.classify_document(document_text)
    viz_data = classifier.get_visualization_data(result)
    return result, viz_data