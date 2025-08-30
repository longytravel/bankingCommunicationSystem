"""
Lloyds Personalization UI - Enhanced with AI Document Intelligence
Voice as 5th channel, AI-powered classification, dynamic validation
Smart placeholder handling and improved initialization
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import re
import json
import base64
import hashlib
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

sys.path.append(str(Path(__file__).parent.parent))

from core.personalization_engine import PersonalizationEngine
from core.voice_note_generator import VoiceNoteGenerator
from core.document_classifier import AIDocumentClassifier, ClassificationResult
from core.content_validator import ContentValidator, PointImportance

# Page config
st.set_page_config(
    page_title="Lloyds AI Personalization Engine",
    page_icon="🏦",
    layout="wide"
)

# Enhanced styling with collapsible sections support
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
    .classification-badge {
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-weight: bold;
        display: inline-block;
    }
    .confidence-high { background-color: #00A651; color: white; }
    .confidence-medium { background-color: #FFA500; color: white; }
    .confidence-low { background-color: #FF4444; color: white; }
</style>
""", unsafe_allow_html=True)

def initialize_ai_classifier():
    """Initialize or reinitialize the AI classifier with proper API key"""
    api_key = os.getenv('CLAUDE_API_KEY')
    if api_key:
        return AIDocumentClassifier(api_key=api_key)
    else:
        return AIDocumentClassifier()

def smart_extract_key_points(letter_text: str) -> List:
    """
    Smart extraction that understands placeholders and templates
    """
    validator = ContentValidator(api_key=os.getenv('CLAUDE_API_KEY'))
    key_points = validator.extract_key_points(letter_text)
    
    # Post-process to handle placeholders intelligently
    processed_points = []
    for point in key_points:
        content = point.content
        
        # Detect and transform placeholders
        placeholder_patterns = [
            (r'\[XXXXXX\]', 'Account reference must be included'),
            (r'\[Customer Name\]', 'Customer name personalization required'),
            (r'\[Account Name\]', 'Account type must be specified'),
            (r'\[Effective Date\]', 'Effective date must be specified'),
            (r'\[Customer Services Number\]', 'Contact number must be provided'),
            (r'account number: \[.*?\]', 'Account reference must be included'),
            (r'\[.*?\]', 'Personalized field required: {}')
        ]
        
        transformed = False
        for pattern, replacement in placeholder_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                # Extract the placeholder name if it's a generic pattern
                match = re.search(pattern, content, re.IGNORECASE)
                if '{}' in replacement and match:
                    placeholder_name = match.group(0).strip('[]')
                    point.content = replacement.format(placeholder_name)
                else:
                    point.content = replacement
                
                # Mark as contextual if it's a placeholder (not critical to match exactly)
                if point.importance == PointImportance.CRITICAL:
                    point.importance = PointImportance.IMPORTANT
                
                point.explanation = f"Template placeholder: {match.group(0) if match else 'detected'}"
                transformed = True
                break
        
        processed_points.append(point)
    
    return processed_points

def smart_validate_personalization(key_points: List, personalized_content: Dict[str, str]) -> tuple:
    """
    Smart validation that understands placeholders were meant to be replaced
    """
    validator = ContentValidator(api_key=os.getenv('CLAUDE_API_KEY'))
    
    # Transform validation to be smarter about placeholders
    smart_points = []
    for point in key_points:
        # If it's a placeholder-related point, check for the concept not the literal
        if 'placeholder' in point.explanation.lower() or '[' in point.content:
            # Look for the concept being addressed
            if 'account' in point.content.lower():
                point.content = "Account reference or number mentioned"
            elif 'customer name' in point.content.lower():
                point.content = "Customer name used"
            elif 'date' in point.content.lower():
                point.content = "Date specified"
            elif 'contact' in point.content.lower() or 'phone' in point.content.lower():
                point.content = "Contact information provided"
        smart_points.append(point)
    
    return validator.validate_personalization(smart_points, personalized_content)

# Initialize session state variables with smart initialization
if 'engine' not in st.session_state:
    st.session_state.engine = PersonalizationEngine()
if 'voice_generator' not in st.session_state:
    st.session_state.voice_generator = VoiceNoteGenerator()

# Smart AI classifier initialization - always check it has API key
if 'ai_classifier' not in st.session_state or not hasattr(st.session_state.ai_classifier, 'client') or st.session_state.ai_classifier.client is None:
    st.session_state.ai_classifier = initialize_ai_classifier()
    
