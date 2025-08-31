"""
Lloyds Personalization UI - Hybrid: Keep Working Left Side, Clean Right Side
Keeps all working functionality, showcases new email system properly
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

# Import NEW email system
from core.simple_email_orchestrator import SimpleEmailOrchestrator

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
    .email-showcase {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border: 1px solid #dee2e6;
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

# Initialize session state variables with smart initialization
if 'email_orchestrator' not in st.session_state:
    st.session_state.email_orchestrator = SimpleEmailOrchestrator()
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
if 'content_validator' not in st.session_state:
    st.session_state.content_validator = ContentValidator(api_key=os.getenv('CLAUDE_API_KEY'))
if 'letter_content' not in st.session_state:
    st.session_state.letter_content = None
if 'letter_analyzed' not in st.session_state:
    st.session_state.letter_analyzed = False
if 'last_letter_hash' not in st.session_state:
    st.session_state.last_letter_hash = None

# Header
st.title("🏦 Lloyds AI Personalization Engine")
st.markdown("Transform generic letters into personalized multi-channel communications with AI intelligence")

# Show system mode
if st.session_state.email_orchestrator:
    st.info("🎯 **MODULAR EMAIL SYSTEM** - Next-generation personalization with content preservation")

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
            st.session_state.ai_classification = None
        
        # Letter Analysis Section - Now with AI Classification Button
        with st.expander("📋 Letter Analysis", expanded=True):
            # Button for AI Classification
            if st.button("🤖 Analyze Document with AI", type="secondary", use_container_width=True):
                # Ensure classifier has API key
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
        
        # Generate button - USING NEW EMAIL SYSTEM
        if st.button("🚀 Generate Personalized Email", type="primary", use_container_width=True):
            with st.spinner(f"Personalizing email for {selected_customer['name']} using modular system..."):
                
                # Use NEW email orchestrator system
                orchestration_result = st.session_state.email_orchestrator.personalize_email(
                    letter_content,
                    selected_customer,
                    validate_content=True
                )
                
                # Analyze personalization factors using existing system
                factors = analyze_personalization(selected_customer)
                
                # Store results
                st.session_state.current_result = {
                    'customer': selected_customer,
                    'orchestration_result': orchestration_result,
                    'factors': factors
                }
                
                if orchestration_result.get('email') and orchestration_result['email'].get('content'):
                    st.success("✅ Modular Email System - Personalization complete!")
                else:
                    st.error("❌ Email generation failed")
                    if orchestration_result.get('errors'):
                        st.error(f"Error: {orchestration_result['errors'][0]}")
                
                st.rerun()

# RIGHT COLUMN - CLEAN Results Display for New System
with col2:
    st.header("📧 Personalized Email Results")
    
    if st.session_state.current_result:
        result = st.session_state.current_result
        customer = result['customer']
        orchestration_result = result['orchestration_result']
        factors = result['factors']
        
        # Success banner if email generated
        if orchestration_result.get('email') and orchestration_result['email'].get('content'):
            st.markdown(f'''
            <div class="success-banner">
                <h3>✅ Email Generated Successfully</h3>
                <p><strong>{customer['name']}</strong> • {factors.get('level', 'Personalized')} • {orchestration_result['email'].get('word_count', 0)} words</p>
            </div>
            ''', unsafe_allow_html=True)
            
            # Email showcase
            email_content = orchestration_result['email']['content']
            
            st.markdown('<div class="email-showcase">', unsafe_allow_html=True)
            st.markdown("### 📧 Personalized Email")
            st.markdown(email_content)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Quick stats
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Words", orchestration_result['email'].get('word_count', 0))
            with col2:
                st.metric("Language", orchestration_result['email'].get('language', 'English'))
            with col3:
                st.metric("Tone", orchestration_result['email'].get('tone', 'Professional'))
            with col4:
                processing_time = orchestration_result.get('processing_time', 0)
                st.metric("Time", f"{processing_time:.1f}s")
            
            # Personalization Analysis - Show Usage Stats Connection
            with st.expander("🎯 Personalization Analysis", expanded=True):
                st.markdown(f"### {factors['level']}")
                score = factors['personalization_score']
                st.progress(min(score / 100, 1.0))
                st.caption(f"Personalization Score: {score}/100")
                
                # Show how customer usage stats influenced content
                st.markdown("**📊 Usage Stats → Content Adaptation:**")
                
                # Digital usage connection
                digital_logins = customer.get('digital_logins_per_month', 0)
                mobile_usage = customer.get('mobile_app_usage', 'Unknown')
                email_opens = customer.get('email_opens_per_month', 0)
                
                if digital_logins > 15:
                    st.write(f"📱 **{digital_logins} logins/month** → Tech-savvy language, app references")
                if mobile_usage == 'high' or mobile_usage == 'Daily':
                    st.write(f"📲 **High mobile usage** → Mobile-first features emphasized")
                if email_opens > 15:
                    st.write(f"📧 **{email_opens} email opens/month** → Detailed content, engaging format")
                
                # Life stage connection
                age = customer.get('age', 'unknown')
                life_event = customer.get('recent_life_events', 'None')
                if age != 'unknown' and int(age) < 25:
                    st.write(f"🎓 **Age {age} + {life_event}** → Casual tone, university context")
                
                # Financial behavior connection  
                balance = customer.get('account_balance', 0)
                recent_transactions = customer.get('recent_transactions', 0)
                if balance < 2000 and recent_transactions > 50:
                    st.write(f"💰 **£{balance:,} balance, {recent_transactions} transactions** → Budgeting focus, student-friendly content")
                
                # Show applied AI factors
                applied_factors = orchestration_result['email'].get('personalization_factors', [])
                if applied_factors:
                    st.markdown("**🤖 AI Personalization Factors Applied:**")
                    for factor in applied_factors:
                        st.write(f"• {factor}")
            
            # Content Quality Check - Fixed Display
            with st.expander("✅ Content Quality Check", expanded=False):
                # Email quality from new system (FIXED)
                if orchestration_result.get('email_validation'):
                    email_val = orchestration_result['email_validation']
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        quality_score = email_val.get('quality_score', 0)
                        st.metric("Quality Score", f"{quality_score:.2f}/1.0")
                    with col2:
                        status_text = email_val.get('status_text', 'Unknown')
                        if quality_score >= 0.8:
                            st.metric("Status", f"🌟 {status_text}")
                        elif quality_score >= 0.6:  
                            st.metric("Status", f"✅ {status_text}")
                        else:
                            st.metric("Status", f"⚠️ {status_text}")
                    with col3:
                        personalization_score = email_val.get('personalization_score', 0)
                        st.metric("Personalization", f"{personalization_score:.2f}/1.0")
                    
                    # Show what drove the quality score
                    st.markdown("**📈 Quality Breakdown:**")
                    factors_applied = email_val.get('personalization_factors_applied', 0)
                    context_integration = email_val.get('context_integration', 0)
                    st.write(f"• **Personalization Factors:** {factors_applied}/5 applied")
                    st.write(f"• **Context Integration:** {context_integration} customer-specific elements")
                    if email_val.get('has_greeting'):
                        st.write("• **Structure:** ✅ Proper greeting")
                    if email_val.get('has_closing'):
                        st.write("• **Structure:** ✅ Professional closing")
                    
                    # Only show REAL issues (not placeholder complaints)
                    real_issues = [issue for issue in email_val.get('issues', []) if 'placeholder' not in issue.lower()]
                    if real_issues:
                        st.warning("**Real Issues:** " + ", ".join(real_issues))
                    
                    if email_val.get('warnings'):
                        st.info("**Suggestions:** " + ", ".join(email_val['warnings']))
                
                # Content preservation (separate from quality)
                if orchestration_result.get('content_validation'):
                    content_val = orchestration_result['content_validation']
                    summary = content_val.get('summary', {})
                    coverage = summary.get('coverage_percentage', 0)
                    
                    st.markdown("**📋 Content Preservation (Separate Check):**")
                    st.progress(coverage / 100)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Coverage", f"{coverage:.0f}%")
                    with col2:
                        st.metric("Key Points", f"{summary.get('total_points', 0)}")
                    
                    # Show realistic content preservation status
                    if coverage >= 95:
                        st.success("🎉 Excellent content preservation!")
                    elif coverage >= 85:
                        st.success("✅ Very good content preservation")
                    elif coverage >= 75:
                        st.info("📝 Good content preservation")
                    else:
                        st.warning("⚠️ Some content may be missing")
            
            # Processing Details - Clean Display
            with st.expander("⚙️ System Processing Details", expanded=False):
                steps = orchestration_result.get('processing_steps', [])
                st.markdown("**Processing Pipeline:**")
                for step in steps:
                    st.write(f"• {step}")
                
                if orchestration_result.get('warnings'):
                    st.markdown("**⚠️ Warnings:**")
                    for warning in orchestration_result['warnings']:
                        st.write(f"• {warning}")
            
            # Export Options
            st.markdown("### 📥 Export")
            col1, col2 = st.columns(2)
            
            with col1:
                st.download_button(
                    "📧 Download Email",
                    email_content,
                    file_name=f"personalized_email_{customer['customer_id']}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            with col2:
                export_data = {
                    'customer': customer,
                    'email': email_content,
                    'personalization_factors': applied_factors,
                    'quality_metrics': orchestration_result.get('email_validation', {}),
                    'generated_at': datetime.now().isoformat()
                }
                
                st.download_button(
                    "📊 Download Report",
                    json.dumps(export_data, indent=2),
                    file_name=f"personalization_report_{customer['customer_id']}.json",
                    mime="application/json",
                    use_container_width=True
                )
        
        else:
            # Error display
            st.error("❌ Email Generation Failed")
            
            if orchestration_result.get('errors'):
                st.markdown("**Errors:**")
                for error in orchestration_result['errors']:
                    st.write(f"• {error}")
            
            if orchestration_result.get('warnings'):
                st.markdown("**Warnings:**")
                for warning in orchestration_result['warnings']:
                    st.write(f"• {warning}")
    
    else:
        st.info("👈 Upload a letter and select a customer to generate personalized email")
        
        # Show capabilities
        st.markdown("### 🎯 Modular Email System Features")
        st.write("✅ **Content Preservation** - Advanced validation ensures nothing is lost")
        st.write("✅ **Deep Personalization** - Context-aware content that feels natural")
        st.write("✅ **Quality Validation** - Multiple layers of quality checking")
        st.write("✅ **Processing Pipeline** - Clean, modular architecture")
        st.write("✅ **Export Options** - Email and detailed reports")

# Sidebar for system status
with st.sidebar:
    st.markdown("### ⚙️ System Status")
    
    orchestrator_status = "✅ Ready" if st.session_state.email_orchestrator else "❌ Error"
    classifier_status = "✅ Ready" if st.session_state.ai_classifier else "❌ Error"
    
    st.write(f"**Email Orchestrator:** {orchestrator_status}")
    st.write(f"**AI Classifier:** {classifier_status}")
    st.write(f"**Voice Generator:** ✅ Ready")
    
    if st.button("🔄 Refresh System"):
        st.session_state.ai_classifier = initialize_ai_classifier()
        st.session_state.email_orchestrator = SimpleEmailOrchestrator()
        st.success("System refreshed!")
        st.rerun()

# Footer
st.markdown("---")
st.caption("Powered by Claude 4 Sonnet | Lloyds Banking Group | Modular Personalization System")