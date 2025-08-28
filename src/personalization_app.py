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
    """Generate detailed personalization analysis"""
    factors = []
    
    # Language & Cultural
    lang = customer.get('preferred_language', 'English')
    if lang != 'English':
        factors.append({
            'category': 'LANGUAGE',
            'factor': f'Full translation to {lang}',
            'detail': f'Content adapted for {lang} speakers with cultural norms',
            'importance': 'HIGH'
        })
    
    # Age-based tone
    age = customer.get('age', 0)
    if isinstance(age, (int, float)) and age > 0:
        if age < 30:
            factors.append({
                'category': 'TONE',
                'factor': 'Modern, casual communication',
                'detail': f'Age {age}: Contemporary language, shorter sentences',
                'importance': 'HIGH'
            })
        elif age > 65:
            factors.append({
                'category': 'TONE',
                'factor': 'Formal, respectful communication',
                'detail': f'Age {age}: Traditional salutation, clear explanations',
                'importance': 'HIGH'
            })
    
    # Digital sophistication
    digital = customer.get('digital_logins_per_month', 0)
    if digital > 20:
        factors.append({
            'category': 'CHANNEL',
            'factor': 'Digital-first approach',
            'detail': f'{digital} logins/month: Emphasizing app features',
            'importance': 'HIGH'
        })
    elif digital < 5:
        factors.append({
            'category': 'CHANNEL',
            'factor': 'Traditional support emphasis',
            'detail': f'{digital} logins/month: Phone and branch support',
            'importance': 'HIGH'
        })
    
    # Financial situation
    balance = customer.get('account_balance', 0)
    if balance > 10000:
        factors.append({
            'category': 'FINANCIAL',
            'factor': 'Premium customer treatment',
            'detail': f'£{balance:,} balance: Premium services mentioned',
            'importance': 'HIGH'
        })
    elif balance < 1000:
        factors.append({
            'category': 'FINANCIAL',
            'factor': 'Financial support focus',
            'detail': f'£{balance:,} balance: Support services emphasized',
            'importance': 'HIGH'
        })
    
    # Life events
    events = customer.get('recent_life_events', 'None')
    if events and events.lower() not in ['none', 'n/a', '']:
        factors.append({
            'category': 'LIFE EVENT',
            'factor': f'{events} acknowledgment',
            'detail': f'Personalized reference to {events}',
            'importance': 'MEDIUM'
        })
    
    # Accessibility
    accessibility = customer.get('accessibility_needs', 'None')
    if accessibility and accessibility.lower() not in ['none', 'n/a', '', 'null']:
        factors.append({
            'category': 'ACCESSIBILITY',
            'factor': f'Adaptation for: {accessibility}',
            'detail': 'Simpler language, alternative formats offered',
            'importance': 'HIGH'
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