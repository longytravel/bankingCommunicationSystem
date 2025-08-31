"""
Input Cleaning Module - Remove Template Artifacts and Standardize Content
Single responsibility: Take messy input and output clean, ready-to-personalize content
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class CleanedContent:
    """Cleaned and structured content ready for personalization"""
    content: str                    # Clean letter content
    original_length: int           # Original length for comparison
    cleaned_length: int           # Length after cleaning
    artifacts_removed: List[str]   # What was cleaned out
    structure_fixed: bool         # Whether structure issues were fixed
    quality_score: float          # 0-1 score of cleaning quality

class InputCleaner:
    """Cleans and standardizes input content, removing template artifacts"""
    
    def __init__(self):
        # Common template placeholders to remove
        self.placeholder_patterns = [
            r'\[Bank\s+Name\s+Letterhead\]',
            r'\[Bank\s+Letterhead\s+Placeholder\]',
            r'\[Bank\s+Name\]',
            r'\[Bank\s+Address\]',
            r'\[Date\]',
            r'\[Customer\s+Name\]',
            r'\[Customer\s+Address\]',
            r'\[Account\s+Name\]',
            r'\[Account\s+Number\]',
            r'\[XXXXXX\]',
            r'\[Customer\s+Services\s+Number\]',
            r'\[Effective\s+Date\]',
            r'\[Name\]',
            r'\[.*?\s+Letterhead.*?\]',
            r'\[.*?Placeholder.*?\]'
        ]
        
        # Duplicate greeting patterns (when template artifacts create multiple greetings)
        self.duplicate_greeting_patterns = [
            r'Dear\s+.*?,\s*Dear\s+.*?,',  # "Dear X, Dear Y,"
            r'Dear\s+.*?\n.*?Dear\s+.*?,',  # Multi-line duplicate greetings
        ]
        
        # Common template structure artifacts
        self.structure_artifacts = [
            r'Address Line \d+',
            r'Postcode',
            r'Customer Name',
            r'\[.*?Address.*?\]',
            r'Important:\s*Important:',  # Duplicate "Important:" headers
            r'Dear\s+Customer,?\s*Dear\s+.*?,',  # Generic then personalized greeting
        ]
    
    def clean_content(self, raw_content: str, customer_data: Optional[Dict] = None) -> CleanedContent:
        """
        Main cleaning function - removes all template artifacts and standardizes content
        
        Args:
            raw_content: Raw letter content with template artifacts
            customer_data: Optional customer data to help with cleaning context
            
        Returns:
            CleanedContent object with cleaned text and metadata
        """
        original_length = len(raw_content)
        artifacts_removed = []
        
        # Step 1: Remove placeholder patterns
        content = self._remove_placeholders(raw_content, artifacts_removed)
        
        # Step 2: Fix duplicate greetings and headers
        content = self._fix_duplicate_structures(content, artifacts_removed)
        
        # Step 3: Clean up structure artifacts
        content = self._remove_structure_artifacts(content, artifacts_removed)
        
        # Step 4: Normalize whitespace and formatting
        content = self._normalize_formatting(content)
        
        # Step 5: Remove empty sections and clean up flow
        content = self._clean_content_flow(content, artifacts_removed)
        
        # Step 6: Quality assessment
        quality_score = self._assess_cleaning_quality(content, original_length)
        structure_fixed = len(artifacts_removed) > 0
        
        return CleanedContent(
            content=content,
            original_length=original_length,
            cleaned_length=len(content),
            artifacts_removed=artifacts_removed,
            structure_fixed=structure_fixed,
            quality_score=quality_score
        )
    
    def _remove_placeholders(self, content: str, artifacts_removed: List[str]) -> str:
        """Remove all placeholder patterns"""
        cleaned_content = content
        
        for pattern in self.placeholder_patterns:
            matches = re.findall(pattern, cleaned_content, re.IGNORECASE)
            if matches:
                artifacts_removed.extend([f"Placeholder: {match}" for match in matches])
                cleaned_content = re.sub(pattern, '', cleaned_content, flags=re.IGNORECASE)
        
        return cleaned_content
    
    def _fix_duplicate_structures(self, content: str, artifacts_removed: List[str]) -> str:
        """Fix duplicate greetings and headers that occur from template merging"""
        cleaned_content = content
        
        # Fix duplicate greetings like "Dear Customer, Dear John,"
        greeting_pattern = r'Dear\s+[^,\n]*,\s*Dear\s+([^,\n]*,)'
        matches = re.findall(greeting_pattern, cleaned_content, re.IGNORECASE)
        if matches:
            artifacts_removed.append(f"Fixed duplicate greetings: {len(matches)} instances")
            # Keep only the second (more personalized) greeting
            cleaned_content = re.sub(greeting_pattern, r'Dear \1', cleaned_content, flags=re.IGNORECASE)
        
        # Fix duplicate "Important:" headers
        important_dupes = re.findall(r'Important:\s*Important:', cleaned_content, re.IGNORECASE)
        if important_dupes:
            artifacts_removed.append(f"Removed duplicate 'Important:' headers: {len(important_dupes)}")
            cleaned_content = re.sub(r'Important:\s*Important:', 'Important:', cleaned_content, flags=re.IGNORECASE)
        
        # Fix duplicate subject lines
        subject_pattern = r'(.*?)\s*\n.*?\1'  # Same line repeated
        # This is tricky, so let's be conservative and just clean obvious duplicates
        lines = cleaned_content.split('\n')
        unique_lines = []
        prev_line = ""
        
        for line in lines:
            line_clean = line.strip()
            # Skip if it's an exact duplicate of the previous line (and not empty)
            if line_clean and line_clean != prev_line.strip():
                unique_lines.append(line)
                prev_line = line
            elif not line_clean:  # Keep empty lines for structure
                unique_lines.append(line)
            else:
                artifacts_removed.append(f"Removed duplicate line: {line_clean[:50]}...")
        
        cleaned_content = '\n'.join(unique_lines)
        return cleaned_content
    
    def _remove_structure_artifacts(self, content: str, artifacts_removed: List[str]) -> str:
        """Remove template structure artifacts"""
        cleaned_content = content
        
        for pattern in self.structure_artifacts:
            matches = re.findall(pattern, cleaned_content, re.IGNORECASE)
            if matches:
                artifacts_removed.extend([f"Structure artifact: {match}" for match in matches])
                cleaned_content = re.sub(pattern, '', cleaned_content, flags=re.IGNORECASE)
        
        return cleaned_content
    
    def _normalize_formatting(self, content: str) -> str:
        """Normalize whitespace and formatting"""
        # Remove excessive blank lines
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        
        # Remove trailing whitespace from lines
        lines = [line.rstrip() for line in content.split('\n')]
        content = '\n'.join(lines)
        
        # Remove leading/trailing whitespace from entire content
        content = content.strip()
        
        # Fix spacing around punctuation
        content = re.sub(r'\s+([,.!?])', r'\1', content)  # Remove space before punctuation
        content = re.sub(r'([,.!?])([A-Za-z])', r'\1 \2', content)  # Add space after punctuation
        
        return content
    
    def _clean_content_flow(self, content: str, artifacts_removed: List[str]) -> str:
        """Clean up content flow, removing orphaned sections and fixing structure"""
        lines = content.split('\n')
        cleaned_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty placeholder sections
            if line == '' and i < len(lines) - 1:
                # Look ahead to see if next non-empty line makes sense
                next_content_line = None
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                if j < len(lines):
                    next_content_line = lines[j].strip()
                
                # If next line starts with a greeting after we already have content,
                # this might be a duplicate structure issue
                if (next_content_line and next_content_line.startswith('Dear ') and 
                    any('Dear ' in prev_line for prev_line in cleaned_lines)):
                    artifacts_removed.append("Removed duplicate greeting section")
                    # Skip to the duplicate greeting and remove it
                    i = j + 1
                    continue
            
            # Keep the line
            cleaned_lines.append(lines[i])
            i += 1
        
        return '\n'.join(cleaned_lines)
    
    def _assess_cleaning_quality(self, cleaned_content: str, original_length: int) -> float:
        """Assess the quality of the cleaning process"""
        
        # Check for remaining artifacts (bad)
        remaining_brackets = len(re.findall(r'\[.*?\]', cleaned_content))
        remaining_placeholders = len(re.findall(r'Customer Name|Bank Name|Date\]', cleaned_content))
        
        # Check for good structure (good)
        has_greeting = bool(re.search(r'Dear\s+\w+', cleaned_content, re.IGNORECASE))
        has_closing = bool(re.search(r'sincerely|regards', cleaned_content, re.IGNORECASE))
        has_content = len(cleaned_content.strip()) > 100
        
        # Calculate score
        quality_score = 1.0
        
        # Penalize remaining artifacts
        quality_score -= (remaining_brackets * 0.1)
        quality_score -= (remaining_placeholders * 0.2)
        
        # Bonus for good structure
        if has_greeting:
            quality_score += 0.1
        if has_closing:
            quality_score += 0.1
        if has_content:
            quality_score += 0.1
        
        # Ensure 0-1 range
        return max(0.0, min(1.0, quality_score))
    
    def validate_cleaning(self, cleaned_content: CleanedContent) -> Dict[str, Any]:
        """Validate that cleaning was successful"""
        
        issues = []
        warnings = []
        
        # Check for remaining placeholders
        remaining_placeholders = re.findall(r'\[.*?\]', cleaned_content.content)
        if remaining_placeholders:
            issues.append(f"Remaining placeholders: {remaining_placeholders}")
        
        # Check for duplicate greetings
        greeting_count = len(re.findall(r'Dear\s+\w+', cleaned_content.content, re.IGNORECASE))
        if greeting_count > 1:
            warnings.append(f"Multiple greetings detected: {greeting_count}")
        
        # Check content length reduction
        reduction_percent = ((cleaned_content.original_length - cleaned_content.cleaned_length) / 
                           cleaned_content.original_length) * 100
        if reduction_percent > 30:
            warnings.append(f"Significant content reduction: {reduction_percent:.1f}%")
        
        # Check if content is too short
        if cleaned_content.cleaned_length < 200:
            issues.append("Cleaned content is very short - may have over-cleaned")
        
        return {
            'is_valid': len(issues) == 0,
            'quality_score': cleaned_content.quality_score,
            'issues': issues,
            'warnings': warnings,
            'artifacts_removed_count': len(cleaned_content.artifacts_removed),
            'content_reduction_percent': reduction_percent
        }

def clean_letter_content(raw_content: str, customer_data: Optional[Dict] = None) -> Tuple[str, Dict]:
    """
    Convenience function to clean letter content
    
    Args:
        raw_content: Raw letter with template artifacts
        customer_data: Optional customer data for context
        
    Returns:
        Tuple of (cleaned_content, cleaning_report)
    """
    cleaner = InputCleaner()
    result = cleaner.clean_content(raw_content, customer_data)
    validation = cleaner.validate_cleaning(result)
    
    report = {
        'original_length': result.original_length,
        'cleaned_length': result.cleaned_length,
        'artifacts_removed': result.artifacts_removed,
        'quality_score': result.quality_score,
        'validation': validation
    }
    
    return result.content, report