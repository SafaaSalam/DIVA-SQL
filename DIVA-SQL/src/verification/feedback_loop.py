"""
Feedback Loop for DIVA-SQL Three-Stage Verification

This module implements the diagnostic error reporting and localized repair mechanism.
It coordinates all three verification stages and provides actionable feedback for corrections.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from .syntax_verifier import SyntaxVerifier, SyntaxVerificationResult
from .semantic_verifier import SemanticVerifier, SemanticVerificationResult
from .execution_verifier import ExecutionVerifier, ExecutionVerificationResult


class VerificationStage(Enum):
    """Verification stages"""
    SYNTAX = "syntax"
    SEMANTIC = "semantic"
    EXECUTION = "execution"


class FeedbackSeverity(Enum):
    """Feedback severity levels"""
    CRITICAL = "critical"  # Must fix
    ERROR = "error"        # Should fix
    WARNING = "warning"    # Consider fixing
    INFO = "info"          # Informational


@dataclass
class VerificationFeedback:
    """
    Comprehensive feedback from all verification stages
    
    Attributes:
        stage: Which stage produced this feedback
        severity: Severity level
        message: Human-readable message
        element: The problematic element (SQL fragment, table, column, etc.)
        suggestion: Suggested fix
        auto_fixable: Whether this can be automatically fixed
        fix_action: Specific action to fix (if auto_fixable)
    """
    stage: VerificationStage
    severity: FeedbackSeverity
    message: str
    element: str
    suggestion: Optional[str] = None
    auto_fixable: bool = False
    fix_action: Optional[Dict[str, Any]] = None


@dataclass
class ThreeStageVerificationResult:
    """
    Complete result from all three verification stages
    
    Attributes:
        overall_valid: Whether SQL passed all stages
        stage_results: Results from each stage
        feedback: Consolidated feedback from all stages
        corrected_sql: Auto-corrected SQL (if applicable)
        performance_metrics: Performance data
    """
    overall_valid: bool
    stage_results: Dict[str, Any]
    feedback: List[VerificationFeedback]
    corrected_sql: Optional[str] = None
    performance_metrics: Dict[str, Any] = None


class FeedbackLoop:
    """
    Three-Stage Verification with Feedback Loop
    
    Implements the complete verification pipeline:
    1. Stage 1: Syntax Verification
    2. Stage 2: Semantic Alignment
    3. Stage 3: Execution Testing
    
    Provides diagnostic feedback and localized repair suggestions.
    """
    
    def __init__(self,
                 database_schema: Dict[str, Any],
                 test_database_path: Optional[str] = None,
                 enable_auto_fix: bool = True):
        """
        Initialize feedback loop
        
        Args:
            database_schema: Database schema for semantic verification
            test_database_path: Path to test database for execution
            enable_auto_fix: Enable automatic fixing of simple errors
        """
        self.syntax_verifier = SyntaxVerifier()
        self.semantic_verifier = SemanticVerifier(database_schema)
        self.execution_verifier = ExecutionVerifier(test_database_path)
        self.enable_auto_fix = enable_auto_fix
        self.database_schema = database_schema
    
    def verify_sql(self,
                   sql: str,
                   semantic_node: Optional[Any] = None,
                   sample_data: Optional[Dict[str, List[Dict]]] = None,
                   max_repair_attempts: int = 3) -> ThreeStageVerificationResult:
        """
        Perform three-stage verification with feedback loop
        
        Args:
            sql: SQL query to verify
            semantic_node: Optional semantic node for context
            sample_data: Sample data for execution testing
            max_repair_attempts: Maximum number of auto-repair attempts
            
        Returns:
            ThreeStageVerificationResult with complete verification details
        """
        current_sql = sql
        attempt = 0
        all_feedback = []
        stage_results = {}
        performance_metrics = {
            "total_verification_time_ms": 0.0,
            "repair_attempts": 0
        }
        
        while attempt < max_repair_attempts:
            attempt += 1
            performance_metrics["repair_attempts"] = attempt
            
            # Stage 1: Syntax Verification
            syntax_result = self.syntax_verifier.verify(current_sql)
            stage_results["syntax"] = syntax_result
            
            if not syntax_result.is_valid:
                feedback = self._process_syntax_feedback(syntax_result)
                all_feedback.extend(feedback)
                
                # Try to auto-fix syntax errors
                if self.enable_auto_fix and attempt < max_repair_attempts:
                    fixed_sql = self._attempt_syntax_fix(current_sql, syntax_result)
                    if fixed_sql and fixed_sql != current_sql:
                        current_sql = fixed_sql
                        continue  # Retry with fixed SQL
                
                # Cannot proceed to next stage
                return ThreeStageVerificationResult(
                    overall_valid=False,
                    stage_results=stage_results,
                    feedback=all_feedback,
                    corrected_sql=current_sql if current_sql != sql else None,
                    performance_metrics=performance_metrics
                )
            
            # Use formatted SQL from syntax verification
            if syntax_result.formatted_sql:
                current_sql = syntax_result.formatted_sql
            
            # Stage 2: Semantic Verification
            semantic_result = self.semantic_verifier.verify(current_sql, semantic_node)
            stage_results["semantic"] = semantic_result
            
            if not semantic_result.is_valid:
                feedback = self._process_semantic_feedback(semantic_result)
                all_feedback.extend(feedback)
                
                # Try to auto-fix semantic errors
                if self.enable_auto_fix and attempt < max_repair_attempts:
                    fixed_sql = self._attempt_semantic_fix(current_sql, semantic_result)
                    if fixed_sql and fixed_sql != current_sql:
                        current_sql = fixed_sql
                        continue  # Retry with fixed SQL
                
                # Cannot proceed to next stage
                return ThreeStageVerificationResult(
                    overall_valid=False,
                    stage_results=stage_results,
                    feedback=all_feedback,
                    corrected_sql=current_sql if current_sql != sql else None,
                    performance_metrics=performance_metrics
                )
            
            # Stage 3: Execution Verification
            if sample_data:
                self.execution_verifier.setup_test_database(self.database_schema, sample_data)
            
            execution_result = self.execution_verifier.verify(current_sql)
            stage_results["execution"] = execution_result
            
            if execution_result.performance_metrics:
                performance_metrics.update(execution_result.performance_metrics)
            
            if not execution_result.is_valid:
                feedback = self._process_execution_feedback(execution_result)
                all_feedback.extend(feedback)
                
                # Try to auto-fix execution errors
                if self.enable_auto_fix and attempt < max_repair_attempts:
                    fixed_sql = self._attempt_execution_fix(current_sql, execution_result)
                    if fixed_sql and fixed_sql != current_sql:
                        current_sql = fixed_sql
                        continue  # Retry with fixed SQL
                
                # Execution failed
                return ThreeStageVerificationResult(
                    overall_valid=False,
                    stage_results=stage_results,
                    feedback=all_feedback,
                    corrected_sql=current_sql if current_sql != sql else None,
                    performance_metrics=performance_metrics
                )
            
            # All stages passed!
            # Add any warnings as feedback
            feedback = []
            if syntax_result.warnings:
                feedback.extend(self._process_syntax_feedback(syntax_result, warnings_only=True))
            if semantic_result.warnings:
                feedback.extend(self._process_semantic_feedback(semantic_result, warnings_only=True))
            if execution_result.warnings:
                feedback.extend(self._process_execution_feedback(execution_result, warnings_only=True))
            
            all_feedback.extend(feedback)
            
            return ThreeStageVerificationResult(
                overall_valid=True,
                stage_results=stage_results,
                feedback=all_feedback,
                corrected_sql=current_sql if current_sql != sql else None,
                performance_metrics=performance_metrics
            )
        
        # Max attempts reached
        return ThreeStageVerificationResult(
            overall_valid=False,
            stage_results=stage_results,
            feedback=all_feedback,
            corrected_sql=current_sql if current_sql != sql else None,
            performance_metrics=performance_metrics
        )
    
    def _process_syntax_feedback(self, 
                                 result: SyntaxVerificationResult,
                                 warnings_only: bool = False) -> List[VerificationFeedback]:
        """Process syntax verification results into feedback"""
        feedback = []
        
        items = result.warnings if warnings_only else result.errors
        severity = FeedbackSeverity.WARNING if warnings_only else FeedbackSeverity.ERROR
        
        for error in items:
            feedback.append(VerificationFeedback(
                stage=VerificationStage.SYNTAX,
                severity=severity,
                message=error.message,
                element=str(error.error_type.value),
                suggestion=error.suggestion,
                auto_fixable=error.error_type.value in ['unbalanced_parentheses', 'reserved_word_misuse']
            ))
        
        return feedback
    
    def _process_semantic_feedback(self,
                                   result: SemanticVerificationResult,
                                   warnings_only: bool = False) -> List[VerificationFeedback]:
        """Process semantic verification results into feedback"""
        feedback = []
        
        items = result.warnings if warnings_only else result.errors
        severity = FeedbackSeverity.WARNING if warnings_only else FeedbackSeverity.ERROR
        
        for error in items:
            feedback.append(VerificationFeedback(
                stage=VerificationStage.SEMANTIC,
                severity=severity,
                message=error.message,
                element=error.element,
                suggestion=error.suggestion,
                auto_fixable=error.error_type.value in ['table_not_found', 'column_not_found']
            ))
        
        return feedback
    
    def _process_execution_feedback(self,
                                    result: ExecutionVerificationResult,
                                    warnings_only: bool = False) -> List[VerificationFeedback]:
        """Process execution verification results into feedback"""
        feedback = []
        
        items = result.warnings if warnings_only else result.errors
        severity = FeedbackSeverity.WARNING if warnings_only else FeedbackSeverity.CRITICAL
        
        for error in items:
            feedback.append(VerificationFeedback(
                stage=VerificationStage.EXECUTION,
                severity=severity,
                message=error.message,
                element=str(error.error_type.value),
                suggestion=error.suggestion,
                auto_fixable=False  # Execution errors typically need manual review
            ))
        
        return feedback
    
    def _attempt_syntax_fix(self, sql: str, result: SyntaxVerificationResult) -> Optional[str]:
        """Attempt to automatically fix syntax errors"""
        # Simple fixes only
        fixed_sql = sql
        
        for error in result.errors:
            if error.error_type.value == 'unbalanced_parentheses':
                # Try to balance parentheses
                open_count = fixed_sql.count('(')
                close_count = fixed_sql.count(')')
                
                if open_count > close_count:
                    fixed_sql += ')' * (open_count - close_count)
                # Note: Cannot easily fix extra closing parens
        
        return fixed_sql if fixed_sql != sql else None
    
    def _attempt_semantic_fix(self, sql: str, result: SemanticVerificationResult) -> Optional[str]:
        """Attempt to automatically fix semantic errors"""
        # Try to fix simple name mismatches
        fixed_sql = sql
        
        for error in result.errors:
            if error.suggestion and 'Did you mean' in error.suggestion:
                # Extract suggested name
                import re
                match = re.search(r"'([^']+)'", error.suggestion)
                if match:
                    suggested_name = match.group(1)
                    # Replace the incorrect name
                    fixed_sql = fixed_sql.replace(error.element, suggested_name)
        
        return fixed_sql if fixed_sql != sql else None
    
    def _attempt_execution_fix(self, sql: str, result: ExecutionVerificationResult) -> Optional[str]:
        """Attempt to automatically fix execution errors"""
        # Execution errors are typically harder to auto-fix
        # Most require understanding the intent
        return None
    
    def generate_feedback_report(self, result: ThreeStageVerificationResult) -> str:
        """Generate human-readable feedback report"""
        lines = []
        lines.append("=" * 70)
        lines.append("DIVA-SQL Three-Stage Verification Report")
        lines.append("=" * 70)
        lines.append(f"\nOverall Status: {'✓ PASSED' if result.overall_valid else '✗ FAILED'}")
        
        # Stage results
        lines.append("\n" + "-" * 70)
        lines.append("Stage Results:")
        lines.append("-" * 70)
        
        for stage_name, stage_result in result.stage_results.items():
            status = "✓" if stage_result.is_valid else "✗"
            lines.append(f"{status} Stage {stage_name.capitalize()}: {'PASSED' if stage_result.is_valid else 'FAILED'}")
        
        # Feedback
        if result.feedback:
            lines.append("\n" + "-" * 70)
            lines.append("Feedback:")
            lines.append("-" * 70)
            
            # Group by severity
            by_severity = {}
            for fb in result.feedback:
                severity = fb.severity.value
                if severity not in by_severity:
                    by_severity[severity] = []
                by_severity[severity].append(fb)
            
            for severity in ['critical', 'error', 'warning', 'info']:
                if severity in by_severity:
                    lines.append(f"\n{severity.upper()}:")
                    for fb in by_severity[severity]:
                        lines.append(f"  [{fb.stage.value}] {fb.message}")
                        if fb.suggestion:
                            lines.append(f"    → Suggestion: {fb.suggestion}")
        
        # Performance metrics
        if result.performance_metrics:
            lines.append("\n" + "-" * 70)
            lines.append("Performance Metrics:")
            lines.append("-" * 70)
            for key, value in result.performance_metrics.items():
                lines.append(f"  {key}: {value}")
        
        # Corrected SQL
        if result.corrected_sql:
            lines.append("\n" + "-" * 70)
            lines.append("Auto-Corrected SQL:")
            lines.append("-" * 70)
            lines.append(result.corrected_sql)
        
        lines.append("\n" + "=" * 70)
        
        return "\n".join(lines)


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
        ],
        "departments": [
            {"id": 1, "name": "Engineering"},
            {"id": 2, "name": "Sales"},
        ]
    }
    
    # Create feedback loop
    feedback_loop = FeedbackLoop(schema)
    
    # Test queries
    test_queries = [
        "SELECT * FROM employees WHERE salary > 50000",
        "SELECT name FROM employee WHERE salary > 50000",  # Wrong table name
        "SELECT * FROM employees WHERE (salary > 50000",  # Unbalanced parens
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*70}")
        print(f"Test {i}: {query}")
        print('='*70)
        
        result = feedback_loop.verify_sql(query, sample_data=sample_data)
        report = feedback_loop.generate_feedback_report(result)
        print(report)
