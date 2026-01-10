"""
Prompt templates for DIVA-SQL agents

This module contains all the prompt templates used by the different agents
in the DIVA-SQL framework.
"""

from typing import Dict, Any, List
import json


class DecomposerPrompts:
    """Prompt templates for the Semantic Decomposer Agent"""
    
    def get_structure_analysis_prompt(self, nl_query: str) -> str:
        """Generate prompt for analyzing query structure"""
        return f"""
You are an expert SQL analyst. Analyze the following natural language query and identify its high-level structure.

Query: "{nl_query}"

Provide your analysis in the following JSON format:
{{
    "query_type": "SELECT|COUNT|SUM|AVG|MAX|MIN|INSERT|UPDATE|DELETE",
    "complexity_indicators": ["JOIN", "GROUP", "FILTER", "ORDER", "SUBQUERY", "AGGREGATE"],
    "estimated_steps": <number>,
    "reasoning": "<brief explanation of your analysis>",
    "key_entities": ["entity1", "entity2"],
    "relationships": ["relationship1", "relationship2"]
}}

Focus on:
1. What type of operation is being requested
2. What complexity patterns are present
3. How many logical steps will be needed
4. What entities and relationships are involved

Respond only with valid JSON.
"""

    def get_component_identification_prompt(self, 
                                          nl_query: str, 
                                          database_schema: Dict[str, Any],
                                          query_analysis: Dict[str, Any]) -> str:
        """Generate prompt for identifying semantic components"""
        schema_str = json.dumps(database_schema, indent=2)
        analysis_str = json.dumps(query_analysis, indent=2)
        
        return f"""
You are an expert at breaking down complex SQL queries into logical steps. 
Given a natural language query and database schema, identify the semantic components needed.

Query: "{nl_query}"

Database Schema:
{schema_str}

Query Analysis:
{analysis_str}

Break down this query into semantic components. Each component should represent a single logical operation.

Provide your response in the following JSON format:
{{
    "components": [
        {{
            "type": "FILTER|JOIN|GROUP|AGGREGATE|SELECT|ORDER|LIMIT|SUBQUERY",
            "description": "Clear description of what this step does",
            "tables": ["table1", "table2"],
            "columns": ["col1", "col2"],
            "conditions": ["condition1", "condition2"],
            "priority": <execution_order>,
            "reasoning": "Why this component is needed"
        }}
    ],
    "execution_flow": "Description of how components work together"
}}

Guidelines:
1. Start with data filtering/selection components
2. Then joins if multiple tables are needed
3. Then grouping/aggregation if needed
4. Finally selection of output columns
5. Each component should be independently understandable
6. Components should have clear dependencies

Respond only with valid JSON.
"""

    def get_refinement_prompt(self, 
                            dag, 
                            feedback: str,
                            database_schema: Dict[str, Any]) -> str:
        """Generate prompt for refining a DAG based on feedback"""
        dag_str = dag.to_json()
        schema_str = json.dumps(database_schema, indent=2)
        
        return f"""
You are an expert at refining semantic query decompositions. 
Given a semantic DAG and feedback, provide refinements to improve the decomposition.

Current DAG:
{dag_str}

Database Schema:
{schema_str}

Feedback: "{feedback}"

Analyze the current DAG and the feedback, then provide refinements in the following JSON format:
{{
    "refinements": [
        {{
            "action": "ADD|MODIFY|REMOVE|REORDER",
            "target": "node_id_or_edge",
            "changes": {{
                "description": "new description",
                "type": "new type if changing",
                "tables": ["updated tables"],
                "columns": ["updated columns"],
                "conditions": ["updated conditions"]
            }},
            "reasoning": "Why this refinement is needed"
        }}
    ],
    "reasoning": "Overall explanation of the refinements"
}}

Focus on:
1. Addressing the specific feedback provided
2. Ensuring logical flow and dependencies
3. Maintaining semantic clarity
4. Improving query accuracy

Respond only with valid JSON.
"""


class GeneratorPrompts:
    """Prompt templates for the Clause Generator Agent"""
    
    def get_clause_generation_prompt(self, 
                                   semantic_node,
                                   database_schema: Dict[str, Any],
                                   previous_clauses: List[str] = None) -> str:
        """Generate prompt for creating SQL clause from semantic node"""
        schema_str = json.dumps(database_schema, indent=2)
        node_dict = semantic_node.to_dict()
        node_str = json.dumps(node_dict, indent=2)
        
        previous_context = ""
        if previous_clauses:
            previous_context = f"""
Previous SQL clauses in this query:
{chr(10).join(f"- {clause}" for clause in previous_clauses)}
"""
        
        return f"""
You are an expert SQL generator. Generate a precise SQL clause for the given semantic operation.

Semantic Node:
{node_str}

Database Schema:
{schema_str}

{previous_context}

Generate a SQL clause that implements exactly what the semantic node describes.

Guidelines:
1. Generate only the specific clause needed (SELECT, WHERE, JOIN, GROUP BY, etc.)
2. Use proper table aliases (T1, T2, etc.)
3. Ensure column names match the schema exactly
4. Consider the context of previous clauses if provided
5. Be precise and avoid unnecessary complexity

Provide your response in the following JSON format:
{{
    "sql_clause": "<generated SQL clause>",
    "explanation": "<brief explanation of the clause>",
    "tables_used": ["table1", "table2"],
    "columns_used": ["col1", "col2"],
    "confidence": <0.0 to 1.0>
}}

Respond only with valid JSON.
"""

    def get_correction_prompt(self, 
                            semantic_node,
                            current_sql: str,
                            error_feedback: str,
                            database_schema: Dict[str, Any]) -> str:
        """Generate prompt for correcting SQL based on verification feedback"""
        schema_str = json.dumps(database_schema, indent=2)
        node_dict = semantic_node.to_dict()
        node_str = json.dumps(node_dict, indent=2)
        
        return f"""
You are an expert SQL debugger. Fix the SQL clause based on the verification feedback.

Semantic Node (what should be implemented):
{node_str}

Current SQL Clause:
{current_sql}

Verification Feedback:
{error_feedback}

Database Schema:
{schema_str}

Analyze the feedback and generate a corrected SQL clause.

Provide your response in the following JSON format:
{{
    "corrected_sql": "<fixed SQL clause>",
    "changes_made": ["change1", "change2"],
    "explanation": "<explanation of the corrections>",
    "confidence": <0.0 to 1.0>
}}

Respond only with valid JSON.
"""


