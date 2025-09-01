"""
Lloyds AI Personalization Engine - Modular Version
Cleaner, more maintainable architecture using display modules
WITH all document intelligence, customer insights, and VOICE support
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import hashlib
import os
from typing import Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
import traceback

# Load environment
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import the modular display system
from src.app.displays import CHANNEL_DISPLAYS, get_display_for_channel
from src.app.utils.safe_access import safe_get_attribute

# Import core modules
try:
    from src.core.shared_brain import SharedBrain, SharedContext
    from src.core.smart_email_generator import SmartEmailGenerator
    from src.core.smart_sms_generator import SmartSMSGenerator
    from src.core.smart_letter_generator import SmartLetterGenerator
    from src.core.content_validator import ContentValidator, PointImportance
    from src.core.document_classifier import AIDocumentClassifier
    CORE_MODULES_AVAILABLE = True
    print("✅ Core modules loaded")
except Exception as e:
    CORE_MODULES_AVAILABLE = False
    print(f"❌ Core modules failed: {e}")
    st.error("Core modules not available - check installation")
    st.stop()

# Try to import voice generator (might not exist yet)
try:
    from src.core.smart_voice_generator import SmartVoiceGenerator
    VOICE_AVAILABLE = True
    print("✅ Voice module loaded")
except ImportError:
    VOICE_AVAILABLE = False
    print("⚠️ Voice module not available")

# Page configuration
st.set_page_config(
    page_title="Lloyds AI Engine - Modular",
    page_icon="🧠",
    layout="wide"
)

# Apply Lloyds styling
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
    .personalization-insights {
        background: linear-gradient(135deg, #fff3e0 0%, #ffcc80 100%);
        border: 2px solid #ff9800;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

class PersonalizationApp:
    """Main application class - cleaner organization"""
    
    def __init__(self):
        """Initialize the application"""
        self.initialize_session_state()
        self.setup_generators()
    
    def initialize_session_state(self):
        """Initialize all session state variables"""
        if 'shared_brain' not in st.session_state:
            st.session_state.shared_brain = SharedBrain() if CORE_MODULES_AVAILABLE else None
        
        if 'generators' not in st.session_state:
            st.session_state.generators = {}
        
        # Initialize state variables (including voice)
        state_vars = [
            'shared_context', 'email_result', 'sms_result', 'letter_result', 'voice_result',
            'letter_content', 'last_letter_hash', 'doc_analyzed',
            'doc_classification', 'doc_key_points'
        ]
        
        for var in state_vars:
            if var not in st.session_state:
                st.session_state[var] = None if var != 'doc_analyzed' else False
    
    def setup_generators(self):
        """Setup all channel generators"""
        if CORE_MODULES_AVAILABLE:
            generators = {
                'email': SmartEmailGenerator(),
                'sms': SmartSMSGenerator(),
                'letter': SmartLetterGenerator()
            }
            
            # Add voice if available
            if VOICE_AVAILABLE:
                generators['voice'] = SmartVoiceGenerator()
            
            st.session_state.generators = generators
    
    def display_header(self):
        """Display application header"""
        channels = "Email • SMS • Letter"
        if VOICE_AVAILABLE:
            channels += " • Voice"
        
        st.markdown(f'''
        <div class="shared-brain-banner">
            <h1>🧠 Lloyds AI Personalization Engine</h1>
            <h3>Modular Architecture • Powered by Shared Brain Intelligence</h3>
            <p>{channels} • Extensible for new channels</p>
        </div>
        ''', unsafe_allow_html=True)
    
    def display_sidebar(self):
        """Display sidebar with system status"""
        with st.sidebar:
            st.markdown("### 🧠 System Status")
            
            # Check each module
            modules_status = {
                'Shared Brain': st.session_state.shared_brain is not None,
                'Email Generator': 'email' in st.session_state.generators,
                'SMS Generator': 'sms' in st.session_state.generators,
                'Letter Generator': 'letter' in st.session_state.generators
            }
            
            # Add voice if available
            if VOICE_AVAILABLE:
                modules_status['Voice Generator'] = 'voice' in st.session_state.generators
            
            for module, status in modules_status.items():
                icon = "✅" if status else "❌"
                st.write(f"**{module}:** {icon}")
            
            st.markdown("---")
            
            # Display modules
            st.markdown("### 📦 Display Modules")
            for channel in CHANNEL_DISPLAYS.keys():
                display = get_display_for_channel(channel)
                if display:
                    st.write(f"{display.icon} {channel.title()}: ✅")
            
            # Current analysis info
            if st.session_state.shared_context:
                st.markdown("---")
                st.markdown("### 📊 Current Analysis")
                customer_name = safe_get_attribute(
                    st.session_state.shared_context, 
                    'customer_data.name', 
                    'Unknown'
                )
                segment = safe_get_attribute(
                    st.session_state.shared_context,
                    'customer_insights.segment',
                    'Unknown'
                )
                confidence = safe_get_attribute(
                    st.session_state.shared_context,
                    'analysis_confidence',
                    0
                )
                
                st.write(f"**Customer:** {customer_name}")
                st.write(f"**Segment:** {segment}")
                st.write(f"**Quality:** {confidence:.0%}")
                
                enabled_channels = safe_get_attribute(
                    st.session_state.shared_context,
                    'channel_decisions.enabled_channels',
                    {}
                )
                enabled = [ch for ch, en in enabled_channels.items() if en]
                st.write(f"**Channels:** {', '.join(enabled) if enabled else 'None'}")
    
    def handle_letter_upload(self) -> Optional[str]:
        """Handle letter file upload"""
        letter_file = st.file_uploader(
            "Select letter to analyze",
            type=['txt', 'docx', 'pdf'],
            help="Upload the letter template to personalize"
        )
        
        if letter_file:
            try:
                # Read content
                if letter_file.type == 'text/plain':
                    content = letter_file.read().decode('utf-8')
                else:
                    content = str(letter_file.read())
                
                # Check if content changed
                current_hash = hashlib.md5(content.encode()).hexdigest()
                
                if st.session_state.last_letter_hash != current_hash:
                    st.session_state.letter_content = content
                    st.session_state.last_letter_hash = current_hash
                    st.session_state.shared_context = None
                    st.session_state.doc_analyzed = False
                    
                    # Auto-analyze document
                    self.analyze_document(content)
                
                return content
                
            except Exception as e:
                st.error(f"Error reading file: {e}")
        
        return None
    
    def analyze_document(self, content: str):
        """Analyze document with AI"""
        if not st.session_state.doc_analyzed:
            with st.spinner("🔍 Analyzing document with AI..."):
                classifier = AIDocumentClassifier()
                validator = ContentValidator()
                
                st.session_state.doc_classification = classifier.classify_document(content)
                st.session_state.doc_key_points = validator.extract_key_points(content)
                st.session_state.doc_analyzed = True
    
    def display_document_analysis(self):
        """Display complete document analysis with all insights"""
        if st.session_state.doc_classification:
            with st.expander("📄 Document Intelligence", expanded=True):
                cls = st.session_state.doc_classification
                
                # Classification metrics - using regular text instead of metrics for better display
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown("**Type**")
                    st.write(cls.primary_classification)
                with col2:
                    st.markdown("**Confidence**")
                    confidence = cls.confidence_score * 100
                    st.write(f"{confidence:.0f}%")
                with col3:
                    st.markdown("**Urgency**")
                    st.write(cls.urgency_level)
                with col4:
                    st.markdown("**Action**")
                    st.write("✅ Yes" if cls.customer_action_required else "❌ No")
                
                # AI Reasoning
                with st.expander("🤖 AI Analysis", expanded=False):
                    st.markdown(f"**Reasoning:** {cls.reasoning}")
                    
                    if cls.key_indicators:
                        st.markdown("**Key Evidence Found:**")
                        for i, indicator in enumerate(cls.key_indicators[:5], 1):
                            st.write(f"{i}. {indicator}")
                    
                    # Show AI insights if available
                    if hasattr(cls, 'ai_insights') and cls.ai_insights:
                        insights = cls.ai_insights
                        st.markdown("**AI Insights:**")
                        if 'primary_purpose' in insights:
                            st.write(f"• **Purpose:** {insights['primary_purpose']}")
                        if 'key_message' in insights:
                            st.write(f"• **Key Message:** {insights['key_message']}")
                        if 'target_audience' in insights:
                            st.write(f"• **Target Audience:** {insights['target_audience']}")
                        if 'emotional_impact' in insights:
                            st.write(f"• **Emotional Impact:** {insights['emotional_impact']}")
        
        # Display Critical Information to Preserve
        if st.session_state.doc_key_points:
            with st.expander("🔒 Critical Information to Preserve", expanded=True):
                # Group points by importance
                critical = [p for p in st.session_state.doc_key_points if p.importance == PointImportance.CRITICAL]
                important = [p for p in st.session_state.doc_key_points if p.importance == PointImportance.IMPORTANT]
                contextual = [p for p in st.session_state.doc_key_points if p.importance == PointImportance.CONTEXTUAL]
                
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
                        if point.explanation:
                            st.caption(f"  ↳ {point.explanation}")
                
                if contextual:
                    st.markdown("**🔵 Contextual:**")
                    for point in contextual[:2]:
                        st.write(f"• {point.content}")
                
                # Summary metrics
                total_points = len(critical) + len(important) + len(contextual)
                st.caption(f"📊 Total: {len(critical)} critical, {len(important)} important, {len(contextual)} contextual points identified")
        
        # Letter preview with normal text size
        if st.session_state.letter_content:
            with st.expander("📄 Letter Preview", expanded=False):
                preview_text = st.session_state.letter_content[:500] + "..." if len(st.session_state.letter_content) > 500 else st.session_state.letter_content
                st.text_area("Original Letter", preview_text, height=150, disabled=True)
    
    def handle_customer_selection(self, customers_df: pd.DataFrame) -> Optional[Dict]:
        """Handle customer selection from dataframe with profile preview"""
        customer_names = [
            f"{row['name']} (ID: {row['customer_id']})" 
            for _, row in customers_df.iterrows()
        ]
        
        selected = st.selectbox("Choose customer:", customer_names)
        
        if selected:
            idx = customer_names.index(selected)
            selected_customer = customers_df.iloc[idx].to_dict()
            
            # Display customer profile
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
            
            return selected_customer
        
        return None
    
    def process_customer(self, letter_content: str, customer: Dict):
        """Process customer through all channels"""
        try:
            with st.spinner(f"🧠 Shared Brain analyzing {customer['name']}..."):
                # Run SharedBrain analysis
                shared_context = st.session_state.shared_brain.analyze_everything(
                    letter_content=letter_content,
                    customer_data=customer,
                    existing_classification=st.session_state.doc_classification,
                    existing_key_points=st.session_state.doc_key_points
                )
                
                st.session_state.shared_context = shared_context
                
                # Generate for each enabled channel
                results = {}
                
                for channel_name, generator in st.session_state.generators.items():
                    # Check if channel is enabled (voice might not be in decisions yet)
                    if channel_name == 'voice':
                        # Default voice to enabled for testing
                        enabled = shared_context.channel_decisions['enabled_channels'].get('voice', True)
                    else:
                        enabled = shared_context.channel_decisions['enabled_channels'].get(channel_name, False)
                    
                    if enabled:
                        with st.spinner(f"Generating {channel_name}..."):
                            if channel_name == 'email':
                                results['email'] = generator.generate_email(shared_context)
                            elif channel_name == 'sms':
                                results['sms'] = generator.generate_sms(shared_context)
                            elif channel_name == 'letter':
                                results['letter'] = generator.generate_letter(shared_context)
                            elif channel_name == 'voice' and VOICE_AVAILABLE:
                                results['voice'] = generator.generate_voice_note(shared_context)
                
                # Store results
                for channel, result in results.items():
                    st.session_state[f"{channel}_result"] = result
                
                processing_time = shared_context.processing_time
                st.success(f"✅ Complete AI analysis finished in {processing_time:.1f}s!")
                
                # Show API calls saved if any
                if hasattr(shared_context, 'api_calls_saved') and shared_context.api_calls_saved > 0:
                    st.info(f"💰 Saved {shared_context.api_calls_saved} API calls by reusing existing analysis")
                
                st.rerun()
                
        except Exception as e:
            st.error(f"Processing error: {e}")
            traceback.print_exc()
    
    def display_results(self):
        """Display all results using modular displays"""
        if not st.session_state.shared_context:
            st.info("👈 Upload a letter and select a customer to begin")
            return
        
        # Create tabs for channels
        available_channels = ['intelligence'] + list(CHANNEL_DISPLAYS.keys()) + ['analysis']
        tab_names = ['🧠 Intelligence'] + [
            f"{CHANNEL_DISPLAYS[ch].icon} {ch.title()}" 
            for ch in CHANNEL_DISPLAYS.keys()
        ] + ['📊 Analysis']
        
        tabs = st.tabs(tab_names)
        
        # Intelligence tab
        with tabs[0]:
            self.display_intelligence()
        
        # Channel tabs (using modular displays)
        for i, channel_name in enumerate(CHANNEL_DISPLAYS.keys(), 1):
            with tabs[i]:
                result = st.session_state.get(f"{channel_name}_result")
                display = get_display_for_channel(channel_name)
                
                if result and display:
                    # Display result
                    display.display_result(result, st.session_state.shared_context)
                    
                    # Validation
                    validation = display.validate_result(result, st.session_state.shared_context)
                    display.display_validation(validation)
                    
                    # Download button
                    customer_name = safe_get_attribute(
                        st.session_state.shared_context,
                        'customer_data.name',
                        'Customer'
                    )
                    display.create_download_button(result, customer_name)
                else:
                    if channel_name == 'voice' and not VOICE_AVAILABLE:
                        st.info("🎙️ Voice module not installed yet")
                    else:
                        st.info(f"{channel_name.title()} not generated - may be disabled by rules")
        
        # Analysis tab
        with tabs[-1]:
            self.display_analysis()
    
    def display_intelligence(self):
        """Display complete SharedBrain intelligence with all insights"""
        if not st.session_state.shared_context:
            return
        
        ctx = st.session_state.shared_context
        insights = ctx.customer_insights
        strategy = ctx.personalization_strategy
        
        st.markdown('<div class="intelligence-card">', unsafe_allow_html=True)
        st.markdown("### 🧠 Shared Brain Intelligence")
        
        # Core metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Customer Segment", safe_get_attribute(insights, 'segment', 'Unknown'))
            st.metric("Confidence", f"{safe_get_attribute(insights, 'confidence_score', 0):.1%}")
        
        with col2:
            life_stage = safe_get_attribute(insights, 'life_stage', 'unknown').replace('_', ' ').title()
            st.metric("Life Stage", life_stage)
            digital_persona = safe_get_attribute(insights, 'digital_persona', 'unknown').replace('_', ' ').title()
            st.metric("Digital Persona", digital_persona)
        
        with col3:
            financial_profile = safe_get_attribute(insights, 'financial_profile', 'unknown').replace('_', ' ').title()
            st.metric("Financial Profile", financial_profile)
            communication_style = safe_get_attribute(insights, 'communication_style', 'unknown').title()
            st.metric("Communication Style", communication_style)
        
        with col4:
            level = safe_get_attribute(strategy, 'level.value', 'basic').upper()
            st.metric("Personalization Level", level)
            processing_time = ctx.processing_time
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
        
        # Special factors
        special_factors = safe_get_attribute(insights, 'special_factors', [])
        if special_factors:
            with st.expander("🌟 Special Factors", expanded=False):
                for factor in special_factors:
                    st.write(f"• {factor}")
        
        # Must mention items
        must_mention = safe_get_attribute(strategy, 'must_mention', [])
        if must_mention:
            with st.expander("✅ Must Mention Items", expanded=False):
                for item in must_mention[:3]:
                    st.write(f"• {item}")
        
        # Channel decisions
        with st.expander("📺 Channel Decisions", expanded=False):
            enabled_channels = safe_get_attribute(ctx, 'channel_decisions.enabled_channels', {})
            channel_reasons = safe_get_attribute(ctx, 'channel_decisions.reasons', {})
            
            for channel, enabled in enabled_channels.items():
                status = "✅ Enabled" if enabled else "❌ Disabled"
                reason = channel_reasons.get(channel, "No reason provided")
                st.write(f"**{channel.upper()}:** {status} - {reason}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def display_analysis(self):
        """Display deep personalization analysis"""
        if not st.session_state.shared_context:
            st.info("No analysis available yet")
            return
        
        ctx = st.session_state.shared_context
        insights = ctx.customer_insights
        strategy = ctx.personalization_strategy
        
        st.markdown('<div class="personalization-insights">', unsafe_allow_html=True)
        st.markdown("### 🎯 Deep Personalization Analysis")
        
        # Brain insights
        st.markdown("**🧠 Brain Insights:**")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"• **Segment:** {safe_get_attribute(insights, 'segment', 'UNKNOWN')}")
            st.write(f"• **Life Stage:** {safe_get_attribute(insights, 'life_stage', 'unknown')}")
            st.write(f"• **Digital Persona:** {safe_get_attribute(insights, 'digital_persona', 'unknown')}")
        
        with col2:
            st.write(f"• **Financial Profile:** {safe_get_attribute(insights, 'financial_profile', 'unknown')}")
            st.write(f"• **Communication Style:** {safe_get_attribute(insights, 'communication_style', 'unknown')}")
            st.write(f"• **Confidence:** {safe_get_attribute(insights, 'confidence_score', 0):.1%}")
        
        # Special factors
        special_factors = safe_get_attribute(insights, 'special_factors', [])
        if special_factors:
            st.markdown("**🎯 Special Factors:**")
            for factor in special_factors:
                st.write(f"• {factor}")
        
        # Personalization hooks
        hooks = safe_get_attribute(insights, 'personalization_hooks', [])
        if hooks:
            st.markdown("**🎣 AI Personalization Hooks:**")
            for i, hook in enumerate(hooks[:5], 1):
                st.write(f"{i}. {hook}")
        
        # Connection points
        connection_points = safe_get_attribute(strategy, 'connection_points', {})
        if connection_points:
            st.markdown("**🔗 Connection Points:**")
            for key, value in connection_points.items():
                st.write(f"• **{key}:** {value}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def run(self):
        """Main application loop"""
        self.display_header()
        self.display_sidebar()
        
        # Two column layout
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.header("📥 Input & Intelligence")
            
            # Letter upload
            st.subheader("1. Upload Letter")
            letter_content = self.handle_letter_upload()
            
            if letter_content:
                # Document analysis display
                self.display_document_analysis()
                
                # Customer upload
                st.subheader("2. Upload Customers")
                customer_file = st.file_uploader("Select CSV/Excel", type=['csv', 'xlsx'])
                
                if customer_file:
                    # Load customers
                    if customer_file.type == 'text/csv':
                        customers_df = pd.read_csv(customer_file)
                    else:
                        customers_df = pd.read_excel(customer_file)
                    
                    st.success(f"Loaded {len(customers_df)} customers")
                    
                    # Select customer
                    st.subheader("3. Select Customer")
                    selected_customer = self.handle_customer_selection(customers_df)
                    
                    if selected_customer:
                        # Process button
                        if st.button("🧠 Analyze with Shared Brain", type="primary", use_container_width=True):
                            self.process_customer(letter_content, selected_customer)
        
        with col2:
            st.header("🎯 AI Intelligence & Results")
            self.display_results()

# Run the application
if __name__ == "__main__":
    app = PersonalizationApp()
    app.run()