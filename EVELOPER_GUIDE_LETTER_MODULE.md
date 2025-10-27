# 📮 Letter Channel Implementation Guide

## 🎯 Overview
You're implementing the **Letter Channel** for the Lloyds AI Personalization Engine. This system uses a **Shared Brain** architecture where all intelligence comes from one source, and each channel has its own self-contained generator.

## 🏗️ Architecture Principles

### Core Concepts
1. **Shared Brain** (`shared_brain.py`) - Does ALL analysis once, creates `SharedContext`
2. **Channel Generators** - Take `SharedContext` and generate channel-specific content
3. **Self-Contained Modules** - Each channel has its config INSIDE the module (not in config.py)
4. **Consistency** - All channels follow the EXACT same pattern

### Data Flow
```
Letter + Customer → SharedBrain.analyze_everything() → SharedContext
                                                            ↓
                                            SmartLetterGenerator.generate_letter()
                                                            ↓
                                                        LetterResult
```

## 📁 File Structure

```
src/
├── config.py                      # ONLY shared settings (paths, API keys, etc)
├── core/
│   ├── __init__.py               # Must import your new generator
│   ├── shared_brain.py          # DO NOT MODIFY - provides SharedContext
│   ├── smart_email_generator.py # Reference pattern
│   ├── smart_sms_generator.py   # Reference pattern
│   └── smart_letter_generator.py # YOUR NEW FILE
└── personalization_app.py       # Update to display letter results
```

## 🔨 Step-by-Step Implementation

### Step 1: Create `smart_letter_generator.py`

Create `src/core/smart_letter_generator.py` following this EXACT structure:

