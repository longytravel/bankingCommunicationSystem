"""
Simple SMS Orchestrator - Coordinates SMS Personalization Pipeline
Single responsibility: Coordinate SMS generation with content validation and rules checking
Follows same modular pattern as SimpleEmailOrchestrator
"""

import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Import existing working components
from .content_validator import ContentValidator
from .sms_channel_generator import SMSChannelGenerator

# Try to import input cleaner
try:
    from .input_cleaner import clean_letter_content
    INPUT_CLEANER_AVAILABLE = True
except ImportError:
    INPUT_CLEANER_AVAILABLE = False
    print("⚠️ Input cleaner not available, using content as-is")

# Try to import rules engine for customer eligibility
try:
    from ..config import Config
    RULES_ENGINE_AVAILABLE = True
except ImportError:
    RULES_ENGINE_AVAILABLE = False
    print("⚠️ Rules engine not available")

class SimpleSMSOrchestrator:
    """Simple orchestrator focused on SMS generation with eligibility checking"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('CLAUDE_API_KEY')
        
        # Initialize components
        self.content_validator = ContentValidator(api_key=self.api_key)
        self.sms_generator = SMSChannelGenerator(api_key=self.api_key)
        
        print("✓ Simple SMS Orchestrator initialized")
    
    def check_sms_eligibility(self, customer: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if customer is eligible for SMS based on rules
        """
        
        # Default eligibility check based on customer segments and behavior
        eligibility = {
            'eligible': False,
            'reason': 'Not eligible',
            'customer_segment': 'unknown',
            'confidence': 0.0
        }
        
        # Customer segmentation based on behavior patterns
        digital_logins = customer.get('digital_logins_per_month', 0)
        mobile_usage = customer.get('mobile_app_usage', 'Unknown')
        age = customer.get('age', 'unknown')
        branch_visits = customer.get('branch_visits_per_month', 0)
        phone_calls = customer.get('phone_calls_per_month', 0)
        
        # Determine customer segment
        segment = self._determine_customer_segment(customer)
        eligibility['customer_segment'] = segment
        
        # SMS eligibility rules based on your system's customer segments
        if segment == 'DIGITAL':
            # Digital customers: primarily app/email, but SMS for urgent notifications
            if digital_logins > 15 and mobile_usage in ['Daily', 'high']:
                eligibility['eligible'] = True
                eligibility['reason'] = 'Digital customer with high mobile engagement'
                eligibility['confidence'] = 0.8
            else:
                eligibility['reason'] = 'Digital customer prefers app notifications'
                
        elif segment == 'ASSISTED':
            # Assisted customers: perfect for SMS - hybrid digital/traditional
            eligibility['eligible'] = True
            eligibility['reason'] = 'Assisted customer - SMS is preferred channel'
            eligibility['confidence'] = 0.9
            
        elif segment == 'TRADITIONAL':
            # Traditional customers: NO SMS - they prefer letters and phone
            eligibility['reason'] = 'Traditional customer - prefers letter and phone contact'
            eligibility['confidence'] = 0.95
            
        # Age-based overrides
        if age != 'unknown' and int(age) if str(age).isdigit() else 0 > 75:
            # Very senior customers - be cautious with SMS
            eligibility['eligible'] = False
            eligibility['reason'] = 'Senior customer (75+) - phone or letter preferred'
            eligibility['confidence'] = 0.9
            
        # Mobile usage override
        if mobile_usage == 'Never' and phone_calls > 10:
            eligibility['eligible'] = False
            eligibility['reason'] = 'Customer prefers phone contact over mobile'
            
        # Digital engagement boost
        if digital_logins > 20 and mobile_usage == 'Daily':
            eligibility['eligible'] = True
            eligibility['reason'] = 'High digital engagement - SMS appropriate'
            eligibility['confidence'] = 0.85
            
        return eligibility
    
    def _determine_customer_segment(self, customer: Dict[str, Any]) -> str:
        """Determine customer segment based on behavior patterns"""
        
        digital_logins = customer.get('digital_logins_per_month', 0)
        mobile_usage = customer.get('mobile_app_usage', 'Unknown')
        branch_visits = customer.get('branch_visits_per_month', 0)
        phone_calls = customer.get('phone_calls_per_month', 0)
        age = customer.get('age', 'unknown')
        
        # DIGITAL: High digital engagement, low traditional contact
        if digital_logins > 20 and mobile_usage in ['Daily', 'high'] and branch_visits <= 1:
            return 'DIGITAL'
            
        # TRADITIONAL: Low/no digital, high traditional contact
        if digital_logins <= 5 and branch_visits >= 2 and phone_calls >= 3:
            return 'TRADITIONAL'
            
        # ASSISTED: Hybrid - some digital, some traditional
        if 5 < digital_logins <= 20 or mobile_usage in ['Weekly', 'Monthly']:
            return 'ASSISTED'
            
        # Age-based fallback
        if age != 'unknown':
            age_val = int(age) if str(age).isdigit() else 40
            if age_val > 65:
                return 'TRADITIONAL'
            elif age_val < 35:
                return 'DIGITAL'
            else:
                return 'ASSISTED'
                
        return 'ASSISTED'  # Default fallback
    
    def personalize_sms(
        self,
        letter_content: str,
        customer: Dict[str, Any],
        validate_content: bool = True,
        force_generation: bool = False
    ) -> Dict[str, Any]:
        """
        Main orchestration method for SMS personalization
        
        Args:
            letter_content: Original letter content
            customer: Customer profile data
            validate_content: Whether to run content validation
            force_generation: Force SMS generation even if not eligible
            
        Returns:
            Complete SMS personalization result with validation
        """
        
        start_time = datetime.now()
        result = {
            'customer_name': customer.get('name', 'Unknown'),
            'processing_steps': [],
            'sms': None,
            'validation': None,
            'eligibility': None,
            'errors': [],
            'warnings': []
        }
        
        try:
            # STEP 1: Check SMS eligibility
            eligibility = self.check_sms_eligibility(customer)
            result['eligibility'] = eligibility
            result['processing_steps'].append(f'✓ Eligibility checked: {eligibility["customer_segment"]}')
            
            if not eligibility['eligible'] and not force_generation:
                result['processing_steps'].append(f'⏭️ SMS skipped: {eligibility["reason"]}')
                result['sms'] = {
                    'content': '',
                    'skipped': True,
                    'skip_reason': eligibility['reason'],
                    'customer_segment': eligibility['customer_segment']
                }
                return result
            
            # STEP 2: Clean input content (if available)
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
            
            # STEP 3: Extract key points for content validation
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
            
            # STEP 4: Generate personalized SMS
            try:
                sms_result = self.sms_generator.generate_sms(
                    clean_content=cleaned_content,
                    customer=customer,
                    key_points=key_points
                )
                result['sms'] = sms_result
                result['processing_steps'].append('✓ SMS generated')
                
                # Validate the generated SMS
                sms_validation = self.sms_generator.validate_sms(
                    sms_result, 
                    cleaned_content, 
                    key_points
                )
                result['sms_validation'] = sms_validation
                result['processing_steps'].append('✓ SMS validated')
                
            except Exception as e:
                result['errors'].append(f"SMS generation failed: {e}")
                return result
            
            # STEP 5: Content validation against original (if requested)
            if validate_content and key_points:
                try:
                    # Create personalized content dict for validator
                    personalized_content = {
                        'email': '',
                        'sms': sms_result['content'],
                        'app': '',
                        'letter': ''
                    }
                    
                    # Use existing validation system
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
                    sms_coverage = validation_report.get('by_channel', {}).get('sms', {}).get('coverage', 0)
                    if sms_coverage < 60:  # SMS has lower expectations than email
                        result['warnings'].append(f"SMS content coverage only {sms_coverage:.0f}%")
                    
                except Exception as e:
                    result['warnings'].append(f"Content validation failed: {e}")
            
            # STEP 6: Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            result['processing_time'] = processing_time
            result['processing_steps'].append(f'✓ Completed in {processing_time:.2f}s')
            
        except Exception as e:
            result['errors'].append(f"SMS orchestration failed: {e}")
        
        return result
    
    def get_sms_summary(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Get a summary of the SMS personalization result"""
        
        eligibility = result.get('eligibility', {})
        
        if not eligibility.get('eligible', False) and not result.get('sms', {}).get('content'):
            return {
                'status': 'skipped',
                'message': eligibility.get('reason', 'Not eligible for SMS'),
                'customer_segment': eligibility.get('customer_segment', 'unknown')
            }
        
        if not result.get('sms'):
            return {'status': 'failed', 'message': 'SMS generation failed'}
        
        sms_result = result['sms']
        sms_validation = result.get('sms_validation', {})
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
        sms_quality = sms_validation.get('quality_score', 0)
        content_coverage = content_validation.get('by_channel', {}).get('sms', {}).get('coverage', 100) / 100
        overall_quality = (sms_quality + content_coverage) / 2
        
        summary = {
            'status': status,
            'customer': result['customer_name'],
            'customer_segment': eligibility.get('customer_segment', 'unknown'),
            'overall_quality': overall_quality,
            'character_count': sms_result.get('character_count', 0),
            'segment_count': sms_result.get('segment_count', 0),
            'personalization_factors': len(sms_result.get('personalization_factors', [])),
            'processing_time': result.get('processing_time', 0),
            'content_coverage': content_coverage * 100,
            'errors': result.get('errors', []),
            'warnings': result.get('warnings', []),
            'processing_steps': result.get('processing_steps', [])
        }
        
        return summary
    
    def batch_personalize_sms(
        self,
        letter_content: str,
        customers: List[Dict[str, Any]],
        validate_content: bool = True,
        max_customers: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Batch process multiple customers for SMS personalization
        
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
        skipped_customers = []
        
        print(f"Processing {len(customers)} customers for SMS personalization...")
        
        for i, customer in enumerate(customers):
            customer_name = customer.get('name', f'Customer_{i}')
            print(f"  {i+1}/{len(customers)}: {customer_name}")
            
            try:
                result = self.personalize_sms(letter_content, customer, validate_content)
                results.append(result)
                
                # Quick status check
                if result.get('errors'):
                    failed_customers.append(customer_name)
                    print(f"    ❌ Failed: {result['errors'][0]}")
                elif result.get('sms', {}).get('skipped'):
                    skipped_customers.append(customer_name)
                    print(f"    ⏭️ Skipped: {result['sms']['skip_reason']}")
                elif result.get('warnings'):
                    print(f"    ⚠️ Completed with warnings")
                else:
                    print(f"    ✅ Success")
                    
            except Exception as e:
                failed_customers.append(customer_name)
                print(f"    ❌ Error: {e}")
        
        # Summary statistics
        successful = len([r for r in results if r.get('sms', {}).get('content') and not r.get('errors')])
        skipped = len([r for r in results if r.get('sms', {}).get('skipped')])
        
        batch_summary = {
            'total_processed': len(customers),
            'successful': successful,
            'skipped': skipped,
            'failed': len(failed_customers),
            'success_rate': successful / len(customers) * 100 if customers else 0,
            'skip_rate': skipped / len(customers) * 100 if customers else 0,
            'failed_customers': failed_customers,
            'skipped_customers': skipped_customers,
            'results': results
        }
        
        print(f"Batch complete: {successful}/{len(customers)} SMS generated ({batch_summary['success_rate']:.1f}%), {skipped} skipped")
        
        return batch_summary

# Convenience function for simple usage
def personalize_sms_simple(
    letter_content: str,
    customer: Dict[str, Any],
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Simple function to personalize SMS for one customer
    
    Returns:
        Dict with personalized SMS and validation results
    """
    orchestrator = SimpleSMSOrchestrator(api_key)
    return orchestrator.personalize_sms(letter_content, customer)