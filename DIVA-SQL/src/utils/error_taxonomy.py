"""
Error Taxonomy for DIVA-SQL

This module contains classifications and patterns of common SQL errors
based on research literature and empirical analysis.
"""

from typing import List, Dict, Any, Set
from dataclasses import dataclass
from enum import Enum


class ErrorCategory(Enum):
    """Categories of SQL errors"""
    SCHEMA_MISMATCH = "schema_mismatch"
    LOGIC_ERROR = "logic_error"
    SYNTAX_ERROR = "syntax_error"
    TYPE_MISMATCH = "type_mismatch"
    JOIN_ERROR = "join_error"
    AGGREGATION_ERROR = "aggregation_error"
    CONSTRAINT_VIOLATION = "constraint_violation"
    PERFORMANCE_ISSUE = "performance_issue"


@dataclass
class ErrorPattern:
    """Represents a specific error pattern"""
    id: str
    name: str
    category: ErrorCategory
    description: str
    regex_pattern: str
    severity: str  # HIGH, MEDIUM, LOW
    common_fix: str
    examples: List[str]


class ErrorTaxonomy:
    """
    Comprehensive taxonomy of Text-to-SQL errors based on research literature
    including NL2SQL-BUGs, BIRD benchmark analysis, and common patterns
    """
    
    def __init__(self):
        self.error_patterns = self._initialize_error_patterns()
        self.error_categories = {category.value: [] for category in ErrorCategory}
        self._categorize_patterns()
    
    def _initialize_error_patterns(self) -> List[ErrorPattern]:
        """Initialize the comprehensive set of error patterns"""
        patterns = []
        
        # Schema Mismatch Errors
        patterns.extend([
            ErrorPattern(
                id="table_not_found",
                name="Table Not Found",
                category=ErrorCategory.SCHEMA_MISMATCH,
                description="Referenced table does not exist in database schema",
                regex_pattern=r"FROM\s+(\w+)|JOIN\s+(\w+)",
                severity="HIGH",
                common_fix="Check table name spelling and availability",
                examples=["FROM Employes", "JOIN Departmnt"]
            ),
            ErrorPattern(
                id="column_not_found",
                name="Column Not Found",
                category=ErrorCategory.SCHEMA_MISMATCH,
                description="Referenced column does not exist in the specified table",
                regex_pattern=r"(\w+)\.(\w+)",
                severity="HIGH",
                common_fix="Verify column name and table association",
                examples=["T1.Nmae", "Employee.DeptName"]
            ),
            ErrorPattern(
                id="ambiguous_column",
                name="Ambiguous Column Reference",
                category=ErrorCategory.SCHEMA_MISMATCH,
                description="Column exists in multiple tables but not qualified",
                regex_pattern=r"\b(?!T\d+\.)(\w+)\s*[=<>]",
                severity="MEDIUM",
                common_fix="Use table aliases to qualify column references",
                examples=["WHERE ID = 1", "SELECT Name FROM Employee, Department"]
            )
        ])
        
        # Type Mismatch Errors
        patterns.extend([
            ErrorPattern(
                id="id_string_comparison",
                name="ID Column String Comparison",
                category=ErrorCategory.TYPE_MISMATCH,
                description="Comparing numeric ID column with string literal",
                regex_pattern=r"\b\w*[Ii][Dd]\s*=\s*'[^']*'",
                severity="HIGH",
                common_fix="Remove quotes for numeric ID comparisons",
                examples=["WHERE EmpID = '123'", "T1.DeptID = 'Sales'"]
            ),
            ErrorPattern(
                id="date_format_error",
                name="Incorrect Date Format",
                category=ErrorCategory.TYPE_MISMATCH,
                description="Using incorrect date format in comparisons",
                regex_pattern=r"date\s*[><=]\s*('\d{4}'|\d{4})",
                severity="MEDIUM",
                common_fix="Use proper date format 'YYYY-MM-DD'",
                examples=["HireDate > '2022'", "BirthDate = 1990"]
            ),
            ErrorPattern(
                id="string_numeric_mismatch",
                name="String-Numeric Type Mismatch",
                category=ErrorCategory.TYPE_MISMATCH,
                description="Comparing string column with numeric value or vice versa",
                regex_pattern=r"(name|title|description)\s*[><=]\s*\d+",
                severity="MEDIUM",
                common_fix="Ensure data types match in comparisons",
                examples=["Name > 100", "Description = 42"]
            )
        ])
        
        # Join Errors
        patterns.extend([
            ErrorPattern(
                id="missing_join_condition",
                name="Missing JOIN Condition",
                category=ErrorCategory.JOIN_ERROR,
                description="JOIN clause without ON condition",
                regex_pattern=r"JOIN\s+\w+(?!\s+ON|\s+AS\s+\w+\s+ON)",
                severity="HIGH",
                common_fix="Add ON condition to specify join relationship",
                examples=["JOIN Department", "LEFT JOIN Employee"]
            ),
            ErrorPattern(
                id="cartesian_product",
                name="Unintended Cartesian Product",
                category=ErrorCategory.JOIN_ERROR,
                description="Multiple tables in FROM without proper joins",
                regex_pattern=r"FROM\s+\w+\s*,\s*\w+",
                severity="HIGH",
                common_fix="Use explicit JOIN syntax with ON conditions",
                examples=["FROM Employee, Department", "FROM T1, T2, T3"]
            ),
            ErrorPattern(
                id="wrong_join_condition",
                name="Incorrect JOIN Condition",
                category=ErrorCategory.JOIN_ERROR,
                description="JOIN condition uses wrong columns or comparison",
                regex_pattern=r"ON\s+\w+\.\w+\s*=\s*\w+\.\w+",
                severity="MEDIUM",
                common_fix="Verify foreign key relationships in schema",
                examples=["ON T1.Name = T2.Name", "ON Employee.ID = Department.ID"]
            )
        ])
        
        # Aggregation Errors
        patterns.extend([
            ErrorPattern(
                id="missing_group_by",
                name="Missing GROUP BY",
                category=ErrorCategory.AGGREGATION_ERROR,
                description="Aggregate function with non-aggregate columns but no GROUP BY",
                regex_pattern=r"SELECT.*\b(COUNT|SUM|AVG|MAX|MIN)\s*\([^)]*\).*,.*\w+(?!\s*\()",
                severity="HIGH",
                common_fix="Add GROUP BY clause or remove non-aggregate columns",
                examples=["SELECT Name, COUNT(*) FROM Employee", "SELECT DeptID, SUM(Salary), Name FROM Employee"]
            ),
            ErrorPattern(
                id="invalid_having_without_group",
                name="HAVING Without GROUP BY",
                category=ErrorCategory.AGGREGATION_ERROR,
                description="HAVING clause used without GROUP BY",
                regex_pattern=r"HAVING\s+.*(?<!GROUP\s+BY)",
                severity="HIGH",
                common_fix="Add GROUP BY clause before HAVING",
                examples=["SELECT * FROM Employee HAVING COUNT(*) > 5"]
            ),
            ErrorPattern(
                id="aggregate_in_where",
                name="Aggregate Function in WHERE",
                category=ErrorCategory.AGGREGATION_ERROR,
                description="Aggregate function used in WHERE clause instead of HAVING",
                regex_pattern=r"WHERE.*\b(COUNT|SUM|AVG|MAX|MIN)\s*\(",
                severity="MEDIUM",
                common_fix="Move aggregate condition to HAVING clause",
                examples=["WHERE COUNT(*) > 5", "WHERE SUM(Salary) > 100000"]
            )
        ])
        
        # Logic Errors
        patterns.extend([
            ErrorPattern(
                id="always_true_condition",
                name="Always True Condition",
                category=ErrorCategory.LOGIC_ERROR,
                description="Condition that is always true, making filter ineffective",
                regex_pattern=r"(\w+\s*=\s*\w+\s+OR\s+\w+\s*!=\s*\w+|\w+\s*>\s*0\s+OR\s+\w+\s*<=\s*0)",
                severity="MEDIUM",
                common_fix="Review logic and fix condition",
                examples=["WHERE Age > 0 OR Age <= 0", "WHERE Status = 'Active' OR Status != 'Active'"]
            ),
            ErrorPattern(
                id="contradictory_conditions",
                name="Contradictory Conditions",
                category=ErrorCategory.LOGIC_ERROR,
                description="AND conditions that cannot be simultaneously true",
                regex_pattern=r"(\w+\s*>\s*\d+\s+AND\s+\w+\s*<\s*\d+)",
                severity="HIGH",
                common_fix="Review and correct logical conditions",
                examples=["WHERE Age > 50 AND Age < 30", "WHERE Salary > 100000 AND Salary < 50000"]
            ),
            ErrorPattern(
                id="null_comparison_error",
                name="Incorrect NULL Comparison",
                category=ErrorCategory.LOGIC_ERROR,
                description="Using = or != with NULL instead of IS NULL/IS NOT NULL",
                regex_pattern=r"\w+\s*[!=]=\s*NULL",
                severity="MEDIUM",
                common_fix="Use IS NULL or IS NOT NULL for NULL comparisons",
                examples=["WHERE Name = NULL", "WHERE Description != NULL"]
            )
        ])
        
        # Performance Issues
        patterns.extend([
            ErrorPattern(
                id="select_star_large_table",
                name="SELECT * on Large Table",
                category=ErrorCategory.PERFORMANCE_ISSUE,
                description="Using SELECT * which may retrieve unnecessary data",
                regex_pattern=r"SELECT\s+\*\s+FROM",
                severity="LOW",
                common_fix="Specify only needed columns in SELECT",
                examples=["SELECT * FROM LargeTable"]
            ),
            ErrorPattern(
                id="no_limit_on_large_result",
                name="No LIMIT on Potentially Large Result",
                category=ErrorCategory.PERFORMANCE_ISSUE,
                description="Query may return many rows without LIMIT",
                regex_pattern=r"SELECT.*FROM.*(?!.*LIMIT)",
                severity="LOW",
                common_fix="Consider adding LIMIT clause for large datasets",
                examples=["SELECT Name FROM Employee WHERE Status = 'Active'"]
            )
        ])
        
        # Constraint Violations
        patterns.extend([
            ErrorPattern(
                id="division_by_zero",
                name="Potential Division by Zero",
                category=ErrorCategory.CONSTRAINT_VIOLATION,
                description="Division operation without zero check",
                regex_pattern=r"\w+\s*/\s*\w+",
                severity="MEDIUM",
                common_fix="Add NULL or zero check before division",
                examples=["SELECT Salary/Hours FROM Employee", "WHERE Total/Count > 100"]
            )
        ])
        
        return patterns
    
    def _categorize_patterns(self):
        """Organize patterns by category"""
        for pattern in self.error_patterns:
            self.error_categories[pattern.category.value].append(pattern)
    
    def get_common_patterns(self) -> List[str]:
        """Get list of common error pattern names for LLM prompts"""
        return [pattern.name for pattern in self.error_patterns if pattern.severity in ["HIGH", "MEDIUM"]]
    
    def get_patterns_by_category(self, category: ErrorCategory) -> List[ErrorPattern]:
        """Get all patterns for a specific category"""
        return self.error_categories[category.value]
    
    def get_high_severity_patterns(self) -> List[ErrorPattern]:
        """Get all high-severity error patterns"""
        return [p for p in self.error_patterns if p.severity == "HIGH"]
    
    def check_pattern_match(self, sql_clause: str, pattern_id: str) -> bool:
        """Check if SQL clause matches a specific error pattern"""
        pattern = next((p for p in self.error_patterns if p.id == pattern_id), None)
        if not pattern:
            return False
        
        import re
        return bool(re.search(pattern.regex_pattern, sql_clause, re.IGNORECASE))
    
    def find_matching_patterns(self, sql_clause: str) -> List[ErrorPattern]:
        """Find all error patterns that match the given SQL clause"""
        import re
        matching_patterns = []
        
        for pattern in self.error_patterns:
            if re.search(pattern.regex_pattern, sql_clause, re.IGNORECASE):
                matching_patterns.append(pattern)
        
        return matching_patterns
    
    def get_pattern_fixes(self, pattern_ids: List[str]) -> Dict[str, str]:
        """Get common fixes for a list of pattern IDs"""
        fixes = {}
        for pattern_id in pattern_ids:
            pattern = next((p for p in self.error_patterns if p.id == pattern_id), None)
            if pattern:
                fixes[pattern_id] = pattern.common_fix
        return fixes
    
    def get_taxonomy_summary(self) -> Dict[str, Any]:
        """Get summary statistics of the error taxonomy"""
        summary = {
            "total_patterns": len(self.error_patterns),
            "categories": {
                category.value: len(patterns) 
                for category, patterns in self.error_categories.items()
            },
            "severity_distribution": {
                "HIGH": len([p for p in self.error_patterns if p.severity == "HIGH"]),
                "MEDIUM": len([p for p in self.error_patterns if p.severity == "MEDIUM"]),
                "LOW": len([p for p in self.error_patterns if p.severity == "LOW"])
            },
            "most_common_categories": sorted(
                self.error_categories.items(), 
                key=lambda x: len(x[1]), 
                reverse=True
            )[:3]
        }
        return summary
    
    def export_patterns_for_training(self) -> List[Dict[str, Any]]:
        """Export patterns in format suitable for training ML models"""
        training_data = []
        
        for pattern in self.error_patterns:
            training_data.append({
                "pattern_id": pattern.id,
                "name": pattern.name,
                "category": pattern.category.value,
                "description": pattern.description,
                "regex": pattern.regex_pattern,
                "severity": pattern.severity,
                "fix": pattern.common_fix,
                "positive_examples": pattern.examples,
                "features": {
                    "has_join": "JOIN" in pattern.regex_pattern.upper(),
                    "has_aggregation": any(agg in pattern.regex_pattern.upper() 
                                         for agg in ["COUNT", "SUM", "AVG", "MAX", "MIN"]),
                    "has_comparison": any(op in pattern.regex_pattern 
                                        for op in ["=", "<", ">", "!=", "<=", ">="]),
                    "involves_id": "ID" in pattern.regex_pattern.upper(),
                    "involves_date": "date" in pattern.regex_pattern.lower()
                }
            })
        
        return training_data