if 'current_result' not in st.session_state:
    st.session_state.current_result = None
if 'voice_result' not in st.session_state:
    st.session_state.voice_result = None
if 'key_points' not in st.session_state:
    st.session_state.key_points = []
if 'voice_eligibility' not in st.session_state:
    st.session_state.voice_eligibility = None
if 'ai_classification' not in st.session_state:
    st.session_state.ai_classification = None
if 'classification_viz_data' not in st.session_state:
    st.session_state.classification_viz_data = None
if 'validation_report' not in st.session_state:
    st.session_state.validation_report = None
if 'content_validator' not in st.session_state:
    st.session_state.content_validator = ContentValidator(api_key=os.getenv('CLAUDE_API_KEY'))
if 'letter_content' not in st.session_state:
    st.session_state.letter_content = None
if 'letter_analyzed' not in st.session_state:
    st.session_state.letter_analyzed = False
if 'last_letter_hash' not in st.session_state:
    st.session_state.last_letter_hash = None

def analyze_personalization(customer: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze customer profile to determine personalization factors
    Returns detailed analysis of WHY content was personalized
    """
    factors = {
        'primary_factors': [],
        'channel_preferences': [],
        'tone_adjustments': [],
        'special_considerations': [],
        'personalization_score': 0
    }
    
    # Age-based analysis
    age = customer.get('age', 'unknown')
    if age != 'unknown':
        age_val = int(age) if isinstance(age, (int, str)) and str(age).isdigit() else 0
        if age_val > 60:
            factors['primary_factors'].append("👴 Senior customer (60+) - Formal tone, clear explanations")
            factors['tone_adjustments'].append("Respectful and formal communication style")
            factors['personalization_score'] += 15
        elif age_val < 35:
            factors['primary_factors'].append("👦 Young customer (<35) - Modern, conversational tone")
            factors['tone_adjustments'].append("Casual and engaging communication style")
            factors['personalization_score'] += 15
        else:
            factors['primary_factors'].append("👤 Middle-aged customer - Professional tone")
            factors['tone_adjustments'].append("Balanced professional communication")
            factors['personalization_score'] += 10
    
    # Digital engagement analysis
    digital_logins = customer.get('digital_logins_per_month', 0)
    mobile_app = customer.get('mobile_app_usage', 'Unknown')
    
    if digital_logins > 20:
        factors['primary_factors'].append(f"📱 Highly digital ({digital_logins} logins/month)")
        factors['channel_preferences'].append("Prioritize app and email channels")
        factors['personalization_score'] += 20
    elif digital_logins < 5:
        factors['primary_factors'].append(f"📮 Traditional banking preference ({digital_logins} logins/month)")
        factors['channel_preferences'].append("Emphasize letter and phone support")
        factors['personalization_score'] += 15
    else:
        factors['primary_factors'].append(f"💻 Moderate digital usage ({digital_logins} logins/month)")
        factors['channel_preferences'].append("Balance digital and traditional channels")
        factors['personalization_score'] += 10
    
    # Mobile app usage
    if mobile_app == 'Daily':
        factors['channel_preferences'].append("🚀 Daily app user - App-first messaging")
        factors['personalization_score'] += 15
    elif mobile_app == 'Never':
        factors['channel_preferences'].append("📵 Non-app user - Avoid app-specific features")
        factors['personalization_score'] += 10
    
    # Financial status analysis
    balance = customer.get('account_balance', 0)
    if balance > 20000:
        factors['primary_factors'].append(f"💎 Premium customer (£{balance:,} balance)")
        factors['special_considerations'].append("Mention premium services and wealth management")
        factors['personalization_score'] += 25
    elif balance < 1000:
        factors['primary_factors'].append(f"💰 Budget-conscious (£{balance:,} balance)")
        factors['special_considerations'].append("Focus on budgeting tools and support")
        factors['personalization_score'] += 15
    else:
        factors['primary_factors'].append(f"💳 Standard balance (£{balance:,})")
        factors['personalization_score'] += 10
    
    # Language preference
    language = customer.get('preferred_language', 'English')
    if language != 'English':
        factors['primary_factors'].append(f"🌍 {language} speaker - Full translation required")
        factors['special_considerations'].append(f"All content in {language}")
        factors['personalization_score'] += 30
    
    # Loyalty analysis
    years_with_bank = customer.get('years_with_bank', 0)
    if years_with_bank > 10:
        factors['special_considerations'].append(f"🏆 Loyal customer ({years_with_bank} years) - Acknowledge loyalty")
        factors['personalization_score'] += 20
    elif years_with_bank > 5:
        factors['special_considerations'].append(f"⭐ Established customer ({years_with_bank} years)")
        factors['personalization_score'] += 10
    
    # Life events
    life_events = customer.get('recent_life_events', 'None')
    if life_events not in ['None', 'unknown', None]:
        factors['special_considerations'].append(f"🎯 Recent life event: {life_events}")
        factors['personalization_score'] += 15
    
    # Accessibility needs
    accessibility = customer.get('accessibility_needs', 'None')
    if accessibility not in ['None', 'unknown', None]:
        factors['special_considerations'].append(f"♿ Accessibility: {accessibility}")
        factors['personalization_score'] += 20
    
    # Family status
    family = customer.get('family_status', 'unknown')
    if 'children' in str(family).lower():
        factors['special_considerations'].append("👨‍👩‍👧‍👦 Has children - Include family financial planning")
        factors['personalization_score'] += 10
    
    # Employment status
    employment = customer.get('employment_status', 'unknown')
    if 'self-employed' in str(employment).lower():
        factors['special_considerations'].append("💼 Self-employed - Mention business banking")
        factors['personalization_score'] += 15
    elif 'retired' in str(employment).lower():
        factors['special_considerations'].append("🏖️ Retired - Focus on security and simplicity")
        factors['personalization_score'] += 10
    
    # Email engagement
    email_opens = customer.get('email_opens_per_month', 0)
    if email_opens < 5:
        factors['tone_adjustments'].append(f"📧 Low email engagement ({email_opens}/month) - Keep messages brief")
    elif email_opens > 15:
        factors['tone_adjustments'].append(f"📧 High email engagement ({email_opens}/month) - Detailed explanations OK")
    
    # Branch visits
    branch_visits = customer.get('branch_visits_per_month', 0)
    if branch_visits > 2:
        factors['channel_preferences'].append(f"🏦 Regular branch visitor ({branch_visits}/month)")
        factors['personalization_score'] += 10
    
    # Calculate overall personalization level
    if factors['personalization_score'] >= 80:
        factors['level'] = "🔥 Hyper-Personalized"
    elif factors['personalization_score'] >= 60:
        factors['level'] = "⭐ Highly Personalized"
    elif factors['personalization_score'] >= 40:
        factors['level'] = "✅ Well Personalized"
    elif factors['personalization_score'] >= 20:
        factors['level'] = "📊 Moderately Personalized"
    else:
        factors['level'] = "📝 Basic Personalization"
    
    return factors

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

def display_classification_insights(classification: ClassificationResult):
    """Display AI classification insights in a compact, visual way"""
    # Top-level metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Type", classification.primary_classification)
    
    with col2:
        confidence = classification.confidence_score * 100
        color = "confidence-high" if confidence > 80 else "confidence-medium" if confidence > 60 else "confidence-low"
        st.metric("Confidence", f"{confidence:.1f}%")
    
    with col3:
        st.metric("Urgency", classification.urgency_level)
    
    with col4:
        st.metric("Tone", classification.tone)
    
    # Key insights in expandable sections
    with st.expander("🔍 Classification Details", expanded=False):
        st.markdown(f"**Reasoning:** {classification.reasoning}")
        
        if classification.key_indicators:
            st.markdown("**Key Evidence:**")
            for indicator in classification.key_indicators[:5]:
                st.write(f"• {indicator}")
    
    with st.expander("🎯 AI Insights", expanded=False):
        insights = classification.ai_insights
        if insights:
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**Document Analysis:**")
                st.write(f"• Purpose: {insights.get('primary_purpose', 'N/A')}")
                st.write(f"• Audience: {insights.get('target_audience', 'N/A')}")
                st.write(f"• Key Message: {insights.get('key_message', 'N/A')}")
            with col_b:
                st.markdown("**Recommendations:**")
                channels = insights.get('recommended_channels', [])
                if channels:
                    st.write(f"• Best Channels: {', '.join(channels[:3])}")
                st.write(f"• Action: {insights.get('call_to_action', 'N/A')}")
    
    # Risk assessment if available
    if 'risk_assessment' in classification.ai_insights:
        with st.expander("⚠️ Risk Assessment", expanded=False):
            risks = classification.ai_insights['risk_assessment']
            cols = st.columns(4)
            risk_types = ['misunderstanding_risk', 'reputation_risk', 'compliance_risk', 'customer_satisfaction_risk']
            for idx, risk_type in enumerate(risk_types):
                if risk_type in risks:
                    with cols[idx]:
                        risk_level = risks[risk_type]
                        color = "🔴" if risk_level == "HIGH" else "🟡" if risk_level == "MEDIUM" else "🟢"
                        st.write(f"{color} {risk_type.replace('_', ' ').title()}")
                        st.caption(risk_level)

# Add debug/refresh in sidebar for troubleshooting
with st.sidebar:
    if st.button("🔄 Refresh AI Services", help="Reinitialize AI services if having issues"):
        st.session_state.ai_classifier = initialize_ai_classifier()
        st.session_state.content_validator = ContentValidator(api_key=os.getenv('CLAUDE_API_KEY'))
        st.success("AI services refreshed")
        st.rerun()

# Header
st.title("🏦 Lloyds AI Personalization Engine")
st.markdown("Transform generic letters into personalized multi-channel communications with AI intelligence")
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
        help="Upload a letter for AI analysis and personalization"
    )
    
    if letter_file:
        # Read the file content
        letter_content = letter_file.read().decode('utf-8') if letter_file.type == 'text/plain' else str(letter_file.read())
        
        # Calculate hash of the current file
        current_hash = hashlib.md5(letter_content.encode()).hexdigest()
        
        # Check if this is a new file or if we haven't analyzed yet
        if (st.session_state.last_letter_hash != current_hash or 
            not st.session_state.letter_analyzed or
            st.session_state.letter_content != letter_content):
            
            # This is a new file or first time
            st.session_state.letter_content = letter_content
            st.session_state.last_letter_hash = current_hash
            
            # Extract key points using SMART AI validator
            with st.spinner("Extracting critical information intelligently..."):
                st.session_state.key_points = smart_extract_key_points(letter_content)
            
            # Mark as analyzed
            st.session_state.letter_analyzed = True
            
            # Clear any previous results since we have a new letter
            st.session_state.current_result = None
            st.session_state.voice_result = None
            st.session_state.validation_report = None
            st.session_state.ai_classification = None
        
        # Letter Analysis Section - Now with AI Classification Button
        with st.expander("📋 Letter Analysis", expanded=True):
            # Button for AI Classification - Force new classifier if needed
            if st.button("🤖 Analyze Document with AI", type="secondary", use_container_width=True):
                # Ensure classifier has API key
                if not st.session_state.ai_classifier.client:
                    st.session_state.ai_classifier = initialize_ai_classifier()
                
                with st.spinner("Running comprehensive AI analysis..."):
                    start_time = datetime.now()
                    classification_result = st.session_state.ai_classifier.classify_document(letter_content)
                    processing_time = (datetime.now() - start_time).total_seconds()
                    
                    st.session_state.ai_classification = classification_result
                    st.session_state.classification_viz_data = st.session_state.ai_classifier.get_visualization_data(classification_result)
                    
                    st.success(f"✅ AI Analysis complete in {processing_time:.1f}s")
                    st.rerun()
            
            # Display AI Classification if available
            if st.session_state.ai_classification:
                st.markdown("### 🤖 AI Document Intelligence")
                display_classification_insights(st.session_state.ai_classification)
            else:
                st.info("Click 'Analyze Document with AI' for comprehensive classification")
            
            # Critical Information Section (ALWAYS SHOWN - ESSENTIAL FOR PERSONALIZATION)
            with st.expander("🔒 Critical Information to Preserve", expanded=True):
                if st.session_state.key_points:
                    st.markdown("**Essential content that MUST appear in personalized versions:**")
                    
                    # Group by importance
                    critical = [p for p in st.session_state.key_points if p.importance == PointImportance.CRITICAL]
                    important = [p for p in st.session_state.key_points if p.importance == PointImportance.IMPORTANT]
                    contextual = [p for p in st.session_state.key_points if p.importance == PointImportance.CONTEXTUAL]
                    
                    if critical:
                        st.markdown("**🔴 Critical (Must Include):**")
                        for point in critical[:5]:
                            st.write(f"• {point.content}")
                            if point.explanation and 'placeholder' not in point.explanation.lower():
                                st.caption(f"  ↳ {point.explanation}")
                    
                    if important:
                        st.markdown("**🟡 Important:**")
                        for point in important[:3]:
                            st.write(f"• {point.content}")
                            if 'placeholder' in point.explanation.lower():
                                st.caption(f"  ↳ {point.explanation}")
                    
                    if contextual:
                        st.markdown("**🔵 Contextual:**")
                        for point in contextual[:2]:
                            st.write(f"• {point.content}")
            
            # Letter preview
            with st.expander("📄 Letter Preview", expanded=False):
                st.text_area("Original Letter", st.session_state.letter_content[:500] + "...", height=150, disabled=True)
    else:
        st.warning("Please upload a letter to personalize")
        # Reset analysis flag when no file
        st.session_state.letter_analyzed = False
        st.session_state.last_letter_hash = None
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
        
        # Check voice eligibility (use AI classification if available, otherwise default)
        doc_type = st.session_state.ai_classification.primary_classification if st.session_state.ai_classification else 'INFORMATIONAL'
        st.session_state.voice_eligibility = check_voice_eligibility(selected_customer, doc_type)
        
        # Show profile in collapsible section
        with st.expander("👤 Customer Profile", expanded=False):
            col_a, col_b = st.columns(2)
            with col_a:
                st.write(f"**Age:** {selected_customer.get('age', 'N/A')}")
                st.write(f"**Language:** {selected_customer.get('preferred_language', 'English')}")
                st.write(f"**Balance:** £{selected_customer.get('account_balance', 0):,}")
                st.write(f"**Years with Bank:** {selected_customer.get('years_with_bank', 0)}")
            with col_b:
                st.write(f"**Digital:** {selected_customer.get('digital_logins_per_month', 0)}/month")
                st.write(f"**App Usage:** {selected_customer.get('mobile_app_usage', 'Unknown')}")
                st.write(f"**Support Needs:** {selected_customer.get('accessibility_needs', 'None')}")
                st.write(f"**Life Events:** {selected_customer.get('recent_life_events', 'None')}")
        
        # Generate button
        if st.button("🚀 Generate Personalization", type="primary", use_container_width=True):
            with st.spinner(f"Personalizing for {selected_customer['name']}..."):
                # Generate personalized content WITH KEY POINTS for preservation
                result = st.session_state.engine.personalize_letter(
                    letter_content, 
                    selected_customer,
                    key_points=st.session_state.key_points  # PASS KEY POINTS FOR PRESERVATION
                )
                
                # Analyze personalization factors
                factors = analyze_personalization(selected_customer)
                
                # SMART validation that understands placeholders
                with st.spinner("Validating content completeness intelligently..."):
                    validated_points, summary = smart_validate_personalization(
                        st.session_state.key_points,
                        result
                    )
                    st.session_state.key_points = validated_points
                    
                    # Generate validation report
                    st.session_state.validation_report = st.session_state.content_validator.generate_validation_report(
                        validated_points,
                        summary
                    )
                
                # Store factors with the result
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
        
        # Customer summary bar
        col_1, col_2, col_3, col_4, col_5 = st.columns(5)
        with col_1:
            st.metric("Customer", customer['name'])
        with col_2:
            st.metric("Language", customer.get('preferred_language', 'English'))
        with col_3:
            st.metric("Age", customer.get('age', 'Unknown'))
        with col_4:
            st.metric("Profile", "Digital" if customer.get('digital_logins_per_month', 0) > 10 else "Traditional")
        with col_5:
            if st.session_state.voice_eligibility:
                st.metric("Voice", "✅" if st.session_state.voice_eligibility['generate'] else "❌")
        
        # ALL SECTIONS NOW COLLAPSIBLE
        
        # Content Validation - CRITICAL SECTION
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
                
                # Missing critical points - but be smart about placeholders
                if report['critical_missing']:
                    missing_real = [p for p in report['critical_missing'] 
                                   if '[' not in p and 'placeholder' not in p.lower()]
                    if missing_real:
                        st.error("**❌ Missing Critical Information:**")
                        for point in missing_real:
                            st.write(f"• {point}")
                
                # Detailed validation in nested expander
                with st.expander("📋 Detailed Validation Results", expanded=False):
                    for detail in report['details']:
                        icon = "🔴" if detail['importance'] == 'critical' else "🟡" if detail['importance'] == 'important' else "🔵"
                        st.write(f"{icon} **{detail['content']}**")
                        
                        if detail['found_in']:
                            st.success(f"✓ Found in: {', '.join(detail['found_in'])}")
                        if detail['missing_from']:
                            # Don't show as missing if it's a placeholder
                            if '[' not in detail['content']:
                                st.warning(f"✗ Missing from: {', '.join(detail['missing_from'])}")
            else:
                st.info("Generate personalization to see validation results")
        
        # Personalization Analysis
        with st.expander("🎯 Personalization Analysis", expanded=False):
            if 'factors' in st.session_state.current_result:
                factors = st.session_state.current_result['factors']
                
                # Overall personalization level with progress bar
                st.markdown(f"### {factors['level']}")
                score = factors['personalization_score']
                st.progress(min(score / 100, 1.0))
                st.caption(f"Personalization Score: {score}/100")
                
                # Tabbed view for different factor categories
                tab_a, tab_b, tab_c, tab_d = st.tabs(["Primary Factors", "Channels", "Tone", "Special"])
                
                with tab_a:
                    if factors['primary_factors']:
                        for factor in factors['primary_factors']:
                            st.write(factor)
                    else:
                        st.write("No primary factors identified")
                
                with tab_b:
                    if factors['channel_preferences']:
                        for pref in factors['channel_preferences']:
                            st.write(pref)
                    else:
                        st.write("Standard channel distribution")
                
                with tab_c:
                    if factors['tone_adjustments']:
                        for tone in factors['tone_adjustments']:
                            st.write(tone)
                    else:
                        st.write("Standard tone applied")
                
                with tab_d:
                    if factors['special_considerations']:
                        for consideration in factors['special_considerations']:
                            st.write(consideration)
                    else:
                        st.write("No special considerations")
            else:
                st.info("Generate personalization to see analysis")
        
        # Generated Content - All 5 channels
        st.subheader("📝 Generated Content")
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📧 Email", "📱 SMS", "📲 App", "📮 Letter", "🎙️ Voice"])
        
        with tab1:  # Email
            with st.expander("View Full Email", expanded=True):
                email_content = content.get('email', 'Not generated')
                st.text_area("Email Version", value=email_content, height=300, disabled=True, label_visibility="collapsed")
        
        with tab2:  # SMS
            with st.expander("View SMS", expanded=True):
                sms_content = content.get('sms', 'Not generated')
                st.text_area("SMS Version", value=sms_content, height=100, disabled=True, label_visibility="collapsed")
                st.caption(f"Length: {len(sms_content)} characters")
        
        with tab3:  # App
            with st.expander("View App Notification", expanded=True):
                st.text_area("App Notification", value=content.get('app', 'Not generated'), height=150, disabled=True, label_visibility="collapsed")
        
        with tab4:  # Letter
            with st.expander("View Postal Letter", expanded=True):
                st.text_area("Postal Letter", value=content.get('letter', 'Not generated'), height=300, disabled=True, label_visibility="collapsed")
        
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
                            
                            # Use AI classification if available
                            doc_class = st.session_state.ai_classification.primary_classification if st.session_state.ai_classification else 'INFORMATIONAL'
                            
                            # Generate voice note
                            voice_result = st.session_state.voice_generator.generate_voice_note(
                                text=voice_text,
                                customer=customer,
                                document={'classification': doc_class},
                                force=True
                            )
                            
                            st.session_state.voice_result = voice_result
                            st.success("✓ Voice note generated!")
                            st.rerun()
                else:
                    # Voice already generated
                    with st.expander("🎙️ Voice Note Details", expanded=True):
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
                        st.text_area("30-Second Script", value=voice_text, height=150, disabled=True, label_visibility="collapsed")
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
                if st.session_state.ai_classification and st.session_state.ai_classification.primary_classification == 'REGULATORY':
                    st.caption("Regulatory documents require written format for compliance")
                elif st.session_state.voice_eligibility:
                    st.caption(f"Reason: {st.session_state.voice_eligibility.get('reason', 'Does not meet eligibility criteria')}")
                else:
                    st.caption("Customer profile does not meet voice criteria")
    else:
        st.info("Upload a letter and customer data, then generate personalization")

# Footer
st.markdown("---")
st.caption("Powered by Claude 4 Sonnet & OpenAI TTS | Lloyds Banking Group")