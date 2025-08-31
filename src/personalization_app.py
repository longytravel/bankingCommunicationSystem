"""
Lloyds Multi-Channel Personalization UI - Email + SMS Modular System
Clean tabbed interface showing multiple personalization channels
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

# Import MODULAR systems
from core.simple_email_orchestrator import SimpleEmailOrchestrator
from core.simple_sms_orchestrator import SimpleSMSOrchestrator

# Import existing working components  
from core.voice_note_generator import VoiceNoteGenerator
from core.document_classifier import AIDocumentClassifier, ClassificationResult
from core.content_validator import ContentValidator, PointImportance

# Page config
st.set_page_config(
    page_title="Lloyds AI Personalization Engine",
    page_icon="🏦",
    layout="wide"
)

# Enhanced styling with tabs and channel cards
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
    
    .channel-showcase {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border: 1px solid #dee2e6;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .email-showcase {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        border: 1px solid #2196f3;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .sms-showcase {
        background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
        border: 1px solid #4caf50;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .success-banner {
        background: linear-gradient(90deg, #00A651, #006A4D);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    
    .skipped-banner {
        background: linear-gradient(90deg, #FFA726, #FF9800);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    
    .channel-stats {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .sms-preview {
        background: #f0f0f0;
        border: 2px solid #4caf50;
        border-radius: 15px;
        padding: 1rem;
        font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 16px;
        line-height: 1.4;
        margin: 1rem 0;
        position: relative;
    }
    
    .sms-preview::before {
        content: "📱 SMS Preview";
        position: absolute;
        top: -10px;
        left: 15px;
        background: #4caf50;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
    }
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
    """Smart extraction that understands placeholders and templates"""
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
                match = re.search(pattern, content, re.IGNORECASE)
                if '{}' in replacement and match:
                    placeholder_name = match.group(0).strip('[]')
                    point.content = replacement.format(placeholder_name)
                else:
                    point.content = replacement
                
                if point.importance == PointImportance.CRITICAL:
                    point.importance = PointImportance.IMPORTANT
                
                point.explanation = f"Template placeholder: {match.group(0) if match else 'detected'}"
                transformed = True
                break
        
        processed_points.append(point)
    
    return processed_points

def analyze_personalization(customer: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze customer profile to determine personalization factors"""
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

