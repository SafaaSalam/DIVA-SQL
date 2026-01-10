#!/usr/bin/env python3
"""
Simplified test for DIVA-SQL using the synthetic dataset
"""

import os
import sys
import json
import time
import sqlite3
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Import DIVA-SQL components
try:
    from src.core.pipeline import DIVASQLPipeline
    from src.utils.gemini_client import GeminiLLMClient
except ImportError as e:
    print(f"Error importing DIVA-SQL modules: {e}")
    print("Make sure DIVA-SQL is properly installed and in your Python path.")
    sys.exit(1)

def execute_query(db_path, query):
    """Execute a SQL query and return the results"""
    if not os.path.exists(db_path):
        return None, f"Database file not found: {db_path}"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        return results, None
    except Exception as e:
        return None, str(e)

def main():
    print("🧪 Running simplified test for DIVA-SQL with synthetic data")
    
    # Check if API key is set
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY environment variable not set")
        print("Please set your API key with: export GOOGLE_API_KEY='your_api_key'")
        sys.exit(1)
    
    print("✓ Google API key found")
    
    # Check for synthetic dataset
    benchmark_dir = Path(__file__).parent.parent / "data" / "benchmarks"
    synthetic_dir = benchmark_dir / "synthetic"
    db_path = synthetic_dir / "database" / "employees.sqlite"
    
    if not db_path.exists():
        print(f"❌ Synthetic database not found at {db_path}")
        print("Please run evaluation/create_synthetic_dataset.py first")
        sys.exit(1)
    
    print(f"✓ Synthetic database found at {db_path}")
    
    # Load questions from synthetic dataset
    with open(synthetic_dir / "dev.json", "r") as f:
        data = json.load(f)
        
    # Select just 2 questions for testing
    questions = data[:2]
    
    # Create LLM client
    llm_client = GeminiLLMClient(api_key=api_key, model_name="gemini-2.0-flash")
    print("✓ Created Gemini client")
    
    # Create DIVA-SQL pipeline
    pipeline = DIVASQLPipeline(llm_client)
    print("✓ Initialized DIVA-SQL pipeline")
    
    # Extract database schema
    schema = {
        "tables": {
            "employees": ["employee_id", "name", "position", "salary", "department_id", "hire_date"],
            "departments": ["department_id", "name", "location", "budget"],
            "projects": ["project_id", "name", "start_date", "end_date", "budget", "department_id"],
            "employee_projects": ["employee_id", "project_id", "role"]
        }
    }
    
    # Run tests
    print("\nRunning tests...")
    
    for i, question_data in enumerate(questions):
        question = question_data["question"]
        gold_query = question_data["query"]
        
        print(f"\n[Test {i+1}/{len(questions)}] Question: {question}")
        print(f"Gold query: {gold_query}")
        
        try:
            # Execute the gold query
            gold_results, gold_error = execute_query(db_path, gold_query)
            if gold_error:
                print(f"❌ Error executing gold query: {gold_error}")
                continue
                
            print(f"✓ Gold query results: {gold_results[:3]}{'...' if len(gold_results) > 3 else ''}")
            
            # Generate SQL with DIVA-SQL
            start_time = time.time()
            result = pipeline.generate_sql(question, schema)
            elapsed_time = time.time() - start_time
            
            if result.final_sql:
                generated_sql = result.final_sql
            else:
                print(f"❌ Failed to generate SQL: {result.error_message}")
                continue
            
            print(f"✓ Generated SQL ({elapsed_time:.2f}s): {generated_sql}")
            print(f"✓ Status: {result.status.value}")
            print(f"✓ Confidence: {result.confidence_score:.2f}")
            
            # Execute the generated SQL
            results, error = execute_query(db_path, generated_sql)
            if error:
                print(f"❌ Error executing generated SQL: {error}")
                continue
                
            print(f"✓ Generated query results: {results[:3]}{'...' if len(results) > 3 else ''}")
            
            # Compare results
            gold_set = set(map(tuple, gold_results))
            generated_set = set(map(tuple, results))
            
            if gold_set == generated_set:
                print("✅ Results match! The generated SQL is correct.")
            else:
                print("❌ Results don't match. The generated SQL produced different results.")
            
            # Display semantic decomposition
            if result.semantic_dag:
                nodes = result.semantic_dag.get_execution_order()
                print(f"\nSemantic decomposition: {len(nodes)} nodes")
                for j, node_id in enumerate(nodes):
                    node = result.semantic_dag.nodes[node_id]
                    print(f"  {j+1}. {node.description}")
                
            # Add delay to avoid rate limiting
            if i < len(questions) - 1:
                delay_time = 60  # 60 seconds to avoid rate limits
                print(f"\nWaiting {delay_time} seconds to avoid API rate limits...")
                time.sleep(delay_time)
                
        except Exception as e:
            print(f"❌ Error in test {i+1}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n🎉 Tests completed!")

if __name__ == "__main__":
    main()
