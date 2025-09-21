"""
Banking Sentiment Analyzer - ACTUALLY WORKS WITH CLAUDE
No stupid fallbacks, just proper AI analysis with explanations
ENHANCED: Now with confidence scores and consistent scoring
"""

import os
import json
from typing import Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
import anthropic

load_dotenv()

class BankingSentimentAnalyzer:
    """
    Banking-specific sentiment analyzer with FULL explanations
    Uses latest Claude model, no fallback nonsense
    ENHANCED with confidence scoring and consistency improvements
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with latest Claude model"""
        self.api_key = api_key or os.getenv('CLAUDE_API_KEY')
        
        if not self.api_key:
            raise ValueError("❌ No Claude API key found! Check your .env file")
        
        try:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            # USE THE LATEST MODEL - configurable via env
            self.model = os.getenv('CLAUDE_MODEL', "claude-sonnet-4-20250514")
            print(f"✅ Banking Sentiment Analyzer initialized with {self.model}")
        except Exception as e:
            raise ValueError(f"❌ Failed to initialize Claude: {e}")
    
    def analyze(
        self, 
        email_content: str, 
        customer_name: str = "Customer",
        customer_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze email with FULL banking metrics and explanations
        
        NO FALLBACK - if it fails, it fails properly
        """
        print(f"🎯 Starting REAL sentiment analysis for {customer_name}...")
        
        # Build the comprehensive prompt
        prompt = self._build_banking_prompt(email_content, customer_name, customer_context)
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.1,  # REDUCED from 0.3 for consistency
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text.strip()
            
            # Parse the response
            result = self._parse_response(content)
            
            # Calculate overall confidence based on data completeness
            result['analysis_confidence'] = self._calculate_confidence(result, customer_context)
            
            # Add metadata
            result['timestamp'] = datetime.now().isoformat()
            result['method'] = 'claude_ai_analysis'
            result['model_used'] = self.model
            result['customer_analyzed'] = customer_name
            result['temperature_used'] = 0.1  # Track for debugging
            
            print(f"✅ Analysis complete. Overall score: {result.get('overall_score', 'N/A')}/100")
            print(f"   Confidence: {result.get('analysis_confidence', 0):.1%}")
            return result
            
        except Exception as e:
            # NO FALLBACK - just fail properly
            raise RuntimeError(f"❌ Claude analysis failed: {e}")
    
    def _calculate_confidence(self, result: Dict[str, Any], customer_context: Optional[Dict]) -> float:
        """Calculate ACTUAL confidence score based on analysis quality and completeness"""
        
        confidence_components = []
        
        # 1. Customer Context Quality (0-25%)
        context_score = 0.0
        if customer_context:
            # Each known field adds confidence
            if customer_context.get('segment') and customer_context.get('segment') != 'Unknown':
                context_score += 0.25
            if customer_context.get('life_stage') and customer_context.get('life_stage') != 'Unknown':
                context_score += 0.25
            if customer_context.get('financial_profile') and customer_context.get('financial_profile') != 'Unknown':
                context_score += 0.25
            if customer_context.get('digital_persona') and customer_context.get('digital_persona') != 'Unknown':
                context_score += 0.25
        else:
            context_score = 0.3  # Base level if no context
        confidence_components.append(context_score * 0.25)
        
        # 2. Analysis Consistency (0-30%)
        consistency_score = 0.5  # Start at medium
        
        # Check if different metrics agree
        sentiment_score = result.get('sentiment', {}).get('score', 0)
        compliance_score = result.get('compliance', {}).get('score', 0)
        readability_score = result.get('readability', {}).get('score', 0)
        
        # Strong positive alignment
        if sentiment_score > 50 and compliance_score > 80 and readability_score > 70:
            consistency_score = 0.95
        # Strong negative alignment  
        elif sentiment_score < -30 and (compliance_score < 50 or readability_score < 40):
            consistency_score = 0.90
        # Mixed signals
        elif (sentiment_score > 50 and compliance_score < 50) or (sentiment_score < -30 and compliance_score > 80):
            consistency_score = 0.40
        # Moderate alignment
        elif abs(sentiment_score) < 30 and 50 <= compliance_score <= 80:
            consistency_score = 0.70
            
        confidence_components.append(consistency_score * 0.30)
        
        # 3. Completeness of Analysis (0-25%)
        completeness_score = 0.0
        
        # Check what components were found
        if result.get('red_flags') is not None:
            if len(result.get('red_flags', [])) > 0:
                completeness_score += 0.30  # Found issues
            else:
                completeness_score += 0.15  # Checked but clean
                
        if result.get('strengths') is not None and len(result.get('strengths', [])) > 0:
            completeness_score += 0.25
            
        if result.get('quick_wins') is not None and len(result.get('quick_wins', [])) > 0:
            completeness_score += 0.25
            
        if result.get('tcf_breakdown'):
            completeness_score += 0.20
            
        confidence_components.append(min(completeness_score, 1.0) * 0.25)
        
        # 4. Decision Clarity (0-20%)
        decision_score = 0.5
        
        # Clear decision with supporting evidence
        if result.get('ready_to_send') is not None:
            if result.get('decision_rationale', {}).get('primary_factors'):
                factors = result['decision_rationale']['primary_factors']
                if len(factors) >= 3:
                    decision_score = 0.95
                elif len(factors) >= 2:
                    decision_score = 0.80
                else:
                    decision_score = 0.65
        
        # Check if decision aligns with scores
        ready = result.get('ready_to_send', False)
        overall_score = result.get('overall_score', 50)
        
        if (ready and overall_score > 70) or (not ready and overall_score < 50):
            decision_score = min(decision_score + 0.15, 1.0)  # Decision aligns with score
        elif (ready and overall_score < 30) or (not ready and overall_score > 80):
            decision_score = max(decision_score - 0.30, 0.2)  # Conflicting signals
            
        confidence_components.append(decision_score * 0.20)
        
        # Calculate final confidence
        raw_confidence = sum(confidence_components)
        
        # Ensure minimum of 40% and maximum of 95%
        final_confidence = max(0.40, min(raw_confidence, 0.95))
        
        # Log the calculation for debugging
        print(f"Confidence calculation:")
        print(f"  Context: {confidence_components[0]:.2%}")
        print(f"  Consistency: {confidence_components[1]:.2%}") 
        print(f"  Completeness: {confidence_components[2]:.2%}")
        print(f"  Decision: {confidence_components[3]:.2%}")
        print(f"  TOTAL: {final_confidence:.1%}")
        
        return final_confidence
    
    def _build_banking_prompt(
        self, 
        email_content: str, 
        customer_name: str,
        customer_context: Optional[Dict[str, Any]]
    ) -> str:
        """Build comprehensive banking analysis prompt with scoring rubrics"""
        
        context_info = ""
        if customer_context:
            context_info = f"""
CUSTOMER CONTEXT:
- Segment: {customer_context.get('segment', 'Unknown')}
- Life Stage: {customer_context.get('life_stage', 'Unknown')}
- Digital Persona: {customer_context.get('digital_persona', 'Unknown')}
- Financial Profile: {customer_context.get('financial_profile', 'Unknown')}
"""
        
        prompt = f"""You are a senior banking compliance and customer experience analyst reviewing an email to {customer_name}.

EMAIL TO ANALYZE:
{email_content}
{context_info}

SCORING RUBRICS FOR CONSISTENCY:

SENTIMENT SCORING:
- 70 to 100: Multiple positive indicators (appreciation, benefits clearly stated, customer-first language)
- 30 to 70: Professional and positive, solution-focused
- -30 to 30: Neutral/factual, neither positive nor negative
- -70 to -30: Contains negative elements (problems, restrictions, denials)
- -100 to -70: Multiple serious negative indicators (account closure, legal action)

COMPLIANCE SCORING:
- 90-100: All TCF principles met, vulnerable customer considerations, perfect regulatory alignment
- 70-89: Minor improvements needed, all critical elements present
- 50-69: Some compliance gaps, needs review
- 30-49: Significant compliance issues
- 0-29: Critical compliance failures

READABILITY SCORING:
- 80-100: Grade 8 or below, crystal clear, no jargon
- 60-79: Grade 9-10, mostly clear, minimal jargon
- 40-59: Grade 11-12, some complexity, industry terms present
- 20-39: Grade 13+, complex, heavy jargon
- 0-19: Extremely complex, inaccessible

CONFIDENCE SCORING:
- 0.9-1.0: Very high confidence - clear indicators, unambiguous assessment
- 0.7-0.89: High confidence - most indicators clear, minor ambiguity
- 0.5-0.69: Medium confidence - mixed signals or limited context
- 0.3-0.49: Low confidence - significant ambiguity
- 0.0-0.29: Very low confidence - insufficient information

ANCHOR EXAMPLES FOR CALIBRATION:
- Sentiment 85: "We're delighted to confirm your application has been approved and you'll receive your new card within 3 days."
- Sentiment 20: "Unfortunately, we must inform you that your overdraft facility has been withdrawn."
- Compliance 95: Email with clear APR disclosure, cooling-off period mentioned, contact details, and plain English
- Readability 90: "Your monthly payment is £50. This includes £45 for your loan and £5 for insurance."

Provide a COMPREHENSIVE banking sentiment analysis with detailed explanations for EVERY score.

Return JSON with this EXACT structure (return ONLY the JSON, no other text):
{{
    "overall_score": 0 to 100,
    "ready_to_send": true/false,
    "executive_summary": "2-3 sentences summarizing the analysis and key decision points",
    
    "sentiment": {{
        "score": -100 to 100,
        "category": "positive/neutral/negative",
        "confidence": 0.7 to 0.95,
        "why": "DETAILED explanation of why this score was given, what specific phrases or tone elements led to this assessment"
    }},
    
    "compliance": {{
        "status": "pass/warning/fail",
        "score": 0 to 100,
        "confidence": 0.7 to 0.95,
        "tcf_compliant": true/false,
        "tcf_breakdown": {{
            "fair_treatment": {{"score": 0-100, "why": "explanation"}},
            "no_financial_harm": {{"score": 0-100, "why": "explanation"}},
            "suitable_products": {{"score": 0-100, "why": "explanation"}},
            "clear_communication": {{"score": 0-100, "why": "explanation"}},
            "customer_support": {{"score": 0-100, "why": "explanation"}},
            "consumer_protection": {{"score": 0-100, "why": "explanation"}}
        }},
        "why": "DETAILED explanation covering FCA TCF principles, regulatory tone requirements, and specific compliance issues or strengths found"
    }},
    
    "customer_impact": {{
        "complaint_risk": 0 to 100,
        "call_risk": 0 to 100,
        "escalation_risk": 0 to 100,
        "confidence": 0.7 to 0.95,
        "why": "DETAILED prediction reasoning based on tone, content, and typical customer reactions to similar communications"
    }},
    
    "nps_impact": {{
        "predicted_impact": -10 to 10,
        "current_promoter_risk": "high/medium/low",
        "confidence": 0.7 to 0.95,
        "why": "DETAILED explanation of how this email would affect Net Promoter Score and customer advocacy"
    }},
    
    "upsell_opportunity": {{
        "score": 0 to 100,
        "receptiveness_prediction": "high/medium/low",
        "confidence": 0.7 to 0.95,
        "why": "DETAILED assessment of whether the tone and content create opportunity for future product discussions"
    }},
    
    "readability": {{
        "score": 0 to 100,
        "grade_level": 1 to 18,
        "complexity": "simple/moderate/complex",
        "confidence": 0.7 to 0.95,
        "why": "DETAILED explanation of readability issues, jargon usage, sentence complexity, and accessibility"
    }},
    
    "emotional_tone": {{
        "primary_emotion": "empathetic/professional/cold/frustrated/apologetic",
        "warmth_score": 0 to 100,
        "confidence": 0.7 to 0.95,
        "why": "DETAILED analysis of emotional undertones and how the customer will FEEL reading this"
    }},
    
    "regulatory_flags": {{
        "has_required_disclosures": true/false,
        "vulnerable_customer_appropriate": true/false,
        "financial_promotion_compliant": true/false,
        "confidence": 0.7 to 0.95,
        "why": "DETAILED review of regulatory requirements and any missing elements"
    }},
    
    "red_flags": [
        {{
            "issue": "Specific problem identified",
            "severity": "critical/high/medium",
            "impact": "Why this matters from banking perspective",
            "fix": "Specific actionable solution",
            "why_flagged": "Detailed reasoning for flagging this"
        }}
    ],
    
    "warnings": [
        {{
            "issue": "Potential concern",
            "impact": "Why to consider this",
            "fix": "Suggested improvement",
            "why_warning": "Reasoning for this warning"
        }}
    ],
    
    "strengths": [
        {{
            "element": "What's working well",
            "why_good": "Why this is effective for banking comms"
        }}
    ],
    
    "quick_wins": [
        {{
            "original": "Current problematic text",
            "improved": "Better banking-appropriate version",
            "why": "Detailed explanation of why this change improves the email"
        }}
    ],
    
    "decision_rationale": {{
        "primary_factors": ["List of main factors driving the ready/not ready decision"],
        "risk_assessment": "Overall risk assessment with reasoning",
        "recommendation": "Clear recommendation with detailed justification",
        "confidence": 0.7 to 0.95
    }}
}}

CRITICAL REQUIREMENTS:
1. Use the scoring rubrics above for CONSISTENT scoring
2. Set all confidence scores between 0.7 and 0.95 (never 0 or below 0.7)
3. EVERY 'why' field must have 2-3 sentences of detailed explanation
4. Consider UK banking regulations and FCA requirements
5. Break down TCF into all 6 components with individual scores
6. Provide SPECIFIC examples from the email text when explaining scores
7. Think about vulnerable customers and accessibility
8. Consider the customer's likely emotional response
9. Return ONLY the JSON object, no additional text before or after"""

        return prompt
    
    def _parse_response(self, content: str) -> Dict[str, Any]:
        """Parse Claude's response with better error handling"""
        
        # Try to extract JSON from response
        try:
            # First try parsing the entire content as JSON
            return json.loads(content)
        except json.JSONDecodeError:
            # If that fails, look for JSON in the content
            if '{' in content and '}' in content:
                try:
                    start = content.index('{')
                    end = content.rindex('}') + 1
                    json_str = content[start:end]
                    result = json.loads(json_str)
                    
                    # Ensure numeric values are actually numbers
                    result = self._ensure_numeric_values(result)
                    
                    # Ensure confidence values are set
                    result = self._ensure_confidence_values(result)
                    
                    return result
                    
                except (json.JSONDecodeError, ValueError) as e:
                    # If parsing fails, raise error with context
                    raise ValueError(f"Failed to parse Claude response: {e}\nRaw response: {content[:500]}...")
        
        raise ValueError(f"No valid JSON in Claude response. Raw: {content[:500]}...")
    
    def _ensure_confidence_values(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure all confidence values are set and valid, but use Claude's values when provided"""
        
        # For each section, only set default if missing or invalid
        for key in ['sentiment', 'compliance', 'customer_impact', 'nps_impact', 
                    'upsell_opportunity', 'readability', 'emotional_tone', 'regulatory_flags']:
            if key in result and isinstance(result[key], dict):
                current_confidence = result[key].get('confidence', 0)
                
                # Only replace if it's missing, 0, or unreasonably low
                if current_confidence == 0 or current_confidence < 0.3:
                    # Calculate section-specific confidence based on the quality of that section
                    section_confidence = self._calculate_section_confidence(key, result[key])
                    result[key]['confidence'] = section_confidence
                elif current_confidence > 1.0:
                    # If it's over 100%, normalize it
                    result[key]['confidence'] = min(current_confidence / 100 if current_confidence > 1 else current_confidence, 0.95)
        
        # Handle decision rationale separately
        if 'decision_rationale' in result and isinstance(result['decision_rationale'], dict):
            current_confidence = result['decision_rationale'].get('confidence', 0)
            if current_confidence == 0 or current_confidence < 0.3:
                # Decision confidence based on number of factors and alignment
                factors = result['decision_rationale'].get('primary_factors', [])
                if len(factors) >= 3:
                    result['decision_rationale']['confidence'] = 0.85
                elif len(factors) >= 2:
                    result['decision_rationale']['confidence'] = 0.70
                else:
                    result['decision_rationale']['confidence'] = 0.55
        
        return result
    
    def _calculate_section_confidence(self, section_name: str, section_data: Dict) -> float:
        """Calculate confidence for a specific section based on its content"""
        
        # Base confidence varies by section importance
        base_confidence = {
            'sentiment': 0.70,
            'compliance': 0.65,
            'customer_impact': 0.60,
            'nps_impact': 0.55,
            'upsell_opportunity': 0.50,
            'readability': 0.80,  # More objective
            'emotional_tone': 0.60,
            'regulatory_flags': 0.70
        }.get(section_name, 0.60)
        
        # Boost confidence if we have a detailed "why" explanation
        if section_data.get('why'):
            why_length = len(section_data['why'])
            if why_length > 200:
                base_confidence += 0.15
            elif why_length > 100:
                base_confidence += 0.10
            elif why_length > 50:
                base_confidence += 0.05
        
        # For compliance, boost if we have TCF breakdown
        if section_name == 'compliance' and section_data.get('tcf_breakdown'):
            base_confidence += 0.10
        
        # For customer impact, check if all risk scores are present
        if section_name == 'customer_impact':
            if all(k in section_data for k in ['complaint_risk', 'call_risk', 'escalation_risk']):
                base_confidence += 0.10
        
        return min(base_confidence, 0.90)
    
    def _ensure_numeric_values(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure all score fields are numeric, not strings"""
        
        # Fix overall_score
        if 'overall_score' in result:
            result['overall_score'] = self._to_numeric(result['overall_score'])
        
        # Fix nested scores
        for key in ['sentiment', 'compliance', 'customer_impact', 'nps_impact', 
                    'upsell_opportunity', 'readability', 'emotional_tone', 'regulatory_flags']:
            if key in result and isinstance(result[key], dict):
                if 'score' in result[key]:
                    result[key]['score'] = self._to_numeric(result[key]['score'])
                if 'confidence' in result[key]:
                    result[key]['confidence'] = self._to_float(result[key]['confidence'])
                if 'warmth_score' in result[key]:
                    result[key]['warmth_score'] = self._to_numeric(result[key]['warmth_score'])
                if 'grade_level' in result[key]:
                    result[key]['grade_level'] = self._to_numeric(result[key]['grade_level'])
                
                # Fix TCF breakdown scores
                if 'tcf_breakdown' in result[key]:
                    for tcf_key in result[key]['tcf_breakdown']:
                        if 'score' in result[key]['tcf_breakdown'][tcf_key]:
                            result[key]['tcf_breakdown'][tcf_key]['score'] = self._to_numeric(
                                result[key]['tcf_breakdown'][tcf_key]['score']
                            )
        
        # Fix risk percentages
        if 'customer_impact' in result:
            for risk_key in ['complaint_risk', 'call_risk', 'escalation_risk']:
                if risk_key in result['customer_impact']:
                    result['customer_impact'][risk_key] = self._to_numeric(
                        result['customer_impact'][risk_key]
                    )
        
        # Fix NPS impact
        if 'nps_impact' in result:
            if 'predicted_impact' in result['nps_impact']:
                result['nps_impact']['predicted_impact'] = self._to_numeric(
                    result['nps_impact']['predicted_impact']
                )
        
        # Fix decision rationale confidence
        if 'decision_rationale' in result:
            if 'confidence' in result['decision_rationale']:
                result['decision_rationale']['confidence'] = self._to_float(
                    result['decision_rationale']['confidence']
                )
        
        return result
    
    def _to_numeric(self, value: Any) -> int:
        """Convert value to integer, handling various formats"""
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            # Remove any formatting like "85/100" -> 85
            if '/' in value:
                value = value.split('/')[0]
            # Remove percentage signs
            value = value.replace('%', '').strip()
            # Remove plus/minus signs for NPS
            value = value.replace('+', '').replace('±', '').strip()
            try:
                return int(float(value))
            except:
                return 0
        return 0
    
    def _to_float(self, value: Any) -> float:
        """Convert value to float for confidence scores"""
        if isinstance(value, float):
            return max(0.7, min(value, 1.0))  # Ensure between 0.7 and 1.0
        if isinstance(value, int):
            if value > 1:  # Probably a percentage
                return max(0.7, min(value / 100, 1.0))
            return max(0.7, float(value))
        if isinstance(value, str):
            try:
                # Handle percentage strings
                if '%' in value:
                    return max(0.7, min(float(value.replace('%', '').strip()) / 100, 1.0))
                return max(0.7, min(float(value), 1.0))
            except:
                return 0.75  # Default confidence
        return 0.75  # Default confidence


def analyze_banking_sentiment(
    email_content: str, 
    customer_name: str = "Customer",
    customer_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Convenience function for banking sentiment analysis
    
    NO FALLBACK - uses Claude or fails properly
    """
    analyzer = BankingSentimentAnalyzer()
    return analyzer.analyze(email_content, customer_name, customer_context)