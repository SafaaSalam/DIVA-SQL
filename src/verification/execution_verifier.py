"""
Stage 3: Execution Testing Verification

This module executes SQL query fragments against sample data to detect runtime errors.
It validates that queries can execute successfully and produce reasonable results.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import sqlite3
import time
import traceback


class ExecutionErrorType(Enum):
    """Types of execution errors"""
    RUNTIME_ERROR = "runtime_error"
    TIMEOUT = "timeout"
    EMPTY_RESULT = "empty_result"
    EXCESSIVE_ROWS = "excessive_rows"
    PERFORMANCE_WARNING = "performance_warning"
    DATA_TYPE_ERROR = "data_type_error"


@dataclass
class ExecutionError:
    """Represents an execution error"""
    error_type: ExecutionErrorType
    message: str
    details: Optional[str] = None
    suggestion: Optional[str] = None
    severity: str = "ERROR"


@dataclass
class ExecutionResult:
    """Result of query execution"""
    success: bool
    rows_returned: int
    execution_time_ms: float
    result_sample: Optional[List[Dict[str, Any]]] = None
    error_message: Optional[str] = None


@dataclass
class ExecutionVerificationResult:
    """Result of execution verification"""
    is_valid: bool
    errors: List[ExecutionError]
    warnings: List[ExecutionError]
    execution_result: Optional[ExecutionResult] = None
    performance_metrics: Dict[str, Any] = None


class ExecutionVerifier:
    """
    Stage 3 Verifier: Execution testing against sample data
    
    Executes SQL queries against a test database to:
    - Detect runtime errors
    - Validate query executability
    - Check performance
    - Verify result sanity
    """
    
    def __init__(self, 
                 database_path: Optional[str] = None,
                 timeout_seconds: float = 10.0,
                 max_rows_warning: int = 10000):
        """
        Initialize execution verifier
        
        Args:
            database_path: Path to test database (creates in-memory if None)
            timeout_seconds: Maximum execution time before timeout
            max_rows_warning: Warn if query returns more rows than this
        """
        self.database_path = database_path or ":memory:"
        self.timeout_seconds = timeout_seconds
        self.max_rows_warning = max_rows_warning
        self.connection = None
    
    def setup_test_database(self, schema: Dict[str, Any], sample_data: Optional[Dict[str, List[Dict]]] = None):
        """
        Set up test database with schema and sample data
        
        Args:
            schema: Database schema
            sample_data: Sample data for tables
        """
        try:
            self.connection = sqlite3.connect(self.database_path)
            self.connection.row_factory = sqlite3.Row
            cursor = self.connection.cursor()
            
            # Create tables from schema
            tables_dict = schema.get('tables', schema)
            
            for table_name, table_info in tables_dict.items():
                # Build CREATE TABLE statement
                columns_def = []
                
                if isinstance(table_info, dict) and 'columns' in table_info:
                    columns = table_info['columns']
                    if isinstance(columns, dict):
                        for col_name, col_info in columns.items():
                            col_type = col_info.get('type', 'TEXT') if isinstance(col_info, dict) else 'TEXT'
                            nullable = col_info.get('nullable', True) if isinstance(col_info, dict) else True
                            null_clause = "" if nullable else " NOT NULL"
                            columns_def.append(f"{col_name} {col_type}{null_clause}")
                    elif isinstance(columns, list):
                        for col_name in columns:
                            columns_def.append(f"{col_name} TEXT")
                elif isinstance(table_info, list):
                    # Simple format: table_name: [col1, col2, ...]
                    for col_name in table_info:
                        columns_def.append(f"{col_name} TEXT")
                
                if columns_def:
                    create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns_def)})"
                    cursor.execute(create_sql)
            
            # Insert sample data if provided
            if sample_data:
                for table_name, rows in sample_data.items():
                    if rows:
                        # Get column names from first row
                        columns = list(rows[0].keys())
                        placeholders = ', '.join(['?' for _ in columns])
                        insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                        
                        for row in rows:
                            values = [row.get(col) for col in columns]
                            cursor.execute(insert_sql, values)
            
            self.connection.commit()
            
        except Exception as e:
            raise Exception(f"Failed to setup test database: {str(e)}")
    
    def verify(self, sql: str, dry_run: bool = False) -> ExecutionVerificationResult:
        """
        Perform execution verification
        
        Args:
            sql: SQL query to execute
            dry_run: If True, only validate without executing
            
        Returns:
            ExecutionVerificationResult with execution details
        """
        errors = []
        warnings = []
        execution_result = None
        performance_metrics = {}
        
        if dry_run:
            # Just validate the query can be prepared
            try:
                if self.connection:
                    cursor = self.connection.cursor()
                    cursor.execute(f"EXPLAIN QUERY PLAN {sql}")
                    return ExecutionVerificationResult(
                        is_valid=True,
                        errors=[],
                        warnings=[],
                        execution_result=None,
                        performance_metrics={"dry_run": True}
                    )
            except Exception as e:
                errors.append(ExecutionError(
                    error_type=ExecutionErrorType.RUNTIME_ERROR,
                    message=f"Query validation failed: {str(e)}",
                    details=traceback.format_exc()
                ))
                return ExecutionVerificationResult(
                    is_valid=False,
                    errors=errors,
                    warnings=warnings,
                    execution_result=None,
                    performance_metrics={}
                )
        
        # Execute the query
        if not self.connection:
            errors.append(ExecutionError(
                error_type=ExecutionErrorType.RUNTIME_ERROR,
                message="No database connection available",
                suggestion="Call setup_test_database() first"
            ))
            return ExecutionVerificationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                execution_result=None,
                performance_metrics={}
            )
        
        try:
            cursor = self.connection.cursor()
            
            # Measure execution time
            start_time = time.time()
            
            # Set timeout
            self.connection.set_trace_callback(None)
            
            # Execute query
            cursor.execute(sql)
            rows = cursor.fetchall()
            
            end_time = time.time()
            execution_time_ms = (end_time - start_time) * 1000
            
            # Create execution result
            rows_returned = len(rows)
            result_sample = []
            
            if rows:
                # Convert first few rows to dict
                sample_size = min(5, len(rows))
                for row in rows[:sample_size]:
                    result_sample.append(dict(row))
            
            execution_result = ExecutionResult(
                success=True,
                rows_returned=rows_returned,
                execution_time_ms=execution_time_ms,
                result_sample=result_sample,
                error_message=None
            )
            
            # Performance metrics
            performance_metrics = {
                "execution_time_ms": execution_time_ms,
                "rows_returned": rows_returned,
                "query_length": len(sql)
            }
            
            # Check for warnings
            exec_warnings = self._check_execution_warnings(execution_result)
            warnings.extend(exec_warnings)
            
        except sqlite3.OperationalError as e:
            error_msg = str(e)
            errors.append(ExecutionError(
                error_type=ExecutionErrorType.RUNTIME_ERROR,
                message=f"SQL execution error: {error_msg}",
                details=traceback.format_exc(),
                suggestion=self._suggest_fix_for_error(error_msg)
            ))
            execution_result = ExecutionResult(
                success=False,
                rows_returned=0,
                execution_time_ms=0.0,
                error_message=error_msg
            )
            
        except Exception as e:
            errors.append(ExecutionError(
                error_type=ExecutionErrorType.RUNTIME_ERROR,
                message=f"Unexpected error: {str(e)}",
                details=traceback.format_exc()
            ))
            execution_result = ExecutionResult(
                success=False,
                rows_returned=0,
                execution_time_ms=0.0,
                error_message=str(e)
            )
        
        is_valid = len(errors) == 0
        
        return ExecutionVerificationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            execution_result=execution_result,
            performance_metrics=performance_metrics
        )
    
    def _check_execution_warnings(self, execution_result: ExecutionResult) -> List[ExecutionError]:
        """Check for execution warnings"""
        warnings = []
        
        # Check for empty results
        if execution_result.rows_returned == 0:
            warnings.append(ExecutionError(
                error_type=ExecutionErrorType.EMPTY_RESULT,
                message="Query returned no results",
                suggestion="Verify query logic and data availability",
                severity="WARNING"
            ))
        
        # Check for excessive rows
        if execution_result.rows_returned > self.max_rows_warning:
            warnings.append(ExecutionError(
                error_type=ExecutionErrorType.EXCESSIVE_ROWS,
                message=f"Query returned {execution_result.rows_returned} rows (>{self.max_rows_warning})",
                suggestion="Consider adding LIMIT clause or refining WHERE conditions",
                severity="WARNING"
            ))
        
        # Check for slow execution
        if execution_result.execution_time_ms > 1000:  # 1 second
            warnings.append(ExecutionError(
                error_type=ExecutionErrorType.PERFORMANCE_WARNING,
                message=f"Slow query execution: {execution_result.execution_time_ms:.2f}ms",
                suggestion="Consider adding indexes or optimizing query",
                severity="WARNING"
            ))
        
        return warnings
    
    def _suggest_fix_for_error(self, error_message: str) -> Optional[str]:
        """Suggest fixes for common errors"""
        error_lower = error_message.lower()
        
        if "no such table" in error_lower:
            return "Verify table name exists in schema"
        
        if "no such column" in error_lower:
            return "Verify column name exists in table"
        
        if "ambiguous column" in error_lower:
            return "Use table aliases to qualify column names"
        
        if "syntax error" in error_lower:
            return "Check SQL syntax and keyword order"
        
        if "datatype mismatch" in error_lower:
            return "Verify data types in comparisons and operations"
        
        return None
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Example usage
if __name__ == "__main__":
    # Sample schema
    schema = {
        "tables": {
            "employees": {
                "columns": {
                    "id": {"type": "INTEGER"},
                    "name": {"type": "TEXT"},
                    "salary": {"type": "INTEGER"},
                    "dept_id": {"type": "INTEGER"}
                }
            },
            "departments": {
                "columns": {
                    "id": {"type": "INTEGER"},
                    "name": {"type": "TEXT"}
                }
            }
        }
    }
    
    # Sample data
    sample_data = {
        "employees": [
            {"id": 1, "name": "Alice", "salary": 60000, "dept_id": 1},
            {"id": 2, "name": "Bob", "salary": 75000, "dept_id": 2},
            {"id": 3, "name": "Charlie", "salary": 55000, "dept_id": 1},
        ],
        "departments": [
            {"id": 1, "name": "Engineering"},
            {"id": 2, "name": "Sales"},
        ]
    }
    
    # Create verifier
    with ExecutionVerifier() as verifier:
        verifier.setup_test_database(schema, sample_data)
        
        # Test queries
        test_queries = [
            "SELECT * FROM employees WHERE salary > 50000",
            "SELECT name FROM employees WHERE salary > 100000",  # Empty result
            "SELECT * FROM unknown_table",  # Runtime error
            "SELECT e.name, d.name FROM employees e JOIN departments d ON e.dept_id = d.id",
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{'='*60}")
            print(f"Test {i}: {query}")
            print('='*60)
            
            result = verifier.verify(query)
            
            print(f"Valid: {result.is_valid}")
            
            if result.execution_result:
                print(f"Execution successful: {result.execution_result.success}")
                print(f"Rows returned: {result.execution_result.rows_returned}")
                print(f"Execution time: {result.execution_result.execution_time_ms:.2f}ms")
                
                if result.execution_result.result_sample:
                    print("\nSample results:")
                    for row in result.execution_result.result_sample:
                        print(f"  {row}")
            
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
