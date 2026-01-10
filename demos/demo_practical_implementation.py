"""
Demo script for DIVA-SQL practical implementation

This script demonstrates the complete DIVA-SQL pipeline with:
1. Template-based SQL generation
2. Three-stage verification
3. Performance monitoring
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.templates import TemplateLibrary, TemplateSelector
from src.verification import SyntaxVerifier, SemanticVerifier, ExecutionVerifier, FeedbackLoop
from src.monitoring import PerformanceTracker, QueryComplexity
from src.core.semantic_dag import SemanticNode, NodeType


def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print('='*70)


def demo_template_library():
    """Demonstrate the template library"""
    print_section("1. Template Library Demo")
    
    library = TemplateLibrary()
    
    print(f"\nTotal templates: {library.get_template_count()}")
    
    # Show statistics
    stats = library.get_statistics()
    print("\nTemplates by category:")
    for category, count in stats['by_category'].items():
        print(f"  {category}: {count} templates")
    
    # Show a sample template
    template = library.get_template("FT002")  # WHERE with comparison
    if template:
        print(f"\nSample Template: {template.name}")
        print(f"Pattern: {template.pattern}")
        print(f"Parameters: {template.parameters}")
        
        # Instantiate it
        sql = template.instantiate({
            "columns": "*",
            "table": "employees",
            "column": "salary",
            "operator": ">",
            "value": "50000"
        })
        print(f"Example SQL: {sql}")


def demo_template_selection():
    """Demonstrate template selection"""
    print_section("2. Template Selection Demo")
    
    library = TemplateLibrary()
    selector = TemplateSelector(library)
    
    # Create a semantic node
    filter_node = SemanticNode(
        node_id="filter_1",
        node_type=NodeType.FILTER,
        description="Filter employees by salary",
        parameters={
            "table": "employees",
            "columns": "*",
            "column": "salary",
            "operator": ">",
            "value": "50000"
        }
    )
    
    print(f"\nSemantic Node: {filter_node.description}")
    print(f"Type: {filter_node.node_type.value}")
    print(f"Parameters: {filter_node.parameters}")
    
    # Select template
    match = selector.select_template(filter_node)
    
    print(f"\nSelected Template: {match.template.name}")
    print(f"Confidence: {match.confidence:.2f}")
    print(f"Reasoning: {match.reasoning}")
    print(f"Suggested params: {match.suggested_params}")
    
    # Generate SQL
    if match.suggested_params:
        sql = match.template.instantiate(match.suggested_params)
        print(f"\nGenerated SQL:\n{sql}")


def demo_syntax_verification():
    """Demonstrate syntax verification"""
    print_section("3. Syntax Verification Demo")
    
    verifier = SyntaxVerifier()
    
    test_queries = [
        ("Valid query", "SELECT * FROM employees WHERE salary > 50000"),
        ("Unbalanced parens", "SELECT * FROM employees WHERE (salary > 50000"),
        ("Missing FROM", "SELECT * WHERE salary > 50000"),
    ]
    
    for name, query in test_queries:
        print(f"\n{name}: {query}")
        result = verifier.verify(query)
        
        print(f"Valid: {result.is_valid}")
        
        if result.errors:
            print("Errors:")
            for error in result.errors:
                print(f"  - {error.message}")
                if error.suggestion:
                    print(f"    Suggestion: {error.suggestion}")


def demo_semantic_verification():
    """Demonstrate semantic verification"""
    print_section("4. Semantic Verification Demo")
    
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
                    "name": {"type": "VARCHAR"}
                }
            }
        }
    }
    
    verifier = SemanticVerifier(schema)
    
    test_queries = [
        ("Valid query", "SELECT name, salary FROM employees WHERE salary > 50000"),
        ("Wrong table", "SELECT name FROM employee WHERE salary > 50000"),
        ("Wrong column", "SELECT nam FROM employees"),
    ]
    
    for name, query in test_queries:
        print(f"\n{name}: {query}")
        result = verifier.verify(query)
        
        print(f"Valid: {result.is_valid}")
        print(f"Validated tables: {result.validated_tables}")
        print(f"Validated columns: {result.validated_columns}")
        
        if result.errors:
            print("Errors:")
            for error in result.errors:
                print(f"  - {error.message}")
                if error.suggestion:
                    print(f"    Suggestion: {error.suggestion}")


def demo_execution_verification():
    """Demonstrate execution verification"""
    print_section("5. Execution Verification Demo")
    
    schema = {
        "tables": {
            "employees": {
                "columns": {
                    "id": {"type": "INTEGER"},
                    "name": {"type": "TEXT"},
                    "salary": {"type": "INTEGER"}
                }
            }
        }
    }
    
    sample_data = {
        "employees": [
            {"id": 1, "name": "Alice", "salary": 60000},
            {"id": 2, "name": "Bob", "salary": 75000},
            {"id": 3, "name": "Charlie", "salary": 55000},
        ]
    }
    
    verifier = ExecutionVerifier()
    verifier.setup_test_database(schema, sample_data)
    
    test_queries = [
        ("Valid query", "SELECT * FROM employees WHERE salary > 50000"),
        ("Empty result", "SELECT * FROM employees WHERE salary > 100000"),
        ("Runtime error", "SELECT * FROM unknown_table"),
    ]
    
    for name, query in test_queries:
        print(f"\n{name}: {query}")
        result = verifier.verify(query)
        
        print(f"Valid: {result.is_valid}")
        
        if result.execution_result:
            print(f"Success: {result.execution_result.success}")
            print(f"Rows: {result.execution_result.rows_returned}")
            print(f"Time: {result.execution_result.execution_time_ms:.2f}ms")
        
        if result.errors:
            print("Errors:")
            for error in result.errors:
                print(f"  - {error.message}")
    
    verifier.close()


def demo_feedback_loop():
    """Demonstrate the complete feedback loop"""
    print_section("6. Three-Stage Verification with Feedback Loop")
    
    schema = {
        "tables": {
            "employees": {
                "columns": {
                    "id": {"type": "INTEGER"},
                    "name": {"type": "TEXT"},
                    "salary": {"type": "INTEGER"}
                }
            }
        }
    }
    
    sample_data = {
        "employees": [
            {"id": 1, "name": "Alice", "salary": 60000},
            {"id": 2, "name": "Bob", "salary": 75000},
        ]
    }
    
    feedback_loop = FeedbackLoop(schema, enable_auto_fix=True)
    
    test_queries = [
        ("Valid query", "SELECT * FROM employees WHERE salary > 50000"),
        ("Auto-fixable", "SELECT * FROM employees WHERE (salary > 50000"),  # Unbalanced parens
    ]
    
    for name, query in test_queries:
        print(f"\n{name}: {query}")
        
        result = feedback_loop.verify_sql(query, sample_data=sample_data)
        
        # Generate report
        report = feedback_loop.generate_feedback_report(result)
        print(report)


def demo_performance_tracking():
    """Demonstrate performance tracking"""
    print_section("7. Performance Tracking Demo")
    
    import time
    
    tracker = PerformanceTracker()
    
    # Simulate a simple query
    tracking_id = tracker.start_tracking("demo_query_1", QueryComplexity.SIMPLE)
    
    tracker.start_stage(tracking_id, "decomposition")
    time.sleep(0.05)  # Simulate work
    tracker.end_stage(tracking_id, "decomposition")
    
    tracker.start_stage(tracking_id, "generation")
    time.sleep(0.08)  # Simulate work
    tracker.end_stage(tracking_id, "generation")
    
    tracker.start_stage(tracking_id, "verification")
    time.sleep(0.03)  # Simulate work
    tracker.end_stage(tracking_id, "verification")
    
    metric = tracker.end_tracking(tracking_id, metadata={"success": True})
    
    print(f"\nQuery completed in {metric.total_time_ms:.2f}ms")
    print(f"Breakdown:")
    for stage, duration in metric.breakdown.items():
        print(f"  {stage}: {duration:.2f}ms")
    
    # Generate report
    print("\n" + tracker.generate_report())
    
    # Check targets
    targets = tracker.check_targets()
    print(f"\nSimple queries target ({tracker.TARGET_SIMPLE_MS}ms): ", end="")
    print("✓ MET" if targets['simple_queries']['target_met'] else "✗ NOT MET")


def main():
    """Run all demos"""
    print("\n" + "="*70)
    print("  DIVA-SQL Practical Implementation Demo")
    print("  Showcasing Template Library, Three-Stage Verification, and Monitoring")
    print("="*70)
    
    try:
        demo_template_library()
        demo_template_selection()
        demo_syntax_verification()
        demo_semantic_verification()
        demo_execution_verification()
        demo_feedback_loop()
        demo_performance_tracking()
        
        print_section("Demo Complete!")
        print("\n✓ All components demonstrated successfully!")
        print("\nKey Features Implemented:")
        print("  • 53 SQL templates covering basic to complex operations")
        print("  • Intelligent template selection with confidence scoring")
        print("  • Stage 1: Syntax verification with sqlparse")
        print("  • Stage 2: Semantic alignment with schema validation")
        print("  • Stage 3: Execution testing with runtime error detection")
        print("  • Feedback loop with diagnostic reporting and auto-fix")
        print("  • Performance tracking with latency targets (2.3s/5.8s)")
        print("\nSee PRACTICAL_IMPLEMENTATION_GUIDE.md for complete documentation.")
        
    except Exception as e:
        print(f"\n✗ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
