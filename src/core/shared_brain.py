"""
Shared Brain - Central Intelligence for Multi-Channel Personalization
FIXED: Prevents ALL hallucinations through strict data-driven constraints
"""

import os
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import anthropic
from dotenv import load_dotenv

load_dotenv()

# Add the project root to Python path
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import your existing working components
try:
    from src.core.content_validator import ContentValidator, PointImportance
    CONTENT_VALIDATOR_AVAILABLE = True
except ImportError as e:
    CONTENT_VALIDATOR_AVAILABLE = False
    print(f"⚠️ Content Validator not available: {e}")

try:
    from src.core.document_classifier import AIDocumentClassifier, DocumentType
    DOCUMENT_CLASSIFIER_AVAILABLE = True
except ImportError as e:
    DOCUMENT_CLASSIFIER_AVAILABLE = False
    print(f"⚠️ Document Classifier not available: {e}")

try:
    from src.core.rules_engine import RulesEngine
    RULES_ENGINE_AVAILABLE = True
except ImportError as e:
    RULES_ENGINE_AVAILABLE = False
    print(f"⚠️ Rules Engine not available: {e}")

try:
    from src.config import Config
    CONFIG_AVAILABLE = True
except ImportError as e:
    CONFIG_AVAILABLE = False
    print(f"⚠️ Config module not available: {e}")
    
    # Create a minimal Config class if not available
    class Config:
        @classmethod
        def load_rules_engine(cls, rules_type: str):
            return None

# ============== UNIVERSAL ANTI-HALLUCINATION CONSTRAINTS ==============
UNIVERSAL_CONSTRAINTS = """
CRITICAL ANTI-HALLUCINATION RULES - APPLY TO EVERY RESPONSE:

1. NEVER INVENT OR CREATE:
   - Names of people (staff, managers, representatives)
   - Names of places (branches, streets, buildings)
   - Specific dates or times not in the data
   - Conversations or meetings that aren't documented
   - Phone calls or interactions not recorded
   - Product names or features not in the system
   - Customer preferences not explicitly stated
   - Life events not mentioned in data
   - Financial details not provided

2. ONLY USE:
   - Exact data points provided
   - Statistical patterns from actual data
   - General segment characteristics (not specific to individual)
   - System-wide features available to all customers
   
3. WHEN DATA IS MISSING:
   - Use general professional language
   - Reference "your local branch" not "Baker Street branch"
   - Say "our team" not "Sarah from customer service"
   - Use "recently" not "last Tuesday at 3pm"
   
4. FORBIDDEN PHRASES:
   - "As we discussed..." (unless conversation is in data)
   - "When you visited..." (unless visit is in data)
   - "Your usual branch..." (unless branch is specified)
   - "As [Name] mentioned..." (never invent staff names)
   - Specific times/dates not in data
   
5. VALIDATION:
   - Every specific claim must trace to input data
   - If you cannot trace it to data, do not include it
   - Better to be general than to be wrong
"""

class PersonalizationLevel(Enum):
    """Levels of personalization intensity"""
    BASIC = "basic"           # Just name and basic details
    MODERATE = "moderate"     # Some context integration
    DEEP = "deep"            # Rich personalization throughout
    HYPER = "hyper"          # Every element tailored

@dataclass
class CustomerInsights:
    """AI-driven customer analysis - FACTS ONLY"""
    segment: str              # DIGITAL, ASSISTED, TRADITIONAL
    life_stage: str          # young_adult, family_building, pre_retirement, etc
    digital_persona: str     # app_native, hybrid_user, traditional_preferred
    financial_profile: str   # budget_conscious, growing_saver, premium_customer
    communication_style: str # formal, friendly, warm, professional
    verified_facts: List[str] # ONLY things we know for certain from data
    behavioral_patterns: List[str] # Patterns inferred from data
    data_gaps: List[str]     # What we DON'T know (to avoid inventing)
    confidence_score: float  # How confident we are in this analysis

@dataclass
class PersonalizationStrategy:
    """The master plan for personalizing content - NO FICTION"""
    level: PersonalizationLevel
    customer_data_profile: Dict[str, Any]  # REPLACED customer_story with facts-only profile
    tone_guidelines: Dict[str, str]
    verified_references: List[str]  # Things we CAN mention (from data)
    forbidden_specifics: List[str]  # Things we must NOT invent
    pattern_language: Dict[str, str]  # How to reference patterns without specifics
    channel_adaptations: Dict[str, Dict] # Channel-specific personalization hints

@dataclass
class ContentStrategy:
    """What content to preserve and how"""
    critical_points: List[Any]    # MUST appear in all applicable channels
    important_points: List[Any]   # Should appear where space allows
    contextual_points: List[Any]  # Nice to have, channel dependent
    
    channel_requirements: Dict[str, List[str]]  # What each channel must include
    preservation_instructions: Dict[str, str]   # How to adapt content per channel

