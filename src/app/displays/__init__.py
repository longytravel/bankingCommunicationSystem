"""Display Module - Updated with Voice Display"""

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

# Convenience function to get all displays
def get_all_displays():
    """Get instances of all display modules"""
    displays = {
        'email': EmailDisplay(),
        'sms': SMSDisplay(),
        'letter': LetterDisplay(),
        'voice': VoiceDisplay()
    }
    
    if OrchestratorDisplay:
        displays['orchestrator'] = OrchestratorDisplay()
    
    return displays

# Export all display classes
__all__ = [
    'EmailDisplay',
    'SMSDisplay', 
    'LetterDisplay',
    'VoiceDisplay',
    'display_voice_note',
    'BaseChannelDisplay',
    'OrchestratorDisplay',
    'get_all_displays'
]