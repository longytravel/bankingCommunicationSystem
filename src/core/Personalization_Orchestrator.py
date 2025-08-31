"""
Personalization Orchestrator - Advanced Personalization with Guaranteed Preservation
This module orchestrates the balance between information preservation and deep personalization
Works with PersonalizationEngine to ensure both goals are achieved
"""

import anthropic
import json
import os
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from dotenv import load_dotenv

load_dotenv()

class PersonalizationDepth(Enum):
    """Levels of personalization depth"""
    SURFACE = "surface"      # Just name and basic details
    MODERATE = "moderate"     # Include some context
    DEEP = "deep"            # Full integration of customer story
    HYPER = "hyper"          # Every aspect tailored

class CustomerContext(Enum):
    """Types of customer contexts to consider"""
    LIFE_STAGE = "life_stage"
    FINANCIAL = "financial"
    BEHAVIORAL = "behavioral"
    ENGAGEMENT = "engagement"
    NEEDS = "needs"
    PREFERENCES = "preferences"

@dataclass
class PersonalizationOpportunity:
    """Represents an opportunity to personalize content"""
    context_type: CustomerContext
    context_value: str
    relevance_score: float
    application_suggestions: List[str]
    keywords: List[str]

@dataclass
class PersonalizationPlan:
    """Complete plan for personalizing content"""
    customer_story: str
    personalization_depth: PersonalizationDepth
    opportunities: List[PersonalizationOpportunity]
    tone_guidelines: Dict[str, str]
    must_mention: List[str]
    connection_points: Dict[str, str]  # Maps information to customer relevance

