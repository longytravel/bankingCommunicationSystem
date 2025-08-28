"""
Quick test script to verify personalization works
Run this directly to test without the UI
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from core.personalization_engine import PersonalizationEngine
import json

# Sample letter content
SAMPLE_LETTER = """
Important: Changes to your account terms and conditions

Dear Customer,

We are writing to inform you of important changes to the terms and conditions of your account. 
These changes will take effect on March 1, 2025.

Key changes:
- Overdraft interest will be calculated daily instead of monthly
- Unpaid transaction fees increase from £5 to £7.50
- You can now cancel future payments until 11:59pm the day before

You don't need to take action unless you disagree with the changes. 
If you have questions, contact us at 0345 300 0000.

Sincerely,
Lloyds Bank
"""

# Test customers with different profiles
TEST_CUSTOMERS = [
    {
        'customer_id': 'CUST001',
        'name': 'Sarah Johnson',
        'age': 28,
        'preferred_language': 'English',
        'account_balance': 15000,
        'income_level': 'High',
        'digital_logins_per_month': 45,
        'mobile_app_usage': 'Daily',
        'recent_life_events': 'New job',
        'family_status': 'Single',
        'accessibility_needs': 'None',
        'employment_status': 'Employed'
    },
    {
        'customer_id': 'CUST002',
        'name': 'Ahmad Khan',
        'age': 67,
        'preferred_language': 'Urdu',
        'account_balance': 3500,
        'income_level': 'Low',
        'digital_logins_per_month': 2,
        'mobile_app_usage': 'Never',
        'recent_life_events': 'Retirement',
        'family_status': 'Married',
        'accessibility_needs': 'Large print required',
        'employment_status': 'Retired'
    },
    {
        'customer_id': 'CUST003',
        'name': 'Maria Rodriguez',
        'age': 45,
        'preferred_language': 'Spanish',
        'account_balance': 8000,
        'income_level': 'Medium',
        'digital_logins_per_month': 12,
        'mobile_app_usage': 'Weekly',
        'recent_life_events': 'New baby',
        'family_status': 'Married with children',
        'accessibility_needs': 'None',
        'employment_status': 'Employed'
    },
    {
        'customer_id': 'CUST004',
        'name': 'Wojciech Kowalski',
        'age': 35,
        'preferred_language': 'Polish',
        'account_balance': 500,
        'income_level': 'Low',
        'digital_logins_per_month': 20,
        'mobile_app_usage': 'Daily',
        'recent_life_events': 'None',
        'family_status': 'Single',
        'accessibility_needs': 'None',
        'employment_status': 'Self-employed'
    }
]

def test_personalization():
    """Test the personalization engine"""
    
    print("=" * 60)
    print("LLOYDS PERSONALIZATION ENGINE TEST")
    print("=" * 60)
    
    # Initialize engine
    engine = PersonalizationEngine()
    print(f"\n✓ Engine initialized (Mock mode: {engine.use_mock})")
    
    # Test each customer
    for customer in TEST_CUSTOMERS:
        print(f"\n{'='*60}")
        print(f"Testing: {customer['name']}")
        print(f"Profile: {customer['age']} years, {customer['preferred_language']}, "
              f"£{customer['account_balance']:,} balance, {customer['digital_logins_per_month']} logins/month")
        print("-" * 40)
        
        # Generate personalization
        result = engine.personalize_letter(SAMPLE_LETTER, customer)
        
        # Show results
        print(f"\n📧 EMAIL (in {customer['preferred_language']}):")
        print(result['email'][:200] + "..." if len(result['email']) > 200 else result['email'])
        
        print(f"\n📱 SMS:")
        print(result['sms'])
        
        print(f"\n📲 APP NOTIFICATION:")
        print(result['app'])
        
        if 'metadata' in result:
            print(f"\n🎯 Personalization Factors:")
            for factor in result['metadata']['personalization_factors']:
                print(f"  • {factor}")
        
        print("\n" + "="*60)
        
        # Ask to continue
        input("\nPress Enter to test next customer...")

def quick_test_single():
    """Quick test with a single customer"""
    print("\n" + "="*60)
    print("QUICK SINGLE CUSTOMER TEST")
    print("="*60)
    
    engine = PersonalizationEngine()
    
    # Test with one customer
    customer = TEST_CUSTOMERS[0]
    result = engine.personalize_letter(SAMPLE_LETTER, customer)
    
    print(f"\nCustomer: {customer['name']}")
    print(f"Language: {customer['preferred_language']}")
    print(f"\nPersonalized Email Preview:")
    print(result['email'])
    
    # Save to file for inspection
    output_file = Path('personalization_test_output.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Full output saved to: {output_file}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--quick':
        quick_test_single()
    else:
        test_personalization()