"""
Stage 2: Semantic Alignment Verification

This module verifies that generated SQL aligns with the database schema.
It checks column/table existence, data type compatibility, and semantic correctness.
"""

from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import sqlparse
from sqlparse import tokens as T
from sqlparse.sql import Statement, Identifier, IdentifierList, Where, Comparison
import re


class SemanticErrorType(Enum):
    """Types of semantic errors"""
    TABLE_NOT_FOUND = "table_not_found"
    COLUMN_NOT_FOUND = "column_not_found"
    AMBIGUOUS_COLUMN = "ambiguous_column"
    TYPE_MISMATCH = "type_mismatch"
    INVALID_AGGREGATION = "invalid_aggregation"
    INVALID_JOIN = "invalid_join"
    MISSING_GROUP_BY = "missing_group_by"
    INVALID_COMPARISON = "invalid_comparison"


@dataclass
class SemanticError:
    """Represents a semantic error"""
    error_type: SemanticErrorType
    message: str
    element: str  # The problematic element (table/column name)
    suggestion: Optional[str] = None
    severity: str = "ERROR"


@dataclass
class SemanticVerificationResult:
    """Result of semantic verification"""
    is_valid: bool
    errors: List[SemanticError]
    warnings: List[SemanticError]
    validated_tables: List[str]
    validated_columns: List[str]
    schema_info: Dict[str, Any]


