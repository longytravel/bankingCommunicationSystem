"""
Simple Banking Sentiment Analyzer - Built for Streamlit
Clean, simple, and actually works!
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Make anthropic import optional
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("⚠️ Anthropic not available - will use pattern matching")

class SimpleSentimentAnalyzer:
    """
    Simplified sentiment analyzer that returns plain dictionaries
    Perfect for Streamlit session state
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Claude API"""
        self.api_key = api_key or os.getenv('CLAUDE_API_KEY')
        self.client = None
        
        if self.api_key and ANTHROPIC_AVAILABLE:
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
                self.model = "claude-3-sonnet-20240229"
                print("✅ Simple Sentiment Analyzer initialized with AI")
            except Exception as e:
                print(f"⚠️ No AI available: {e}")
                self.client = None
        else:
            print("⚠️ Running in pattern-matching mode (no AI)")
    
    def analyze(self, email_content: str, customer_name: str = "Customer") -> Dict[str, Any]:
        """
        Main analysis method - returns a simple dictionary
        
        Args:
            email_content: The email text to analyze
            customer_name: Customer name for context
            
        Returns:
            Simple dictionary with all results
        """
        print(f"🎯 Starting sentiment analysis for {customer_name}...")
        
        # Always return a valid dictionary structure
        result = self._create_empty_result()
        
        try:
            if self.client:
                # Use AI analysis
                ai_result = self._analyze_with_ai(email_content, customer_name)
                if ai_result:
                    result = ai_result
            else:
                # Use pattern-based fallback
                result = self._analyze_with_patterns(email_content)
            
            # Ensure all required fields exist
            result = self._ensure_complete_result(result)
            
            print(f"✅ Analysis complete. Score: {result['overall_score']}/100")
            return result
            
        except Exception as e:
            print(f"❌ Analysis error: {e}")
            # Return safe fallback
            return self._create_error_result(str(e))
    
    def _create_empty_result(self) -> Dict[str, Any]:
        """Create an empty but valid result structure"""
        return {
            # Core scores (what matters most)
            'overall_score': 0,  # -100 to 100
            'ready_to_send': False,
            'executive_summary': 'Analysis pending...',
            
            # Main assessments
            'sentiment': {
                'score': 0,
                'category': 'neutral',  # positive/neutral/negative
                'why': 'Analysis not yet complete'
            },
            
            'compliance': {
                'status': 'warning',  # pass/warning/fail
                'score': 50,
                'why': 'Compliance check pending'
            },
            
            'customer_impact': {
                'complaint_risk': 50,  # 0-100%
                'call_risk': 50,  # 0-100%
                'why': 'Impact assessment pending'
            },
            
            'readability': {
                'score': 50,  # 0-100
                'grade_level': 10,
                'why': 'Readability check pending'
            },
            
            # Issues and improvements
            'red_flags': [],  # List of critical issues
            'warnings': [],  # List of warnings
            'quick_wins': [],  # List of easy improvements
            
            # Metadata
            'timestamp': datetime.now().isoformat(),
            'method': 'pending'
        }
    
    def _analyze_with_ai(self, email_content: str, customer_name: str) -> Optional[Dict[str, Any]]:
        """Use Claude for intelligent analysis"""
        
        prompt = f"""Analyze this banking email for sentiment and compliance.

EMAIL:
{email_content}

CUSTOMER: {customer_name}

Provide a JSON response with this EXACT structure:
{{
    "overall_score": -100 to 100 (0 is neutral),
    "ready_to_send": true or false,
    "executive_summary": "2-3 sentence summary with reasoning",
    
    "sentiment": {{
        "score": -100 to 100,
        "category": "positive" or "neutral" or "negative",
        "why": "Clear explanation"
    }},
    
    "compliance": {{
        "status": "pass" or "warning" or "fail",
        "score": 0 to 100,
        "why": "Explanation"
    }},
    
    "customer_impact": {{
        "complaint_risk": 0 to 100,
        "call_risk": 0 to 100,
        "why": "Prediction reasoning"
    }},
    
    "readability": {{
        "score": 0 to 100,
        "grade_level": 1 to 18,
        "why": "Assessment"
    }},
    
    "red_flags": [
        {{
            "issue": "What's wrong",
            "impact": "Why it matters",
            "fix": "How to fix"
        }}
    ],
    
    "warnings": [
        {{
            "issue": "Potential problem",
            "impact": "Why consider",
            "fix": "Suggestion"
        }}
    ],
    
    "quick_wins": [
        {{
            "original": "Current text",
            "improved": "Better version",
            "why": "Reason"
        }}
    ]
}}

