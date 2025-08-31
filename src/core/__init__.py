"""Package initialization."""

# Import the new Shared Brain
from .shared_brain import SharedBrain, SharedContext, CustomerInsights, PersonalizationStrategy, ContentStrategy, PersonalizationLevel

# Import your existing working components
from .content_validator import ContentValidator, PointImportance, KeyPoint, validate_personalization
from .document_classifier import AIDocumentClassifier, ClassificationResult, DocumentType, classify_document
from .rules_engine import RulesEngine, Rule, RuleOperator, RuleAction
from .personalization_engine import PersonalizationEngine, create_personalization_engine, personalize_for_customer

# Import channel generators
from .email_channel_generator import EmailChannelGenerator, EmailPersonalizationContext, generate_personalized_email
from .sms_channel_generator import SMSChannelGenerator, SMSPersonalizationContext, generate_personalized_sms

# Import orchestrators
from .simple_email_orchestrator import SimpleEmailOrchestrator, personalize_email_simple
from .simple_sms_orchestrator import SimpleSMSOrchestrator, personalize_sms_simple

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