class SemanticVerifier:
    """
    Stage 2 Verifier: Semantic alignment with database schema
    
    Verifies:
    - Table existence in schema
    - Column existence in referenced tables
    - Data type compatibility
    - Aggregation validity
    - JOIN relationship correctness
    - GROUP BY requirements
    """
    
    def __init__(self, database_schema: Dict[str, Any]):
        """
        Initialize semantic verifier
        
        Args:
            database_schema: Database schema information
                Format: {
                    "tables": {
                        "table_name": {
                            "columns": {
                                "column_name": {"type": "INTEGER", "nullable": True},
                                ...
                            },
                            "primary_key": ["id"],
                            "foreign_keys": {
                                "dept_id": {"references": "departments.id"}
                            }
                        }
                    }
                }
        """
        self.schema = database_schema
        self.tables = self._extract_tables()
        self.columns_by_table = self._extract_columns()
    
    def _extract_tables(self) -> Set[str]:
        """Extract all table names from schema"""
        if isinstance(self.schema, dict):
            if 'tables' in self.schema:
                return set(self.schema['tables'].keys())
            else:
                # Assume schema is direct table mapping
                return set(self.schema.keys())
        return set()
    
    def _extract_columns(self) -> Dict[str, Set[str]]:
        """Extract columns for each table"""
        columns = {}
        
        if isinstance(self.schema, dict):
            tables_dict = self.schema.get('tables', self.schema)
            
            for table_name, table_info in tables_dict.items():
                if isinstance(table_info, dict):
                    if 'columns' in table_info:
                        if isinstance(table_info['columns'], dict):
                            columns[table_name] = set(table_info['columns'].keys())
                        elif isinstance(table_info['columns'], list):
                            columns[table_name] = set(table_info['columns'])
                    else:
                        columns[table_name] = set()
                elif isinstance(table_info, list):
                    # Schema format: {"table_name": ["col1", "col2", ...]}
                    columns[table_name] = set(table_info)
        
        return columns
    
    def verify(self, sql: str, semantic_node: Optional[Any] = None) -> SemanticVerificationResult:
        """
        Perform semantic verification
        
        Args:
            sql: SQL query to verify
            semantic_node: Optional semantic node for additional context
            
        Returns:
            SemanticVerificationResult with validation details
        """
        errors = []
        warnings = []
        validated_tables = []
        validated_columns = []
        
        # Parse SQL
        try:
            parsed = sqlparse.parse(sql)
            if not parsed:
                errors.append(SemanticError(
                    error_type=SemanticErrorType.TABLE_NOT_FOUND,
                    message="Failed to parse SQL for semantic analysis",
                    element="",
                    severity="ERROR"
                ))
                return SemanticVerificationResult(
                    is_valid=False,
                    errors=errors,
                    warnings=warnings,
                    validated_tables=[],
                    validated_columns=[],
                    schema_info={}
                )
            
            statement = parsed[0]
            
        except Exception as e:
            errors.append(SemanticError(
                error_type=SemanticErrorType.TABLE_NOT_FOUND,
                message=f"Parse error: {str(e)}",
                element="",
                severity="ERROR"
            ))
            return SemanticVerificationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                validated_tables=[],
                validated_columns=[],
                schema_info={}
            )
        
        # Extract referenced tables and columns
        referenced_tables = self._extract_referenced_tables(statement)
        referenced_columns = self._extract_referenced_columns(statement)
        
        # Verify tables exist
        table_errors, valid_tables = self._verify_tables(referenced_tables)
        errors.extend(table_errors)
        validated_tables.extend(valid_tables)
        
        # Verify columns exist
        column_errors, valid_columns = self._verify_columns(referenced_columns, valid_tables)
        errors.extend(column_errors)
        validated_columns.extend(valid_columns)
        
        # Verify aggregations
        agg_errors = self._verify_aggregations(statement)
        errors.extend(agg_errors)
        
        # Verify JOINs
        join_errors = self._verify_joins(statement, valid_tables)
        errors.extend(join_errors)
        
        # Verify GROUP BY requirements
        group_errors = self._verify_group_by(statement)
        warnings.extend(group_errors)
        
        # Verify data type compatibility
        type_warnings = self._verify_type_compatibility(statement, valid_tables)
        warnings.extend(type_warnings)
        
        is_valid = len(errors) == 0
        
        return SemanticVerificationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            validated_tables=validated_tables,
            validated_columns=validated_columns,
            schema_info={
                "referenced_tables": list(referenced_tables),
                "referenced_columns": list(referenced_columns)
            }
        )
    
    def _extract_referenced_tables(self, statement: Statement) -> Set[str]:
        """Extract all table references from SQL"""
        tables = set()
        sql_upper = str(statement).upper()
        
        # Extract from FROM clause
        from_match = re.search(r'FROM\s+([\w\s,\.]+?)(?:WHERE|JOIN|GROUP|ORDER|LIMIT|$)', sql_upper, re.IGNORECASE)
        if from_match:
            from_clause = from_match.group(1)
            # Split by comma and extract table names
            for part in from_clause.split(','):
                # Remove aliases (words after AS or space)
                table = re.split(r'\s+AS\s+|\s+', part.strip())[0]
                if table:
                    tables.add(table.lower())
        
        # Extract from JOIN clauses
        join_matches = re.finditer(r'JOIN\s+([\w\.]+)', sql_upper, re.IGNORECASE)
        for match in join_matches:
            table = match.group(1).lower()
            tables.add(table)
        
        return tables
    
    def _extract_referenced_columns(self, statement: Statement) -> Set[str]:
        """Extract all column references from SQL"""
        columns = set()
        sql = str(statement)
        
        # This is a simplified extraction
        # In practice, would need more sophisticated parsing
        
        # Extract from SELECT clause
        select_match = re.search(r'SELECT\s+(.*?)\s+FROM', sql, re.IGNORECASE | re.DOTALL)
        if select_match:
            select_clause = select_match.group(1)
            # Skip if SELECT *
            if '*' not in select_clause:
                # Extract column names (simplified)
                parts = select_clause.split(',')
                for part in parts:
                    # Remove functions, aliases, etc.
                    # This is very simplified
                    col_match = re.search(r'([\w\.]+)', part.strip())
                    if col_match:
                        col = col_match.group(1)
                        if '.' in col:
                            col = col.split('.')[1]
                        columns.add(col.lower())
        
        # Extract from WHERE clause
        where_match = re.search(r'WHERE\s+(.*?)(?:GROUP|ORDER|LIMIT|$)', sql, re.IGNORECASE | re.DOTALL)
        if where_match:
            where_clause = where_match.group(1)
            # Extract column names
            col_matches = re.finditer(r'\b([\w\.]+)\s*[=<>!]', where_clause)
            for match in col_matches:
                col = match.group(1)
                if '.' in col:
                    col = col.split('.')[1]
                if col.lower() not in ['and', 'or', 'not']:
                    columns.add(col.lower())
        
        return columns
    
    def _verify_tables(self, referenced_tables: Set[str]) -> Tuple[List[SemanticError], List[str]]:
        """Verify that all referenced tables exist in schema"""
        errors = []
        valid_tables = []
        
        for table in referenced_tables:
            if table.lower() not in {t.lower() for t in self.tables}:
                # Try to find similar table names
                suggestion = self._find_similar_name(table, self.tables)
                errors.append(SemanticError(
                    error_type=SemanticErrorType.TABLE_NOT_FOUND,
                    message=f"Table '{table}' not found in schema",
                    element=table,
                    suggestion=f"Did you mean '{suggestion}'?" if suggestion else "Check available tables in schema"
                ))
            else:
                valid_tables.append(table)
        
        return errors, valid_tables
    
    def _verify_columns(self, referenced_columns: Set[str], valid_tables: List[str]) -> Tuple[List[SemanticError], List[str]]:
        """Verify that all referenced columns exist in their tables"""
        errors = []
        valid_columns = []
        
        # If no valid tables, can't verify columns
        if not valid_tables:
            return errors, valid_columns
        
        # Get all available columns from valid tables
        available_columns = set()
        for table in valid_tables:
            table_lower = table.lower()
            for schema_table, columns in self.columns_by_table.items():
                if schema_table.lower() == table_lower:
                    available_columns.update({c.lower() for c in columns})
        
        for column in referenced_columns:
            if column.lower() not in available_columns:
                # Try to find similar column names
                suggestion = self._find_similar_name(column, available_columns)
                errors.append(SemanticError(
                    error_type=SemanticErrorType.COLUMN_NOT_FOUND,
                    message=f"Column '{column}' not found in referenced tables",
                    element=column,
                    suggestion=f"Did you mean '{suggestion}'?" if suggestion else "Check available columns in schema"
                ))
            else:
                valid_columns.append(column)
        
        return errors, valid_columns
    
    def _verify_aggregations(self, statement: Statement) -> List[SemanticError]:
        """Verify aggregation function usage"""
        errors = []
        sql_upper = str(statement).upper()
        
        # Check for aggregation functions
        agg_functions = ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX']
        has_aggregation = any(f'{func}(' in sql_upper for func in agg_functions)
        
        if has_aggregation:
            # If there's aggregation, should have GROUP BY or be a single aggregation
            has_group_by = 'GROUP BY' in sql_upper
            
            # Count non-aggregated columns in SELECT
            # This is simplified - would need proper parsing
            select_match = re.search(r'SELECT\s+(.*?)\s+FROM', sql_upper, re.IGNORECASE)
            if select_match and not has_group_by:
                select_clause = select_match.group(1)
                # Check if there are non-aggregated columns
                # This is a simplified check
                if ',' in select_clause:
                    # Multiple columns - might need GROUP BY
                    pass  # This would be a warning, not an error
        
        return errors
    
    def _verify_joins(self, statement: Statement, valid_tables: List[str]) -> List[SemanticError]:
        """Verify JOIN relationships"""
        errors = []
        sql_upper = str(statement).upper()
        
        # Check if JOINs reference valid foreign keys
        # This is simplified - would need schema foreign key information
        
        join_matches = re.finditer(r'JOIN\s+(\w+)\s+ON\s+([\w\.]+)\s*=\s*([\w\.]+)', sql_upper, re.IGNORECASE)
        for match in join_matches:
            join_table = match.group(1).lower()
            left_col = match.group(2).lower()
            right_col = match.group(3).lower()
            
            # Verify join table exists
            if join_table not in {t.lower() for t in valid_tables}:
                errors.append(SemanticError(
                    error_type=SemanticErrorType.INVALID_JOIN,
                    message=f"JOIN references unknown table '{join_table}'",
                    element=join_table
                ))
        
        return errors
    
    def _verify_group_by(self, statement: Statement) -> List[SemanticError]:
        """Verify GROUP BY requirements"""
        warnings = []
        sql_upper = str(statement).upper()
        
        # Check for aggregation without GROUP BY when selecting multiple columns
        agg_functions = ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX']
        has_aggregation = any(f'{func}(' in sql_upper for func in agg_functions)
        has_group_by = 'GROUP BY' in sql_upper
        
        if has_aggregation and not has_group_by:
            # Check if SELECT has multiple columns
            select_match = re.search(r'SELECT\s+(.*?)\s+FROM', sql_upper, re.IGNORECASE)
            if select_match:
                select_clause = select_match.group(1)
                # Count columns (simplified)
                if ',' in select_clause:
                    warnings.append(SemanticError(
                        error_type=SemanticErrorType.MISSING_GROUP_BY,
                        message="Aggregation with multiple columns may require GROUP BY",
                        element="GROUP BY",
                        suggestion="Add GROUP BY clause for non-aggregated columns",
                        severity="WARNING"
                    ))
        
        return warnings
    
    def _verify_type_compatibility(self, statement: Statement, valid_tables: List[str]) -> List[SemanticError]:
        """Verify data type compatibility in comparisons"""
        warnings = []
        
        # This would require detailed type information from schema
        # Simplified implementation
        
        sql = str(statement)
        
        # Check for common type mismatches
        # e.g., comparing string to number without quotes
        
        # Check for numeric comparisons with quoted values
        numeric_comparison = re.finditer(r"(\w+)\s*([<>=!]+)\s*'(\d+)'", sql)
        for match in numeric_comparison:
            column = match.group(1)
            value = match.group(3)
            warnings.append(SemanticError(
                error_type=SemanticErrorType.TYPE_MISMATCH,
                message=f"Potential type mismatch: comparing {column} with quoted number '{value}'",
                element=column,
                suggestion=f"Use unquoted number: {value}",
                severity="WARNING"
            ))
        
        return warnings
    
    def _find_similar_name(self, name: str, candidates: Set[str]) -> Optional[str]:
        """Find similar name using simple string similarity"""
        if not candidates:
            return None
        
        name_lower = name.lower()
        
        # Exact case-insensitive match
        for candidate in candidates:
            if candidate.lower() == name_lower:
                return candidate
        
        # Partial match
        for candidate in candidates:
            if name_lower in candidate.lower() or candidate.lower() in name_lower:
                return candidate
        
        # Levenshtein distance (simplified - just check first few characters)
        for candidate in candidates:
            if len(name) >= 3 and len(candidate) >= 3:
                if name_lower[:3] == candidate.lower()[:3]:
                    return candidate
        
        return None


