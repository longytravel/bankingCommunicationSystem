"""
Lloyds Banking Communication System - Main Application
Integrated with Voice Notes Generation
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import json
import base64
from typing import Dict, Any, Optional
import sys
import re

sys.path.append(str(Path(__file__).parent.parent))

from src.core.personalization_engine import PersonalizationEngine
from src.core.voice_note_generator import VoiceNoteGenerator
from src.config import Config

# Page configuration
st.set_page_config(
    page_title="Lloyds AI Communication System",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Lloyds branding
st.markdown(Config.get_css_theme(), unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    """Initialize all session state variables"""
    if 'personalization_engine' not in st.session_state:
        st.session_state.personalization_engine = PersonalizationEngine()
    
    if 'voice_generator' not in st.session_state:
        st.session_state.voice_generator = VoiceNoteGenerator()
    
    if 'current_result' not in st.session_state:
        st.session_state.current_result = None
    
    if 'voice_result' not in st.session_state:
        st.session_state.voice_result = None
    
    if 'key_points' not in st.session_state:
        st.session_state.key_points = []
    
    if 'voice_eligibility' not in st.session_state:
        st.session_state.voice_eligibility = None
    
    if 'letter_content' not in st.session_state:
        st.session_state.letter_content = None
    
    if 'selected_customer' not in st.session_state:
        st.session_state.selected_customer = None
    
    if 'document_type' not in st.session_state:
        st.session_state.document_type = 'INFORMATIONAL'

def extract_key_points(letter_text: str) -> list:
    """Extract key points from letter for validation"""
    key_points = []
    text_lower = letter_text.lower()
    
    # Date extraction
    date_patterns = [
        (r"march 1, 2025", "Effective date: March 1, 2025"),
        (r"(\d{1,2}[/-]\d{1,2}[/-]\d{4})", "Date mentioned: {}"),
        (r"effective\s+([^,\n]+)", "Effective date: {}")
    ]
    
    for pattern, template in date_patterns:
        if re.search(pattern, text_lower):
            match = re.search(pattern, letter_text, re.IGNORECASE)
            if match:
                date_str = match.group(1) if match.groups() else match.group(0)
                key_points.append({
                    "point": template.format(date_str) if '{}' in template else template,
                    "critical": True
                })
                break
    
    # Financial amounts
    amounts = re.findall(r'£\d+(?:\.\d{2})?', letter_text)
    for amount in amounts:
        key_points.append({"point": f"Amount: {amount}", "critical": True})
    
    # Specific changes
    change_keywords = [
        ("overdraft interest", "daily", "Daily overdraft interest calculation"),
        ("11:59pm", None, "Cancellation deadline: 11:59pm"),
        ("no action", None, "No action required"),
        ("terms and conditions", None, "Terms and conditions update")
    ]
    
    for keyword1, keyword2, description in change_keywords:
        if keyword1 in text_lower:
            if keyword2 is None or keyword2 in text_lower:
                key_points.append({"point": description, "critical": True})
    
    # Contact information
    phone_match = re.search(r'0\d{3}\s?\d{3}\s?\d{4}', letter_text)
    if phone_match:
        key_points.append({"point": f"Contact: {phone_match.group(0)}", "critical": False})
    
    return key_points

def create_voice_content(personalized_content: Dict[str, str], customer: Dict[str, Any], target_duration: int = 30) -> str:
    """
    Create optimized voice content targeting specific duration
    
    Args:
        personalized_content: Dictionary with personalized channel content
        customer: Customer profile
        target_duration: Target duration in seconds (default 30)
    
    Returns:
        Optimized text for voice generation
    """
    # Estimate: 150 words per minute = 2.5 words per second
    # For 30 seconds: ~75 words
    target_words = int(target_duration * 2.5)
    
    # Start with greeting
    name = customer.get('name', 'Valued Customer').split()[0]  # First name only
    greeting = f"Hello {name}, this is your Lloyds Bank update. "
    
    # Extract key information from personalized content
    email_content = personalized_content.get('email', '')
    app_content = personalized_content.get('app', '')
    
    # Find the most important information
    key_info = []
    
    # Look for dates
    date_match = re.search(r'(march \d+|january \d+|february \d+|\d{1,2}[/-]\d{1,2}[/-]\d{4})', 
                          email_content, re.IGNORECASE)
    if date_match:
        key_info.append(f"Important changes take effect {date_match.group(1)}. ")
    
    # Look for amounts
    amount_matches = re.findall(r'£\d+(?:\.\d{2})?', email_content)
    if amount_matches and len(amount_matches) <= 2:
        key_info.append(f"Fee changes include {' and '.join(amount_matches)}. ")
    
    # Look for action required
    if "no action" in email_content.lower():
        key_info.append("No action is required from you. ")
    elif "action required" in email_content.lower():
        key_info.append("Action is required on your account. ")
    
    # Core message from app notification (usually concise)
    if app_content and len(app_content) < 200:
        core_message = app_content.replace('\n', ' ').strip()
    else:
        # Extract first meaningful sentence from email
        sentences = email_content.split('.')[:3]
        core_message = '. '.join(sentences).strip()
    
    # Build the voice message
    voice_text = greeting + ' '.join(key_info)
    
    # Add core message if we have word budget
    current_words = len(voice_text.split())
    if current_words < target_words - 20:
        # Clean and add core message
        core_message = re.sub(r'\s+', ' ', core_message)  # Remove extra whitespace
        voice_text += core_message
    
    # Add closing if still under target
    current_words = len(voice_text.split())
    if current_words < target_words - 10:
        voice_text += " For full details, please check your Lloyds app or online banking."
    
    # Trim if over target
    words = voice_text.split()
    if len(words) > target_words + 10:  # Allow 10 words over
        words = words[:target_words]
        voice_text = ' '.join(words) + "... Check your app for full details."
    
    return voice_text

def check_voice_eligibility(customer: Dict[str, Any], document_type: str) -> Dict[str, Any]:
    """Check if customer is eligible for voice notes"""
    document_metadata = {
        'classification': document_type,
        'urgency': 'normal',
        'compliance_required': document_type == 'REGULATORY'
    }
    
    return st.session_state.voice_generator.should_generate_voice_note(
        customer=customer,
        document=document_metadata
    )

def display_voice_eligibility(eligibility: Dict[str, Any]):
    """Display voice eligibility status with visual indicators"""
    if eligibility['generate']:
        st.success(f"🎙️ **Voice Note Eligible** - {eligibility.get('voice_style', 'standard')} style")
        col1, col2 = st.columns(2)
        with col1:
            st.caption(f"Language: {eligibility.get('voice_language', 'English')}")
        with col2:
            st.caption(f"Speed: {eligibility.get('voice_speed', 1.0)}x")
    else:
        st.info(f"🔇 Voice Note Not Required - {eligibility.get('reason', 'Does not meet criteria')}")

def play_audio_file(file_path: Path):
    """Create an audio player for the generated voice note"""
    if file_path.exists():
        if file_path.suffix == '.mp3':
            # Real audio file
            with open(file_path, 'rb') as f:
                audio_bytes = f.read()
            
            # Create audio player
            st.audio(audio_bytes, format='audio/mp3')
            
            # Download button
            b64 = base64.b64encode(audio_bytes).decode()
            href = f'<a href="data:audio/mp3;base64,{b64}" download="{file_path.name}">Download Voice Note</a>'
            st.markdown(href, unsafe_allow_html=True)
        
        elif file_path.suffix == '.json':
            # Mock audio (for testing)
            with open(file_path, 'r') as f:
                mock_data = json.load(f)
            st.info("🎵 Mock Voice Note (API not connected)")
            st.json(mock_data)

def validate_content_completeness(original_points: list, personalized_content: Dict[str, str]) -> list:
    """Validate that personalized content includes key points"""
    all_content = " ".join(str(v).lower() for v in personalized_content.values() if v)
    
    validated = []
    for point_data in original_points:
        point = point_data["point"]
        found = False
        
        # Check for specific patterns
        if "£" in point:
            amount = re.search(r'£[\d.]+', point)
            if amount:
                found = amount.group(0) in all_content or amount.group(0)[1:] in all_content
        elif "date" in point.lower():
            date_part = point.split(":")[-1].strip() if ":" in point else point
            found = date_part.lower() in all_content
        else:
            # General keyword matching
            keywords = [w for w in point.lower().split() if len(w) > 3]
            found = any(keyword in all_content for keyword in keywords)
        
        validated.append({
            "point": point,
            "critical": point_data["critical"],
            "found": found
        })
    
    return validated

# Initialize session state
init_session_state()

# Header
st.title("🏦 Lloyds AI Communication System")
st.markdown("Transform generic letters into personalized multi-channel communications with voice notes")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Document type selector
    st.session_state.document_type = st.selectbox(
        "Document Type",
        ["INFORMATIONAL", "PROMOTIONAL", "REGULATORY"],
        help="Regulatory documents won't generate voice notes"
    )
    
    # Test mode options
    st.markdown("### Test Options")
    quick_test = st.checkbox("Quick Test Mode (5 customers)", value=Config.QUICK_TEST_MODE)
    use_mock = st.checkbox("Mock Mode (no API calls)", value=Config.USE_MOCK_DATA)
    
    if quick_test:
        Config.QUICK_TEST_MODE = True
    if use_mock:
        Config.USE_MOCK_DATA = True
    
    # API Status
    st.markdown("### API Status")
    col1, col2 = st.columns(2)
    with col1:
        claude_status = "✅ Connected" if Config.CLAUDE_API_KEY else "❌ Not configured"
        st.caption(f"Claude: {claude_status}")
    with col2:
        openai_status = "✅ Connected" if Config.OPENAI_API_KEY else "❌ Not configured"
        st.caption(f"OpenAI: {openai_status}")
    
    # Stats
    if st.session_state.voice_generator.stats['total_evaluated'] > 0:
        st.markdown("### Voice Stats")
        stats = st.session_state.voice_generator.get_statistics()
        st.metric("Generated", stats['voice_generated'])
        st.metric("Skipped", stats['voice_skipped'])
        st.metric("Rate", f"{stats['generation_rate']:.1f}%")

# Main content area
tab1, tab2 = st.tabs(["📥 Input & Process", "📊 Results"])

with tab1:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("1️⃣ Upload Letter")
        letter_file = st.file_uploader(
            "Select letter to personalize",
            type=['txt', 'docx', 'pdf'],
            help="Upload the generic letter that needs personalization"
        )
        
        if letter_file:
            st.session_state.letter_content = letter_file.read().decode('utf-8') if letter_file.type == 'text/plain' else str(letter_file.read())
            st.session_state.key_points = extract_key_points(st.session_state.letter_content)
            
            with st.expander("📄 View Letter Content", expanded=False):
                st.text_area("Letter Preview", st.session_state.letter_content[:1000], height=200, disabled=True)
                
                # Show key points
                if st.session_state.key_points:
                    st.markdown("**Key Information Detected:**")
                    for point in st.session_state.key_points:
                        icon = "🔴" if point['critical'] else "🔵"
                        st.write(f"{icon} {point['point']}")
    
    with col2:
        st.header("2️⃣ Upload Customers")
        customer_file = st.file_uploader(
            "Select customer data",
            type=['csv', 'xlsx'],
            help="Upload customer profiles CSV/Excel"
        )
        
        if customer_file:
            customers_df = pd.read_csv(customer_file) if customer_file.type == 'text/csv' else pd.read_excel(customer_file)
            st.success(f"✅ Loaded {len(customers_df)} customers")
            
            # Customer selector
            st.markdown("### 3️⃣ Select Customer")
            customer_options = [f"{row['name']} (ID: {row['customer_id']})" for _, row in customers_df.iterrows()]
            selected_option = st.selectbox("Choose customer:", customer_options)
            
            if selected_option:
                idx = customer_options.index(selected_option)
                st.session_state.selected_customer = customers_df.iloc[idx].to_dict()
                
                # Display customer profile
                with st.expander("👤 Customer Profile", expanded=True):
                    customer = st.session_state.selected_customer
                    
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("Age", customer.get('age', 'N/A'))
                        st.metric("Language", customer.get('preferred_language', 'English'))
                    with col_b:
                        st.metric("Balance", f"£{customer.get('account_balance', 0):,}")
                        st.metric("Digital Logins", f"{customer.get('digital_logins_per_month', 0)}/mo")
                    with col_c:
                        st.metric("App Usage", customer.get('mobile_app_usage', 'Unknown'))
                        st.metric("Years", customer.get('years_with_bank', 0))
                    
                    # Check voice eligibility
                    if st.session_state.selected_customer:
                        eligibility = check_voice_eligibility(
                            st.session_state.selected_customer,
                            st.session_state.document_type
                        )
                        st.session_state.voice_eligibility = eligibility
                        
                        st.markdown("---")
                        display_voice_eligibility(eligibility)
    
    # Process buttons
    if st.session_state.letter_content and st.session_state.selected_customer:
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚀 Generate Personalization", type="primary", use_container_width=True):
                with st.spinner(f"Personalizing for {st.session_state.selected_customer['name']}..."):
                    result = st.session_state.personalization_engine.personalize_letter(
                        st.session_state.letter_content,
                        st.session_state.selected_customer
                    )
                    st.session_state.current_result = result
                    st.success("✅ Personalization complete!")
                    st.rerun()
        
        with col2:
            # Only show voice button if eligible and personalization exists
            if st.session_state.current_result and st.session_state.voice_eligibility and st.session_state.voice_eligibility['generate']:
                if st.button("🎙️ Generate Voice Note", type="secondary", use_container_width=True):
                    with st.spinner("Generating voice note..."):
                        # Create optimized voice content
                        voice_text = create_voice_content(
                            st.session_state.current_result,
                            st.session_state.selected_customer,
                            target_duration=30
                        )
                        
                        # Generate voice note
                        voice_result = st.session_state.voice_generator.generate_voice_note(
                            text=voice_text,
                            customer=st.session_state.selected_customer,
                            document={'classification': st.session_state.document_type},
                            force=True  # Force since we already checked eligibility
                        )
                        
                        st.session_state.voice_result = voice_result
                        st.success("✅ Voice note generated!")
                        st.rerun()

with tab2:
    if st.session_state.current_result:
        st.header("📤 Personalized Output")
        
        # Customer summary bar
        customer = st.session_state.selected_customer
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Customer", customer['name'])
        with col2:
            st.metric("Language", customer.get('preferred_language', 'English'))
        with col3:
            st.metric("Age", customer.get('age', 'Unknown'))
        with col4:
            digital = customer.get('digital_logins_per_month', 0)
            st.metric("Profile", "Digital" if digital > 10 else "Traditional")
        with col5:
            if st.session_state.voice_eligibility:
                st.metric("Voice", "✅ Eligible" if st.session_state.voice_eligibility['generate'] else "❌ Not Eligible")
        
        # Content validation
        with st.expander("✅ Content Completeness Check", expanded=False):
            validated = validate_content_completeness(st.session_state.key_points, st.session_state.current_result)
            
            critical = [p for p in validated if p['critical']]
            found_critical = sum(1 for p in critical if p['found'])
            
            progress = found_critical / len(critical) if critical else 1.0
            st.progress(progress)
            st.caption(f"{found_critical}/{len(critical)} critical points preserved")
            
            for item in validated:
                if item['found']:
                    st.success(f"✅ {item['point']}")
                else:
                    st.error(f"❌ MISSING: {item['point']}")
        
        # Channel tabs including voice
        tabs = ["📧 Email", "📱 SMS", "📲 App", "📮 Letter"]
        if st.session_state.voice_result:
            tabs.append("🎙️ Voice Note")
        
        tab_list = st.tabs(tabs)
        
        with tab_list[0]:  # Email
            st.text_area("Email Version", value=st.session_state.current_result.get('email', ''), height=400, disabled=True)
        
        with tab_list[1]:  # SMS
            sms_content = st.session_state.current_result.get('sms', '')
            st.text_area("SMS Version", value=sms_content, height=150, disabled=True)
            st.caption(f"Length: {len(sms_content)} characters")
        
        with tab_list[2]:  # App
            st.text_area("App Notification", value=st.session_state.current_result.get('app', ''), height=200, disabled=True)
        
        with tab_list[3]:  # Letter
            st.text_area("Postal Letter", value=st.session_state.current_result.get('letter', ''), height=400, disabled=True)
        
        if st.session_state.voice_result:
            with tab_list[4]:  # Voice Note
                st.markdown("### 🎙️ Voice Note Details")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Voice", st.session_state.voice_result.get('voice', 'Unknown'))
                    st.metric("Language", st.session_state.voice_result.get('language', 'English'))
                    st.metric("Duration", f"~{st.session_state.voice_result.get('duration_estimate', 0):.1f} seconds")
                
                with col2:
                    st.metric("Style", st.session_state.voice_result.get('style', 'standard'))
                    st.metric("Speed", f"{st.session_state.voice_result.get('speed', 1.0)}x")
                    st.metric("Generated", st.session_state.voice_result.get('generated_at', '')[:10])
                
                # Show the text that was converted
                with st.expander("📝 Voice Script", expanded=True):
                    # Recreate the voice text to show what was spoken
                    voice_text = create_voice_content(
                        st.session_state.current_result,
                        st.session_state.selected_customer,
                        target_duration=30
                    )
                    st.text_area("Voice Script (30 seconds)", value=voice_text, height=200, disabled=True)
                    word_count = len(voice_text.split())
                    st.caption(f"Word count: {word_count} (~{word_count/150*60:.1f} seconds at normal speed)")
                
                # Audio player
                st.markdown("### 🔊 Audio Player")
                file_path = Path(st.session_state.voice_result.get('filename', ''))
                if file_path.exists():
                    play_audio_file(file_path)
                else:
                    st.warning("Audio file not found")
    else:
        st.info("👈 Upload a letter and customer data, then generate personalization to see results")

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("Powered by Claude Sonnet 4 & OpenAI TTS")
with col2:
    st.caption("© 2025 Lloyds Banking Group")
with col3:
    if st.button("📊 Export Stats"):
        report_file = st.session_state.voice_generator.export_report()
        st.success(f"Report saved: {report_file}")