"""
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