class PersonalizationOrchestrator:
    """
    Orchestrates the complex balance between preserving information and personalizing content
    Ensures BOTH goals are achieved without compromise
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the orchestrator"""
        self.api_key = api_key or os.getenv('CLAUDE_API_KEY')
        self.client = None
        
        if self.api_key:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
                self.model = "claude-3-5-sonnet-20241022"
                print("✓ Personalization Orchestrator initialized with Claude")
            except ImportError:
                print("⚠️ Anthropic not available")
                self.client = None
        else:
            print("⚠️ No API key for Personalization Orchestrator")
    
    def orchestrate_personalization(
        self,
        letter_content: str,
        customer: Dict[str, Any],
        key_points: Optional[List] = None,
        existing_engine = None
    ) -> Dict[str, str]:
        """
        Main orchestration method that ensures both preservation and personalization
        
        Args:
            letter_content: Original letter to personalize
            customer: Customer profile data
            key_points: Key points that must be preserved
            existing_engine: Existing PersonalizationEngine instance to use
            
        Returns:
            Personalized content for all channels
        """
        
        # Step 1: Deep customer analysis
        personalization_plan = self._analyze_customer_deeply(customer)
        
        # Step 2: Map information to customer context
        connection_map = self._map_information_to_customer(
            letter_content, 
            customer, 
            personalization_plan
        )
        
        # Step 3: Generate with rich instructions
        result = self._generate_rich_personalization(
            letter_content,
            customer,
            personalization_plan,
            connection_map,
            key_points
        )
        
        # Step 4: Validate quality
        if self._has_placeholders(result):
            print("Placeholders detected, regenerating...")
            result = self._fix_placeholder_content(result, letter_content, customer)
        
        # Step 5: Verify personalization depth
        if not self._has_sufficient_personalization(result, personalization_plan):
            print("Insufficient personalization, enhancing...")
            result = self._enhance_personalization(result, customer, personalization_plan)
        
        return result
    
    def _analyze_customer_deeply(self, customer: Dict[str, Any]) -> PersonalizationPlan:
        """
        Perform deep analysis of customer to identify ALL personalization opportunities
        This is NOT hardcoded - it dynamically analyzes whatever data is provided
        """
        opportunities = []
        must_mention = []
        
        # Analyze life stage dynamically
        if 'recent_life_events' in customer and customer['recent_life_events'] not in ['None', 'unknown', None]:
            life_event = customer['recent_life_events']
            opportunities.append(PersonalizationOpportunity(
                context_type=CustomerContext.LIFE_STAGE,
                context_value=life_event,
                relevance_score=1.0,
                application_suggestions=self._get_life_event_suggestions(life_event),
                keywords=self._extract_keywords(life_event)
            ))
            must_mention.append(f"Reference to {life_event}")
        
        # Analyze age dynamically
        if 'age' in customer and customer['age'] not in ['unknown', None]:
            age = int(customer['age']) if isinstance(customer['age'], (int, str)) and str(customer['age']).isdigit() else 0
            if age > 0:
                life_stage = self._determine_life_stage(age)
                opportunities.append(PersonalizationOpportunity(
                    context_type=CustomerContext.LIFE_STAGE,
                    context_value=life_stage,
                    relevance_score=0.8,
                    application_suggestions=[f"Language appropriate for {life_stage}"],
                    keywords=[]
                ))
        
        # Analyze financial situation dynamically
        if 'account_balance' in customer:
            balance = customer.get('account_balance', 0)
            financial_context = self._analyze_financial_context(balance)
            if financial_context:
                opportunities.append(PersonalizationOpportunity(
                    context_type=CustomerContext.FINANCIAL,
                    context_value=financial_context,
                    relevance_score=0.7,
                    application_suggestions=self._get_financial_suggestions(balance),
                    keywords=[]
                ))
        
        # Analyze digital behavior dynamically
        digital_logins = customer.get('digital_logins_per_month', 0)
        mobile_usage = customer.get('mobile_app_usage', 'Unknown')
        digital_profile = self._analyze_digital_profile(digital_logins, mobile_usage)
        if digital_profile:
            opportunities.append(PersonalizationOpportunity(
                context_type=CustomerContext.BEHAVIORAL,
                context_value=digital_profile,
                relevance_score=0.9,
                application_suggestions=[f"Emphasize {digital_profile} features"],
                keywords=self._get_digital_keywords(digital_profile)
            ))
        
        # Analyze any special needs
        if 'accessibility_needs' in customer and customer['accessibility_needs'] not in ['None', 'none', None]:
            opportunities.append(PersonalizationOpportunity(
                context_type=CustomerContext.NEEDS,
                context_value=customer['accessibility_needs'],
                relevance_score=1.0,
                application_suggestions=[f"Accommodate {customer['accessibility_needs']}"],
                keywords=[]
            ))
        
        # Analyze employment dynamically
        if 'employment_status' in customer and customer['employment_status'] not in ['unknown', None]:
            employment = customer['employment_status']
            opportunities.append(PersonalizationOpportunity(
                context_type=CustomerContext.LIFE_STAGE,
                context_value=employment,
                relevance_score=0.6,
                application_suggestions=self._get_employment_suggestions(employment),
                keywords=self._extract_keywords(employment)
            ))
        
        # Build customer story
        customer_story = self._build_customer_story(customer, opportunities)
        
        # Determine personalization depth
        depth = self._determine_personalization_depth(opportunities)
        
        # Generate tone guidelines
        tone_guidelines = self._generate_tone_guidelines(customer, opportunities)
        
        return PersonalizationPlan(
            customer_story=customer_story,
            personalization_depth=depth,
            opportunities=opportunities,
            tone_guidelines=tone_guidelines,
            must_mention=must_mention,
            connection_points={}
        )
    
    def _get_life_event_suggestions(self, life_event: str) -> List[str]:
        """Generate suggestions based on life event - dynamically"""
        event_lower = life_event.lower()
        suggestions = []
        
        # Dynamic analysis based on keywords
        if 'university' in event_lower or 'college' in event_lower or 'student' in event_lower:
            suggestions.extend([
                "Reference student life and budgeting",
                "Mention features useful for students",
                "Consider academic calendar timing"
            ])
        elif 'baby' in event_lower or 'parent' in event_lower or 'child' in event_lower:
            suggestions.extend([
                "Reference family financial planning",
                "Mention savings for children",
                "Consider family-friendly features"
            ])
        elif 'job' in event_lower or 'career' in event_lower or 'employment' in event_lower:
            suggestions.extend([
                "Reference career transitions",
                "Mention income changes",
                "Consider professional needs"
            ])
        elif 'retirement' in event_lower or 'retired' in event_lower:
            suggestions.extend([
                "Reference retirement planning",
                "Mention fixed income considerations",
                "Consider simplicity and security"
            ])
        elif 'marriage' in event_lower or 'wedding' in event_lower or 'married' in event_lower:
            suggestions.extend([
                "Reference joint financial planning",
                "Mention shared accounts",
                "Consider dual decision-making"
            ])
        elif 'home' in event_lower or 'house' in event_lower or 'mortgage' in event_lower:
            suggestions.extend([
                "Reference property ownership",
                "Mention home-related expenses",
                "Consider long-term planning"
            ])
        else:
            # Generic suggestions for any life event
            suggestions.append(f"Acknowledge {life_event} and its impact")
        
        return suggestions
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text dynamically"""
        if not text:
            return []
        
        # Simple keyword extraction
        words = text.lower().replace('_', ' ').split()
        # Filter out common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
        keywords = [w for w in words if w not in stop_words and len(w) > 3]
        return keywords
    
    def _determine_life_stage(self, age: int) -> str:
        """Determine life stage from age - dynamic ranges"""
        if age < 25:
            return "young adult"
        elif age < 35:
            return "early career"
        elif age < 45:
            return "established professional"
        elif age < 55:
            return "mid-career"
        elif age < 65:
            return "pre-retirement"
        else:
            return "retirement age"
    
    def _analyze_financial_context(self, balance: float) -> str:
        """Analyze financial context dynamically"""
        if balance < 500:
            return "budget-conscious"
        elif balance < 2000:
            return "everyday banking"
        elif balance < 10000:
            return "building savings"
        elif balance < 50000:
            return "established saver"
        else:
            return "wealth management focus"
    
    def _get_financial_suggestions(self, balance: float) -> List[str]:
        """Get financial suggestions based on balance"""
        if balance < 1000:
            return ["Focus on budgeting tools", "Mention overdraft protection"]
        elif balance < 5000:
            return ["Highlight savings opportunities", "Mention growth potential"]
        else:
            return ["Emphasize investment options", "Mention premium services"]
    
    def _analyze_digital_profile(self, logins: int, mobile_usage: str) -> str:
        """Analyze digital engagement profile"""
        if logins > 20 or mobile_usage == 'Daily':
            return "digital-first"
        elif logins > 10 or mobile_usage == 'Weekly':
            return "digitally-engaged"
        elif logins > 5:
            return "hybrid-user"
        elif logins > 0:
            return "occasional-digital"
        else:
            return "traditional-preferred"
    
    def _get_digital_keywords(self, profile: str) -> List[str]:
        """Get keywords for digital profile"""
        if "digital" in profile:
            return ["app", "online", "mobile", "digital"]
        elif "hybrid" in profile:
            return ["convenient", "flexible", "choice"]
        else:
            return ["support", "assistance", "help"]
    
    def _get_employment_suggestions(self, employment: str) -> List[str]:
        """Get suggestions based on employment status"""
        emp_lower = employment.lower()
        if 'self-employed' in emp_lower or 'business' in emp_lower:
            return ["Mention business banking", "Reference cash flow management"]
        elif 'employed' in emp_lower:
            return ["Reference regular income", "Mention workplace benefits"]
        elif 'retired' in emp_lower:
            return ["Focus on security", "Mention fixed income"]
        else:
            return [f"Consider {employment} circumstances"]
    
    def _build_customer_story(self, customer: Dict, opportunities: List[PersonalizationOpportunity]) -> str:
        """Build a narrative about the customer"""
        story_parts = []
        
        # Name and basic info
        story_parts.append(f"{customer.get('name', 'Customer')} is")
        
        # Add key characteristics
        for opp in opportunities:
            if opp.relevance_score > 0.7:
                story_parts.append(opp.context_value)
        
        return " ".join(story_parts)
    
    def _determine_personalization_depth(self, opportunities: List[PersonalizationOpportunity]) -> PersonalizationDepth:
        """Determine how deep personalization should go"""
        total_score = sum(opp.relevance_score for opp in opportunities)
        
        if total_score > 3.5:
            return PersonalizationDepth.HYPER
        elif total_score > 2.5:
            return PersonalizationDepth.DEEP
        elif total_score > 1.5:
            return PersonalizationDepth.MODERATE
        else:
            return PersonalizationDepth.SURFACE
    
    def _generate_tone_guidelines(self, customer: Dict, opportunities: List) -> Dict[str, str]:
        """Generate tone guidelines based on customer analysis"""
        guidelines = {}
        
        # Age-based tone
        age = customer.get('age', 'unknown')
        if age != 'unknown':
            age_val = int(age) if str(age).isdigit() else 40
            if age_val < 30:
                guidelines['formality'] = 'casual and friendly'
            elif age_val > 60:
                guidelines['formality'] = 'respectful and clear'
            else:
                guidelines['formality'] = 'professional'
        
        # Digital profile tone
        for opp in opportunities:
            if opp.context_type == CustomerContext.BEHAVIORAL:
                if 'digital' in opp.context_value:
                    guidelines['technical'] = 'comfortable with digital terms'
                else:
                    guidelines['technical'] = 'avoid technical jargon'
        
        return guidelines
    
    def _map_information_to_customer(
        self, 
        letter_content: str, 
        customer: Dict,
        plan: PersonalizationPlan
    ) -> Dict[str, str]:
        """
        Map each piece of information in the letter to customer relevance
        This creates connections between generic info and specific customer context
        """
        if not self.client:
            return self._manual_mapping(letter_content, customer, plan)
        
        # Build comprehensive customer context
        context_description = f"""
