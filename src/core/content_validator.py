"""
Content Validator Module - AI-Powered Content Validation
Ensures critical information is preserved across all personalized channels
Robust extraction for ALL letter types
"""

import os
import json
import re
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum

# Try to import anthropic for AI analysis
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("Anthropic not available - using enhanced pattern extraction")

class PointImportance(Enum):
    """Importance levels for extracted points"""
    CRITICAL = "critical"      # Must be included (legal, compliance, dates, amounts)
    IMPORTANT = "important"     # Should be included (features, benefits, contact)
    CONTEXTUAL = "contextual"   # Nice to have (examples, additional info)

@dataclass
class KeyPoint:
    """Represents a key point from the letter"""
    content: str
    importance: PointImportance
    category: str
    found_in_channels: Dict[str, bool]
    explanation: str = ""

class ContentValidator:
    """Validates that personalized content preserves critical information"""
    
    def __init__(self, api_key: str = None):
        """Initialize the validator with optional API key"""
        self.api_key = api_key or os.getenv('CLAUDE_API_KEY')
        self.client = None
        
        if self.api_key and ANTHROPIC_AVAILABLE:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.model = "claude-3-haiku-20240307"  # Fast model for validation
            print("✓ Content Validator using Claude AI")
        else:
            print("⚠️ Content Validator using enhanced pattern extraction")
    
    def extract_key_points(self, letter_content: str) -> List[KeyPoint]:
        """
        Extract key points from the original letter
        ALWAYS returns meaningful points for ANY letter
        """
        # Try AI extraction first
        if self.client:
            points = self._ai_extract_points(letter_content)
            # If AI returns too few points, enhance with pattern extraction
            if len(points) < 5:
                pattern_points = self._comprehensive_extract_points(letter_content)
                # Merge, avoiding duplicates
                existing_content = {p.content.lower() for p in points}
                for pp in pattern_points:
                    if pp.content.lower() not in existing_content:
                        points.append(pp)
        else:
            points = self._comprehensive_extract_points(letter_content)
        
        # Always ensure we have meaningful points
        if len(points) < 3:
            points.extend(self._extract_fallback_points(letter_content))
        
        return points
    
    def _ai_extract_points(self, letter_content: str) -> List[KeyPoint]:
        """Use Claude to intelligently extract key points"""
        
        prompt = f"""You are analyzing a bank letter to extract ALL important information that must be preserved in personalized versions.

LETTER:
{letter_content}

Extract EVERY piece of important information, including:
1. CRITICAL (must be exact): 
   - All dates and deadlines
   - All monetary amounts and fees
   - Legal/regulatory requirements
   - Action requirements (what customer must/must not do)
   - Important times/deadlines
   - Account details mentioned

2. IMPORTANT (should include):
   - Features and benefits described
   - Contact information (phone, web, email)
   - Service offerings
   - Tools and resources mentioned
   - Eligibility criteria
   - Key processes or steps

3. CONTEXTUAL (good to include):
   - Examples given
   - Additional tips
   - Supporting information

BE COMPREHENSIVE - extract at least 10-15 points from the letter. Include EVERYTHING that matters.

Return as JSON array:
[
  {{
    "content": "The specific information",
    "importance": "CRITICAL|IMPORTANT|CONTEXTUAL",
    "category": "date|amount|deadline|action|contact|feature|legal|benefit|process|tool",
    "explanation": "Why this must be preserved"
  }}
]"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text.strip()
            
            # Parse JSON response
            if '[' in content:
                json_start = content.index('[')
                json_end = content.rindex(']') + 1
                json_str = content[json_start:json_end]
                points_data = json.loads(json_str)
                
                # Convert to KeyPoint objects
                key_points = []
                for point in points_data:
                    key_points.append(KeyPoint(
                        content=point['content'],
                        importance=PointImportance[point['importance']],
                        category=point['category'],
                        found_in_channels={},
                        explanation=point.get('explanation', '')
                    ))
                
                return key_points
            else:
                return []
                
        except Exception as e:
            print(f"AI extraction error: {e}")
            return []
    
    def _comprehensive_extract_points(self, letter_content: str) -> List[KeyPoint]:
        """Comprehensive pattern-based extraction for ALL letter types"""
        key_points = []
        text_lower = letter_content.lower()
        
        # 1. Extract ALL dates (critical)
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}\b',
            r'\b\d{1,2}\s+(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4}\b',
            r'\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)[,\s]+(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}\b'
        ]
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, letter_content, re.IGNORECASE)
            for match in matches:
                key_points.append(KeyPoint(
                    content=f"Date: {match.group()}",
                    importance=PointImportance.CRITICAL,
                    category="date",
                    found_in_channels={},
                    explanation="Dates must be accurate"
                ))
        
        # 2. Extract ALL amounts (critical)
        amount_pattern = r'[£$€]\s*\d+(?:,\d{3})*(?:\.\d{2})?(?:\s*(?:GBP|USD|EUR))?'
        amounts = re.findall(amount_pattern, letter_content)
        for amount in amounts:
            key_points.append(KeyPoint(
                content=f"Amount: {amount}",
                importance=PointImportance.CRITICAL,
                category="amount",
                found_in_channels={},
                explanation="Financial amounts must be exact"
            ))
        
        # 3. Extract percentages (critical)
        percent_pattern = r'\d+(?:\.\d+)?%'
        percentages = re.findall(percent_pattern, letter_content)
        for percent in percentages:
            key_points.append(KeyPoint(
                content=f"Percentage: {percent}",
                importance=PointImportance.CRITICAL,
                category="amount",
                found_in_channels={},
                explanation="Rates and percentages must be accurate"
            ))
        
        # 4. Extract times (critical)
        time_patterns = [
            r'\b\d{1,2}:\d{2}\s*(?:am|pm|AM|PM)?\b',
            r'\b\d{1,2}\.\d{2}\s*(?:am|pm|AM|PM)\b',
            r'\bmidnight\b|\bnoon\b|\bmidday\b'
        ]
        for pattern in time_patterns:
            times = re.findall(pattern, letter_content, re.IGNORECASE)
            for time in times:
                key_points.append(KeyPoint(
                    content=f"Time: {time}",
                    importance=PointImportance.CRITICAL,
                    category="deadline",
                    found_in_channels={},
                    explanation="Specific times are critical"
                ))
        
        # 5. Extract contact information (important)
        # Phone numbers
        phone_patterns = [
            r'\b0\d{3}\s?\d{3}\s?\d{4}\b',
            r'\b\+44\s?\d{2}\s?\d{4}\s?\d{4}\b',
            r'\b0800\s?\d{3}\s?\d{3,4}\b'
        ]
        for pattern in phone_patterns:
            phones = re.findall(pattern, letter_content)
            for phone in phones:
                key_points.append(KeyPoint(
                    content=f"Contact number: {phone}",
                    importance=PointImportance.IMPORTANT,
                    category="contact",
                    found_in_channels={},
                    explanation="Customer support contact"
                ))
        
        # Websites
        website_pattern = r'(?:www\.|https?://)?[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+(?:/[^\s]*)?'
        websites = re.findall(website_pattern, letter_content)
        for website in websites[:3]:  # Limit to avoid too many
            if len(website) > 10:  # Filter out false positives
                key_points.append(KeyPoint(
                    content=f"Website: {website}",
                    importance=PointImportance.IMPORTANT,
                    category="contact",
                    found_in_channels={},
                    explanation="Online resource"
                ))
        
        # 6. Extract action requirements (critical)
        action_patterns = [
            (r'no action (?:is )?(?:required|needed)', "No action required"),
            (r'you (?:must|need to|should) (?:contact|call|visit)', "Customer must contact bank"),
            (r'action (?:is )?required', "Action required"),
            (r'please (?:review|check|verify)', "Review required"),
            (r'you (?:can|may) (?:now|continue)', "New capability available"),
            (r'deadline|by \d+|before \d+', "Deadline mentioned"),
            (r'effective (?:from|date)', "Effective date specified")
        ]
        
        for pattern, description in action_patterns:
            if re.search(pattern, text_lower):
                key_points.append(KeyPoint(
                    content=description,
                    importance=PointImportance.CRITICAL,
                    category="action",
                    found_in_channels={},
                    explanation="Customer action/awareness required"
                ))
        
        # 7. Extract features and tools (important for informational letters)
        feature_keywords = [
            'spending limit', 'savings goal', 'budget', 'alert', 'notification',
            'mobile app', 'online banking', 'feature', 'tool', 'service',
            'benefit', 'reward', 'cashback', 'interest', 'overdraft',
            'payment', 'transfer', 'direct debit', 'standing order'
        ]
        
        for keyword in feature_keywords:
            if keyword in text_lower:
                # Find the sentence containing this keyword
                sentences = letter_content.split('.')
                for sent in sentences:
                    if keyword in sent.lower():
                        # Extract a meaningful phrase around the keyword
                        key_points.append(KeyPoint(
                            content=f"Feature: {sent.strip()[:100]}",
                            importance=PointImportance.IMPORTANT,
                            category="feature",
                            found_in_channels={},
                            explanation="Service feature mentioned"
                        ))
                        break
        
        # 8. Extract any account-specific information
        account_patterns = [
            r'account\s+(?:number|ending|type)[:\s]+([A-Z0-9\-]+)',
            r'sort\s+code[:\s]+(\d{2}-\d{2}-\d{2})',
            r'reference[:\s]+([A-Z0-9]+)'
        ]
        
        for pattern in account_patterns:
            matches = re.finditer(pattern, letter_content, re.IGNORECASE)
            for match in matches:
                key_points.append(KeyPoint(
                    content=f"Account detail: {match.group()}",
                    importance=PointImportance.CRITICAL,
                    category="account",
                    found_in_channels={},
                    explanation="Account-specific information"
                ))
        
        # 9. Check for regulatory/legal mentions
        if any(term in text_lower for term in ['terms and conditions', 'regulatory', 'legal', 'compliance']):
            key_points.append(KeyPoint(
                content="Legal/regulatory notification",
                importance=PointImportance.CRITICAL,
                category="legal",
                found_in_channels={},
                explanation="Regulatory requirement"
            ))
        
        # 10. Extract specific named services or products
        # Look for capitalized multi-word phrases that might be product names
        product_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b'
        products = re.findall(product_pattern, letter_content)
        for product in products[:5]:  # Limit to avoid too many
            if len(product) > 5 and product not in ['Dear Customer', 'Lloyds Bank', 'Yours Sincerely']:
                key_points.append(KeyPoint(
                    content=f"Service/Product: {product}",
                    importance=PointImportance.IMPORTANT,
                    category="feature",
                    found_in_channels={},
                    explanation="Named service or product"
                ))
        
        return key_points
    
    def _extract_fallback_points(self, letter_content: str) -> List[KeyPoint]:
        """Fallback to ensure we always have some key points"""
        points = []
        text_lower = letter_content.lower()
        
        # Core message - first substantive paragraph
        paragraphs = [p.strip() for p in letter_content.split('\n\n') if len(p.strip()) > 50]
        if paragraphs:
            # Skip greeting and get to the meat
            main_para = paragraphs[1] if len(paragraphs) > 1 else paragraphs[0]
            points.append(KeyPoint(
                content=f"Main message: {main_para[:150]}...",
                importance=PointImportance.CRITICAL,
                category="message",
                found_in_channels={},
                explanation="Core communication purpose"
            ))
        
        # Bank name/sender
        if 'lloyds' in text_lower:
            points.append(KeyPoint(
                content="Sender: Lloyds Bank",
                importance=PointImportance.IMPORTANT,
                category="sender",
                found_in_channels={},
                explanation="Message source identification"
            ))
        
        # Any call to action
        if 'visit' in text_lower or 'call' in text_lower or 'log in' in text_lower:
            points.append(KeyPoint(
                content="Customer action suggested",
                importance=PointImportance.IMPORTANT,
                category="action",
                found_in_channels={},
                explanation="Next steps for customer"
            ))
        
        return points
    
    def validate_personalization(
        self, 
        key_points: List[KeyPoint], 
        personalized_content: Dict[str, str]
    ) -> Tuple[List[KeyPoint], Dict[str, Any]]:
        """
        Validate that key points appear in personalized content
        Returns updated key points and validation summary
        """
        if self.client and len(key_points) > 0:
            validated, summary = self._ai_validate(key_points, personalized_content)
            # If AI validation fails, use pattern matching
            if not summary or summary.get('critical_total', 0) == 0:
                return self._pattern_validate(key_points, personalized_content)
            return validated, summary
        else:
            return self._pattern_validate(key_points, personalized_content)
    
    def _ai_validate(
        self, 
        key_points: List[KeyPoint], 
        personalized_content: Dict[str, str]
    ) -> Tuple[List[KeyPoint], Dict[str, Any]]:
        """Use AI to check if key points are preserved"""
        
        # Build prompt for validation
        points_list = "\n".join([f"- {p.content} ({p.importance.value})" for p in key_points[:20]])  # Limit for token size
        
        prompt = f"""Check if these key points from the original letter appear in the personalized versions.
