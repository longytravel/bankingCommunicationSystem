"""
Content Validator Module - AI-Powered Content Validation
Ensures critical information is preserved across all personalized channels
Fully AI-driven extraction with proper validation
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
            print("⚠️ Content Validator using pattern extraction fallback")
    
    def extract_key_points(self, letter_content: str) -> List[KeyPoint]:
        """
        Extract key points from the original letter using AI
        Returns only actual content that exists, never "No X found" statements
        """
        # Use AI extraction as primary method
        if self.client:
            points = self._ai_extract_points(letter_content)
            
            # Filter out any negative/absence points that might have been created
            points = [p for p in points if not self._is_negative_point(p)]
            
            # If AI didn't find enough points, try one more time with better prompt
            if len(points) < 3:
                points = self._ai_extract_points_retry(letter_content)
                points = [p for p in points if not self._is_negative_point(p)]
        else:
            # Fallback to pattern extraction if no AI available
            points = self._pattern_extract_points(letter_content)
        
        # Always filter out negative points
        points = [p for p in points if not self._is_negative_point(p)]
        
        # If we still have no points, extract the main message
        if len(points) == 0:
            points = self._extract_core_message(letter_content)
        
        return points
    
    def _is_negative_point(self, point: KeyPoint) -> bool:
        """Check if a point is a negative/absence statement"""
        negative_indicators = [
            'no specific', 'no monetary', 'no legal', 'not mentioned',
            'no dates', 'no amounts', 'no deadline', 'none found',
            'there are no', 'does not contain', 'absent', 'missing'
        ]
        content_lower = point.content.lower()
        return any(indicator in content_lower for indicator in negative_indicators)
    
    def _ai_extract_points(self, letter_content: str) -> List[KeyPoint]:
        """Use Claude to intelligently extract key points - context-aware"""
        
        prompt = f"""You are analyzing a bank letter to identify what information MUST be preserved in personalized versions.

IMPORTANT: Only extract information that ACTUALLY EXISTS in the letter. Never create points about what's absent or missing.

LETTER:
{letter_content}

Analyze this specific letter and determine what's truly critical based on its PURPOSE and CONTENT:

For each piece of information found, classify as:
- CRITICAL: Information that would be legally problematic or dangerous if omitted (actual dates, actual amounts, specific requirements, legal obligations that are stated)
- IMPORTANT: Key features, benefits, or actions the customer should know about
- CONTEXTUAL: Supporting details that enhance understanding

DO NOT create points like "No dates mentioned" or "No amounts found". Only list information that IS PRESENT.

If this is a promotional/informational letter about features, the critical points might be:
- How to access or enable the features
- Any limitations or requirements
- Key benefits being offered

If this is a regulatory letter, critical points would be:
- Specific dates and deadlines mentioned
- Fee amounts stated
- Legal requirements described

Return ONLY points for information that EXISTS in the letter.

Return as JSON array:
[
  {{
    "content": "The specific information found in the letter",
    "importance": "CRITICAL|IMPORTANT|CONTEXTUAL",
    "category": "feature|benefit|action|contact|instruction|requirement|date|amount|greeting|closing",
    "explanation": "Why this specific information matters for this type of letter"
  }}
]