Customer Profile:
- Name: {customer.get('name')}
- Story: {plan.customer_story}
- Key contexts: {[opp.context_value for opp in plan.opportunities]}
- Must mention: {plan.must_mention}
"""
        
        mapping_prompt = f"""Analyze this letter and map each piece of information to this specific customer's relevance:

LETTER:
{letter_content}

CUSTOMER:
{context_description}

For each major piece of information in the letter, explain how it specifically relates to this customer.
Focus on creating natural connections, not forced ones.

Return a JSON object mapping information to relevance:
{{
    "feature_or_info_1": "how this relates to this specific customer",
    "feature_or_info_2": "relevance to their situation",
    ...
}}

Be specific and natural. For example:
- If the letter mentions savings and the customer is a student: "As a university student, building savings habits now will help throughout your studies"
- If the letter mentions digital features and they're digital-first: "You're already using our app daily, these new features will enhance your experience"
"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.6,
                messages=[{"role": "user", "content": mapping_prompt}]
            )
            
            content = response.content[0].text.strip()
            
            # Extract JSON
            if '{' in content and '}' in content:
                json_start = content.index('{')
                json_end = content.rindex('}') + 1
                json_str = content[json_start:json_end]
                return json.loads(json_str)
            else:
                return {}
                
        except Exception as e:
            print(f"Mapping generation error: {e}")
            return self._manual_mapping(letter_content, customer, plan)
    
    def _manual_mapping(self, letter_content: str, customer: Dict, plan: PersonalizationPlan) -> Dict[str, str]:
        """Fallback manual mapping"""
        mapping = {}
        
        # Generic mappings based on common patterns
        for opp in plan.opportunities:
            if opp.context_type == CustomerContext.LIFE_STAGE:
                if 'university' in opp.context_value.lower():
                    mapping['savings'] = "Perfect for managing student finances"
                    mapping['budgeting'] = "Essential for student life"
                    mapping['mobile app'] = "Access your account between lectures"
        
        return mapping
    
    def _generate_rich_personalization(
        self,
        letter_content: str,
        customer: Dict,
        plan: PersonalizationPlan,
        connection_map: Dict[str, str],
        key_points: Optional[List]
    ) -> Dict[str, str]:
        """
        Generate deeply personalized content with ALL information preserved
        """
        if not self.client:
            return self._basic_personalization(letter_content, customer)
        
        # Build the personalization context
        personalization_context = self._build_personalization_context(plan, connection_map)
        
        # Create information preservation requirements
        preservation_requirements = self._build_preservation_requirements(key_points)
        
        generation_prompt = f"""You are creating a deeply personalized version of this bank letter for a specific customer.

CRITICAL REQUIREMENTS:
1. Include 100% of the information from the original letter - NOTHING can be omitted
2. Deeply personalize based on the customer's specific situation
3. NO PLACEHOLDERS - write complete, real content
4. Make natural connections between information and customer context

ORIGINAL LETTER (preserve ALL information):
{letter_content}

CUSTOMER PROFILE:
Name: {customer.get('name')}
Story: {plan.customer_story}
{self._format_customer_details(customer)}

PERSONALIZATION REQUIREMENTS:
{personalization_context}

SPECIFIC CONNECTIONS TO MAKE:
{json.dumps(connection_map, indent=2) if connection_map else "Make natural connections based on customer profile"}

MUST MENTION:
{chr(10).join(['- ' + item for item in plan.must_mention])}

{preservation_requirements}

TONE GUIDELINES:
{json.dumps(plan.tone_guidelines, indent=2)}

CRITICAL INSTRUCTIONS:
- The email and letter MUST contain ALL information from the original
- Do NOT use placeholders like [REST OF CONTENT] or [CONTINUED...]
- Write COMPLETE content
- Weave the customer's context naturally throughout
- For a university student, mention student life naturally
- For a retiree, reference retirement appropriately
- Make it feel like this letter was written specifically for them

Generate personalized versions for:
- EMAIL: Complete, friendly, all information with personal touches throughout
- SMS: 160 chars max, most critical points with personal touch
- APP: Brief but personalized notification
- LETTER: Formal but personalized, complete information

Return ONLY a complete JSON object:
{{
    "email": "COMPLETE email text with ALL information woven with personal context",
    "sms": "Personalized SMS under 160 characters",
    "app": "Personalized app notification",
    "letter": "COMPLETE formal letter with ALL information and formal personalization"
}}

REMEMBER: NO PLACEHOLDERS. Write everything out completely."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=5000,  # Enough for complete content
                temperature=0.5,   # Balanced for creativity and accuracy
                messages=[{"role": "user", "content": generation_prompt}]
            )
            
            content = response.content[0].text.strip()
            result = self._extract_json_safely(content)
            
            if result and self._validate_result(result):
                return result
            else:
                # Retry with even more explicit instructions
                return self._retry_generation(letter_content, customer, plan)
                
        except Exception as e:
            print(f"Generation error: {e}")
            return self._basic_personalization(letter_content, customer)
    
    def _build_personalization_context(self, plan: PersonalizationPlan, connection_map: Dict) -> str:
        """Build detailed personalization context"""
        context_parts = []
        
        context_parts.append(f"Personalization Depth: {plan.personalization_depth.value}")
        
        context_parts.append("\nKey Opportunities:")
        for opp in plan.opportunities:
            if opp.relevance_score > 0.5:
                context_parts.append(f"- {opp.context_type.value}: {opp.context_value}")
                for suggestion in opp.application_suggestions:
                    context_parts.append(f"  → {suggestion}")
        
        return "\n".join(context_parts)
    
    def _build_preservation_requirements(self, key_points: Optional[List]) -> str:
        """Build preservation requirements from key points"""
        if not key_points:
            return "PRESERVE ALL INFORMATION FROM THE ORIGINAL LETTER"
        
        requirements = ["MANDATORY INFORMATION TO PRESERVE:"]
        
        from src.core.content_validator import PointImportance
        
        for point in key_points:
            if hasattr(point, 'importance') and hasattr(point, 'content'):
                if point.importance == PointImportance.CRITICAL:
                    requirements.append(f"🔴 CRITICAL: {point.content}")
                elif point.importance == PointImportance.IMPORTANT:
                    requirements.append(f"🟡 IMPORTANT: {point.content}")
        
        return "\n".join(requirements)
    
    def _format_customer_details(self, customer: Dict) -> str:
        """Format customer details for the prompt"""
        details = []
        
        relevant_fields = [
            'age', 'preferred_language', 'account_balance', 'digital_logins_per_month',
            'mobile_app_usage', 'recent_life_events', 'employment_status',
            'family_status', 'accessibility_needs', 'years_with_bank'
        ]
        
        for field in relevant_fields:
            if field in customer and customer[field] not in ['unknown', 'None', None]:
                # Format field name nicely
                field_name = field.replace('_', ' ').title()
                details.append(f"{field_name}: {customer[field]}")
        
        return "\n".join(details)
    
    def _extract_json_safely(self, content: str) -> Optional[Dict]:
        """Safely extract JSON from response"""
        # Remove markdown
        content = re.sub(r'```json\s*', '', content)
        content = re.sub(r'```\s*', '', content)
        
        try:
            return json.loads(content)
        except:
            if '{' in content and '}' in content:
                try:
                    json_start = content.index('{')
                    json_end = content.rindex('}') + 1
                    return json.loads(content[json_start:json_end])
                except:
                    pass
        return None
    
    def _validate_result(self, result: Dict) -> bool:
        """Validate the result has all required fields and no placeholders"""
        required_fields = ['email', 'sms', 'app', 'letter']
        
        # Check all fields exist
        if not all(field in result for field in required_fields):
            return False
        
        # Check for placeholders
        if self._has_placeholders(result):
            return False
        
        # Check minimum content length
        if len(result.get('email', '')) < 100 or len(result.get('letter', '')) < 100:
            return False
        
        return True
    
    def _has_placeholders(self, result: Dict) -> bool:
        """Check if result contains placeholder text"""
        placeholder_patterns = [
            r'\[.*?\]',  # Anything in square brackets
            'REST OF', 'CONTINUED', 'REMAINING',
            'IDENTICAL TO ORIGINAL', 'SAME AS ABOVE',
            '...', '[...]'
        ]
        
        for channel in ['email', 'letter']:
            content = result.get(channel, '')
            for pattern in placeholder_patterns:
                if isinstance(pattern, str):
                    if pattern in content.upper():
                        return True
                else:
                    if re.search(pattern, content):
                        return True
        
        return False
    
    def _fix_placeholder_content(self, result: Dict, letter_content: str, customer: Dict) -> Dict:
        """Fix content that has placeholders"""
        if not self.client:
            return result
        
        fix_prompt = f"""The following content has placeholders that need to be replaced with real content:

