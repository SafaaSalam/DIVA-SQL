"""
Clause Generator Agent for DIVA-SQL

This agent is responsible for generating SQL clauses from individual semantic nodes.
It focuses on translating single logical operations into precise SQL syntax.
"""

from typing import Dict, List, Optional, Any
import json
from dataclasses import dataclass

from ..core.semantic_dag import SemanticNode, NodeType
from ..utils.prompts import GeneratorPrompts


@dataclass
class GenerationResult:
    """Result of SQL clause generation"""
    success: bool
    sql_clause: Optional[str]
    explanation: Optional[str] = None
    tables_used: List[str] = None
    columns_used: List[str] = None
    confidence: float = 0.0
    error_message: Optional[str] = None


class ClauseGenerator:
    """
    Agent responsible for generating SQL clauses from semantic nodes
    """
    
    def __init__(self, llm_client, model_name: str = "gpt-4"):
        self.llm_client = llm_client
        self.model_name = model_name
        self.prompts = GeneratorPrompts()
        
        # Template mappings for different node types
        self.node_type_templates = {
            NodeType.FILTER: self._generate_filter_clause,
            NodeType.JOIN: self._generate_join_clause,
            NodeType.GROUP: self._generate_group_clause,
            NodeType.AGGREGATE: self._generate_aggregate_clause,
            NodeType.SELECT: self._generate_select_clause,
            NodeType.ORDER: self._generate_order_clause,
            NodeType.LIMIT: self._generate_limit_clause,
            NodeType.HAVING: self._generate_having_clause
        }
    
    def generate_clause(self, 
                       semantic_node: SemanticNode,
                       database_schema: Dict[str, Any],
                       context: Optional[Dict[str, Any]] = None) -> GenerationResult:
        """
        Generate SQL clause for a semantic node
        
        Args:
            semantic_node: The semantic node to generate SQL for
            database_schema: Database schema information
            context: Additional context (previous clauses, etc.)
            
        Returns:
            GenerationResult containing the SQL clause or error information
        """
        try:
            # Extract previous clauses from context if available
            previous_clauses = []
            if context and "previous_clauses" in context:
                previous_clauses = context["previous_clauses"]
            
            # Use specialized method if available, otherwise use general LLM approach
            if semantic_node.node_type in self.node_type_templates:
                result = self.node_type_templates[semantic_node.node_type](
                    semantic_node, database_schema, previous_clauses
                )
            else:
                result = self._generate_with_llm(
                    semantic_node, database_schema, previous_clauses
                )
            
            return result
            
        except Exception as e:
            return GenerationResult(
                success=False,
                sql_clause=None,
                error_message=f"Clause generation failed: {str(e)}"
            )
    
    def correct_clause(self, 
                      semantic_node: SemanticNode,
                      current_sql: str,
                      error_feedback: str,
                      database_schema: Dict[str, Any]) -> GenerationResult:
        """
        Correct a SQL clause based on verification feedback
        
        Args:
            semantic_node: The semantic node the SQL should implement
            current_sql: The current (incorrect) SQL clause
            error_feedback: Feedback from the verification agent
            database_schema: Database schema information
            
        Returns:
            GenerationResult with corrected SQL clause
        """
        try:
            prompt = self.prompts.get_correction_prompt(
                semantic_node, current_sql, error_feedback, database_schema
            )
            
            response = self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            correction_data = json.loads(response.choices[0].message.content)
            
            return GenerationResult(
                success=True,
                sql_clause=correction_data.get("corrected_sql"),
                explanation=correction_data.get("explanation"),
                confidence=correction_data.get("confidence", 0.8)
            )
            
        except Exception as e:
            return GenerationResult(
                success=False,
                sql_clause=current_sql,  # Return original if correction fails
                error_message=f"Clause correction failed: {str(e)}"
            )
    
    def _generate_with_llm(self, 
                          semantic_node: SemanticNode,
                          database_schema: Dict[str, Any],
                          previous_clauses: List[str]) -> GenerationResult:
        """
        Generate SQL clause using LLM with general prompt
        """
        prompt = self.prompts.get_clause_generation_prompt(
            semantic_node, database_schema, previous_clauses
        )
        
        response = self.llm_client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        
        try:
            generation_data = json.loads(response.choices[0].message.content)
            
            return GenerationResult(
                success=True,
                sql_clause=generation_data.get("sql_clause"),
                explanation=generation_data.get("explanation"),
                tables_used=generation_data.get("tables_used", []),
                columns_used=generation_data.get("columns_used", []),
                confidence=generation_data.get("confidence", 0.7)
            )
            
        except json.JSONDecodeError:
            # Fallback: try to extract SQL from raw response
            content = response.choices[0].message.content
            sql_clause = self._extract_sql_from_text(content)
            
            return GenerationResult(
                success=sql_clause is not None,
                sql_clause=sql_clause,
                explanation="Fallback extraction from LLM response",
                confidence=0.5
            )
    
    def _generate_filter_clause(self, 
                              semantic_node: SemanticNode,
                              database_schema: Dict[str, Any],
                              previous_clauses: List[str]) -> GenerationResult:
        """
        Generate WHERE clause for filtering operations
        """
        try:
            # Extract filter conditions from the semantic node
            conditions = semantic_node.conditions
            tables = semantic_node.tables
            columns = semantic_node.columns
            
            if not conditions and not columns:
                # Use LLM as fallback
                return self._generate_with_llm(semantic_node, database_schema, previous_clauses)
            
            # Build WHERE clause
            where_parts = []
            table_alias = f"T{len(tables)}" if tables else "T1"
            
            # Simple rule-based generation for common patterns
            description_lower = semantic_node.description.lower()
            
            if "after" in description_lower and any("date" in col.lower() for col in columns):
                # Date filtering
                date_col = next((col for col in columns if "date" in col.lower()), columns[0])
                if "2022" in description_lower:
                    where_parts.append(f"{table_alias}.{date_col} > '2022-01-01'")
                elif "2023" in description_lower:
                    where_parts.append(f"{table_alias}.{date_col} > '2023-01-01'")
            
            elif "before" in description_lower and any("date" in col.lower() for col in columns):
                # Date filtering (before)
                date_col = next((col for col in columns if "date" in col.lower()), columns[0])
                if "2022" in description_lower:
                    where_parts.append(f"{table_alias}.{date_col} < '2022-01-01'")
            
            elif any(op in description_lower for op in ["greater than", "more than", ">"]):
                # Numeric comparison
                if columns:
                    col = columns[0]
                    # Try to extract number from description
                    import re
                    numbers = re.findall(r'\d+', semantic_node.description)
                    if numbers:
                        where_parts.append(f"{table_alias}.{col} > {numbers[0]}")
            
            # Add explicit conditions
            for condition in conditions:
                if not condition.startswith(table_alias):
                    condition = f"{table_alias}.{condition}"
                where_parts.append(condition)
            
            if where_parts:
                sql_clause = "WHERE " + " AND ".join(where_parts)
                return GenerationResult(
                    success=True,
                    sql_clause=sql_clause,
                    explanation=f"Filter clause with {len(where_parts)} conditions",
                    tables_used=tables,
                    columns_used=columns,
                    confidence=0.8
                )
            else:
                # Fallback to LLM
                return self._generate_with_llm(semantic_node, database_schema, previous_clauses)
            
        except Exception as e:
            return GenerationResult(
                success=False,
                sql_clause=None,
                error_message=f"Filter clause generation failed: {str(e)}"
            )
    
    def _generate_join_clause(self, 
                            semantic_node: SemanticNode,
                            database_schema: Dict[str, Any],
                            previous_clauses: List[str]) -> GenerationResult:
        """
        Generate JOIN clause for table joining operations
        """
        try:
            tables = semantic_node.tables
            
            if len(tables) < 2:
                return self._generate_with_llm(semantic_node, database_schema, previous_clauses)
            
            # Simple rule-based join generation
            # Assume first table is already in FROM, join the second
            main_table = tables[0]
            join_table = tables[1]
            
            # Look for common join patterns in schema
            join_conditions = []
            
            # Check for foreign key relationships (simplified)
            main_table_schema = database_schema.get("tables", {}).get(main_table, [])
            join_table_schema = database_schema.get("tables", {}).get(join_table, [])
            
            # Look for ID columns
            for col in main_table_schema:
                if col.endswith("ID") and col in join_table_schema:
                    join_conditions.append(f"T1.{col} = T2.{col}")
            
            # If no automatic match, look for common patterns
            if not join_conditions:
                if f"{join_table}ID" in main_table_schema and "ID" in join_table_schema:
                    join_conditions.append(f"T1.{join_table}ID = T2.ID")
                elif f"{main_table}ID" in join_table_schema and "ID" in main_table_schema:
                    join_conditions.append(f"T1.ID = T2.{main_table}ID")
            
            if join_conditions:
                sql_clause = f"JOIN {join_table} AS T2 ON {' AND '.join(join_conditions)}"
                return GenerationResult(
                    success=True,
                    sql_clause=sql_clause,
                    explanation=f"Join between {main_table} and {join_table}",
                    tables_used=tables,
                    confidence=0.8
                )
            else:
                # Fallback to LLM
                return self._generate_with_llm(semantic_node, database_schema, previous_clauses)
            
        except Exception as e:
            return GenerationResult(
                success=False,
                sql_clause=None,
                error_message=f"Join clause generation failed: {str(e)}"
            )
    
    def _generate_group_clause(self, 
                             semantic_node: SemanticNode,
                             database_schema: Dict[str, Any],
                             previous_clauses: List[str]) -> GenerationResult:
        """
        Generate GROUP BY clause for grouping operations
        """
        try:
            columns = semantic_node.columns
            
            if not columns:
                return self._generate_with_llm(semantic_node, database_schema, previous_clauses)
            
            # Build GROUP BY clause
            table_alias = "T1"  # Default alias
            group_columns = [f"{table_alias}.{col}" for col in columns]
            
            sql_clause = f"GROUP BY {', '.join(group_columns)}"
            
            return GenerationResult(
                success=True,
                sql_clause=sql_clause,
                explanation=f"Group by {len(columns)} columns",
                columns_used=columns,
                confidence=0.9
            )
            
        except Exception as e:
            return GenerationResult(
                success=False,
                sql_clause=None,
                error_message=f"Group clause generation failed: {str(e)}"
            )
    
    def _generate_aggregate_clause(self, 
                                 semantic_node: SemanticNode,
                                 database_schema: Dict[str, Any],
                                 previous_clauses: List[str]) -> GenerationResult:
        """
        Generate aggregate functions (COUNT, SUM, AVG, etc.)
        """
        try:
            description_lower = semantic_node.description.lower()
            columns = semantic_node.columns
            
            # Determine aggregate function from description
            agg_func = None
            if "count" in description_lower:
                agg_func = "COUNT"
            elif "sum" in description_lower or "total" in description_lower:
                agg_func = "SUM"
            elif "average" in description_lower or "avg" in description_lower:
                agg_func = "AVG"
            elif "maximum" in description_lower or "max" in description_lower:
                agg_func = "MAX"
            elif "minimum" in description_lower or "min" in description_lower:
                agg_func = "MIN"
            
            if not agg_func:
                return self._generate_with_llm(semantic_node, database_schema, previous_clauses)
            
            # Build aggregate expression
            if agg_func == "COUNT":
                if columns:
                    sql_clause = f"COUNT(T1.{columns[0]})"
                else:
                    sql_clause = "COUNT(*)"
            else:
                if columns:
                    sql_clause = f"{agg_func}(T1.{columns[0]})"
                else:
                    return self._generate_with_llm(semantic_node, database_schema, previous_clauses)
            
            return GenerationResult(
                success=True,
                sql_clause=sql_clause,
                explanation=f"{agg_func} aggregation",
                columns_used=columns,
                confidence=0.9
            )
            
        except Exception as e:
            return GenerationResult(
                success=False,
                sql_clause=None,
                error_message=f"Aggregate clause generation failed: {str(e)}"
            )
    
    def _generate_select_clause(self, 
                              semantic_node: SemanticNode,
                              database_schema: Dict[str, Any],
                              previous_clauses: List[str]) -> GenerationResult:
        """
        Generate SELECT clause for column selection
        """
        try:
            columns = semantic_node.columns
            tables = semantic_node.tables
            
            if not columns:
                return self._generate_with_llm(semantic_node, database_schema, previous_clauses)
            
            # Build SELECT clause
            table_alias = "T1"  # Default alias
            select_columns = []
            
            for col in columns:
                if "." not in col:  # Add table alias if not present
                    select_columns.append(f"{table_alias}.{col}")
                else:
                    select_columns.append(col)
            
            sql_clause = f"SELECT {', '.join(select_columns)}"
            
            return GenerationResult(
                success=True,
                sql_clause=sql_clause,
                explanation=f"Select {len(columns)} columns",
                tables_used=tables,
                columns_used=columns,
                confidence=0.9
            )
            
        except Exception as e:
            return GenerationResult(
                success=False,
                sql_clause=None,
                error_message=f"Select clause generation failed: {str(e)}"
            )
    
    def _generate_order_clause(self, 
                             semantic_node: SemanticNode,
                             database_schema: Dict[str, Any],
                             previous_clauses: List[str]) -> GenerationResult:
        """
        Generate ORDER BY clause for sorting
        """
        try:
            columns = semantic_node.columns
            description_lower = semantic_node.description.lower()
            
            if not columns:
                return self._generate_with_llm(semantic_node, database_schema, previous_clauses)
            
            # Determine sort direction
            if any(word in description_lower for word in ["desc", "descending", "highest", "largest"]):
                direction = "DESC"
            else:
                direction = "ASC"
            
            # Build ORDER BY clause
            table_alias = "T1"
            order_columns = [f"{table_alias}.{col} {direction}" for col in columns]
            
            sql_clause = f"ORDER BY {', '.join(order_columns)}"
            
            return GenerationResult(
                success=True,
                sql_clause=sql_clause,
                explanation=f"Order by {len(columns)} columns {direction}",
                columns_used=columns,
                confidence=0.9
            )
            
        except Exception as e:
            return GenerationResult(
                success=False,
                sql_clause=None,
                error_message=f"Order clause generation failed: {str(e)}"
            )
    
    def _generate_limit_clause(self, 
                             semantic_node: SemanticNode,
                             database_schema: Dict[str, Any],
                             previous_clauses: List[str]) -> GenerationResult:
        """
        Generate LIMIT clause for result limiting
        """
        try:
            description = semantic_node.description
            
            # Extract number from description
            import re
            numbers = re.findall(r'\d+', description)
            
            if numbers:
                limit_value = numbers[0]
                sql_clause = f"LIMIT {limit_value}"
                
                return GenerationResult(
                    success=True,
                    sql_clause=sql_clause,
                    explanation=f"Limit to {limit_value} rows",
                    confidence=0.9
                )
            else:
                return self._generate_with_llm(semantic_node, database_schema, previous_clauses)
            
        except Exception as e:
            return GenerationResult(
                success=False,
                sql_clause=None,
                error_message=f"Limit clause generation failed: {str(e)}"
            )
    
    def _generate_having_clause(self, 
                              semantic_node: SemanticNode,
                              database_schema: Dict[str, Any],
                              previous_clauses: List[str]) -> GenerationResult:
        """
        Generate HAVING clause for aggregate filtering
        """
        try:
            conditions = semantic_node.conditions
            
            if not conditions:
                return self._generate_with_llm(semantic_node, database_schema, previous_clauses)
            
            # Build HAVING clause
            having_parts = []
            for condition in conditions:
                having_parts.append(condition)
            
            sql_clause = f"HAVING {' AND '.join(having_parts)}"
            
            return GenerationResult(
                success=True,
                sql_clause=sql_clause,
                explanation=f"Having clause with {len(conditions)} conditions",
                confidence=0.8
            )
            
        except Exception as e:
            return GenerationResult(
                success=False,
                sql_clause=None,
                error_message=f"Having clause generation failed: {str(e)}"
            )
    
    def _extract_sql_from_text(self, text: str) -> Optional[str]:
        """
        Extract SQL clause from raw text response (fallback method)
        """
        # Simple regex to find SQL-like patterns
        import re
        
        # Look for common SQL keywords
        sql_patterns = [
            r'(SELECT\s+.+)',
            r'(WHERE\s+.+)',
            r'(JOIN\s+.+)',
            r'(GROUP BY\s+.+)',
            r'(ORDER BY\s+.+)',
            r'(HAVING\s+.+)',
            r'(LIMIT\s+\d+)'
        ]
        
        for pattern in sql_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return None


