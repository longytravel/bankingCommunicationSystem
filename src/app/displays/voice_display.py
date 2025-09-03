"""
Voice Note Display Module - Shows voice notes with audio player
Integrates with Streamlit to display and play voice notes
"""

import streamlit as st
from pathlib import Path
from typing import Dict, Any, Optional
import base64
from datetime import datetime

# Import the base display class
try:
    from src.display.base_display import BaseChannelDisplay
except ImportError:
    # If base display doesn't exist, create a simple version
    class BaseChannelDisplay:
        def display_header(self, title: str, icon: str = ""):
            st.subheader(f"{icon} {title}")
        
        def display_metric(self, label: str, value: Any):
            st.metric(label, value)

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
        super().__init__()
        self.channel_name = "Voice Note"
        self.channel_icon = "🎙️"
    
    def display(self, result: VoiceResult, shared_context: Any, validation: Optional[Dict] = None):
        """Display voice note with audio player"""
        
        # Header
        self.display_header(f"{self.channel_icon} Voice Note", self.channel_icon)
        
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
    
    def display_analytics(self, results: list):
        """Display analytics for multiple voice notes"""
        st.markdown("### 📊 Voice Note Analytics")
        
        if not results:
            st.info("No voice notes generated yet")
            return
        
        # Calculate stats
        total = len(results)
        with_audio = sum(1 for r in results if r.audio_file_path)
        avg_duration = sum(r.duration_estimate for r in results) / total if total > 0 else 0
        languages = {}
        for r in results:
            languages[r.language] = languages.get(r.language, 0) + 1
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Voice Notes", total)
        
        with col2:
            st.metric("With Audio", f"{with_audio}/{total}")
        
        with col3:
            st.metric("Avg Duration", f"{avg_duration:.1f}s")
        
        with col4:
            st.metric("Languages", len(languages))
        
        # Language breakdown
        if languages:
            st.markdown("**Language Distribution:**")
            for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total) * 100
                st.progress(percentage / 100)
                st.text(f"{lang}: {count} ({percentage:.1f}%)")
        
        # Quality distribution
        quality_scores = [r.quality_score for r in results if r.quality_score > 0]
        if quality_scores:
            avg_quality = sum(quality_scores) / len(quality_scores)
            
            st.markdown("**Quality Metrics:**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Avg Quality", f"{avg_quality*100:.1f}%")
            
            with col2:
                high_quality = sum(1 for s in quality_scores if s >= 0.8)
                st.metric("High Quality", f"{high_quality}/{len(quality_scores)}")
            
            with col3:
                low_quality = sum(1 for s in quality_scores if s < 0.6)
                if low_quality > 0:
                    st.warning(f"Low Quality: {low_quality}")
                else:
                    st.success("No Low Quality")
    
    def display_comparison(self, result1: VoiceResult, result2: VoiceResult):
        """Compare two voice notes side by side"""
        st.markdown("### 🔄 Voice Note Comparison")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Voice Note 1**")
            self._display_summary(result1)
        
        with col2:
            st.markdown("**Voice Note 2**")
            self._display_summary(result2)
    
    def _display_summary(self, result: VoiceResult):
        """Display summary of a voice note"""
        if result.generation_method == 'disabled':
            st.error("Disabled")
            return
        
        st.info(f"Language: {result.language}")
        st.text(f"Duration: {result.duration_estimate:.1f}s")
        st.text(f"Words: {result.word_count}")
        st.text(f"Quality: {result.quality_score*100:.0f}%")
        
        if result.audio_file_path:
            st.success("✅ Has Audio")
        else:
            st.warning("📝 Script Only")
        
        # Show first few words of script
        if result.content:
            preview = result.content[:100] + "..." if len(result.content) > 100 else result.content
            st.text_area("Preview:", preview, height=100, disabled=True)


def create_voice_display() -> VoiceDisplay:
    """Factory function to create voice display"""
    return VoiceDisplay()


# Standalone display function for testing
def display_voice_note(result: VoiceResult, shared_context: Any = None, validation: Dict = None):
    """Display a voice note result"""
    display = VoiceDisplay()
    display.display(result, shared_context, validation)