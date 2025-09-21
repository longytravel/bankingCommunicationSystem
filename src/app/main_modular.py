"""
Lloyds AI Personalization Engine - Modular Version
Cleaner, more maintainable architecture using display modules
WITH all document intelligence, customer insights, VOICE support, and HALLUCINATION DETECTION
UPDATED: Now includes EMAIL REFINEMENT functionality and BANKING SENTIMENT ANALYSIS
"""

import streamlit as st
import pandas as pd
import html
from pathlib import Path
import sys
import hashlib
import os
from typing import Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
import traceback
from contextlib import contextmanager

# Load environment
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import the modular display system
from src.app.displays import CHANNEL_DISPLAYS, get_display_for_channel
from src.app.utils.safe_access import safe_get_attribute

from src.app.styles import (
    apply_lloyds_branding,
    asset_to_data_uri,
    get_brand_asset,
    render_brand_header,
)

# Import refinement modules
try:
    from src.core.email_refiner import EmailRefiner, refine_email
    from src.app.displays.refinement_display import RefinementDisplay
    REFINEMENT_AVAILABLE = True
    print("Email refinement module loaded")
except ImportError as e:
    REFINEMENT_AVAILABLE = False
    print(f"Email refinement not available: {e}")

# Import the PROPER BANKING sentiment analysis modules
try:
    from src.core.sentiment_analyzer_banking import analyze_banking_sentiment
    from src.app.displays.sentiment_display_banking import display_banking_sentiment
    BANKING_SENTIMENT_AVAILABLE = True
    print("Banking sentiment analysis loaded")
except ImportError as e:
    BANKING_SENTIMENT_AVAILABLE = False
    print(f"Banking sentiment not available: {e}")
    # Fallback to simple if banking not available
    try:
        from src.core.sentiment_analyzer_simple import analyze_sentiment_simple
        from src.app.displays.sentiment_display_simple import display_simple_sentiment
        SIMPLE_SENTIMENT_AVAILABLE = True
        print("Using simple sentiment as fallback")
    except:
        SIMPLE_SENTIMENT_AVAILABLE = False

# Import core modules
try:
    from src.core.shared_brain import SharedBrain, SharedContext
    from src.core.smart_email_generator import SmartEmailGenerator
    from src.core.smart_sms_generator import SmartSMSGenerator
    from src.core.smart_letter_generator import SmartLetterGenerator
    from src.core.content_validator import ContentValidator, PointImportance
    from src.core.document_classifier import AIDocumentClassifier
    CORE_MODULES_AVAILABLE = True
    print("Core modules loaded")
except Exception as e:
    CORE_MODULES_AVAILABLE = False
    print(f"Core modules failed: {e}")
    st.error("Core modules not available - check installation")
    st.stop()

# Try to import hallucination detector
try:
    from src.core.hallucination_detector import HallucinationDetector
    HALLUCINATION_AVAILABLE = True
    print("Hallucination detector loaded")
except ImportError:
    HALLUCINATION_AVAILABLE = False
    print("Hallucination detector not available")

# Try to import voice generator (use the enhanced version with audio file support)
try:
    from src.core.voice_note_generator_enhanced import SmartVoiceGenerator
    VOICE_AVAILABLE = True
    print("Voice module loaded (enhanced version with audio support)")
except ImportError:
    try:
        # Fallback to basic voice generator if enhanced not available
        from src.core.voice_note_generator import SmartVoiceGenerator
        VOICE_AVAILABLE = True
        print("Voice module loaded (basic version)")
    except ImportError:
        VOICE_AVAILABLE = False
        print("Voice module not available")

# Page configuration
brand_logo = get_brand_asset('mainLogo.png') or get_brand_asset('mainLogoWhiteBackgroup.png')
page_icon = str(brand_logo) if brand_logo else None

st.set_page_config(
    page_title="Lloyds AI Engine - Modular",
    page_icon=page_icon,
    layout="wide"
)

apply_lloyds_branding()