Focus on practical banking concerns: TCF compliance, clarity, and customer satisfaction."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text.strip()
            
            # Parse JSON response
            if '{' in content and '}' in content:
                start = content.index('{')
                end = content.rindex('}') + 1
                json_str = content[start:end]
                result = json.loads(json_str)
                result['method'] = 'ai_analysis'
                result['timestamp'] = datetime.now().isoformat()
                return result
                
        except Exception as e:
            print(f"AI analysis failed: {e}")
            
        return None
    
    def _analyze_with_patterns(self, email_content: str) -> Dict[str, Any]:
        """Simple pattern-based analysis as fallback"""
        
        content_lower = email_content.lower()
        
        # Count positive and negative indicators
        positive_words = ['pleased', 'happy', 'thank', 'appreciate', 'valued', 'benefit', 'opportunity']
        negative_words = ['unfortunately', 'regret', 'sorry', 'unable', 'charge', 'fee', 'penalty', 'decline']
        
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        # Calculate overall score
        if positive_count + negative_count > 0:
            score = int(((positive_count - negative_count) / (positive_count + negative_count)) * 100)
        else:
            score = 0
        
        # Determine category
        if score > 30:
            category = 'positive'
        elif score < -30:
            category = 'negative'
        else:
            category = 'neutral'
        
        # Check for issues
        has_fees = 'fee' in content_lower or 'charge' in content_lower
        is_too_long = len(email_content.split()) > 500
        
        # Build result
        result = {
            'overall_score': score,
            'ready_to_send': score >= -20 and not has_fees,
            'executive_summary': f"Email scores {score}/100 based on word analysis. {'Fee mentions detected - review needed.' if has_fees else 'No major issues found.'}",
            
            'sentiment': {
                'score': score,
                'category': category,
                'why': f"Found {positive_count} positive and {negative_count} negative indicators"
            },
            
            'compliance': {
                'status': 'warning' if has_fees else 'pass',
                'score': 60 if has_fees else 80,
                'why': 'Fee disclosure needs review' if has_fees else 'Basic compliance met'
            },
            
            'customer_impact': {
                'complaint_risk': 60 if has_fees else 20,
                'call_risk': 70 if has_fees else 30,
                'why': 'Fees often trigger customer contact' if has_fees else 'Low risk content'
            },
            
            'readability': {
                'score': 40 if is_too_long else 70,
                'grade_level': 12 if is_too_long else 9,
                'why': 'Email is too long' if is_too_long else 'Reasonable length'
            },
            
            'red_flags': [],
            'warnings': [],
            'quick_wins': [],
            
            'timestamp': datetime.now().isoformat(),
            'method': 'pattern_analysis'
        }
        
        # Add red flags if needed
        if has_fees:
            result['red_flags'].append({
                'issue': 'Fee mentioned without clear justification',
                'impact': 'May trigger complaints',
                'fix': 'Add clear explanation of value provided'
            })
        
        if is_too_long:
            result['warnings'].append({
                'issue': 'Email is too long',
                'impact': 'Customer may not read it fully',
                'fix': 'Reduce to under 300 words'
            })
        
        if negative_count > positive_count:
            result['warnings'].append({
                'issue': 'Negative tone detected',
                'impact': 'May upset customer',
                'fix': 'Balance with more positive language'
            })
        
        return result
    
    def _ensure_complete_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure result has all required fields"""
        
        # Get template
        template = self._create_empty_result()
        
        # Merge with template to ensure all fields exist
        for key, value in template.items():
            if key not in result:
                result[key] = value
            elif isinstance(value, dict) and isinstance(result.get(key), dict):
                # Merge nested dicts
                for subkey, subvalue in value.items():
                    if subkey not in result[key]:
                        result[key][subkey] = subvalue
        
        return result
    
    def _create_error_result(self, error_msg: str) -> Dict[str, Any]:
        """Create a result for when analysis fails"""
        
        result = self._create_empty_result()
        result.update({
            'overall_score': 0,
            'ready_to_send': False,
            'executive_summary': f'Analysis failed: {error_msg}. Manual review required.',
            'method': 'error',
            'red_flags': [{
                'issue': 'Analysis failed',
                'impact': error_msg,
                'fix': 'Retry analysis or review manually'
            }]
        })
        
        return result


# Convenience function that's Streamlit-friendly
def analyze_sentiment_simple(email_content: str, customer_name: str = "Customer") -> Dict[str, Any]:
    """
    Simple function to analyze sentiment - returns a plain dictionary
    
    Args:
        email_content: Email text to analyze
        customer_name: Customer name for context
        
    Returns:
        Dictionary with analysis results
    """
    analyzer = SimpleSentimentAnalyzer()
    return analyzer.analyze(email_content, customer_name)