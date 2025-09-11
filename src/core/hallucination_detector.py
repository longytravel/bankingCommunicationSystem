"""
Hallucination Detector Module - AI-Powered Detection of Fabricated Content
Uses Claude Sonnet 4 to identify hallucinations in generated content
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

class HallucinationCategory(Enum):
    """Categories of hallucinations"""
    PERSON_NAME = "person_name"      # Made-up names of people
    DATE_TIME = "date_time"          # Specific dates/times not in source
    LOCATION = "location"            # Places, branches, addresses
    FACT = "fact"                    # Customer facts not in data
    EVENT = "event"                  # Life events not mentioned
    RELATIONSHIP = "relationship"     # Family/advisor relationships
    FINANCIAL = "financial"          # Amounts, products not mentioned
    HISTORICAL = "historical"        # Past interactions, promises
    OTHER = "other"                  # Other fabrications

class SeverityLevel(Enum):
    """Severity levels for hallucinations"""
    HIGH = "high"        # Could cause compliance issues or confusion
    MEDIUM = "medium"    # Incorrect but not critical
    LOW = "low"         # Minor embellishments

@dataclass
class HallucinationFinding:
    """Single hallucination finding"""
    text: str                    # The hallucinated text
    category: HallucinationCategory  # Type of hallucination
    severity: SeverityLevel      # How serious is this
    context: str                 # Surrounding text for context
    channel: str                 # Which channel (email, sms, letter, voice)
    explanation: str             # Why this is likely hallucinated
    suggested_fix: str           # How to fix it
    confidence: float            # How confident we are this is hallucinated (0-1)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'text': self.text,
            'category': self.category.value,
            'severity': self.severity.value,
            'context': self.context,
            'channel': self.channel,
            'explanation': self.explanation,
            'suggested_fix': self.suggested_fix,
            'confidence': self.confidence
        }

@dataclass
class HallucinationReport:
    """Complete hallucination analysis report"""
    total_hallucinations: int
    findings: List[HallucinationFinding]
    risk_score: float           # 0-1 scale overall risk
    summary: str                 # Executive summary
    recommendations: List[str]   # Overall recommendations
    analysis_confidence: float   # How confident in the analysis
    processing_time: float      # Time taken to analyze
    channels_analyzed: List[str] # Which channels were checked
    model_used: str             # Which Claude model was used
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'total_hallucinations': self.total_hallucinations,
            'findings': [f.to_dict() for f in self.findings],
            'risk_score': self.risk_score,
            'summary': self.summary,
            'recommendations': self.recommendations,
            'analysis_confidence': self.analysis_confidence,
            'processing_time': self.processing_time,
            'channels_analyzed': self.channels_analyzed,
            'model_used': self.model_used
        }
    
    def get_high_severity_findings(self) -> List[HallucinationFinding]:
        """Get only high severity findings"""
        return [f for f in self.findings if f.severity == SeverityLevel.HIGH]
    
    def get_findings_by_channel(self, channel: str) -> List[HallucinationFinding]:
        """Get findings for a specific channel"""
        return [f for f in self.findings if f.channel == channel]
    
    def get_findings_by_category(self, category: HallucinationCategory) -> List[HallucinationFinding]:
        """Get findings by category"""
        return [f for f in self.findings if f.category == category]

class HallucinationDetector:
    """
    AI-Powered Hallucination Detector
    Uses Claude Sonnet 4 to identify fabricated content in generated communications
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Claude API"""
        self.api_key = api_key or os.getenv('CLAUDE_API_KEY')
        self.client = None
        
        if self.api_key:
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
                # Use Claude Sonnet 4 - update with actual model name when available
                self.model = "claude-3-5-sonnet-20241022"  # Will update to claude-sonnet-4-[date] when available
                print("✅ Hallucination Detector initialized with Claude AI")
            except Exception as e:
                print(f"⚠️ Failed to initialize Claude client: {e}")
                self.client = None
        else:
            print("⚠️ Hallucination Detector running without AI (limited functionality)")
    
    def detect_hallucinations(
        self,
        generated_content: Dict[str, str],
        original_letter: str,
        customer_data: Dict[str, Any],
        shared_context: Optional[Any] = None
    ) -> HallucinationReport:
        """
        Main method to detect hallucinations in generated content
        
        Args:
            generated_content: Dict with keys 'email', 'sms', 'letter', 'voice' containing generated text
            original_letter: The original letter that was personalized
            customer_data: The customer data used for personalization
            shared_context: Optional SharedContext object with additional intelligence
            
        Returns:
            HallucinationReport with all findings and recommendations
        """
        start_time = datetime.now()
        
        print("🔍 Starting hallucination detection...")
        
        # Build truth database from source data
        truth_database = self._build_truth_database(original_letter, customer_data, shared_context)
        
        # Analyze each channel
        all_findings = []
        channels_analyzed = []
        
        for channel, content in generated_content.items():
            if content and len(content.strip()) > 0:
                print(f"  Analyzing {channel}...")
                findings = self._analyze_channel(
                    channel=channel,
                    content=content,
                    truth_database=truth_database,
                    original_letter=original_letter,
                    customer_data=customer_data
                )
                all_findings.extend(findings)
                channels_analyzed.append(channel)
        
        # Calculate risk score and generate recommendations
        risk_score = self._calculate_risk_score(all_findings)
        recommendations = self._generate_recommendations(all_findings)
        summary = self._generate_summary(all_findings, risk_score)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        print(f"✅ Hallucination detection complete in {processing_time:.2f}s")
        print(f"   Found {len(all_findings)} potential hallucinations")
        print(f"   Risk score: {risk_score:.2%}")
        
        return HallucinationReport(
            total_hallucinations=len(all_findings),
            findings=all_findings,
            risk_score=risk_score,
            summary=summary,
            recommendations=recommendations,
            analysis_confidence=0.85 if self.client else 0.5,
            processing_time=processing_time,
            channels_analyzed=channels_analyzed,
            model_used=self.model if self.client else "pattern_matching"
        )
    
    def _build_truth_database(
        self,
        original_letter: str,
        customer_data: Dict[str, Any],
        shared_context: Optional[Any]
    ) -> Dict[str, Any]:
        """Build a database of verifiable facts from source data"""
        
        truth_db = {
            'customer_facts': {},
            'letter_facts': {},
            'mentioned_names': [],
            'mentioned_dates': [],
            'mentioned_locations': [],
            'mentioned_amounts': [],
            'mentioned_events': []
        }
        
        # Extract customer facts
        for key, value in customer_data.items():
            if value not in [None, '', 'None', 'none', 'N/A', 'n/a']:
                truth_db['customer_facts'][key] = str(value)
        
        # Extract names from customer data
        if 'name' in customer_data:
            truth_db['mentioned_names'].append(customer_data['name'])
            # Add first/last name variations
            name_parts = str(customer_data.get('name', '')).split()
            truth_db['mentioned_names'].extend(name_parts)
        
        # Extract facts from original letter using simple pattern matching
        # This is a fallback when AI is not available
        truth_db['letter_facts']['full_text'] = original_letter
        
        # Extract dates from letter
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}\b'
        ]
        for pattern in date_patterns:
            matches = re.finditer(pattern, original_letter, re.IGNORECASE)
            for match in matches:
                truth_db['mentioned_dates'].append(match.group())
        
        # Extract amounts
        amount_pattern = r'[£$€]\s*\d+(?:,\d{3})*(?:\.\d{2})?'
        amounts = re.findall(amount_pattern, original_letter)
        truth_db['mentioned_amounts'].extend(amounts)
        
        # Add shared context intelligence if available
        if shared_context:
            # Add any validated personalization hooks
            if hasattr(shared_context, 'customer_insights'):
                insights = shared_context.customer_insights
                if hasattr(insights, 'special_factors'):
                    truth_db['mentioned_events'].extend(insights.special_factors)
        
        return truth_db
    
    def _analyze_channel(
        self,
        channel: str,
        content: str,
        truth_database: Dict[str, Any],
        original_letter: str,
        customer_data: Dict[str, Any]
    ) -> List[HallucinationFinding]:
        """Analyze a single channel for hallucinations"""
        
        if self.client:
            # Use AI for intelligent detection
            return self._ai_detect_hallucinations(
                channel, content, truth_database, original_letter, customer_data
            )
        else:
            # Fallback to pattern matching
            return self._pattern_detect_hallucinations(
                channel, content, truth_database
            )
    
    def _ai_detect_hallucinations(
        self,
        channel: str,
        content: str,
        truth_database: Dict[str, Any],
        original_letter: str,
        customer_data: Dict[str, Any]
    ) -> List[HallucinationFinding]:
        """Use Claude AI to detect hallucinations intelligently"""
        
        # Prepare customer data summary
        customer_summary = json.dumps(customer_data, indent=2)
        
        # Build the detection prompt
        prompt = f"""You are a hallucination detector for bank communications. Your job is to identify ANY information in the generated content that is NOT present in the source data.

