#!/usr/bin/env python3
"""
Generate paper results for DIVA-SQL benchmark evaluation

This script runs a comprehensive benchmark evaluation on the synthetic dataset
and generates results suitable for inclusion in an academic paper.
"""

import os
import sys
import json
import time
import random
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime

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

# Constants
RESULTS_DIR = Path(__file__).parent.parent / "results"
BENCHMARKS_DIR = Path(__file__).parent.parent / "data" / "benchmarks"
SYNTHETIC_DIR = BENCHMARKS_DIR / "synthetic"
DELAY = 60  # Delay between API calls to avoid rate limits

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

def load_synthetic_data():
    """Load the synthetic dataset"""
    if not SYNTHETIC_DIR.exists():
        print("Creating synthetic dataset...")
        # Import and run the create_synthetic_dataset module
        sys.path.append(str(Path(__file__).parent))
        from create_synthetic_dataset import main as create_dataset
        create_dataset()
    
    # Load the dataset
    with open(SYNTHETIC_DIR / "dev.json", "r") as f:
        data = json.load(f)
    
    # Load table schema
    with open(SYNTHETIC_DIR / "tables.json", "r") as f:
        tables_data = json.load(f)
    
    schema = {
        "tables": {
            table_name: tables_data[table_name]["column_names"] 
            for table_name in tables_data
        }
    }
    
    # Format examples
    examples = []
    for i, item in enumerate(data):
        examples.append({
            "id": f"synthetic-{i+1}",
            "db_id": item["db_id"],
            "question": item["question"],
            "query": item["query"],
            "gold_sql": item["query"],
            "db_path": str(SYNTHETIC_DIR / "database" / f"{item['db_id']}.sqlite"),
            "schema": schema
        })
    
    return examples

def evaluate_example(example, pipeline):
    """Evaluate a single example using DIVA-SQL"""
    start_time = time.time()
    result = pipeline.generate_sql(example["question"], example["schema"])
    elapsed_time = time.time() - start_time
    
    # Execute generated SQL if available
    execution_match = False
    error_message = None
    
    if result.final_sql:
        gold_results, gold_error = execute_query(example["db_path"], example["gold_sql"])
        
        if gold_error:
            error_message = f"Error executing gold SQL: {gold_error}"
        else:
            results, error = execute_query(example["db_path"], result.final_sql)
            
            if error:
                error_message = f"Error executing generated SQL: {error}"
            else:
                # Compare results
                gold_set = set(map(tuple, gold_results))
                generated_set = set(map(tuple, results))
                execution_match = gold_set == generated_set
    
    return {
        "id": example["id"],
        "db_id": example["db_id"],
        "question": example["question"],
        "gold_sql": example["gold_sql"],
        "generated_sql": result.final_sql,
        "status": result.status.value,
        "confidence_score": result.confidence_score,
        "execution_match": execution_match,
        "elapsed_time": elapsed_time,
        "node_count": len(result.semantic_dag.nodes) if result.semantic_dag else 0,
        "error_message": error_message or result.error_message,
        "decomposition": [
            {
                "id": node_id,
                "description": result.semantic_dag.nodes[node_id].description,
                "sql": result.semantic_dag.nodes[node_id].sql
            }
            for node_id in result.semantic_dag.get_execution_order()
        ] if result.semantic_dag else []
    }

