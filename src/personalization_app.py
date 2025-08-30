"""
Lloyds Personalization UI - Enhanced with Voice Notes
Voice as 5th channel, auto-classification, dynamic validation
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import re
import json
import base64
from typing import Dict, Any, Optional, List

sys.path.append(str(Path(__file__).parent.parent))

from core.personalization_engine import PersonalizationEngine
from core.voice_note_generator import VoiceNoteGenerator

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
if 'document_classification' not in st.session_state:
    st.session_state.document_classification = None
if 'validation_report' not in st.session_state:
    st.session_state.validation_report = None
if 'content_validator' not in st.session_state:
    from core.content_validator import ContentValidator
    st.session_state.content_validator = ContentValidator()
if 'letter_content' not in st.session_state:
    st.session_state.letter_content = None

def classify_document(letter_text: str) -> str:
    """
    Automatically classify document type based on content
    Returns: REGULATORY, PROMOTIONAL, or INFORMATIONAL
    """
    text_lower = letter_text.lower()
    
    # Check for regulatory keywords
    regulatory_keywords = [
        'terms and conditions', 'regulatory', 'compliance', 'legal requirement',
        'payment services regulations', 'mandatory', 'required by law',
        'important changes', 'notice of changes', 'must inform you'
    ]
    regulatory_score = sum(1 for keyword in regulatory_keywords if keyword in text_lower)
    
    # Check for promotional keywords
    promotional_keywords = [
        'offer', 'save money', 'exclusive', 'limited time', 'special rate',
        'earn rewards', 'bonus', 'discount', 'new feature', 'opportunity',
        'benefit', 'advantage', 'upgrade', 'premium'
    ]
    promotional_score = sum(1 for keyword in promotional_keywords if keyword in text_lower)
    
    # Check for informational keywords
    informational_keywords = [
        'update', 'information', 'notice', 'announcement', 'helpful',
        'tips', 'guide', 'support', 'reminder', 'for your information'
    ]
    informational_score = sum(1 for keyword in informational_keywords if keyword in text_lower)
    
    # Determine classification based on scores
    if regulatory_score >= 2 or ('terms' in text_lower and 'conditions' in text_lower):
        return 'REGULATORY'
    elif promotional_score > informational_score and promotional_score >= 2:
        return 'PROMOTIONAL'
    else:
        return 'INFORMATIONAL'

def check_voice_eligibility(customer: Dict[str, Any], document_type: str) -> Dict[str, Any]:
    """Check if customer is eligible for voice notes using rules engine"""
    document_metadata = {
        'classification': document_type,
        'urgency': 'normal',
        'compliance_required': document_type == 'REGULATORY'
    }
    
    return st.session_state.voice_generator.should_generate_voice_note(
        customer=customer,
        document=document_metadata
    )

def create_voice_content(personalized_content: Dict[str, str], customer: Dict[str, Any], target_duration: int = 30) -> str:
    """
    Create optimized voice content targeting 30 seconds
    ~75 words for 30 seconds at normal speaking pace
    """
    target_words = int(target_duration * 2.5)  # 2.5 words per second
    
    # Start with personalized greeting
    name = customer.get('name', 'Valued Customer').split()[0]  # First name only
    greeting = f"Hello {name}, this is your Lloyds Bank message. "
    
    # Use app content as base (it's usually most concise)
    app_content = personalized_content.get('app', '')
    email_content = personalized_content.get('email', '')
    
    # Build core message
    if app_content and len(app_content.split()) < 50:
        core_message = app_content.replace('\n', ' ').strip()
    else:
        # Take first 2 sentences from email
        sentences = email_content.split('.')[:2]
        core_message = '. '.join(sentences).strip() + '.'
    
    # Combine
    voice_text = greeting + core_message
    
    # Add closing if under word limit
    if len(voice_text.split()) < target_words - 10:
        voice_text += " For full details, check your Lloyds app or visit us online."
    
    # Trim if over target
    words = voice_text.split()
    if len(words) > target_words + 5:
        words = words[:target_words]
        voice_text = ' '.join(words) + "..."
    
    return voice_text

def play_audio_file(file_path: Path):
    """Create an audio player for the generated voice note"""
    if file_path.exists():
        if file_path.suffix == '.mp3':
            # Real audio file
            with open(file_path, 'rb') as f:
                audio_bytes = f.read()
            
            st.audio(audio_bytes, format='audio/mp3')
            
            st.download_button(
                label="📥 Download Voice Note",
                data=audio_bytes,
                file_name=file_path.name,
                mime="audio/mp3"
            )
        
        elif file_path.suffix == '.json':
            # Mock audio (for testing)
            with open(file_path, 'r') as f:
                mock_data = json.load(f)
            st.info("🎵 Mock Voice Note (OpenAI API not connected)")
            with st.expander("Mock Data"):
                st.json(mock_data)

# Header
st.title("🏦 Lloyds AI Personalization Engine")
st.markdown("Transform generic letters into personalized multi-channel communications")
st.markdown("---")

# Two columns
col1, col2 = st.columns([1, 2])

# LEFT COLUMN - Inputs
with col1:
    st.header("📥 Inputs")
    
    # Letter upload
    st.subheader("1. Upload Letter")
    letter_file = st.file_uploader(
        "Select letter to personalize",
        type=['txt', 'docx', 'pdf'],
        help="System will auto-detect letter type"
    )
    
    if letter_file:
        letter_content = letter_file.read().decode('utf-8') if letter_file.type == 'text/plain' else str(letter_file.read())
        st.session_state.letter_content = letter_content
        
        # Auto-classify document
        st.session_state.document_classification = classify_document(letter_content)
        
        # Extract key points using AI validator
        with st.spinner("Analyzing letter content..."):
            st.session_state.key_points = st.session_state.content_validator.extract_key_points(letter_content)
        
        with st.expander("Letter Analysis", expanded=True):
            # Show auto-classification
            doc_type = st.session_state.document_classification
            if doc_type == 'REGULATORY':
                st.warning(f"📋 Document Type: {doc_type} (No voice notes for compliance)")
            else:
                st.info(f"📋 Document Type: {doc_type}")
            
            # Show AI-extracted key points
            if st.session_state.key_points:
                st.markdown("**🤖 AI-Identified Key Information:**")
                
                # Group by importance
                from core.content_validator import PointImportance
                critical = [p for p in st.session_state.key_points if p.importance == PointImportance.CRITICAL]
                important = [p for p in st.session_state.key_points if p.importance == PointImportance.IMPORTANT]
                contextual = [p for p in st.session_state.key_points if p.importance == PointImportance.CONTEXTUAL]
                
                if critical:
                    st.markdown("**🔴 Critical (Must Include):**")
                    for point in critical[:5]:
                        st.write(f"• {point.content}")
                        if point.explanation:
                            st.caption(f"  ↳ {point.explanation}")
                
                if important:
                    st.markdown("**🟡 Important:**")
                    for point in important[:3]:
                        st.write(f"• {point.content}")
                
                if contextual:
                    st.markdown("**🔵 Contextual:**")
                    for point in contextual[:2]:
                        st.write(f"• {point.content}")
            
            # Letter preview
            st.text_area("Letter Preview", letter_content[:300] + "...", height=100, disabled=True)
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
        
        # Check voice eligibility
        st.session_state.voice_eligibility = check_voice_eligibility(
            selected_customer, 
            st.session_state.document_classification
        )
        
        # Show profile
        with st.expander("Customer Profile"):
            col_a, col_b = st.columns(2)
            with col_a:
                st.write(f"**Age:** {selected_customer.get('age', 'N/A')}")
                st.write(f"**Language:** {selected_customer.get('preferred_language', 'English')}")
                st.write(f"**Balance:** £{selected_customer.get('account_balance', 0):,}")
            with col_b:
                st.write(f"**Digital:** {selected_customer.get('digital_logins_per_month', 0)}/month")
                st.write(f"**App Usage:** {selected_customer.get('mobile_app_usage', 'Unknown')}")
                st.write(f"**Support Needs:** {selected_customer.get('accessibility_needs', 'None')}")
        
        # Generate button
        if st.button("🚀 Generate Personalization", type="primary", use_container_width=True):
            with st.spinner(f"Personalizing for {selected_customer['name']}..."):
                result = st.session_state.engine.personalize_letter(letter_content, selected_customer)
                
                # Validate the personalization
                with st.spinner("Validating content completeness..."):
                    validated_points, summary = st.session_state.content_validator.validate_personalization(
                        st.session_state.key_points,
                        result
                    )
                    st.session_state.key_points = validated_points
                    
                    # Generate validation report
                    st.session_state.validation_report = st.session_state.content_validator.generate_validation_report(
                        validated_points,
                        summary
                    )
                
                st.session_state.current_result = {
                    'customer': selected_customer,
                    'content': result
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
        
        # Customer summary
        col_1, col_2, col_3, col_4 = st.columns(4)
        with col_1:
            st.metric("Customer", customer['name'])
        with col_2:
            st.metric("Language", customer.get('preferred_language', 'English'))
        with col_3:
            st.metric("Age", customer.get('age', 'Unknown'))
        with col_4:
            if st.session_state.voice_eligibility:
                st.metric("Voice", "✅ Eligible" if st.session_state.voice_eligibility['generate'] else "❌ Not Eligible")
        
        # Content Validation
        with st.expander("✅ Content Completeness Check", expanded=True):
            if st.session_state.validation_report:
                report = st.session_state.validation_report
                
                # Overall status
                status = report.get('status', 'unknown')
                message = report.get('message', 'Validation incomplete')
                
                if status == 'success':
                    st.success(message)
                elif status == 'error':
                    st.error(message)
                else:
                    st.warning(message)
                
                # Progress bar
                coverage = report['summary']['coverage_percentage']
                st.progress(coverage / 100)
                
                # Summary metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Points", report['summary']['total_points'])
                with col2:
                    st.metric("Critical Points", report['summary']['critical_points'])
                with col3:
                    st.metric("Coverage", f"{coverage:.0f}%")
                
                # Channel coverage
                st.markdown("**Coverage by Channel:**")
                channel_cols = st.columns(4)
                channels = ['email', 'sms', 'app', 'letter']
                for idx, channel in enumerate(channels):
                    with channel_cols[idx]:
                        ch_data = report['by_channel'][channel]
                        st.metric(
                            channel.capitalize(),
                            f"{ch_data['found']}/{report['summary']['total_points']}",
                            f"{ch_data['coverage']:.0f}%"
                        )
                
                # Missing critical points
                if report['critical_missing']:
                    st.error("**❌ Missing Critical Information:**")
                    for point in report['critical_missing']:
                        st.write(f"• {point}")
                
                # Show detailed validation
                with st.expander("Detailed Validation Results", expanded=False):
                    for detail in report['details']:
                        icon = "🔴" if detail['importance'] == 'critical' else "🟡" if detail['importance'] == 'important' else "🔵"
                        st.write(f"{icon} **{detail['content']}**")
                        
                        if detail['found_in']:
                            st.success(f"✓ Found in: {', '.join(detail['found_in'])}")
                        if detail['missing_from']:
                            st.warning(f"✗ Missing from: {', '.join(detail['missing_from'])}")
            else:
                st.info("Generate personalization to see validation results")
        
        # Generated Content - All 5 channels
        st.subheader("📝 Generated Content")
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📧 Email", "📱 SMS", "📲 App", "📮 Letter", "🎙️ Voice"])
        
        with tab1:  # Email
            email_content = content.get('email', 'Not generated')
            st.text_area("Email Version", value=email_content, height=300, disabled=True)
        
        with tab2:  # SMS
            sms_content = content.get('sms', 'Not generated')
            st.text_area("SMS Version", value=sms_content, height=100, disabled=True)
            st.caption(f"Length: {len(sms_content)} characters")
        
        with tab3:  # App
            st.text_area("App Notification", value=content.get('app', 'Not generated'), height=150, disabled=True)
        
        with tab4:  # Letter
            st.text_area("Postal Letter", value=content.get('letter', 'Not generated'), height=300, disabled=True)
        
        with tab5:  # Voice - Always present as 5th channel
            if st.session_state.voice_eligibility and st.session_state.voice_eligibility['generate']:
                if not st.session_state.voice_result:
                    # Voice not generated yet
                    st.info("🎙️ Voice note available for this customer")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Style:** {st.session_state.voice_eligibility.get('voice_style', 'standard')}")
                        st.write(f"**Language:** {st.session_state.voice_eligibility.get('voice_language', customer.get('preferred_language'))}")
                    with col2:
                        st.write(f"**Speed:** {st.session_state.voice_eligibility.get('voice_speed', 1.0)}x")
                        st.write(f"**Duration:** ~30 seconds")
                    
                    # Generate voice button INSIDE the voice tab
                    if st.button("🎙️ Generate Voice Note", type="primary", use_container_width=True):
                        with st.spinner("Generating 30-second voice note..."):
                            # Create optimized voice content
                            voice_text = create_voice_content(
                                content,
                                customer,
                                target_duration=30
                            )
                            
                            # Generate voice note
                            voice_result = st.session_state.voice_generator.generate_voice_note(
                                text=voice_text,
                                customer=customer,
                                document={'classification': st.session_state.document_classification},
                                force=True
                            )
                            
                            st.session_state.voice_result = voice_result
                            st.success("✓ Voice note generated!")
                            st.rerun()
                else:
                    # Voice already generated
                    st.success("✅ Voice Note Generated")
                    
                    # Metadata
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Voice", st.session_state.voice_result.get('voice', 'Unknown'))
                    with col2:
                        st.metric("Duration", f"~{st.session_state.voice_result.get('duration_estimate', 0):.1f}s")
                    with col3:
                        st.metric("Language", st.session_state.voice_result.get('language', 'English'))
                    
                    # Voice script
                    st.markdown("### 📝 Voice Script")
                    voice_text = create_voice_content(content, customer, target_duration=30)
                    st.text_area("30-Second Script", value=voice_text, height=150, disabled=True)
                    st.caption(f"Word count: {len(voice_text.split())} words")
                    
                    # Audio player
                    st.markdown("### 🔊 Audio Player")
                    file_path = Path(st.session_state.voice_result.get('filename', ''))
                    if file_path.exists():
                        play_audio_file(file_path)
                    
                    # Regenerate button
                    if st.button("🔄 Regenerate Voice Note", type="secondary"):
                        st.session_state.voice_result = None
                        st.rerun()
            else:
                # Not eligible for voice
                st.info("🔇 Voice notes not available")
                if st.session_state.document_classification == 'REGULATORY':
                    st.caption("Regulatory documents require written format for compliance")
                elif st.session_state.voice_eligibility:
                    st.caption(f"Reason: {st.session_state.voice_eligibility.get('reason', 'Does not meet eligibility criteria')}")
                else:
                    st.caption("Customer profile does not meet voice criteria")
    else:
        st.info("Upload a letter and customer data, then generate personalization")

# Footer
st.markdown("---")
st.caption("Powered by Claude Sonnet 4 & OpenAI TTS | Lloyds Banking Group")