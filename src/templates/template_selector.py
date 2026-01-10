"""
Template Selector for DIVA-SQL

This module selects the most appropriate SQL template based on semantic node analysis.
It implements intelligent template matching to ensure high-quality SQL generation.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import re

from .template_library import TemplateLibrary, SQLTemplate, TemplateCategory
from ..core.semantic_dag import SemanticNode, NodeType


@dataclass
class TemplateMatch:
    """
    Represents a template match with confidence score
    
    Attributes:
        template: The matched SQL template
        confidence: Confidence score (0.0 to 1.0)
        reasoning: Explanation for the match
        suggested_params: Suggested parameter values
    """
    template: SQLTemplate
    confidence: float
    reasoning: str
    suggested_params: Dict[str, Any]


class TemplateSelector:
    """
    Intelligent template selection based on semantic analysis
    
    This class analyzes semantic nodes and selects the most appropriate
    SQL template from the library, ensuring structured and reliable SQL generation.
    """
    
    def __init__(self, template_library: Optional[TemplateLibrary] = None):
        """
        Initialize template selector
        
        Args:
            template_library: Template library to use (creates new if None)
        """
        self.library = template_library or TemplateLibrary()
        self._node_type_to_category = self._build_mapping()
    
    def _build_mapping(self) -> Dict[NodeType, List[TemplateCategory]]:
        """Build mapping from semantic node types to template categories"""
        return {
            NodeType.SELECT: [TemplateCategory.BASIC_SELECT],
            NodeType.FILTER: [TemplateCategory.FILTERING],
            NodeType.JOIN: [TemplateCategory.JOINS],
            NodeType.AGGREGATE: [TemplateCategory.AGGREGATION],
            NodeType.GROUP: [TemplateCategory.GROUPING],
            NodeType.SORT: [TemplateCategory.BASIC_SELECT],  # ORDER BY
            NodeType.LIMIT: [TemplateCategory.BASIC_SELECT],
            NodeType.SUBQUERY: [TemplateCategory.SUBQUERIES],
        }
    
    def select_template(self, 
                       semantic_node: SemanticNode,
                       context: Optional[Dict[str, Any]] = None) -> TemplateMatch:
        """
        Select the best template for a semantic node
        
        Args:
            semantic_node: The semantic node to generate SQL for
            context: Additional context (previous clauses, schema, etc.)
            
        Returns:
            TemplateMatch with selected template and metadata
        """
        context = context or {}
        
        # Get candidate templates based on node type
        candidates = self._get_candidate_templates(semantic_node)
        
        if not candidates:
            # Fallback to generic template
            return self._create_fallback_match(semantic_node)
        
        # Score each candidate
        scored_matches = []
        for template in candidates:
            match = self._score_template(template, semantic_node, context)
            scored_matches.append(match)
        
        # Return best match
        scored_matches.sort(key=lambda m: m.confidence, reverse=True)
        return scored_matches[0]
    
    def select_multiple_templates(self,
                                  semantic_node: SemanticNode,
                                  context: Optional[Dict[str, Any]] = None,
                                  top_k: int = 3) -> List[TemplateMatch]:
        """
        Select top-k templates for a semantic node
        
        Args:
            semantic_node: The semantic node
            context: Additional context
            top_k: Number of top matches to return
            
        Returns:
            List of top template matches
        """
        context = context or {}
        candidates = self._get_candidate_templates(semantic_node)
        
        if not candidates:
            return [self._create_fallback_match(semantic_node)]
        
        scored_matches = []
        for template in candidates:
            match = self._score_template(template, semantic_node, context)
            scored_matches.append(match)
        
        scored_matches.sort(key=lambda m: m.confidence, reverse=True)
        return scored_matches[:top_k]
    
    def _get_candidate_templates(self, semantic_node: SemanticNode) -> List[SQLTemplate]:
        """Get candidate templates based on node type"""
        node_type = semantic_node.node_type
        
        # Get relevant categories
        categories = self._node_type_to_category.get(node_type, [])
        
        candidates = []
        for category in categories:
            candidates.extend(self.library.get_templates_by_category(category))
        
        # Additional filtering based on node properties
        candidates = self._filter_by_node_properties(candidates, semantic_node)
        
        return candidates
    
    def _filter_by_node_properties(self, 
                                   templates: List[SQLTemplate],
                                   semantic_node: SemanticNode) -> List[SQLTemplate]:
        """Filter templates based on semantic node properties"""
        filtered = []
        
        for template in templates:
            if self._template_matches_node(template, semantic_node):
                filtered.append(template)
        
        return filtered if filtered else templates  # Return all if none match
    
    def _template_matches_node(self, template: SQLTemplate, node: SemanticNode) -> bool:
        """Check if template matches node requirements"""
        params = node.parameters
        
        # Check for JOIN-specific matching
        if node.node_type == NodeType.JOIN:
            join_type = params.get('join_type', 'INNER').upper()
            if join_type in template.name.upper():
                return True
            if join_type == 'INNER' and 'Simple INNER JOIN' in template.name:
                return True
        
        # Check for aggregation-specific matching
        if node.node_type == NodeType.AGGREGATE:
            agg_function = params.get('function', '').upper()
            if agg_function and agg_function in template.name.upper():
                return True
        
        # Check for filter-specific matching
        if node.node_type == NodeType.FILTER:
            condition_type = self._analyze_filter_condition(params)
            if condition_type in template.name:
                return True
        
        return True  # Default to accepting template
    
    def _analyze_filter_condition(self, params: Dict[str, Any]) -> str:
        """Analyze filter parameters to determine condition type"""
        condition = params.get('condition', '')
        
        if 'AND' in condition.upper():
            return 'AND'
        if 'OR' in condition.upper():
            return 'OR'
        if 'IN' in condition.upper():
            return 'IN'
        if 'BETWEEN' in condition.upper():
            return 'BETWEEN'
        if 'LIKE' in condition.upper():
            return 'LIKE'
        if 'NULL' in condition.upper():
            return 'NULL'
        if any(op in condition for op in ['>', '<', '>=', '<=', '!=']):
            return 'Comparison'
        if '=' in condition:
            return 'Equality'
        
        return 'Simple'
    
    def _score_template(self,
                       template: SQLTemplate,
                       semantic_node: SemanticNode,
                       context: Dict[str, Any]) -> TemplateMatch:
        """
        Score a template for a semantic node
        
        Scoring factors:
        - Parameter match (40%)
        - Complexity appropriateness (30%)
        - Context compatibility (30%)
        """
        score = 0.0
        reasoning_parts = []
        suggested_params = {}
        
        # Factor 1: Parameter match (40%)
        param_score, param_suggestions = self._score_parameters(template, semantic_node)
        score += param_score * 0.4
        suggested_params.update(param_suggestions)
        reasoning_parts.append(f"Parameter match: {param_score:.2f}")
        
        # Factor 2: Complexity appropriateness (30%)
        complexity_score = self._score_complexity(template, semantic_node, context)
        score += complexity_score * 0.3
        reasoning_parts.append(f"Complexity fit: {complexity_score:.2f}")
        
        # Factor 3: Context compatibility (30%)
        context_score = self._score_context(template, context)
        score += context_score * 0.3
        reasoning_parts.append(f"Context compatibility: {context_score:.2f}")
        
        reasoning = "; ".join(reasoning_parts)
        
        return TemplateMatch(
            template=template,
            confidence=score,
            reasoning=reasoning,
            suggested_params=suggested_params
        )
    
    def _score_parameters(self,
                         template: SQLTemplate,
                         semantic_node: SemanticNode) -> Tuple[float, Dict[str, Any]]:
        """Score based on parameter availability"""
        required_params = set(template.parameters)
        node_params = semantic_node.parameters
        
        suggestions = {}
        matched = 0
        
        for param in required_params:
            # Try to extract parameter from node
            value = self._extract_parameter(param, semantic_node)
            if value is not None:
                suggestions[param] = value
                matched += 1
        
        score = matched / len(required_params) if required_params else 1.0
        return score, suggestions
    
    def _extract_parameter(self, param_name: str, node: SemanticNode) -> Optional[Any]:
        """Extract parameter value from semantic node"""
        params = node.parameters
        
        # Direct parameter mapping
        param_mappings = {
            'table': params.get('table', params.get('tables', [None])[0] if isinstance(params.get('tables'), list) else None),
            'columns': params.get('columns', params.get('column', '*')),
            'column': params.get('column', params.get('columns', [None])[0] if isinstance(params.get('columns'), list) else None),
            'condition': params.get('condition'),
            'join_condition': params.get('join_condition'),
            'aggregation': params.get('function'),
            'group_columns': params.get('group_by'),
            'order_columns': params.get('order_by'),
            'limit': params.get('limit'),
        }
        
        # Check direct mapping first
        if param_name in param_mappings:
            return param_mappings[param_name]
        
        # Check node parameters directly
        if param_name in params:
            return params[param_name]
        
        return None
    
    def _score_complexity(self,
                         template: SQLTemplate,
                         semantic_node: SemanticNode,
                         context: Dict[str, Any]) -> float:
        """Score based on complexity appropriateness"""
        # Estimate required complexity from node
        required_complexity = self._estimate_node_complexity(semantic_node, context)
        
        # Prefer templates with matching complexity
        complexity_diff = abs(template.complexity - required_complexity)
        
        if complexity_diff == 0:
            return 1.0
        elif complexity_diff == 1:
            return 0.8
        elif complexity_diff == 2:
            return 0.6
        else:
            return 0.4
    
    def _estimate_node_complexity(self,
                                  semantic_node: SemanticNode,
                                  context: Dict[str, Any]) -> int:
        """Estimate complexity required for a semantic node"""
        complexity = 1
        params = semantic_node.parameters
        
        # Increase complexity based on features
        if len(semantic_node.dependencies) > 2:
            complexity += 1
        
        if params.get('condition') and ('AND' in str(params['condition']) or 'OR' in str(params['condition'])):
            complexity += 1
        
        if semantic_node.node_type in [NodeType.SUBQUERY, NodeType.JOIN]:
            complexity += 1
        
        if context.get('has_aggregation') and context.get('has_grouping'):
            complexity += 1
        
        return min(complexity, 5)
    
    def _score_context(self, template: SQLTemplate, context: Dict[str, Any]) -> float:
        """Score based on context compatibility"""
        score = 1.0
        
        # Check if template fits with previous clauses
        previous_clauses = context.get('previous_clauses', [])
        
        if previous_clauses:
            # Ensure template doesn't conflict with existing clauses
            if self._has_conflicts(template, previous_clauses):
                score *= 0.5
        
        # Check database compatibility
        db_type = context.get('database_type', 'sqlite')
        if not self._is_db_compatible(template, db_type):
            score *= 0.7
        
        return score
    
    def _has_conflicts(self, template: SQLTemplate, previous_clauses: List[str]) -> bool:
        """Check if template conflicts with previous clauses"""
        # Simple conflict detection
        template_pattern = template.pattern.upper()
        
        for clause in previous_clauses:
            clause_upper = clause.upper()
            
            # Check for duplicate clause types
            if 'GROUP BY' in template_pattern and 'GROUP BY' in clause_upper:
                return True
            if 'ORDER BY' in template_pattern and 'ORDER BY' in clause_upper:
                return True
        
        return False
    
    def _is_db_compatible(self, template: SQLTemplate, db_type: str) -> bool:
        """Check if template is compatible with database type"""
        # Most templates are compatible with all databases
        # Special cases:
        
        if db_type == 'mysql':
            # MySQL doesn't support FULL OUTER JOIN
            if 'FULL OUTER JOIN' in template.pattern:
                return False
        
        if db_type == 'sqlite':
            # SQLite has limited support for RIGHT JOIN and FULL OUTER JOIN
            if 'RIGHT JOIN' in template.pattern or 'FULL OUTER JOIN' in template.pattern:
                return False
        
        return True
    
    def _create_fallback_match(self, semantic_node: SemanticNode) -> TemplateMatch:
        """Create a fallback match when no suitable template is found"""
        # Use the simplest template from the library
        all_templates = list(self.library.templates.values())
        all_templates.sort(key=lambda t: t.complexity)
        
        fallback_template = all_templates[0] if all_templates else None
        
        if not fallback_template:
            # Create a minimal template
            fallback_template = SQLTemplate(
                id="FALLBACK",
                name="Generic Query",
                category=TemplateCategory.BASIC_SELECT,
                pattern="SELECT {columns} FROM {table}",
                parameters=["columns", "table"],
                description="Fallback generic query",
                complexity=1,
                examples=[]
            )
        
        return TemplateMatch(
            template=fallback_template,
            confidence=0.3,
            reasoning="No specific template found; using fallback",
            suggested_params={}
        )


# Example usage
if __name__ == "__main__":
    from ..core.semantic_dag import SemanticNode, NodeType
    
    # Create selector
    selector = TemplateSelector()
    
    # Test with a filter node
    filter_node = SemanticNode(
        node_id="filter_1",
        node_type=NodeType.FILTER,
        description="Filter employees with salary > 50000",
        parameters={
            "table": "employees",
            "column": "salary",
            "condition": "salary > 50000"
        }
    )
    
    match = selector.select_template(filter_node)
    print(f"Selected template: {match.template.name}")
    print(f"Confidence: {match.confidence:.2f}")
    print(f"Reasoning: {match.reasoning}")
    print(f"Suggested params: {match.suggested_params}")
    
    # Instantiate the template
    if match.suggested_params:
        sql = match.template.instantiate(match.suggested_params)
        print(f"\nGenerated SQL:\n{sql}")