Remember: Quality over quantity. Only extract real information that appears in the letter."""

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
                    # Skip if it's a negative point
                    if 'no ' in point['content'].lower() and 'mentioned' in point['content'].lower():
                        continue
                    
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
    
    def _ai_extract_points_retry(self, letter_content: str) -> List[KeyPoint]:
        """Retry with a more focused prompt if first attempt didn't find enough"""
        
        prompt = f"""Extract the key information from this bank letter that customers need to know:

{letter_content}

Focus on:
1. What is the main purpose/message of this letter?
2. What actions (if any) should the customer take?
3. What features or services are being described?
4. What contact information is provided?
5. What are the key benefits mentioned?
6. Include greetings and closings if they're personalized or important

Only list information that is ACTUALLY IN THE LETTER. 

Return as JSON array with at least 3-5 key points:
[{{"content": "...", "importance": "CRITICAL|IMPORTANT|CONTEXTUAL", "category": "...", "explanation": "..."}}]"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.4,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text.strip()
            
            if '[' in content:
                json_start = content.index('[')
                json_end = content.rindex(']') + 1
                json_str = content[json_start:json_end]
                points_data = json.loads(json_str)
                
                key_points = []
                for point in points_data:
                    key_points.append(KeyPoint(
                        content=point['content'],
                        importance=PointImportance[point.get('importance', 'IMPORTANT')],
                        category=point.get('category', 'general'),
                        found_in_channels={},
                        explanation=point.get('explanation', '')
                    ))
                
                return key_points
            else:
                return []
                
        except Exception as e:
            print(f"AI retry error: {e}")
            return []
    
    def _pattern_extract_points(self, letter_content: str) -> List[KeyPoint]:
        """Fallback pattern extraction - only extracts actual content found"""
        key_points = []
        text_lower = letter_content.lower()
        
        # Extract actual dates if they exist
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}\b',
        ]
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, letter_content, re.IGNORECASE)
            for match in matches:
                key_points.append(KeyPoint(
                    content=f"Date: {match.group()}",
                    importance=PointImportance.CRITICAL,
                    category="date",
                    found_in_channels={},
                    explanation="Specific date found"
                ))
        
        # Extract actual amounts if they exist
        amount_pattern = r'[£$€]\s*\d+(?:,\d{3})*(?:\.\d{2})?'
        amounts = re.findall(amount_pattern, letter_content)
        for amount in amounts:
            key_points.append(KeyPoint(
                content=f"Amount: {amount}",
                importance=PointImportance.CRITICAL,
                category="amount",
                found_in_channels={},
                explanation="Monetary amount found"
            ))
        
        # Extract contact information if it exists
        phone_patterns = [r'\b0\d{3}\s?\d{3}\s?\d{4}\b', r'\b0800\s?\d{3}\s?\d{3,4}\b']
        for pattern in phone_patterns:
            phones = re.findall(pattern, letter_content)
            for phone in phones:
                key_points.append(KeyPoint(
                    content=f"Contact: {phone}",
                    importance=PointImportance.IMPORTANT,
                    category="contact",
                    found_in_channels={},
                    explanation="Contact number"
                ))
        
        # Extract website URLs if they exist
        website_pattern = r'(?:www\.|https?://)?[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+(?:/[^\s]*)?'
        websites = re.findall(website_pattern, letter_content)
        for website in websites[:2]:  # Limit to first 2
            if len(website) > 10 and 'bank' in website.lower():
                key_points.append(KeyPoint(
                    content=f"Website: {website}",
                    importance=PointImportance.IMPORTANT,
                    category="contact",
                    found_in_channels={},
                    explanation="Website URL"
                ))
        
        # Extract key features or actions mentioned
        action_phrases = re.findall(r'you can now [^.]+', text_lower)
        for phrase in action_phrases[:3]:
            key_points.append(KeyPoint(
                content=phrase.strip(),
                importance=PointImportance.IMPORTANT,
                category="feature",
                found_in_channels={},
                explanation="New capability or feature"
            ))
        
        # Extract greeting and closing if present
        if 'thank you for banking with us' in text_lower:
            key_points.append(KeyPoint(
                content="Thank you for banking with us",
                importance=PointImportance.CONTEXTUAL,
                category="closing",
                found_in_channels={},
                explanation="Letter closing"
            ))
        
        return key_points
    
    def _extract_core_message(self, letter_content: str) -> List[KeyPoint]:
        """Extract the core message as a fallback"""
        # Find the main paragraph (skip greeting)
        lines = letter_content.split('\n')
        main_content = []
        
        for line in lines:
            line = line.strip()
            if len(line) > 50 and not line.startswith('Dear') and not line.startswith('Sincerely'):
                main_content.append(line)
        
        if main_content:
            # Take first substantial paragraph
            core_message = main_content[0][:200]
            return [KeyPoint(
                content=f"Main message: {core_message}",
                importance=PointImportance.IMPORTANT,
                category="message",
                found_in_channels={},
                explanation="Core letter message"
            )]
        
        return []
    
    def validate_personalization(
        self, 
        key_points: List[KeyPoint], 
        personalized_content: Dict[str, str]
    ) -> Tuple[List[KeyPoint], Dict[str, Any]]:
        """
        Validate that key points appear in personalized content
        Returns updated key points and validation summary
        """
        # Skip validation if no key points
        if not key_points:
            return key_points, {
                'critical_preserved': 0,
                'critical_total': 0,
                'total_preserved': 0,
                'total_points': 0,
                'coverage_percentage': 100  # No points to validate = 100% coverage
            }
        
        if self.client and len(key_points) > 0:
            # Try AI validation with FULL content
            validated, summary = self._ai_validate_full_content(key_points, personalized_content)
            
            # If AI validation seems wrong, try improved pattern matching
            if not summary or self._validation_seems_wrong(validated, personalized_content):
                print("AI validation seems incorrect, using improved pattern matching")
                return self._improved_pattern_validate(key_points, personalized_content)
            
            return validated, summary
        else:
            return self._improved_pattern_validate(key_points, personalized_content)
    
    def _validation_seems_wrong(self, key_points: List[KeyPoint], personalized_content: Dict[str, str]) -> bool:
        """Quick check if validation results seem wrong"""
        # Check for obvious errors like "Thank you" being marked as missing when it's clearly there
        for point in key_points:
            if 'thank you' in point.content.lower():
                # Check if it's really in the letter
                letter_content = personalized_content.get('letter', '').lower()
                if 'thank you' in letter_content and not point.found_in_channels.get('letter', False):
                    return True  # Validation is wrong
        return False
    
    def _ai_validate_full_content(
        self, 
        key_points: List[KeyPoint], 
        personalized_content: Dict[str, str]
    ) -> Tuple[List[KeyPoint], Dict[str, Any]]:
        """Use AI to check if key points are preserved - with FULL content"""
        
        # Build the validation request with full content
        points_list = []
        for i, p in enumerate(key_points):
            points_list.append(f"{i+1}. {p.content}")
        
        points_text = "\n".join(points_list)
        
        # IMPORTANT: Send FULL content, not truncated
        email_full = personalized_content.get('email', 'Not generated')
        letter_full = personalized_content.get('letter', 'Not generated')
        sms_full = personalized_content.get('sms', 'Not generated')
        app_full = personalized_content.get('app', 'Not generated')
        
        prompt = f"""You are validating if key information appears in personalized content.

