"""
Stage 1: Syntax Verification

This module implements strict SQL grammar validation using sqlparse.
It ensures generated SQL strictly follows SQL grammatical rules.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import sqlparse
from sqlparse import tokens as T
from sqlparse.sql import Statement, Token
import re


class SyntaxErrorType(Enum):
    """Types of syntax errors"""
    INVALID_SYNTAX = "invalid_syntax"
    INCOMPLETE_STATEMENT = "incomplete_statement"
    UNBALANCED_PARENTHESES = "unbalanced_parentheses"
    INVALID_KEYWORD_ORDER = "invalid_keyword_order"
    MISSING_CLAUSE = "missing_clause"
    INVALID_IDENTIFIER = "invalid_identifier"
    RESERVED_WORD_MISUSE = "reserved_word_misuse"


@dataclass
class SyntaxError:
    """Represents a syntax error"""
    error_type: SyntaxErrorType
    message: str
    position: Optional[int] = None
    suggestion: Optional[str] = None
    severity: str = "ERROR"  # ERROR, WARNING


@dataclass
class SyntaxVerificationResult:
    """Result of syntax verification"""
    is_valid: bool
    errors: List[SyntaxError]
    warnings: List[SyntaxError]
    formatted_sql: Optional[str] = None
    parse_tree: Optional[Any] = None


class SyntaxVerifier:
    """
    Stage 1 Verifier: Strict SQL syntax validation
    
    Uses sqlparse for comprehensive syntax checking including:
    - SQL grammar validation
    - Keyword order verification
    - Parentheses balancing
    - Identifier validation
    - Reserved word checking
    """
    
    # SQL reserved keywords (subset of common ones)
    RESERVED_KEYWORDS = {
        'SELECT', 'FROM', 'WHERE', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'OUTER',
        'ON', 'AND', 'OR', 'NOT', 'IN', 'EXISTS', 'BETWEEN', 'LIKE', 'IS',
        'NULL', 'GROUP', 'BY', 'HAVING', 'ORDER', 'ASC', 'DESC', 'LIMIT',
        'OFFSET', 'UNION', 'INTERSECT', 'EXCEPT', 'AS', 'DISTINCT', 'ALL',
        'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'TABLE',
        'INDEX', 'VIEW', 'WITH', 'RECURSIVE', 'CASE', 'WHEN', 'THEN', 'ELSE',
        'END', 'COUNT', 'SUM', 'AVG', 'MIN', 'MAX'
    }
    
    # Expected clause order in SELECT statements
    CLAUSE_ORDER = [
        'WITH', 'SELECT', 'FROM', 'WHERE', 'GROUP BY', 'HAVING', 
        'ORDER BY', 'LIMIT', 'OFFSET'
    ]
    
    def __init__(self):
        """Initialize syntax verifier"""
        pass
    
    def verify(self, sql: str) -> SyntaxVerificationResult:
        """
        Perform comprehensive syntax verification
        
        Args:
            sql: SQL query to verify
            
        Returns:
            SyntaxVerificationResult with validation details
        """
        errors = []
        warnings = []
        
        # Clean and normalize SQL
        sql = sql.strip()
        if not sql:
            errors.append(SyntaxError(
                error_type=SyntaxErrorType.INCOMPLETE_STATEMENT,
                message="Empty SQL statement",
                severity="ERROR"
            ))
            return SyntaxVerificationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings
            )
        
        # Parse SQL
        try:
            parsed = sqlparse.parse(sql)
            if not parsed:
                errors.append(SyntaxError(
                    error_type=SyntaxErrorType.INVALID_SYNTAX,
                    message="Failed to parse SQL statement",
                    severity="ERROR"
                ))
                return SyntaxVerificationResult(
                    is_valid=False,
                    errors=errors,
                    warnings=warnings
                )
            
            statement = parsed[0]
            
            # Format SQL for readability
            formatted_sql = sqlparse.format(
                sql,
                reindent=True,
                keyword_case='upper',
                identifier_case='lower'
            )
            
        except Exception as e:
            errors.append(SyntaxError(
                error_type=SyntaxErrorType.INVALID_SYNTAX,
                message=f"Parse error: {str(e)}",
                severity="ERROR"
            ))
            return SyntaxVerificationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings
            )
        
        # Run validation checks
        errors.extend(self._check_parentheses(sql))
        errors.extend(self._check_statement_completeness(statement))
        errors.extend(self._check_clause_order(statement))
        errors.extend(self._check_identifiers(statement))
        warnings.extend(self._check_reserved_words(statement))
        warnings.extend(self._check_best_practices(statement))
        
        is_valid = len(errors) == 0
        
        return SyntaxVerificationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            formatted_sql=formatted_sql if is_valid else None,
            parse_tree=statement if is_valid else None
        )
    
    def _check_parentheses(self, sql: str) -> List[SyntaxError]:
        """Check for balanced parentheses"""
        errors = []
        stack = []
        
        for i, char in enumerate(sql):
            if char == '(':
                stack.append(i)
            elif char == ')':
                if not stack:
                    errors.append(SyntaxError(
                        error_type=SyntaxErrorType.UNBALANCED_PARENTHESES,
                        message="Unmatched closing parenthesis",
                        position=i,
                        suggestion="Remove extra ')' or add opening '('"
                    ))
                else:
                    stack.pop()
        
        if stack:
            errors.append(SyntaxError(
                error_type=SyntaxErrorType.UNBALANCED_PARENTHESES,
                message=f"Unclosed parentheses (missing {len(stack)} closing parenthesis)",
                position=stack[0],
                suggestion="Add closing ')' for each opening '('"
            ))
        
        return errors
    
    def _check_statement_completeness(self, statement: Statement) -> List[SyntaxError]:
        """Check if statement is complete"""
        errors = []
        
        # Convert statement to string for analysis
        sql_upper = str(statement).upper()
        
        # Check for SELECT without FROM (unless it's a scalar select)
        if 'SELECT' in sql_upper:
            # Check if it's not just "SELECT 1" or similar
            if not re.search(r'SELECT\s+\d+', sql_upper) and 'FROM' not in sql_upper:
                # Allow SELECT without FROM for expressions like SELECT 1, SELECT NOW(), etc.
                if not re.search(r'SELECT\s+[\w\(\)]+\s*$', sql_upper):
                    errors.append(SyntaxError(
                        error_type=SyntaxErrorType.MISSING_CLAUSE,
                        message="SELECT statement missing FROM clause",
                        suggestion="Add FROM clause to specify table"
                    ))
        
        # Check for JOIN without ON/USING
        if 'JOIN' in sql_upper and 'CROSS JOIN' not in sql_upper and 'NATURAL JOIN' not in sql_upper:
            # Simple check: if JOIN exists, ON or USING should exist
            if 'ON' not in sql_upper and 'USING' not in sql_upper:
                errors.append(SyntaxError(
                    error_type=SyntaxErrorType.MISSING_CLAUSE,
                    message="JOIN clause missing ON or USING condition",
                    suggestion="Add ON condition to specify join relationship"
                ))
        
        # Check for GROUP BY with aggregation
        if 'GROUP BY' in sql_upper:
            # Should have aggregation function
            has_agg = any(func in sql_upper for func in ['COUNT(', 'SUM(', 'AVG(', 'MIN(', 'MAX('])
            if not has_agg:
                # This is a warning, not an error
                pass
        
        return errors
    
    def _check_clause_order(self, statement: Statement) -> List[SyntaxError]:
        """Check if SQL clauses are in correct order"""
        errors = []
        
        sql_upper = str(statement).upper()
        
        # Find positions of clauses
        clause_positions = {}
        for clause in self.CLAUSE_ORDER:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + clause.replace(' ', r'\s+') + r'\b'
            match = re.search(pattern, sql_upper)
            if match:
                clause_positions[clause] = match.start()
        
        # Check order
        found_clauses = sorted(clause_positions.items(), key=lambda x: x[1])
        expected_order = [c for c in self.CLAUSE_ORDER if c in clause_positions]
        actual_order = [c[0] for c in found_clauses]
        
        if actual_order != expected_order:
            errors.append(SyntaxError(
                error_type=SyntaxErrorType.INVALID_KEYWORD_ORDER,
                message=f"Incorrect clause order. Expected: {' -> '.join(expected_order)}, Got: {' -> '.join(actual_order)}",
                suggestion=f"Reorder clauses to: {' -> '.join(expected_order)}"
            ))
        
        return errors
    
    def _check_identifiers(self, statement: Statement) -> List[SyntaxError]:
        """Check identifier validity"""
        errors = []
        
        # SQL identifier rules:
        # - Must start with letter or underscore
        # - Can contain letters, digits, underscores
        # - Can be quoted with backticks, double quotes, or square brackets
        
        identifier_pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
        
        # Extract identifiers (simplified - would need more sophisticated parsing)
        sql = str(statement)
        
        # Find potential identifiers (this is a simplified check)
        # In practice, would need to parse the token stream more carefully
        tokens = statement.flatten()
        
        for token in tokens:
            if token.ttype in (T.Name, T.Name.Placeholder):
                identifier = token.value
                
                # Skip if quoted
                if identifier.startswith('"') or identifier.startswith('`') or identifier.startswith('['):
                    continue
                
                # Check if it's a reserved keyword used as identifier
                if identifier.upper() in self.RESERVED_KEYWORDS:
                    errors.append(SyntaxError(
                        error_type=SyntaxErrorType.RESERVED_WORD_MISUSE,
                        message=f"Reserved keyword '{identifier}' used as identifier",
                        suggestion=f"Quote the identifier: \"{identifier}\" or use a different name"
                    ))
                
                # Check identifier format
                if not re.match(identifier_pattern, identifier):
                    errors.append(SyntaxError(
                        error_type=SyntaxErrorType.INVALID_IDENTIFIER,
                        message=f"Invalid identifier '{identifier}'",
                        suggestion="Identifiers must start with letter/underscore and contain only letters, digits, underscores"
                    ))
        
        return errors
    
    def _check_reserved_words(self, statement: Statement) -> List[SyntaxError]:
        """Check for reserved word usage (warnings)"""
        warnings = []
        
        # This is handled in _check_identifiers, but we can add additional checks
        # For example, checking for common mistakes
        
        sql_upper = str(statement).upper()
        
        # Check for common mistakes
        if 'WHERE AND' in sql_upper or 'WHERE OR' in sql_upper:
            warnings.append(SyntaxError(
                error_type=SyntaxErrorType.INVALID_SYNTAX,
                message="WHERE clause starts with AND/OR",
                suggestion="Remove leading AND/OR from WHERE clause",
                severity="WARNING"
            ))
        
        return warnings
    
    def _check_best_practices(self, statement: Statement) -> List[SyntaxError]:
        """Check for SQL best practices (warnings)"""
        warnings = []
        
        sql = str(statement)
        sql_upper = sql.upper()
        
        # Check for SELECT *
        if re.search(r'SELECT\s+\*', sql_upper):
            warnings.append(SyntaxError(
                error_type=SyntaxErrorType.INVALID_SYNTAX,
                message="Using SELECT * is not recommended",
                suggestion="Specify explicit column names for better performance and clarity",
                severity="WARNING"
            ))
        
        # Check for missing table aliases in joins
        if 'JOIN' in sql_upper and sql.count('.') < 2:
            warnings.append(SyntaxError(
                error_type=SyntaxErrorType.INVALID_SYNTAX,
                message="Table aliases recommended for JOIN queries",
                suggestion="Use table aliases to improve query readability",
                severity="WARNING"
            ))
        
        # Check for very long queries (potential complexity issue)
        if len(sql) > 1000:
            warnings.append(SyntaxError(
                error_type=SyntaxErrorType.INVALID_SYNTAX,
                message="Very long SQL query detected",
                suggestion="Consider breaking into CTEs or subqueries for better readability",
                severity="WARNING"
            ))
        
        return warnings
    
    def format_sql(self, sql: str) -> str:
        """Format SQL for readability"""
        try:
            return sqlparse.format(
                sql,
                reindent=True,
                keyword_case='upper',
                identifier_case='lower',
                indent_width=2
            )
        except:
            return sql


# Example usage
if __name__ == "__main__":
    verifier = SyntaxVerifier()
    
    # Test cases
    test_queries = [
        "SELECT * FROM employees",
        "SELECT name, salary FROM employees WHERE salary > 50000",
        "SELECT * FROM employees WHERE",  # Incomplete
        "SELECT * FROM employees WHERE (salary > 50000",  # Unbalanced
        "SELECT name FROM employees JOIN departments",  # Missing ON
        "SELECT * FROM WHERE name = 'John'",  # Missing table
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}: {query}")
        print('='*60)
        
        result = verifier.verify(query)
        
        print(f"Valid: {result.is_valid}")
        
        if result.errors:
            print("\nErrors:")
            for error in result.errors:
                print(f"  - [{error.error_type.value}] {error.message}")
                if error.suggestion:
                    print(f"    Suggestion: {error.suggestion}")
        
        if result.warnings:
            print("\nWarnings:")
            for warning in result.warnings:
                print(f"  - {warning.message}")
        
        if result.formatted_sql:
            print(f"\nFormatted SQL:\n{result.formatted_sql}")
