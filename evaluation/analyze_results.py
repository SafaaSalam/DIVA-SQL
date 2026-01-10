"""
Analyze benchmark results for DIVA-SQL

This script analyzes the results of benchmark evaluations and generates visualizations.
"""

import os
import json
import argparse
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(description='Analyze benchmark results')
    parser.add_argument('--results', type=str, required=True, 
                        help='Results CSV file')
    parser.add_argument('--output-dir', type=str, default=None,
                        help='Output directory for visualizations (defaults to same directory as results)')
    return parser.parse_args()

def analyze_results(results_file, output_dir=None):
    """Analyze benchmark results and generate visualizations"""
    try:
        import pandas as pd
        import matplotlib.pyplot as plt
        import seaborn as sns
    except ImportError:
        print("Error: This script requires pandas, matplotlib, and seaborn.")
        print("Please install them with: pip install pandas matplotlib seaborn")
        return
    
    # Load results
    df = pd.read_csv(results_file)
    
    # Set up output directory
    if output_dir is None:
        output_dir = Path(results_file).parent / 'visualizations'
    else:
        output_dir = Path(output_dir)
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Basic statistics
    total = len(df)
    if total == 0:
        print("No results found in the file.")
        return
    
    valid_syntax = df['syntactically_valid'].sum()
    execution_match = df['execution_match'].sum()
    success_rate = df[df['status'] == 'SUCCESS'].shape[0] / total
    
    print(f"Analysis of {results_file}")
    print(f"Total examples: {total}")
    print(f"Syntactically Valid: {valid_syntax} ({valid_syntax/total:.2%})")
    print(f"Execution Match (Correct): {execution_match} ({execution_match/total:.2%})")
    print(f"Success Rate: {success_rate:.2%}")
    
    # 1. Plot status distribution
    plt.figure(figsize=(10, 6))
    status_counts = df['status'].value_counts()
    status_counts.plot(kind='bar', color=['green', 'orange', 'red'])
    plt.title('Query Status Distribution')
    plt.ylabel('Count')
    plt.tight_layout()
    status_plot_path = output_dir / 'status_distribution.png'
    plt.savefig(status_plot_path)
    print(f"Saved status distribution plot to {status_plot_path}")
    
    # 2. Plot confidence distribution
    if 'confidence' in df.columns and df['confidence'].notna().any():
        plt.figure(figsize=(10, 6))
        sns.histplot(df['confidence'].dropna(), bins=10, kde=True)
        plt.axvline(x=df['confidence'].mean(), color='red', linestyle='--', 
                    label=f'Mean: {df["confidence"].mean():.2f}')
        plt.title('Confidence Score Distribution')
        plt.xlabel('Confidence Score')
        plt.ylabel('Frequency')
        plt.legend()
        plt.tight_layout()
        confidence_plot_path = output_dir / 'confidence_distribution.png'
        plt.savefig(confidence_plot_path)
        print(f"Saved confidence distribution plot to {confidence_plot_path}")
    
    # 3. Confidence vs. correctness
    if 'confidence' in df.columns and df['confidence'].notna().any():
        plt.figure(figsize=(10, 6))
        sns.boxplot(x='execution_match', y='confidence', data=df)
        plt.title('Confidence Score vs. Execution Match')
        plt.xlabel('Execution Match (Correct SQL)')
        plt.ylabel('Confidence Score')
        plt.tight_layout()
        confidence_vs_correctness_path = output_dir / 'confidence_vs_correctness.png'
        plt.savefig(confidence_vs_correctness_path)
        print(f"Saved confidence vs correctness plot to {confidence_vs_correctness_path}")
    
    # 4. Node count distribution
    if 'node_count' in df.columns and (df['node_count'] > 0).any():
        plt.figure(figsize=(10, 6))
        sns.histplot(df[df['node_count'] > 0]['node_count'], bins=10, kde=False, discrete=True)
        plt.title('Semantic Node Count Distribution')
        plt.xlabel('Number of Nodes')
        plt.ylabel('Frequency')
        plt.tight_layout()
        node_dist_path = output_dir / 'node_distribution.png'
        plt.savefig(node_dist_path)
        print(f"Saved node distribution plot to {node_dist_path}")
    
    # 5. Execution time vs. complexity (node count)
    if 'node_count' in df.columns and 'execution_time' in df.columns and (df['node_count'] > 0).any():
        plt.figure(figsize=(10, 6))
        sns.scatterplot(x='node_count', y='execution_time', hue='execution_match', data=df[df['node_count'] > 0])
        plt.title('Execution Time vs. Complexity')
        plt.xlabel('Number of Semantic Nodes')
        plt.ylabel('Execution Time (s)')
        plt.tight_layout()
        time_vs_complexity_path = output_dir / 'time_vs_complexity.png'
        plt.savefig(time_vs_complexity_path)
        print(f"Saved time vs complexity plot to {time_vs_complexity_path}")
    
    # 6. Calculate accuracy by node count
    if 'node_count' in df.columns and (df['node_count'] > 0).any():
        node_accuracy = df.groupby('node_count')['execution_match'].mean().reset_index()
        plt.figure(figsize=(10, 6))
        sns.barplot(x='node_count', y='execution_match', data=node_accuracy)
        plt.title('Accuracy by Complexity')
        plt.xlabel('Number of Semantic Nodes')
        plt.ylabel('Accuracy (Execution Match)')
        plt.tight_layout()
        accuracy_by_complexity_path = output_dir / 'accuracy_by_complexity.png'
        plt.savefig(accuracy_by_complexity_path)
        print(f"Saved accuracy by complexity plot to {accuracy_by_complexity_path}")
    
    # Generate summary JSON
    summary = {
        'total_examples': total,
        'syntactically_valid': int(valid_syntax),
        'syntactically_valid_percent': float(valid_syntax/total),
        'execution_match': int(execution_match),
        'execution_match_percent': float(execution_match/total),
        'success_rate': float(success_rate),
        'avg_confidence': float(df['confidence'].mean()) if 'confidence' in df.columns else None,
        'avg_execution_time': float(df['execution_time'].mean()) if 'execution_time' in df.columns else None,
        'avg_node_count': float(df[df['node_count'] > 0]['node_count'].mean()) if 'node_count' in df.columns and (df['node_count'] > 0).any() else None,
        'visualization_files': [f.name for f in output_dir.glob('*.png')]
    }
    
    summary_path = output_dir / 'summary.json'
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"Analysis summary saved to {summary_path}")
    return summary

def main():
    args = parse_args()
    analyze_results(args.results, args.output_dir)

if __name__ == '__main__':
    main()
