"""
SMS Display Module - Handles all SMS result display logic
"""

import streamlit as st
from typing import Any, Dict, Tuple
from datetime import datetime
from .base_display import BaseChannelDisplay

class SMSDisplay(BaseChannelDisplay):
    """Display handler for SMS results"""
    
    def __init__(self):
        super().__init__("SMS", "📱")
        self.style = """
        <style>
        .smart-sms-showcase {
            background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
            border: 2px solid #4caf50;
            border-radius: 10px;
            padding: 2rem;
            margin: 1rem 0;
        }
        
        .sms-preview {
            background: #f0f0f0;
            border: 2px solid #333;
            border-radius: 20px;
            padding: 20px;
            max-width: 350px;
            margin: 20px auto;
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        .sms-bubble {
            background: white;
            border-radius: 15px;
            padding: 12px;
            margin-bottom: 10px;
        }
        
        .sms-meta {
            text-align: center;
            color: #666;
            font-size: 12px;
            margin-top: 10px;
        }
        </style>
        """
    
    def display_result(self, result: Any, shared_context: Any) -> None:
        """Display the SMS result with phone-like preview"""
        
        if not result:
            st.error("❌ No SMS result available")
            return
        
        try:
            # Apply custom styling
            st.markdown(self.style, unsafe_allow_html=True)
            
            st.markdown('<div class="smart-sms-showcase">', unsafe_allow_html=True)
            st.markdown(f"### {self.icon} Smart SMS Result")
            
            # Display metrics
            self._display_sms_metrics(result)
            
            # SMS preview
            st.markdown("**📱 SMS Preview:**")
            self._display_sms_preview(result)
            
            # Additional details
            self._display_sms_details(result)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Error displaying SMS result: {e}")
    
    def _display_sms_metrics(self, result: Any) -> None:
        """Display SMS-specific metrics"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            quality_score = getattr(result, 'quality_score', 0)
            st.metric("Quality Score", f"{quality_score:.1%}")
        
        with col2:
            char_count = getattr(result, 'character_count', 0)
            st.metric("Characters", f"{char_count}/400")
        
        with col3:
            segments = getattr(result, 'segments', 1)
            st.metric("Segments", segments)
        
        with col4:
            processing_time = getattr(result, 'processing_time', 0)
            st.metric("Time", f"{processing_time:.2f}s")
    
    def _display_sms_preview(self, result: Any) -> None:
        """Display SMS in phone-like preview"""
        content = getattr(result, 'content', 'No content available')
        char_count = getattr(result, 'character_count', 0)
        segments = getattr(result, 'segments', 1)
        
        st.markdown(f'''
        <div class="sms-preview">
            <div class="sms-bubble">
                {content}
            </div>
            <div class="sms-meta">
                {char_count} characters • {segments} segment(s)
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    def _display_sms_details(self, result: Any) -> None:
        """Display additional SMS details"""
        col1, col2 = st.columns(2)
        
        with col1:
            critical_points = getattr(result, 'critical_points_included', [])
            if critical_points:
                st.markdown("**✅ Critical Points Included:**")
                for point in critical_points:
                    st.write(f"• {point}")
        
        with col2:
            abbreviations = getattr(result, 'abbreviations_used', {})
            if abbreviations:
                st.markdown("**📝 Abbreviations Used:**")
                for full, abbrev in abbreviations.items():
                    st.write(f"• {full} → {abbrev}")
        
        # Personalization elements
        personalization_elements = getattr(result, 'personalization_elements', [])
        if personalization_elements:
            with st.expander("🎯 SMS Personalization Applied", expanded=False):
                for element in personalization_elements:
                    st.write(f"• {element}")
    
    def validate_result(self, result: Any, shared_context: Any) -> Dict[str, Any]:
        """Validate SMS result"""
        
        # Try to use the SMS generator's validation
        try:
            from src.core.smart_sms_generator import SmartSMSGenerator
            generator = SmartSMSGenerator()
            return generator.validate_sms(result, shared_context)
        except:
            # Fallback validation
            return {
                'is_valid': True,
                'quality_score': getattr(result, 'quality_score', 0),
                'issues': [],
                'achievements': [],
                'metrics': {
                    'character_count': getattr(result, 'character_count', 0),
                    'segments': getattr(result, 'segments', 1),
                    'critical_points': len(getattr(result, 'critical_points_included', [])),
                    'personalization': len(getattr(result, 'personalization_elements', []))
                }
            }
    
    def get_download_data(self, result: Any, customer_name: str) -> Tuple[str, str, str]:
        """Get download data for SMS"""
        content = getattr(result, 'content', '')
        
        if not content:
            return "", "", ""
        
        customer_filename = customer_name.replace(' ', '_') if customer_name else 'customer'
        
        return content, f"sms_{customer_filename}.txt", "text/plain"