# Example usage
if __name__ == "__main__":
    # Sample schema
    schema = {
        "tables": {
            "employees": {
                "columns": {
                    "id": {"type": "INTEGER"},
                    "name": {"type": "VARCHAR"},
                    "salary": {"type": "INTEGER"},
                    "dept_id": {"type": "INTEGER"}
                }
            },
            "departments": {
                "columns": {
                    "id": {"type": "INTEGER"},
                    "name": {"type": "VARCHAR"},
                    "budget": {"type": "INTEGER"}
                }
            }
        }
    }
    
    verifier = SemanticVerifier(schema)
    
    # Test cases
    test_queries = [
        "SELECT name, salary FROM employees WHERE salary > 50000",
        "SELECT name FROM employee WHERE salary > 50000",  # Wrong table name
        "SELECT nam FROM employees",  # Wrong column name
        "SELECT e.name, d.name FROM employees e JOIN departments d ON e.dept_id = d.id",
        "SELECT name FROM employees JOIN unknown_table ON employees.id = unknown_table.emp_id",  # Unknown table
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}: {query}")
        print('='*60)
        
        result = verifier.verify(query)
        
        print(f"Valid: {result.is_valid}")
        print(f"Validated tables: {result.validated_tables}")
        print(f"Validated columns: {result.validated_columns}")
        
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