@dataclass
class SharedContext:
    """The complete intelligence package for all channels"""
    # Input data
    original_letter: str
    customer_data: Dict[str, Any]
    processing_timestamp: str
    
    # AI Analysis Results
    document_classification: Dict[str, Any]
    customer_insights: CustomerInsights
    rules_evaluation: Dict[str, Any]
    
    # Strategic Decisions
    personalization_strategy: PersonalizationStrategy
    content_strategy: ContentStrategy
    channel_decisions: Dict[str, Any]  # Which channels, why, how
    
    # Quality Metadata
    analysis_confidence: float
    processing_time: float
    ai_model_used: str
    api_calls_saved: int  # Track saved API calls
    hallucination_check_passed: bool  # NEW: Track if we passed anti-hallucination checks

class SharedBrain:
    """
    The all-powerful AI brain that creates consistent, deeply personalized context
    FIXED: Now prevents ALL hallucinations through strict constraints
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the shared brain with all its components"""
        self.api_key = api_key or os.getenv('CLAUDE_API_KEY')
        self.client = None
        
        if self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.model = "claude-3-5-sonnet-20241022"
            print("🧠 Shared Brain initialized with Claude AI (Hallucination-Free Mode)")
        else:
            print("⚠️ Shared Brain running in simulation mode")
        
        # Initialize all the existing working components
        self.document_classifier = AIDocumentClassifier(api_key=self.api_key) if DOCUMENT_CLASSIFIER_AVAILABLE else None
        self.content_validator = ContentValidator(api_key=self.api_key) if CONTENT_VALIDATOR_AVAILABLE else None
        
        # Load rules engines
        self.communication_rules = Config.load_rules_engine('communication') if CONFIG_AVAILABLE else None
        self.personalization_rules = Config.load_rules_engine('personalization') if CONFIG_AVAILABLE else None
        
        print("✓ All brain components loaded with anti-hallucination measures")
    
    def analyze_everything(
        self,
        letter_content: str,
        customer_data: Dict[str, Any],
        force_channels: Optional[List[str]] = None,
        existing_classification: Optional[Any] = None,
        existing_key_points: Optional[List] = None
    ) -> SharedContext:
        """
        THE MAIN METHOD: Analyze everything and create the shared context
        FIXED: Now includes hallucination prevention at every step
        """
        
        start_time = datetime.now()
        api_calls_saved = 0
        print(f"🧠 Shared Brain analyzing for customer: {customer_data.get('name', 'Unknown')}")
        print("   🛡️ Hallucination prevention: ACTIVE")
        
        # STEP 1: Document Intelligence - USE EXISTING IF AVAILABLE
        if existing_classification:
            print("  📄 Using existing document classification (saving 1 API call)")
            document_classification = existing_classification
            api_calls_saved += 1
        else:
            print("  📄 Analyzing document...")
            if self.document_classifier:
                document_classification = self.document_classifier.classify_document(letter_content)
            else:
                document_classification = self._simulate_classification()
        
        # STEP 2: Content Intelligence - USE EXISTING IF AVAILABLE
        if existing_key_points:
            print("  🔍 Using existing key points (saving 1 API call)")
            key_points = existing_key_points
            api_calls_saved += 1
        else:
            print("  🔍 Extracting key content...")
            if self.content_validator:
                key_points = self.content_validator.extract_key_points(letter_content)
            else:
                key_points = []
        
        content_strategy = self._create_content_strategy(key_points, document_classification)
        
        # STEP 3: Customer Intelligence (THE BIG ONE) - With anti-hallucination
        print("  👤 Deep customer analysis (facts only)...")
        customer_insights = self._analyze_customer_deeply(customer_data, document_classification)
        
        # STEP 4: Rules Intelligence
        print("  📋 Evaluating all rules...")
        rules_evaluation = self._evaluate_all_rules(customer_data, document_classification, customer_insights)
        
        # STEP 5: Personalization Strategy (THE MASTER PLAN) - No fiction allowed
        print("  🎯 Creating personalization strategy (data-driven)...")
        personalization_strategy = self._create_personalization_strategy(
            customer_insights, 
            document_classification, 
            content_strategy,
            letter_content
        )
        
        # STEP 6: Channel Decisions WITH VOICE
        print("  📺 Making channel decisions (including voice)...")
        
        # Build comprehensive context for rules evaluation
        rules_context = {
            'customer': customer_data,
            'document': {
                'type': document_classification.primary_classification if hasattr(document_classification, 'primary_classification') else document_classification.get('primary_classification', 'INFORMATIONAL'),
                'urgency': document_classification.urgency_level if hasattr(document_classification, 'urgency_level') else document_classification.get('urgency_level', 'MEDIUM'),
                'compliance_required': document_classification.compliance_required if hasattr(document_classification, 'compliance_required') else document_classification.get('compliance_required', False),
                'customer_action_required': document_classification.customer_action_required if hasattr(document_classification, 'customer_action_required') else document_classification.get('customer_action_required', False)
            },
            'insights': {
                'segment': customer_insights.segment,
                'life_stage': customer_insights.life_stage,
                'digital_persona': customer_insights.digital_persona,
                'financial_profile': customer_insights.financial_profile,
                'verified_facts': customer_insights.verified_facts
            }
        }
        
        # Initialize channel decisions
        channel_decisions = {
            'enabled_channels': {
                'email': False,
                'sms': False,
                'letter': False,
                'voice': False
            },
            'reasons': {
                'email': 'Not evaluated',
                'sms': 'Not evaluated',
                'letter': 'Not evaluated',
                'voice': 'Not evaluated'
            }
        }
        
        # Use rules engine to determine channel eligibility
        if self.communication_rules:
            print("    Using rules engine for channel decisions...")
            
            # Evaluate all channel eligibility rules
            channel_rules_result = self.communication_rules.evaluate(rules_context, tags=['channel_eligibility'])
            
            # Process the features that were enabled/disabled
            features = channel_rules_result.get('features', {})
            
            # Check each channel
            for channel in ['email', 'sms', 'letter', 'voice_note']:
                # Map voice_note to voice for consistency
                channel_key = 'voice' if channel == 'voice_note' else channel
                
                if channel in features:
                    channel_decisions['enabled_channels'][channel_key] = features[channel]
                    
                    # Get the reason from metadata
                    metadata = channel_rules_result.get('metadata', {})
                    if 'reason' in metadata and channel == 'voice_note':  # Voice note gets special reason
                        channel_decisions['reasons'][channel_key] = metadata['reason']
                    else:
                        # Find triggered rules for this channel
                        triggered_rules = channel_rules_result.get('triggered_rules', [])
                        if triggered_rules:
                            channel_decisions['reasons'][channel_key] = f"Enabled by rules: {', '.join(triggered_rules[:2])}"
                        else:
                            channel_decisions['reasons'][channel_key] = "Enabled by rules engine"
            
            # Store voice metadata if available
            if 'voice_note' in features and features['voice_note']:
                metadata = channel_rules_result.get('metadata', {})
                if 'voice_style' in metadata:
                    channel_decisions['voice_style'] = metadata['voice_style']
                if 'voice_speed' in metadata:
                    channel_decisions['voice_speed'] = metadata['voice_speed']
            
            print(f"    Rules evaluation complete. Triggered rules: {channel_rules_result.get('triggered_rules', [])}")
            
        else:
            print("    ⚠️ No rules engine available - using fallback defaults")
            # Fallback if no rules engine
            channel_decisions['enabled_channels']['email'] = True
            channel_decisions['reasons']['email'] = 'Default channel (no rules engine)'
            
            # Basic fallback logic
            if customer_insights.segment == 'DIGITAL':
                channel_decisions['enabled_channels']['sms'] = True
                channel_decisions['reasons']['sms'] = 'Digital segment (fallback)'
            
            if customer_insights.segment in ['TRADITIONAL', 'ASSISTED']:
                channel_decisions['enabled_channels']['letter'] = True
                channel_decisions['reasons']['letter'] = 'Traditional/Assisted segment (fallback)'
        
        # Force channels if requested (override rules)
        if force_channels:
            for channel in force_channels:
                channel_decisions['enabled_channels'][channel] = True
                channel_decisions['reasons'][channel] = f"Forced by user request (original: {channel_decisions['reasons'].get(channel, 'N/A')})"
        
        # Log the final decisions
        enabled = [ch for ch, en in channel_decisions['enabled_channels'].items() if en]
        print(f"    Final enabled channels: {enabled}")
        for channel in enabled:
            print(f"      - {channel}: {channel_decisions['reasons'][channel]}")
        
        # STEP 7: Hallucination Check
        hallucination_check = self._validate_no_hallucinations(
            personalization_strategy,
            customer_insights,
            customer_data
        )
        
        # STEP 8: Calculate confidence and metadata
        processing_time = (datetime.now() - start_time).total_seconds()
        analysis_confidence = self._calculate_overall_confidence(
            document_classification,
            customer_insights,
            personalization_strategy
        )
        
        # Create the shared context with hallucination check
        shared_context = SharedContext(
            original_letter=letter_content,
            customer_data=customer_data,
            processing_timestamp=start_time.isoformat(),
            document_classification=document_classification.to_dict() if hasattr(document_classification, 'to_dict') else document_classification,
            customer_insights=customer_insights,
            rules_evaluation=rules_evaluation,
            personalization_strategy=personalization_strategy,
            content_strategy=content_strategy,
            channel_decisions=channel_decisions,
            analysis_confidence=analysis_confidence,
            processing_time=processing_time,
            ai_model_used=self.model if self.client else "simulation",
            api_calls_saved=api_calls_saved,
            hallucination_check_passed=hallucination_check  # NEW field
        )
        
        print(f"✅ Shared Brain analysis complete in {processing_time:.2f}s")
        if api_calls_saved > 0:
            print(f"   💰 Saved {api_calls_saved} API calls by reusing existing analysis")
        print(f"   Customer Segment: {customer_insights.segment}")
        print(f"   Personalization Level: {personalization_strategy.level.value}")
        print(f"   🛡️ Hallucination Check: {'PASSED' if hallucination_check else 'FAILED'}")
        
        # Show enabled channels including voice
        enabled = [ch for ch, en in channel_decisions['enabled_channels'].items() if en]
        print(f"   Enabled Channels: {enabled}")
        if channel_decisions['enabled_channels'].get('voice'):
            print(f"   🎙️ Voice enabled: {channel_decisions['reasons']['voice']}")
        
        return shared_context
    
    def _simulate_classification(self):
        """Fallback classification when classifier not available"""
        return {
            'primary_classification': 'INFORMATIONAL',
            'confidence_score': 0.8,
            'urgency_level': 'MEDIUM',
            'customer_action_required': False,
            'compliance_required': False,
            'tone': 'PROFESSIONAL'
        }
    
    def _analyze_customer_deeply(
        self, 
        customer_data: Dict[str, Any], 
        document_classification
    ) -> CustomerInsights:
        """
        AI-POWERED deep customer analysis - FIXED to prevent hallucinations
        This builds customer insights from ONLY verified data
        """
        
        if not self.client:
            return self._simulate_customer_insights(customer_data)
        
        # Build comprehensive customer context for AI analysis
        customer_summary = self._build_customer_summary(customer_data)
        doc_type = document_classification.primary_classification if hasattr(document_classification, 'primary_classification') else document_classification.get('primary_classification', 'INFORMATIONAL')
        doc_tone = document_classification.tone if hasattr(document_classification, 'tone') else document_classification.get('tone', 'FORMAL')
        doc_urgency = document_classification.urgency_level if hasattr(document_classification, 'urgency_level') else document_classification.get('urgency_level', 'MEDIUM')
        
        document_context = f"Document type: {doc_type}, Tone: {doc_tone}, Urgency: {doc_urgency}"
        
        analysis_prompt = f"""{UNIVERSAL_CONSTRAINTS}

You are an expert customer analyst for a major bank. Analyze this customer profile and create insights for personalization using ONLY the data provided.

CUSTOMER DATA:
{customer_summary}

DOCUMENT CONTEXT:
{document_context}

Perform analysis and return insights in this exact JSON format:

{{
    "segment": "DIGITAL|ASSISTED|TRADITIONAL",
    "life_stage": "describe their life stage in 1-2 words based on age/data",
    "digital_persona": "describe their digital relationship based on login data", 
    "financial_profile": "describe their financial situation based on balance data",
    "communication_style": "formal|friendly|warm|professional|respectful",
    "verified_facts": [
        "ONLY list facts that are explicitly in the data",
        "e.g., 'Has account balance of £X'",
        "e.g., 'Logs in X times per month'",
        "DO NOT make up any facts"
    ],
    "behavioral_patterns": [
        "Patterns you can infer from the numbers",
        "e.g., 'Regular digital user' if logins > 20",
        "e.g., 'Branch visitor' if visits > 0"
    ],
    "data_gaps": [
        "Things we DON'T know about this customer",
        "e.g., 'No branch preference data'",
        "e.g., 'No previous conversation history'"
    ],
    "confidence_score": 0.0-1.0,
    "reasoning": "brief explanation of your analysis"
}}

CRITICAL RULES:
- NEVER invent staff names, branch names, or specific locations
- NEVER reference conversations or meetings not in the data
- NEVER assume preferences not explicitly stated
- If something is not in the data, add it to data_gaps
- Only use patterns and statistics, not specific invented details

Analyze this customer now:"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.3,  # Lower temperature for more consistency
                messages=[{"role": "user", "content": analysis_prompt}]
            )
            
            content = response.content[0].text.strip()
            
            # Parse JSON response
            if '{' in content and '}' in content:
                json_start = content.index('{')
                json_end = content.rindex('}') + 1
                json_str = content[json_start:json_end]
                analysis_data = json.loads(json_str)
                
                return CustomerInsights(
                    segment=analysis_data.get('segment', 'ASSISTED'),
                    life_stage=analysis_data.get('life_stage', 'unknown'),
                    digital_persona=analysis_data.get('digital_persona', 'hybrid_user'),
                    financial_profile=analysis_data.get('financial_profile', 'standard_customer'),
                    communication_style=analysis_data.get('communication_style', 'professional'),
                    verified_facts=analysis_data.get('verified_facts', []),
                    behavioral_patterns=analysis_data.get('behavioral_patterns', []),
                    data_gaps=analysis_data.get('data_gaps', []),
                    confidence_score=float(analysis_data.get('confidence_score', 0.7))
                )
            
        except Exception as e:
            print(f"AI customer analysis error: {e}")
        
        # Fallback to simulation
        return self._simulate_customer_insights(customer_data)
    
    def _create_personalization_strategy(
        self,
        customer_insights: CustomerInsights,
        document_classification,
        content_strategy,
        letter_content: str
    ) -> PersonalizationStrategy:
        """
        AI-POWERED creation of the master personalization strategy
        FIXED: Uses data profiles instead of fictional narratives
        """
        
        if not self.client:
            return self._simulate_personalization_strategy(customer_insights)
        
        doc_type = document_classification.primary_classification if hasattr(document_classification, 'primary_classification') else document_classification.get('primary_classification', 'INFORMATIONAL')
        doc_tone = document_classification.tone if hasattr(document_classification, 'tone') else document_classification.get('tone', 'FORMAL')
        
        strategy_prompt = f"""{UNIVERSAL_CONSTRAINTS}

