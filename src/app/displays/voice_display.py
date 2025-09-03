"""
Voice Note Display Module - Shows voice notes with audio player
Integrates with Streamlit to display and play voice notes
"""

import streamlit as st
from pathlib import Path
from typing import Dict, Any, Optional
import base64
from datetime import datetime

# Import the base display class - FIXED import path
from .base_display import BaseChannelDisplay

# Import voice result type
try:
    from src.core.voice_note_generator_enhanced import VoiceResult
except ImportError:
    from dataclasses import dataclass
    from typing import List
    
    @dataclass
    class VoiceResult:
        content: str
        duration_estimate: float
        word_count: int
        speaking_pace: str
        tone_markers: List[str]
        personalization_elements: List[str]
        emphasis_words: List[str]
        language: str
        generation_method: str
        processing_time: float
        quality_score: float
        audio_file_path: Optional[str] = None
        audio_format: str = "mp3"
        tts_engine_used: str = "none"

class VoiceDisplay(BaseChannelDisplay):
    """Display component for voice notes with audio player"""
    
    def __init__(self):
        # FIXED: Properly initialize base class with channel_name and icon
        super().__init__(channel_name="Voice Note", icon="🎙️")
    
    def display_result(self, result: Any, shared_context: Any) -> None:
        """Override base class method to display voice result"""
        self.display(result, shared_context)
    
    def display(self, result: VoiceResult, shared_context: Any, validation: Optional[Dict] = None):
        """Display voice note with audio player"""
        
        # Header using the icon from base class
        self.display_header(f"{self.icon} Voice Note", self.icon)
        
        # Status badges
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if result.generation_method == 'disabled':
                st.error("❌ Disabled")
            elif result.audio_file_path:
                st.success("✅ Generated")
            else:
                st.warning("⚠️ Script Only")
        
        with col2:
            st.info(f"🌍 {result.language}")
        
        with col3:
            if result.duration_estimate > 0:
                st.metric("Duration", f"{result.duration_estimate:.1f}s")
        
        with col4:
            if result.quality_score > 0:
                quality_pct = result.quality_score * 100
                if quality_pct >= 80:
                    st.success(f"Quality: {quality_pct:.0f}%")
                elif quality_pct >= 60:
                    st.warning(f"Quality: {quality_pct:.0f}%")
                else:
                    st.error(f"Quality: {quality_pct:.0f}%")
        
        if result.generation_method == 'disabled':
            st.info("Voice note disabled by communication rules")
            return
        
        # Audio Player Section
        if result.audio_file_path:
            st.markdown("### 🎵 Audio Player")
            
            # Check if file exists
            audio_path = Path(result.audio_file_path)
            if audio_path.exists():
                # Create audio player
                try:
                    # Read audio file
                    with open(audio_path, 'rb') as audio_file:
                        audio_bytes = audio_file.read()
                    
                    # Display audio player
                    st.audio(audio_bytes, format=f'audio/{result.audio_format}')
                    
                    # Download button
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            label="📥 Download Audio",
                            data=audio_bytes,
                            file_name=audio_path.name,
                            mime=f'audio/{result.audio_format}'
                        )
                    
                    with col2:
                        st.info(f"🎙️ Engine: {result.tts_engine_used}")
                    
                except Exception as e:
                    st.error(f"Error loading audio: {e}")
            else:
                st.warning(f"Audio file not found: {audio_path}")
                st.info("Showing script only")
        else:
            st.info("🔇 No audio generated - Showing script only")
        
        # Script Section
        st.markdown("### 📝 Voice Script")
        
        # Language indicator
        if result.language != 'English':
            st.info(f"Script in {result.language}")
        
        # Display script with formatting
        if result.content:
            # Create a nice box for the script
            script_html = f"""
            <div style="
                background-color: #f0f2f6;
                border-left: 4px solid #1f77b4;
                padding: 20px;
                border-radius: 5px;
                margin: 10px 0;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 16px;
                line-height: 1.6;
            ">
                <div style="color: #333; white-space: pre-wrap;">{self._format_script(result.content, result.emphasis_words)}</div>
            </div>
            """
            st.markdown(script_html, unsafe_allow_html=True)
            
            # Word count and reading time
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📊 Word Count", result.word_count)
            with col2:
                st.metric("⏱️ Speaking Pace", result.speaking_pace.title())
            with col3:
                st.metric("🎯 Est. Duration", f"{result.duration_estimate:.1f}s")
        else:
            st.warning("No script generated")
        
        # Technical Details (collapsible)
        with st.expander("🔧 Technical Details"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Generation Info:**")
                st.text(f"Method: {result.generation_method}")
                st.text(f"Processing: {result.processing_time:.2f}s")
                if result.tts_engine_used != "none":
                    st.text(f"TTS: {result.tts_engine_used}")
            
            with col2:
                st.markdown("**Content Analysis:**")
                if result.tone_markers:
                    st.text(f"Tone: {', '.join(result.tone_markers)}")
                if result.emphasis_words:
                    st.text(f"Emphasis: {', '.join(result.emphasis_words[:5])}")
        
        # Personalization Elements
        if result.personalization_elements:
            with st.expander(f"✨ Personalization ({len(result.personalization_elements)} elements)"):
                for element in result.personalization_elements:
                    st.write(f"• {element}")
        
        # Validation Results
        if validation:
            with st.expander("✅ Validation Results"):
                if validation.get('is_valid'):
                    st.success("Voice note passed all validation checks")
                else:
                    st.error("Voice note has validation issues")
                
                if validation.get('achievements'):
                    st.markdown("**Achievements:**")
                    for achievement in validation['achievements']:
                        st.write(f"✅ {achievement}")
                
                if validation.get('issues'):
                    st.markdown("**Issues:**")
                    for issue in validation['issues']:
                        st.write(f"⚠️ {issue}")
                
                if validation.get('metrics'):
                    st.markdown("**Metrics:**")
                    st.json(validation['metrics'])
    
    def _format_script(self, script: str, emphasis_words: list) -> str:
        """Format script with emphasis highlighting"""
        formatted = script
        
        # Highlight emphasis words
        for word in emphasis_words:
            formatted = formatted.replace(
                word, 
                f'<strong style="color: #1f77b4; background-color: #e8f4f8; padding: 2px 4px; border-radius: 3px;">{word}</strong>'
            )
        
        # Replace pauses with visual indicators
        formatted = formatted.replace('...', '<em style="color: #666;">... [pause] ...</em>')
        
        return formatted
    
    def display_header(self, title: str, icon: str = ""):
        """Helper method to display header"""
        st.subheader(f"{icon} {title}" if icon else title)
    
    def display_metric(self, label: str, value: Any):
        """Helper method to display metric"""
        st.metric(label, value)
    
    def validate_result(self, result: Any, shared_context: Any) -> Dict[str, Any]:
        """Validate voice result"""
        validation = {
            'is_valid': True,
            'quality_score': result.quality_score if hasattr(result, 'quality_score') else 0,
            'issues': [],
            'achievements': [],
            'metrics': {}
        }
        
        # Check if result has required attributes
        if hasattr(result, 'duration_estimate'):
            if result.duration_estimate > 0:
                validation['achievements'].append(f"Duration: {result.duration_estimate:.1f}s")
                validation['metrics']['duration'] = result.duration_estimate
            else:
                validation['issues'].append("No duration estimate")
        
        if hasattr(result, 'audio_file_path') and result.audio_file_path:
            validation['achievements'].append("Audio file generated")
            validation['metrics']['has_audio'] = True
        else:
            validation['metrics']['has_audio'] = False
        
        if hasattr(result, 'language'):
            validation['metrics']['language'] = result.language
        
        return validation
    
    def get_download_data(self, result: Any, customer_name: str) -> tuple[str, str, str]:
        """Get download data for voice script"""
        content = result.content if hasattr(result, 'content') else ''
        
        if not content:
            return "", "", ""
        
        customer_filename = customer_name.replace(' ', '_') if customer_name else 'customer'
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        filename = f"voice_script_{customer_filename}_{timestamp}.txt"
        
        return content, filename, "text/plain"

# Standalone display function for testing
def display_voice_note(result: VoiceResult, shared_context: Any = None, validation: Dict = None):
    """Display a voice note result"""
    display = VoiceDisplay()
    display.display(result, shared_context, validation)

def create_voice_display() -> VoiceDisplay:
    """Factory function to create voice display"""
    return VoiceDisplay()