# Example usage
if __name__ == "__main__":
    from ..core.semantic_dag import SemanticNode, NodeType
    
    # Mock LLM client for testing
    class MockLLMClient:
        class Chat:
            class Completions:
                def create(self, **kwargs):
                    class Response:
                        class Choice:
                            class Message:
                                content = '{"sql_clause": "WHERE T1.HireDate > \'2022-01-01\'", "explanation": "Filter employees hired after 2022", "confidence": 0.9}'
                        choices = [Choice()]
                    return Response()
        chat = Chat()
    
    # Test the generator
    generator = ClauseGenerator(MockLLMClient())
    
    # Test filter node
    filter_node = SemanticNode(
        id="filter_employees",
        node_type=NodeType.FILTER,
        description="Find employees hired after 2022",
        tables=["Employees"],
        columns=["HireDate"],
        conditions=["HireDate > '2022-01-01'"]
    )
    
    schema = {
        "tables": {
            "Employees": ["EmpID", "Name", "DeptID", "HireDate"],
            "Departments": ["DeptID", "DeptName"]
        }
    }
    
    result = generator.generate_clause(filter_node, schema)
    
    if result.success:
        print(f"Generated SQL: {result.sql_clause}")
        print(f"Explanation: {result.explanation}")
        print(f"Confidence: {result.confidence}")
    else:
        print(f"Generation failed: {result.error_message}")
