"""Package initialization - Updated with Enhanced Voice Generator and Hallucination Detector"""

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

# Import Hallucination Detector
from .hallucination_detector import (
    HallucinationDetector, 
    HallucinationReport, 
    HallucinationFinding,
    HallucinationCategory,
    SeverityLevel,
    detect_hallucinations
)

# Import your existing working components
from .content_validator import ContentValidator, PointImportance, KeyPoint, validate_personalization
from .document_classifier import AIDocumentClassifier, ClassificationResult, DocumentType, classify_document
from .rules_engine import RulesEngine, Rule, RuleOperator, RuleAction

# Try to import personalization engine (if available)
try:
    from .personalization_engine import PersonalizationEngine, create_personalization_engine, personalize_for_customer
    PERSONALIZATION_ENGINE_AVAILABLE = True
except ImportError:
    PERSONALIZATION_ENGINE_AVAILABLE = False
    # Create dummy functions to prevent errors
    PersonalizationEngine = None
    create_personalization_engine = None
    personalize_for_customer = None

# Import advanced personalization (if available)
try:
    from .Personalization_Orchestrator import PersonalizationOrchestrator, orchestrate_with_engine
    ORCHESTRATOR_AVAILABLE = True
except ImportError:
    ORCHESTRATOR_AVAILABLE = False
    PersonalizationOrchestrator = None
    orchestrate_with_engine = None

# Import input cleaner (if available)
try:
    from .input_cleaner import InputCleaner, CleanedContent, clean_letter_content
    INPUT_CLEANER_AVAILABLE = True
except ImportError:
    INPUT_CLEANER_AVAILABLE = False
    InputCleaner = None
    CleanedContent = None
    clean_letter_content = None

# Make all components easily accessible
__all__ = [
    'SharedBrain', 'SharedContext', 'CustomerInsights', 'PersonalizationStrategy', 'PersonalizationLevel',
    'SmartEmailGenerator', 'EmailResult', 'generate_smart_email',
    'SmartSMSGenerator', 'SMSResult', 'generate_smart_sms',
    'SmartLetterGenerator', 'LetterResult', 'generate_smart_letter',
    'SmartVoiceGenerator', 'VoiceResult', 'generate_smart_voice_note',
    'HallucinationDetector', 'HallucinationReport', 'HallucinationFinding',
    'HallucinationCategory', 'SeverityLevel', 'detect_hallucinations',
    'ContentValidator', 'PointImportance', 'KeyPoint', 'validate_personalization',
    'AIDocumentClassifier', 'ClassificationResult', 'DocumentType', 'classify_document',
    'RulesEngine', 'Rule', 'RuleOperator', 'RuleAction'
]

# Only add to __all__ if available
if PERSONALIZATION_ENGINE_AVAILABLE:
    __all__.extend(['PersonalizationEngine', 'create_personalization_engine', 'personalize_for_customer'])

if ORCHESTRATOR_AVAILABLE:
    __all__.extend(['PersonalizationOrchestrator', 'orchestrate_with_engine'])

if INPUT_CLEANER_AVAILABLE:
    __all__.extend(['InputCleaner', 'CleanedContent', 'clean_letter_content'])