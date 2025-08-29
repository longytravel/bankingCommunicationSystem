"""
Voice Note Integration - Combines personalization with voice generation
Shows how to integrate voice notes into the existing system
"""

import sys
import os
from pathlib import Path
import pandas as pd
import json
from typing import Dict, Any, List, Optional

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.core.personalization_engine import PersonalizationEngine
from src.core.voice_note_generator import VoiceNoteGenerator
from src.core.rules_engine import RulesEngine

class PersonalizationWithVoice:
    """Integrated personalization and voice note generation"""
    
    def __init__(self):
        """Initialize all components"""
        self.personalization_engine = PersonalizationEngine()
        self.voice_generator = VoiceNoteGenerator()
        self.rules_engine = RulesEngine(
            str(Path(__file__).parent.parent / 'data' / 'rules' / 'communication_rules.json')
        )
        
        # Statistics tracking
        self.stats = {
            'customers_processed': 0,
            'personalizations_created': 0,
            'voice_notes_created': 0,
            'channels_used': {}
        }
    
    def process_customer(
        self,
        letter_content: str,
        customer: Dict[str, Any],
        document_metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Process a single customer: personalize content and generate voice note if eligible
        
        Args:
            letter_content: Original letter text
            customer: Customer profile data
            document_metadata: Optional document classification and metadata
            
        Returns:
            Complete personalization result with voice note if applicable
        """
        result = {
            'customer_id': customer.get('customer_id'),
            'customer_name': customer.get('name'),
            'channels': {}
        }
        
        # Step 1: Generate personalized content
        print(f"\n📝 Personalizing for {customer.get('name')}...")
        personalized = self.personalization_engine.personalize_letter(letter_content, customer)
        
        # Store personalized content
        result['channels']['email'] = personalized.get('email', '')
        result['channels']['sms'] = personalized.get('sms', '')
        result['channels']['app'] = personalized.get('app', '')
        result['channels']['letter'] = personalized.get('letter', '')
        
        # Step 2: Check if voice note should be generated
        voice_decision = self.voice_generator.should_generate_voice_note(customer, document_metadata)
        
        if voice_decision['generate']:
            print(f"🎙️ Generating voice note for {customer.get('name')}...")
            
            # Use the app notification text for voice (it's concise)
            voice_text = personalized.get('app', '')
            
            # If app text is too short, use email intro
            if len(voice_text) < 50:
                email_text = personalized.get('email', '')
                # Extract first paragraph or first 500 chars
                voice_text = email_text[:500] if email_text else voice_text
            
            # Generate voice note
            voice_result = self.voice_generator.generate_voice_note(
                text=voice_text,
                customer=customer,
                document=document_metadata
            )
            
            if voice_result:
                result['channels']['voice_note'] = voice_result
                result['voice_generated'] = True
                print(f"✅ Voice note created: {voice_result['filename']}")
            else:
                result['voice_generated'] = False
                print(f"⚠️ Voice note generation failed")
        else:
            result['voice_generated'] = False
            result['voice_skip_reason'] = voice_decision['reason']
            print(f"⏭️ Voice note skipped: {voice_decision['reason']}")
        
        # Update statistics
        self.stats['customers_processed'] += 1
        self.stats['personalizations_created'] += 1
        if result.get('voice_generated'):
            self.stats['voice_notes_created'] += 1
        
        for channel in result['channels'].keys():
            self.stats['channels_used'][channel] = self.stats['channels_used'].get(channel, 0) + 1
        
        return result
    
    def batch_process(
        self,
        letter_file: str,
        customers_file: str,
        document_type: str = 'INFORMATIONAL',
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Process multiple customers in batch
        
        Args:
            letter_file: Path to letter file
            customers_file: Path to customer CSV/Excel file
            document_type: Classification of document (REGULATORY/PROMOTIONAL/INFORMATIONAL)
            limit: Optional limit on number of customers to process
            
        Returns:
            List of processing results
        """
        print("=" * 60)
        print("BATCH PERSONALIZATION WITH VOICE NOTES")
        print("=" * 60)
        
        # Load letter
        with open(letter_file, 'r') as f:
            letter_content = f.read()
        print(f"✅ Loaded letter: {Path(letter_file).name}")
        
        # Load customers
        if customers_file.endswith('.csv'):
            customers_df = pd.read_csv(customers_file)
        else:
            customers_df = pd.read_excel(customers_file)
        
        print(f"✅ Loaded {len(customers_df)} customers")
        
        # Apply limit if specified
        if limit:
            customers_df = customers_df.head(limit)
            print(f"📊 Processing first {limit} customers")
        
        # Document metadata
        document_metadata = {
            'classification': document_type,
            'urgency': 'normal',
            'compliance_required': document_type == 'REGULATORY'
        }
        
        # Process each customer
        results = []
        for idx, customer_row in customers_df.iterrows():
            customer = customer_row.to_dict()
            print(f"\n--- Customer {idx + 1}/{len(customers_df)} ---")
            
            result = self.process_customer(letter_content, customer, document_metadata)
            results.append(result)
        
        # Print summary
        self.print_summary()
        
        # Save results
        self.save_results(results)
        
        return results
    
    def print_summary(self):
        """Print processing summary"""
        print("\n" + "=" * 60)
        print("PROCESSING SUMMARY")
        print("=" * 60)
        print(f"Customers Processed: {self.stats['customers_processed']}")
        print(f"Personalizations Created: {self.stats['personalizations_created']}")
        print(f"Voice Notes Generated: {self.stats['voice_notes_created']}")
        
        if self.stats['customers_processed'] > 0:
            voice_rate = (self.stats['voice_notes_created'] / self.stats['customers_processed']) * 100
            print(f"Voice Generation Rate: {voice_rate:.1f}%")
        
        print("\nChannels Used:")
        for channel, count in self.stats['channels_used'].items():
            print(f"  - {channel}: {count}")
        
        # Get voice generation statistics
        voice_stats = self.voice_generator.get_statistics()
        if voice_stats['skip_reasons']:
            print("\nVoice Skip Reasons:")
            for reason, count in voice_stats['skip_reasons'].items():
                print(f"  - {reason}: {count}")
    
    def save_results(self, results: List[Dict[str, Any]]):
        """Save processing results to file"""
        output_dir = Path(__file__).parent.parent / 'data' / 'output'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f'voice_integration_results_{timestamp}.json'
        
        with open(output_file, 'w') as f:
            json.dump({
                'results': results,
                'statistics': self.stats,
                'voice_statistics': self.voice_generator.get_statistics()
            }, f, indent=2)
        
        print(f"\n📁 Results saved to: {output_file}")

def example_usage():
    """Example of how to use the integrated system"""
    
    # Initialize the integrated system
    system = PersonalizationWithVoice()
    
    # Example 1: Process a single customer
    print("\n" + "=" * 60)
    print("EXAMPLE 1: Single Customer Processing")
    print("=" * 60)
    
    # Sample customer (digitally active - should get voice note)
    digital_customer = {
        'customer_id': 'CUST001',
        'name': 'Sarah Johnson',
        'age': 32,
        'preferred_language': 'English',
        'account_balance': 15000,
        'digital_logins_per_month': 25,  # High digital activity
        'mobile_app_usage': 'Daily',     # Active app user
        'email_opens_per_month': 18,
        'recent_life_events': 'New job',
        'accessibility_needs': 'None'
    }
    
    sample_letter = """
    Important Update About Your Account
    
    Dear Customer,
    
    We wanted to let you know about exciting new features available in your mobile app.
    You can now set spending limits, track savings goals, and get instant notifications.
    
    These features are designed to help you manage your money more effectively.
    
    Best regards,
    Lloyds Bank
    """
    
    result = system.process_customer(
        letter_content=sample_letter,
        customer=digital_customer,
        document_metadata={'classification': 'INFORMATIONAL'}
    )
    
    print(f"\n✅ Processing complete for {digital_customer['name']}")
    print(f"Voice note generated: {result.get('voice_generated', False)}")
    
    # Example 2: Process a traditional customer (should NOT get voice note)
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Traditional Customer Processing")
    print("=" * 60)
    
    traditional_customer = {
        'customer_id': 'CUST002',
        'name': 'Robert Thompson',
        'age': 68,
        'preferred_language': 'English',
        'account_balance': 8000,
        'digital_logins_per_month': 1,   # Very low digital activity
        'mobile_app_usage': 'Never',     # Doesn't use app
        'email_opens_per_month': 2,
        'branch_visits_per_month': 3,
        'accessibility_needs': 'Large print required'
    }
    
    result = system.process_customer(
        letter_content=sample_letter,
        customer=traditional_customer,
        document_metadata={'classification': 'INFORMATIONAL'}
    )
    
    print(f"\n✅ Processing complete for {traditional_customer['name']}")
    print(f"Voice note generated: {result.get('voice_generated', False)}")
    if not result.get('voice_generated'):
        print(f"Reason: {result.get('voice_skip_reason', 'Unknown')}")

def test_rules_only():
    """Test just the rules engine to see decision making"""
    print("\n" + "=" * 60)
    print("TESTING RULES ENGINE DECISIONS")
    print("=" * 60)
    
    voice_gen = VoiceNoteGenerator()
    
    # Test different customer profiles
    test_profiles = [
        {
            'name': 'Digital Native',
            'customer': {
                'name': 'Emma Wilson',
                'age': 25,
                'digital_logins_per_month': 30,
                'mobile_app_usage': 'Daily',
                'accessibility_needs': 'None'
            }
        },
        {
            'name': 'Traditional Senior',
            'customer': {
                'name': 'George Brown',
                'age': 75,
                'digital_logins_per_month': 0,
                'mobile_app_usage': 'Never',
                'accessibility_needs': 'None'
            }
        },
        {
            'name': 'Hearing Impaired',
            'customer': {
                'name': 'Lisa Chen',
                'age': 45,
                'digital_logins_per_month': 20,
                'mobile_app_usage': 'Daily',
                'accessibility_needs': 'Hearing impaired'
            }
        },
        {
            'name': 'Premium Customer',
            'customer': {
                'name': 'James Mitchell',
                'age': 50,
                'account_balance': 75000,
                'years_with_bank': 15,
                'digital_logins_per_month': 15,
                'mobile_app_usage': 'Weekly'
            }
        }
    ]
    
    for profile in test_profiles:
        print(f"\n📊 Testing: {profile['name']}")
        decision = voice_gen.should_generate_voice_note(profile['customer'])
        print(f"  Generate Voice: {'✅ Yes' if decision['generate'] else '❌ No'}")
        print(f"  Reason: {decision['reason']}")
        if decision['triggered_rules']:
            print(f"  Triggered Rules: {', '.join(decision['triggered_rules'])}")
        if decision.get('voice_style'):
            print(f"  Voice Style: {decision['voice_style']}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--test-rules':
            test_rules_only()
        elif sys.argv[1] == '--batch':
            # Example batch processing
            system = PersonalizationWithVoice()
            
            # Use the sample files from your project
            letter_file = Path(__file__).parent.parent / 'data' / 'input' / 'letters' / 'Letter_2_Informational.txt'
            customers_file = Path(__file__).parent.parent / 'data' / 'input' / 'customers' / 'customers.csv'
            
            if letter_file.exists() and customers_file.exists():
                system.batch_process(
                    str(letter_file),
                    str(customers_file),
                    document_type='INFORMATIONAL',
                    limit=5  # Process first 5 customers
                )
            else:
                print("Sample files not found. Please ensure letter and customer files exist.")
    else:
        # Run examples
        example_usage()