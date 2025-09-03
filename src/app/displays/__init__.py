"""Display Module - Updated with Voice Display"""

# Import type hints
from typing import Any

# Import all display modules
from .email_display import EmailDisplay
from .sms_display import SMSDisplay
from .letter_display import LetterDisplay
from .voice_display import VoiceDisplay, display_voice_note
from .base_display import BaseChannelDisplay

# Import orchestrator display if available
try:
    from .orchestrator_display import OrchestratorDisplay
except ImportError:
    OrchestratorDisplay = None

# Create display instances - FIXED: Added CHANNEL_DISPLAYS
CHANNEL_DISPLAYS = {
    'email': EmailDisplay(),
    'sms': SMSDisplay(),
    'letter': LetterDisplay(),
    'voice': VoiceDisplay()
}

# Add orchestrator if available
if OrchestratorDisplay:
    CHANNEL_DISPLAYS['orchestrator'] = OrchestratorDisplay()

# FIXED: Added get_display_for_channel function
def get_display_for_channel(channel_name: str):
    """Get display instance for a specific channel
    
    Args:
        channel_name: Name of the channel (email, sms, letter, voice, etc.)
        
    Returns:
        Display instance or None if not found
    """
    return CHANNEL_DISPLAYS.get(channel_name.lower())

# Convenience function to get all displays
def get_all_displays():
    """Get instances of all display modules"""
    return CHANNEL_DISPLAYS.copy()

# Function to display channel result using the appropriate display
def display_channel_result(channel_name: str, result: Any, shared_context: Any) -> None:
    """Display result for a specific channel
    
    Args:
        channel_name: Name of the channel
        result: The result object for that channel
        shared_context: The SharedContext from SharedBrain
    """
    display = get_display_for_channel(channel_name)
    if display:
        display.display_result(result, shared_context)
    else:
        print(f"No display found for channel: {channel_name}")

# Export all display classes and functions - FIXED: Added missing exports
__all__ = [
    'EmailDisplay',
    'SMSDisplay', 
    'LetterDisplay',
    'VoiceDisplay',
    'display_voice_note',
    'BaseChannelDisplay',
    'OrchestratorDisplay',
    'get_all_displays',
    'CHANNEL_DISPLAYS',  # FIXED: Added
    'get_display_for_channel',  # FIXED: Added
    'display_channel_result'  # FIXED: Added
]