```python
"""
Smart Letter Generator - Self-contained with configuration
Uses SharedContext for Consistent, Formal Letter Generation
"""

import os
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# Environment setup
from dotenv import load_dotenv
load_dotenv()

# AI imports
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("⚠️ Anthropic not available - using simulation mode")

# Import SharedContext
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.core.shared_brain import SharedContext, PersonalizationLevel
    SHARED_BRAIN_AVAILABLE = True
except ImportError:
    SHARED_BRAIN_AVAILABLE = False
    print("⚠️ Could not import SharedContext")

@dataclass
class LetterResult:
    """Result from letter generation - MUST match pattern of EmailResult/SMSResult"""
    content: str
    word_count: int
    page_count: int  # Letter-specific
    personalization_elements: List[str]
    formality_level: str  # Letter-specific
    includes_return_envelope: bool  # Letter-specific
    tone_achieved: str
    language: str
    generation_method: str
    processing_time: float
    quality_score: float

class SmartLetterGenerator:
    """
    Smart Letter Generator - Self-contained with all configuration
    Takes a SharedContext and generates perfectly aligned letter content
    """
    
    # ============== LETTER CONFIGURATION ==============
    # All letter-specific configuration in one place (MUST BE SELF-CONTAINED)
    LETTER_CONFIG = {
        'max_length': 10000,  # Maximum letter length in characters
        'min_length': 500,    # Minimum for a proper letter
        'format': {
            'paper_size': 'A4',
            'margins': {'top': 2.5, 'bottom': 2.5, 'left': 3, 'right': 3},  # cm
            'font': 'Arial',
            'font_size': 11,
            'line_spacing': 1.5
        },
        'structure': {
            'include_letterhead': True,
            'include_date': True,
            'include_reference': True,
            'include_footer': True,
            'include_page_numbers': True
        },
        'addressing': {
            'DIGITAL': {
                'style': 'modern_personal',
                'salutation': 'Dear {first_name}',
                'closing': 'Kind regards',
                'include_ps': False
            },
            'ASSISTED': {
                'style': 'balanced_formal',
                'salutation': 'Dear {title} {last_name}',
                'closing': 'Yours sincerely',
                'include_ps': False
            },
            'TRADITIONAL': {
                'style': 'traditional_formal',
                'salutation': 'Dear {title} {last_name}',
                'closing': 'Yours faithfully',
                'include_ps': True  # P.S. for branch contact
            }
        },
        'letterhead_template': """
Lloyds Banking Group
25 Gresham Street
London EC2V 7HN

{date}

{customer_name}
{customer_address}

Reference: {reference_number}
        """,
        'footer_template': """
Lloyds Bank plc. Registered Office: 25 Gresham Street, London EC2V 7HN.
Registered in England and Wales no. 2065. Authorised by the Prudential Regulation Authority.
        """,
        'quality_thresholds': {
            'min_paragraphs': 3,
            'max_paragraphs': 8,
            'ideal_paragraph_length': 150,  # words
            'min_personalization': 4,  # More than email due to length
            'formality_check': True
        },
        'enclosures': {
            'REGULATORY': ['Terms and Conditions', 'Privacy Notice'],
            'PROMOTIONAL': ['Product Brochure', 'Reply Form'],
            'INFORMATIONAL': [],
            'DEFAULT': []
        }
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the smart letter generator"""
        self.api_key = api_key or os.getenv('CLAUDE_API_KEY')
        self.client = None
        self.config = self.LETTER_CONFIG  # Use local config
        
        if self.api_key and ANTHROPIC_AVAILABLE:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.model = "claude-haiku-4-5-20251001"  # Same model for consistency
            print("✅ Smart Letter Generator initialized with Claude AI")
        else:
            print("⚠️ Smart Letter Generator running in simulation mode")
    
    def generate_letter(self, shared_context: SharedContext) -> LetterResult:
        """
        Generate a perfectly personalized letter using the Shared Brain's intelligence
        
        Args:
            shared_context: The complete intelligence from SharedBrain.analyze_everything()
            
        Returns:
            LetterResult with the generated letter and metadata
        """
        # MUST follow same pattern as generate_email() and generate_sms()
        
        start_time = datetime.now()
        
        print(f"📮 Generating smart letter for {shared_context.customer_data.get('name')}...")
        
        # Check if letter is enabled
        if not shared_context.channel_decisions['enabled_channels'].get('letter', False):
            return self._create_disabled_result(shared_context, "Letter disabled by rules")
        
        if self.client:
            result = self._generate_with_ai(shared_context)
        else:
            result = self._generate_simulation(shared_context)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        result.processing_time = processing_time
        
        print(f"✅ Smart letter generated in {processing_time:.2f}s")
        print(f"   Words: {result.word_count}, Pages: {result.page_count}, Quality: {result.quality_score:.2%}")
        
        return result
    
    # ... implement all the same methods as email/sms generators ...
    # _generate_with_ai()
    # _build_generation_prompt()
    # _parse_ai_response()
    # _create_letter_result()
    # _calculate_quality_score()
    # _generate_fallback()
    # _generate_simulation()
    # _create_disabled_result()
    # validate_letter()

# Convenience function (MUST HAVE THIS)
def generate_smart_letter(shared_context: SharedContext, api_key: Optional[str] = None) -> LetterResult:
    """
    Convenience function to generate a smart letter from shared context
    
    Args:
        shared_context: Complete intelligence from SharedBrain
        api_key: Optional API key
        
    Returns:
        LetterResult with generated letter
    """
    generator = SmartLetterGenerator(api_key=api_key)
    return generator.generate_letter(shared_context)
```

### Step 2: Key Patterns to Follow

#### Pattern 1: Configuration INSIDE Module
```python
LETTER_CONFIG = {
    # ALL letter-specific settings here
    # Nothing in config.py about letters except basic registration
}
```

#### Pattern 2: Same Method Names
- `generate_letter()` (not `create_letter()` or `build_letter()`)
- `validate_letter()` (not `check_letter()`)
- Same internal method names with underscore prefix

#### Pattern 3: Use SharedContext Intelligence
```python
def _generate_with_ai(self, shared_context: SharedContext):
    # Extract from shared context - DON'T re-analyze
    customer = shared_context.customer_data
    insights = shared_context.customer_insights
    strategy = shared_context.personalization_strategy
    content_strategy = shared_context.content_strategy
    
    # Get segment-specific config
    segment = insights.segment
    addressing = self.config['addressing'].get(segment)
```

#### Pattern 4: Result Dataclass
```python
@dataclass
class LetterResult:
    # MUST have these common fields:
    content: str
    personalization_elements: List[str]
    tone_achieved: str
    language: str
    generation_method: str
    processing_time: float
    quality_score: float
    
    # Plus letter-specific fields:
    page_count: int
    formality_level: str
    includes_return_envelope: bool
```

### Step 3: Update `core/__init__.py`

Add these imports:
```python
# Import Smart Letter Generator
from .smart_letter_generator import SmartLetterGenerator, LetterResult, generate_smart_letter
```

