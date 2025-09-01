"""
Display Module Registry - Auto-registers all channel displays
"""

from typing import Dict, Any, Optional
from .base_display import BaseChannelDisplay
from .letter_display import LetterDisplay
from .email_display import EmailDisplay
from .sms_display import SMSDisplay
from .voice_display import VoiceDisplay

# Registry of all available channel displays
CHANNEL_DISPLAYS: Dict[str, BaseChannelDisplay] = {
    'email': EmailDisplay(),
    'sms': SMSDisplay(),
    'letter': LetterDisplay(),
    'voice': VoiceDisplay(),
}

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

def validate_channel_result(channel_name: str, result: Any, shared_context: Any) -> Dict[str, Any]:
    """
    Validate result for a specific channel
    
    Args:
        channel_name: Name of the channel
        result: Channel-specific result object
        shared_context: SharedContext from SharedBrain
        
    Returns:
        Validation dictionary
    """
    display = get_display_for_channel(channel_name)
    
    if display:
        return display.validate_result(result, shared_context)
    
    return {'is_valid': False, 'error': 'Display handler not found'}

def get_available_channels() -> list:
    """Get list of available channel names"""
    return list(CHANNEL_DISPLAYS.keys())