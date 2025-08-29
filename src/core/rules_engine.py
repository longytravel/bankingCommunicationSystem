"""
Rules Engine Module - Flexible Business Rules Evaluation
Handles all business logic through configurable rules
"""

import json
import operator
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
from enum import Enum

class RuleOperator(Enum):
    """Supported rule operators"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    LESS_THAN = "less_than"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"
    BETWEEN = "between"
    REGEX = "regex"
    IS_TRUE = "is_true"
    IS_FALSE = "is_false"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"

class RuleAction(Enum):
    """Supported rule actions"""
    ENABLE = "enable"
    DISABLE = "disable"
    SET_VALUE = "set_value"
    ADD_TAG = "add_tag"
    REMOVE_TAG = "remove_tag"
    TRIGGER_FUNCTION = "trigger_function"
    LOG = "log"

class Rule:
    """Individual rule definition"""
    
    def __init__(self, rule_dict: Dict[str, Any]):
        self.id = rule_dict.get('id', 'unnamed_rule')
        self.name = rule_dict.get('name', '')
        self.description = rule_dict.get('description', '')
        self.enabled = rule_dict.get('enabled', True)
        self.priority = rule_dict.get('priority', 100)
        self.conditions = rule_dict.get('conditions', [])
        self.actions = rule_dict.get('actions', [])
        self.tags = rule_dict.get('tags', [])
        
    def evaluate_conditions(self, context: Dict[str, Any]) -> bool:
        """Evaluate all conditions for this rule"""
        if not self.conditions:
            return True
            
        # Get logical operator (AND/OR)
        logic = self.conditions.get('logic', 'AND')
        rules = self.conditions.get('rules', [])
        
        if logic == 'AND':
            return all(self._evaluate_single_condition(cond, context) for cond in rules)
        elif logic == 'OR':
            return any(self._evaluate_single_condition(cond, context) for cond in rules)
        else:
            return False
    
    def _evaluate_single_condition(self, condition: Dict, context: Dict) -> bool:
        """Evaluate a single condition"""
        field = condition.get('field')
        operator_str = condition.get('operator')
        value = condition.get('value')
        
        # Get the actual value from context using dot notation
        actual_value = self._get_nested_value(context, field)
        
        # Get operator function
        operator_func = self._get_operator_function(operator_str)
        
        if operator_func:
            return operator_func(actual_value, value)
        
        return False
    
    def _get_nested_value(self, context: Dict, path: str) -> Any:
        """Get nested value from context using dot notation"""
        if not path:
            return None
            
        keys = path.split('.')
        value = context
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
                
        return value
    
    def _get_operator_function(self, operator_str: str) -> Optional[Callable]:
        """Get the operator function for evaluation"""
        operators = {
            'equals': lambda a, b: a == b,
            'not_equals': lambda a, b: a != b,
            'greater_than': lambda a, b: float(a) > float(b) if a is not None else False,
            'greater_than_or_equal': lambda a, b: float(a) >= float(b) if a is not None else False,
            'less_than': lambda a, b: float(a) < float(b) if a is not None else False,
            'less_than_or_equal': lambda a, b: float(a) <= float(b) if a is not None else False,
            'contains': lambda a, b: b in str(a) if a is not None else False,
            'not_contains': lambda a, b: b not in str(a) if a is not None else False,
            'in': lambda a, b: a in b if isinstance(b, list) else False,
            'not_in': lambda a, b: a not in b if isinstance(b, list) else False,
            'between': lambda a, b: b[0] <= float(a) <= b[1] if a is not None and isinstance(b, list) and len(b) == 2 else False,
            'is_true': lambda a, b: bool(a) is True,
            'is_false': lambda a, b: bool(a) is False,
            'is_null': lambda a, b: a is None,
            'is_not_null': lambda a, b: a is not None,
        }
        
        return operators.get(operator_str)

class RulesEngine:
    """Main rules engine for evaluating business rules"""
    
    def __init__(self, rules_file: Optional[str] = None):
        self.rules: List[Rule] = []
        self.rule_results: List[Dict] = []
        self.callbacks: Dict[str, Callable] = {}
        
        if rules_file:
            self.load_rules(rules_file)
    
    def load_rules(self, rules_file: str):
        """Load rules from JSON file"""
        path = Path(rules_file)
        if path.exists():
            with open(path, 'r') as f:
                rules_data = json.load(f)
                self.rules = [Rule(r) for r in rules_data.get('rules', [])]
                # Sort by priority (lower number = higher priority)
                self.rules.sort(key=lambda x: x.priority)
        else:
            print(f"Warning: Rules file {rules_file} not found")
    
    def register_callback(self, action_name: str, callback: Callable):
        """Register a callback function for custom actions"""
        self.callbacks[action_name] = callback
    
    def evaluate(self, context: Dict[str, Any], tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Evaluate all rules against the context
        
        Args:
            context: Dictionary containing all data for evaluation
            tags: Optional list of tags to filter rules
            
        Returns:
            Dictionary containing evaluation results and actions to perform
        """
        results = {
            'evaluated_rules': [],
            'triggered_rules': [],
            'actions': [],
            'features': {},
            'metadata': {}
        }
        
        for rule in self.rules:
            # Skip disabled rules
            if not rule.enabled:
                continue
            
            # Filter by tags if specified
            if tags and not any(tag in rule.tags for tag in tags):
                continue
            
            # Evaluate rule conditions
            if rule.evaluate_conditions(context):
                results['triggered_rules'].append(rule.id)
                
                # Process actions
                for action in rule.actions:
                    self._process_action(action, context, results)
            
            results['evaluated_rules'].append(rule.id)
        
        return results
    
    def _process_action(self, action: Dict, context: Dict, results: Dict):
        """Process a rule action"""
        action_type = action.get('type')
        
        if action_type == 'enable':
            feature = action.get('feature')
            results['features'][feature] = True
            
        elif action_type == 'disable':
            feature = action.get('feature')
            results['features'][feature] = False
            
        elif action_type == 'set_value':
            key = action.get('key')
            value = action.get('value')
            results['metadata'][key] = value
            
        elif action_type == 'add_tag':
            tag = action.get('tag')
            if 'tags' not in results:
                results['tags'] = []
            results['tags'].append(tag)
            
        elif action_type == 'trigger_function':
            function_name = action.get('function')
            params = action.get('params', {})
            
            if function_name in self.callbacks:
                callback_result = self.callbacks[function_name](context, params)
                results['actions'].append({
                    'type': 'function',
                    'name': function_name,
                    'result': callback_result
                })
        
        results['actions'].append(action)
    
    def check_feature(self, feature_name: str, context: Dict[str, Any]) -> bool:
        """
        Quick check if a feature should be enabled for given context
        
        Args:
            feature_name: Name of the feature to check
            context: Customer/situation context
            
        Returns:
            Boolean indicating if feature should be enabled
        """
        results = self.evaluate(context)
        return results.get('features', {}).get(feature_name, False)
    
    def get_applicable_rules(self, context: Dict[str, Any], tags: Optional[List[str]] = None) -> List[Rule]:
        """Get all rules that would trigger for given context"""
        applicable = []
        
        for rule in self.rules:
            if not rule.enabled:
                continue
                
            if tags and not any(tag in rule.tags for tag in tags):
                continue
                
            if rule.evaluate_conditions(context):
                applicable.append(rule)
        
        return applicable
    
    def validate_rules(self) -> List[Dict[str, Any]]:
        """Validate all loaded rules for errors"""
        errors = []
        
        for rule in self.rules:
            # Check for duplicate IDs
            rule_ids = [r.id for r in self.rules]
            if rule_ids.count(rule.id) > 1:
                errors.append({
                    'rule_id': rule.id,
                    'error': 'Duplicate rule ID'
                })
            
            # Check for empty conditions
            if not rule.conditions:
                errors.append({
                    'rule_id': rule.id,
                    'error': 'No conditions defined',
                    'severity': 'warning'
                })
            
            # Check for empty actions
            if not rule.actions:
                errors.append({
                    'rule_id': rule.id,
                    'error': 'No actions defined'
                })
        
        return errors
    
    def export_rules(self, output_file: str):
        """Export current rules to JSON file"""
        rules_data = {
            'rules': [
                {
                    'id': rule.id,
                    'name': rule.name,
                    'description': rule.description,
                    'enabled': rule.enabled,
                    'priority': rule.priority,
                    'conditions': rule.conditions,
                    'actions': rule.actions,
                    'tags': rule.tags
                }
                for rule in self.rules
            ]
        }
        
        with open(output_file, 'w') as f:
            json.dump(rules_data, f, indent=2)
    
    def add_rule(self, rule_dict: Dict[str, Any]):
        """Add a new rule at runtime"""
        rule = Rule(rule_dict)
        self.rules.append(rule)
        self.rules.sort(key=lambda x: x.priority)
    
    def remove_rule(self, rule_id: str):
        """Remove a rule by ID"""
        self.rules = [r for r in self.rules if r.id != rule_id]
    
    def enable_rule(self, rule_id: str):
        """Enable a rule by ID"""
        for rule in self.rules:
            if rule.id == rule_id:
                rule.enabled = True
                break
    
    def disable_rule(self, rule_id: str):
        """Disable a rule by ID"""
        for rule in self.rules:
            if rule.id == rule_id:
                rule.enabled = False
                break