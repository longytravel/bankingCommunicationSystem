"""Package initialization - Updated with Enhanced Voice Generator"""

# Import the NEW Shared Brain
from .shared_brain import SharedBrain, SharedContext, CustomerInsights, PersonalizationStrategy, PersonalizationLevel

# Import Smart Email Generator
from .smart_email_generator import SmartEmailGenerator, EmailResult, generate_smart_email

# Import Smart SMS Generator
from .smart_sms_generator import SmartSMSGenerator, SMSResult, generate_smart_sms

# Import Smart Letter Generator
from .smart_letter_generator import SmartLetterGenerator, LetterResult, generate_smart_letter

# Import Enhanced Voice Generator with Audio Support
from .voice_note_generator_enhanced import SmartVoiceGenerator, VoiceResult, generate_smart_voice_note

# Import your existing working components
from .content_validator import ContentValidator, PointImportance, KeyPoint, validate_personalization
from .document_classifier import AIDocumentClassifier, ClassificationResult, DocumentType, classify_document
from .rules_engine import RulesEngine, Rule, RuleOperator, RuleAction
# REMOVED: personalization_engine import (module doesn't exist)

# Import advanced personalization (if available)
try:
    from .Personalization_Orchestrator import PersonalizationOrchestrator, orchestrate_with_engine
except ImportError:
    pass

# Import input cleaner (if available)
try:
    from .input_cleaner import InputCleaner, CleanedContent, clean_letter_content
except ImportError:
    pass

# Make all components easily accessible
__all__ = [
    'SharedBrain', 'SharedContext', 'CustomerInsights', 'PersonalizationStrategy', 'PersonalizationLevel',
    'SmartEmailGenerator', 'EmailResult', 'generate_smart_email',
    'SmartSMSGenerator', 'SMSResult', 'generate_smart_sms',
    'SmartLetterGenerator', 'LetterResult', 'generate_smart_letter',
    'SmartVoiceGenerator', 'VoiceResult', 'generate_smart_voice_note',
    'ContentValidator', 'PointImportance', 'KeyPoint', 'validate_personalization',
    'AIDocumentClassifier', 'ClassificationResult', 'DocumentType', 'classify_document',
    'RulesEngine', 'Rule', 'RuleOperator', 'RuleAction'
    # REMOVED: PersonalizationEngine items
]