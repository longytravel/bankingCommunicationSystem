"""Package initialization - Updated with Smart SMS Generator"""

# Import the NEW Shared Brain
from .shared_brain import SharedBrain, SharedContext, CustomerInsights, PersonalizationStrategy, PersonalizationLevel

# Import Smart Email Generator
from .smart_email_generator import SmartEmailGenerator, EmailResult, generate_smart_email

# Import Smart SMS Generator (NEW - replacing old orchestrator)
from .smart_sms_generator import SmartSMSGenerator, SMSResult, generate_smart_sms

# Import Smart Letter Generator (NEW)
from .smart_letter_generator import SmartLetterGenerator, LetterResult, generate_smart_letter

# Import your existing working components
from .content_validator import ContentValidator, PointImportance, KeyPoint, validate_personalization
from .document_classifier import AIDocumentClassifier, ClassificationResult, DocumentType, classify_document
from .rules_engine import RulesEngine, Rule, RuleOperator, RuleAction
from .personalization_engine import PersonalizationEngine, create_personalization_engine, personalize_for_customer

# Import advanced personalization (if available)
try:
    from .Personalization_Orchestrator import PersonalizationOrchestrator, orchestrate_with_engine
except ImportError:
    pass

# Import voice integration (if available)
try:
    from .voice_note_generator import VoiceNoteGenerator
except ImportError:
    pass

# Import input cleaner (if available)
try:
    from .input_cleaner import InputCleaner, CleanedContent, clean_letter_content
except ImportError:
    pass