def display_classification_insights(classification: ClassificationResult):
    """Display AI classification insights in a compact, visual way"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Type", classification.primary_classification)
    
    with col2:
        confidence = classification.confidence_score * 100
        st.metric("Confidence", f"{confidence:.1f}%")
    
    with col3:
        st.metric("Urgency", classification.urgency_level)
    
    with col4:
        st.metric("Tone", classification.tone)
    
    with st.expander("🔍 Classification Details", expanded=False):
        st.markdown(f"**Reasoning:** {classification.reasoning}")
        
        if classification.key_indicators:
            st.markdown("**Key Evidence:**")
            for indicator in classification.key_indicators[:5]:
                st.write(f"• {indicator}")

# Initialize session state variables with smart initialization
if 'email_orchestrator' not in st.session_state:
    st.session_state.email_orchestrator = SimpleEmailOrchestrator()
if 'sms_orchestrator' not in st.session_state:
    st.session_state.sms_orchestrator = SimpleSMSOrchestrator()
if 'voice_generator' not in st.session_state:
    st.session_state.voice_generator = VoiceNoteGenerator()

# Smart AI classifier initialization
if 'ai_classifier' not in st.session_state or not hasattr(st.session_state.ai_classifier, 'client') or st.session_state.ai_classifier.client is None:
    st.session_state.ai_classifier = initialize_ai_classifier()
    
if 'current_results' not in st.session_state:
    st.session_state.current_results = None
if 'voice_result' not in st.session_state:
    st.session_state.voice_result = None
if 'key_points' not in st.session_state:
    st.session_state.key_points = []
if 'voice_eligibility' not in st.session_state:
    st.session_state.voice_eligibility = None
if 'ai_classification' not in st.session_state:
    st.session_state.ai_classification = None
if 'content_validator' not in st.session_state:
    st.session_state.content_validator = ContentValidator(api_key=os.getenv('CLAUDE_API_KEY'))
if 'letter_content' not in st.session_state:
    st.session_state.letter_content = None
if 'letter_analyzed' not in st.session_state:
    st.session_state.letter_analyzed = False
if 'last_letter_hash' not in st.session_state:
    st.session_state.last_letter_hash = None

# Header
st.title("🏦 Lloyds Multi-Channel AI Personalization Engine")
st.markdown("Transform generic letters into personalized multi-channel communications with AI intelligence")

# Show system mode
col1, col2 = st.columns(2)
with col1:
    st.info("📧 **EMAIL MODULE** - Advanced personalization with content preservation")
with col2:
    st.info("📱 **SMS MODULE** - Smart, rules-based SMS generation")

st.markdown("---")

# Two columns
col1, col2 = st.columns([1, 2])

# LEFT COLUMN - Keep all the working functionality
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
            
            st.session_state.letter_content = letter_content
            st.session_state.last_letter_hash = current_hash
            
            # Extract key points using SMART AI validator
            with st.spinner("Extracting critical information intelligently..."):
                st.session_state.key_points = smart_extract_key_points(letter_content)
            
            st.session_state.letter_analyzed = True
            st.session_state.current_results = None
            st.session_state.ai_classification = None
        
        # Letter Analysis Section
        with st.expander("📋 Letter Analysis", expanded=True):
            # Button for AI Classification
            if st.button("🤖 Analyze Document with AI", type="secondary", use_container_width=True):
                if not st.session_state.ai_classifier.client:
                    st.session_state.ai_classifier = initialize_ai_classifier()
                
                with st.spinner("Running comprehensive AI analysis..."):
                    start_time = datetime.now()
                    classification_result = st.session_state.ai_classifier.classify_document(letter_content)
                    processing_time = (datetime.now() - start_time).total_seconds()
                    
                    st.session_state.ai_classification = classification_result
                    
                    st.success(f"✅ AI Analysis complete in {processing_time:.1f}s")
                    st.rerun()
            
            # Display AI Classification if available
            if st.session_state.ai_classification:
                st.markdown("### 🤖 AI Document Intelligence")
                display_classification_insights(st.session_state.ai_classification)
            else:
                st.info("Click 'Analyze Document with AI' for comprehensive classification")
            
            # Critical Information Section
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
                    
                    if important:
                        st.markdown("**🟡 Important:**")
                        for point in important[:3]:
                            st.write(f"• {point.content}")
                    
                    if contextual:
                        st.markdown("**🔵 Contextual:**")
                        for point in contextual[:2]:
                            st.write(f"• {point.content}")
            
            # Letter preview
            with st.expander("📄 Letter Preview", expanded=False):
                st.text_area("Original Letter", st.session_state.letter_content[:500] + "...", height=150, disabled=True)
    else:
        st.warning("Please upload a letter to personalize")
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
        
        # Check voice eligibility
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
        
        # Generate button - USING BOTH ORCHESTRATORS
        if st.button("🚀 Generate Multi-Channel Personalization", type="primary", use_container_width=True):
            with st.spinner(f"Personalizing all channels for {selected_customer['name']}..."):
                
                # Generate Email
                email_result = st.session_state.email_orchestrator.personalize_email(
                    letter_content,
                    selected_customer,
                    validate_content=True
                )
                
                # Generate SMS
                sms_result = st.session_state.sms_orchestrator.personalize_sms(
                    letter_content,
                    selected_customer,
                    validate_content=True
                )
                
                # Analyze personalization factors
                factors = analyze_personalization(selected_customer)
                
                # Store results
                st.session_state.current_results = {
                    'customer': selected_customer,
                    'email_result': email_result,
                    'sms_result': sms_result,
                    'factors': factors
                }
                
                # Show completion status
                email_success = email_result.get('email') and email_result['email'].get('content')
                sms_success = sms_result.get('sms') and sms_result['sms'].get('content') and not sms_result.get('sms', {}).get('skipped')
                sms_skipped = sms_result.get('sms', {}).get('skipped', False)
                
                if email_success and sms_success:
                    st.success("✅ Both Email & SMS Generated Successfully!")
                elif email_success and sms_skipped:
                    st.success("✅ Email Generated | SMS Skipped (Customer Rules)")
                elif email_success:
                    st.success("✅ Email Generated | SMS Failed")
                else:
                    st.error("❌ Generation failed")
                
                st.rerun()

# RIGHT COLUMN - Multi-Channel Results Display
with col2:
    st.header("📺 Multi-Channel Results")
    
    if st.session_state.current_results:
        result = st.session_state.current_results
        customer = result['customer']
        email_result = result['email_result']
        sms_result = result['sms_result']
        factors = result['factors']
        
        # Overall success banner
        email_success = email_result.get('email') and email_result['email'].get('content')
        sms_success = sms_result.get('sms') and sms_result['sms'].get('content') and not sms_result.get('sms', {}).get('skipped')
        sms_skipped = sms_result.get('sms', {}).get('skipped', False)
        
        if email_success and sms_success:
            st.markdown(f'''
            <div class="success-banner">
                <h3>✅ Multi-Channel Success</h3>
                <p><strong>{customer['name']}</strong> • Both Email & SMS Generated • {factors.get('level', 'Personalized')}</p>
            </div>
            ''', unsafe_allow_html=True)
        elif email_success and sms_skipped:
            st.markdown(f'''
            <div class="success-banner">
                <h3>✅ Email Success • SMS Skipped</h3>
                <p><strong>{customer['name']}</strong> • {sms_result.get('sms', {}).get('skip_reason', 'Rules-based skip')}</p>
            </div>
            ''', unsafe_allow_html=True)
        
        # Tabbed interface for channels
        tab1, tab2, tab3 = st.tabs(["📧 Email", "📱 SMS", "🎯 Analysis"])
        
        with tab1:
            # EMAIL TAB
            if email_success:
                email_content = email_result['email']['content']
                
                st.markdown('<div class="email-showcase">', unsafe_allow_html=True)
                st.markdown("### 📧 Personalized Email")
                st.markdown(email_content)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Email stats
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Words", email_result['email'].get('word_count', 0))
                with col2:
                    st.metric("Language", email_result['email'].get('language', 'English'))
                with col3:
                    st.metric("Tone", email_result['email'].get('tone', 'Professional'))
                with col4:
                    processing_time = email_result.get('processing_time', 0)
                    st.metric("Time", f"{processing_time:.1f}s")
                
                # Email quality details
                with st.expander("📊 Email Quality Details", expanded=False):
                    if email_result.get('email_validation'):
                        email_val = email_result['email_validation']
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            quality_score = email_val.get('quality_score', 0)
                            st.metric("Quality Score", f"{quality_score:.2f}/1.0")
                        with col2:
                            status_text = email_val.get('status_text', 'Unknown')
                            st.metric("Status", status_text)
                        with col3:
                            personalization_score = email_val.get('personalization_score', 0)
                            st.metric("Personalization", f"{personalization_score:.2f}/1.0")
                        
                        factors_applied = email_val.get('personalization_factors_applied', 0)
                        context_integration = email_val.get('context_integration', 0)
                        st.write(f"• **Personalization Factors:** {factors_applied}/5 applied")
                        st.write(f"• **Context Integration:** {context_integration} customer-specific elements")
                
                # Download email
                st.download_button(
                    "📧 Download Email",
                    email_content,
                    file_name=f"personalized_email_{customer['customer_id']}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
                
            else:
                st.error("❌ Email generation failed")
                if email_result.get('errors'):
                    for error in email_result['errors']:
                        st.write(f"• {error}")
        
        with tab2:
            # SMS TAB
            if sms_success:
                sms_content = sms_result['sms']['content']
                char_count = sms_result['sms'].get('character_count', len(sms_content))
                segment_count = sms_result['sms'].get('segment_count', 1)
                
                st.markdown('<div class="sms-showcase">', unsafe_allow_html=True)
                st.markdown("### 📱 Personalized SMS")
                
                # SMS preview in phone-like interface
                st.markdown(f'''
                <div class="sms-preview">
                    {sms_content}
                </div>
                ''', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # SMS stats
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Characters", f"{char_count}")
                with col2:
                    st.metric("Segments", f"{segment_count}")
                with col3:
                    cost = segment_count * 0.05  # 5p per segment
                    st.metric("Cost", f"£{cost:.2f}")
                with col4:
                    processing_time = sms_result.get('processing_time', 0)
                    st.metric("Time", f"{processing_time:.1f}s")
                
                # SMS quality details
                with st.expander("📊 SMS Quality Details", expanded=False):
                    if sms_result.get('sms_validation'):
                        sms_val = sms_result['sms_validation']
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            quality_score = sms_val.get('quality_score', 0)
                            st.metric("Quality Score", f"{quality_score:.2f}/1.0")
                        with col2:
                            status_text = sms_val.get('status_text', 'Unknown')
                            st.metric("Status", status_text)
                        with col3:
                            target_length = sms_val.get('target_length', 160)
                            st.metric("Target Length", f"{target_length}")
                        
                        if sms_val.get('critical_content_preserved'):
                            st.success("✅ Critical content preserved")
                        else:
                            st.warning("⚠️ Some critical content may be missing")
                
                # Download SMS
                st.download_button(
                    "📱 Download SMS",
                    sms_content,
                    file_name=f"personalized_sms_{customer['customer_id']}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
                
            elif sms_skipped:
                st.markdown(f'''
                <div class="skipped-banner">
                    <h3>⏭️ SMS Skipped</h3>
                    <p><strong>Reason:</strong> {sms_result.get('sms', {}).get('skip_reason', 'Customer rules')}</p>
                    <p><strong>Customer Segment:</strong> {sms_result.get('eligibility', {}).get('customer_segment', 'Unknown')}</p>
                </div>
                ''', unsafe_allow_html=True)
                
                # Show eligibility details
                with st.expander("🔍 SMS Eligibility Details", expanded=True):
                    eligibility = sms_result.get('eligibility', {})
                    
                    st.write(f"**Customer Segment:** {eligibility.get('customer_segment', 'Unknown')}")
                    st.write(f"**Eligible:** {'Yes' if eligibility.get('eligible') else 'No'}")
                    st.write(f"**Reason:** {eligibility.get('reason', 'Unknown')}")
                    st.write(f"**Confidence:** {eligibility.get('confidence', 0):.1%}")
                    
                    # Explain the rules
                    st.markdown("**📋 SMS Rules:**")
                    st.write("• **DIGITAL customers:** App/email preferred, SMS only for urgent")
                    st.write("• **ASSISTED customers:** SMS is ideal channel")
                    st.write("• **TRADITIONAL customers:** No SMS - prefer letter/phone")
                    st.write("• **Senior customers (75+):** SMS generally avoided")
                
            else:
                st.error("❌ SMS generation failed")
                if sms_result.get('errors'):
                    for error in sms_result['errors']:
                        st.write(f"• {error}")
        
        with tab3:
            # ANALYSIS TAB
            st.markdown("### 🎯 Personalization Analysis")
            
            # Overall personalization score
            st.markdown(f"### {factors['level']}")
            score = factors['personalization_score']
            st.progress(min(score / 100, 1.0))
            st.caption(f"Personalization Score: {score}/100")
            
            # Channel strategy
            with st.expander("📺 Channel Strategy", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**📧 Email:**")
                    if email_success:
                        st.success("✅ Generated successfully")
                    else:
                        st.error("❌ Failed to generate")
                
                with col2:
                    st.markdown("**📱 SMS:**")
                    if sms_success:
                        st.success("✅ Generated successfully")
                    elif sms_skipped:
                        st.warning("⏭️ Skipped (rules-based)")
                    else:
                        st.error("❌ Failed to generate")
            
            # Show how customer data influenced personalization
            with st.expander("📊 Data-Driven Personalization", expanded=True):
                st.markdown("**How customer data shaped the content:**")
                
                for factor in factors['primary_factors']:
                    st.write(f"• {factor}")
                
                for consideration in factors['special_considerations']:
                    st.write(f"• {consideration}")
            
            # Processing details
            with st.expander("⚙️ Processing Pipeline", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**📧 Email Steps:**")
                    for step in email_result.get('processing_steps', []):
                        st.write(f"• {step}")
                
                with col2:
                    st.markdown("**📱 SMS Steps:**")
                    for step in sms_result.get('processing_steps', []):
                        st.write(f"• {step}")
    
    else:
        st.info("👈 Upload a letter and select a customer to generate multi-channel personalization")
        
        # Show capabilities
        st.markdown("### 🎯 Multi-Channel Capabilities")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📧 Email Module**")
            st.write("✅ Content Preservation")
            st.write("✅ Deep Personalization")
            st.write("✅ Quality Validation")
            st.write("✅ Multi-language Support")
        
        with col2:
            st.markdown("**📱 SMS Module**")
            st.write("✅ Rules-based Eligibility")
            st.write("✅ Smart Character Limits")
            st.write("✅ Segment Cost Optimization")
            st.write("✅ Customer Segment Routing")

# Sidebar for system status
with st.sidebar:
    st.markdown("### ⚙️ Multi-Channel System Status")
    
    email_status = "✅ Ready" if st.session_state.email_orchestrator else "❌ Error"
    sms_status = "✅ Ready" if st.session_state.sms_orchestrator else "❌ Error"
    classifier_status = "✅ Ready" if st.session_state.ai_classifier else "❌ Error"
    
    st.write(f"**Email Orchestrator:** {email_status}")
    st.write(f"**SMS Orchestrator:** {sms_status}")
    st.write(f"**AI Classifier:** {classifier_status}")
    st.write(f"**Voice Generator:** ✅ Ready")
    
    st.markdown("### 📊 Channel Statistics")
    if st.session_state.current_results:
        email_generated = bool(st.session_state.current_results.get('email_result', {}).get('email', {}).get('content'))
        sms_generated = bool(st.session_state.current_results.get('sms_result', {}).get('sms', {}).get('content')) and not st.session_state.current_results.get('sms_result', {}).get('sms', {}).get('skipped')
        sms_skipped = st.session_state.current_results.get('sms_result', {}).get('sms', {}).get('skipped', False)
        
        st.write(f"**Email:** {'✅ Generated' if email_generated else '❌ Not generated'}")
        st.write(f"**SMS:** {'✅ Generated' if sms_generated else '⏭️ Skipped' if sms_skipped else '❌ Not generated'}")
    else:
        st.write("No results yet")
    
    if st.button("🔄 Refresh All Systems"):
        st.session_state.ai_classifier = initialize_ai_classifier()
        st.session_state.email_orchestrator = SimpleEmailOrchestrator()
        st.session_state.sms_orchestrator = SimpleSMSOrchestrator()
        st.success("All systems refreshed!")
        st.rerun()

# Footer
st.markdown("---")
st.caption("Powered by Claude 4 Sonnet | Lloyds Banking Group | Modular Multi-Channel System")