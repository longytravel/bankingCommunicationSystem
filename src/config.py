"""
Lloyds Banking Communication System - Configuration Module
Manages all application settings, paths, and constants
Business rules moved to JSON files - only technical config remains
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any

# Load environment variables
load_dotenv()

class Config:
    """Main configuration class for the application"""
    
    # ============== PATHS ==============
    # Project structure
    PROJECT_ROOT = Path(__file__).parent.parent
    SRC_DIR = PROJECT_ROOT / "src"
    DATA_DIR = PROJECT_ROOT / "data"
    ASSETS_DIR = PROJECT_ROOT / "assets"
    
    # Data subdirectories
    INPUT_DIR = DATA_DIR / "input"
    LETTERS_DIR = INPUT_DIR / "letters"
    CUSTOMERS_DIR = INPUT_DIR / "customers"
    OUTPUT_DIR = DATA_DIR / "output"
    PERSONALIZED_DIR = OUTPUT_DIR / "personalized"
    CACHE_DIR = DATA_DIR / "cache"
    
    # Rules directory
    RULES_DIR = DATA_DIR / "rules"
    
    # ============== API CONFIGURATION ==============
    # Claude API (Anthropic)
    CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')
    CLAUDE_MODEL = "claude-3-opus-20240229"
    CLAUDE_MAX_TOKENS = 2000
    CLAUDE_TEMPERATURE = 0.7
    
    # OpenAI API (for voice notes)
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_TTS_MODEL = "tts-1"
    OPENAI_TTS_HD_MODEL = "tts-1-hd"
    
    # ============== APPLICATION SETTINGS ==============
    # Environment
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    IS_DEVELOPMENT = ENVIRONMENT == 'development'
    
    # Processing limits
    MAX_BATCH_SIZE = int(os.getenv('MAX_BATCH_SIZE', '50'))
    DEFAULT_TEST_SIZE = int(os.getenv('DEFAULT_TEST_SIZE', '5'))
    
    # Testing flags
    QUICK_TEST_MODE = os.getenv('QUICK_TEST_MODE', 'false').lower() == 'true'
    USE_MOCK_DATA = os.getenv('USE_MOCK_DATA', 'false').lower() == 'true'
    LOG_API_CALLS = os.getenv('LOG_API_CALLS', 'true').lower() == 'true'
    
    # Performance settings
    ENABLE_CACHING = os.getenv('ENABLE_CACHING', 'true').lower() == 'true'
    CACHE_TTL_HOURS = int(os.getenv('CACHE_TTL_HOURS', '24'))
    PARALLEL_PROCESSING = os.getenv('PARALLEL_PROCESSING', 'true').lower() == 'true'
    
    # ============== LLOYDS BRANDING ==============
    BRAND_COLORS = {
        'primary_green': '#006A4D',      # Lloyds signature green
        'black': '#000000',              # Primary text
        'white': '#FFFFFF',              # Background
        'light_grey': '#F5F5F5',         # Secondary background
        'medium_grey': '#666666',        # Secondary text
        'dark_grey': '#333333',          # Headers
        'accent_teal': '#00BFA5',        # Interactive elements
        'error_red': '#D32F2F',          # Error states
        'success_green': '#388E3C',      # Success states
        'warning_amber': '#F57C00',      # Warning states
        'info_blue': '#1976D2'           # Info messages
    }
    
    # Typography
    FONTS = {
        'headline': 'Georgia, serif',    # GT Ultra substitute
        'body': 'Arial, Helvetica, sans-serif',
        'mono': 'Consolas, Courier New, monospace'
    }
    
    FONT_SIZES = {
        'h1': '2.5rem',
        'h2': '2rem',
        'h3': '1.5rem',
        'body': '1rem',
        'small': '0.875rem'
    }
    
    # ============== COMMUNICATION CHANNELS ==============
    CHANNELS = {
        'email': {
            'cost': 0.01,
            'max_length': 5000,
            'format': 'html',
            'compliance': True,
            'icon': '✉'
        },
        'sms': {
            'cost': 0.05,
            'max_length': 160,
            'format': 'plain',
            'compliance': False,
            'icon': '📱'
        },
        'letter': {
            'cost': 1.20,
            'max_length': 10000,
            'format': 'formal',
            'compliance': True,
            'icon': '📮'
        },
        'app': {
            'cost': 0.001,
            'max_length': 500,
            'format': 'plain',
            'compliance': True,
            'icon': '📲'
        },
        'voice': {
            'cost': 0.002,
            'max_length': 4000,
            'format': 'audio',
            'compliance': False,
            'icon': '🎙️'
        }
    }
    
    # ============== DOCUMENT CLASSIFICATION ==============
    DOCUMENT_CATEGORIES = ['REGULATORY', 'PROMOTIONAL', 'INFORMATIONAL']
    
    CLASSIFICATION_KEYWORDS = {
        'REGULATORY': [
            'terms and conditions', 'regulatory', 'compliance', 'legal requirement',
            'payment services regulations', 'mandatory', 'required by law'
        ],
        'PROMOTIONAL': [
            'offer', 'save money', 'exclusive', 'limited time', 'special rate',
            'earn rewards', 'bonus', 'discount'
        ],
        'INFORMATIONAL': [
            'update', 'information', 'notice', 'announcement', 'new feature',
            'helpful', 'tips', 'guide', 'support'
        ]
    }
    
    # ============== CUSTOMER SEGMENTS ==============
    # NOTE: Segment definitions are now in data/rules/personalization_rules.json
    CUSTOMER_SEGMENTS = {
        'DIGITAL': {
            'description': 'Self-service, app-first customers',
            'channel_preference': ['app', 'email', 'voice'],
            'tone': 'modern'
        },
        'ASSISTED': {
            'description': 'Hybrid digital/human support',
            'channel_preference': ['email', 'sms', 'app'],
            'tone': 'friendly'
        },
        'TRADITIONAL': {
            'description': 'Branch and postal preference',
            'channel_preference': ['letter', 'email'],
            'tone': 'formal'
        }
    }
    
    # Vulnerability indicators
    VULNERABILITY_KEYWORDS = [
        'elderly', 'disability', 'bereavement', 'health condition',
        'financial difficulty', 'mental health', 'accessibility'
    ]
    
    # Life events
    LIFE_EVENTS = [
        'marriage', 'divorce', 'new baby', 'bereavement',
        'new job', 'retirement', 'house move', 'graduation'
    ]
    
    # ============== LANGUAGE SUPPORT ==============
    # Claude supports 95+ languages automatically
    # Common languages for reference
    COMMON_LANGUAGES = [
        'English', 'Spanish', 'French', 'German', 'Italian', 'Portuguese',
        'Dutch', 'Polish', 'Russian', 'Chinese', 'Japanese', 'Korean',
        'Arabic', 'Hindi', 'Urdu', 'Bengali', 'Punjabi', 'Turkish',
        'Vietnamese', 'Thai', 'Indonesian', 'Malay', 'Swahili'
    ]
    
    # RTL (Right-to-Left) languages
    RTL_LANGUAGES = ['Arabic', 'Hebrew', 'Urdu', 'Persian', 'Pashto']
    
    # ============== TECHNICAL VALIDATION ==============
    # Only technical validations remain here
    # Business rules moved to data/rules/validation_rules.json
    TECHNICAL_VALIDATION = {
        'max_file_size_mb': 10,
        'allowed_file_types': ['.txt', '.docx', '.pdf', '.csv', '.xlsx'],
        'max_api_retries': 3,
        'api_timeout_seconds': 30,
        'max_concurrent_requests': 10
    }
    
    # ============== MOCK DATA FOR TESTING ==============
    MOCK_CLASSIFICATION = {
        'classification': 'REGULATORY',
        'confidence': 0.95,
        'reasoning': 'Contains terms and conditions changes'
    }
    
    MOCK_PERSONALIZATION = {
        'email': 'Dear {name}, We have important updates about your account...',
        'sms': 'Lloyds: Account update required. Check app for details.',
        'letter': 'Dear {name}, Following our recent review of your account...',
        'app': 'You have a new message about your account terms.',
        'voice': 'Hello {name}, this is an important message from Lloyds Bank.'
    }
    
    # ============== RULES ENGINE CONFIGURATION ==============
    RULES_FILES = {
        'communication': 'communication_rules.json',
        'personalization': 'personalization_rules.json',
        'voice_config': 'voice_config_rules.json',
        'validation': 'validation_rules.json'
    }
    
    # ============== HELPER METHODS ==============
    @classmethod
    def create_directories(cls):
        """Create all required directories if they don't exist"""
        directories = [
            cls.DATA_DIR, cls.INPUT_DIR, cls.LETTERS_DIR,
            cls.CUSTOMERS_DIR, cls.OUTPUT_DIR, cls.PERSONALIZED_DIR,
            cls.CACHE_DIR, cls.ASSETS_DIR, cls.RULES_DIR,
            cls.OUTPUT_DIR / 'voice_notes',
            cls.CACHE_DIR / 'voice_notes'
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_sample_size(cls) -> int:
        """Get the number of customers to process based on test mode"""
        if cls.QUICK_TEST_MODE:
            return cls.DEFAULT_TEST_SIZE
        return cls.MAX_BATCH_SIZE
    
    @classmethod
    def should_use_mock_data(cls) -> bool:
        """Check if mock data should be used"""
        return cls.USE_MOCK_DATA or not cls.CLAUDE_API_KEY
    
    @classmethod
    def get_channel_cost(cls, channel: str, count: int = 1) -> float:
        """Calculate cost for a communication channel"""
        if channel in cls.CHANNELS:
            return cls.CHANNELS[channel]['cost'] * count
        return 0.0
    
    @classmethod
    def is_rtl_language(cls, language: str) -> bool:
        """Check if a language is right-to-left"""
        return language in cls.RTL_LANGUAGES
    
    @classmethod
    def validate_file_type(cls, filename: str) -> bool:
        """Check if file type is allowed (technical validation only)"""
        return any(filename.lower().endswith(ext) 
                  for ext in cls.TECHNICAL_VALIDATION['allowed_file_types'])
    
    @classmethod
    def get_rules_path(cls, rules_type: str) -> Path:
        """Get path to a specific rules file"""
        if rules_type in cls.RULES_FILES:
            return cls.RULES_DIR / cls.RULES_FILES[rules_type]
        return None
    
    @classmethod
    def load_rules_engine(cls, rules_type: str):
        """Load a specific rules engine"""
        from src.core.rules_engine import RulesEngine
        
        rules_path = cls.get_rules_path(rules_type)
        if rules_path and rules_path.exists():
            return RulesEngine(str(rules_path))
        else:
            print(f"Warning: Rules file not found: {rules_type}")
            return None
    
    @classmethod
    def evaluate_business_rule(cls, rule_type: str, context: Dict[str, Any], tags: list = None) -> Dict[str, Any]:
        """
        Evaluate business rules for a given context
        
        Args:
            rule_type: Type of rules to evaluate ('validation', 'personalization', etc.)
            context: Context dictionary with customer/document data
            tags: Optional tags to filter rules
            
        Returns:
            Rules evaluation result
        """
        engine = cls.load_rules_engine(rule_type)
        if engine:
            return engine.evaluate(context, tags=tags)
        return {'features': {}, 'metadata': {}, 'triggered_rules': []}
    
    @classmethod
    def get_css_theme(cls) -> str:
        """Get Lloyds-branded CSS for Streamlit"""
        return f"""
        <style>
        /* Lloyds Banking Group Theme */
        .stApp {{
            background-color: {cls.BRAND_COLORS['white']};
        }}
        
        /* Headers */
        h1, h2, h3 {{
            color: {cls.BRAND_COLORS['dark_grey']};
            font-family: {cls.FONTS['headline']};
        }}
        
        /* Primary button */
        .stButton > button {{
            background-color: {cls.BRAND_COLORS['primary_green']};
            color: white;
            border: none;
            border-radius: 4px;
            padding: 0.5rem 1rem;
            font-weight: 500;
            transition: background-color 0.3s;
        }}
        
        .stButton > button:hover {{
            background-color: {cls.BRAND_COLORS['accent_teal']};
        }}
        
        /* Sidebar */
        .css-1d391kg {{
            background-color: {cls.BRAND_COLORS['light_grey']};
        }}
        
        /* Success messages */
        .success {{
            color: {cls.BRAND_COLORS['success_green']};
        }}
        
        /* Error messages */
        .error {{
            color: {cls.BRAND_COLORS['error_red']};
        }}
        
        /* Info boxes */
        .stInfo {{
            background-color: {cls.BRAND_COLORS['light_grey']};
            border-left: 4px solid {cls.BRAND_COLORS['primary_green']};
        }}
        
        /* Voice note indicators */
        .voice-eligible {{
            background-color: {cls.BRAND_COLORS['accent_teal']};
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.875rem;
        }}
        </style>
        """
    
    @classmethod
    def get_api_config(cls, api_name: str) -> Dict[str, Any]:
        """Get configuration for a specific API"""
        configs = {
            'claude': {
                'api_key': cls.CLAUDE_API_KEY,
                'model': cls.CLAUDE_MODEL,
                'max_tokens': cls.CLAUDE_MAX_TOKENS,
                'temperature': cls.CLAUDE_TEMPERATURE
            },
            'openai': {
                'api_key': cls.OPENAI_API_KEY,
                'tts_model': cls.OPENAI_TTS_MODEL,
                'tts_hd_model': cls.OPENAI_TTS_HD_MODEL
            }
        }
        return configs.get(api_name, {})
    
    @classmethod
    def log_event(cls, event_type: str, details: Dict[str, Any]):
        """Log system events (placeholder for future logging implementation)"""
        if cls.LOG_API_CALLS and event_type == 'api_call':
            print(f"API Call: {details}")
        # Future: Implement proper logging to file/database
    
    @classmethod
    def validate_customer_data(cls, customer: Dict[str, Any]) -> tuple[bool, list]:
        """
        Validate customer data structure
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        required_fields = ['name', 'customer_id']
        errors = []
        
        for field in required_fields:
            if field not in customer:
                errors.append(f"Missing required field: {field}")
        
        return len(errors) == 0, errors
    
    @classmethod
    def get_environment_info(cls) -> Dict[str, Any]:
        """Get current environment information"""
        return {
            'environment': cls.ENVIRONMENT,
            'is_development': cls.IS_DEVELOPMENT,
            'quick_test_mode': cls.QUICK_TEST_MODE,
            'mock_mode': cls.USE_MOCK_DATA,
            'caching_enabled': cls.ENABLE_CACHING,
            'apis_configured': {
                'claude': bool(cls.CLAUDE_API_KEY),
                'openai': bool(cls.OPENAI_API_KEY)
            },
            'rules_files': {
                name: cls.get_rules_path(name).exists() if cls.get_rules_path(name) else False
                for name in cls.RULES_FILES.keys()
            }
        }

# Create directories on import
Config.create_directories()

# Quick access variables for backward compatibility
PROJECT_ROOT = Config.PROJECT_ROOT
DATA_DIR = Config.DATA_DIR
QUICK_TEST_MODE = Config.QUICK_TEST_MODE
USE_MOCK_DATA = Config.USE_MOCK_DATA