# Utility functions for error analysis
def analyze_sql_errors(sql_clause: str, taxonomy: ErrorTaxonomy) -> Dict[str, Any]:
    """
    Comprehensive error analysis of a SQL clause
    """
    matching_patterns = taxonomy.find_matching_patterns(sql_clause)
    
    analysis = {
        "sql_clause": sql_clause,
        "total_issues": len(matching_patterns),
        "severity_breakdown": {
            "HIGH": len([p for p in matching_patterns if p.severity == "HIGH"]),
            "MEDIUM": len([p for p in matching_patterns if p.severity == "MEDIUM"]),
            "LOW": len([p for p in matching_patterns if p.severity == "LOW"])
        },
        "categories_affected": list(set(p.category.value for p in matching_patterns)),
        "patterns_matched": [
            {
                "id": p.id,
                "name": p.name,
                "category": p.category.value,
                "severity": p.severity,
                "description": p.description,
                "suggested_fix": p.common_fix
            }
            for p in matching_patterns
        ],
        "risk_score": calculate_risk_score(matching_patterns),
        "recommended_actions": generate_recommendations(matching_patterns)
    }
    
    return analysis


def calculate_risk_score(patterns: List[ErrorPattern]) -> float:
    """
    Calculate a risk score based on detected error patterns
    """
    if not patterns:
        return 0.0
    
    severity_weights = {"HIGH": 1.0, "MEDIUM": 0.6, "LOW": 0.3}
    total_weight = sum(severity_weights[p.severity] for p in patterns)
    
    # Normalize to 0-1 scale
    max_possible_weight = len(patterns) * 1.0  # All HIGH severity
    risk_score = min(total_weight / max_possible_weight, 1.0)
    
    return round(risk_score, 2)