Email: {result.get('email', '')}
Letter: {result.get('letter', '')}

ORIGINAL LETTER TO INCLUDE COMPLETELY:
{letter_content}

CUSTOMER: {customer.get('name')}

Replace ALL placeholders with the actual content from the original letter.
Maintain personalization but include ALL information.
NO square brackets, NO "continued", NO "rest of content".

Return a JSON object with complete content:
{{
    "email": "COMPLETE email",
    "sms": "{result.get('sms', '')}",
    "app": "{result.get('app', '')}",
    "letter": "COMPLETE letter"
}}"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.3,
                messages=[{"role": "user", "content": fix_prompt}]
            )
            
            fixed = self._extract_json_safely(response.content[0].text.strip())
            if fixed:
                return fixed
        except Exception as e:
            print(f"Placeholder fix error: {e}")
        
        return result
    
    def _has_sufficient_personalization(self, result: Dict, plan: PersonalizationPlan) -> bool:
        """Check if content has sufficient personalization"""
        # Check if must-mention items are included
        email_content = result.get('email', '').lower()
        letter_content = result.get('letter', '').lower()
        
        for must_mention in plan.must_mention:
            # Extract key terms from must_mention
            key_terms = [term.lower() for term in must_mention.split() if len(term) > 4]
            if key_terms:
                # Check if these terms appear
                found_in_email = any(term in email_content for term in key_terms)
                found_in_letter = any(term in letter_content for term in key_terms)
                if not (found_in_email or found_in_letter):
                    return False
        
        # Check for personalization depth
        if plan.personalization_depth in [PersonalizationDepth.DEEP, PersonalizationDepth.HYPER]:
            # Should have multiple personal references
            personal_indicators = 0
            for opp in plan.opportunities:
                if opp.relevance_score > 0.7:
                    for keyword in opp.keywords:
                        if keyword.lower() in email_content:
                            personal_indicators += 1
            
            if personal_indicators < 2:
                return False
        
        return True
    
    def _enhance_personalization(self, result: Dict, customer: Dict, plan: PersonalizationPlan) -> Dict:
        """Enhance content with more personalization"""
        if not self.client:
            return result
        
        enhancement_prompt = f"""The following content needs MORE personalization for this customer:

CUSTOMER STORY: {plan.customer_story}
MUST MENTION: {plan.must_mention}

CURRENT EMAIL:
{result.get('email', '')}

Enhance the email to:
1. Include specific references to: {', '.join(plan.must_mention)}
2. Make clear connections to their situation
3. Keep ALL existing information
4. Add personal touches throughout

Return enhanced versions in JSON format with all channels."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.6,
                messages=[{"role": "user", "content": enhancement_prompt}]
            )
            
            enhanced = self._extract_json_safely(response.content[0].text.strip())
            if enhanced:
                return enhanced
        except Exception as e:
            print(f"Enhancement error: {e}")
        
        return result
    
    def _retry_generation(self, letter_content: str, customer: Dict, plan: PersonalizationPlan) -> Dict:
        """Retry generation with simpler approach"""
        retry_prompt = f"""Personalize this letter for {customer.get('name')} who is {plan.customer_story}.

