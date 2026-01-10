"""
Template Library for DIVA-SQL

This module contains 53 pre-defined SQL templates covering basic to complex operations.
Templates ensure high code quality and reduce logical errors through structured generation.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json


class TemplateCategory(Enum):
    """Categories of SQL templates"""
    BASIC_SELECT = "basic_select"
    FILTERING = "filtering"
    JOINS = "joins"
    AGGREGATION = "aggregation"
    GROUPING = "grouping"
    SUBQUERIES = "subqueries"
    CTES = "ctes"
    WINDOW_FUNCTIONS = "window_functions"


@dataclass
class SQLTemplate:
    """
    Represents a SQL template with placeholders
    
    Attributes:
        id: Unique template identifier
        name: Human-readable template name
        category: Template category
        pattern: SQL pattern with placeholders
        parameters: Required parameters for the template
        description: Template description
        complexity: Complexity level (1-5)
        examples: Example usages
    """
    id: str
    name: str
    category: TemplateCategory
    pattern: str
    parameters: List[str]
    description: str
    complexity: int
    examples: List[Dict[str, Any]]
    
    def instantiate(self, params: Dict[str, Any]) -> str:
        """
        Instantiate the template with provided parameters
        
        Args:
            params: Dictionary of parameter values
            
        Returns:
            Instantiated SQL string
        """
        sql = self.pattern
        for param_name, param_value in params.items():
            placeholder = f"{{{param_name}}}"
            if isinstance(param_value, list):
                param_value = ", ".join(str(v) for v in param_value)
            sql = sql.replace(placeholder, str(param_value))
        return sql


class TemplateLibrary:
    """
    Comprehensive library of 53 SQL templates for DIVA-SQL
    
    This library provides pre-defined templates for:
    - Basic operations (SELECT, WHERE, JOIN)
    - Complex operations (Nested queries, CTEs, Window functions)
    """
    
    def __init__(self):
        self.templates: Dict[str, SQLTemplate] = {}
        self._initialize_templates()
    
    def _initialize_templates(self):
        """Initialize all 53 templates"""
        
        # ===== BASIC SELECT TEMPLATES (10 templates) =====
        self._add_basic_select_templates()
        
        # ===== FILTERING TEMPLATES (8 templates) =====
        self._add_filtering_templates()
        
        # ===== JOIN TEMPLATES (12 templates) =====
        self._add_join_templates()
        
        # ===== AGGREGATION TEMPLATES (8 templates) =====
        self._add_aggregation_templates()
        
        # ===== GROUPING TEMPLATES (5 templates) =====
        self._add_grouping_templates()
        
        # ===== SUBQUERY TEMPLATES (6 templates) =====
        self._add_subquery_templates()
        
        # ===== CTE TEMPLATES (4 templates) =====
        self._add_cte_templates()
    
    def _add_basic_select_templates(self):
        """Add 10 basic SELECT templates"""
        
        templates = [
            SQLTemplate(
                id="BS001",
                name="Simple Select All",
                category=TemplateCategory.BASIC_SELECT,
                pattern="SELECT * FROM {table}",
                parameters=["table"],
                description="Select all columns from a single table",
                complexity=1,
                examples=[{"table": "employees", "result": "SELECT * FROM employees"}]
            ),
            SQLTemplate(
                id="BS002",
                name="Select Specific Columns",
                category=TemplateCategory.BASIC_SELECT,
                pattern="SELECT {columns} FROM {table}",
                parameters=["columns", "table"],
                description="Select specific columns from a table",
                complexity=1,
                examples=[{"columns": "name, age", "table": "employees", "result": "SELECT name, age FROM employees"}]
            ),
            SQLTemplate(
                id="BS003",
                name="Select Distinct",
                category=TemplateCategory.BASIC_SELECT,
                pattern="SELECT DISTINCT {columns} FROM {table}",
                parameters=["columns", "table"],
                description="Select distinct values",
                complexity=1,
                examples=[{"columns": "department", "table": "employees", "result": "SELECT DISTINCT department FROM employees"}]
            ),
            SQLTemplate(
                id="BS004",
                name="Select with Alias",
                category=TemplateCategory.BASIC_SELECT,
                pattern="SELECT {column} AS {alias} FROM {table}",
                parameters=["column", "alias", "table"],
                description="Select column with alias",
                complexity=1,
                examples=[{"column": "employee_name", "alias": "name", "table": "employees"}]
            ),
            SQLTemplate(
                id="BS005",
                name="Select with Multiple Aliases",
                category=TemplateCategory.BASIC_SELECT,
                pattern="SELECT {column_aliases} FROM {table}",
                parameters=["column_aliases", "table"],
                description="Select multiple columns with aliases",
                complexity=2,
                examples=[{"column_aliases": "name AS employee_name, dept AS department", "table": "employees"}]
            ),
            SQLTemplate(
                id="BS006",
                name="Select with LIMIT",
                category=TemplateCategory.BASIC_SELECT,
                pattern="SELECT {columns} FROM {table} LIMIT {limit}",
                parameters=["columns", "table", "limit"],
                description="Select with row limit",
                complexity=1,
                examples=[{"columns": "*", "table": "employees", "limit": "10"}]
            ),
            SQLTemplate(
                id="BS007",
                name="Select with OFFSET",
                category=TemplateCategory.BASIC_SELECT,
                pattern="SELECT {columns} FROM {table} LIMIT {limit} OFFSET {offset}",
                parameters=["columns", "table", "limit", "offset"],
                description="Select with pagination",
                complexity=2,
                examples=[{"columns": "*", "table": "employees", "limit": "10", "offset": "20"}]
            ),
            SQLTemplate(
                id="BS008",
                name="Select with ORDER BY",
                category=TemplateCategory.BASIC_SELECT,
                pattern="SELECT {columns} FROM {table} ORDER BY {order_columns} {direction}",
                parameters=["columns", "table", "order_columns", "direction"],
                description="Select with ordering",
                complexity=2,
                examples=[{"columns": "*", "table": "employees", "order_columns": "salary", "direction": "DESC"}]
            ),
            SQLTemplate(
                id="BS009",
                name="Select with Multiple ORDER BY",
                category=TemplateCategory.BASIC_SELECT,
                pattern="SELECT {columns} FROM {table} ORDER BY {order_spec}",
                parameters=["columns", "table", "order_spec"],
                description="Select with multiple ordering columns",
                complexity=2,
                examples=[{"columns": "*", "table": "employees", "order_spec": "department ASC, salary DESC"}]
            ),
            SQLTemplate(
                id="BS010",
                name="Select with Calculated Column",
                category=TemplateCategory.BASIC_SELECT,
                pattern="SELECT {columns}, {calculation} AS {calc_alias} FROM {table}",
                parameters=["columns", "calculation", "calc_alias", "table"],
                description="Select with calculated/derived column",
                complexity=2,
                examples=[{"columns": "name, salary", "calculation": "salary * 12", "calc_alias": "annual_salary", "table": "employees"}]
            ),
        ]
        
        for template in templates:
            self.templates[template.id] = template
    
    def _add_filtering_templates(self):
        """Add 8 filtering templates"""
        
        templates = [
            SQLTemplate(
                id="FT001",
                name="Simple WHERE Equality",
                category=TemplateCategory.FILTERING,
                pattern="SELECT {columns} FROM {table} WHERE {column} = {value}",
                parameters=["columns", "table", "column", "value"],
                description="Filter with equality condition",
                complexity=1,
                examples=[{"columns": "*", "table": "employees", "column": "department", "value": "'Sales'"}]
            ),
            SQLTemplate(
                id="FT002",
                name="WHERE with Comparison",
                category=TemplateCategory.FILTERING,
                pattern="SELECT {columns} FROM {table} WHERE {column} {operator} {value}",
                parameters=["columns", "table", "column", "operator", "value"],
                description="Filter with comparison operator",
                complexity=1,
                examples=[{"columns": "*", "table": "employees", "column": "salary", "operator": ">", "value": "50000"}]
            ),
            SQLTemplate(
                id="FT003",
                name="WHERE with AND",
                category=TemplateCategory.FILTERING,
                pattern="SELECT {columns} FROM {table} WHERE {condition1} AND {condition2}",
                parameters=["columns", "table", "condition1", "condition2"],
                description="Filter with AND logic",
                complexity=2,
                examples=[{"columns": "*", "table": "employees", "condition1": "department = 'Sales'", "condition2": "salary > 50000"}]
            ),
            SQLTemplate(
                id="FT004",
                name="WHERE with OR",
                category=TemplateCategory.FILTERING,
                pattern="SELECT {columns} FROM {table} WHERE {condition1} OR {condition2}",
                parameters=["columns", "table", "condition1", "condition2"],
                description="Filter with OR logic",
                complexity=2,
                examples=[{"columns": "*", "table": "employees", "condition1": "department = 'Sales'", "condition2": "department = 'Marketing'"}]
            ),
            SQLTemplate(
                id="FT005",
                name="WHERE with IN",
                category=TemplateCategory.FILTERING,
                pattern="SELECT {columns} FROM {table} WHERE {column} IN ({values})",
                parameters=["columns", "table", "column", "values"],
                description="Filter with IN clause",
                complexity=2,
                examples=[{"columns": "*", "table": "employees", "column": "department", "values": "'Sales', 'Marketing', 'IT'"}]
            ),
            SQLTemplate(
                id="FT006",
                name="WHERE with BETWEEN",
                category=TemplateCategory.FILTERING,
                pattern="SELECT {columns} FROM {table} WHERE {column} BETWEEN {lower} AND {upper}",
                parameters=["columns", "table", "column", "lower", "upper"],
                description="Filter with range",
                complexity=2,
                examples=[{"columns": "*", "table": "employees", "column": "salary", "lower": "40000", "upper": "80000"}]
            ),
            SQLTemplate(
                id="FT007",
                name="WHERE with LIKE",
                category=TemplateCategory.FILTERING,
                pattern="SELECT {columns} FROM {table} WHERE {column} LIKE {pattern}",
                parameters=["columns", "table", "column", "pattern"],
                description="Filter with pattern matching",
                complexity=2,
                examples=[{"columns": "*", "table": "employees", "column": "name", "pattern": "'John%'"}]
            ),
            SQLTemplate(
                id="FT008",
                name="WHERE with NULL check",
                category=TemplateCategory.FILTERING,
                pattern="SELECT {columns} FROM {table} WHERE {column} IS {null_check} NULL",
                parameters=["columns", "table", "column", "null_check"],
                description="Filter for NULL/NOT NULL values",
                complexity=1,
                examples=[{"columns": "*", "table": "employees", "column": "manager_id", "null_check": "NOT"}]
            ),
        ]
        
        for template in templates:
            self.templates[template.id] = template
    
    def _add_join_templates(self):
        """Add 12 join templates"""
        
        templates = [
            SQLTemplate(
                id="JN001",
                name="Simple INNER JOIN",
                category=TemplateCategory.JOINS,
                pattern="SELECT {columns} FROM {table1} INNER JOIN {table2} ON {table1}.{key1} = {table2}.{key2}",
                parameters=["columns", "table1", "table2", "key1", "key2"],
                description="Basic inner join between two tables",
                complexity=2,
                examples=[{"columns": "*", "table1": "employees", "table2": "departments", "key1": "dept_id", "key2": "id"}]
            ),
            SQLTemplate(
                id="JN002",
                name="LEFT JOIN",
                category=TemplateCategory.JOINS,
                pattern="SELECT {columns} FROM {table1} LEFT JOIN {table2} ON {table1}.{key1} = {table2}.{key2}",
                parameters=["columns", "table1", "table2", "key1", "key2"],
                description="Left outer join",
                complexity=2,
                examples=[{"columns": "*", "table1": "employees", "table2": "departments", "key1": "dept_id", "key2": "id"}]
            ),
            SQLTemplate(
                id="JN003",
                name="RIGHT JOIN",
                category=TemplateCategory.JOINS,
                pattern="SELECT {columns} FROM {table1} RIGHT JOIN {table2} ON {table1}.{key1} = {table2}.{key2}",
                parameters=["columns", "table1", "table2", "key1", "key2"],
                description="Right outer join",
                complexity=2,
                examples=[{"columns": "*", "table1": "employees", "table2": "departments", "key1": "dept_id", "key2": "id"}]
            ),
            SQLTemplate(
                id="JN004",
                name="FULL OUTER JOIN",
                category=TemplateCategory.JOINS,
                pattern="SELECT {columns} FROM {table1} FULL OUTER JOIN {table2} ON {table1}.{key1} = {table2}.{key2}",
                parameters=["columns", "table1", "table2", "key1", "key2"],
                description="Full outer join",
                complexity=3,
                examples=[{"columns": "*", "table1": "employees", "table2": "departments", "key1": "dept_id", "key2": "id"}]
            ),
            SQLTemplate(
                id="JN005",
                name="CROSS JOIN",
                category=TemplateCategory.JOINS,
                pattern="SELECT {columns} FROM {table1} CROSS JOIN {table2}",
                parameters=["columns", "table1", "table2"],
                description="Cartesian product of two tables",
                complexity=2,
                examples=[{"columns": "*", "table1": "colors", "table2": "sizes"}]
            ),
            SQLTemplate(
                id="JN006",
                name="Self JOIN",
                category=TemplateCategory.JOINS,
                pattern="SELECT {columns} FROM {table} {alias1} INNER JOIN {table} {alias2} ON {alias1}.{key1} = {alias2}.{key2}",
                parameters=["columns", "table", "alias1", "alias2", "key1", "key2"],
                description="Self-join on same table",
                complexity=3,
                examples=[{"columns": "e1.name, e2.name AS manager", "table": "employees", "alias1": "e1", "alias2": "e2", "key1": "manager_id", "key2": "id"}]
            ),
            SQLTemplate(
                id="JN007",
                name="Multiple INNER JOINs",
                category=TemplateCategory.JOINS,
                pattern="SELECT {columns} FROM {table1} INNER JOIN {table2} ON {join_condition1} INNER JOIN {table3} ON {join_condition2}",
                parameters=["columns", "table1", "table2", "table3", "join_condition1", "join_condition2"],
                description="Join three tables",
                complexity=3,
                examples=[{"columns": "*", "table1": "employees", "table2": "departments", "table3": "locations", "join_condition1": "employees.dept_id = departments.id", "join_condition2": "departments.location_id = locations.id"}]
            ),
            SQLTemplate(
                id="JN008",
                name="JOIN with WHERE",
                category=TemplateCategory.JOINS,
                pattern="SELECT {columns} FROM {table1} INNER JOIN {table2} ON {join_condition} WHERE {filter_condition}",
                parameters=["columns", "table1", "table2", "join_condition", "filter_condition"],
                description="Join with additional filtering",
                complexity=3,
                examples=[{"columns": "*", "table1": "employees", "table2": "departments", "join_condition": "employees.dept_id = departments.id", "filter_condition": "employees.salary > 50000"}]
            ),
            SQLTemplate(
                id="JN009",
                name="JOIN with Aggregation",
                category=TemplateCategory.JOINS,
                pattern="SELECT {columns}, {aggregation} FROM {table1} INNER JOIN {table2} ON {join_condition} GROUP BY {group_columns}",
                parameters=["columns", "aggregation", "table1", "table2", "join_condition", "group_columns"],
                description="Join with aggregation",
                complexity=4,
                examples=[{"columns": "departments.name", "aggregation": "COUNT(*) AS employee_count", "table1": "employees", "table2": "departments", "join_condition": "employees.dept_id = departments.id", "group_columns": "departments.name"}]
            ),
            SQLTemplate(
                id="JN010",
                name="LEFT JOIN with NULL check",
                category=TemplateCategory.JOINS,
                pattern="SELECT {columns} FROM {table1} LEFT JOIN {table2} ON {join_condition} WHERE {table2}.{key} IS NULL",
                parameters=["columns", "table1", "table2", "join_condition", "key"],
                description="Find unmatched records using LEFT JOIN",
                complexity=3,
                examples=[{"columns": "table1.*", "table1": "employees", "table2": "departments", "join_condition": "employees.dept_id = departments.id", "key": "id"}]
            ),
            SQLTemplate(
                id="JN011",
                name="JOIN with USING",
                category=TemplateCategory.JOINS,
                pattern="SELECT {columns} FROM {table1} INNER JOIN {table2} USING ({common_column})",
                parameters=["columns", "table1", "table2", "common_column"],
                description="Join using common column name",
                complexity=2,
                examples=[{"columns": "*", "table1": "employees", "table2": "departments", "common_column": "dept_id"}]
            ),
            SQLTemplate(
                id="JN012",
                name="Natural JOIN",
                category=TemplateCategory.JOINS,
                pattern="SELECT {columns} FROM {table1} NATURAL JOIN {table2}",
                parameters=["columns", "table1", "table2"],
                description="Natural join on all common columns",
                complexity=2,
                examples=[{"columns": "*", "table1": "employees", "table2": "departments"}]
            ),
        ]
        
        for template in templates:
            self.templates[template.id] = template
    
    def _add_aggregation_templates(self):
        """Add 8 aggregation templates"""
        
        templates = [
            SQLTemplate(
                id="AG001",
                name="COUNT All",
                category=TemplateCategory.AGGREGATION,
                pattern="SELECT COUNT(*) AS {alias} FROM {table}",
                parameters=["alias", "table"],
                description="Count all rows",
                complexity=1,
                examples=[{"alias": "total_count", "table": "employees"}]
            ),
            SQLTemplate(
                id="AG002",
                name="COUNT Distinct",
                category=TemplateCategory.AGGREGATION,
                pattern="SELECT COUNT(DISTINCT {column}) AS {alias} FROM {table}",
                parameters=["column", "alias", "table"],
                description="Count distinct values",
                complexity=2,
                examples=[{"column": "department", "alias": "dept_count", "table": "employees"}]
            ),
            SQLTemplate(
                id="AG003",
                name="SUM",
                category=TemplateCategory.AGGREGATION,
                pattern="SELECT SUM({column}) AS {alias} FROM {table}",
                parameters=["column", "alias", "table"],
                description="Sum of column values",
                complexity=1,
                examples=[{"column": "salary", "alias": "total_salary", "table": "employees"}]
            ),
            SQLTemplate(
                id="AG004",
                name="AVG",
                category=TemplateCategory.AGGREGATION,
                pattern="SELECT AVG({column}) AS {alias} FROM {table}",
                parameters=["column", "alias", "table"],
                description="Average of column values",
                complexity=1,
                examples=[{"column": "salary", "alias": "avg_salary", "table": "employees"}]
            ),
            SQLTemplate(
                id="AG005",
                name="MIN/MAX",
                category=TemplateCategory.AGGREGATION,
                pattern="SELECT {function}({column}) AS {alias} FROM {table}",
                parameters=["function", "column", "alias", "table"],
                description="Minimum or maximum value",
                complexity=1,
                examples=[{"function": "MAX", "column": "salary", "alias": "max_salary", "table": "employees"}]
            ),
            SQLTemplate(
                id="AG006",
                name="Multiple Aggregations",
                category=TemplateCategory.AGGREGATION,
                pattern="SELECT {aggregations} FROM {table}",
                parameters=["aggregations", "table"],
                description="Multiple aggregate functions",
                complexity=2,
                examples=[{"aggregations": "COUNT(*) AS total, AVG(salary) AS avg_sal, MAX(salary) AS max_sal", "table": "employees"}]
            ),
            SQLTemplate(
                id="AG007",
                name="Aggregation with Filter",
                category=TemplateCategory.AGGREGATION,
                pattern="SELECT {aggregation} FROM {table} WHERE {condition}",
                parameters=["aggregation", "table", "condition"],
                description="Aggregation with WHERE clause",
                complexity=2,
                examples=[{"aggregation": "AVG(salary) AS avg_salary", "table": "employees", "condition": "department = 'Sales'"}]
            ),
            SQLTemplate(
                id="AG008",
                name="Conditional Aggregation",
                category=TemplateCategory.AGGREGATION,
                pattern="SELECT {aggregation_with_case} FROM {table}",
                parameters=["aggregation_with_case", "table"],
                description="Aggregation with CASE expression",
                complexity=3,
                examples=[{"aggregation_with_case": "SUM(CASE WHEN salary > 50000 THEN 1 ELSE 0 END) AS high_earners", "table": "employees"}]
            ),
        ]
        
        for template in templates:
            self.templates[template.id] = template
    
    def _add_grouping_templates(self):
        """Add 5 grouping templates"""
        
        templates = [
            SQLTemplate(
                id="GP001",
                name="Simple GROUP BY",
                category=TemplateCategory.GROUPING,
                pattern="SELECT {group_columns}, {aggregation} FROM {table} GROUP BY {group_columns}",
                parameters=["group_columns", "aggregation", "table"],
                description="Basic grouping with aggregation",
                complexity=2,
                examples=[{"group_columns": "department", "aggregation": "COUNT(*) AS emp_count", "table": "employees"}]
            ),
            SQLTemplate(
                id="GP002",
                name="GROUP BY with HAVING",
                category=TemplateCategory.GROUPING,
                pattern="SELECT {group_columns}, {aggregation} FROM {table} GROUP BY {group_columns} HAVING {having_condition}",
                parameters=["group_columns", "aggregation", "table", "having_condition"],
                description="Grouping with HAVING filter",
                complexity=3,
                examples=[{"group_columns": "department", "aggregation": "COUNT(*) AS emp_count", "table": "employees", "having_condition": "COUNT(*) > 10"}]
            ),
            SQLTemplate(
                id="GP003",
                name="GROUP BY Multiple Columns",
                category=TemplateCategory.GROUPING,
                pattern="SELECT {group_columns}, {aggregation} FROM {table} GROUP BY {group_columns}",
                parameters=["group_columns", "aggregation", "table"],
                description="Group by multiple columns",
                complexity=3,
                examples=[{"group_columns": "department, location", "aggregation": "AVG(salary) AS avg_salary", "table": "employees"}]
            ),
            SQLTemplate(
                id="GP004",
                name="GROUP BY with WHERE and HAVING",
                category=TemplateCategory.GROUPING,
                pattern="SELECT {group_columns}, {aggregation} FROM {table} WHERE {where_condition} GROUP BY {group_columns} HAVING {having_condition}",
                parameters=["group_columns", "aggregation", "table", "where_condition", "having_condition"],
                description="Complete grouping with both filters",
                complexity=4,
                examples=[{"group_columns": "department", "aggregation": "AVG(salary) AS avg_salary", "table": "employees", "where_condition": "hire_date > '2020-01-01'", "having_condition": "AVG(salary) > 60000"}]
            ),
            SQLTemplate(
                id="GP005",
                name="GROUP BY with ORDER BY",
                category=TemplateCategory.GROUPING,
                pattern="SELECT {group_columns}, {aggregation} FROM {table} GROUP BY {group_columns} ORDER BY {order_spec}",
                parameters=["group_columns", "aggregation", "table", "order_spec"],
                description="Grouping with ordering",
                complexity=3,
                examples=[{"group_columns": "department", "aggregation": "COUNT(*) AS emp_count", "table": "employees", "order_spec": "emp_count DESC"}]
            ),
        ]
        
        for template in templates:
            self.templates[template.id] = template
    
    def _add_subquery_templates(self):
        """Add 6 subquery templates"""
        
        templates = [
            SQLTemplate(
                id="SQ001",
                name="Subquery in WHERE",
                category=TemplateCategory.SUBQUERIES,
                pattern="SELECT {columns} FROM {table} WHERE {column} IN (SELECT {subquery_column} FROM {subquery_table} WHERE {subquery_condition})",
                parameters=["columns", "table", "column", "subquery_column", "subquery_table", "subquery_condition"],
                description="Subquery in WHERE clause with IN",
                complexity=3,
                examples=[{"columns": "*", "table": "employees", "column": "dept_id", "subquery_column": "id", "subquery_table": "departments", "subquery_condition": "budget > 100000"}]
            ),
            SQLTemplate(
                id="SQ002",
                name="Scalar Subquery",
                category=TemplateCategory.SUBQUERIES,
                pattern="SELECT {columns}, (SELECT {subquery_expression} FROM {subquery_table} WHERE {subquery_condition}) AS {alias} FROM {table}",
                parameters=["columns", "subquery_expression", "subquery_table", "subquery_condition", "alias", "table"],
                description="Scalar subquery in SELECT",
                complexity=3,
                examples=[{"columns": "name, salary", "subquery_expression": "AVG(salary)", "subquery_table": "employees", "subquery_condition": "1=1", "alias": "avg_salary", "table": "employees"}]
            ),
            SQLTemplate(
                id="SQ003",
                name="Correlated Subquery",
                category=TemplateCategory.SUBQUERIES,
                pattern="SELECT {columns} FROM {table} {alias1} WHERE {column} > (SELECT AVG({subquery_column}) FROM {table} {alias2} WHERE {correlation_condition})",
                parameters=["columns", "table", "alias1", "column", "subquery_column", "alias2", "correlation_condition"],
                description="Correlated subquery",
                complexity=4,
                examples=[{"columns": "*", "table": "employees", "alias1": "e1", "column": "salary", "subquery_column": "salary", "alias2": "e2", "correlation_condition": "e1.department = e2.department"}]
            ),
            SQLTemplate(
                id="SQ004",
                name="EXISTS Subquery",
                category=TemplateCategory.SUBQUERIES,
                pattern="SELECT {columns} FROM {table} {alias1} WHERE EXISTS (SELECT 1 FROM {subquery_table} {alias2} WHERE {correlation_condition})",
                parameters=["columns", "table", "alias1", "subquery_table", "alias2", "correlation_condition"],
                description="EXISTS subquery",
                complexity=3,
                examples=[{"columns": "*", "table": "departments", "alias1": "d", "subquery_table": "employees", "alias2": "e", "correlation_condition": "e.dept_id = d.id AND e.salary > 100000"}]
            ),
            SQLTemplate(
                id="SQ005",
                name="NOT EXISTS Subquery",
                category=TemplateCategory.SUBQUERIES,
                pattern="SELECT {columns} FROM {table} {alias1} WHERE NOT EXISTS (SELECT 1 FROM {subquery_table} {alias2} WHERE {correlation_condition})",
                parameters=["columns", "table", "alias1", "subquery_table", "alias2", "correlation_condition"],
                description="NOT EXISTS subquery",
                complexity=3,
                examples=[{"columns": "*", "table": "departments", "alias1": "d", "subquery_table": "employees", "alias2": "e", "correlation_condition": "e.dept_id = d.id"}]
            ),
            SQLTemplate(
                id="SQ006",
                name="Derived Table",
                category=TemplateCategory.SUBQUERIES,
                pattern="SELECT {columns} FROM (SELECT {subquery_columns} FROM {subquery_table} WHERE {subquery_condition}) AS {alias}",
                parameters=["columns", "subquery_columns", "subquery_table", "subquery_condition", "alias"],
                description="Derived table in FROM clause",
                complexity=3,
                examples=[{"columns": "*", "subquery_columns": "department, AVG(salary) AS avg_sal", "subquery_table": "employees", "subquery_condition": "1=1 GROUP BY department", "alias": "dept_avg"}]
            ),
        ]
        
        for template in templates:
            self.templates[template.id] = template
    
    def _add_cte_templates(self):
        """Add 4 CTE (Common Table Expression) templates"""
        
        templates = [
            SQLTemplate(
                id="CT001",
                name="Simple CTE",
                category=TemplateCategory.CTES,
                pattern="WITH {cte_name} AS (SELECT {cte_columns} FROM {cte_table} WHERE {cte_condition}) SELECT {columns} FROM {cte_name}",
                parameters=["cte_name", "cte_columns", "cte_table", "cte_condition", "columns"],
                description="Basic Common Table Expression",
                complexity=3,
                examples=[{"cte_name": "high_earners", "cte_columns": "*", "cte_table": "employees", "cte_condition": "salary > 80000", "columns": "*"}]
            ),
            SQLTemplate(
                id="CT002",
                name="Multiple CTEs",
                category=TemplateCategory.CTES,
                pattern="WITH {cte1_name} AS (SELECT {cte1_query}), {cte2_name} AS (SELECT {cte2_query}) SELECT {columns} FROM {cte1_name} JOIN {cte2_name} ON {join_condition}",
                parameters=["cte1_name", "cte1_query", "cte2_name", "cte2_query", "columns", "join_condition"],
                description="Multiple CTEs with join",
                complexity=4,
                examples=[{"cte1_name": "dept_avg", "cte1_query": "department, AVG(salary) AS avg_sal FROM employees GROUP BY department", "cte2_name": "dept_count", "cte2_query": "department, COUNT(*) AS emp_count FROM employees GROUP BY department", "columns": "*", "join_condition": "dept_avg.department = dept_count.department"}]
            ),
            SQLTemplate(
                id="CT003",
                name="Recursive CTE",
                category=TemplateCategory.CTES,
                pattern="WITH RECURSIVE {cte_name} AS (SELECT {base_query} UNION ALL SELECT {recursive_query} FROM {cte_name} WHERE {termination_condition}) SELECT {columns} FROM {cte_name}",
                parameters=["cte_name", "base_query", "recursive_query", "termination_condition", "columns"],
                description="Recursive CTE for hierarchical data",
                complexity=5,
                examples=[{"cte_name": "org_hierarchy", "base_query": "id, name, manager_id, 1 AS level FROM employees WHERE manager_id IS NULL", "recursive_query": "e.id, e.name, e.manager_id, oh.level + 1 FROM employees e JOIN org_hierarchy oh ON e.manager_id = oh.id", "termination_condition": "level < 5", "columns": "*"}]
            ),
            SQLTemplate(
                id="CT004",
                name="CTE with Aggregation",
                category=TemplateCategory.CTES,
                pattern="WITH {cte_name} AS (SELECT {group_columns}, {aggregation} FROM {table} GROUP BY {group_columns}) SELECT {columns} FROM {cte_name} WHERE {condition}",
                parameters=["cte_name", "group_columns", "aggregation", "table", "columns", "condition"],
                description="CTE with aggregation and filtering",
                complexity=4,
                examples=[{"cte_name": "dept_stats", "group_columns": "department", "aggregation": "COUNT(*) AS emp_count, AVG(salary) AS avg_salary", "table": "employees", "columns": "*", "condition": "emp_count > 10"}]
            ),
        ]
        
        for template in templates:
            self.templates[template.id] = template
    
    def get_template(self, template_id: str) -> Optional[SQLTemplate]:
        """Get template by ID"""
        return self.templates.get(template_id)
    
    def get_templates_by_category(self, category: TemplateCategory) -> List[SQLTemplate]:
        """Get all templates in a category"""
        return [t for t in self.templates.values() if t.category == category]
    
    def search_templates(self, 
                        keyword: Optional[str] = None,
                        category: Optional[TemplateCategory] = None,
                        max_complexity: Optional[int] = None) -> List[SQLTemplate]:
        """
        Search templates by various criteria
        
        Args:
            keyword: Search in name and description
            category: Filter by category
            max_complexity: Maximum complexity level
            
        Returns:
            List of matching templates
        """
        results = list(self.templates.values())
        
        if keyword:
            keyword_lower = keyword.lower()
            results = [t for t in results 
                      if keyword_lower in t.name.lower() 
                      or keyword_lower in t.description.lower()]
        
        if category:
            results = [t for t in results if t.category == category]
        
        if max_complexity is not None:
            results = [t for t in results if t.complexity <= max_complexity]
        
        return results
    
    def get_template_count(self) -> int:
        """Get total number of templates"""
        return len(self.templates)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get library statistics"""
        stats = {
            "total_templates": len(self.templates),
            "by_category": {},
            "by_complexity": {}
        }
        
        for template in self.templates.values():
            # Count by category
            cat_name = template.category.value
            stats["by_category"][cat_name] = stats["by_category"].get(cat_name, 0) + 1
            
            # Count by complexity
            complexity = template.complexity
            stats["by_complexity"][complexity] = stats["by_complexity"].get(complexity, 0) + 1
        
        return stats


# Example usage
if __name__ == "__main__":
    library = TemplateLibrary()
    
    print(f"Total templates: {library.get_template_count()}")
    print("\nLibrary statistics:")
    stats = library.get_statistics()
    print(json.dumps(stats, indent=2))
    
    # Test template instantiation
    template = library.get_template("BS002")
    if template:
        sql = template.instantiate({
            "columns": "name, email, department",
            "table": "employees"
        })
        print(f"\nExample SQL:\n{sql}")
    
    # Search templates
    join_templates = library.search_templates(keyword="join", max_complexity=3)
    print(f"\nFound {len(join_templates)} join templates with complexity <= 3")
