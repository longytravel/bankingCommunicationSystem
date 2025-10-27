"""
Banking Sentiment Analyzer - ACTUALLY WORKS WITH CLAUDE
No stupid fallbacks, just proper AI analysis with explanations
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
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with latest Claude model"""
        self.api_key = api_key or os.getenv('CLAUDE_API_KEY')
        
        if not self.api_key:
            raise ValueError("❌ No Claude API key found! Check your .env file")
        
        try:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            # USE THE LATEST MODEL
            self.model = "claude-haiku-4-5-20251001"  # Latest available model
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
                max_tokens=3000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text.strip()
            
            # Parse the response
            result = self._parse_response(content)
            
            # Add metadata
            result['timestamp'] = datetime.now().isoformat()
            result['method'] = 'claude_ai_analysis'
            result['model_used'] = self.model
            result['customer_analyzed'] = customer_name
            
            print(f"✅ Analysis complete. Overall score: {result.get('overall_score', 'N/A')}/100")
            return result
            
        except Exception as e:
            # NO FALLBACK - just fail properly
            raise RuntimeError(f"❌ Claude analysis failed: {e}")
    
    def _build_banking_prompt(
        self, 
        email_content: str, 
        customer_name: str,
        customer_context: Optional[Dict[str, Any]]
    ) -> str:
        """Build comprehensive banking analysis prompt"""
        
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

Provide a COMPREHENSIVE banking sentiment analysis with detailed explanations for EVERY score.

Return JSON with this EXACT structure:
{{
    "overall_score": -100 to 100,
    "ready_to_send": true/false,
    "executive_summary": "2-3 sentences summarizing the analysis and key decision points",
    
    "sentiment": {{
        "score": -100 to 100,
        "category": "positive/neutral/negative",
        "why": "DETAILED explanation of why this score was given, what specific phrases or tone elements led to this assessment"
    }},
    
    "compliance": {{
        "status": "pass/warning/fail",
        "score": 0-100,
        "tcf_compliant": true/false,
        "why": "DETAILED explanation covering FCA TCF principles, regulatory tone requirements, and specific compliance issues or strengths found"
    }},
    
    "customer_impact": {{
        "complaint_risk": 0-100,
        "call_risk": 0-100,
        "escalation_risk": 0-100,
        "why": "DETAILED prediction reasoning based on tone, content, and typical customer reactions to similar communications"
    }},
    
    "nps_impact": {{
        "predicted_impact": -10 to +10,
        "current_promoter_risk": "high/medium/low",
        "why": "DETAILED explanation of how this email would affect Net Promoter Score and customer advocacy"
    }},
    
    "upsell_opportunity": {{
        "score": 0-100,
        "receptiveness_prediction": "high/medium/low",
        "why": "DETAILED assessment of whether the tone and content create opportunity for future product discussions"
    }},
    
    "readability": {{
        "score": 0-100,
        "grade_level": 1-18,
        "complexity": "simple/moderate/complex",
        "why": "DETAILED explanation of readability issues, jargon usage, sentence complexity, and accessibility"
    }},
    
    "emotional_tone": {{
        "primary_emotion": "empathetic/professional/cold/frustrated/apologetic",
        "warmth_score": 0-100,
        "why": "DETAILED analysis of emotional undertones and how the customer will FEEL reading this"
    }},
    
    "regulatory_flags": {{
        "has_required_disclosures": true/false,
        "vulnerable_customer_appropriate": true/false,
        "financial_promotion_compliant": true/false,
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
        "recommendation": "Clear recommendation with detailed justification"
    }}
}}

CRITICAL REQUIREMENTS:
1. EVERY 'why' field must have 2-3 sentences of detailed explanation
2. Consider UK banking regulations and FCA requirements
3. Assess from both compliance AND customer experience perspectives
4. Provide SPECIFIC examples from the email text when explaining scores
5. Think about vulnerable customers and accessibility
6. Consider the customer's likely emotional response
7. NO generic responses - be specific to THIS email"""

        return prompt
    
    def _parse_response(self, content: str) -> Dict[str, Any]:
        """Parse Claude's response"""
        
        # Extract JSON from response
        if '{' in content and '}' in content:
            try:
                start = content.index('{')
                end = content.rindex('}') + 1
                json_str = content[start:end]
                return json.loads(json_str)
            except (json.JSONDecodeError, ValueError) as e:
                # If parsing fails, raise error - NO FALLBACK
                raise ValueError(f"Failed to parse Claude response: {e}")
        
        raise ValueError("No valid JSON in Claude response")


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