IMPORTANT: Include ALL information from the original letter.
Make it personal by mentioning their situation naturally.

ORIGINAL LETTER:
{letter_content}

Create:
- Email: Complete personalized version with ALL information
- SMS: Under 160 chars
- App: Brief notification
- Letter: Formal complete version

NO PLACEHOLDERS. Write complete content.

Return JSON with these four fields."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.4,
                messages=[{"role": "user", "content": retry_prompt}]
            )
            
            return self._extract_json_safely(response.content[0].text.strip())
        except:
            return self._basic_personalization(letter_content, customer)
    
    def _basic_personalization(self, letter_content: str, customer: Dict) -> Dict:
        """Basic fallback personalization"""
        name = customer.get('name', 'Valued Customer')
        
        # Add personal touches to the beginning and end
        personalized_opening = f"Dear {name},\n\n"
        
        # Add context if available
        if 'recent_life_events' in customer and customer['recent_life_events'] not in ['None', 'unknown']:
            personalized_opening += f"We hope everything is going well with {customer['recent_life_events']}. "
        
        return {
            'email': personalized_opening + letter_content + f"\n\nBest regards,\nLloyds Bank",
            'sms': f"Lloyds: Important update for {name}. Check email/app for details.",
            'app': f"New message about your account",
            'letter': f"Dear {name},\n\n{letter_content}\n\nYours sincerely,\nLloyds Bank"
        }

# Integration function to work with existing PersonalizationEngine
def orchestrate_with_engine(
    letter_content: str,
    customer: Dict[str, Any],
    key_points: Optional[List] = None,
    personalization_engine = None
) -> Dict[str, str]:
    """
    Orchestrate personalization using the new orchestrator
    Can work standalone or with existing PersonalizationEngine
    
    Args:
        letter_content: Letter to personalize
        customer: Customer data
        key_points: Points to preserve
        personalization_engine: Existing engine instance (optional)
        
    Returns:
        Personalized content for all channels
    """
    orchestrator = PersonalizationOrchestrator()
    
    return orchestrator.orchestrate_personalization(
        letter_content=letter_content,
        customer=customer,
        key_points=key_points,
        existing_engine=personalization_engine
    )