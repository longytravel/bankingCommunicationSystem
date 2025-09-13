"""
Refinement Display Module - Shows email refinement results
Displays before/after comparison, metrics, and improvements
"""

import streamlit as st
from typing import Any, Dict, Optional, Tuple
from datetime import datetime
from .base_display import BaseChannelDisplay

# Import refinement types
try:
    from src.core.email_refiner import RefinedEmailResult, RefinementMetrics, InferenceRule
    REFINER_AVAILABLE = True
except ImportError:
    REFINER_AVAILABLE = False
    print("⚠️ Email refiner not available")

class RefinementDisplay(BaseChannelDisplay):
    """Display handler for email refinement results"""
    
    def __init__(self):
        super().__init__("Email Refinement", "✨")
        self.style = """
        <style>
        .refinement-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 10px;
            margin-bottom: 1.5rem;
            text-align: center;
        }
        
        .metrics-improvement {
            background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
            padding: 1.5rem;
            border-radius: 10px;
            margin: 1rem 0;
        }
        
        .before-after-container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 20px 0;
        }
        
        .before-box {
            background: #fff5f5;
            border: 2px solid #feb2b2;
            border-radius: 10px;
            padding: 1.5rem;
        }
        
        .after-box {
            background: #f0fff4;
            border: 2px solid #9ae6b4;
            border-radius: 10px;
            padding: 1.5rem;
        }
        
        .hallucination-removed {
            background: #fed7d7;
            text-decoration: line-through;
            padding: 2px 4px;
            border-radius: 3px;
        }
        
        .inference-added {
            background: #c6f6d5;
            padding: 2px 4px;
            border-radius: 3px;
            font-weight: bold;
        }
        
        .metric-card {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            margin: 0.5rem 0;
        }
        
        .metric-label {
            color: #666;
            font-size: 0.9em;
        }
        
        .improvement-arrow {
            color: #48bb78;
            font-size: 1.2em;
        }
        
        .action-buttons {
            display: flex;
            gap: 10px;
            margin-top: 20px;
            justify-content: center;
        }
        
        .personalization-dna {
            background: #f7fafc;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        
        .dna-bar {
            height: 30px;
            background: linear-gradient(to right, #4299e1 0%, #48bb78 100%);
            border-radius: 15px;
            position: relative;
            margin: 10px 0;
        }
        
        .dna-marker {
            position: absolute;
            top: -5px;
            width: 40px;
            height: 40px;
            background: white;
            border: 3px solid #333;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
        }
        </style>
        """
    
    def display_refinement_in_hallucination_tab(
        self,
        refined_result: 'RefinedEmailResult',
        shared_context: Any
    ) -> None:
        """Display refinement results within the hallucination tab"""
        
        if not refined_result or not REFINER_AVAILABLE:
            st.error("❌ No refinement results available")
            return
        
        try:
            # Apply custom styling
            st.markdown(self.style, unsafe_allow_html=True)
            
            # Header
            st.markdown('''
            <div class="refinement-header">
                <h2>✨ Email Refinement Complete</h2>
                <p>Hallucinations removed, personalization enhanced</p>
            </div>
            ''', unsafe_allow_html=True)
            
            # Display metrics improvement
            self._display_metrics_improvement(refined_result.metrics)
            
            # Show what was fixed
            self._display_fixes_applied(refined_result)
            
            # Before/After comparison
            self._display_before_after(refined_result)
            
            # Personalization DNA
            self._display_personalization_dna(refined_result)
            
            # Action buttons
            self._display_action_buttons(refined_result)
            
        except Exception as e:
            st.error(f"Error displaying refinement: {e}")
            import traceback
            st.error(traceback.format_exc())
    
    def _display_metrics_improvement(self, metrics: 'RefinementMetrics') -> None:
        """Display improvement metrics"""
        
        st.markdown("### 📊 Refinement Impact")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            hallucinations_icon = "🚫" if metrics.hallucinations_removed > 0 else "✅"
            st.metric(
                f"{hallucinations_icon} Hallucinations",
                f"{metrics.hallucinations_removed} removed",
                delta=f"-{metrics.hallucinations_removed}" if metrics.hallucinations_removed > 0 else "Clean"
            )
        
        with col2:
            inferences_icon = "➕" if metrics.inferences_added > 0 else "📝"
            st.metric(
                f"{inferences_icon} Inferences",
                f"{metrics.inferences_added} added",
                delta=f"+{metrics.inferences_added}" if metrics.inferences_added > 0 else None
            )
        
        with col3:
            quality_before = metrics.quality_score_before * 100
            quality_after = metrics.quality_score_after * 100
            quality_delta = quality_after - quality_before
            st.metric(
                "📈 Quality Score",
                f"{quality_after:.0f}%",
                delta=f"+{quality_delta:.0f}%" if quality_delta > 0 else f"{quality_delta:.0f}%"
            )
        
        with col4:
            personalization_before = metrics.personalization_score_before * 100
            personalization_after = metrics.personalization_score_after * 100
            personalization_delta = personalization_after - personalization_before
            st.metric(
                "🎯 Personalization",
                f"{personalization_after:.0f}%",
                delta=f"+{personalization_delta:.0f}%" if personalization_delta > 0 else f"{personalization_delta:.0f}%"
            )
    
    def _display_fixes_applied(self, refined_result: 'RefinedEmailResult') -> None:
        """Show what was fixed"""
        
        with st.expander("🔧 Refinements Applied", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🚫 Hallucinations Removed:**")
                if refined_result.hallucinations_addressed:
                    for h in refined_result.hallucinations_addressed[:5]:
                        st.markdown(f"""
                        <div style="background: #fed7d7; padding: 8px; margin: 5px 0; border-radius: 5px;">
                            <s>{h['text']}</s><br>
                            <small>Category: {h['category']}</small>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.success("No hallucinations to remove")
            
            with col2:
                st.markdown("**✨ Inferences Added:**")
                if refined_result.inferences_applied:
                    for inf in refined_result.inferences_applied[:5]:
                        confidence_color = {
                            'high': '#48bb78',
                            'medium': '#ed8936',
                            'low': '#f6e05e'
                        }.get(inf.confidence.value, '#718096')
                        
                        st.markdown(f"""
                        <div style="background: #c6f6d5; padding: 8px; margin: 5px 0; border-radius: 5px;">
                            "{inf.inference}"<br>
                            <small style="color: {confidence_color};">
                                Confidence: {inf.confidence.value.upper()} | {inf.category}
                            </small>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No inferences added")
    
    def _display_before_after(self, refined_result: 'RefinedEmailResult') -> None:
        """Display before/after comparison"""
        
        st.markdown("### 📝 Before & After Comparison")
        
        # Use tabs for cleaner comparison
        tab1, tab2, tab3 = st.tabs(["Side by Side", "Original", "Refined"])
        
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**❌ Original (with issues)**")
                # Show COMPLETE email, not truncated
                original_content_escaped = refined_result.original_email.content.replace('\n', '<br>')
                st.markdown(f"""
                <div class="before-box">
                    <strong>Subject:</strong> {refined_result.original_email.subject_line}<br><br>
                    <div style="max-height: 600px; overflow-y: auto; white-space: pre-wrap;">
                        {original_content_escaped}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("**✅ Refined Version**")
                # Show COMPLETE refined email, not truncated
                refined_content_escaped = refined_result.refined_content.replace('\n', '<br>')
                st.markdown(f"""
                <div class="after-box">
                    <strong>Subject:</strong> {refined_result.refined_subject}<br><br>
                    <div style="max-height: 600px; overflow-y: auto; white-space: pre-wrap;">
                        {refined_content_escaped}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        with tab2:
            st.text_area(
                "Original Email",
                refined_result.original_email.content,
                height=300,
                disabled=True
            )
        
        with tab3:
            st.text_area(
                "Refined Email",
                refined_result.refined_content,
                height=300,
                disabled=True
            )
    
    def _display_personalization_dna(self, refined_result: 'RefinedEmailResult') -> None:
        """Display personalization DNA visualization"""
        
        with st.expander("🧬 Personalization DNA", expanded=False):
            st.markdown("**Before:**")
            before_score = int(refined_result.metrics.personalization_score_before * 10)
            self._draw_dna_bar(before_score, 10)
            
            st.markdown("**After:**")
            after_score = int(refined_result.metrics.personalization_score_after * 10)
            self._draw_dna_bar(after_score, 10)
            
            # Show elements
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Original Elements:**")
                for elem in refined_result.original_email.personalization_elements[:5]:
                    st.write(f"• {elem}")
            
            with col2:
                st.markdown("**Refined Elements:**")
                for elem in refined_result.personalization_elements[:5]:
                    st.write(f"• {elem}")
    
    def _draw_dna_bar(self, filled: int, total: int) -> None:
        """Draw a DNA-style progress bar"""
        filled_blocks = "●" * filled
        empty_blocks = "○" * (total - filled)
        
        bar_color = "#48bb78" if filled >= 8 else "#ed8936" if filled >= 5 else "#e53e3e"
        
        st.markdown(f"""
        <div style="font-size: 1.5em; color: {bar_color}; letter-spacing: 2px;">
            {filled_blocks}<span style="color: #cbd5e0;">{empty_blocks}</span>
            <span style="font-size: 0.8em; margin-left: 10px;">{filled}/{total}</span>
        </div>
        """, unsafe_allow_html=True)
    
    def _display_action_buttons(self, refined_result: 'RefinedEmailResult') -> None:
        """Display action buttons"""
        
        st.markdown("---")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("✅ Accept Refined", type="primary", use_container_width=True):
                st.session_state.email_result = self._convert_to_email_result(refined_result)
                st.session_state.refinement_accepted = True
                st.success("Refined email accepted!")
                st.rerun()
        
        with col2:
            if st.button("❌ Keep Original", use_container_width=True):
                st.session_state.refinement_rejected = True
                st.info("Keeping original email")
        
        with col3:
            if st.button("🔄 Refine Again", use_container_width=True):
                st.session_state.refine_again = True
                st.rerun()
        
        with col4:
            # Download refined version
            st.download_button(
                "📥 Download Refined",
                refined_result.refined_content,
                file_name=f"refined_email_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )
    
    def _highlight_issues(self, text: str) -> str:
        """Add highlighting for issues (simplified)"""
        # This would ideally highlight actual hallucinations
        return text
    
    def _highlight_improvements(self, text: str) -> str:
        """Add highlighting for improvements (simplified)"""
        # This would ideally highlight new inferences
        return text
    
    def _convert_to_email_result(self, refined_result: 'RefinedEmailResult') -> Any:
        """Convert refined result back to EmailResult format"""
        from src.core.smart_email_generator import EmailResult
        
        return EmailResult(
            content=refined_result.refined_content,
            subject_line=refined_result.refined_subject,
            word_count=refined_result.metrics.word_count_after,
            character_count=len(refined_result.refined_content),
            personalization_elements=refined_result.personalization_elements,
            tone_achieved=refined_result.original_email.tone_achieved,
            language=refined_result.language,
            generation_method="refined",
            processing_time=refined_result.metrics.processing_time,
            quality_score=refined_result.metrics.quality_score_after
        )
    
    # Required base class methods
    def display_result(self, result: Any, shared_context: Any) -> None:
        """Required by base class - redirects to main display method"""
        self.display_refinement_in_hallucination_tab(result, shared_context)
    
    def validate_result(self, result: Any, shared_context: Any) -> Dict[str, Any]:
        """Validate refinement result"""
        if not hasattr(result, 'metrics'):
            return {
                'is_valid': False,
                'issues': ['Invalid refinement result'],
                'achievements': [],
                'metrics': {}
            }
        
        metrics = result.metrics
        
        validation = {
            'is_valid': True,
            'issues': [],
            'achievements': [],
            'metrics': {
                'hallucinations_removed': metrics.hallucinations_removed,
                'inferences_added': metrics.inferences_added,
                'quality_improvement': metrics.quality_score_after - metrics.quality_score_before,
                'personalization_improvement': metrics.personalization_score_after - metrics.personalization_score_before
            }
        }
        
        # Check achievements
        if metrics.hallucinations_removed > 0:
            validation['achievements'].append(f"Removed {metrics.hallucinations_removed} hallucinations")
        
        if metrics.inferences_added > 0:
            validation['achievements'].append(f"Added {metrics.inferences_added} smart inferences")
        
        if metrics.quality_score_after > metrics.quality_score_before:
            improvement = (metrics.quality_score_after - metrics.quality_score_before) * 100
            validation['achievements'].append(f"Quality improved by {improvement:.0f}%")
        
        if metrics.personalization_score_after > metrics.personalization_score_before:
            improvement = (metrics.personalization_score_after - metrics.personalization_score_before) * 100
            validation['achievements'].append(f"Personalization improved by {improvement:.0f}%")
        
        # Check for issues
        if metrics.quality_score_after < metrics.quality_score_before:
            validation['issues'].append("Quality decreased")
            validation['is_valid'] = False
        
        if metrics.personalization_score_after < metrics.personalization_score_before:
            validation['issues'].append("Personalization decreased")
        
        return validation
    
    def get_download_data(self, result: Any, customer_name: str) -> Tuple[str, str, str]:
        """Get download data for refined email"""
        
        if not hasattr(result, 'refined_content'):
            return "", "", ""
        
        content = f"""REFINED EMAIL
Customer: {customer_name}
Subject: {result.refined_subject}

{result.refined_content}

---
REFINEMENT METRICS:
Hallucinations Removed: {result.metrics.hallucinations_removed}
Inferences Added: {result.metrics.inferences_added}
Quality Score: {result.metrics.quality_score_before:.0%} → {result.metrics.quality_score_after:.0%}
Personalization: {result.metrics.personalization_score_before:.0%} → {result.metrics.personalization_score_after:.0%}
"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"refined_email_{customer_name}_{timestamp}.txt"
        
        return content, filename, "text/plain"

# Convenience function
def display_refinement(refined_result: Any, shared_context: Any = None):
    """Display refinement results"""
    display = RefinementDisplay()
    display.display_refinement_in_hallucination_tab(refined_result, shared_context)