def generate_paper_figures(results, output_dir):
    """Generate figures for paper publication"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a DataFrame from results
    df = pd.DataFrame(results)
    
    # 1. Execution Match Accuracy
    accuracy = df["execution_match"].mean()
    plt.figure(figsize=(8, 5))
    plt.bar(["DIVA-SQL"], [accuracy], color="#4285F4", width=0.5)
    plt.ylabel("Execution Match Accuracy")
    plt.ylim(0, 1)
    plt.title("DIVA-SQL Execution Match Accuracy")
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "execution_match.png"), dpi=300)
    plt.close()
    
    # 2. Query Execution Time
    plt.figure(figsize=(10, 6))
    sns.histplot(data=df, x="elapsed_time", bins=10, kde=True)
    plt.xlabel("Execution Time (seconds)")
    plt.ylabel("Count")
    plt.title("DIVA-SQL Query Generation Time Distribution")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "execution_time.png"), dpi=300)
    plt.close()
    
    # 3. Confidence Score vs. Accuracy
    plt.figure(figsize=(10, 6))
    df_sorted = df.sort_values(by="confidence_score")
    plt.scatter(df_sorted["confidence_score"], df_sorted["execution_match"].astype(int), 
               alpha=0.7, color="#4285F4", s=100)
    plt.xlabel("Confidence Score")
    plt.ylabel("Execution Match (0=Incorrect, 1=Correct)")
    plt.title("DIVA-SQL Confidence Score vs. Execution Match")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "confidence_accuracy.png"), dpi=300)
    plt.close()
    
    # 4. Decomposition Node Count Distribution
    plt.figure(figsize=(10, 6))
    sns.countplot(data=df, x="node_count", palette="viridis")
    plt.xlabel("Number of Decomposition Nodes")
    plt.ylabel("Count")
    plt.title("DIVA-SQL Semantic Decomposition Node Count")
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "node_count.png"), dpi=300)
    plt.close()
    
    # 5. Summary table for paper (LaTeX)
    summary = {
        "Total Examples": len(df),
        "Execution Match Accuracy": f"{accuracy:.2%}",
        "Avg. Generation Time": f"{df['elapsed_time'].mean():.2f}s",
        "Avg. Decomposition Nodes": f"{df['node_count'].mean():.1f}",
        "Min Confidence": f"{df['confidence_score'].min():.2f}",
        "Max Confidence": f"{df['confidence_score'].max():.2f}",
        "Avg. Confidence": f"{df['confidence_score'].mean():.2f}",
    }
    
    # Generate LaTeX table
    latex_table = "\\begin{table}[h]\n\\centering\n\\begin{tabular}{l|r}\n\\hline\n"
    latex_table += "\\textbf{Metric} & \\textbf{Value} \\\\\n\\hline\n"
    
    for metric, value in summary.items():
        latex_table += f"{metric} & {value} \\\\\n"
    
    latex_table += "\\hline\n\\end{tabular}\n"
    latex_table += "\\caption{DIVA-SQL Benchmark Evaluation Results}\n"
    latex_table += "\\label{tab:diva_results}\n\\end{table}"
    
    with open(os.path.join(output_dir, "results_table.tex"), "w") as f:
        f.write(latex_table)
    
    # Generate JSON summary for easy import
    with open(os.path.join(output_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    
    # Generate CSV of full results
    df.to_csv(os.path.join(output_dir, "full_results.csv"), index=False)
    
    return summary

def main():
    print("📊 DIVA-SQL Benchmark Evaluation for Paper Results")
    print("=" * 60)
    
    # Check if API key is set
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY environment variable not set")
        print("Please set your API key with: export GOOGLE_API_KEY='your_api_key'")
        sys.exit(1)
    
    print("✓ Google API key found")
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = RESULTS_DIR / f"paper_results_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    
    # Load data
    examples = load_synthetic_data()
    print(f"✓ Loaded {len(examples)} examples from synthetic dataset")
    
    # Create client and pipeline
    llm_client = GeminiLLMClient(api_key=api_key, model_name="gemini-2.0-flash")
    pipeline = DIVASQLPipeline(llm_client)
    print("✓ Initialized DIVA-SQL pipeline")
    
    # Run evaluation
    results = []
    print("\nRunning benchmark evaluation...")
    
    for i, example in enumerate(examples):
        print(f"\n[{i+1}/{len(examples)}] Processing: {example['question']}")
        
        try:
            result = evaluate_example(example, pipeline)
            results.append(result)
            
            print(f"  Status: {result['status']}")
            print(f"  Execution Match: {result['execution_match']}")
            print(f"  Confidence: {result['confidence_score']:.2f}")
            print(f"  Time: {result['elapsed_time']:.2f}s")
            
            # Add delay to avoid rate limiting
            if i < len(examples) - 1:
                print(f"\nWaiting {DELAY} seconds to avoid API rate limits...")
                time.sleep(DELAY)
        except Exception as e:
            print(f"❌ Error processing example: {e}")
            import traceback
            traceback.print_exc()
    
    # Generate paper figures and tables
    print("\n📈 Generating figures and tables for paper...")
    summary = generate_paper_figures(results, output_dir)
    
    print("\n📝 Results Summary:")
    for metric, value in summary.items():
        print(f"  • {metric}: {value}")
    
    print(f"\n✅ Evaluation complete! Results saved to: {output_dir}")
    print(f"   Include the LaTeX table in your paper using: \\input{{{output_dir}/results_table.tex}}")
    print(f"   Figures are available in: {output_dir}")

if __name__ == "__main__":
    main()
