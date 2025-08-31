"""
Lloyds AI Personalization Engine - Complete Fixed Version
Uses the new SharedBrain + Smart Email Generator architecture with robust error handling
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
import traceback

# Ensure environment variables are loaded
load_dotenv()

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Initialize all availability flags first
CORE_MODULES_AVAILABLE = False
ADDITIONAL_MODULES_AVAILABLE = False
SharedBrain = None
SharedContext = None
CustomerInsights = None
PersonalizationStrategy = None
SmartEmailGenerator = None
EmailResult = None
ContentValidator = None
PointImportance = None
SimpleSMSOrchestrator = None
VoiceNoteGenerator = None
AIDocumentClassifier = None
ClassificationResult = None

# Import the NEW modular system with absolute imports
try:
    print("Attempting to import core modules...")
    from src.core.shared_brain import SharedBrain, SharedContext, CustomerInsights, PersonalizationStrategy
    print("✅ SharedBrain modules imported")
    
    from src.core.smart_email_generator import SmartEmailGenerator, EmailResult
    print("✅ SmartEmailGenerator imported")
    
    from src.core.content_validator import ContentValidator, PointImportance
    print("✅ ContentValidator imported")
    
    from src.core.document_classifier import AIDocumentClassifier, ClassificationResult
    print("✅ DocumentClassifier imported")
    
    CORE_MODULES_AVAILABLE = True
    print("✅ All core modules imported successfully")
    
except Exception as e:
    print(f"❌ Core modules import failed: {e}")
    print("Full traceback:")
    traceback.print_exc()
    
    # Create dummy classes to prevent NameErrors
    class SharedBrain:
        def __init__(self, *args, **kwargs):
            pass
        def analyze_everything(self, *args, **kwargs):
            return None
    
    class SharedContext:
        def __init__(self):
            self.customer_data = {}
            self.customer_insights = type('obj', (object,), {'segment': 'UNKNOWN'})()
            self.personalization_strategy = type('obj', (object,), {'level': type('obj', (object,), {'value': 'basic'})()})()
            self.processing_time = 0
            self.analysis_confidence = 0
            self.channel_decisions = {'enabled_channels': {}}
    
    class CustomerInsights:
        def __init__(self):
            self.segment = 'UNKNOWN'
    
    class PersonalizationStrategy:
        def __init__(self):
            self.level = type('obj', (object,), {'value': 'basic'})()
    
    class SmartEmailGenerator:
        def __init__(self, *args, **kwargs):
            pass
        def generate_email(self, *args, **kwargs):
            return type('obj', (object,), {
                'content': 'Error: Core modules not available',
                'subject_line': 'Error',
                'quality_score': 0,
                'processing_time': 0,
                'generation_method': 'error'
            })()
    
    class EmailResult:
        def __init__(self):
            self.content = ''
    
    class ContentValidator:
        def __init__(self, *args, **kwargs):
            pass
    
    class PointImportance:
        pass
    
    class AIDocumentClassifier:
        def __init__(self, *args, **kwargs):
            pass

# Import existing working components
try:
    from src.core.simple_sms_orchestrator import SimpleSMSOrchestrator
    from src.core.voice_note_generator import VoiceNoteGenerator
    ADDITIONAL_MODULES_AVAILABLE = True
    print("✅ Additional modules imported")
except Exception as e:
    print(f"⚠️ Additional modules not available: {e}")
    
    # Create dummy classes
    class SimpleSMSOrchestrator:
        def __init__(self, *args, **kwargs):
            pass
    
    class VoiceNoteGenerator:
        def __init__(self, *args, **kwargs):
            pass

# Page config
st.set_page_config(
    page_title="Lloyds AI Personalization Engine - Shared Brain",
    page_icon="🧠",
    layout="wide"
)

# Enhanced styling for the new system
st.markdown("""
<style>
    .main {padding-top: 1rem;}
    .stButton>button {
        background-color: #006A4D;
        color: white;
    }
    
    .shared-brain-banner {
        background: linear-gradient(90deg, #006A4D, #00A651);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .intelligence-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border: 2px solid #006A4D;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .smart-email-showcase {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        border: 2px solid #2196f3;
        border-radius: 10px;
        padding: 2rem;
        margin: 1rem 0;
    }
    
    .personalization-insights {
        background: linear-gradient(135deg, #fff3e0 0%, #ffcc80 100%);
        border: 2px solid #ff9800;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .brain-stats {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .success-banner {
        background: linear-gradient(90deg, #00A651, #006A4D);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    
    .error-banner {
        background: linear-gradient(90deg, #dc3545, #c82333);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def safe_get_attribute(obj, attr_path, default=None):
    """Safely get nested attributes from objects"""
    try:
        attrs = attr_path.split('.')
        for attr in attrs:
            obj = getattr(obj, attr, None)
            if obj is None:
                return default
        return obj
    except:
        return default

def analyze_personalization_deeply(customer: Dict[str, Any], shared_context) -> Dict[str, Any]:
    """Enhanced personalization analysis using shared context"""
    
    if not shared_context or not CORE_MODULES_AVAILABLE:
        return {
            'error': 'Core modules not available',
            'brain_insights': {},
            'personalization_strategy': {},
            'special_factors': [],
            'personalization_hooks': [],
            'channel_decisions': {}
        }
    
    try:
        insights = shared_context.customer_insights
        strategy = shared_context.personalization_strategy
        
        analysis = {
            'brain_insights': {
                'segment': safe_get_attribute(insights, 'segment', 'UNKNOWN'),
                'life_stage': safe_get_attribute(insights, 'life_stage', 'unknown'),
                'digital_persona': safe_get_attribute(insights, 'digital_persona', 'unknown'),
                'financial_profile': safe_get_attribute(insights, 'financial_profile', 'unknown'),
                'communication_style': safe_get_attribute(insights, 'communication_style', 'unknown'),
                'confidence': safe_get_attribute(insights, 'confidence_score', 0)
            },
            'personalization_strategy': {
                'level': safe_get_attribute(strategy, 'level.value', 'basic'),
                'customer_story': safe_get_attribute(strategy, 'customer_story', 'No story available'),
                'tone_guidelines': safe_get_attribute(strategy, 'tone_guidelines', {}),
                'must_mention': safe_get_attribute(strategy, 'must_mention', []),
                'connection_points': safe_get_attribute(strategy, 'connection_points', {})
            },
            'special_factors': safe_get_attribute(insights, 'special_factors', []),
            'personalization_hooks': safe_get_attribute(insights, 'personalization_hooks', []),
            'channel_decisions': safe_get_attribute(shared_context, 'channel_decisions', {})
        }
        
        return analysis
    except Exception as e:
        print(f"Error in analyze_personalization_deeply: {e}")
        return {
            'error': str(e),
            'brain_insights': {},
            'personalization_strategy': {},
            'special_factors': [],
            'personalization_hooks': [],
            'channel_decisions': {}
        }

def display_shared_brain_intelligence(shared_context):
    """Display the Shared Brain's analysis in a beautiful way"""
    
    if not shared_context or not CORE_MODULES_AVAILABLE:
        st.error("❌ Shared context not available")
        return
    
    try:
        insights = shared_context.customer_insights
        strategy = shared_context.personalization_strategy
        
        st.markdown('<div class="intelligence-card">', unsafe_allow_html=True)
        st.markdown("### 🧠 Shared Brain Intelligence")
        
        # Core insights
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            segment = safe_get_attribute(insights, 'segment', 'UNKNOWN')
            confidence = safe_get_attribute(insights, 'confidence_score', 0)
            st.metric("Customer Segment", segment)
            st.metric("Confidence", f"{confidence:.1%}")
        
        with col2:
            life_stage = safe_get_attribute(insights, 'life_stage', 'unknown').replace('_', ' ').title()
            digital_persona = safe_get_attribute(insights, 'digital_persona', 'unknown').replace('_', ' ').title()
            st.metric("Life Stage", life_stage)
            st.metric("Digital Persona", digital_persona)
        
        with col3:
            financial_profile = safe_get_attribute(insights, 'financial_profile', 'unknown').replace('_', ' ').title()
            communication_style = safe_get_attribute(insights, 'communication_style', 'unknown').title()
            st.metric("Financial Profile", financial_profile)
            st.metric("Communication Style", communication_style)
        
        with col4:
            level = safe_get_attribute(strategy, 'level.value', 'basic').upper()
            processing_time = safe_get_attribute(shared_context, 'processing_time', 0)
            st.metric("Personalization Level", level)
            st.metric("Processing Time", f"{processing_time:.1f}s")
        
        # Customer story
        customer_story = safe_get_attribute(strategy, 'customer_story', '')
        if customer_story:
            st.markdown("**🎯 AI Customer Story:**")
            st.info(customer_story)
        
        # Personalization hooks
        personalization_hooks = safe_get_attribute(insights, 'personalization_hooks', [])
        if personalization_hooks:
            with st.expander("🎣 AI Personalization Hooks", expanded=False):
                for i, hook in enumerate(personalization_hooks[:5], 1):
                    st.write(f"{i}. {hook}")
        
        # Must mention items
        must_mention = safe_get_attribute(strategy, 'must_mention', [])
        if must_mention:
            with st.expander("✅ Must Mention Items", expanded=False):
                for item in must_mention[:3]:
                    st.write(f"• {item}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Error displaying brain intelligence: {e}")

def display_smart_email_result(email_result, shared_context):
    """Display the Smart Email Generator result"""
    
    if not email_result:
        st.error("❌ No email result available")
        return
    
    try:
        st.markdown('<div class="smart-email-showcase">', unsafe_allow_html=True)
        st.markdown("### 📧 Smart Email Result")
        
        # Email metadata
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            quality_score = safe_get_attribute(email_result, 'quality_score', 0)
            st.metric("Quality Score", f"{quality_score:.1%}")
        with col2:
            word_count = safe_get_attribute(email_result, 'word_count', 0)
            st.metric("Words", word_count)
        with col3:
            generation_method = safe_get_attribute(email_result, 'generation_method', 'unknown').replace('_', ' ').title()
            st.metric("Generation Method", generation_method)
        with col4:
            processing_time = safe_get_attribute(email_result, 'processing_time', 0)
            st.metric("Processing Time", f"{processing_time:.2f}s")
        
        # Subject line
        subject_line = safe_get_attribute(email_result, 'subject_line', 'No subject')
        st.markdown("**📝 Subject Line:**")
        st.code(subject_line)
        
        # Email content
        content = safe_get_attribute(email_result, 'content', 'No content available')
        st.markdown("**✉️ Email Content:**")
        st.markdown(f'<div style="background: white; padding: 1.5rem; border-radius: 8px; border: 1px solid #ddd; white-space: pre-wrap;">{content}</div>', unsafe_allow_html=True)
        
        # Personalization achieved
        personalization_elements = safe_get_attribute(email_result, 'personalization_elements', [])
        if personalization_elements:
            with st.expander("🎯 Personalization Elements Applied", expanded=False):
                for i, element in enumerate(personalization_elements, 1):
                    st.write(f"{i}. {element}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Error displaying email result: {e}")

# Initialize session state with error handling
def initialize_session_state():
    """Initialize session state with proper error handling"""
    try:
        if 'shared_brain' not in st.session_state:
            if CORE_MODULES_AVAILABLE:
                st.session_state.shared_brain = SharedBrain()
                print("✅ SharedBrain initialized in session state")
            else:
                st.session_state.shared_brain = None
                
        if 'smart_email_generator' not in st.session_state:
            if CORE_MODULES_AVAILABLE:
                st.session_state.smart_email_generator = SmartEmailGenerator()
                print("✅ SmartEmailGenerator initialized in session state")
            else:
                st.session_state.smart_email_generator = None
                
        if 'sms_orchestrator' not in st.session_state:
            if ADDITIONAL_MODULES_AVAILABLE:
                st.session_state.sms_orchestrator = SimpleSMSOrchestrator()
            else:
                st.session_state.sms_orchestrator = None
                
        if 'voice_generator' not in st.session_state:
            if ADDITIONAL_MODULES_AVAILABLE:
                st.session_state.voice_generator = VoiceNoteGenerator()
            else:
                st.session_state.voice_generator = None

    except Exception as e:
        print(f"Error initializing session state: {e}")

# Initialize other session state variables
def initialize_other_session_state():
    """Initialize other session state variables"""
    if 'shared_context' not in st.session_state:
        st.session_state.shared_context = None
    if 'email_result' not in st.session_state:
        st.session_state.email_result = None
    if 'letter_content' not in st.session_state:
        st.session_state.letter_content = None
    if 'last_letter_hash' not in st.session_state:
        st.session_state.last_letter_hash = None
    if 'doc_analyzed' not in st.session_state:
        st.session_state.doc_analyzed = False
    if 'doc_classification' not in st.session_state:
        st.session_state.doc_classification = None
    if 'doc_key_points' not in st.session_state:
        st.session_state.doc_key_points = None

# Initialize session state
initialize_session_state()
initialize_other_session_state()

# Header with system status
if CORE_MODULES_AVAILABLE:
    st.markdown('''
    <div class="shared-brain-banner">
        <h1>🧠 Lloyds AI Personalization Engine</h1>
        <h3>Powered by Shared Brain Intelligence + Smart Channel Generators</h3>
        <p>Consistent, deeply personalized communications across all channels</p>
    </div>
    ''', unsafe_allow_html=True)
else:
    st.markdown('''
    <div class="error-banner">
        <h1>⚠️ Lloyds AI Personalization Engine - Limited Mode</h1>
        <h3>Some core modules are not available</h3>
        <p>Check your file structure and imports</p>
    </div>
    ''', unsafe_allow_html=True)

# Two columns layout
col1, col2 = st.columns([1, 2])

# LEFT COLUMN - Input and Analysis
with col1:
    st.header("📥 Input & Intelligence")
    
    if not CORE_MODULES_AVAILABLE:
        st.error("❌ Core modules not available. Check:")
        st.error("- src/core/shared_brain.py exists")
        st.error("- src/core/smart_email_generator.py exists") 
        st.error("- Import errors in terminal")
        st.stop()
    
    # Letter upload
    st.subheader("1. Upload Letter")
    letter_file = st.file_uploader(
        "Select letter to analyze and personalize",
        type=['txt', 'docx', 'pdf'],
        help="The Shared Brain will analyze this with AI intelligence"
    )
    
    if letter_file:
        try:
            # Read the file content
            if letter_file.type == 'text/plain':
                letter_content = letter_file.read().decode('utf-8')
            else:
                letter_content = str(letter_file.read())
            
            # Calculate hash
            current_hash = hashlib.md5(letter_content.encode()).hexdigest()
            
            # Check if this is new content
            if st.session_state.last_letter_hash != current_hash:
                st.session_state.letter_content = letter_content
                st.session_state.last_letter_hash = current_hash
                st.session_state.shared_context = None  # Reset analysis
                st.session_state.doc_analyzed = False  # Reset document analysis
            
            # Automatic document analysis on upload
            if st.session_state.letter_content and not st.session_state.doc_analyzed:
                with st.spinner("🔍 Analyzing document with AI..."):
                    # Use the same components SharedBrain uses
                    classifier = AIDocumentClassifier()
                    validator = ContentValidator()
                    
                    # Classify document
                    classification = classifier.classify_document(st.session_state.letter_content)
                    
                    # Extract key points
                    key_points = validator.extract_key_points(st.session_state.letter_content)
                    
                    # Store in session state
                    st.session_state.doc_classification = classification
                    st.session_state.doc_key_points = key_points
                    st.session_state.doc_analyzed = True
            
            # Display Document Analysis
            with st.expander("📄 Document Intelligence", expanded=True):
                if st.session_state.doc_classification:
                    cls = st.session_state.doc_classification
                    
                    # Classification metrics
                    col_a, col_b, col_c, col_d = st.columns(4)
                    with col_a:
                        st.metric("Type", cls.primary_classification)
                    with col_b:
                        confidence = cls.confidence_score * 100
                        color = "🟢" if confidence > 80 else "🟡" if confidence > 60 else "🔴"
                        st.metric("Confidence", f"{confidence:.0f}%")
                    with col_c:
                        urgency_color = "🔴" if cls.urgency_level == "HIGH" else "🟡" if cls.urgency_level == "MEDIUM" else "🟢"
                        st.metric("Urgency", f"{cls.urgency_level}")
                    with col_d:
                        st.metric("Action", "✅ Yes" if cls.customer_action_required else "❌ No")
                    
                    # AI Reasoning
                    with st.expander("🤖 AI Analysis", expanded=False):
                        st.markdown(f"**Reasoning:** {cls.reasoning}")
                        
                        if cls.key_indicators:
                            st.markdown("**Key Evidence Found:**")
                            for i, indicator in enumerate(cls.key_indicators[:5], 1):
                                st.write(f"{i}. {indicator}")
            
            # Display Critical Information to Preserve
            with st.expander("🔒 Critical Information to Preserve", expanded=True):
                if st.session_state.doc_key_points:
                    # Group points by importance (exactly like old app)
                    critical = [p for p in st.session_state.doc_key_points if p.importance == PointImportance.CRITICAL]
                    important = [p for p in st.session_state.doc_key_points if p.importance == PointImportance.IMPORTANT]
                    contextual = [p for p in st.session_state.doc_key_points if p.importance == PointImportance.CONTEXTUAL]
                    
                    # Display exactly like the old app
                    if critical:
                        st.markdown("**🔴 Critical (Must Include):**")
                        for point in critical[:5]:  # Show up to 5 critical points
                            st.write(f"• {point.content}")
                            if point.explanation:
                                st.caption(f"  ↳ {point.explanation}")
                    
                    if important:
                        st.markdown("**🟡 Important:**")
                        for point in important[:3]:  # Show up to 3 important points
                            st.write(f"• {point.content}")
                            if point.explanation:
                                st.caption(f"  ↳ {point.explanation}")
                    
                    if contextual:
                        st.markdown("**🔵 Contextual:**")
                        for point in contextual[:2]:  # Show up to 2 contextual points
                            st.write(f"• {point.content}")
                    
                    # Summary metrics
                    total_points = len(critical) + len(important) + len(contextual)
                    st.caption(f"📊 Total: {len(critical)} critical, {len(important)} important, {len(contextual)} contextual points identified")
                else:
                    st.info("Analyzing content...")
            
            # Letter preview
            with st.expander("📄 Letter Preview", expanded=False):
                preview_text = st.session_state.letter_content[:500] + "..." if len(st.session_state.letter_content) > 500 else st.session_state.letter_content
                st.text_area("Original Letter", preview_text, height=150, disabled=True)
                
        except Exception as e:
            st.error(f"Error reading file: {e}")
            letter_content = None
    
    # Customer data upload
    st.subheader("2. Upload Customer Data")
    customer_file = st.file_uploader(
        "Select customer CSV/Excel file",
        type=['csv', 'xlsx'],
        help="Customer data for personalization analysis"
    )
    
    if customer_file and st.session_state.letter_content:
        try:
            # Load customer data
            if customer_file.type == 'text/csv':
                customers_df = pd.read_csv(customer_file)
            else:
                customers_df = pd.read_excel(customer_file)
            
            st.success(f"Loaded {len(customers_df)} customers")
            
            # Customer selector
            st.subheader("3. Select Customer")
            customer_names = [f"{row['name']} (ID: {row['customer_id']})" 
                             for _, row in customers_df.iterrows()]
            
            selected_customer_name = st.selectbox("Choose customer for analysis:", customer_names)
            
            if selected_customer_name:
                idx = customer_names.index(selected_customer_name)
                selected_customer = customers_df.iloc[idx].to_dict()
                
                # Customer profile preview
                with st.expander("👤 Customer Profile", expanded=False):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write(f"**Name:** {selected_customer.get('name', 'N/A')}")
                        st.write(f"**Age:** {selected_customer.get('age', 'N/A')}")
                        st.write(f"**Language:** {selected_customer.get('preferred_language', 'English')}")
                        st.write(f"**Balance:** £{selected_customer.get('account_balance', 0):,}")
                    with col_b:
                        st.write(f"**Digital Logins:** {selected_customer.get('digital_logins_per_month', 0)}/month")
                        st.write(f"**App Usage:** {selected_customer.get('mobile_app_usage', 'Unknown')}")
                        st.write(f"**Life Events:** {selected_customer.get('recent_life_events', 'None')}")
                        st.write(f"**Years with Bank:** {selected_customer.get('years_with_bank', 0)}")
                
                # THE BIG BUTTON - Shared Brain Analysis
                if st.button("🧠 Analyze with Shared Brain", type="primary", use_container_width=True):
                    
                    if not st.session_state.shared_brain:
                        st.error("❌ Shared Brain not available")
                    else:
                        try:
                            with st.spinner(f"🧠 Shared Brain analyzing {selected_customer['name']}..."):
                                
                                # Run the complete Shared Brain analysis
                                shared_context = st.session_state.shared_brain.analyze_everything(
                                    letter_content=st.session_state.letter_content,
                                    customer_data=selected_customer
                                )
                                
                                # Store the shared context
                                st.session_state.shared_context = shared_context
                                
                                # Generate smart email using the shared context
                                if st.session_state.smart_email_generator:
                                    with st.spinner("📧 Generating smart email..."):
                                        email_result = st.session_state.smart_email_generator.generate_email(shared_context)
                                        st.session_state.email_result = email_result
                                else:
                                    st.session_state.email_result = None
                                
                                processing_time = safe_get_attribute(shared_context, 'processing_time', 0)
                                st.success(f"✅ Complete AI analysis finished in {processing_time:.1f}s!")
                                st.rerun()
                                
                        except Exception as e:
                            st.error(f"❌ Analysis failed: {e}")
                            print(f"Analysis error: {e}")
                            traceback.print_exc()
        
        except Exception as e:
            st.error(f"Error loading customer data: {e}")

# RIGHT COLUMN - Results and Intelligence
with col2:
    st.header("🎯 AI Intelligence & Results")
    
    if st.session_state.shared_context and st.session_state.email_result:
        
        shared_context = st.session_state.shared_context
        email_result = st.session_state.email_result
        customer_name = safe_get_attribute(shared_context, 'customer_data.name', 'Customer')
        
        # Success banner
        segment = safe_get_attribute(shared_context, 'customer_insights.segment', 'UNKNOWN')
        level = safe_get_attribute(shared_context, 'personalization_strategy.level.value', 'basic').upper()
        quality = safe_get_attribute(email_result, 'quality_score', 0)
        
        st.markdown(f'''
        <div class="success-banner">
            <h3>✅ AI Analysis Complete</h3>
            <p><strong>{customer_name}</strong> • Segment: {segment} • 
            Personalization: {level} • 
            Quality: {quality:.0%}</p>
        </div>
        ''', unsafe_allow_html=True)
        
        # Tabbed results interface
        tab1, tab2, tab3, tab4 = st.tabs(["🧠 Intelligence", "📧 Smart Email", "📊 Analysis", "⚙️ System"])
        
        with tab1:
            # INTELLIGENCE TAB - Show the brain's analysis
            display_shared_brain_intelligence(shared_context)
            
            # Channel decisions
            with st.expander("📺 Channel Decisions", expanded=False):
                try:
                    enabled_channels = safe_get_attribute(shared_context, 'channel_decisions.enabled_channels', {})
                    channel_reasons = safe_get_attribute(shared_context, 'channel_decisions.reasons', {})
                    
                    for channel, enabled in enabled_channels.items():
                        status = "✅ Enabled" if enabled else "❌ Disabled"
                        reason = channel_reasons.get(channel, "No reason provided")
                        st.write(f"**{channel.upper()}:** {status} - {reason}")
                except Exception as e:
                    st.error(f"Error displaying channel decisions: {e}")
        
        with tab2:
            # SMART EMAIL TAB - Show the generated email
            display_smart_email_result(email_result, shared_context)
            
            # Email validation
            try:
                if st.session_state.smart_email_generator and hasattr(st.session_state.smart_email_generator, 'validate_email'):
                    validation = st.session_state.smart_email_generator.validate_email(email_result, shared_context)
                    
                    with st.expander("📋 Email Validation", expanded=False):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**✅ Achievements:**")
                            for achievement in validation.get('achievements', []):
                                st.write(f"• {achievement}")
                        
                        with col2:
                            st.write("**⚠️ Issues:**")
                            issues = validation.get('issues', [])
                            if issues:
                                for issue in issues:
                                    st.write(f"• {issue}")
                            else:
                                st.write("• No issues detected")
            except Exception as e:
                st.error(f"Validation error: {e}")
            
            # Download email
            if safe_get_attribute(email_result, 'content', ''):
                try:
                    subject_line = safe_get_attribute(email_result, 'subject_line', 'Email')
                    content = safe_get_attribute(email_result, 'content', '')
                    email_download_content = f"Subject: {subject_line}\n\n{content}"
                    customer_filename = customer_name.replace(' ', '_') if customer_name else 'customer'
                    
                    st.download_button(
                        "📧 Download Complete Email",
                        email_download_content,
                        file_name=f"smart_email_{customer_filename}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Download error: {e}")
        
        with tab3:
            # ANALYSIS TAB - Deep analysis
            try:
                customer_data = safe_get_attribute(shared_context, 'customer_data', {})
                analysis = analyze_personalization_deeply(customer_data, shared_context)
                
                if 'error' in analysis:
                    st.error(f"Analysis error: {analysis['error']}")
                else:
                    st.markdown('<div class="personalization-insights">', unsafe_allow_html=True)
                    st.markdown("### 🎯 Deep Personalization Analysis")
                    
                    # Brain insights
                    st.markdown("**🧠 Brain Insights:**")
                    brain_insights = analysis['brain_insights']
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"• **Segment:** {brain_insights.get('segment', 'UNKNOWN')}")
                        st.write(f"• **Life Stage:** {brain_insights.get('life_stage', 'unknown')}")
                        st.write(f"• **Digital Persona:** {brain_insights.get('digital_persona', 'unknown')}")
                    
                    with col2:
                        st.write(f"• **Financial Profile:** {brain_insights.get('financial_profile', 'unknown')}")
                        st.write(f"• **Communication Style:** {brain_insights.get('communication_style', 'unknown')}")
                        st.write(f"• **Confidence:** {brain_insights.get('confidence', 0):.1%}")
                    
                    # Special factors and hooks
                    if analysis.get('special_factors'):
                        st.markdown("**🎯 Special Factors:**")
                        for factor in analysis['special_factors']:
                            st.write(f"• {factor}")
                    
                    if analysis.get('personalization_hooks'):
                        st.markdown("**🎣 AI Personalization Hooks:**")
                        for i, hook in enumerate(analysis['personalization_hooks'][:5], 1):
                            st.write(f"{i}. {hook}")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
            except Exception as e:
                st.error(f"Analysis tab error: {e}")
        
        with tab4:
            # SYSTEM TAB - Technical details
            st.markdown("### ⚙️ System Performance")
            
            try:
                # Processing metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    processing_time = safe_get_attribute(shared_context, 'processing_time', 0)
                    st.metric("Brain Processing", f"{processing_time:.2f}s")
                with col2:
                    email_time = safe_get_attribute(email_result, 'processing_time', 0)
                    st.metric("Email Generation", f"{email_time:.2f}s")
                with col3:
                    confidence = safe_get_attribute(shared_context, 'analysis_confidence', 0)
                    st.metric("Overall Quality", f"{confidence:.1%}")
                with col4:
                    model = safe_get_attribute(shared_context, 'ai_model_used', 'unknown')
                    model_short = model.split('-')[-1] if '-' in model else model
                    st.metric("AI Model", model_short)
                
                # System details
                with st.expander("🔧 Technical Details", expanded=False):
                    tech_details = {
                        "core_modules_available": CORE_MODULES_AVAILABLE,
                        "additional_modules_available": ADDITIONAL_MODULES_AVAILABLE,
                        "document_classification": safe_get_attribute(shared_context, 'document_classification', {}),
                        "processing_time": safe_get_attribute(shared_context, 'processing_time', 0),
                        "analysis_confidence": safe_get_attribute(shared_context, 'analysis_confidence', 0)
                    }
                    st.json(tech_details)
                    
            except Exception as e:
                st.error(f"System tab error: {e}")
    
    else:
        # Show capabilities when no analysis yet
        if CORE_MODULES_AVAILABLE:
            st.info("👈 Upload a letter and select a customer to see the Shared Brain in action")
            
            st.markdown("### 🧠 Shared Brain Capabilities")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🔍 Deep Analysis**")
                st.write("✅ AI Customer Segmentation")
                st.write("✅ Document Classification")
                st.write("✅ Content Extraction")
                st.write("✅ Rules Engine Integration")
            
            with col2:
                st.markdown("**🎯 Smart Generation**")
                st.write("✅ Personalization Strategy")
                st.write("✅ Channel Decisions")
                st.write("✅ Quality Validation")
                st.write("✅ Multi-language Support")
        else:
            st.error("❌ Core modules not available - check your installation")

# Sidebar for system status
with st.sidebar:
    st.markdown("### 🧠 System Status")
    
    brain_status = "✅ Ready" if (st.session_state.shared_brain and CORE_MODULES_AVAILABLE) else "❌ Error"
    email_status = "✅ Ready" if (st.session_state.smart_email_generator and CORE_MODULES_AVAILABLE) else "❌ Error"
    sms_status = "✅ Ready" if st.session_state.sms_orchestrator else "⚠️ Limited"
    voice_status = "✅ Ready" if st.session_state.voice_generator else "⚠️ Limited"
    
    st.write(f"**Shared Brain:** {brain_status}")
    st.write(f"**Smart Email Gen:** {email_status}")
    st.write(f"**SMS Orchestrator:** {sms_status}")
    st.write(f"**Voice Generator:** {voice_status}")
    
    st.markdown("---")
    
    # Module availability
    st.markdown("### 📦 Module Status")
    core_status = "✅ Loaded" if CORE_MODULES_AVAILABLE else "❌ Failed"
    additional_status = "✅ Loaded" if ADDITIONAL_MODULES_AVAILABLE else "⚠️ Partial"
    
    st.write(f"**Core Modules:** {core_status}")
    st.write(f"**Additional Modules:** {additional_status}")
    
    # Current analysis info
    if st.session_state.shared_context:
        st.markdown("### 📊 Current Analysis")
        try:
            customer_name = safe_get_attribute(st.session_state.shared_context, 'customer_data.name', 'Unknown')
            segment = safe_get_attribute(st.session_state.shared_context, 'customer_insights.segment', 'UNKNOWN')
            confidence = safe_get_attribute(st.session_state.shared_context, 'analysis_confidence', 0)
            
            st.write(f"**Customer:** {customer_name}")
            st.write(f"**Segment:** {segment}")
            st.write(f"**Quality:** {confidence:.0%}")
            
            # Enabled channels
            enabled_channels = safe_get_attribute(st.session_state.shared_context, 'channel_decisions.enabled_channels', {})
            enabled = [ch for ch, en in enabled_channels.items() if en]
            st.write(f"**Channels:** {', '.join(enabled) if enabled else 'None'}")
        except Exception as e:
            st.write(f"**Error:** {e}")
    
    if st.button("🔄 Refresh All Systems"):
        try:
            if CORE_MODULES_AVAILABLE:
                st.session_state.shared_brain = SharedBrain()
                st.session_state.smart_email_generator = SmartEmailGenerator()
            if ADDITIONAL_MODULES_AVAILABLE:
                st.session_state.sms_orchestrator = SimpleSMSOrchestrator()
                st.session_state.voice_generator = VoiceNoteGenerator()
            st.session_state.doc_analyzed = False
            st.success("All available systems refreshed!")
            st.rerun()
        except Exception as e:
            st.error(f"Refresh failed: {e}")

# Footer
st.markdown("---")
footer_text = "🧠 Powered by Shared Brain Intelligence | Claude 4 Sonnet | Lloyds Banking Group"
if not CORE_MODULES_AVAILABLE:
    footer_text += " | ⚠️ Limited Mode"

st.caption(footer_text)