The content may be rephrased or translated, but the core information must be present.

KEY POINTS TO FIND:
{points_list}

PERSONALIZED CONTENT:
Email: {personalized_content.get('email', 'Not generated')[:1000]}
SMS: {personalized_content.get('sms', 'Not generated')}
App: {personalized_content.get('app', 'Not generated')}
Letter: {personalized_content.get('letter', 'Not generated')[:1000]}

For each key point, check if the INFORMATION (not exact wording) appears in each channel.

Return JSON:
{{
  "validations": [
    {{
      "point": "exact point text from list",
      "email": true/false,
      "sms": true/false,
      "app": true/false,
      "letter": true/false
    }}
  ],
  "summary": {{
    "critical_preserved": X,
    "critical_total": Y,
    "coverage_percentage": Z
  }}
}}"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text.strip()
            
            # Parse response
            if '{' in content:
                json_start = content.index('{')
                json_end = content.rindex('}') + 1
                json_str = content[json_start:json_end]
                result = json.loads(json_str)
                
                # Update key points with validation results
                for point in key_points:
                    # Find matching validation
                    for validation in result.get('validations', []):
                        if validation['point'] in point.content or point.content in validation['point']:
                            point.found_in_channels = {
                                'email': validation.get('email', False),
                                'sms': validation.get('sms', False),
                                'app': validation.get('app', False),
                                'letter': validation.get('letter', False)
                            }
                            break
                
                return key_points, result.get('summary', {})
            else:
                return key_points, {}
                
        except Exception as e:
            print(f"AI validation error: {e}")
            return key_points, {}
    
    def _pattern_validate(
        self, 
        key_points: List[KeyPoint], 
        personalized_content: Dict[str, str]
    ) -> Tuple[List[KeyPoint], Dict[str, Any]]:
        """Enhanced pattern validation that's more flexible"""
        
        # Check each channel
        channels = ['email', 'sms', 'app', 'letter']
        
        for point in key_points:
            point.found_in_channels = {}
            
            for channel in channels:
                content = str(personalized_content.get(channel, '')).lower()
                
                # Extract the key value from the point
                point_lower = point.content.lower()
                
                # Check if value appears in content
                found = False
                
                # For dates, be flexible
                if point.category == 'date':
                    # Extract date components
                    date_parts = re.findall(r'\b(?:\d+|january|february|march|april|may|june|july|august|september|october|november|december)\b', point_lower)
                    # Check if at least 2 parts match
                    matching_parts = sum(1 for part in date_parts if part in content)
                    found = matching_parts >= 2
                
                # For amounts, check numbers
                elif point.category == 'amount':
                    # Extract just the numbers
                    numbers = re.findall(r'\d+(?:\.\d+)?', point.content)
                    found = any(num in content for num in numbers)
                
                # For features/actions, check key words
                elif point.category in ['feature', 'action', 'benefit']:
                    # Extract meaningful words (3+ characters)
                    words = [w for w in re.findall(r'\b\w+\b', point_lower) if len(w) > 3]
                    # Check if at least half the words appear
                    if words:
                        matching_words = sum(1 for word in words if word in content)
                        found = matching_words >= len(words) / 2
                
                # For contact info, check the actual number/website
                elif point.category == 'contact':
                    # Extract numbers or URLs
                    contact_values = re.findall(r'[\d\s]+|www\.[^\s]+|https?://[^\s]+', point.content)
                    found = any(val.replace(' ', '') in content.replace(' ', '') for val in contact_values)
                
                # Default: check for substantial overlap
                else:
                    # Extract meaningful words
                    words = [w for w in re.findall(r'\b\w+\b', point_lower) if len(w) > 3]
                    if words:
                        matching_words = sum(1 for word in words if word in content)
                        found = matching_words >= min(3, len(words) * 0.5)
                
                point.found_in_channels[channel] = found
        
        # Calculate summary
        critical_points = [p for p in key_points if p.importance == PointImportance.CRITICAL]
        critical_preserved = sum(
            1 for p in critical_points 
            if any(p.found_in_channels.values())
        )
        
        all_preserved = sum(
            1 for p in key_points
            if any(p.found_in_channels.values())
        )
        
        summary = {
            'critical_preserved': critical_preserved,
            'critical_total': len(critical_points),
            'total_preserved': all_preserved,
            'total_points': len(key_points),
            'coverage_percentage': (all_preserved / len(key_points) * 100) if key_points else 100
        }
        
        return key_points, summary
    
    def generate_validation_report(
        self, 
        key_points: List[KeyPoint], 
        summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a structured validation report"""
        
        report = {
            'summary': {
                'total_points': len(key_points),
                'critical_points': len([p for p in key_points if p.importance == PointImportance.CRITICAL]),
                'important_points': len([p for p in key_points if p.importance == PointImportance.IMPORTANT]),
                'contextual_points': len([p for p in key_points if p.importance == PointImportance.CONTEXTUAL]),
                'coverage_percentage': summary.get('coverage_percentage', 0),
                'critical_coverage': (summary.get('critical_preserved', 0) / summary.get('critical_total', 1) * 100) if summary.get('critical_total', 0) > 0 else 100
            },
            'by_channel': {
                'email': {'found': 0, 'missing': 0, 'coverage': 0},
                'sms': {'found': 0, 'missing': 0, 'coverage': 0},
                'app': {'found': 0, 'missing': 0, 'coverage': 0},
                'letter': {'found': 0, 'missing': 0, 'coverage': 0}
            },
            'critical_missing': [],
            'important_missing': [],
            'details': []
        }
        
        # Analyze by channel
        for channel in ['email', 'sms', 'app', 'letter']:
            found = sum(1 for p in key_points if p.found_in_channels.get(channel, False))
            total = len(key_points)
            report['by_channel'][channel] = {
                'found': found,
                'missing': total - found,
                'coverage': (found / total * 100) if total > 0 else 0
            }
        
        # Identify missing critical/important points
        for point in key_points:
            if point.importance == PointImportance.CRITICAL:
                if not any(point.found_in_channels.values()):
                    report['critical_missing'].append(point.content)
            elif point.importance == PointImportance.IMPORTANT:
                if not any(point.found_in_channels.values()):
                    report['important_missing'].append(point.content)
            
            # Add to details
            report['details'].append({
                'content': point.content,
                'importance': point.importance.value,
                'category': point.category,
                'found_in': [ch for ch, found in point.found_in_channels.items() if found],
                'missing_from': [ch for ch, found in point.found_in_channels.items() if not found],
                'explanation': point.explanation
            })
        
        return report
    
    def get_validation_status(self, report: Dict[str, Any]) -> Tuple[str, str]:
        """
        Get overall validation status and message
        Returns: (status, message) where status is 'success', 'warning', or 'error'
        """
        critical_coverage = report['summary'].get('critical_coverage', 0)
        overall_coverage = report['summary'].get('coverage_percentage', 0)
        critical_missing = len(report.get('critical_missing', []))
        
        if critical_missing == 0 and critical_coverage == 100:
            return 'success', f"✅ All critical information preserved ({overall_coverage:.0f}% total coverage)"
        elif critical_missing == 0 and critical_coverage >= 90:
            return 'warning', f"⚠️ Most critical info preserved ({critical_coverage:.0f}% critical, {overall_coverage:.0f}% total)"
        elif critical_missing > 0:
            return 'error', f"❌ {critical_missing} critical points missing ({critical_coverage:.0f}% critical coverage)"
        else:
            return 'warning', f"⚠️ Validation incomplete ({overall_coverage:.0f}% coverage)"

# Convenience function for easy integration
def validate_personalization(
    original_letter: str,
    personalized_content: Dict[str, str],
    api_key: str = None
) -> Dict[str, Any]:
    """
    Simple function to validate personalized content
    
    Args:
        original_letter: The original letter text
        personalized_content: Dict with keys 'email', 'sms', 'app', 'letter'
        api_key: Optional Claude API key
    
    Returns:
        Validation report dictionary
    """
    validator = ContentValidator(api_key)
    
    # Extract key points - ALWAYS returns meaningful points
    key_points = validator.extract_key_points(original_letter)
    
    # Validate personalization
    validated_points, summary = validator.validate_personalization(key_points, personalized_content)
    
    # Generate report
    report = validator.generate_validation_report(validated_points, summary)
    
    # Add status
    status, message = validator.get_validation_status(report)
    report['status'] = status
    report['message'] = message
    report['key_points'] = validated_points
    
    return report