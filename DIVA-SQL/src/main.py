"""
Main entry point for DIVA-SQL

This script provides a command-line interface for running DIVA-SQL
and conducting evaluations.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from src.core.pipeline import DIVASQLPipeline
from evaluation.framework import BenchmarkEvaluator, DIVASQLSystem, ZeroShotBaselineSystem


def load_openai_client():
    """Load OpenAI client with API key"""
    try:
        import openai
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            print("Error: OPENAI_API_KEY not found in environment variables")
            sys.exit(1)
        
        return openai.OpenAI(api_key=api_key)
    
    except ImportError:
        print("Error: OpenAI package not installed. Run: pip install openai")
        sys.exit(1)


def interactive_mode(llm_client):
    """Run DIVA-SQL in interactive mode"""
    print("DIVA-SQL Interactive Mode")
    print("=" * 30)
    print("Type 'quit' to exit\n")
    
    # Initialize pipeline
    pipeline = DIVASQLPipeline(llm_client)
    
    # Sample schema for demo
    sample_schema = {
        "tables": {
            "Employees": ["EmpID", "Name", "DeptID", "HireDate", "Salary"],
            "Departments": ["DeptID", "DeptName", "ManagerID"],
            "Projects": ["ProjectID", "ProjectName", "Budget", "DeptID"],
            "Assignments": ["EmpID", "ProjectID", "StartDate", "EndDate"]
        }
    }
    
    print("Sample Database Schema:")
    print(json.dumps(sample_schema, indent=2))
    print("\n" + "="*50 + "\n")
    
    while True:
        try:
            # Get user input
            nl_query = input("Enter your natural language query: ").strip()
            
            if nl_query.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not nl_query:
                continue
            
            print(f"\nProcessing: '{nl_query}'")
            print("-" * 40)
            
            # Generate SQL
            result = pipeline.generate_sql(nl_query, sample_schema)
            
            # Display results
            print(f"Status: {result.status.value}")
            print(f"Execution Time: {result.execution_time:.2f}s")
            print(f"Confidence Score: {result.confidence_score:.2f}")
            
            if result.final_sql:
                print(f"\nGenerated SQL:")
                print(result.final_sql)
            
            if result.semantic_dag:
                print(f"\nSemantic Decomposition:")
                print(result.semantic_dag.visualize())
            
            if result.error_message:
                print(f"\nError: {result.error_message}")
            
            # Show verification log summary
            if result.verification_log:
                passed = sum(1 for log in result.verification_log if log.get("verification_status") == "PASS")
                total = len(result.verification_log)
                print(f"\nVerification Summary: {passed}/{total} nodes verified successfully")
            
            print("\n" + "="*50 + "\n")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {str(e)}")


def evaluation_mode(llm_client, benchmark_name: str, data_path: str, database_path: str):
    """Run evaluation on a benchmark"""
    print(f"DIVA-SQL Evaluation Mode")
    print(f"Benchmark: {benchmark_name}")
    print("=" * 40)
    
    # Load benchmark data
    benchmark_data = []
    if benchmark_name.lower() == "bird":
        from evaluation.framework import load_bird_benchmark
        benchmark_data = load_bird_benchmark(data_path)
    elif benchmark_name.lower() == "spider":
        from evaluation.framework import load_spider_benchmark
        benchmark_data = load_spider_benchmark(data_path)
    else:
        print(f"Error: Unknown benchmark '{benchmark_name}'")
        sys.exit(1)
    
    # Sample schema (in practice, this would be loaded from the benchmark)
    sample_schema = {
        "tables": {
            "Employees": ["EmpID", "Name", "DeptID", "HireDate", "Salary"],
            "Departments": ["DeptID", "DeptName", "ManagerID"]
        }
    }
    
    # Initialize evaluator
    evaluator = BenchmarkEvaluator(database_path)
    
    # Create systems to compare
    diva_system = DIVASQLSystem(llm_client)
    baseline_system = ZeroShotBaselineSystem(llm_client)
    
    systems = [diva_system, baseline_system]
    
    print(f"Evaluating {len(systems)} systems on {len(benchmark_data)} queries...")
    
    # Run evaluation
    comparison_results = evaluator.compare_systems(systems, benchmark_data, sample_schema)
    
    # Generate and display report
    report = evaluator.generate_comparison_report(comparison_results)
    print("\n" + report)
    
    # Save results
    output_file = f"evaluation_results_{benchmark_name}.json"
    results_data = {
        system_name: {
            "execution_accuracy": results.execution_accuracy,
            "avg_valid_efficiency_score": results.avg_valid_efficiency_score,
            "avg_execution_time": results.avg_execution_time,
            "error_analysis": results.error_analysis
        }
        for system_name, results in comparison_results.items()
    }
    
    with open(output_file, 'w') as f:
        json.dump(results_data, f, indent=2)
    
    print(f"\nDetailed results saved to: {output_file}")


def single_query_mode(llm_client, query: str, schema_file: Optional[str] = None):
    """Process a single query"""
    print("DIVA-SQL Single Query Mode")
    print("=" * 30)
    
    # Load schema if provided
    if schema_file:
        try:
            with open(schema_file, 'r') as f:
                schema = json.load(f)
        except Exception as e:
            print(f"Error loading schema file: {e}")
            sys.exit(1)
    else:
        # Use sample schema
        schema = {
            "tables": {
                "Employees": ["EmpID", "Name", "DeptID", "HireDate", "Salary"],
                "Departments": ["DeptID", "DeptName", "ManagerID"]
            }
        }
    
    # Initialize pipeline
    pipeline = DIVASQLPipeline(llm_client)
    
    print(f"Query: {query}")
    print(f"Schema: {json.dumps(schema, indent=2)}")
    print("-" * 40)
    
    # Generate SQL
    result = pipeline.generate_sql(query, schema)
    
    # Display results
    print(f"Status: {result.status.value}")
    print(f"Final SQL: {result.final_sql}")
    print(f"Confidence: {result.confidence_score}")
    print(f"Execution Time: {result.execution_time:.2f}s")
    
    if result.semantic_dag:
        print(f"\nSemantic DAG:")
        print(result.semantic_dag.visualize())


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="DIVA-SQL: Decomposable, Interpretable, and Verifiable Text-to-SQL")
    
    subparsers = parser.add_subparsers(dest='mode', help='Operation mode')
    
    # Interactive mode
    interactive_parser = subparsers.add_parser('interactive', help='Run in interactive mode')
    
    # Single query mode
    single_parser = subparsers.add_parser('query', help='Process a single query')
    single_parser.add_argument('query', help='Natural language query')
    single_parser.add_argument('--schema', help='Path to schema JSON file')
    
    # Evaluation mode
    eval_parser = subparsers.add_parser('evaluate', help='Run benchmark evaluation')
    eval_parser.add_argument('benchmark', choices=['bird', 'spider'], help='Benchmark to evaluate on')
    eval_parser.add_argument('--data-path', required=True, help='Path to benchmark data')
    eval_parser.add_argument('--database-path', required=True, help='Path to database file')
    
    # Demo mode
    demo_parser = subparsers.add_parser('demo', help='Run demo with sample queries')
    
    args = parser.parse_args()
    
    if not args.mode:
        parser.print_help()
        return
    
    # Load LLM client
    print("Initializing LLM client...")
    llm_client = load_openai_client()
    
    # Route to appropriate mode
    if args.mode == 'interactive':
        interactive_mode(llm_client)
    elif args.mode == 'query':
        single_query_mode(llm_client, args.query, args.schema)
    elif args.mode == 'evaluate':
        evaluation_mode(llm_client, args.benchmark, args.data_path, args.database_path)
    elif args.mode == 'demo':
        demo_queries = [
            "What are the names of all employees?",
            "How many employees work in each department?",
            "Which departments have more than 5 employees?",
            "What is the average salary by department?",
            "Who are the managers of each department?"
        ]
        
        schema = {
            "tables": {
                "Employees": ["EmpID", "Name", "DeptID", "HireDate", "Salary"],
                "Departments": ["DeptID", "DeptName", "ManagerID"]
            }
        }
        
        pipeline = DIVASQLPipeline(llm_client)
        
        print("DIVA-SQL Demo")
        print("=" * 20)
        
        for i, query in enumerate(demo_queries, 1):
            print(f"\nDemo Query {i}: {query}")
            print("-" * 40)
            
            result = pipeline.generate_sql(query, schema)
            
            print(f"Status: {result.status.value}")
            print(f"Generated SQL: {result.final_sql}")
            print(f"Confidence: {result.confidence_score:.2f}")
            
            if result.semantic_dag:
                print("Semantic Steps:")
                for node_id, node in result.semantic_dag.nodes.items():
                    print(f"  - {node.description}")


if __name__ == "__main__":
    main()
