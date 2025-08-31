"""
Simple Email Orchestrator - Coordinates Email Personalization Pipeline
Single responsibility: Coordinate between existing components and email generator
Keeps your working content validation, adds focused email generation
"""

import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Import existing working components
from .content_validator import ContentValidator, validate_personalization
from .email_channel_generator import EmailChannelGenerator

# Try to import input cleaner (skip if not working yet)
try:
    from .input_cleaner import clean_letter_content
    INPUT_CLEANER_AVAILABLE = True
except ImportError:
    INPUT_CLEANER_AVAILABLE = False
    print("⚠️ Input cleaner not available, using content as-is")

class SimpleEmailOrchestrator:
    """Simple orchestrator focused on email generation with content validation"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('CLAUDE_API_KEY')
        
        # Initialize components
        self.content_validator = ContentValidator(api_key=self.api_key)
        self.email_generator = EmailChannelGenerator(api_key=self.api_key)
        
        print("✓ Simple Email Orchestrator initialized")
    
    def personalize_email(
        self,
        letter_content: str,
        customer: Dict[str, Any],
        validate_content: bool = True
    ) -> Dict[str, Any]:
        """
        Main orchestration method for email personalization
        
        Args:
            letter_content: Original letter content
            customer: Customer profile data
            validate_content: Whether to run content validation
            
        Returns:
            Complete email personalization result with validation
        """
        
        start_time = datetime.now()
        result = {
            'customer_name': customer.get('name', 'Unknown'),
            'processing_steps': [],
            'email': None,
            'validation': None,
            'errors': [],
            'warnings': []
        }
        
        try:
            # STEP 1: Clean input content (if available)
            if INPUT_CLEANER_AVAILABLE:
                try:
                    cleaned_content, cleaning_report = clean_letter_content(letter_content, customer)
                    result['processing_steps'].append('✓ Input cleaned')
                    result['cleaning_report'] = cleaning_report
                except Exception as e:
                    result['warnings'].append(f"Input cleaning failed: {e}")
                    cleaned_content = letter_content
            else:
                cleaned_content = letter_content
                result['processing_steps'].append('⚠️ Input cleaning skipped')
            
            # STEP 2: Extract key points for content validation (your existing system)
            if validate_content:
                try:
                    key_points = self.content_validator.extract_key_points(cleaned_content)
                    result['key_points'] = key_points
                    result['processing_steps'].append(f'✓ Extracted {len(key_points)} key points')
                except Exception as e:
                    result['warnings'].append(f"Key point extraction failed: {e}")
                    key_points = []
            else:
                key_points = []
                result['processing_steps'].append('⚠️ Content validation skipped')
            
            # STEP 3: Generate personalized email
            try:
                email_result = self.email_generator.generate_email(
                    clean_content=cleaned_content,
                    customer=customer,
                    key_points=key_points
                )
                result['email'] = email_result
                result['processing_steps'].append('✓ Email generated')
                
                # Validate the generated email
                email_validation = self.email_generator.validate_email(
                    email_result, 
                    cleaned_content, 
                    key_points
                )
                result['email_validation'] = email_validation
                result['processing_steps'].append('✓ Email validated')
                
            except Exception as e:
                result['errors'].append(f"Email generation failed: {e}")
                return result
            
            # STEP 4: Content validation against original (your existing system)
            if validate_content and key_points:
                try:
                    # Create personalized content dict in format expected by your validator
                    personalized_content = {
                        'email': email_result['content'],
                        'sms': '',  # Not generating these yet
                        'app': '',
                        'letter': ''
                    }
                    
                    # Use your existing validation system
                    validated_points, validation_summary = self.content_validator.validate_personalization(
                        key_points, 
                        personalized_content
                    )
                    
                    validation_report = self.content_validator.generate_validation_report(
                        validated_points,
                        validation_summary
                    )
                    
                    result['content_validation'] = validation_report
                    result['processing_steps'].append('✓ Content validation completed')
                    
                    # Check if validation passed
                    if validation_report.get('summary', {}).get('coverage_percentage', 0) < 80:
                        result['warnings'].append(f"Content coverage only {validation_report['summary']['coverage_percentage']:.0f}%")
                    
                except Exception as e:
                    result['warnings'].append(f"Content validation failed: {e}")
            
            # STEP 5: Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            result['processing_time'] = processing_time
            result['processing_steps'].append(f'✓ Completed in {processing_time:.2f}s')
            
        except Exception as e:
            result['errors'].append(f"Orchestration failed: {e}")
        
        return result
    
    def get_personalization_summary(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Get a summary of the personalization result"""
        
        if not result.get('email'):
            return {'status': 'failed', 'message': 'Email generation failed'}
        
        email_result = result['email']
        email_validation = result.get('email_validation', {})
        content_validation = result.get('content_validation', {})
        
        # Determine overall status
        has_errors = len(result.get('errors', [])) > 0
        has_warnings = len(result.get('warnings', [])) > 0
        
        if has_errors:
            status = 'error'
        elif has_warnings:
            status = 'warning'  
        else:
            status = 'success'
        
        # Calculate overall quality score
        email_quality = email_validation.get('quality_score', 0)
        content_coverage = content_validation.get('summary', {}).get('coverage_percentage', 100) / 100
        overall_quality = (email_quality + content_coverage) / 2
        
        summary = {
            'status': status,
            'customer': result['customer_name'],
            'overall_quality': overall_quality,
            'email_word_count': email_result.get('word_count', 0),
            'personalization_factors': len(email_result.get('personalization_factors', [])),
            'processing_time': result.get('processing_time', 0),
            'content_coverage': content_coverage * 100,
            'errors': result.get('errors', []),
            'warnings': result.get('warnings', []),
            'processing_steps': result.get('processing_steps', [])
        }
        
        return summary
    
    def batch_personalize_emails(
        self,
        letter_content: str,
        customers: List[Dict[str, Any]],
        validate_content: bool = True,
        max_customers: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Batch process multiple customers for email personalization
        
        Args:
            letter_content: Original letter content
            customers: List of customer profiles
            validate_content: Whether to validate content preservation
            max_customers: Optional limit on number of customers to process
            
        Returns:
            Batch processing results
        """
        
        if max_customers:
            customers = customers[:max_customers]
        
        results = []
        failed_customers = []
        
        print(f"Processing {len(customers)} customers for email personalization...")
        
        for i, customer in enumerate(customers):
            customer_name = customer.get('name', f'Customer_{i}')
            print(f"  {i+1}/{len(customers)}: {customer_name}")
            
            try:
                result = self.personalize_email(letter_content, customer, validate_content)
                results.append(result)
                
                # Quick status check
                if result.get('errors'):
                    failed_customers.append(customer_name)
                    print(f"    ❌ Failed: {result['errors'][0]}")
                elif result.get('warnings'):
                    print(f"    ⚠️ Completed with warnings")
                else:
                    print(f"    ✓ Success")
                    
            except Exception as e:
                failed_customers.append(customer_name)
                print(f"    ❌ Error: {e}")
        
        # Summary statistics
        successful = len(results) - len(failed_customers)
        
        batch_summary = {
            'total_processed': len(customers),
            'successful': successful,
            'failed': len(failed_customers),
            'success_rate': successful / len(customers) * 100 if customers else 0,
            'failed_customers': failed_customers,
            'results': results
        }
        
        print(f"Batch complete: {successful}/{len(customers)} successful ({batch_summary['success_rate']:.1f}%)")
        
        return batch_summary

# Convenience function for simple usage
def personalize_email_simple(
    letter_content: str,
    customer: Dict[str, Any],
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Simple function to personalize email for one customer
    
    Returns:
        Dict with personalized email and validation results
    """
    orchestrator = SimpleEmailOrchestrator(api_key)
    return orchestrator.personalize_email(letter_content, customer)