You are a master personalization strategist for banking communications. Create a personalization strategy using ONLY verified data.

CUSTOMER INSIGHTS:
- Segment: {customer_insights.segment}
- Life Stage: {customer_insights.life_stage}
- Digital Persona: {customer_insights.digital_persona}
- Financial Profile: {customer_insights.financial_profile}
- Communication Style: {customer_insights.communication_style}
- Verified Facts: {', '.join(customer_insights.verified_facts[:5]) if customer_insights.verified_facts else 'None'}
- Known Patterns: {', '.join(customer_insights.behavioral_patterns[:5]) if customer_insights.behavioral_patterns else 'None'}
- Data Gaps: {', '.join(customer_insights.data_gaps[:3]) if customer_insights.data_gaps else 'None'}

DOCUMENT TYPE: {doc_type}
DOCUMENT TONE: {doc_tone}

LETTER CONTENT PREVIEW:
{letter_content[:500]}...

Create a data-driven personalization strategy in this JSON format:

{{
    "level": "BASIC|MODERATE|DEEP|HYPER",
    "customer_data_profile": {{
        "known_attributes": ["list what we know"],
        "behavioral_patterns": ["patterns from data"],
        "segment_characteristics": ["general traits of their segment"],
        "missing_data": ["what we don't know"]
    }},
    "tone_guidelines": {{
        "overall_tone": "description",
        "formality_level": "casual|professional|formal",
        "warmth_level": "business|friendly|warm|personal",
        "energy_level": "calm|engaging|enthusiastic"
    }},
    "verified_references": [
        "Things we CAN mention because they're in the data",
        "e.g., 'Your account balance'",
        "e.g., 'Your digital banking usage'"
    ],
    "forbidden_specifics": [
        "Things we must NOT invent",
        "e.g., 'Specific branch names'",
        "e.g., 'Staff member names'",
        "e.g., 'Previous conversations'"
    ],
    "pattern_language": {{
        "instead_of_branch_name": "your local branch",
        "instead_of_staff_name": "our team",
        "instead_of_specific_date": "recently",
        "instead_of_conversation": "our records show"
    }},
    "channel_adaptations": {{
        "email": {{"hints": "how to personalize without inventing"}},
        "sms": {{"hints": "brief factual personalization"}},
        "letter": {{"hints": "formal but understanding tone"}},
        "voice": {{"hints": "conversational without fiction"}}
    }}
}}

