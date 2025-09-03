"""
EMERGENCY VOICE TEST - WORKS IMMEDIATELY
No display dependencies - just core functionality
"""

import os
import sys
from pathlib import Path
import streamlit as st

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Only import core - no display modules
from src.core.shared_brain import SharedBrain
from src.core.voice_note_generator_enhanced import SmartVoiceGenerator

st.set_page_config(page_title="Voice Demo", page_icon="🎙️")
st.title("🎙️ Voice Note Generator - DEMO")

# Quick test customers
customers = {
    "English - John": {
        'name': 'John Smith',
        'preferred_language': 'English',
        'customer_id': 'DEMO001',
        'age': 35,
        'digital_logins_per_month': 20,
        'mobile_app_usage': 'Daily',
        'recent_life_events': 'New baby',
        'account_balance': 5000
    },
    "Spanish - Maria": {
        'name': 'Maria Garcia',
        'preferred_language': 'Spanish',
        'customer_id': 'DEMO002',
        'age': 42,
        'digital_logins_per_month': 15,
        'mobile_app_usage': 'Weekly',
        'recent_life_events': 'Started university',
        'account_balance': 8000
    },
    "French - Pierre": {
        'name': 'Pierre Dubois',
        'preferred_language': 'French',
        'customer_id': 'DEMO003',
        'age': 55,
        'digital_logins_per_month': 5,
        'mobile_app_usage': 'Monthly',
        'recent_life_events': 'Approaching retirement',
        'account_balance': 25000
    }
}

# Letter
test_letter = """
Important Account Update

We're updating your account with new features.
Your interest rate is changing to 2.5%.
This takes effect from next month.

Please contact us with any questions.

Lloyds Bank
"""

# Select customer
customer_key = st.selectbox("Select Customer:", list(customers.keys()))
customer = customers[customer_key]

# Show customer info
col1, col2, col3 = st.columns(3)
with col1:
    st.info(f"**Language:** {customer['preferred_language']}")
with col2:
    st.info(f"**Name:** {customer['name']}")
with col3:
    st.info(f"**Life Event:** {customer['recent_life_events']}")

# Generate button
if st.button("🎙️ GENERATE VOICE NOTE", type="primary", use_container_width=True):
    try:
        with st.spinner(f"Generating in {customer['preferred_language']}..."):
            
            # Create shared context
            brain = SharedBrain()
            context = brain.analyze_everything(
                letter_content=test_letter,
                customer_data=customer,
                force_channels=['voice']
            )
            
            # Generate voice
            generator = SmartVoiceGenerator()
            result = generator.generate_voice_note(context)
            
            st.success(f"✅ Generated in {result.language}!")
            
            # Show results
            st.markdown("---")
            
            # Metrics
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Language", result.language)
            with c2:
                st.metric("Duration", f"{result.duration_estimate:.0f}s")
            with c3:
                st.metric("Quality", f"{result.quality_score*100:.0f}%")
            
            # Audio player
            if result.audio_file_path and Path(result.audio_file_path).exists():
                st.markdown("### 🎵 Play Audio")
                with open(result.audio_file_path, 'rb') as f:
                    audio_bytes = f.read()
                st.audio(audio_bytes, format='audio/mp3')
                st.download_button("Download Audio", audio_bytes, file_name=f"voice_{customer['customer_id']}.mp3", mime='audio/mp3')
            else:
                st.warning("No audio file (TTS not configured)")
            
            # Show script
            st.markdown("### 📝 Script")
            st.text_area("Voice Script:", result.content, height=150)
            
    except Exception as e:
        st.error(f"Error: {e}")
        st.info("Check: CLAUDE_API_KEY and OPENAI_API_KEY in .env file")