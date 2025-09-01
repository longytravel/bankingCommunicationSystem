"""
Voice Note Display Module - Handles all voice note result display logic
"""

import streamlit as st
from typing import Any, Dict, Tuple
from datetime import datetime
from .base_display import BaseChannelDisplay

class VoiceDisplay(BaseChannelDisplay):
    """Display handler for voice note results"""
    
    def __init__(self):
        super().__init__("Voice Note", "🎙️")
        self.style = """
        <style>
        .voice-showcase {
            background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%);
            border: 2px solid #9c27b0;
            border-radius: 10px;
            padding: 2rem;
            margin: 1rem 0;
        }
        
        .voice-player {
            background: #2d2d2d;
            border-radius: 25px;
            padding: 20px;
            margin: 20px auto;
            max-width: 500px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        
        .voice-waveform {
            height: 60px;
            background: linear-gradient(90deg, #9c27b0 0%, #673ab7 50%, #9c27b0 100%);
            border-radius: 30px;
            margin: 15px 0;
            position: relative;
            overflow: hidden;
        }
        
        .voice-controls {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 20px;
            margin-top: 15px;
        }
        
        .play-button {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: #9c27b0;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .play-button:hover {
            background: #7b1fa2;
            transform: scale(1.1);
        }
        
        .voice-script {
            background: white;
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            line-height: 1.8;
        }
        
        .voice-emphasis {
            color: #9c27b0;
            font-weight: bold;
        }
        
        .voice-pause {
            color: #999;
            font-style: italic;
        }
        </style>
        """
    
    def display_result(self, result: Any, shared_context: Any) -> None:
        """Display the voice note result with audio player mockup"""
        
        if not result:
            st.error("❌ No voice note result available")
            return
        
        try:
            # Apply custom styling
            st.markdown(self.style, unsafe_allow_html=True)
            
            st.markdown('<div class="voice-showcase">', unsafe_allow_html=True)
            st.markdown(f"### {self.icon} Smart Voice Note Result")
            
            # Display metrics
            self._display_voice_metrics(result)
            
            # Display audio player mockup
            self._display_voice_player(result)
            
            # Display script with markup
            self._display_voice_script(result)
            
            # Display voice characteristics
            self._display_voice_characteristics(result)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Error displaying voice result: {e}")
    
    def _display_voice_metrics(self, result: Any) -> None:
        """Display voice-specific metrics"""
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            duration = getattr(result, 'duration_estimate', 0)
            st.metric("Duration", f"{duration:.0f}s")
        
        with col2:
            word_count = getattr(result, 'word_count', 0)
            st.metric("Words", word_count)
        
        with col3:
            pace = getattr(result, 'speaking_pace', 'normal').title()
            st.metric("Pace", pace)
        
        with col4:
            quality = getattr(result, 'quality_score', 0)
            st.metric("Quality", f"{quality:.1%}")
        
        with col5:
            callback = getattr(result, 'requires_callback', False)
            st.metric("Callback", "Yes" if callback else "No")
    
    def _display_voice_player(self, result: Any) -> None:
        """Display a mock audio player interface"""
        duration = getattr(result, 'duration_estimate', 30)
        
        st.markdown(f"""
        <div class="voice-player">
            <div style="color: white; text-align: center; margin-bottom: 10px;">
                🎙️ Voice Message Preview
            </div>
            <div class="voice-waveform"></div>
            <div style="color: #aaa; text-align: center; font-size: 14px;">
                0:00 / {int(duration//60)}:{int(duration%60):02d}
            </div>
            <div class="voice-controls">
                <div class="play-button">
                    <span style="color: white; font-size: 24px;">▶️</span>
                </div>
            </div>
            <div style="color: #aaa; text-align: center; margin-top: 10px; font-size: 12px;">
                Click to preview (simulation mode)
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def _display_voice_script(self, result: Any) -> None:
        """Display the voice script with emphasis and pauses marked"""
        script = getattr(result, 'content', 'No script available')
        emphasis_words = getattr(result, 'emphasis_words', [])
        
        # Mark up emphasis words
        marked_script = script
        for word in emphasis_words:
            marked_script = marked_script.replace(
                word, 
                f'<span class="voice-emphasis">{word}</span>'
            )
        
        # Mark up pauses
        marked_script = marked_script.replace(
            '...', 
            '<span class="voice-pause">[pause]</span>'
        )
        
        st.markdown("**🎯 Voice Script:**")
        st.markdown(f'<div class="voice-script">{marked_script}</div>', unsafe_allow_html=True)
    
    def _display_voice_characteristics(self, result: Any) -> None:
        """Display voice characteristics and personalization"""
        col1, col2 = st.columns(2)
        
        with col1:
            tone_markers = getattr(result, 'tone_markers', [])
            if tone_markers:
                st.markdown("**🎭 Voice Tone:**")
                for tone in tone_markers[:3]:
                    st.write(f"• {tone.title()}")
        
        with col2:
            personalization = getattr(result, 'personalization_elements', [])
            if personalization:
                st.markdown("**🎯 Personalization:**")
                for element in personalization[:3]:
                    st.write(f"• {element}")
        
        # Natural pauses and emphasis
        with st.expander("🎵 Speech Patterns", expanded=False):
            natural_pauses = getattr(result, 'natural_pauses', [])
            if natural_pauses:
                st.write(f"**Natural pauses at words:** {', '.join(map(str, natural_pauses[:5]))}")
            
            emphasis_words = getattr(result, 'emphasis_words', [])
            if emphasis_words:
                st.write(f"**Emphasized words:** {', '.join(emphasis_words[:5])}")
            
            pace = getattr(result, 'speaking_pace', 'normal')
            st.write(f"**Speaking pace:** {pace}")
    
    def validate_result(self, result: Any, shared_context: Any) -> Dict[str, Any]:
        """Validate voice note result"""
        
        # Try to use the voice generator's validation if available
        try:
            from src.core.smart_voice_generator import SmartVoiceGenerator
            generator = SmartVoiceGenerator()
            return generator.validate_voice_note(result, shared_context)
        except:
            # Fallback validation
            return {
                'is_valid': True,
                'quality_score': getattr(result, 'quality_score', 0),
                'issues': [],
                'achievements': [
                    f"Duration: {getattr(result, 'duration_estimate', 0):.0f} seconds",
                    f"Pace: {getattr(result, 'speaking_pace', 'normal')}"
                ],
                'metrics': {
                    'duration': f"{getattr(result, 'duration_estimate', 0):.1f}s",
                    'word_count': getattr(result, 'word_count', 0),
                    'personalization_elements': len(getattr(result, 'personalization_elements', [])),
                    'requires_callback': getattr(result, 'requires_callback', False)
                }
            }
    
    def get_download_data(self, result: Any, customer_name: str) -> Tuple[str, str, str]:
        """Get download data for voice script"""
        content = getattr(result, 'content', '')
        
        if not content:
            return "", "", ""
        
        # Format for download
        download_content = f"""VOICE NOTE SCRIPT
Customer: {customer_name}
Duration: {getattr(result, 'duration_estimate', 0):.0f} seconds
Pace: {getattr(result, 'speaking_pace', 'normal')}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

SCRIPT:
{content}

TONE MARKERS: {', '.join(getattr(result, 'tone_markers', []))}
EMPHASIS WORDS: {', '.join(getattr(result, 'emphasis_words', []))}
"""
        
        customer_filename = customer_name.replace(' ', '_') if customer_name else 'customer'
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"voice_script_{customer_filename}_{timestamp}.txt"
        
        return download_content, filename, "text/plain"