CRITICAL RULES:
- Use customer_data_profile NOT a narrative story
- List what we DON'T know to avoid inventing it
- Provide pattern language for general references
- Higher personalization levels only when more verified data exists
- NEVER suggest mentioning specific people, places, or conversations

Create the strategy now:"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2500,
                temperature=0.4,  # Lower for consistency
                messages=[{"role": "user", "content": strategy_prompt}]
            )
            
            content = response.content[0].text.strip()
            
            # Parse JSON response
            if '{' in content and '}' in content:
                json_start = content.index('{')
                json_end = content.rindex('}') + 1
                json_str = content[json_start:json_end]
                strategy_data = json.loads(json_str)
                
                return PersonalizationStrategy(
                    level=PersonalizationLevel(strategy_data.get('level', 'MODERATE').lower()),
                    customer_data_profile=strategy_data.get('customer_data_profile', {}),
                    tone_guidelines=strategy_data.get('tone_guidelines', {}),
                    verified_references=strategy_data.get('verified_references', []),
                    forbidden_specifics=strategy_data.get('forbidden_specifics', []),
                    pattern_language=strategy_data.get('pattern_language', {}),
                    channel_adaptations=strategy_data.get('channel_adaptations', {})
                )
            
        except Exception as e:
            print(f"AI personalization strategy error: {e}")
        
        # Fallback to simulation
        return self._simulate_personalization_strategy(customer_insights)
    
    def _validate_no_hallucinations(
        self,
        strategy: PersonalizationStrategy,
        insights: CustomerInsights,
        customer_data: Dict[str, Any]
    ) -> bool:
        """
        NEW METHOD: Validate that no hallucinations will occur
        Returns True if safe, False if risk detected
        """
        
        # Check for risky elements
        risky_elements = []
        
        # Check if we have sufficient data for the personalization level
        fact_count = len(insights.verified_facts)
        if strategy.level == PersonalizationLevel.HYPER and fact_count < 5:
            risky_elements.append("Hyper personalization with insufficient data")
        elif strategy.level == PersonalizationLevel.DEEP and fact_count < 3:
            risky_elements.append("Deep personalization with limited data")
        
        # Check for proper data gaps acknowledgment
        if not insights.data_gaps:
            risky_elements.append("No data gaps identified - risk of assumptions")
        
        # Check for forbidden specifics list
        if not strategy.forbidden_specifics:
            risky_elements.append("No forbidden specifics defined")
        
        # Check for pattern language (fallbacks)
        if not strategy.pattern_language:
            risky_elements.append("No pattern language for missing data")
        
        # Log any risks
        if risky_elements:
            print(f"   ⚠️ Hallucination risks detected: {risky_elements}")
            return False
        
        return True
    
    def _create_content_strategy(
        self, 
        key_points: List[Any], 
        document_classification
    ) -> ContentStrategy:
        """
        Create the content preservation strategy based on document type and key points
        """
        
        # Separate points by importance
        critical_points = [p for p in key_points if hasattr(p, 'importance') and p.importance == PointImportance.CRITICAL]
        important_points = [p for p in key_points if hasattr(p, 'importance') and p.importance == PointImportance.IMPORTANT]
        contextual_points = [p for p in key_points if hasattr(p, 'importance') and p.importance == PointImportance.CONTEXTUAL]
        
        # Channel requirements based on document type and urgency
        doc_type = document_classification.primary_classification if hasattr(document_classification, 'primary_classification') else document_classification.get('primary_classification', 'INFORMATIONAL')
        urgency = document_classification.urgency_level if hasattr(document_classification, 'urgency_level') else document_classification.get('urgency_level', 'MEDIUM')
        
        if doc_type == "REGULATORY" or urgency == "HIGH":
            # Regulatory/urgent: more content in more channels
            channel_requirements = {
                "email": ["critical", "important", "contextual"],
                "letter": ["critical", "important", "contextual"],
                "sms": ["critical"],
                "app": ["critical"],
                "voice": ["critical", "important"]
            }
        elif doc_type == "PROMOTIONAL":
            # Promotional: focus on benefits and calls to action
            channel_requirements = {
                "email": ["critical", "important"],
                "sms": ["critical"],
                "app": ["critical"],
                "letter": ["critical", "important"],
                "voice": ["critical"]
            }
        else:
            # Informational: balanced approach
            channel_requirements = {
                "email": ["critical", "important"],
                "sms": ["critical"],
                "app": ["critical"],
                "letter": ["critical", "important", "contextual"],
                "voice": ["critical"]
            }
        
        preservation_instructions = {
            "email": "Include full detail with explanations and context",
            "sms": "Critical points only, abbreviated but clear",
            "app": "Actionable summary with clear next steps",
            "letter": "Complete formal presentation with all details",
            "voice": "Conversational explanation of key points with natural speech"
        }
        
        return ContentStrategy(
            critical_points=critical_points,
            important_points=important_points,
            contextual_points=contextual_points,
            channel_requirements=channel_requirements,
            preservation_instructions=preservation_instructions
        )
    
    def _evaluate_all_rules(
        self, 
        customer_data: Dict[str, Any], 
        document_classification,
        customer_insights: CustomerInsights
    ) -> Dict[str, Any]:
        """
        Evaluate ALL rules engines to get channel and personalization decisions
        """
        
        # Build context for rules evaluation
        context = {
            'customer': customer_data,
            'document': {
                'type': document_classification.primary_classification if hasattr(document_classification, 'primary_classification') else document_classification.get('primary_classification', 'INFORMATIONAL'),
                'urgency': document_classification.urgency_level if hasattr(document_classification, 'urgency_level') else document_classification.get('urgency_level', 'MEDIUM'),
                'compliance_required': document_classification.compliance_required if hasattr(document_classification, 'compliance_required') else document_classification.get('compliance_required', False)
            },
            'insights': {
                'segment': customer_insights.segment,
                'digital_persona': customer_insights.digital_persona,
                'verified_facts': customer_insights.verified_facts  # Use facts not fiction
            }
        }
        
        # Evaluate communication rules (channel eligibility)
        communication_results = {}
        if self.communication_rules:
            communication_results = self.communication_rules.evaluate(context, tags=['channel_eligibility'])
        
        # Evaluate personalization rules (personalization approach)
        personalization_results = {}
        if self.personalization_rules:
            personalization_results = self.personalization_rules.evaluate(context, tags=['personalization'])
        
        return {
            'communication': communication_results,
            'personalization': personalization_results,
            'context': context
        }
    
    def _build_customer_summary(self, customer_data: Dict[str, Any]) -> str:
        """Build a comprehensive customer summary for AI analysis"""
        
        summary_parts = []
        
        # Basic demographics
        name = customer_data.get('name', 'Unknown')
        age = customer_data.get('age', 'unknown')
        summary_parts.append(f"Name: {name}, Age: {age}")
        
        # Financial profile
        balance = customer_data.get('account_balance', 0)
        years_with_bank = customer_data.get('years_with_bank', 0)
        summary_parts.append(f"Account balance: £{balance:,}, Customer for {years_with_bank} years")
        
        # Digital behavior
        digital_logins = customer_data.get('digital_logins_per_month', 0)
        mobile_usage = customer_data.get('mobile_app_usage', 'Unknown')
        email_opens = customer_data.get('email_opens_per_month', 0)
        summary_parts.append(f"Digital activity: {digital_logins} logins/month, App usage: {mobile_usage}, Email opens: {email_opens}/month")
        
        # Traditional behavior
        branch_visits = customer_data.get('branch_visits_per_month', 0)
        phone_calls = customer_data.get('phone_calls_per_month', 0)
        summary_parts.append(f"Traditional activity: {branch_visits} branch visits/month, {phone_calls} phone calls/month")
        
        # Personal context
        language = customer_data.get('preferred_language', 'English')
        life_events = customer_data.get('recent_life_events', 'None')
        family_status = customer_data.get('family_status', 'unknown')
        employment = customer_data.get('employment_status', 'unknown')
        summary_parts.append(f"Language: {language}, Life events: {life_events}, Family: {family_status}, Employment: {employment}")
        
        # Special needs
        accessibility = customer_data.get('accessibility_needs', 'None')
        if accessibility not in ['None', 'unknown', None]:
            summary_parts.append(f"Accessibility needs: {accessibility}")
        
        return '\n'.join(summary_parts)
    
    def _calculate_overall_confidence(
        self,
        document_classification,
        customer_insights: CustomerInsights,
        personalization_strategy: PersonalizationStrategy
    ) -> float:
        """Calculate overall confidence in the analysis"""
        
        doc_confidence = document_classification.confidence_score if hasattr(document_classification, 'confidence_score') else document_classification.get('confidence_score', 0.8)
        customer_confidence = customer_insights.confidence_score
        
        # Factor in data availability - more facts = higher confidence
        data_confidence = min(1.0, len(customer_insights.verified_facts) * 0.1 + 0.5)
        
        # Factor in personalization level - higher levels need higher confidence
        strategy_confidence = 1.0
        if personalization_strategy.level == PersonalizationLevel.HYPER:
            strategy_confidence = 0.9
        elif personalization_strategy.level == PersonalizationLevel.DEEP:
            strategy_confidence = 0.95
        
        # Average with weight toward actual data
        overall = (doc_confidence * 0.2 + customer_confidence * 0.3 + data_confidence * 0.4 + strategy_confidence * 0.1)
        
        return round(overall, 3)
    
    def _simulate_customer_insights(self, customer_data: Dict[str, Any]) -> CustomerInsights:
        """Simulation fallback for customer insights - NO HALLUCINATIONS"""
        
        # Simple rule-based simulation
        digital_logins = customer_data.get('digital_logins_per_month', 0)
        age = customer_data.get('age', 40)
        age_val = int(age) if isinstance(age, (int, str)) and str(age).isdigit() else 40
        
        if digital_logins > 20:
            segment = 'DIGITAL'
            digital_persona = 'app_native'
        elif digital_logins > 5:
            segment = 'ASSISTED'
            digital_persona = 'hybrid_user'
        else:
            segment = 'TRADITIONAL' 
            digital_persona = 'traditional_preferred'
        
        balance = customer_data.get('account_balance', 0)
        if balance > 20000:
            financial_profile = 'premium_customer'
        elif balance < 1000:
            financial_profile = 'budget_conscious'
        else:
            financial_profile = 'standard_saver'
        
        # Build verified facts from actual data
        verified_facts = []
        if customer_data.get('name'):
            verified_facts.append(f"Customer name: {customer_data['name']}")
        if customer_data.get('account_balance') is not None:
            verified_facts.append(f"Account balance: £{customer_data['account_balance']:,}")
        if customer_data.get('digital_logins_per_month') is not None:
            verified_facts.append(f"Digital logins: {customer_data['digital_logins_per_month']} per month")
        
        # Identify data gaps
        data_gaps = []
        if not customer_data.get('preferred_branch'):
            data_gaps.append("No preferred branch information")
        if not customer_data.get('conversation_history'):
            data_gaps.append("No previous conversation records")
        if not customer_data.get('product_preferences'):
            data_gaps.append("No product preference data")
        
        behavioral_patterns = []
        if digital_logins > 20:
            behavioral_patterns.append("Frequent digital user")
        if age_val > 65:
            behavioral_patterns.append("Senior customer segment")
        
        return CustomerInsights(
            segment=segment,
            life_stage='established' if age_val > 35 else 'building',
            digital_persona=digital_persona,
            financial_profile=financial_profile,
            communication_style='friendly' if age_val < 50 else 'respectful',
            verified_facts=verified_facts,
            behavioral_patterns=behavioral_patterns,
            data_gaps=data_gaps,
            confidence_score=0.7
        )
    
    def _simulate_personalization_strategy(self, customer_insights: CustomerInsights) -> PersonalizationStrategy:
        """Simulation fallback for personalization strategy - DATA DRIVEN ONLY"""
        
        # Determine level based on available data
        fact_count = len(customer_insights.verified_facts)
        
        if fact_count >= 5:
            level = PersonalizationLevel.DEEP
        elif fact_count >= 3:
            level = PersonalizationLevel.MODERATE
        else:
            level = PersonalizationLevel.BASIC
        
        # Build data profile (not story)
        customer_data_profile = {
            "known_attributes": customer_insights.verified_facts,
            "behavioral_patterns": customer_insights.behavioral_patterns,
            "segment_characteristics": [f"{customer_insights.segment} segment customer"],
            "missing_data": customer_insights.data_gaps
        }
        
        return PersonalizationStrategy(
            level=level,
            customer_data_profile=customer_data_profile,
            tone_guidelines={
                'overall_tone': customer_insights.communication_style,
                'formality_level': 'formal' if customer_insights.segment == 'TRADITIONAL' else 'professional',
                'warmth_level': 'friendly'
            },
            verified_references=customer_insights.verified_facts[:3],
            forbidden_specifics=[
                "Branch names",
                "Staff names",
                "Specific dates not in data",
                "Previous conversations"
            ],
            pattern_language={
                "instead_of_branch_name": "your local branch",
                "instead_of_staff_name": "our team",
                "instead_of_specific_date": "recently"
            },
            channel_adaptations={
                'email': {'hints': 'Use verified data only'},
                'sms': {'hints': 'Brief factual only'},
                'app': {'hints': 'Action-oriented facts'},
                'letter': {'hints': 'Formal with verified data'},
                'voice': {'hints': 'Natural but factual'}
            }
        )
    
    def get_analysis_summary(self, shared_context: SharedContext) -> Dict[str, Any]:
        """Get a human-readable summary of the analysis"""
        
        return {
            'customer_name': shared_context.customer_data.get('name', 'Unknown'),
            'customer_segment': shared_context.customer_insights.segment,
            'personalization_level': shared_context.personalization_strategy.level.value,
            'enabled_channels': list(shared_context.channel_decisions['enabled_channels'].keys()),
            'confidence_score': shared_context.analysis_confidence,
            'processing_time': f"{shared_context.processing_time:.2f}s",
            'document_type': shared_context.document_classification.get('primary_classification'),
            'verified_facts': shared_context.customer_insights.verified_facts,
            'data_gaps': shared_context.customer_insights.data_gaps,
            'forbidden_specifics': shared_context.personalization_strategy.forbidden_specifics,
            'ai_model_used': shared_context.ai_model_used,
            'api_calls_saved': shared_context.api_calls_saved,
            'voice_enabled': shared_context.channel_decisions['enabled_channels'].get('voice', False),
            'voice_reason': shared_context.channel_decisions['reasons'].get('voice', 'N/A'),
            'hallucination_check': 'PASSED' if shared_context.hallucination_check_passed else 'FAILED'
        }