class VerifierPrompts:
    """Prompt templates for the Verification & Alignment Agent"""
    
    def get_schema_alignment_prompt(self, 
                                  semantic_node,
                                  sql_clause: str,
                                  database_schema: Dict[str, Any]) -> str:
        """Generate prompt for checking schema alignment"""
        schema_str = json.dumps(database_schema, indent=2)
        node_dict = semantic_node.to_dict()
        node_str = json.dumps(node_dict, indent=2)
        
        return f"""
You are an expert SQL validator. Check if the SQL clause correctly implements the semantic intent using the proper schema.

Semantic Intent:
{node_str}

Generated SQL Clause:
{sql_clause}

Database Schema:
{schema_str}

Verify the following aspects:
1. Are the correct tables referenced?
2. Are the column names spelled correctly and exist in the schema?
3. Are the data types being used appropriately?
4. Does the SQL logic match the semantic description?
5. Are table aliases used consistently?

Provide your response in the following JSON format:
{{
    "is_aligned": true/false,
    "issues": [
        {{
            "type": "TABLE_MISMATCH|COLUMN_MISMATCH|TYPE_MISMATCH|LOGIC_MISMATCH",
            "description": "Description of the issue",
            "severity": "HIGH|MEDIUM|LOW"
        }}
    ],
    "suggestions": ["suggestion1", "suggestion2"],
    "confidence": <0.0 to 1.0>
}}

Respond only with valid JSON.
"""

    def get_error_pattern_prompt(self, 
                               sql_clause: str,
                               known_patterns: List[str] = None) -> str:
        """Generate prompt for checking common error patterns"""
        patterns_context = ""
        if known_patterns:
            patterns_context = f"""
Known Error Patterns to check for:
{chr(10).join(f"- {pattern}" for pattern in known_patterns)}
"""
        
        return f"""
You are an expert SQL error detector. Analyze the SQL clause for common error patterns.

SQL Clause:
{sql_clause}

{patterns_context}

Check for these common SQL errors:
1. Comparing ID columns to string literals
2. Missing table joins when referencing multiple tables
3. Incorrect aggregation without GROUP BY
4. Wrong comparison operators for dates
5. Case sensitivity issues
6. NULL handling problems
7. Ambiguous column references

Provide your response in the following JSON format:
{{
    "has_errors": true/false,
    "errors_found": [
        {{
            "pattern": "Error pattern name",
            "description": "Description of the error",
            "severity": "HIGH|MEDIUM|LOW",
            "suggested_fix": "How to fix this error"
        }}
    ],
    "confidence": <0.0 to 1.0>
}}

Respond only with valid JSON.
"""

    def get_execution_sanity_prompt(self, 
                                  sql_clause: str,
                                  execution_result: Dict[str, Any]) -> str:
        """Generate prompt for analyzing execution results"""
        result_str = json.dumps(execution_result, indent=2)
        
        return f"""
You are an expert SQL execution analyzer. Analyze the execution result to determine if it's reasonable.

SQL Clause:
{sql_clause}

Execution Result:
{result_str}

Analyze the execution result for sanity:
1. Did the query execute without errors?
2. Is the result set reasonable (not empty when it shouldn't be)?
3. Are there any suspicious patterns in the data?
4. Does the row count make sense?
5. Are there any obvious data quality issues?

Provide your response in the following JSON format:
{{
    "is_sane": true/false,
    "issues": [
        {{
            "type": "EMPTY_RESULT|EXECUTION_ERROR|SUSPICIOUS_DATA|PERFORMANCE",
            "description": "Description of the issue",
            "severity": "HIGH|MEDIUM|LOW"
        }}
    ],
    "recommendations": ["recommendation1", "recommendation2"],
    "confidence": <0.0 to 1.0>
}}

Respond only with valid JSON.
"""


class PipelinePrompts:
    """Prompt templates for the main DIVA-SQL pipeline"""
    
    def get_final_composition_prompt(self, 
                                   dag,
                                   verified_clauses: Dict[str, str]) -> str:
        """Generate prompt for composing final SQL from verified clauses"""
        dag_str = dag.to_json()
        clauses_str = json.dumps(verified_clauses, indent=2)
        
        return f"""
You are an expert SQL composer. Combine the verified SQL clauses into a final, complete SQL query.

Semantic DAG:
{dag_str}

Verified SQL Clauses:
{clauses_str}

Compose these clauses into a single, syntactically correct and efficient SQL query.

Guidelines:
1. Follow the dependency order specified in the DAG
2. Ensure proper JOIN syntax
3. Place WHERE clauses appropriately
4. Handle GROUP BY and aggregation correctly
5. Maintain proper parentheses and operator precedence

Provide your response in the following JSON format:
{{
    "final_sql": "<complete SQL query>",
    "composition_notes": ["note1", "note2"],
    "estimated_complexity": "LOW|MEDIUM|HIGH",
    "confidence": <0.0 to 1.0>
}}

Respond only with valid JSON.
"""