KEY POINTS TO FIND:
{points_text}

IMPORTANT: Check the ENTIRE content of each channel. The information might be rephrased, translated, or appear anywhere in the text (beginning, middle, or end).

PERSONALIZED CONTENT TO SEARCH:

=== EMAIL (FULL CONTENT) ===
{email_full}

=== SMS (FULL CONTENT) ===
{sms_full}

=== APP (FULL CONTENT) ===
{app_full}

=== LETTER (FULL CONTENT) ===
{letter_full}

For each numbered point above, determine if the INFORMATION (not exact wording) appears ANYWHERE in each channel.
Be thorough - check the ENTIRE content, including greetings, body, and closings.

Return a JSON object with this exact structure:
{{
  "validations": [
    {{
      "point_number": 1,
      "point_text": "exact text of point 1",
      "email": true/false,
      "sms": true/false,
      "app": true/false,
      "letter": true/false,
      "notes": "optional notes about where found or why missing"
    }}
  ],
  "summary": {{
    "critical_preserved": number,
    "critical_total": number,
    "total_preserved": number,
    "total_points": number,
    "coverage_percentage": percentage
  }}
}}

Be accurate - if something appears ANYWHERE in the content, mark it as true."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.1,  # Very low for accuracy
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
                for i, point in enumerate(key_points):
                    # Find matching validation by index
                    for validation in result.get('validations', []):
                        if validation.get('point_number') == i + 1:
                            point.found_in_channels = {
                                'email': validation.get('email', False),
                                'sms': validation.get('sms', False),
                                'app': validation.get('app', False),
                                'letter': validation.get('letter', False)
                            }
                            break
                
                # Calculate accurate summary
                critical_points = [p for p in key_points if p.importance == PointImportance.CRITICAL]
                critical_preserved = sum(1 for p in critical_points if any(p.found_in_channels.values()))
                total_preserved = sum(1 for p in key_points if any(p.found_in_channels.values()))
                
                summary = {
                    'critical_preserved': critical_preserved,
                    'critical_total': len(critical_points),
                    'total_preserved': total_preserved,
                    'total_points': len(key_points),
                    'coverage_percentage': (total_preserved / len(key_points) * 100) if key_points else 100
                }
                
                return key_points, summary
            else:
                return key_points, {}
                
        except Exception as e:
            print(f"AI validation error: {e}")
            return self._improved_pattern_validate(key_points, personalized_content)
    
    def _improved_pattern_validate(
        self, 
        key_points: List[KeyPoint], 
        personalized_content: Dict[str, str]
    ) -> Tuple[List[KeyPoint], Dict[str, Any]]:
        """Improved pattern-based validation with better matching"""
        
        channels = ['email', 'sms', 'app', 'letter']
        
        for point in key_points:
            point.found_in_channels = {}
            
            # Get the essence of what we're looking for
            search_text = point.content.lower()
            
            # Remove prefixes like "Date:", "Amount:", etc.
            if ':' in search_text:
                search_text = search_text.split(':', 1)[1].strip()
            
            for channel in channels:
                content = str(personalized_content.get(channel, '')).lower()
                
                # Multiple strategies for finding content
                found = False
                
                # Strategy 1: Direct substring search (most reliable)
                if search_text in content:
                    found = True
                
                # Strategy 2: Check for the core words (for phrases)
                elif len(search_text.split()) > 2:
                    # For phrases, check if all important words are present
                    important_words = [w for w in search_text.split() if len(w) > 3]
                    if important_words:
                        words_found = sum(1 for word in important_words if word in content)
                        found = words_found >= len(important_words) * 0.7  # 70% of words
                
                # Strategy 3: For single important words/values
                elif len(search_text.split()) <= 2:
                    # Remove common words and check
                    key_part = search_text.replace('the', '').replace('for', '').replace('with', '').strip()
                    if key_part and key_part in content:
                        found = True
                
                # Strategy 4: Special handling for common phrases
                if not found:
                    # Check for variations of common phrases
                    if 'thank you' in search_text:
                        found = any(phrase in content for phrase in ['thank you', 'thanks for', 'appreciate your', 'grateful for'])
                    elif 'banking with us' in search_text:
                        found = any(phrase in content for phrase in ['banking with us', 'banking with lloyds', 'choosing lloyds', 'being our customer'])
                
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
                'coverage': (found / total * 100) if total > 0 else 100
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
            return 'warning', f"⚠️ Validation complete ({overall_coverage:.0f}% coverage)"

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
    
    # Extract key points using AI
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
