"""
Benchmark Evaluation for DIVA-SQL

This script evaluates DIVA-SQL on established benchmarks like Spider and BIRD.
"""

import os
import json
import time
import argparse
import sqlite3
import pandas as pd
from tqdm import tqdm
from pathlib import Path

# Add project root to path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.core.pipeline import DIVASQLPipeline, PipelineStatus
from src.utils.gemini_client import create_gemini_client

# Configuration
def parse_args():
    parser = argparse.ArgumentParser(description='Evaluate DIVA-SQL on benchmarks')
    parser.add_argument('--benchmark', type=str, choices=['spider', 'bird'], required=True,
                        help='Benchmark dataset to evaluate on')
    parser.add_argument('--split', type=str, default='dev', choices=['dev', 'test'],
                        help='Dataset split to use')
    parser.add_argument('--model', type=str, default='gemini-2.0-flash',
                        help='LLM model to use')
    parser.add_argument('--limit', type=int, default=None,
                        help='Limit evaluation to N examples (for testing)')
    parser.add_argument('--output', type=str, default='results/benchmark_results.csv',
                        help='Output file for results')
    return parser.parse_args()

def load_spider_data(split='dev'):
    """Load the Spider benchmark data"""
    data_path = f'data/benchmarks/spider/{split}.json'
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    # Process data into a list of examples
    examples = []
    for item in data:
        db_id = item['db_id']
        db_path = f'data/benchmarks/spider/database/{db_id}/{db_id}.sqlite'
        
        # Extract schema
        schema = extract_schema_from_sqlite(db_path)
        
        examples.append({
            'id': f"spider_{db_id}_{len(examples)}",
            'question': item['question'],
            'db_id': db_id,
            'db_path': db_path,
            'schema': schema,
            'gold_sql': item['query']
        })
    
    return examples

def load_bird_data(split='dev'):
    """Load the BIRD benchmark data"""
    data_path = f'data/benchmarks/bird-{split}.json'
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    # Process data into a list of examples
    examples = []
    for item in data:
        db_id = item['db_id']
        db_path = f'data/benchmarks/bird/databases/{db_id}.sqlite'
        
        # Extract schema
        schema = extract_schema_from_sqlite(db_path)
        
        examples.append({
            'id': item['question_id'],
            'question': item['question'],
            'db_id': db_id,
            'db_path': db_path,
            'schema': schema,
            'gold_sql': item['SQL']
        })
    
    return examples

def extract_schema_from_sqlite(db_path):
    """Extract database schema from SQLite file"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table[0] for table in cursor.fetchall() 
                 if not table[0].startswith('sqlite_')]
        
        schema = {"tables": {}}
        
        # Get columns for each table
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table});")
            columns = [col[1] for col in cursor.fetchall()]
            schema["tables"][table] = columns
        
        conn.close()
        return schema
    except Exception as e:
        print(f"Error extracting schema from {db_path}: {e}")
        return {"tables": {}}

def execute_sql(sql, db_path):
    """Execute SQL query and return results"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
        conn.close()
        return True, results
    except Exception as e:
        return False, str(e)

def evaluate_example(example, pipeline):
    """Evaluate DIVA-SQL on a single example"""
    start_time = time.time()
    result = pipeline.generate_sql(example['question'], example['schema'])
    end_time = time.time()
    
    # Try to execute both generated and gold SQL
    generated_execution = execute_sql(result.final_sql, example['db_path']) if result.final_sql else (False, "No SQL generated")
    gold_execution = execute_sql(example['gold_sql'], example['db_path'])
    
    # Check if results match
    execution_match = False
    if generated_execution[0] and gold_execution[0]:
        # Compare result sets (ignoring order)
        generated_results = set(map(tuple, generated_execution[1]))
        gold_results = set(map(tuple, gold_execution[1]))
        execution_match = generated_results == gold_results
    
    return {
        'id': example['id'],
        'question': example['question'],
        'generated_sql': result.final_sql,
        'gold_sql': example['gold_sql'],
        'status': result.status.value if hasattr(result, 'status') else 'UNKNOWN',
        'confidence': result.confidence_score if hasattr(result, 'confidence_score') else 0.0,
        'execution_time': end_time - start_time,
        'syntactically_valid': generated_execution[0],
        'execution_match': execution_match,
        'node_count': len(result.semantic_dag.nodes) if result.semantic_dag else 0,
        'error_message': generated_execution[1] if not generated_execution[0] else None
    }

def main():
    args = parse_args()
    
    # Set up results directory
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # Initialize the client and pipeline
    client = create_gemini_client(model_name=args.model)
    pipeline = DIVASQLPipeline(client, model_name=args.model)
    
    # Load the appropriate benchmark data
    if args.benchmark == 'spider':
        examples = load_spider_data(args.split)
    else:  # bird
        examples = load_bird_data(args.split)
    
    print(f"Loaded {len(examples)} examples from {args.benchmark} {args.split} split")
    
    # Limit examples if specified
    if args.limit:
        examples = examples[:args.limit]
        print(f"Limited to first {args.limit} examples")
    
    # Evaluate each example
    results = []
    for example in tqdm(examples, desc="Evaluating examples"):
        try:
            result = evaluate_example(example, pipeline)
            results.append(result)
        except Exception as e:
            print(f"Error evaluating example {example['id']}: {e}")
            results.append({
                'id': example['id'],
                'question': example['question'],
                'generated_sql': None,
                'gold_sql': example['gold_sql'],
                'status': 'ERROR',
                'confidence': 0.0,
                'execution_time': 0.0,
                'syntactically_valid': False,
                'execution_match': False,
                'node_count': 0,
                'error_message': str(e)
            })
    
    # Calculate overall metrics
    total = len(results)
    valid_syntax = sum(1 for r in results if r['syntactically_valid'])
    execution_match = sum(1 for r in results if r['execution_match'])
    success_rate = sum(1 for r in results if r['status'] == 'SUCCESS') / total if total > 0 else 0
    avg_confidence = sum(r['confidence'] for r in results) / total if total > 0 else 0
    avg_time = sum(r['execution_time'] for r in results) / total if total > 0 else 0
    avg_nodes = sum(r['node_count'] for r in results if r['node_count'] > 0) / sum(1 for r in results if r['node_count'] > 0) if sum(1 for r in results if r['node_count'] > 0) > 0 else 0
    
    print(f"\nEvaluation Results on {args.benchmark} {args.split} (n={total}):")
    print(f"Syntactically Valid: {valid_syntax}/{total} ({valid_syntax/total:.2%})" if total > 0 else "No results")
    print(f"Execution Match: {execution_match}/{total} ({execution_match/total:.2%})" if total > 0 else "No results")
    print(f"Success Rate: {success_rate:.2%}")
    print(f"Average Confidence: {avg_confidence:.2f}")
    print(f"Average Execution Time: {avg_time:.2f}s")
    print(f"Average Semantic Nodes: {avg_nodes:.1f}")
    
    # Save results to CSV
    df = pd.DataFrame(results)
    df.to_csv(args.output, index=False)
    print(f"Results saved to {args.output}")
    
    # Save summary metrics
    summary = {
        'benchmark': args.benchmark,
        'split': args.split,
        'model': args.model,
        'total_examples': total,
        'syntactically_valid': valid_syntax,
        'execution_match': execution_match,
        'success_rate': success_rate,
        'avg_confidence': avg_confidence,
        'avg_time': avg_time,
        'avg_nodes': avg_nodes,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    summary_path = os.path.join(os.path.dirname(args.output), 'benchmark_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"Summary saved to {summary_path}")

if __name__ == '__main__':
    main()
