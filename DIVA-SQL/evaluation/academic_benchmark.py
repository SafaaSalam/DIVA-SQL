#!/usr/bin/env python3
"""
Academic benchmark evaluation for DIVA-SQL with rate limiting

This script runs a benchmark evaluation for academic research purposes
with proper rate limiting to avoid exceeding API quotas.
"""

import os
import json
import time
import argparse
import sqlite3
import pandas as pd
from tqdm import tqdm
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

# Add project root to path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.core.pipeline import DIVASQLPipeline, PipelineStatus
from src.utils.gemini_client import create_gemini_client

# Rate limiting parameters
REQUESTS_PER_MINUTE = 20  # Conservative limit to avoid quota issues
REQUEST_INTERVAL = 60 / REQUESTS_PER_MINUTE  # Seconds between requests

class RateLimitedBenchmark:
    def __init__(self, benchmark='synthetic', split='dev', model='gemini-2.0-flash', 
                 limit=None, output='results/academic_benchmark/results.csv'):
        self.benchmark = benchmark
        self.split = split
        self.model = model
        self.limit = limit
        self.output_path = output
        
        # Create output directory
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        
        # Initialize LLM client
        self.client = create_gemini_client(model_name=self.model)
        self.pipeline = DIVASQLPipeline(self.client, model_name=self.model)
        
        # Load data
        self.data = self.load_data()
        
    def load_data(self):
        """Load the benchmark data"""
        if self.benchmark == 'synthetic':
            data_path = f'data/benchmarks/synthetic/{self.split}.json'
        elif self.benchmark == 'spider':
            data_path = f'data/benchmarks/spider/{self.split}.json'
        elif self.benchmark == 'bird':
            data_path = f'data/benchmarks/bird/{self.split}.json'
        else:
            raise ValueError(f"Unsupported benchmark: {self.benchmark}")
            
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Dataset not found: {data_path}. "
                                    f"Please run download_datasets.py first.")
        
        with open(data_path, 'r') as f:
            data = json.load(f)
            
        # Limit the number of examples if specified
        if self.limit:
            data = data[:self.limit]
            
        print(f"Loaded {len(data)} examples from {data_path}")
        return data
        
    def run_evaluation(self):
        """Run the benchmark evaluation with rate limiting"""
        results = []
        
        print(f"Running evaluation on {len(self.data)} examples...")
        for i, example in enumerate(tqdm(self.data)):
            # Extract query and schema
            query_text = example['question']
            schema = example['schema']
            gold_sql = example.get('query', '')  # Gold SQL query if available
            
            # Apply rate limiting
            if i > 0:
                time.sleep(REQUEST_INTERVAL)
                
            # Run DIVA-SQL on the query
            start_time = time.time()
            try:
                result = self.pipeline.run(query_text, schema)
                elapsed_time = time.time() - start_time
                
                # Process the result
                result_data = {
                    'id': example.get('id', i),
                    'question': query_text,
                    'gold_sql': gold_sql,
                    'generated_sql': result.sql if result.status == PipelineStatus.SUCCESS else '',
                    'status': result.status.name,
                    'time': elapsed_time,
                    'errors': str(result.errors) if result.errors else '',
                    'decomposition': json.dumps(result.decomposition) if result.decomposition else ''
                }
                results.append(result_data)
                
            except Exception as e:
                elapsed_time = time.time() - start_time
                # Record the error
                results.append({
                    'id': example.get('id', i),
                    'question': query_text,
                    'gold_sql': gold_sql,
                    'generated_sql': '',
                    'status': 'ERROR',
                    'time': elapsed_time,
                    'errors': str(e),
                    'decomposition': ''
                })
                
        # Save results
        df = pd.DataFrame(results)
        df.to_csv(self.output_path, index=False)
        print(f"Results saved to {self.output_path}")
        
        return df
        
    def analyze_results(self, results_df=None):
        """Analyze the benchmark results"""
        if results_df is None:
            results_df = pd.read_csv(self.output_path)
            
        # Calculate success rate
        total = len(results_df)
        successful = len(results_df[results_df['status'] == 'SUCCESS'])
        success_rate = successful / total * 100
        
        print(f"Success rate: {success_rate:.2f}% ({successful}/{total})")
        
        # Analyze error types
        error_counts = results_df[results_df['status'] != 'SUCCESS']['status'].value_counts()
        print("\nError distribution:")
        for error_type, count in error_counts.items():
            print(f"  {error_type}: {count} ({count/total*100:.2f}%)")
            
        # Visualize results
        plt.figure(figsize=(10, 6))
        
        # Success rate pie chart
        plt.subplot(1, 2, 1)
        plt.pie([successful, total-successful], 
                labels=['Success', 'Failure'], 
                autopct='%1.1f%%', 
                colors=['#4CAF50', '#F44336'])
        plt.title('DIVA-SQL Success Rate')
        
        # Error type distribution
        plt.subplot(1, 2, 2)
        error_counts.plot(kind='bar', color='#FF9800')
        plt.title('Error Distribution')
        plt.ylabel('Count')
        plt.tight_layout()
        
        # Save the visualization
        viz_path = self.output_path.replace('.csv', '_viz.png')
        plt.savefig(viz_path)
        print(f"Visualization saved to {viz_path}")
        
        return success_rate, error_counts

def main():
    parser = argparse.ArgumentParser(description='Academic benchmark evaluation for DIVA-SQL')
    parser.add_argument('--benchmark', type=str, choices=['synthetic', 'spider', 'bird'], 
                        default='synthetic', help='Benchmark dataset to evaluate on')
    parser.add_argument('--split', type=str, default='dev', choices=['dev', 'test'],
                        help='Dataset split to use')
    parser.add_argument('--model', type=str, default='gemini-2.0-flash',
                        help='LLM model to use')
    parser.add_argument('--limit', type=int, default=None,
                        help='Limit evaluation to N examples')
    parser.add_argument('--output', type=str, default='results/academic_benchmark/results.csv',
                        help='Output file for results')
    parser.add_argument('--analyze-only', action='store_true',
                        help='Only analyze existing results without running evaluation')
    args = parser.parse_args()
    
    benchmark = RateLimitedBenchmark(
        benchmark=args.benchmark,
        split=args.split,
        model=args.model,
        limit=args.limit,
        output=args.output
    )
    
    if not args.analyze_only:
        results_df = benchmark.run_evaluation()
        benchmark.analyze_results(results_df)
    else:
        benchmark.analyze_results()

if __name__ == "__main__":
    main()