def generate_recommendations(patterns: List[ErrorPattern]) -> List[str]:
    """
    Generate prioritized recommendations based on error patterns
    """
    if not patterns:
        return ["No issues detected. SQL clause appears correct."]
    
    recommendations = []
    
    # Sort by severity
    high_patterns = [p for p in patterns if p.severity == "HIGH"]
    medium_patterns = [p for p in patterns if p.severity == "MEDIUM"]
    low_patterns = [p for p in patterns if p.severity == "LOW"]
    
    if high_patterns:
        recommendations.append("🚨 CRITICAL: Address high-severity issues immediately:")
        for pattern in high_patterns:
            recommendations.append(f"   - {pattern.name}: {pattern.common_fix}")
    
    if medium_patterns:
        recommendations.append("⚠️  IMPORTANT: Review medium-severity issues:")
        for pattern in medium_patterns:
            recommendations.append(f"   - {pattern.name}: {pattern.common_fix}")
    
    if low_patterns:
        recommendations.append("💡 SUGGESTIONS: Consider these improvements:")
        for pattern in low_patterns:
            recommendations.append(f"   - {pattern.name}: {pattern.common_fix}")
    
    # Add general recommendations
    categories = set(p.category for p in patterns)
    if ErrorCategory.SCHEMA_MISMATCH in categories:
        recommendations.append("🔍 Verify all table and column names against the database schema")
    
    if ErrorCategory.JOIN_ERROR in categories:
        recommendations.append("🔗 Review table relationships and foreign key constraints")
    
    if ErrorCategory.AGGREGATION_ERROR in categories:
        recommendations.append("📊 Check GROUP BY and aggregate function usage")
    
    return recommendations


# Example usage and testing
if __name__ == "__main__":
    # Initialize taxonomy
    taxonomy = ErrorTaxonomy()
    
    # Print summary
    summary = taxonomy.get_taxonomy_summary()
    print("Error Taxonomy Summary:")
    print(f"Total patterns: {summary['total_patterns']}")
    print(f"Categories: {list(summary['categories'].keys())}")
    print(f"Severity distribution: {summary['severity_distribution']}")
    
    # Test error detection
    test_sql = "SELECT Name, COUNT(*) FROM Employee WHERE EmpID = '123'"
    
    print(f"\nAnalyzing SQL: {test_sql}")
    analysis = analyze_sql_errors(test_sql, taxonomy)
    
    print(f"Issues found: {analysis['total_issues']}")
    print(f"Risk score: {analysis['risk_score']}")
    print("Recommendations:")
    for rec in analysis['recommended_actions']:
        print(f"  {rec}")
