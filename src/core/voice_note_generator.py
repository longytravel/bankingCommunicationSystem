"""
Voice Note Generator Module - OpenAI TTS Integration
Generates voice notes for personalized communications
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# Try to import OpenAI (will fail gracefully if not installed)
try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("OpenAI not installed - voice notes will be simulated")

from src.core.rules_engine import RulesEngine

class VoiceNoteGenerator:
    """Generate voice notes using OpenAI TTS with rules-based eligibility"""
    
    # OpenAI TTS Voice Options
    VOICES = {
        'alloy': {'gender': 'neutral', 'style': 'balanced'},
        'echo': {'gender': 'male', 'style': 'smooth'},
        'fable': {'gender': 'neutral', 'style': 'expressive'},
        'onyx': {'gender': 'male', 'style': 'deep'},
        'nova': {'gender': 'female', 'style': 'friendly'},
        'shimmer': {'gender': 'female', 'style': 'warm'}
    }
    
    # Language to voice mapping
    LANGUAGE_VOICES = {
        'English': ['nova', 'echo', 'alloy'],
        'Spanish': ['nova', 'shimmer', 'alloy'],
        'French': ['shimmer', 'nova', 'alloy'],
        'German': ['echo', 'onyx', 'alloy'],
        'Italian': ['fable', 'nova', 'alloy'],
        'Portuguese': ['nova', 'shimmer', 'alloy'],
        'Polish': ['echo', 'alloy', 'nova'],
        'Chinese': ['alloy', 'shimmer', 'nova'],
        'Japanese': ['shimmer', 'alloy', 'nova'],
        'Korean': ['nova', 'alloy', 'shimmer'],
        'Arabic': ['onyx', 'echo', 'alloy'],
        'Hindi': ['fable', 'nova', 'alloy'],
        'default': ['alloy', 'nova', 'echo']
    }
    
    def __init__(self, api_key: Optional[str] = None, rules_file: Optional[str] = None):
        """
        Initialize the voice note generator
        
        Args:
            api_key: OpenAI API key (or use environment variable)
            rules_file: Path to rules configuration file
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.client = None
        
        if self.api_key and OPENAI_AVAILABLE:
            self.client = OpenAI(api_key=self.api_key)
        else:
            print("Warning: No OpenAI API key provided. Voice notes will be simulated.")
        
        # Initialize rules engine
        rules_path = rules_file or str(Path(__file__).parent.parent.parent / 'data' / 'rules' / 'communication_rules.json')
        self.rules_engine = RulesEngine(rules_path)
        
        # Set up output directory
        self.output_dir = Path(__file__).parent.parent.parent / 'data' / 'output' / 'voice_notes'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache directory for voice files
        self.cache_dir = Path(__file__).parent.parent.parent / 'data' / 'cache' / 'voice_notes'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Voice generation stats
        self.stats = {
            'total_evaluated': 0,
            'voice_generated': 0,
            'voice_skipped': 0,
            'reasons': {}
        }
    
    def should_generate_voice_note(self, customer: Dict[str, Any], document: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Determine if voice note should be generated based on rules
        
        Args:
            customer: Customer profile data
            document: Optional document metadata
            
        Returns:
            Dictionary with decision and metadata
        """
        # Build context for rules evaluation
        context = {
            'customer': customer,
            'document': document or {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Evaluate rules
        rules_result = self.rules_engine.evaluate(context, tags=['voice_note'])
        
        # Check for explicit disables (they override enables)
        should_generate = False  # Start with False
        has_disable = False
        
        for action in rules_result.get('actions', []):
            if action.get('type') == 'disable' and action.get('feature') == 'voice_note':
                should_generate = False
                has_disable = True
                break  # Disable takes priority
            elif action.get('type') == 'enable' and action.get('feature') == 'voice_note' and not has_disable:
                should_generate = True
        
        # Alternative: Check features dictionary
        if not has_disable and 'features' in rules_result:
            should_generate = rules_result.get('features', {}).get('voice_note', False)
        
        # Get metadata from rules
        metadata = rules_result.get('metadata', {})
        
        # Build response
        result = {
            'generate': should_generate,
            'voice_style': metadata.get('voice_style', 'conversational'),
            'voice_speed': metadata.get('voice_speed', 1.0),
            'voice_language': metadata.get('voice_language', customer.get('preferred_language', 'English')),
            'priority_channel': metadata.get('priority_channel', 'standard'),
            'reason': metadata.get('reason', 'Rules evaluation completed'),
            'triggered_rules': rules_result.get('triggered_rules', []),
            'tags': rules_result.get('tags', [])
        }
        
        # Update stats
        self.stats['total_evaluated'] += 1
        if should_generate:
            self.stats['voice_generated'] += 1
        else:
            self.stats['voice_skipped'] += 1
            reason = result['reason']
            self.stats['reasons'][reason] = self.stats['reasons'].get(reason, 0) + 1
        
        return result
    
    def generate_voice_note(
        self,
        text: str,
        customer: Dict[str, Any],
        document: Optional[Dict] = None,
        force: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a voice note for the given text and customer
        
        Args:
            text: Text content to convert to speech
            customer: Customer profile data
            document: Optional document metadata
            force: Force generation regardless of rules
            
        Returns:
            Dictionary with voice note details or None if not generated
        """
        # Check if voice note should be generated
        if not force:
            decision = self.should_generate_voice_note(customer, document)
            if not decision['generate']:
                print(f"Voice note skipped for {customer.get('name', 'Unknown')}: {decision['reason']}")
                return None
        else:
            decision = {
                'voice_style': 'conversational',
                'voice_speed': 1.0,
                'voice_language': customer.get('preferred_language', 'English')
            }
        
        # Select appropriate voice
        voice = self._select_voice(customer, decision)
        
        # Prepare text for TTS
        prepared_text = self._prepare_text(text, customer, decision)
        
        # Generate voice note
        if self.client:
            audio_data = self._generate_tts(prepared_text, voice, decision['voice_speed'])
        else:
            audio_data = self._simulate_tts(prepared_text, voice)
        
        if not audio_data:
            return None
        
        # Save voice note
        filename = self._save_voice_note(audio_data, customer)
        
        # Create metadata
        result = {
            'customer_id': customer.get('customer_id', 'unknown'),
            'customer_name': customer.get('name', 'Unknown'),
            'filename': str(filename),
            'text_length': len(prepared_text),
            'voice': voice,
            'language': decision['voice_language'],
            'style': decision.get('voice_style', 'standard'),
            'speed': decision.get('voice_speed', 1.0),
            'generated_at': datetime.now().isoformat(),
            'duration_estimate': len(prepared_text) / 150,  # Rough estimate: 150 chars per second
            'tags': decision.get('tags', [])
        }
        
        # Save metadata
        self._save_metadata(result, customer)
        
        return result
    
    def _select_voice(self, customer: Dict[str, Any], decision: Dict[str, Any]) -> str:
        """Select appropriate voice based on customer profile and rules"""
        language = decision.get('voice_language', 'English')
        style = decision.get('voice_style', 'conversational')
        
        # Get language-appropriate voices
        language_options = self.LANGUAGE_VOICES.get(language, self.LANGUAGE_VOICES['default'])
        
        # Select based on style preference
        if style == 'premium':
            # Use more professional voices for premium customers
            preferred_voices = ['echo', 'onyx', 'shimmer']
        elif style == 'engaging':
            # Use expressive voices for promotional content
            preferred_voices = ['fable', 'nova', 'shimmer']
        elif style == 'clear_and_slow':
            # Use clear voices for elderly customers
            preferred_voices = ['echo', 'alloy', 'nova']
        else:
            # Default conversational style
            preferred_voices = ['nova', 'alloy', 'shimmer']
        
        # Find best match between language and style preferences
        for voice in preferred_voices:
            if voice in language_options:
                return voice
        
        # Fallback to first language option
        return language_options[0]
    
    def _prepare_text(self, text: str, customer: Dict[str, Any], decision: Dict[str, Any]) -> str:
        """Prepare and optimize text for TTS"""
        # Clean up text for TTS
        prepared = text
        
        # Add appropriate greeting based on customer profile
        name = customer.get('name', 'Valued Customer')
        language = decision.get('voice_language', 'English')
        
        # Add contextual introduction
        if 'urgent_voice' in decision.get('tags', []):
            intro = f"Urgent message for {name}. "
        elif decision.get('voice_style') == 'premium':
            intro = f"Personal message for {name}. "
        else:
            intro = f"Hello {name}. "
        
        # Handle language-specific formatting
        if language != 'English':
            # You might want to add language-specific introductions here
            prepared = intro + prepared
        else:
            prepared = intro + prepared
        
        # Clean up for TTS
        prepared = prepared.replace('£', 'pounds')
        prepared = prepared.replace('€', 'euros')
        prepared = prepared.replace('$', 'dollars')
        prepared = prepared.replace('&', 'and')
        
        # Remove excessive punctuation
        prepared = prepared.replace('...', '.')
        prepared = prepared.replace('!!', '!')
        prepared = prepared.replace('??', '?')
        
        # Limit length for voice notes (TTS has limits)
        max_length = 4000  # OpenAI TTS limit is 4096 characters
        if len(prepared) > max_length:
            prepared = prepared[:max_length-20] + "... Please check your app for full details."
        
        return prepared
    
    def _generate_tts(self, text: str, voice: str, speed: float = 1.0) -> Optional[bytes]:
        """Generate TTS using OpenAI API"""
        if not OPENAI_AVAILABLE:
            return self._simulate_tts(text, voice)
            
        try:
            response = self.client.audio.speech.create(
                model="tts-1",  # or "tts-1-hd" for higher quality
                voice=voice,
                input=text,
                speed=speed
            )
            
            # Get audio data
            audio_data = response.content
            return audio_data
            
        except Exception as e:
            print(f"Error generating TTS: {e}")
            return None
    
    def _simulate_tts(self, text: str, voice: str) -> bytes:
        """Simulate TTS for testing without API"""
        # Create a mock audio file (just metadata for testing)
        mock_data = {
            'type': 'mock_audio',
            'text': text[:100] + '...' if len(text) > 100 else text,
            'voice': voice,
            'length': len(text),
            'generated': datetime.now().isoformat()
        }
        return json.dumps(mock_data).encode('utf-8')
    
    def _save_voice_note(self, audio_data: bytes, customer: Dict[str, Any]) -> Path:
        """Save voice note to file"""
        # Generate filename
        customer_id = customer.get('customer_id', 'unknown')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Determine file extension based on data
        if audio_data.startswith(b'{'):
            # Mock data
            extension = '.json'
        else:
            # Real audio
            extension = '.mp3'
        
        filename = f"voice_note_{customer_id}_{timestamp}{extension}"
        filepath = self.output_dir / filename
        
        # Save file
        with open(filepath, 'wb') as f:
            f.write(audio_data)
        
        return filepath
    
    def _save_metadata(self, metadata: Dict[str, Any], customer: Dict[str, Any]):
        """Save voice note metadata"""
        customer_id = customer.get('customer_id', 'unknown')
        metadata_file = self.output_dir / f"metadata_{customer_id}.json"
        
        # Load existing metadata if exists
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                existing = json.load(f)
        else:
            existing = {'voice_notes': []}
        
        # Append new metadata
        existing['voice_notes'].append(metadata)
        
        # Save updated metadata
        with open(metadata_file, 'w') as f:
            json.dump(existing, f, indent=2)
    
    def batch_generate(
        self,
        communications: List[Dict[str, Any]],
        show_progress: bool = True
    ) -> Dict[str, Any]:
        """
        Generate voice notes for multiple communications
        
        Args:
            communications: List of dicts with 'text', 'customer', and optional 'document'
            show_progress: Show progress updates
            
        Returns:
            Summary of generation results
        """
        results = []
        
        for i, comm in enumerate(communications):
            if show_progress:
                print(f"Processing {i+1}/{len(communications)}: {comm['customer'].get('name', 'Unknown')}")
            
            result = self.generate_voice_note(
                text=comm['text'],
                customer=comm['customer'],
                document=comm.get('document')
            )
            
            if result:
                results.append(result)
        
        # Return summary
        return {
            'total_processed': len(communications),
            'voice_notes_generated': len(results),
            'voice_notes_skipped': len(communications) - len(results),
            'results': results,
            'stats': self.stats
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get voice generation statistics"""
        return {
            'total_evaluated': self.stats['total_evaluated'],
            'voice_generated': self.stats['voice_generated'],
            'voice_skipped': self.stats['voice_skipped'],
            'generation_rate': (
                self.stats['voice_generated'] / self.stats['total_evaluated'] * 100
                if self.stats['total_evaluated'] > 0 else 0
            ),
            'skip_reasons': self.stats['reasons'],
            'output_directory': str(self.output_dir),
            'cache_directory': str(self.cache_dir)
        }
    
    def clear_cache(self):
        """Clear cached voice notes"""
        for file in self.cache_dir.glob('*'):
            file.unlink()
        print(f"Cleared cache directory: {self.cache_dir}")
    
    def export_report(self, output_file: Optional[str] = None) -> str:
        """Export generation report"""
        if not output_file:
            output_file = self.output_dir / f"voice_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'statistics': self.get_statistics(),
            'configuration': {
                'available_voices': list(self.VOICES.keys()),
                'language_support': list(self.LANGUAGE_VOICES.keys()),
                'rules_file': self.rules_engine.rules[0].name if self.rules_engine.rules else 'No rules loaded'
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return str(output_file)
    
    