"""
Rate-Limited Benchmark Evaluation for DIVA-SQL

This script evaluates DIVA-SQL on established benchmarks with rate limiting for API calls.
"""

import os
import json
import time
import argparse
import random
from tqdm import tqdm
from pathlib import Path

# Add project root to path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from evaluation.benchmark_eval import load_spider_data, load_bird_data, evaluate_example, execute_sql
from src.utils.gemini_client import create_gemini_client
from src.core.pipeline import DIVASQLPipeline

def parse_args():
    parser = argparse.ArgumentParser(description='Rate-limited evaluation of DIVA-SQL')
    parser.add_argument('--benchmark', type=str, choices=['synthetic', 'spider', 'bird'], required=True,
                        help='Benchmark dataset to evaluate on')
    parser.add_argument('--split', type=str, default='dev', choices=['dev', 'test'],
                        help='Dataset split to use')
    parser.add_argument('--sample', type=int, default=10,
                        help='Number of examples to randomly sample')
    parser.add_argument('--delay', type=float, default=3.0,
                        help='Delay between API calls in seconds')
    parser.add_argument('--output', type=str, default='results/sampled_results.csv',
                        help='Output file for results')
    parser.add_argument('--model', type=str, default='gemini-2.0-flash',
                        help='LLM model to use')
    return parser.parse_args()

def main():
    args = parse_args()

    # Set up results directory
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    # Initialize the client and pipeline
    client = create_gemini_client(model_name=args.model)
    pipeline = DIVASQLPipeline(client, model_name=args.model)

    # Load the appropriate benchmark data
    try:
        if args.benchmark == 'synthetic':
            # Load synthetic dataset
            benchmark_dir = Path(__file__).parent.parent / "data" / "benchmarks"
            synthetic_dir = benchmark_dir / "synthetic"
            
            if not synthetic_dir.exists():
                print("Error: Synthetic dataset not found")
                print("Please run evaluation/create_synthetic_dataset.py first")
                return
            
            # Load examples
            with open(synthetic_dir / "dev.json", 'r') as f:
                data = json.load(f)
            
            # Load table schema
            with open(synthetic_dir / "tables.json", 'r') as f:
                tables_data = json.load(f)
                
            examples = []
            for i, item in enumerate(data):
                # Extract schema information
                schema = {
                    "tables": {
                        table_name: tables_data[table_name]["column_names"] 
                        for table_name in tables_data
                    }
                }
                
                examples.append({
                    "id": f"synthetic-{i+1}",
                    "db_id": item["db_id"],
                    "question": item["question"],
                    "query": item["query"],
                    "db_path": str(synthetic_dir / "database" / f"{item['db_id']}.sqlite"),
                    "schema": schema
                })
            
            print(f"Loaded {len(examples)} examples from synthetic dataset")
        elif args.benchmark == 'spider':
            examples = load_spider_data(args.split)
        else:  # bird
            examples = load_bird_data(args.split)
        
        print(f"Loaded {len(examples)} examples from {args.benchmark} {args.split} split")
    except Exception as e:
        print(f"Error loading benchmark data: {e}")
        print(f"Make sure you have downloaded the {args.benchmark} benchmark to data/benchmarks/")
        return
    
    # Randomly sample examples
    if args.sample < len(examples):
        sampled_examples = random.sample(examples, args.sample)
    else:
        sampled_examples = examples
    
    print(f"Randomly sampled {len(sampled_examples)} examples for evaluation")
    
    # Evaluate each example with delay
    results = []
    for i, example in enumerate(tqdm(sampled_examples, desc="Evaluating examples")):
        try:
            print(f"\n[{i+1}/{len(sampled_examples)}] Processing: {example['question']}")
            result = evaluate_example(example, pipeline)
            results.append(result)
            print(f"  Status: {result['status']}, Execution Match: {result['execution_match']}")
            # Add delay to avoid rate limiting
            if i < len(sampled_examples) - 1:  # No need to delay after the last example
                print(f"  Waiting {args.delay} seconds to avoid rate limiting...")
                time.sleep(args.delay)
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
            # Still add delay even on error
            if i < len(sampled_examples) - 1:
                time.sleep(args.delay)
    
    # Calculate overall metrics
    total = len(results)
    if total > 0:
        valid_syntax = sum(1 for r in results if r['syntactically_valid'])
        execution_match = sum(1 for r in results if r['execution_match'])
        success_rate = sum(1 for r in results if r['status'] == 'SUCCESS') / total
        
        print(f"\nEvaluation Results on {args.benchmark} {args.split} (sampled n={total}):")
        print(f"Syntactically Valid: {valid_syntax}/{total} ({valid_syntax/total:.2%})")
        print(f"Execution Match: {execution_match}/{total} ({execution_match/total:.2%})")
        print(f"Success Rate: {success_rate:.2%}")
    else:
        print("\nNo results collected.")
    
    # Save results to CSV
    try:
        import pandas as pd
        df = pd.DataFrame(results)
        df.to_csv(args.output, index=False)
        print(f"Results saved to {args.output}")

        # Save summary metrics
        if total > 0:
            summary = {
                'benchmark': args.benchmark,
                'split': args.split,
                'model': args.model,
                'total_examples': total,
                'syntactically_valid': valid_syntax,
                'execution_match': execution_match,
                'success_rate': success_rate,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            summary_path = os.path.join(os.path.dirname(args.output), f'{args.benchmark}_summary.json')
            with open(summary_path, 'w') as f:
                json.dump(summary, f, indent=2)
            
            print(f"Summary saved to {summary_path}")
    except ImportError:
        print("Pandas not installed. Saving results as JSON instead.")
        with open(args.output.replace('.csv', '.json'), 'w') as f:
            json.dump(results, f, indent=2)

if __name__ == '__main__':
    main()
