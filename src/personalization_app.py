"""
Lloyds Personalization UI - Clean Final Version
No test letters - requires real letter upload
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import re

sys.path.append(str(Path(__file__).parent.parent))
from core.personalization_engine import PersonalizationEngine

# Page config
st.set_page_config(
    page_title="Lloyds AI Personalization Engine",
    page_icon="🏦",
    layout="wide"
)

# Clean styling
st.markdown("""
<style>
    .main {padding-top: 1rem;}
    .stButton>button {
        background-color: #006A4D;
        color: white;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.2rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize
if 'engine' not in st.session_state:
    st.session_state.engine = PersonalizationEngine()
if 'current_result' not in st.session_state:
    st.session_state.current_result = None
if 'key_points' not in st.session_state:
    st.session_state.key_points = []

def extract_key_points(letter_text):
    """Extract specific key points from the original letter"""
    key_points = []
    text_lower = letter_text.lower()
    
    # Dates
    if "march 1, 2025" in text_lower or "1 march 2025" in text_lower:
        key_points.append({"point": "Effective date: March 1, 2025", "critical": True})
    elif "effective" in text_lower:
        date_match = re.search(r'effective\s+([^,\n]+)', letter_text)
        if date_match:
            key_points.append({"point": f"Effective date: {date_match.group(1).strip()}", "critical": True})
    
    # Specific changes
    if "overdraft interest" in text_lower and "daily" in text_lower:
        key_points.append({"point": "Overdraft interest calculated DAILY (not monthly)", "critical": True})
    
    if "£7.50" in letter_text or "7.50" in letter_text:
        if "£5" in letter_text or "5" in letter_text:
            key_points.append({"point": "Fee increase: £5 → £7.50 for unpaid transactions", "critical": True})
        else:
            key_points.append({"point": "Fee amount: £7.50", "critical": True})
    
    if "11:59pm" in letter_text:
        key_points.append({"point": "Payment cancellation cutoff: 11:59pm day before", "critical": True})
    
    # Contact information
    if "0345 300 0000" in letter_text:
        key_points.append({"point": "Contact number: 0345 300 0000", "critical": True})
    elif "0345" in letter_text:
        key_points.append({"point": "Contact number provided (0345...)", "critical": True})
    
    # Action requirements
    if "no action" in text_lower or "don't need to" in text_lower:
        key_points.append({"point": "NO ACTION required (unless customer disagrees)", "critical": True})
    
    if "disagree" in text_lower:
        key_points.append({"point": "Customer can reject changes if they disagree", "critical": False})
    
    if "branch" in text_lower:
        key_points.append({"point": "Branch visit option mentioned", "critical": False})
    
    if "terms and conditions" in text_lower:
        key_points.append({"point": "Terms and conditions change notification", "critical": True})
    
    # Find amounts
    amounts = re.findall(r'£\d+(?:\.\d{2})?', letter_text)
    for amount in amounts:
        if amount not in ["£5", "£7.50"]:
            key_points.append({"point": f"Amount mentioned: {amount}", "critical": False})
    
    return key_points

def check_content_completeness(original_points, personalized_content):
    """Check if personalized content includes all key points"""
    all_content = ""
    for key, value in personalized_content.items():
        if value:
            all_content += str(value).lower()
    
    validated_points = []
    for point_data in original_points:
        point = point_data["point"]
        critical = point_data["critical"]
        found = False
        
        if "March 1, 2025" in point:
            found = "march 1" in all_content or "1 march" in all_content
        elif "£7.50" in point:
            found = "7.50" in all_content
        elif "£5" in point and "£7.50" in point:
            found = ("5" in all_content or "five" in all_content) and ("7.50" in all_content)
        elif "daily" in point.lower():
            found = "daily" in all_content or "cada día" in all_content or "يوميا" in all_content
        elif "11:59pm" in point:
            found = "11:59" in all_content or "23:59" in all_content
        elif "0345" in point:
            found = "0345" in all_content
        elif "NO ACTION" in point:
            found = "no action" in all_content or "don't need" in all_content
        elif "Terms and conditions" in point:
            found = "terms" in all_content or "conditions" in all_content
        else:
            key_words = point.lower().split()
            found = any(word in all_content for word in key_words if len(word) > 3)
        
        validated_points.append({
            "point": point,
            "critical": critical,
            "found": found
        })
    
    return validated_points

def analyze_personalization(customer):
    """Generate comprehensive personalization analysis using ALL customer data"""
    factors = []
    
    # 1. LANGUAGE & CULTURAL
    lang = customer.get('preferred_language', 'English')
    if lang != 'English':
        factors.append({
            'category': 'LANGUAGE',
            'factor': f'Full translation to {lang}',
            'detail': f'Complete content adaptation for {lang} speakers with appropriate cultural norms and local banking terminology',
            'importance': 'HIGH'
        })
    
    # 2. AGE-BASED COMMUNICATION STYLE
    age = customer.get('age', 0)
    if isinstance(age, (int, float)) and age > 0:
        if age < 30:
            factors.append({
                'category': 'TONE',
                'factor': 'Modern, digital-native communication',
                'detail': f'Age {age}: Contemporary language, brief sentences, app-first approach, emoji-appropriate for digital channels',
                'importance': 'HIGH'
            })
        elif age > 60:
            factors.append({
                'category': 'TONE',
                'factor': 'Traditional, respectful communication',
                'detail': f'Age {age}: Formal salutation (Mr/Mrs), detailed explanations, avoiding technical jargon, larger font suggestions',
                'importance': 'HIGH'
            })
        else:
            factors.append({
                'category': 'TONE',
                'factor': 'Professional yet approachable',
                'detail': f'Age {age}: Balanced formality, clear but not patronizing, mix of digital and traditional options',
                'importance': 'MEDIUM'
            })
    
    # 3. DIGITAL ENGAGEMENT LEVEL
    digital = customer.get('digital_logins_per_month', 0)
    app_usage = customer.get('mobile_app_usage', 'Unknown')
    
    if digital > 20:
        factors.append({
            'category': 'CHANNEL',
            'factor': 'Heavy digital user optimization',
            'detail': f'{digital} logins/month + {app_usage} app use: Push notifications prioritized, self-service features highlighted, QR codes for quick actions',
            'importance': 'HIGH'
        })
    elif digital < 5:
        factors.append({
            'category': 'CHANNEL',
            'factor': 'Traditional banking preference',
            'detail': f'Only {digital} logins/month: Branch locations emphasized, phone support prominent, printed materials offered, step-by-step guidance',
            'importance': 'HIGH'
        })
    else:
        factors.append({
            'category': 'CHANNEL',
            'factor': 'Hybrid user approach',
            'detail': f'{digital} logins/month: Both digital and traditional options presented equally',
            'importance': 'MEDIUM'
        })
    
    # 4. EMAIL ENGAGEMENT PATTERN
    email_opens = customer.get('email_opens_per_month', 0)
    if email_opens > 15:
        factors.append({
            'category': 'ENGAGEMENT',
            'factor': 'High email engagement',
            'detail': f'{email_opens} opens/month: Detailed content welcomed, multiple touchpoints effective, newsletter subscriptions likely valued',
            'importance': 'MEDIUM'
        })
    elif email_opens < 5:
        factors.append({
            'category': 'ENGAGEMENT',
            'factor': 'Low email engagement',
            'detail': f'{email_opens} opens/month: Keep emails brief and critical only, subject lines must be compelling, consider alternative channels',
            'importance': 'MEDIUM'
        })
    
    # 5. FINANCIAL SITUATION & OPPORTUNITIES
    balance = customer.get('account_balance', 0)
    income = customer.get('income_level', 'Unknown')
    transactions = customer.get('recent_transactions', 0)
    
    if balance > 20000:
        factors.append({
            'category': 'FINANCIAL',
            'factor': 'High-value customer treatment',
            'detail': f'£{balance:,} balance + {income} income + {transactions} transactions: Premier banking eligibility, wealth management options, exclusive rates mentioned',
            'importance': 'HIGH'
        })
    elif balance < 1000:
        factors.append({
            'category': 'FINANCIAL',
            'factor': 'Financial support emphasis',
            'detail': f'£{balance:,} balance: Fee waiver options highlighted, budgeting tools promoted, financial wellbeing resources, overdraft alternatives',
            'importance': 'HIGH'
        })
    else:
        factors.append({
            'category': 'FINANCIAL',
            'factor': 'Standard banking tier',
            'detail': f'£{balance:,} balance: Growth opportunities mentioned, savings account suggestions',
            'importance': 'LOW'
        })
    
    # 6. LIFE EVENTS ACKNOWLEDGMENT
    events = customer.get('recent_life_events', 'None')
    if events and events.lower() not in ['none', 'n/a', '', 'unknown']:
        event_responses = {
            'marriage': 'Joint account options, name change services, combined financial planning',
            'baby': 'Junior ISA information, child trust fund, family insurance products',
            'bereavement': 'Compassionate tone, extended deadlines, dedicated bereavement team contact',
            'job': 'Income protection options, mortgage pre-approval, career-related banking services',
            'retirement': 'Pension services, senior account benefits, estate planning',
            'house': 'Mortgage products, home insurance, moving home checklist'
        }
        
        for key, response in event_responses.items():
            if key in events.lower():
                factors.append({
                    'category': 'LIFE EVENT',
                    'factor': f'{events} acknowledgment',
                    'detail': response,
                    'importance': 'HIGH'
                })
                break
        else:
            factors.append({
                'category': 'LIFE EVENT',
                'factor': f'{events} acknowledgment',
                'detail': f'Personalized reference and relevant services for {events}',
                'importance': 'MEDIUM'
            })
    
    # 7. CUSTOMER LOYALTY & TENURE
    years = customer.get('years_with_bank', 0)
    if years > 10:
        factors.append({
            'category': 'LOYALTY',
            'factor': f'Long-term customer ({years} years)',
            'detail': 'Loyalty acknowledgment, exclusive long-term customer benefits, priority service eligibility',
            'importance': 'HIGH'
        })
    elif years > 5:
        factors.append({
            'category': 'LOYALTY',
            'factor': f'Established customer ({years} years)',
            'detail': 'Relationship appreciation, upgrade opportunities highlighted',
            'importance': 'MEDIUM'
        })
    elif years <= 1:
        factors.append({
            'category': 'LOYALTY',
            'factor': 'New customer',
            'detail': 'Welcome offers, onboarding support, getting started guides',
            'importance': 'MEDIUM'
        })
    
    # 8. SUPPORT NEEDS
    requires_support = customer.get('requires_support', False)
    accessibility = customer.get('accessibility_needs', 'None')
    
    if requires_support or (accessibility and accessibility.lower() not in ['none', 'n/a', '', 'null']):
        factors.append({
            'category': 'SUPPORT',
            'factor': f'Enhanced support required',
            'detail': f'Accessibility: {accessibility}, Support needed: {requires_support} - Simplified language, larger fonts offered, dedicated support line, alternative formats available',
            'importance': 'HIGH'
        })
    
    # 9. CONTACT PREFERENCES
    phone_calls = customer.get('phone_calls_per_month', 0)
    branch_visits = customer.get('branch_visits_per_month', 0)
    
    if phone_calls > 3:
        factors.append({
            'category': 'CONTACT',
            'factor': f'Phone preference ({phone_calls} calls/month)',
            'detail': 'Callback services offered, direct line numbers provided, phone banking emphasized',
            'importance': 'MEDIUM'
        })
    
    if branch_visits > 2:
        factors.append({
            'category': 'CONTACT',
            'factor': f'Branch visitor ({branch_visits} visits/month)',
            'detail': 'Nearest branch location highlighted, appointment booking offered, in-person service benefits mentioned',
            'importance': 'MEDIUM'
        })
    
    # 10. ACCOUNT TYPE SPECIFIC
    account_type = customer.get('account_type', 'Unknown')
    if account_type and account_type != 'Unknown':
        factors.append({
            'category': 'ACCOUNT',
            'factor': f'{account_type} account holder',
            'detail': f'Specific features and benefits for {account_type} account highlighted, upgrade paths shown',
            'importance': 'LOW'
        })
    
    # 11. EMPLOYMENT STATUS
    employment = customer.get('employment_status', 'Unknown')
    if employment.lower() == 'self-employed':
        factors.append({
            'category': 'EMPLOYMENT',
            'factor': 'Self-employed customer',
            'detail': 'Business banking options, tax season support, flexible overdraft mentioned',
            'importance': 'MEDIUM'
        })
    elif employment.lower() == 'retired':
        factors.append({
            'category': 'EMPLOYMENT',
            'factor': 'Retired customer',
            'detail': 'Fixed income considerations, pension services, senior benefits highlighted',
            'importance': 'MEDIUM'
        })
    elif employment.lower() == 'student':
        factors.append({
            'category': 'EMPLOYMENT',
            'factor': 'Student customer',
            'detail': 'Student account benefits, overdraft options, financial education resources',
            'importance': 'MEDIUM'
        })
    
    # 12. FAMILY SITUATION
    family = customer.get('family_status', 'Unknown')
    if 'children' in family.lower():
        factors.append({
            'category': 'FAMILY',
            'factor': 'Parent/Family account holder',
            'detail': 'Family financial products, children savings accounts, family insurance mentioned',
            'importance': 'LOW'
        })
    
    # 13. DIGITAL PREFERENCE FLAG
    prefers_digital = customer.get('prefers_digital', False)
    if prefers_digital:
        factors.append({
            'category': 'PREFERENCE',
            'factor': 'Digital-first preference confirmed',
            'detail': 'Paperless options emphasized, digital signatures offered, app features prioritized',
            'importance': 'MEDIUM'
        })
    
    return factors

# Header
st.title("🏦 Lloyds AI Personalization Engine")
st.markdown("Transform generic letters into personalized communications")
st.markdown("---")

# Two columns
col1, col2 = st.columns([1, 2])

# LEFT COLUMN - Inputs
with col1:
    st.header("📥 Inputs")
    
    # Letter upload (REQUIRED)
    st.subheader("1. Upload Letter")
    letter_file = st.file_uploader(
        "Select letter to personalize",
        type=['txt', 'docx', 'pdf'],
        help="Upload the generic letter that needs personalization"
    )
    
    if letter_file:
        letter_content = letter_file.read().decode('utf-8') if letter_file.type == 'text/plain' else str(letter_file.read())
        st.session_state.key_points = extract_key_points(letter_content)
        
        with st.expander("View Letter & Key Points"):
            st.text(letter_content[:500] + "..." if len(letter_content) > 500 else letter_content)
            
            critical = [p for p in st.session_state.key_points if p['critical']]
            other = [p for p in st.session_state.key_points if not p['critical']]
            
            if critical:
                st.markdown("**Critical Information:**")
                for point in critical:
                    st.write(f"🔴 {point['point']}")
            if other:
                st.markdown("**Additional Information:**")
                for point in other:
                    st.write(f"🔵 {point['point']}")
    else:
        st.warning("Please upload a letter to personalize")
        letter_content = None
    
    # Customer data upload
    st.subheader("2. Upload Customer Data")
    customer_file = st.file_uploader(
        "Select customer CSV",
        type=['csv', 'xlsx']
    )
    
    if customer_file and letter_content:
        customers_df = pd.read_csv(customer_file) if customer_file.type == 'text/csv' else pd.read_excel(customer_file)
        st.success(f"Loaded {len(customers_df)} customers")
        
        # Customer selector
        st.subheader("3. Select Customer")
        customer_names = [f"{row['name']} (ID: {row['customer_id']})" 
                         for _, row in customers_df.iterrows()]
        
        selected_customer_name = st.selectbox("Choose customer:", customer_names)
        
        idx = customer_names.index(selected_customer_name)
        selected_customer = customers_df.iloc[idx].to_dict()
        
        # Show profile
        with st.expander("Customer Profile"):
            col_a, col_b = st.columns(2)
            with col_a:
                st.write(f"**Age:** {selected_customer.get('age', 'N/A')}")
                st.write(f"**Language:** {selected_customer.get('preferred_language', 'English')}")
                st.write(f"**Balance:** £{selected_customer.get('account_balance', 0):,}")
            with col_b:
                st.write(f"**Digital:** {selected_customer.get('digital_logins_per_month', 0)}/month")
                st.write(f"**Life Events:** {selected_customer.get('recent_life_events', 'None')}")
                st.write(f"**Accessibility:** {selected_customer.get('accessibility_needs', 'None')}")
        
        # Generate button
        if st.button("🚀 Generate Personalization", type="primary", use_container_width=True):
            with st.spinner(f"Personalizing for {selected_customer['name']}..."):
                result = st.session_state.engine.personalize_letter(letter_content, selected_customer)
                factors = analyze_personalization(selected_customer)
                
                st.session_state.current_result = {
                    'customer': selected_customer,
                    'content': result,
                    'factors': factors
                }
                st.success("✓ Personalization complete!")
                st.rerun()

# RIGHT COLUMN - Results
with col2:
    st.header("📤 Personalized Output")
    
    if st.session_state.current_result:
        result = st.session_state.current_result
        customer = result['customer']
        content = result['content']
        factors = result['factors']
        
        # Customer summary
        col_1, col_2, col_3, col_4 = st.columns(4)
        with col_1:
            st.metric("Customer", customer['name'])
        with col_2:
            st.metric("Language", customer.get('preferred_language', 'English'))
        with col_3:
            st.metric("Age", customer.get('age', 'Unknown'))
        with col_4:
            digital = customer.get('digital_logins_per_month', 0)
            st.metric("Type", "Digital" if digital > 10 else "Traditional")
        
        # Content Validation (Collapsed)
        with st.expander("✅ **Content Completeness Check**", expanded=False):
            validated_points = check_content_completeness(st.session_state.key_points, content)
            critical_points = [p for p in validated_points if p['critical']]
            other_points = [p for p in validated_points if not p['critical']]
            
            if critical_points:
                st.markdown("**🔴 CRITICAL INFORMATION:**")
                for item in critical_points:
                    if item['found']:
                        st.success(f"✅ {item['point']}")
                    else:
                        st.error(f"❌ MISSING: {item['point']}")
            
            if other_points:
                st.markdown("**🔵 ADDITIONAL INFORMATION:**")
                for item in other_points:
                    if item['found']:
                        st.info(f"✅ {item['point']}")
                    else:
                        st.warning(f"⚠️ Not found: {item['point']}")
            
            total_critical = len(critical_points)
            found_critical = sum(1 for p in critical_points if p['found'])
            
            if found_critical == total_critical:
                st.success(f"✅ All {total_critical} critical points preserved")
            else:
                st.error(f"⚠️ Only {found_critical}/{total_critical} critical points found")
        
        # Personalization Analysis (Collapsed)
        with st.expander(f"🎯 **AI Personalization Analysis ({len(factors)} Factors)**", expanded=False):
            for factor in factors:
                st.markdown(f"**{factor['category']} - {factor['factor']}**")
                st.caption(factor['detail'])
                st.markdown("---")
        
        # Generated Content
        st.subheader("📝 Generated Content")
        
        tab1, tab2, tab3, tab4 = st.tabs(["📧 Email", "📱 SMS", "📲 App", "📮 Letter"])
        
        with tab1:
            email_content = content.get('email', 'Not generated')
            if isinstance(email_content, dict):
                email_content = str(email_content)
            st.text_area("Email Version", value=email_content, height=300, disabled=True)
        
        with tab2:
            sms_content = content.get('sms', 'Not generated')
            st.text_area("SMS Version", value=sms_content, height=100, disabled=True)
            st.caption(f"Length: {len(sms_content)} characters")
        
        with tab3:
            st.text_area("App Notification", value=content.get('app', 'Not generated'), height=150, disabled=True)
        
        with tab4:
            st.text_area("Postal Letter", value=content.get('letter', 'Not generated'), height=300, disabled=True)
    else:
        st.info("Upload a letter and customer data, then generate personalization")

# Footer
st.markdown("---")
st.caption("Powered by Claude Sonnet 4 | Lloyds Banking Group")