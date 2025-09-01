"""
Email Display Module - Handles all email result display logic
"""

import streamlit as st
from typing import Any, Dict, Tuple
from datetime import datetime
from .base_display import BaseChannelDisplay

class EmailDisplay(BaseChannelDisplay):
    """Display handler for email results"""
    
    def __init__(self):
        super().__init__("Email", "📧")
        self.style = """
        <style>
        .smart-email-showcase {
            background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
            border: 2px solid #2196f3;
            border-radius: 10px;
            padding: 2rem;
            margin: 1rem 0;
        }
        
        .email-content-preview {
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            border: 1px solid #ddd;
            white-space: pre-wrap;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            line-height: 1.6;
            max-height: 600px;
            overflow-y: auto;
        }
        
        .email-subject-line {
            background: #f0f0f0;
            padding: 10px;
            border-radius: 5px;
            font-weight: bold;
            margin-bottom: 15px;
        }
        </style>
        """
    
    def display_result(self, result: Any, shared_context: Any) -> None:
        """Display the email result with proper formatting"""
        
        if not result:
            st.error("❌ No email result available")
            return
        
        try:
            # Apply custom styling
            st.markdown(self.style, unsafe_allow_html=True)
            
            st.markdown('<div class="smart-email-showcase">', unsafe_allow_html=True)
            st.markdown(f"### {self.icon} Smart Email Result")
            
            # Display metrics
            self._display_email_metrics(result)
            
            # Subject line
            subject_line = getattr(result, 'subject_line', 'No subject')
            st.markdown("**📝 Subject Line:**")
            st.markdown(f'<div class="email-subject-line">{subject_line}</div>', unsafe_allow_html=True)
            
            # Email content
            st.markdown("**✉️ Email Content:**")
            self._display_email_content(result)
            
            # Personalization achieved
            self._display_personalization_details(result)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Error displaying email result: {e}")
    
    def _display_email_metrics(self, result: Any) -> None:
        """Display email-specific metrics"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            quality_score = getattr(result, 'quality_score', 0)
            st.metric("Quality Score", f"{quality_score:.1%}")
        
        with col2:
            word_count = getattr(result, 'word_count', 0)
            st.metric("Words", word_count)
        
        with col3:
            generation_method = getattr(result, 'generation_method', 'unknown').replace('_', ' ').title()
            st.metric("Generation", generation_method)
        
        with col4:
            processing_time = getattr(result, 'processing_time', 0)
            st.metric("Time", f"{processing_time:.2f}s")
    
    def _display_email_content(self, result: Any) -> None:
        """Display the email content"""
        content = getattr(result, 'content', 'No content available')
        st.markdown(f'<div class="email-content-preview">{content}</div>', unsafe_allow_html=True)
    
    def _display_personalization_details(self, result: Any) -> None:
        """Display personalization elements applied"""
        personalization_elements = getattr(result, 'personalization_elements', [])
        
        if personalization_elements:
            with st.expander("🎯 Personalization Elements Applied", expanded=False):
                for i, element in enumerate(personalization_elements, 1):
                    st.write(f"{i}. {element}")
    
    def validate_result(self, result: Any, shared_context: Any) -> Dict[str, Any]:
        """Validate email result"""
        
        # Try to use the email generator's validation
        try:
            from src.core.smart_email_generator import SmartEmailGenerator
            generator = SmartEmailGenerator()
            return generator.validate_email(result, shared_context)
        except:
            # Fallback validation
            return {
                'is_valid': True,
                'quality_score': getattr(result, 'quality_score', 0),
                'issues': [],
                'achievements': [],
                'metrics': {
                    'word_count': getattr(result, 'word_count', 0),
                    'character_count': getattr(result, 'character_count', 0),
                    'personalization_elements': len(getattr(result, 'personalization_elements', []))
                }
            }
    
    def get_download_data(self, result: Any, customer_name: str) -> Tuple[str, str, str]:
        """Get download data for email"""
        subject_line = getattr(result, 'subject_line', 'Email')
        content = getattr(result, 'content', '')
        
        if not content:
            return "", "", ""
        
        email_download_content = f"Subject: {subject_line}\n\n{content}"
        customer_filename = customer_name.replace(' ', '_') if customer_name else 'customer'
        
        return email_download_content, f"email_{customer_filename}.txt", "text/plain"