@contextmanager
def lbg_card(title: str, subtitle: str = "", *, badge: Optional[str] = None):
    """Render a Lloyds-styled card container."""
    wrapper = st.container()

    badge_html = f"<div class='lbg-card-badge'>{html.escape(badge)}</div>" if badge else ""
    subtitle_html = f"<p class='lbg-card-subtitle'>{html.escape(subtitle)}</p>" if subtitle else ""

    header_segments = [
        "<div class='lbg-surface-card'>",
        "  <div class='lbg-card-header'>",
        "    <div>",
    ]

    if badge_html:
        header_segments.append(f"      {badge_html}")

    header_segments.append(f"      <h3 class='lbg-card-title'>{html.escape(title)}</h3>")

    if subtitle_html:
        header_segments.append(f"      {subtitle_html}")

    header_segments.extend([
        "    </div>",
        "  </div>",
        "  <div class='lbg-card-body'>",
    ])

    wrapper.markdown('\n'.join(header_segments), unsafe_allow_html=True)
    body = wrapper.container()
    try:
        yield body
    finally:
        body.markdown("</div></div>", unsafe_allow_html=True)

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
        
        # Initialize state variables (including voice and hallucination)
        state_vars = [
            'shared_context', 'email_result', 'sms_result', 'letter_result', 'voice_result',
            'hallucination_result',  # Add hallucination result
            'letter_content', 'last_letter_hash', 'doc_analyzed',
            'doc_classification', 'doc_key_points'
        ]
        
        # Add refinement state variables
        refinement_vars = [
            'refined_email_result',
            'refine_email_triggered', 
            'refinement_in_progress',
            'refinement_accepted',
            'refinement_rejected'
        ]
        
        # Add sentiment state variables (now banking-focused)
        sentiment_vars = [
            'sentiment_result_banking',  # NEW banking sentiment result
            'sentiment_analysis_result',  # Keep old one for compatibility
            'analyze_sentiment_triggered',
            'sentiment_analysis_in_progress',
            'improve_sentiment_triggered'
        ]
        
        for var in state_vars + refinement_vars + sentiment_vars:
            if var not in st.session_state:
                st.session_state[var] = None if 'result' in var or 'content' in var else False
    
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
                print("Voice generator added to generators")
            
            st.session_state.generators = generators

    def display_header(self):
        """Display application header"""
        channels = ['Email', 'SMS', 'Letter']
        if VOICE_AVAILABLE:
            channels.append('Voice')
        if HALLUCINATION_AVAILABLE:
            channels.append('Hallucination Detection')
        if REFINEMENT_AVAILABLE:
            channels.append('Email Refinement')
        if BANKING_SENTIMENT_AVAILABLE:
            channels.append('Banking Sentiment Analysis')
        elif SIMPLE_SENTIMENT_AVAILABLE:
            channels.append('Sentiment Insights')

        subtitle = ' | '.join(channels) + ' | Powered by Shared Brain Intelligence'
        badge = 'Unified Communications Suite'
        # Use transparentLogo.jpg for green banner
        logo_data = asset_to_data_uri('transparentLogo.jpg')

        render_brand_header(
            title='Lloyds AI Personalisation Engine',
            subtitle=subtitle,
            badge=badge,
            logo=logo_data,
        )

    
    def display_sidebar(self):
        """Display sidebar with system status"""
        with st.sidebar:
            st.markdown("<div class='lbg-section-title'>System Status</div>", unsafe_allow_html=True)

            modules_status = {
                'Shared Brain': st.session_state.shared_brain is not None,
                'Email Generator': 'email' in st.session_state.generators,
                'SMS Generator': 'sms' in st.session_state.generators,
                'Letter Generator': 'letter' in st.session_state.generators,
            }

            if VOICE_AVAILABLE:
                modules_status['Voice Generator'] = 'voice' in st.session_state.generators
            if HALLUCINATION_AVAILABLE:
                modules_status['Hallucination Detector'] = True
            if REFINEMENT_AVAILABLE:
                modules_status['Email Refiner'] = True
            if BANKING_SENTIMENT_AVAILABLE:
                modules_status['Banking Sentiment'] = True
            elif SIMPLE_SENTIMENT_AVAILABLE:
                modules_status['Sentiment Analyzer'] = True

            status_rows = []
            for module, status in modules_status.items():
                tag_class = 'lbg-tag' if status else 'lbg-tag lbg-badge-critical'
                tag_label = 'Active' if status else 'Attention'
                status_rows.append(
                    f"<div class='lbg-sidebar-status'><span>{html.escape(module)}</span><span class='{tag_class}'>{tag_label}</span></div>"
                )

            if status_rows:
                st.markdown("<div class='lbg-card'>" + ''.join(status_rows) + "</div>", unsafe_allow_html=True)

            st.markdown("<div class='lbg-section-title'>Modules</div>", unsafe_allow_html=True)
            module_rows = []
            for channel in CHANNEL_DISPLAYS.keys():
                display = get_display_for_channel(channel)
                if display:
                    module_rows.append(
                        f"<div class='lbg-sidebar-status'><span>{html.escape(channel.title())}</span><span class='lbg-tag'>Ready</span></div>"
                    )

            if module_rows:
                st.markdown("<div class='lbg-card'>" + ''.join(module_rows) + "</div>", unsafe_allow_html=True)

            if st.session_state.shared_context:
                st.markdown("<div class='lbg-section-title'>Current Analysis</div>", unsafe_allow_html=True)
                customer_name = safe_get_attribute(st.session_state.shared_context, 'customer_data.name', 'Unknown')
                segment = safe_get_attribute(st.session_state.shared_context, 'customer_insights.segment', 'Unknown')
                confidence = safe_get_attribute(st.session_state.shared_context, 'analysis_confidence', 0)
                enabled_channels = safe_get_attribute(
                    st.session_state.shared_context,
                    'channel_decisions.enabled_channels',
                    {},
                )
                enabled = [ch.title() for ch, flag in enabled_channels.items() if flag]

                sidebar_pairs = [
                    ('Customer', customer_name),
                    ('Segment', segment),
                    ('Quality', f"{confidence:.0%}"),
                    ('Channels', ', '.join(enabled) if enabled else 'None'),
                ]

                if st.session_state.hallucination_result:
                    report = st.session_state.hallucination_result
                    sidebar_pairs.append(
                        (
                            'Hallucination Risk',
                            f"{report.total_hallucinations} findings | {report.risk_score:.0%} risk",
                        )
                    )

                if st.session_state.refined_email_result:
                    sidebar_pairs.append(('Email Refinement', 'Completed'))

                if st.session_state.sentiment_result_banking:
                    sentiment_ready = 'Ready' if st.session_state.sentiment_result_banking.get('ready_to_send', False) else 'Review'
                    sidebar_pairs.append(
                        ('Banking Sentiment', f"{st.session_state.sentiment_result_banking.get('overall_score', 0)}/100 | {sentiment_ready}")
                    )

                analysis_rows = []
                for label, value in sidebar_pairs:
                    analysis_rows.append(
                        f"<div class='lbg-sidebar-status'><span>{html.escape(label)}</span><span>{html.escape(str(value))}</span></div>"
                    )

                st.markdown("<div class='lbg-card'>" + ''.join(analysis_rows) + "</div>", unsafe_allow_html=True)

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
            with st.spinner("Analysing document with AI..."):
                classifier = AIDocumentClassifier()
                validator = ContentValidator()
                
                st.session_state.doc_classification = classifier.classify_document(content)
                st.session_state.doc_key_points = validator.extract_key_points(content)
                st.session_state.doc_analyzed = True
    
    def display_document_analysis(self):
        """Display complete document analysis with all insights"""
        if st.session_state.doc_classification:
            with st.expander("Document Intelligence", expanded=True):
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
                    st.write("Yes" if cls.customer_action_required else "No")
                
                # AI Reasoning
                with st.expander("AI Analysis", expanded=False):
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
                            st.write(f"**Purpose:** {insights['primary_purpose']}")
                        if 'key_message' in insights:
                            st.write(f"**Key Message:** {insights['key_message']}")
                        if 'target_audience' in insights:
                            st.write(f"**Target Audience:** {insights['target_audience']}")
                        if 'emotional_impact' in insights:
                            st.write(f"**Emotional Impact:** {insights['emotional_impact']}")
        
        # Display Critical Information to Preserve
        if st.session_state.doc_key_points:
            with st.expander("Critical Information to Preserve", expanded=True):
                # Group points by importance
                critical = [p for p in st.session_state.doc_key_points if p.importance == PointImportance.CRITICAL]
                important = [p for p in st.session_state.doc_key_points if p.importance == PointImportance.IMPORTANT]
                contextual = [p for p in st.session_state.doc_key_points if p.importance == PointImportance.CONTEXTUAL]
                
                if critical:
                    st.markdown("**Critical (Must Include):**")
                    for point in critical[:5]:
                        st.write(f"- {point.content}")
                        if point.explanation:
                            st.caption(point.explanation)
                
                if important:
                    st.markdown("**Important:**")
                    for point in important[:3]:
                        st.write(f"- {point.content}")
                        if point.explanation:
                            st.caption(point.explanation)
                
                if contextual:
                    st.markdown("**Contextual:**")
                    for point in contextual[:2]:
                        st.write(f"- {point.content}")
                
                # Summary metrics
                total_points = len(critical) + len(important) + len(contextual)
                st.caption(f"Total: {len(critical)} critical, {len(important)} important, {len(contextual)} contextual points identified")
        
        # Letter preview with scrollable full content
        if st.session_state.letter_content:
            with st.expander("📄 Full Letter Preview", expanded=False):
                # Create a scrollable container with full letter content using the styled class
                st.markdown(
                    f'<div class="letter-preview-container">{html.escape(st.session_state.letter_content)}</div>',
                    unsafe_allow_html=True
                )
    
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
            with st.expander("Customer Profile", expanded=False):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write(f"**Name:** {selected_customer.get('name', 'N/A')}")
                    st.write(f"**Age:** {selected_customer.get('age', 'N/A')}")
                    st.write(f"**Language:** {selected_customer.get('preferred_language', 'English')}")
                    st.write(f"**Balance:** {selected_customer.get('account_balance', 0):,}")
                with col_b:
                    st.write(f"**Digital Logins:** {selected_customer.get('digital_logins_per_month', 0)}/month")
                    st.write(f"**App Usage:** {selected_customer.get('mobile_app_usage', 'Unknown')}")
                    st.write(f"**Life Events:** {selected_customer.get('recent_life_events', 'None')}")
                    st.write(f"**Years with Bank:** {selected_customer.get('years_with_bank', 0)}")
            
            return selected_customer
        
        return None
    
    def process_customer(self, letter_content: str, customer: Dict):
        """Process customer through all channels and run hallucination detection"""
        try:
            with st.spinner(f"Shared Brain analysing {customer['name']}..."):
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
                
                # RUN HALLUCINATION DETECTION ON ALL GENERATED CONTENT
                if HALLUCINATION_AVAILABLE and results:
                    with st.spinner("Running hallucination detection..."):
                        # Prepare content for hallucination detection
                        generated_content = {}
                        for channel, result in results.items():
                            if result and hasattr(result, 'content') and result.content:
                                generated_content[channel] = result.content
                        
                        # Only run if we have content to check
                        if generated_content:
                            detector = HallucinationDetector()
                            hallucination_report = detector.detect_hallucinations(
                                generated_content=generated_content,
                                original_letter=letter_content,
                                customer_data=customer,
                                shared_context=shared_context
                            )
                            
                            # Store the hallucination report
                            st.session_state.hallucination_result = hallucination_report
                            
                            # Log summary
                            print(f"Hallucination Detection Complete:")
                            print(f"Total Findings: {hallucination_report.total_hallucinations}")
                            print(f"Risk Score: {hallucination_report.risk_score:.0%}")
                            print(f"Channels Analyzed: {', '.join(hallucination_report.channels_analyzed)}")
                
                processing_time = shared_context.processing_time
                st.success(f"Complete AI analysis finished in {processing_time:.1f}s!")
                
                # Show API calls saved if any
                if hasattr(shared_context, 'api_calls_saved') and shared_context.api_calls_saved > 0:
                    st.info(f"Saved {shared_context.api_calls_saved} API calls by reusing existing analysis")
                
                # Show hallucination summary if detected
                if HALLUCINATION_AVAILABLE and st.session_state.hallucination_result:
                    report = st.session_state.hallucination_result
                    if report.total_hallucinations > 0:
                        st.warning(f"Detected {report.total_hallucinations} potential hallucination(s) - Risk: {report.risk_score:.0%}")
                    else:
                        st.success("No hallucinations detected in generated content")
                
                st.rerun()
                
        except Exception as e:
            st.error(f"Processing error: {e}")
            traceback.print_exc()
    
    def display_results(self):
        """Display all results using modular displays"""
        if not st.session_state.shared_context:
            st.info("Upload a letter and select a customer to begin")
            return
        
        # Create tabs for channels
        available_channels = ['intelligence'] + list(CHANNEL_DISPLAYS.keys()) + ['analysis']
        tab_names = [' Intelligence'] + [
            f"{CHANNEL_DISPLAYS[ch].icon} {ch.title()}" 
            for ch in CHANNEL_DISPLAYS.keys()
        ] + [' Analysis']
        
        tabs = st.tabs(tab_names)
        
        # Intelligence tab
        with tabs[0]:
            self.display_intelligence()
        
        # Channel tabs (using modular displays)
        for i, channel_name in enumerate(CHANNEL_DISPLAYS.keys(), 1):
            with tabs[i]:
                # Special handling for hallucination tab
                if channel_name == 'hallucination':
                    # Display hallucination report if available
                    if st.session_state.hallucination_result:
                        display = get_display_for_channel(channel_name)
                        if display:
                            display.display_result(
                                st.session_state.hallucination_result, 
                                st.session_state.shared_context
                            )
                            
                            # Validation
                            validation = display.validate_result(
                                st.session_state.hallucination_result, 
                                st.session_state.shared_context
                            )
                            display.display_validation(validation)
                            
                            # Download button
                            customer_name = safe_get_attribute(
                                st.session_state.shared_context,
                                'customer_data.name',
                                'Customer'
                            )
                            display.create_download_button(
                                st.session_state.hallucination_result, 
                                customer_name
                            )
                            
                            # HANDLE EMAIL REFINEMENT TRIGGER
                            if st.session_state.get('refine_email_triggered', False) and REFINEMENT_AVAILABLE:
                                # Clear the trigger
                                st.session_state.refine_email_triggered = False
                                
                                # Check if we have what we need
                                if (st.session_state.get('email_result') and 
                                    st.session_state.get('hallucination_result') and
                                    st.session_state.get('shared_context')):
                                    
                                    with st.spinner("Refining email... Removing hallucinations and enhancing personalisation..."):
                                        # Perform refinement
                                        refined_result = refine_email(
                                            st.session_state.email_result,
                                            st.session_state.hallucination_result,
                                            st.session_state.shared_context
                                        )
                                        
                                        # Store refined result
                                        st.session_state.refined_email_result = refined_result
                                        st.session_state.refinement_in_progress = False
                                    
                                    # Display refinement results
                                    st.markdown("---")
                                    refinement_display = RefinementDisplay()
                                    refinement_display.display_refinement_in_hallucination_tab(
                                        refined_result,
                                        st.session_state.shared_context
                                    )
                                    
                                    # BANKING SENTIMENT ANALYSIS SECTION
                                    if BANKING_SENTIMENT_AVAILABLE:
                                        st.markdown("---")
                                        st.markdown("###  Banking Sentiment Analysis")
                                        
                                        # Check if we already have results
                                        if st.session_state.get('sentiment_result_banking'):
                                            # Display existing results
                                            display_banking_sentiment(
                                                st.session_state.sentiment_result_banking,
                                                refined_result.refined_content
                                            )
                                            
                                            # Option to re-analyze
                                            if st.button("Re-analyse Sentiment", key="reanalyze_sentiment_banking"):
                                                st.session_state.sentiment_result_banking = None
                                                st.rerun()
                                        else:
                                            # No analysis yet - show button to trigger
                                            st.info("Analyse the emotional tone, compliance, NPS impact, and predicted customer response.")
                                            
                                            if st.button("Analyse Banking Sentiment", type="primary", use_container_width=True, key="analyze_sentiment_button"):
                                                with st.spinner("Analysing with banking-specific metrics..."):
                                                    try:
                                                        # Get what we need
                                                        email_content = refined_result.refined_content
                                                        customer_name = st.session_state.shared_context.customer_data.get('name', 'Customer')
                                                        
                                                        # Build customer context for better analysis
                                                        customer_context = {
                                                            'segment': safe_get_attribute(
                                                                st.session_state.shared_context.customer_insights,
                                                                'segment',
                                                                'Unknown'
                                                            ),
                                                            'life_stage': safe_get_attribute(
                                                                st.session_state.shared_context.customer_insights,
                                                                'life_stage',
                                                                'Unknown'
                                                            ),
                                                            'digital_persona': safe_get_attribute(
                                                                st.session_state.shared_context.customer_insights,
                                                                'digital_persona',
                                                                'Unknown'
                                                            ),
                                                            'financial_profile': safe_get_attribute(
                                                                st.session_state.shared_context.customer_insights,
                                                                'financial_profile',
                                                                'Unknown'
                                                            )
                                                        }
                                                        
                                                        # Run banking analyzer
                                                        result = analyze_banking_sentiment(
                                                            email_content, 
                                                            customer_name,
                                                            customer_context
                                                        )
                                                        
                                                        # Store in session state
                                                        st.session_state.sentiment_result_banking = result
                                                        
                                                        st.success("Banking sentiment analysis complete")
                                                        st.rerun()
                                                        
                                                    except Exception as e:
                                                        st.error(f"Analysis failed: {str(e)}")
                                                        st.info("Check your Claude API key in .env file")
                                                        import traceback
                                                        st.error(traceback.format_exc())
                                    
                                    # Fallback to simple sentiment if banking not available
                                    elif SIMPLE_SENTIMENT_AVAILABLE:
                                        st.markdown("---")
                                        st.markdown("###  Sentiment Analysis (Simple)")
                                        st.warning("Banking sentiment analyzer not available - using simple version")
                                        # Simple sentiment code here...
                                
                                else:
                                    st.error("Missing required data for refinement")
                                    st.session_state.refinement_in_progress = False
                            
                            # Display previous refinement if exists
                            elif st.session_state.get('refined_email_result') and REFINEMENT_AVAILABLE:
                                st.markdown("---")
                                st.markdown("###  Previous Refinement")
                                refinement_display = RefinementDisplay()
                                refinement_display.display_refinement_in_hallucination_tab(
                                    st.session_state.refined_email_result,
                                    st.session_state.shared_context
                                )
                                
                                # BANKING SENTIMENT ANALYSIS SECTION (for existing refinement)
                                if BANKING_SENTIMENT_AVAILABLE:
                                    st.markdown("---")
                                    st.markdown("###  Banking Sentiment Analysis")
                                    
                                    if st.session_state.get('sentiment_result_banking'):
                                        # Display existing sentiment analysis
                                        display_banking_sentiment(
                                            st.session_state.sentiment_result_banking,
                                            st.session_state.refined_email_result.refined_content
                                        )
                                        
                                        # Option to re-analyze
                                        if st.button("Re-analyse Sentiment", key="reanalyze_existing_sentiment"):
                                            st.session_state.sentiment_result_banking = None
                                            st.rerun()
                                    else:
                                        # Show button to trigger sentiment analysis
                                        st.info("Analyse the emotional tone, compliance, and NPS impact of your refined email.")
                                        
                                        if st.button("Analyse Banking Sentiment", type="primary", use_container_width=True, key="analyze_existing_sentiment"):
                                            with st.spinner("Analysing with banking metrics..."):
                                                try:
                                                    email_content = st.session_state.refined_email_result.refined_content
                                                    customer_name = st.session_state.shared_context.customer_data.get('name', 'Customer')
                                                    
                                                    # Build customer context
                                                    customer_context = {
                                                        'segment': safe_get_attribute(
                                                            st.session_state.shared_context.customer_insights,
                                                            'segment',
                                                            'Unknown'
                                                        ),
                                                        'life_stage': safe_get_attribute(
                                                            st.session_state.shared_context.customer_insights,
                                                            'life_stage',
                                                            'Unknown'
                                                        ),
                                                        'digital_persona': safe_get_attribute(
                                                            st.session_state.shared_context.customer_insights,
                                                            'digital_persona',
                                                            'Unknown'
                                                        ),
                                                        'financial_profile': safe_get_attribute(
                                                            st.session_state.shared_context.customer_insights,
                                                            'financial_profile',
                                                            'Unknown'
                                                        )
                                                    }
                                                    
                                                    result = analyze_banking_sentiment(
                                                        email_content,
                                                        customer_name,
                                                        customer_context
                                                    )
                                                    st.session_state.sentiment_result_banking = result
                                                    st.success("Banking sentiment analysis complete")
                                                    st.rerun()
                                                except Exception as e:
                                                    st.error(f"Banking sentiment analysis failed: {str(e)}")
                    else:
                        st.info("No hallucination analysis available yet. Generate content first.")
                else:
                    # Normal channel display
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
                            st.info("Voice module not installed yet")
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

        st.markdown("<div class='lbg-card is-highlight'>", unsafe_allow_html=True)
        st.markdown("### Shared Brain Intelligence")

        metric_tiles = [
            ('Segment', safe_get_attribute(insights, 'segment', 'Unknown').title()),
            ('Confidence', f"{safe_get_attribute(insights, 'confidence_score', 0):.1%}"),
            ('Life Stage', safe_get_attribute(insights, 'life_stage', 'unknown').replace('_', ' ').title()),
            ('Digital Persona', safe_get_attribute(insights, 'digital_persona', 'unknown').replace('_', ' ').title()),
            ('Financial Profile', safe_get_attribute(insights, 'financial_profile', 'unknown').replace('_', ' ').title()),
            ('Comm Style', safe_get_attribute(insights, 'communication_style', 'unknown').title()),
            ('Personalisation Level', safe_get_attribute(strategy, 'level.value', 'basic').upper()),
            ('Processing Time', f"{ctx.processing_time:.2f}s" if ctx.processing_time else 'n/a'),
        ]

        metric_html = ''.join(
            f"<div class='lbg-metric-tile'><div class='lbg-metric-label'>{html.escape(label)}</div><div class='lbg-metric-value'>{html.escape(value)}</div></div>"
            for label, value in metric_tiles
        )
        st.markdown("<div class='lbg-metric-grid'>" + metric_html + "</div>", unsafe_allow_html=True)

        special_factors = safe_get_attribute(insights, 'special_factors', []) or []
        if special_factors:
            tag_html = ''.join(f"<span class='lbg-tag'>{html.escape(str(factor))}</span>" for factor in special_factors)
            st.markdown("<div class='lbg-section-title'>Key Drivers</div>", unsafe_allow_html=True)
            st.markdown(tag_html, unsafe_allow_html=True)

        hooks = safe_get_attribute(insights, 'personalization_hooks', []) or []
        if hooks:
            st.markdown("<div class='lbg-section-title'>Personalisation Hooks</div>", unsafe_allow_html=True)
            for idx, hook in enumerate(hooks[:5], 1):
                st.markdown(f"{idx}. {hook}")

        connection_points = safe_get_attribute(strategy, 'connection_points', {}) or {}
        if connection_points:
            st.markdown("<div class='lbg-section-title'>Connection Points</div>", unsafe_allow_html=True)
            for key, value in connection_points.items():
                st.markdown(f"- **{key.replace('_', ' ').title()}:** {value}")

        st.markdown('</div>', unsafe_allow_html=True)

    def display_analysis(self):
        """Display deep personalization analysis"""
        if not st.session_state.shared_context:
            st.info('No analysis available yet')
            return

        ctx = st.session_state.shared_context
        insights = ctx.customer_insights
        strategy = ctx.personalization_strategy

        st.markdown("<div class='lbg-card'>", unsafe_allow_html=True)
        st.markdown("### Deep Personalisation Analysis")

        st.markdown("<div class='lbg-section-title'>Brain Insights</div>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"- **Segment:** {safe_get_attribute(insights, 'segment', 'UNKNOWN')}")
            st.write(f"- **Life Stage:** {safe_get_attribute(insights, 'life_stage', 'unknown')}")
            st.write(f"- **Digital Persona:** {safe_get_attribute(insights, 'digital_persona', 'unknown')}")
        with col2:
            st.write(f"- **Financial Profile:** {safe_get_attribute(insights, 'financial_profile', 'unknown')}")
            st.write(f"- **Communication Style:** {safe_get_attribute(insights, 'communication_style', 'unknown')}")
            st.write(f"- **Confidence:** {safe_get_attribute(insights, 'confidence_score', 0):.1%}")

        special_factors = safe_get_attribute(insights, 'special_factors', [])
        if special_factors:
            st.markdown("<div class='lbg-section-title'>Special Factors</div>", unsafe_allow_html=True)
            tags = ''.join(f"<span class='lbg-tag'>{html.escape(str(factor))}</span>" for factor in special_factors)
            st.markdown(tags, unsafe_allow_html=True)

        hooks = safe_get_attribute(insights, 'personalization_hooks', [])
        if hooks:
            st.markdown("<div class='lbg-section-title'>AI Personalisation Hooks</div>", unsafe_allow_html=True)
            for i, hook in enumerate(hooks[:5], 1):
                st.markdown(f"{i}. {hook}")

        connection_points = safe_get_attribute(strategy, 'connection_points', {})
        if connection_points:
            st.markdown("<div class='lbg-section-title'>Connection Points</div>", unsafe_allow_html=True)
            for key, value in connection_points.items():
                st.markdown(f"- **{key.replace('_', ' ').title()}:** {value}")

        if st.session_state.hallucination_result:
            st.markdown("<div class='lbg-divider'></div>", unsafe_allow_html=True)
            st.markdown("**Hallucination Analysis Summary**")
            report = st.session_state.hallucination_result

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Findings", report.total_hallucinations)
            with col2:
                st.metric("Risk Score", f"{report.risk_score:.0%}")
            with col3:
                st.metric("Confidence", f"{report.analysis_confidence:.0%}")

            if report.summary:
                st.info(report.summary)

            if report.recommendations:
                st.markdown("**Recommendations:**")
                for rec in report.recommendations[:3]:
                    st.markdown(f"- {rec}")

        if st.session_state.refined_email_result and REFINEMENT_AVAILABLE:
            st.markdown("<div class='lbg-divider'></div>", unsafe_allow_html=True)
            st.markdown("**Email Refinement Summary**")
            refined = st.session_state.refined_email_result

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Hallucinations Removed", refined.metrics.hallucinations_removed)
            with col2:
                st.metric("Inferences Added", refined.metrics.inferences_added)
            with col3:
                quality_delta = (refined.metrics.quality_score_after - refined.metrics.quality_score_before) * 100
                st.metric("Quality Improvement", f"+{quality_delta:.0f}%")
            with col4:
                personal_delta = (refined.metrics.personalization_score_after - refined.metrics.personalization_score_before) * 100
                st.metric("Personalisation Boost", f"+{personal_delta:.0f}%")

        if st.session_state.sentiment_result_banking and BANKING_SENTIMENT_AVAILABLE:
            st.markdown("<div class='lbg-divider'></div>", unsafe_allow_html=True)
            st.markdown("**Banking Sentiment Summary**")
            sentiment = st.session_state.sentiment_result_banking

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Overall Score", f"{sentiment.get('overall_score', 0)}/100")
            with col2:
                ready_text = 'Ready' if sentiment.get('ready_to_send', False) else 'Requires Review'
                st.metric("Status", ready_text)
            with col3:
                complaint_risk = sentiment.get('customer_impact', {}).get('complaint_risk', 0)
                st.metric("Complaint Risk", f"{complaint_risk:.0f}%")
            with col4:
                nps_impact = sentiment.get('nps_impact', {}).get('predicted_impact', 0)
                st.metric("NPS Impact", f"{'+' if nps_impact > 0 else ''}{nps_impact}")

            if 'executive_summary' in sentiment:
                st.info(sentiment['executive_summary'])

            if 'decision_rationale' in sentiment:
                rationale = sentiment['decision_rationale']
                with st.expander("Decision Factors"):
                    for factor in rationale.get('primary_factors', []):
                        st.markdown(f"- {factor}")

        st.markdown('</div>', unsafe_allow_html=True)



    def run(self):
        """Main application loop"""
        self.display_header()
        self.display_sidebar()

        col1, col2 = st.columns([1, 2])

        with col1:
            with lbg_card(
                "Input Workspace",
                "Upload source material and prepare the Shared Brain journey.",
                badge="Setup",
            ):
                st.markdown(
                    """
                    <div class='lbg-step-item'>
                        <div class='lbg-step-icon'>1</div>
                        <div class='lbg-step-content'>
                            <h4>Upload Letter Template</h4>
                            <p>Select the base document you want the engine to personalise.</p>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                letter_content = self.handle_letter_upload()
                active_letter = letter_content or st.session_state.get('letter_content')

                if active_letter:
                    st.markdown("<div class='lbg-divider'></div>", unsafe_allow_html=True)
                    st.markdown("#### Document Intelligence")
                    self.display_document_analysis()

                    st.markdown("<div class='lbg-divider'></div>", unsafe_allow_html=True)
                    st.markdown(
                        """
                        <div class='lbg-step-item'>
                            <div class='lbg-step-icon'>2</div>
                            <div class='lbg-step-content'>
                                <h4>Upload Customer Data</h4>
                                <p>Provide the audience list so the engine can tailor messaging per persona.</p>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    customer_file = st.file_uploader("Select CSV/Excel", type=['csv', 'xlsx'])

                    if customer_file:
                        if customer_file.type == 'text/csv':
                            customers_df = pd.read_csv(customer_file)
                        else:
                            customers_df = pd.read_excel(customer_file)

                        st.success(f"Loaded {len(customers_df)} customers")

                        st.markdown(
                            """
                            <div class='lbg-step-item'>
                                <div class='lbg-step-icon'>3</div>
                                <div class='lbg-step-content'>
                                    <h4>Select Customer & Analyse</h4>
                                    <p>Review insights and launch Shared Brain for the selected profile.</p>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        selected_customer = self.handle_customer_selection(customers_df)

                        if selected_customer:
                            if st.button("Analyse with Shared Brain", type="primary", use_container_width=True):
                                self.process_customer(active_letter, selected_customer)
                else:
                    st.caption("Accepted formats: TXT, DOCX, PDF (max 200MB).")

        with col2:
            with lbg_card(
                "AI Intelligence & Results",
                "Review personalised outputs, validations, and channel intelligence.",
                badge="Shared Brain",
            ):
                self.display_results()


# Run the application
if __name__ == "__main__":
    app = PersonalizationApp()
    app.run()
