#!/usr/bin/env python3
"""
Quick test for DIVA-SQL benchmark evaluation

This script runs a small test with 1-2 queries to verify the benchmark setup.
"""

import os
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.gemini_client import create_gemini_client
from src.core.pipeline import DIVASQLPipeline

def run_mini_test():
    """Run a minimal test of the DIVA-SQL benchmark setup"""
    print("🧪 Running mini-test for DIVA-SQL benchmark")
    print("=" * 50)
    
    # Check Google API key
    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        print("❌ Error: GOOGLE_API_KEY environment variable not set")
        print("   Please set it with: export GOOGLE_API_KEY='your_api_key'")
        return False
    
    print("✓ Google API key found")
    
    # Test database schema
    schema = {
        "tables": {
            "employees": ["employee_id", "name", "position", "salary", "department_id", "hire_date"],
            "departments": ["department_id", "name", "location", "budget"],
            "projects": ["project_id", "name", "start_date", "end_date", "budget", "department_id"],
            "employee_projects": ["employee_id", "project_id", "role"]
        }
    }
    
    # Sample query
    query = "Find employees with salary greater than 50000"
    
    try:
        # Initialize client and pipeline
        client = create_gemini_client(model_name="gemini-2.0-flash")
        pipeline = DIVASQLPipeline(client, model_name="gemini-2.0-flash")
        
        print("✓ Successfully initialized DIVA-SQL pipeline")
        print("\n🔍 Testing query generation...")
        print(f"Query: \"{query}\"")
        
        # Generate SQL
        result = pipeline.generate_sql(query, schema)
        
        print(f"\nGeneration status: {result.status.value}")
        print(f"Confidence score: {result.confidence_score:.2f}")
        
        if result.final_sql:
            print(f"\nGenerated SQL:")
            print(f"{result.final_sql}")
            print("\n✅ Successfully generated SQL")
        else:
            print(f"\n❌ Failed to generate SQL: {result.error_message}")
            return False
        
        # Test semantic DAG
        if result.semantic_dag:
            nodes = result.semantic_dag.get_execution_order()
            print(f"\nSemantic decomposition: {len(nodes)} nodes")
            for i, node_id in enumerate(nodes):
                node = result.semantic_dag.nodes[node_id]
                print(f"  {i+1}. {node.description}")
            print("\n✅ Successfully decomposed query")
        
        print("\n🎉 Mini-test completed successfully!")
        return True
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dataset_access():
    """Test if benchmark datasets are accessible"""
    print("\n📊 Testing benchmark dataset access")
    print("=" * 50)
    
    # Check Synthetic dataset
    synthetic_path = Path(__file__).parent.parent / "data" / "benchmarks" / "synthetic"
    if synthetic_path.exists() and (synthetic_path / "dev.json").exists():
        print("✓ Synthetic dataset found")
        try:
            with open(synthetic_path / "dev.json", 'r') as f:
                data = json.load(f)
                print(f"  • Contains {len(data)} examples")
            print("✓ Successfully loaded synthetic data")
            
            # Check if database exists
            db_path = synthetic_path / "database" / "employees.sqlite"
            if db_path.exists():
                print("✓ Synthetic database found")
            else:
                print("❌ Synthetic database not found")
                print("   Run: python evaluation/create_synthetic_dataset.py")
        except Exception as e:
            print(f"❌ Error loading synthetic data: {e}")
    else:
        print("❓ Synthetic dataset not found")
        print("   Run: python evaluation/create_synthetic_dataset.py")
    
    # Check Spider (optional)
    spider_path = Path(__file__).parent.parent / "data" / "benchmarks" / "spider"
    if spider_path.exists() and (spider_path / "dev.json").exists():
        print("✓ Spider dataset found")
    else:
        print("❓ Spider dataset not found (optional)")
    
    # Check BIRD (optional)
    bird_path = Path(__file__).parent.parent / "data" / "benchmarks" / "bird-dev.json"
    if bird_path.exists():
        print("✓ BIRD dataset found")
    else:
        print("❓ BIRD dataset not found (optional)")

if __name__ == "__main__":
    success = run_mini_test()
    if success:
        test_dataset_access()
        
    print("\n🚀 Next steps:")
    if success:
        print("1. Run the full benchmark: ./run_benchmark.sh")
        print("2. Or try a rate-limited sample: python evaluation/rate_limited_eval.py --benchmark spider --sample 5 --delay 3")
    else:
        print("1. Check your API key and try again")
        print("2. Download the benchmark datasets: python evaluation/download_datasets.py")
