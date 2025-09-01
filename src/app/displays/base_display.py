"""
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
