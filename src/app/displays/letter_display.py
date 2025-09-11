"""
Letter Display Module - Handles all letter result display logic
FIXED VERSION - Corrects HTML structure and text sizing
"""

import streamlit as st
from typing import Any, Dict, Tuple
from datetime import datetime
from .base_display import BaseChannelDisplay

class LetterDisplay(BaseChannelDisplay):
    """Display handler for letter results"""
    
    def __init__(self):
        super().__init__("Letter", "📮")
        self.style = """
        <style>
        .letter-preview {
            background: white;
            border: 2px solid #006A4D;
            border-radius: 10px;
            padding: 30px;
            margin: 20px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .letter-content {
            font-family: 'Arial', sans-serif;
            font-size: 12px;  /* Fixed: Reduced from 11pt to 12px for better control */
            line-height: 1.6;
            white-space: pre-wrap;
            word-wrap: break-word;
            color: #333;
        }
        
        .letter-header {
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #006A4D;
        }
        
        .letter-metrics {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
        }
        </style>
        """
    
    def display_result(self, result: Any, shared_context: Any) -> None:
        """Display the letter result with proper formatting"""
        
        if not result:
            st.error("❌ No letter result available")
            return
        
        try:
            # Apply custom styling
            st.markdown(self.style, unsafe_allow_html=True)
            
            # Header section
            st.markdown('<div class="letter-header">', unsafe_allow_html=True)
            st.markdown(f"### {self.icon} Smart Letter Result")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Display metrics
            self._display_letter_metrics(result)
            
            # Display letter content
            st.markdown("**📄 Letter Preview:**")
            self._display_letter_content(result)
            
            # Display personalization details
            self._display_personalization_details(result)
            
            # Additional letter-specific information
            self._display_letter_specifics(result)
            
        except Exception as e:
            st.error(f"Error displaying letter result: {e}")
    
    def _display_letter_metrics(self, result: Any) -> None:
        """Display letter-specific metrics"""
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            quality_score = getattr(result, 'quality_score', 0)
            st.metric("Quality", f"{quality_score:.1%}")
        
        with col2:
            word_count = getattr(result, 'word_count', 0)
            st.metric("Words", f"{word_count:,}")
        
        with col3:
            page_count = getattr(result, 'page_count', 1)
            st.metric("Pages", page_count)
        
        with col4:
            formality = getattr(result, 'formality_level', 'unknown')
            st.metric("Formality", formality.replace('_', ' ').title())
        
        with col5:
            processing_time = getattr(result, 'processing_time', 0)
            st.metric("Time", f"{processing_time:.2f}s")
    
    def _display_letter_content(self, result: Any) -> None:
        """Display the letter content in a formatted preview"""
        content = getattr(result, 'content', 'No content available')
        
        # FIXED: Clean any stray HTML tags from content
        content = self._clean_html_artifacts(content)
        
        # FIXED: Proper HTML structure with escaped content
        import html
        escaped_content = html.escape(content)
        
        # Create a nice letter preview with proper HTML structure
        st.markdown(f'''
        <div class="letter-preview">
            <div class="letter-content">{escaped_content}</div>
        </div>
        ''', unsafe_allow_html=True)
    
    def _clean_html_artifacts(self, content: str) -> str:
        """Remove any stray HTML tags from content"""
        # Remove common HTML artifacts that might appear
        html_tags = ['</pre>', '</div>', '<pre>', '<div>', '</p>', '<p>', 
                     '</span>', '<span>', '```', '```html', '```css']
        
        cleaned_content = content
        for tag in html_tags:
            cleaned_content = cleaned_content.replace(tag, '')
        
        return cleaned_content.strip()
    
    def _display_personalization_details(self, result: Any) -> None:
        """Display personalization elements applied"""
        personalization_elements = getattr(result, 'personalization_elements', [])
        
        if personalization_elements:
            with st.expander("🎯 Personalization Elements Applied", expanded=False):
                for i, element in enumerate(personalization_elements, 1):
                    st.write(f"{i}. {element}")
    
    def _display_letter_specifics(self, result: Any) -> None:
        """Display letter-specific information"""
        col1, col2 = st.columns(2)
        
        with col1:
            includes_envelope = getattr(result, 'includes_return_envelope', False)
            if includes_envelope:
                st.info("✉️ Includes return envelope")
        
        with col2:
            tone = getattr(result, 'tone_achieved', 'unknown')
            st.info(f"💬 Tone: {tone}")
    
    def validate_result(self, result: Any, shared_context: Any) -> Dict[str, Any]:
        """Validate letter result"""
        
        # Try to use the letter generator's validation if available
        try:
            from src.core.smart_letter_generator import SmartLetterGenerator
            generator = SmartLetterGenerator()
            return generator.validate_letter(result, shared_context)
        except:
            # Fallback validation
            return {
                'is_valid': True,
                'quality_score': getattr(result, 'quality_score', 0),
                'issues': [],
                'achievements': [
                    f"Generated {getattr(result, 'page_count', 1)} page letter",
                    f"Formality: {getattr(result, 'formality_level', 'professional')}"
                ],
                'metrics': {
                    'word_count': getattr(result, 'word_count', 0),
                    'page_count': getattr(result, 'page_count', 1),
                    'personalization_elements': len(getattr(result, 'personalization_elements', []))
                }
            }
    
    def get_download_data(self, result: Any, customer_name: str) -> Tuple[str, str, str]:
        """Get download data for letter"""
        content = getattr(result, 'content', '')
        
        # Clean HTML artifacts before download
        content = self._clean_html_artifacts(content)
        
        if not content:
            return "", "", ""
        
        # Format customer name for filename
        customer_filename = customer_name.replace(' ', '_') if customer_name else 'customer'
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        filename = f"letter_{customer_filename}_{timestamp}.txt"
        
        return content, filename, "text/plain"