### Step 4: Update `personalization_app.py`

#### 4.1 Add to imports section:
```python
SmartLetterGenerator = None
LetterResult = None

# In the try block:
from src.core.smart_letter_generator import SmartLetterGenerator, LetterResult
print("✅ SmartLetterGenerator imported")
```

#### 4.2 Initialize in session state:
```python
if 'smart_letter_generator' not in st.session_state:
    if CORE_MODULES_AVAILABLE:
        st.session_state.smart_letter_generator = SmartLetterGenerator()
```

#### 4.3 Generate after SharedBrain analysis:
```python
# Generate smart letter using the shared context
if st.session_state.smart_letter_generator:
    with st.spinner("📮 Generating smart letter..."):
        letter_result = st.session_state.smart_letter_generator.generate_letter(shared_context)
        st.session_state.letter_result = letter_result
```

#### 4.4 Add Letter Tab:
```python
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🧠 Intelligence", "📧 Email", "📱 SMS", "📮 Letter", "📊 Analysis", "⚙️ System"])

with tab4:  # Letter tab
    if letter_result:
        display_smart_letter_result(letter_result, shared_context)
        # ... validation and download ...
```

### Step 5: Letter-Specific Considerations

#### 5.1 Physical Format
Letters need formatting for printing:
- Page breaks
- Proper margins
- Address positioning for windowed envelopes
- Barcode space (if using automated mail)

#### 5.2 Regulatory Requirements
Letters often have stricter requirements:
- Must include company registration details
- Regulatory notices in specific font sizes
- Accessibility considerations (min 11pt font)

#### 5.3 Multi-page Handling
```python
def _calculate_page_count(self, content: str) -> int:
    """Calculate number of pages based on content"""
    # Approximately 500 words per page
    word_count = len(content.split())
    return max(1, (word_count + 499) // 500)
```

#### 5.4 Enclosures
```python
def _determine_enclosures(self, doc_type: str) -> List[str]:
    """Determine what to include with the letter"""
    return self.config['enclosures'].get(doc_type, [])
```

## 🚨 Common Pitfalls to Avoid

### ❌ DON'T:
1. **Re-analyze the customer** - SharedBrain already did this
2. **Put letter config in config.py** - Keep it self-contained
3. **Create new patterns** - Follow email/SMS exactly
4. **Import from config.py** - Only import SharedContext from shared_brain
5. **Forget type hints** - Import `List`, `Dict`, etc. from `typing`
6. **Skip validation** - Every channel needs a `validate_` method

### ✅ DO:
1. **Use SharedContext** for all intelligence
2. **Keep config in the module**
3. **Follow naming patterns exactly**
4. **Test with simulation mode first**
5. **Handle disabled channels gracefully**
6. **Calculate quality scores consistently**

## 📊 Testing Checklist

- [ ] Module is self-contained (no config.py dependencies)
- [ ] Imports SharedContext correctly
- [ ] Has LETTER_CONFIG inside the class
- [ ] generate_letter() takes only SharedContext
- [ ] Returns LetterResult dataclass
- [ ] Has validate_letter() method
- [ ] Has convenience function generate_smart_letter()
- [ ] Updated core/__init__.py
- [ ] Updated personalization_app.py
- [ ] Tested with mock mode
- [ ] Tested with real API
- [ ] Quality score calculation works
- [ ] Handles disabled channel properly

## 🎯 Success Criteria

Your letter module is complete when:
1. It follows the EXACT pattern of email/SMS generators
2. It's completely self-contained
3. It integrates seamlessly with SharedBrain
4. The app shows letter results in its own tab
5. Validation and download work

## 💡 Pro Tips

1. **Copy smart_email_generator.py** as your starting template
2. **Search & Replace** "email" with "letter", "Email" with "Letter"
3. **Keep the same method structure** - just adapt the content
4. **Test with simulation first** before using API credits
5. **Letter tone should be MORE formal** than email
6. **Include page formatting** for physical printing

## 📞 Questions?

If something is unclear:
1. Look at `smart_email_generator.py` - it's the gold standard
2. Check `smart_sms_generator.py` - shows how to adapt for constraints
3. Remember: SharedContext has everything you need
4. Keep it self-contained and consistent!

Good luck! You've got this! 🚀