SOURCE DATA - This is the ONLY truth:

ORIGINAL LETTER:
{original_letter}

CUSTOMER DATA (complete):
{customer_summary}

GENERATED {channel.upper()} CONTENT TO ANALYZE:
{content}

CRITICAL INSTRUCTIONS:
1. Compare EVERY claim, name, date, fact, and detail in the generated content against the source data
2. If something is NOT explicitly in the source data, it's a hallucination
3. Pay special attention to:
   - Names of people (advisors, staff, family members)
   - Specific dates or time periods
   - Locations (branches, streets, regions)
   - Customer facts (years with bank, account details)
   - Life events (deaths, marriages, moves)
   - Any specific claims about the customer

Find ALL hallucinations and return as JSON array:
[
    {{
        "text": "exact hallucinated text from the generated content",
        "category": "person_name|date_time|location|fact|event|relationship|financial|historical|other",
        "severity": "high|medium|low",
        "context": "the full sentence containing the hallucination",
        "explanation": "why this is a hallucination (what's missing from source)",
        "suggested_fix": "specific suggestion to fix this",
        "confidence": 0.0-1.0
    }}
]

Be THOROUGH. Even small fabrications matter. If the generated content mentions ANYTHING not in the source data, flag it.
Return ONLY the JSON array, no other text."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=3000,
                temperature=0.2,  # Low temperature for accuracy
                messages=[{"role": "user", "content": prompt}]
            )
            
            content_text = response.content[0].text.strip()
            
            # Parse JSON response
            findings = []
            if content_text:
                try:
                    # Extract JSON array from response
                    if '[' in content_text:
                        json_start = content_text.index('[')
                        json_end = content_text.rindex(']') + 1
                        json_str = content_text[json_start:json_end]
                        findings_data = json.loads(json_str)
                        
                        # Convert to HallucinationFinding objects
                        for finding in findings_data:
                            findings.append(HallucinationFinding(
                                text=finding.get('text', ''),
                                category=HallucinationCategory(finding.get('category', 'other')),
                                severity=SeverityLevel(finding.get('severity', 'medium')),
                                context=finding.get('context', ''),
                                channel=channel,
                                explanation=finding.get('explanation', ''),
                                suggested_fix=finding.get('suggested_fix', ''),
                                confidence=float(finding.get('confidence', 0.8))
                            ))
                except json.JSONDecodeError as e:
                    print(f"Failed to parse AI response: {e}")
            
            return findings
            
        except Exception as e:
            print(f"AI detection error: {e}")
            # Fallback to pattern matching
            return self._pattern_detect_hallucinations(channel, content, truth_database)
    
    def _pattern_detect_hallucinations(
        self,
        channel: str,
        content: str,
        truth_database: Dict[str, Any]
    ) -> List[HallucinationFinding]:
        """Fallback pattern-based detection when AI is not available"""
        
        findings = []
        content_lower = content.lower()
        
        # Check for common hallucination patterns
        
        # 1. Check for advisor/staff names not in source
        advisor_patterns = [
            r'\b(?:Mr\.|Mrs\.|Ms\.|Dr\.)\s+([A-Z][a-z]+)',
            r'your (?:advisor|manager|representative),?\s+([A-Z][a-z]+)',
            r'([A-Z][a-z]+),?\s+your (?:advisor|manager|representative)'
        ]
        
        for pattern in advisor_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                name = match.group(1) if match.group(1) else match.group(0)
                if name not in truth_database['mentioned_names']:
                    findings.append(HallucinationFinding(
                        text=match.group(0),
                        category=HallucinationCategory.PERSON_NAME,
                        severity=SeverityLevel.HIGH,
                        context=self._get_context(content, match.start(), match.end()),
                        channel=channel,
                        explanation=f"The name '{name}' does not appear in source data",
                        suggested_fix=f"Replace with 'your advisor' or 'our team'",
                        confidence=0.9
                    ))
        
        # 2. Check for specific branch/location names
        location_patterns = [
            r'at our ([A-Z][a-z]+\s*(?:Street|Road|Avenue|Branch|Office))',
            r'(?:visit|at|from) our ([A-Z][a-z]+) (?:branch|location|office)'
        ]
        
        for pattern in location_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                location = match.group(1)
                if location not in original_letter and location not in str(truth_database):
                    findings.append(HallucinationFinding(
                        text=match.group(0),
                        category=HallucinationCategory.LOCATION,
                        severity=SeverityLevel.MEDIUM,
                        context=self._get_context(content, match.start(), match.end()),
                        channel=channel,
                        explanation=f"Location '{location}' not mentioned in source data",
                        suggested_fix="Remove specific location or use 'your local branch'",
                        confidence=0.85
                    ))
        
        # 3. Check for specific years/dates not in source
        year_pattern = r'\b(1\d{3}|20\d{2})\b'
        year_matches = re.finditer(year_pattern, content)
        for match in year_matches:
            year = match.group(0)
            if year not in original_letter and year not in str(truth_database):
                findings.append(HallucinationFinding(
                    text=year,
                    category=HallucinationCategory.DATE_TIME,
                    severity=SeverityLevel.MEDIUM,
                    context=self._get_context(content, match.start(), match.end()),
                    channel=channel,
                    explanation=f"Year {year} not found in source data",
                    suggested_fix="Verify or remove specific year",
                    confidence=0.7
                ))
        
        return findings
    
    def _get_context(self, text: str, start: int, end: int, context_chars: int = 100) -> str:
        """Get surrounding context for a match"""
        context_start = max(0, start - context_chars)
        context_end = min(len(text), end + context_chars)
        return text[context_start:context_end].strip()
    
    def _calculate_risk_score(self, findings: List[HallucinationFinding]) -> float:
        """Calculate overall risk score based on findings"""
        
        if not findings:
            return 0.0
        
        # Weight by severity
        severity_weights = {
            SeverityLevel.HIGH: 1.0,
            SeverityLevel.MEDIUM: 0.5,
            SeverityLevel.LOW: 0.2
        }
        
        total_weight = 0
        for finding in findings:
            total_weight += severity_weights[finding.severity] * finding.confidence
        
        # Normalize to 0-1 scale (cap at 1.0)
        risk_score = min(1.0, total_weight / 10.0)
        
        return risk_score
    
    def _generate_recommendations(self, findings: List[HallucinationFinding]) -> List[str]:
        """Generate recommendations based on findings"""
        
        recommendations = []
        
        # Check for systemic issues
        categories = {}
        for finding in findings:
            if finding.category not in categories:
                categories[finding.category] = 0
            categories[finding.category] += 1
        
        # Generate recommendations by category
        if HallucinationCategory.PERSON_NAME in categories:
            recommendations.append(
                "Avoid using specific staff names unless verified in source data. Use generic terms like 'your advisor' or 'our team'."
            )
        
        if HallucinationCategory.LOCATION in categories:
            recommendations.append(
                "Remove specific branch or location names. Use 'your local branch' or 'Lloyds Bank' instead."
            )
        
        if HallucinationCategory.DATE_TIME in categories:
            recommendations.append(
                "Verify all dates and time periods against source data. Use relative terms like 'recently' when specific dates are unknown."
            )
        
        if HallucinationCategory.FACT in categories:
            recommendations.append(
                "Only include customer facts that are explicitly provided in the customer data. Avoid assumptions about tenure, products, or history."
            )
        
        if HallucinationCategory.EVENT in categories:
            recommendations.append(
                "Do not assume or invent life events, circumstances, or relationships not mentioned in the source data."
            )
        
        # Add general recommendations
        if len(findings) > 5:
            recommendations.append(
                "Consider adjusting AI prompts to emphasize using ONLY information from source data."
            )
        
        if any(f.severity == SeverityLevel.HIGH for f in findings):
            recommendations.append(
                "HIGH PRIORITY: Review and fix all high-severity hallucinations before sending communications."
            )
        
        return recommendations
    
    def _generate_summary(self, findings: List[HallucinationFinding], risk_score: float) -> str:
        """Generate executive summary of findings"""
        
        if not findings:
            return "No hallucinations detected. Content appears to be faithful to source data."
        
        high_severity = len([f for f in findings if f.severity == SeverityLevel.HIGH])
        medium_severity = len([f for f in findings if f.severity == SeverityLevel.MEDIUM])
        low_severity = len([f for f in findings if f.severity == SeverityLevel.LOW])
        
        risk_level = "HIGH" if risk_score > 0.7 else "MEDIUM" if risk_score > 0.4 else "LOW"
        
        summary = f"Detected {len(findings)} potential hallucination(s) with {risk_level} overall risk ({risk_score:.0%}). "
        summary += f"Severity breakdown: {high_severity} high, {medium_severity} medium, {low_severity} low. "
        
        if high_severity > 0:
            summary += f"URGENT: {high_severity} high-severity issue(s) require immediate attention. "
        
        # Most common category
        categories = {}
        for finding in findings:
            if finding.category not in categories:
                categories[finding.category] = 0
            categories[finding.category] += 1
        
        if categories:
            most_common = max(categories.items(), key=lambda x: x[1])
            summary += f"Most common issue: {most_common[0].value.replace('_', ' ')} ({most_common[1]} instance(s))."
        
        return summary

# Convenience function for easy integration
def detect_hallucinations(
    generated_content: Dict[str, str],
    original_letter: str,
    customer_data: Dict[str, Any],
    api_key: Optional[str] = None
) -> HallucinationReport:
    """
    Quick function to detect hallucinations in generated content
    
    Args:
        generated_content: Dict with channel content (email, sms, letter, voice)
        original_letter: Original letter text
        customer_data: Customer data dictionary
        api_key: Optional Claude API key
        
    Returns:
        HallucinationReport with findings and recommendations
    """
    detector = HallucinationDetector(api_key=api_key)
    return detector.detect_hallucinations(
        generated_content=generated_content,
        original_letter=original_letter,
        customer_data=customer_data
    )