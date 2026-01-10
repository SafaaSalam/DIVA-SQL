"""
Verification & Alignment Agent for DIVA-SQL

This agent is responsible for verifying that generated SQL clauses correctly
implement the semantic intent and are free from common errors.
"""

from typing import Dict, List, Optional, Any, Tuple
import json
import re
from dataclasses import dataclass
from enum import Enum

from ..core.semantic_dag import SemanticNode
from ..utils.prompts import VerifierPrompts
from ..utils.error_taxonomy import ErrorTaxonomy


class VerificationStatus(Enum):
    """Status of verification checks"""
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    UNKNOWN = "UNKNOWN"


@dataclass
class VerificationIssue:
    """Represents a verification issue"""
    type: str
    description: str
    severity: str  # HIGH, MEDIUM, LOW
    suggested_fix: Optional[str] = None


@dataclass
class VerificationResult:
    """Result of SQL clause verification"""
    status: VerificationStatus
    issues: List[VerificationIssue]
    confidence: float
    detailed_feedback: Optional[str] = None
    execution_info: Optional[Dict[str, Any]] = None


class VerificationAgent:
    """
    Agent responsible for verifying SQL clauses against semantic intent
    """
    
    def __init__(self, llm_client, model_name: str = "gpt-4"):
        self.llm_client = llm_client
        self.model_name = model_name
        self.prompts = VerifierPrompts()
        self.error_taxonomy = ErrorTaxonomy()
    
    def verify_clause(self, 
                     semantic_node: SemanticNode,
                     sql_clause: str,
                     database_schema: Dict[str, Any],
                     execution_result: Optional[Dict[str, Any]] = None) -> VerificationResult:
        """
        Comprehensive verification of a SQL clause
        
        Args:
            semantic_node: The semantic intent to verify against
            sql_clause: The generated SQL clause
            database_schema: Database schema information
            execution_result: Optional execution result for sanity checking
            
        Returns:
            VerificationResult with overall status and detailed feedback
        """
        all_issues = []
        confidence_scores = []
        
        # 1. Schema Alignment Check
        schema_result = self._check_schema_alignment(
            semantic_node, sql_clause, database_schema
        )
        all_issues.extend(schema_result.issues)
        confidence_scores.append(schema_result.confidence)
        
        # 2. Error Pattern Check
        pattern_result = self._check_error_patterns(sql_clause)
        all_issues.extend(pattern_result.issues)
        confidence_scores.append(pattern_result.confidence)
        
        # 3. Execution Sanity Check (if execution result provided)
        if execution_result:
            execution_result_check = self._check_execution_sanity(sql_clause, execution_result)
            all_issues.extend(execution_result_check.issues)
            confidence_scores.append(execution_result_check.confidence)
        
        # 4. Semantic Logic Check
        logic_result = self._check_semantic_logic(semantic_node, sql_clause, database_schema)
        all_issues.extend(logic_result.issues)
        confidence_scores.append(logic_result.confidence)
        
        # Determine overall status
        high_issues = [issue for issue in all_issues if issue.severity == "HIGH"]
        medium_issues = [issue for issue in all_issues if issue.severity == "MEDIUM"]
        
        if high_issues:
            status = VerificationStatus.FAIL
        elif medium_issues:
            status = VerificationStatus.WARNING
        else:
            status = VerificationStatus.PASS
        
        # Calculate overall confidence
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        # Generate detailed feedback
        feedback = self._generate_detailed_feedback(all_issues, status)
        
        return VerificationResult(
            status=status,
            issues=all_issues,
            confidence=overall_confidence,
            detailed_feedback=feedback,
            execution_info=execution_result
        )
    
    def _check_schema_alignment(self, 
                              semantic_node: SemanticNode,
                              sql_clause: str,
                              database_schema: Dict[str, Any]) -> VerificationResult:
        """
        Check if SQL clause uses correct schema elements
        """
        issues = []
        
        try:
            # Use LLM for sophisticated schema alignment check
            prompt = self.prompts.get_schema_alignment_prompt(
                semantic_node, sql_clause, database_schema
            )
            
            response = self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            alignment_data = json.loads(response.choices[0].message.content)
            
            # Convert LLM response to VerificationIssues
            for issue_data in alignment_data.get("issues", []):
                issues.append(VerificationIssue(
                    type=issue_data["type"],
                    description=issue_data["description"],
                    severity=issue_data["severity"]
                ))
            
            confidence = alignment_data.get("confidence", 0.7)
            
        except Exception as e:
            # Fallback to rule-based schema checking
            issues, confidence = self._rule_based_schema_check(
                semantic_node, sql_clause, database_schema
            )
        
        status = VerificationStatus.FAIL if any(i.severity == "HIGH" for i in issues) else VerificationStatus.PASS
        
        return VerificationResult(
            status=status,
            issues=issues,
            confidence=confidence
        )
    
    def _rule_based_schema_check(self, 
                               semantic_node: SemanticNode,
                               sql_clause: str,
                               database_schema: Dict[str, Any]) -> Tuple[List[VerificationIssue], float]:
        """
        Rule-based schema validation as fallback
        """
        issues = []
        
        # Extract table and column references from SQL
        table_refs = self._extract_table_references(sql_clause)
        column_refs = self._extract_column_references(sql_clause)
        
        # Check if referenced tables exist in schema
        available_tables = set(database_schema.get("tables", {}).keys())
        for table in table_refs:
            if table not in available_tables:
                issues.append(VerificationIssue(
                    type="TABLE_MISMATCH",
                    description=f"Table '{table}' not found in database schema",
                    severity="HIGH",
                    suggested_fix=f"Use one of: {', '.join(available_tables)}"
                ))
        
        # Check if referenced columns exist in their tables
        for table, columns in column_refs.items():
            if table in available_tables:
                available_columns = set(database_schema["tables"][table])
                for column in columns:
                    if column not in available_columns:
                        issues.append(VerificationIssue(
                            type="COLUMN_MISMATCH",
                            description=f"Column '{column}' not found in table '{table}'",
                            severity="HIGH",
                            suggested_fix=f"Use one of: {', '.join(available_columns)}"
                        ))
        
        # Check if semantic node's expected tables/columns are used
        expected_tables = set(semantic_node.tables)
        expected_columns = set(semantic_node.columns)
        
        used_tables = set(table_refs)
        used_columns = set()
        for cols in column_refs.values():
            used_columns.update(cols)
        
        # Check for missing expected tables
        missing_tables = expected_tables - used_tables
        if missing_tables:
            issues.append(VerificationIssue(
                type="LOGIC_MISMATCH",
                description=f"Expected tables not used: {', '.join(missing_tables)}",
                severity="MEDIUM",
                suggested_fix=f"Consider including tables: {', '.join(missing_tables)}"
            ))
        
        # Check for missing expected columns
        missing_columns = expected_columns - used_columns
        if missing_columns:
            issues.append(VerificationIssue(
                type="LOGIC_MISMATCH",
                description=f"Expected columns not used: {', '.join(missing_columns)}",
                severity="MEDIUM",
                suggested_fix=f"Consider including columns: {', '.join(missing_columns)}"
            ))
        
        confidence = 0.8 if not issues else 0.6
        return issues, confidence
    
    def _check_error_patterns(self, sql_clause: str) -> VerificationResult:
        """
        Check for common SQL error patterns
        """
        issues = []
        
        try:
            # Get known error patterns from taxonomy
            known_patterns = self.error_taxonomy.get_common_patterns()
            
            # Use LLM for pattern detection
            prompt = self.prompts.get_error_pattern_prompt(sql_clause, known_patterns)
            
            response = self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            pattern_data = json.loads(response.choices[0].message.content)
            
            # Convert detected errors to VerificationIssues
            for error_data in pattern_data.get("errors_found", []):
                issues.append(VerificationIssue(
                    type=error_data["pattern"],
                    description=error_data["description"],
                    severity=error_data["severity"],
                    suggested_fix=error_data.get("suggested_fix")
                ))
            
            confidence = pattern_data.get("confidence", 0.7)
            
        except Exception as e:
            # Fallback to rule-based pattern checking
            issues, confidence = self._rule_based_pattern_check(sql_clause)
        
        status = VerificationStatus.FAIL if any(i.severity == "HIGH" for i in issues) else VerificationStatus.PASS
        
        return VerificationResult(
            status=status,
            issues=issues,
            confidence=confidence
        )
    
    def _rule_based_pattern_check(self, sql_clause: str) -> Tuple[List[VerificationIssue], float]:
        """
        Rule-based error pattern detection as fallback
        """
        issues = []
        clause_upper = sql_clause.upper()
        
        # Pattern 1: Comparing ID to string literal
        if re.search(r'\b\w*ID\s*=\s*\'[^\']*\'', sql_clause, re.IGNORECASE):
            issues.append(VerificationIssue(
                type="ID_STRING_COMPARISON",
                description="Comparing ID column to string literal",
                severity="HIGH",
                suggested_fix="Use numeric comparison for ID columns"
            ))
        
        # Pattern 2: Missing JOIN when using multiple tables
        table_refs = self._extract_table_references(sql_clause)
        if len(table_refs) > 1 and "JOIN" not in clause_upper:
            issues.append(VerificationIssue(
                type="MISSING_JOIN",
                description="Multiple tables referenced without explicit JOIN",
                severity="HIGH",
                suggested_fix="Add explicit JOIN clause"
            ))
        
        # Pattern 3: Aggregation without GROUP BY
        agg_functions = ["COUNT", "SUM", "AVG", "MAX", "MIN"]
        has_aggregation = any(func in clause_upper for func in agg_functions)
        has_group_by = "GROUP BY" in clause_upper
        
        if has_aggregation and not has_group_by and "SELECT" in clause_upper:
            # Check if there are non-aggregate columns in SELECT
            select_match = re.search(r'SELECT\s+(.+?)(?:\s+FROM|\s+WHERE|$)', sql_clause, re.IGNORECASE | re.DOTALL)
            if select_match:
                select_list = select_match.group(1)
                has_non_agg_columns = any(
                    col.strip() for col in select_list.split(',') 
                    if not any(agg in col.upper() for agg in agg_functions)
                )
                if has_non_agg_columns:
                    issues.append(VerificationIssue(
                        type="MISSING_GROUP_BY",
                        description="Aggregation with non-aggregate columns but no GROUP BY",
                        severity="HIGH",
                        suggested_fix="Add GROUP BY clause or remove non-aggregate columns"
                    ))
        
        # Pattern 4: Date comparison issues
        date_patterns = [
            r"date\s*[><=]\s*'\d{4}'",  # Date compared to year only
            r"date\s*[><=]\s*\d{4}",    # Date compared to numeric year
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, sql_clause, re.IGNORECASE):
                issues.append(VerificationIssue(
                    type="DATE_FORMAT_ERROR",
                    description="Incorrect date format in comparison",
                    severity="MEDIUM",
                    suggested_fix="Use proper date format: 'YYYY-MM-DD'"
                ))
        
        # Pattern 5: Ambiguous column references
        if re.search(r'\b\w+\.\w+\s+AND\s+\w+(?!\.|AS)', sql_clause, re.IGNORECASE):
            issues.append(VerificationIssue(
                type="AMBIGUOUS_COLUMN",
                description="Possible ambiguous column reference",
                severity="LOW",
                suggested_fix="Use table aliases consistently"
            ))
        
        confidence = 0.7 if not issues else 0.8
        return issues, confidence
    
    def _check_execution_sanity(self, 
                              sql_clause: str,
                              execution_result: Dict[str, Any]) -> VerificationResult:
        """
        Check if execution result makes sense
        """
        issues = []
        
        try:
            # Use LLM for sophisticated execution analysis
            prompt = self.prompts.get_execution_sanity_prompt(sql_clause, execution_result)
            
            response = self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            sanity_data = json.loads(response.choices[0].message.content)
            
            # Convert analysis results to VerificationIssues
            for issue_data in sanity_data.get("issues", []):
                issues.append(VerificationIssue(
                    type=issue_data["type"],
                    description=issue_data["description"],
                    severity=issue_data["severity"]
                ))
            
            confidence = sanity_data.get("confidence", 0.7)
            
        except Exception as e:
            # Fallback to rule-based execution checking
            issues, confidence = self._rule_based_execution_check(execution_result)
        
        status = VerificationStatus.FAIL if any(i.severity == "HIGH" for i in issues) else VerificationStatus.PASS
        
        return VerificationResult(
            status=status,
            issues=issues,
            confidence=confidence
        )
    
    def _rule_based_execution_check(self, execution_result: Dict[str, Any]) -> Tuple[List[VerificationIssue], float]:
        """
        Rule-based execution result validation
        """
        issues = []
        
        # Check for execution errors
        if execution_result.get("error"):
            issues.append(VerificationIssue(
                type="EXECUTION_ERROR",
                description=f"SQL execution failed: {execution_result['error']}",
                severity="HIGH",
                suggested_fix="Fix SQL syntax or logic errors"
            ))
        
        # Check for empty results when they might not be expected
        row_count = execution_result.get("row_count", 0)
        if row_count == 0:
            issues.append(VerificationIssue(
                type="EMPTY_RESULT",
                description="Query returned no results",
                severity="MEDIUM",
                suggested_fix="Verify filter conditions and data existence"
            ))
        
        # Check for suspiciously large result sets
        if row_count > 10000:
            issues.append(VerificationIssue(
                type="LARGE_RESULT",
                description=f"Query returned {row_count} rows, which may be excessive",
                severity="LOW",
                suggested_fix="Consider adding LIMIT clause or more restrictive filters"
            ))
        
        # Check execution time
        execution_time = execution_result.get("execution_time_ms", 0)
        if execution_time > 5000:  # 5 seconds
            issues.append(VerificationIssue(
                type="PERFORMANCE",
                description=f"Query took {execution_time}ms to execute",
                severity="MEDIUM",
                suggested_fix="Consider optimizing query with indexes or better joins"
            ))
        
        confidence = 0.8 if not issues else 0.6
        return issues, confidence
    
    def _check_semantic_logic(self, 
                            semantic_node: SemanticNode,
                            sql_clause: str,
                            database_schema: Dict[str, Any]) -> VerificationResult:
        """
        Check if SQL logic matches semantic intent
        """
        issues = []
        
        # Basic semantic checks based on node type
        node_type = semantic_node.node_type
        description = semantic_node.description.lower()
        clause_upper = sql_clause.upper()
        
        # Check if SQL clause type matches semantic node type
        type_mappings = {
            "FILTER": ["WHERE", "HAVING"],
            "JOIN": ["JOIN"],
            "GROUP": ["GROUP BY"],
            "AGGREGATE": ["COUNT", "SUM", "AVG", "MAX", "MIN"],
            "SELECT": ["SELECT"],
            "ORDER": ["ORDER BY"],
            "LIMIT": ["LIMIT"]
        }
        
        expected_keywords = type_mappings.get(node_type.value, [])
        has_expected_keyword = any(keyword in clause_upper for keyword in expected_keywords)
        
        if not has_expected_keyword:
            issues.append(VerificationIssue(
                type="LOGIC_MISMATCH",
                description=f"SQL clause doesn't contain expected keywords for {node_type.value} operation",
                severity="HIGH",
                suggested_fix=f"Ensure clause contains one of: {', '.join(expected_keywords)}"
            ))
        
        # Check specific semantic patterns
        if "after" in description and node_type.value == "FILTER":
            if ">" not in sql_clause and ">=" not in sql_clause:
                issues.append(VerificationIssue(
                    type="LOGIC_MISMATCH",
                    description="'After' condition should use > or >= operator",
                    severity="MEDIUM",
                    suggested_fix="Use > or >= for 'after' conditions"
                ))
        
        if "before" in description and node_type.value == "FILTER":
            if "<" not in sql_clause and "<=" not in sql_clause:
                issues.append(VerificationIssue(
                    type="LOGIC_MISMATCH",
                    description="'Before' condition should use < or <= operator",
                    severity="MEDIUM",
                    suggested_fix="Use < or <= for 'before' conditions"
                ))
        
        if "more than" in description or "greater than" in description:
            if ">" not in sql_clause:
                issues.append(VerificationIssue(
                    type="LOGIC_MISMATCH",
                    description="'More than' condition should use > operator",
                    severity="MEDIUM",
                    suggested_fix="Use > operator for 'more than' conditions"
                ))
        
        confidence = 0.7 if not issues else 0.5
        status = VerificationStatus.FAIL if any(i.severity == "HIGH" for i in issues) else VerificationStatus.PASS
        
        return VerificationResult(
            status=status,
            issues=issues,
            confidence=confidence
        )
    
    def _extract_table_references(self, sql_clause: str) -> List[str]:
        """
        Extract table references from SQL clause
        """
        tables = []
        
        # Look for FROM clauses
        from_matches = re.findall(r'FROM\s+(\w+)', sql_clause, re.IGNORECASE)
        tables.extend(from_matches)
        
        # Look for JOIN clauses
        join_matches = re.findall(r'JOIN\s+(\w+)', sql_clause, re.IGNORECASE)
        tables.extend(join_matches)
        
        # Look for table.column patterns
        table_col_matches = re.findall(r'(\w+)\.\w+', sql_clause)
        for match in table_col_matches:
            if match not in ["T1", "T2", "T3", "T4", "T5"]:  # Skip common aliases
                tables.append(match)
        
        return list(set(tables))  # Remove duplicates
    
    def _extract_column_references(self, sql_clause: str) -> Dict[str, List[str]]:
        """
        Extract column references grouped by table
        """
        column_refs = {}
        
        # Look for table.column patterns
        table_col_matches = re.findall(r'([A-Za-z]\w*)\\.([A-Za-z]\w*)', sql_clause)
        
        for table, column in table_col_matches:
            if table not in column_refs:
                column_refs[table] = []
            column_refs[table].append(column)
        
        return column_refs
    
    def _generate_detailed_feedback(self, 
                                  issues: List[VerificationIssue],
                                  status: VerificationStatus) -> str:
        """
        Generate detailed feedback message
        """
        if status == VerificationStatus.PASS:
            return "SQL clause verification passed. No issues detected."
        
        feedback_lines = [f"Verification Status: {status.value}"]
        
        if issues:
            feedback_lines.append("\nIssues Detected:")
            
            high_issues = [i for i in issues if i.severity == "HIGH"]
            medium_issues = [i for i in issues if i.severity == "MEDIUM"]
            low_issues = [i for i in issues if i.severity == "LOW"]
            
            for issue_list, severity in [(high_issues, "HIGH"), (medium_issues, "MEDIUM"), (low_issues, "LOW")]:
                if issue_list:
                    feedback_lines.append(f"\n{severity} Severity:")
                    for issue in issue_list:
                        feedback_lines.append(f"  - {issue.description}")
                        if issue.suggested_fix:
                            feedback_lines.append(f"    Fix: {issue.suggested_fix}")
        
        return "\n".join(feedback_lines)


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
                                content = '{"is_aligned": true, "issues": [], "confidence": 0.9}'
                        choices = [Choice()]
                    return Response()
        chat = Chat()
    
    # Test the verifier
    verifier = VerificationAgent(MockLLMClient())
    
    # Test semantic node
    filter_node = SemanticNode(
        id="filter_employees",
        node_type=NodeType.FILTER,
        description="Find employees hired after 2022",
        tables=["Employees"],
        columns=["HireDate"],
        conditions=["HireDate > '2022-01-01'"]
    )
    
    sql_clause = "WHERE T1.HireDate > '2022-01-01'"
    schema = {
        "tables": {
            "Employees": ["EmpID", "Name", "DeptID", "HireDate"],
        }
    }
    
    result = verifier.verify_clause(filter_node, sql_clause, schema)
    
    print(f"Verification Status: {result.status}")
    print(f"Confidence: {result.confidence}")
    print(f"Issues: {len(result.issues)}")
    if result.detailed_feedback:
        print(f"Feedback:\n{result.detailed_feedback}")
