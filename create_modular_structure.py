"""
Setup script to create the modular app structure
Run this from your project root directory
"""

import os
from pathlib import Path

def create_file(filepath, content):
    """Create a file with the given content"""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Created: {filepath}")

# Define all the file contents
files_to_create = {
    'src/app/__init__.py': '''"""
Modular Streamlit App Package
Organizes the personalization app into maintainable modules
"""

from .displays import CHANNEL_DISPLAYS, get_display_for_channel, display_channel_result

__version__ = "2.0.0"

__all__ = [
    'CHANNEL_DISPLAYS',
    'get_display_for_channel', 
    'display_channel_result'
]
''',

    'src/app/displays/__init__.py': '''"""
Display Module Registry - Auto-registers all channel displays
"""

from typing import Dict, Any, Optional
from .base_display import BaseChannelDisplay
from .letter_display import LetterDisplay

# Import other displays as they're created
try:
    from .email_display import EmailDisplay
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False

try:
    from .sms_display import SMSDisplay
    SMS_AVAILABLE = True
except ImportError:
    SMS_AVAILABLE = False

# Registry of all available channel displays
CHANNEL_DISPLAYS: Dict[str, BaseChannelDisplay] = {
    'letter': LetterDisplay(),
}

# Add other displays if available
if EMAIL_AVAILABLE:
    CHANNEL_DISPLAYS['email'] = EmailDisplay()

if SMS_AVAILABLE:
    CHANNEL_DISPLAYS['sms'] = SMSDisplay()

def get_display_for_channel(channel_name: str) -> Optional[BaseChannelDisplay]:
    """
    Get the display handler for a specific channel
    
    Args:
        channel_name: Name of the channel (email, sms, letter, etc.)
        
    Returns:
        Display handler or None if not found
    """
    return CHANNEL_DISPLAYS.get(channel_name.lower())

def display_channel_result(channel_name: str, result: Any, shared_context: Any) -> bool:
    """
    Display result for a specific channel
    
    Args:
        channel_name: Name of the channel
        result: Channel-specific result object
        shared_context: SharedContext from SharedBrain
        
    Returns:
        True if displayed successfully, False otherwise
    """
    display = get_display_for_channel(channel_name)
    
    if display:
        display.display_result(result, shared_context)
        return True
    
    return False

def get_available_channels() -> list:
    """Get list of available channel names"""
    return list(CHANNEL_DISPLAYS.keys())
''',

    'src/app/displays/base_display.py': '''"""
Base Display Class - Abstract interface for all channel displays
All channel displays must inherit from this
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple
import streamlit as st

class BaseChannelDisplay(ABC):
    """Abstract base class for all channel display modules"""
    
    def __init__(self, channel_name: str, icon: str):
        self.channel_name = channel_name
        self.icon = icon
        self.enabled = True
    
    @abstractmethod
    def display_result(self, result: Any, shared_context: Any) -> None:
        """
        Display the channel's result in the UI
        
        Args:
            result: The channel-specific result object (EmailResult, SMSResult, etc.)
            shared_context: The SharedContext from SharedBrain
        """
        pass
    
    @abstractmethod
    def validate_result(self, result: Any, shared_context: Any) -> Dict[str, Any]:
        """
        Validate the channel's result
        
        Args:
            result: The channel-specific result object
            shared_context: The SharedContext from SharedBrain
            
        Returns:
            Validation dictionary with 'is_valid', 'issues', 'achievements', etc.
        """
        pass
    
    @abstractmethod
    def get_download_data(self, result: Any, customer_name: str) -> Tuple[str, str, str]:
        """
        Get download data for the channel
        
        Args:
            result: The channel-specific result object
            customer_name: Customer name for filename
            
        Returns:
            Tuple of (content, filename, mime_type)
        """
        pass
    
    def display_metrics(self, result: Any) -> None:
        """
        Display common metrics - can be overridden
        
        Args:
            result: The channel-specific result object
        """
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            quality_score = getattr(result, 'quality_score', 0)
            st.metric("Quality Score", f"{quality_score:.1%}")
        
        with col2:
            processing_time = getattr(result, 'processing_time', 0)
            st.metric("Processing Time", f"{processing_time:.2f}s")
        
        with col3:
            method = getattr(result, 'generation_method', 'unknown')
            st.metric("Method", method.replace('_', ' ').title())
        
        with col4:
            language = getattr(result, 'language', 'English')
            st.metric("Language", language)
    
    def display_validation(self, validation: Dict[str, Any]) -> None:
        """
        Display validation results - common pattern
        
        Args:
            validation: Validation dictionary
        """
        with st.expander(f"📋 {self.channel_name} Validation", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**✅ Achievements:**")
                achievements = validation.get('achievements', [])
                if achievements:
                    for achievement in achievements:
                        st.write(f"• {achievement}")
                else:
                    st.write("• Processing complete")
            
            with col2:
                st.write("**⚠️ Issues:**")
                issues = validation.get('issues', [])
                if issues:
                    for issue in issues:
                        st.write(f"• {issue}")
                else:
                    st.write("• No issues detected")
            
            # Show metrics if available
            if 'metrics' in validation:
                st.write("**📊 Metrics:**")
                metrics = validation['metrics']
                for key, value in metrics.items():
                    if value is not None:
                        st.write(f"• {key.replace('_', ' ').title()}: {value}")
    
    def create_download_button(self, result: Any, customer_name: str) -> None:
        """
        Create download button for the channel
        
        Args:
            result: The channel-specific result object
            customer_name: Customer name for filename
        """
        try:
            content, filename, mime_type = self.get_download_data(result, customer_name)
            
            if content:
                st.download_button(
                    f"{self.icon} Download {self.channel_name}",
                    content,
                    file_name=filename,
                    mime=mime_type,
                    use_container_width=True
                )
        except Exception as e:
            st.error(f"Download error: {e}")
''',

    'src/app/displays/letter_display.py': '''"""
Letter Display Module - Handles all letter result display logic
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
            font-family: 'Arial', sans-serif;
            font-size: 11pt;
            line-height: 1.5;
            min-height: 400px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
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
        
        # Create a nice letter preview
        st.markdown(f\'\'\'
        <div class="letter-preview">
            <pre style="white-space: pre-wrap; font-family: Arial, sans-serif; font-size: 11pt; line-height: 1.6;">
{content}
            </pre>
        </div>
        \'\'\', unsafe_allow_html=True)
    
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
        
        if not content:
            return "", "", ""
        
        # Format customer name for filename
        customer_filename = customer_name.replace(' ', '_') if customer_name else 'customer'
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        filename = f"letter_{customer_filename}_{timestamp}.txt"
        
        return content, filename, "text/plain"
''',

    'src/app/utils/__init__.py': '"""Utility functions for the modular app"""',
    
    'src/app/utils/safe_access.py': '''"""
Safe Access Utilities - Safely access nested attributes and dictionary keys
"""

from typing import Any, Optional

def safe_get_attribute(obj: Any, attr_path: str, default: Any = None) -> Any:
    """
    Safely get nested attributes from objects
    
    Args:
        obj: Object to get attribute from
        attr_path: Dot-separated path to attribute (e.g., 'customer.name.first')
        default: Default value if attribute not found
        
    Returns:
        Attribute value or default
    """
    try:
        attrs = attr_path.split('.')
        for attr in attrs:
            if obj is None:
                return default
            
            # Handle both objects and dictionaries
            if isinstance(obj, dict):
                obj = obj.get(attr, None)
            else:
                obj = getattr(obj, attr, None)
                
        return obj if obj is not None else default
    except:
        return default

def safe_get_dict_value(data: dict, key_path: str, default: Any = None) -> Any:
    """
    Safely get nested dictionary values
    
    Args:
        data: Dictionary to get value from
        key_path: Dot-separated path to key
        default: Default value if key not found
        
    Returns:
        Dictionary value or default
    """
    try:
        keys = key_path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
                
        return value
    except:
        return default
''',

    'src/app/components/__init__.py': '"""Reusable UI components for the modular app"""',
    
    'src/app/processors/__init__.py': '"""Business logic processors for the modular app"""',
    
    'src/app/styles/__init__.py': '"""Styling and themes for the modular app"""',
}

def main():
    """Create all the files and directories"""
    print("🚀 Creating modular app structure...")
    print("=" * 50)
    
    # Create each file
    for filepath, content in files_to_create.items():
        create_file(filepath, content)
    
    print("=" * 50)
    print("✨ Modular app structure created successfully!")
    print("\nNext steps:")
    print("1. Review the created files")
    print("2. Test the letter display module")
    print("3. We'll create email and SMS display modules next")
    print("4. Then refactor the main app to use these modules")

if __name__ == "__main__":
    main()