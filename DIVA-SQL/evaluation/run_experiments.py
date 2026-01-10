"""
DIVA-SQL Research Evaluation Script

This script implements the evaluation methodology described in the research proposal,
including comparisons with baselines and human study setup.
"""

import argparse
import json
import time
import sqlite3
from pathlib import Path
from typing import Dict, List, Any
import sys

# Add src to path
sys.path.append(str(Path(__file__).parents[1] / "src"))

from evaluation.framework import (
    BenchmarkEvaluator, DIVASQLSystem, ZeroShotBaselineSystem,
    BenchmarkResults, EvaluationResult
)


class ResearchEvaluator:
    """
    Main class for conducting research evaluation experiments
    """
    
    def __init__(self, output_dir: str = "results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.timestamp = int(time.time())
    
    def run_rq1_evaluation(self, llm_client, benchmark_data: List[Dict], 
                          database_schema: Dict, database_path: str) -> Dict[str, BenchmarkResults]:
        """
        Research Question 1: Accuracy Evaluation
        Does DIVA-SQL achieve higher execution accuracy on complex queries?
        """
        print("=== RQ1: Accuracy Evaluation ===")
        
        # Initialize systems
        systems = {
            "DIVA-SQL": DIVASQLSystem(llm_client, "gpt-4"),
            "Zero-Shot-GPT4": ZeroShotBaselineSystem(llm_client, "gpt-4"),
            # Additional baselines would be added here:
            # "DIN-SQL": DINSQLSystem(llm_client),
            # "MAC-SQL": MACSQLSystem(llm_client),
        }
        
        # Run evaluation
        evaluator = BenchmarkEvaluator(database_path)
        results = {}
        
        for system_name, system in systems.items():
            print(f"\nEvaluating {system_name}...")
            system_results = evaluator.evaluate_system(system, benchmark_data, database_schema)
            results[system_name] = system_results
            
            # Print interim results
            print(f"  EX: {system_results.execution_accuracy:.3f}")
            print(f"  VES: {system_results.avg_valid_efficiency_score:.3f}")
            print(f"  Avg Time: {system_results.avg_execution_time:.2f}s")
        
        # Save detailed results
        self._save_rq1_results(results)
        
        return results
    
    def run_rq2_setup(self, failed_queries: List[Dict]) -> Dict[str, Any]:
        """
        Research Question 2: Interpretability Setup
        Prepare data for human subject study on interpretability
        """
        print("=== RQ2: Human Study Setup ===")
        
        # Select challenging queries where baselines failed
        study_queries = []
        
        for query_data in failed_queries[:20]:  # Select top 20 challenging queries
            study_item = {
                "query_id": query_data["query_id"],
                "natural_language": query_data["question"],
                "gold_sql": query_data["sql"],
                "baseline_sql": query_data.get("predicted_sql"),
                "baseline_error": query_data.get("error_message"),
                "diva_dag": query_data.get("semantic_dag"),
                "diva_verification": query_data.get("verification_log")
            }
            study_queries.append(study_item)
        
        # Create study configuration
        study_config = {
            "study_type": "within_subjects",
            "conditions": ["baseline", "diva_sql"],
            "queries": study_queries,
            "metrics": [
                "task_success_rate",
                "time_to_completion", 
                "confidence_rating",
                "understanding_rating"
            ],
            "instructions": {
                "baseline": "Fix the incorrect SQL query using standard SQL editing tools",
                "diva_sql": "Use the DIVA-SQL interface showing semantic steps and verification results"
            }
        }
        
        # Save study configuration
        study_file = self.output_dir / f"human_study_config_{self.timestamp}.json"
        with open(study_file, 'w') as f:
            json.dump(study_config, f, indent=2)
        
        print(f"Human study configuration saved to: {study_file}")
        
        return study_config
    
    def run_rq3_analysis(self, diva_results: BenchmarkResults) -> Dict[str, Any]:
        """
        Research Question 3: Error Prevention Analysis
        Analyze the effectiveness of in-line verification
        """
        print("=== RQ3: Error Prevention Analysis ===")
        
        verification_stats = {
            "total_nodes": 0,
            "nodes_verified": 0,
            "nodes_failed": 0,
            "correction_attempts": 0,
            "successful_corrections": 0,
            "error_types_caught": {},
            "verification_time": 0.0
        }
        
        # Analyze verification logs from DIVA results
        for result in diva_results.results_by_query:
            if result.metadata and "verification_log" in result.metadata:
                verification_log = result.metadata["verification_log"]
                
                for log_entry in verification_log:
                    verification_stats["total_nodes"] += 1
                    
                    status = log_entry.get("verification_status")
                    if status == "PASS":
                        verification_stats["nodes_verified"] += 1
                    elif status == "FAIL":
                        verification_stats["nodes_failed"] += 1
                    
                    # Count error types
                    issues = log_entry.get("issues", [])
                    for issue in issues:
                        error_type = issue.get("type", "unknown")
                        verification_stats["error_types_caught"][error_type] = \
                            verification_stats["error_types_caught"].get(error_type, 0) + 1
        
        # Calculate metrics
        if verification_stats["total_nodes"] > 0:
            verification_stats["verification_success_rate"] = \
                verification_stats["nodes_verified"] / verification_stats["total_nodes"]
        
        verification_stats["error_prevention_effectiveness"] = \
            len(verification_stats["error_types_caught"]) / max(verification_stats["total_nodes"], 1)
        
        # Save analysis
        analysis_file = self.output_dir / f"rq3_error_prevention_analysis_{self.timestamp}.json"
        with open(analysis_file, 'w') as f:
            json.dump(verification_stats, f, indent=2)
        
        print(f"Error prevention analysis saved to: {analysis_file}")
        print(f"Verification success rate: {verification_stats.get('verification_success_rate', 0):.3f}")
        print(f"Error types caught: {len(verification_stats['error_types_caught'])}")
        
        return verification_stats
    
    def generate_research_report(self, rq1_results: Dict[str, BenchmarkResults],
                               rq2_config: Dict[str, Any],
                               rq3_analysis: Dict[str, Any]) -> str:
        """
        Generate comprehensive research report
        """
        print("=== Generating Research Report ===")
        
        report_lines = []
        report_lines.append("DIVA-SQL Research Evaluation Report")
        report_lines.append("=" * 50)
        report_lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # RQ1 Results
        report_lines.append("\n## Research Question 1: Accuracy Comparison")
        report_lines.append("-" * 40)
        
        report_lines.append(f"{'System':<20} {'EX':<8} {'VES':<8} {'Time(s)':<10}")
        report_lines.append("-" * 50)
        
        for system_name, results in rq1_results.items():
            report_lines.append(
                f"{system_name:<20} "
                f"{results.execution_accuracy:<8.3f} "
                f"{results.avg_valid_efficiency_score:<8.3f} "
                f"{results.avg_execution_time:<10.2f}"
            )
        
        # Statistical significance (placeholder)
        report_lines.append("\n### Statistical Analysis:")
        report_lines.append("- McNemar's test p-value: [To be calculated]")
        report_lines.append("- Effect size: [To be calculated]")
        
        # RQ2 Setup
        report_lines.append("\n## Research Question 2: Human Study Configuration")
        report_lines.append("-" * 40)
        report_lines.append(f"Total study queries: {len(rq2_config['queries'])}")
        report_lines.append(f"Study design: {rq2_config['study_type']}")
        report_lines.append(f"Conditions: {', '.join(rq2_config['conditions'])}")
        
        # RQ3 Analysis
        report_lines.append("\n## Research Question 3: Error Prevention Analysis")
        report_lines.append("-" * 40)
        report_lines.append(f"Total semantic nodes processed: {rq3_analysis['total_nodes']}")
        report_lines.append(f"Verification success rate: {rq3_analysis.get('verification_success_rate', 0):.3f}")
        report_lines.append(f"Error types detected: {len(rq3_analysis['error_types_caught'])}")
        
        report_lines.append("\n### Error Types Caught:")
        for error_type, count in rq3_analysis['error_types_caught'].items():
            report_lines.append(f"  - {error_type}: {count}")
        
        # Conclusions
        report_lines.append("\n## Key Findings")
        report_lines.append("-" * 40)
        
        # Compare DIVA-SQL vs best baseline
        if "DIVA-SQL" in rq1_results:
            diva_ex = rq1_results["DIVA-SQL"].execution_accuracy
            baseline_systems = {k: v for k, v in rq1_results.items() if k != "DIVA-SQL"}
            
            if baseline_systems:
                best_baseline = max(baseline_systems.values(), key=lambda x: x.execution_accuracy)
                best_baseline_name = next(k for k, v in baseline_systems.items() if v == best_baseline)
                
                improvement = diva_ex - best_baseline.execution_accuracy
                report_lines.append(f"1. DIVA-SQL achieved {diva_ex:.3f} EX vs {best_baseline.execution_accuracy:.3f} for {best_baseline_name}")
                report_lines.append(f"   Improvement: {improvement:+.3f} ({improvement/best_baseline.execution_accuracy*100:+.1f}%)")
        
        report_lines.append(f"2. Verification system caught {len(rq3_analysis['error_types_caught'])} different error types")
        report_lines.append(f"3. Human study configured with {len(rq2_config['queries'])} challenging queries")
        
        # Future work
        report_lines.append("\n## Limitations and Future Work")
        report_lines.append("-" * 40)
        report_lines.append("1. Evaluation limited to [benchmark size] queries")
        report_lines.append("2. Human study results pending data collection")
        report_lines.append("3. Comparison with additional baselines recommended")
        report_lines.append("4. Cross-domain evaluation needed")
        
        report_content = "\n".join(report_lines)
        
        # Save report
        report_file = self.output_dir / f"research_report_{self.timestamp}.md"
        with open(report_file, 'w') as f:
            f.write(report_content)
        
        print(f"Research report saved to: {report_file}")
        
        return report_content
    
    def _save_rq1_results(self, results: Dict[str, BenchmarkResults]):
        """Save RQ1 detailed results"""
        rq1_data = {}
        
        for system_name, benchmark_results in results.items():
            rq1_data[system_name] = {
                "execution_accuracy": benchmark_results.execution_accuracy,
                "avg_valid_efficiency_score": benchmark_results.avg_valid_efficiency_score,
                "avg_execution_time": benchmark_results.avg_execution_time,
                "total_queries": benchmark_results.total_queries,
                "error_analysis": benchmark_results.error_analysis,
                "detailed_results": [
                    {
                        "query_id": r.query_id,
                        "execution_accuracy": r.execution_accuracy,
                        "valid_efficiency_score": r.valid_efficiency_score,
                        "execution_time": r.execution_time,
                        "error_message": r.error_message
                    }
                    for r in benchmark_results.results_by_query
                ]
            }
        
        rq1_file = self.output_dir / f"rq1_accuracy_results_{self.timestamp}.json"
        with open(rq1_file, 'w') as f:
            json.dump(rq1_data, f, indent=2)
        
        print(f"RQ1 detailed results saved to: {rq1_file}")


def create_sample_benchmark():
    """Create sample benchmark data for testing"""
    return [
        {
            "query_id": "sample_001",
            "question": "What are the names of departments with more than 10 employees hired after 2022?",
            "sql": "SELECT T2.DeptName FROM Employees AS T1 JOIN Departments AS T2 ON T1.DeptID = T2.DeptID WHERE T1.HireDate > '2022-01-01' GROUP BY T2.DeptID HAVING COUNT(*) > 10",
            "difficulty": "HARD"
        },
        {
            "query_id": "sample_002",
            "question": "How many employees work in each department?",
            "sql": "SELECT T2.DeptName, COUNT(*) FROM Employees AS T1 JOIN Departments AS T2 ON T1.DeptID = T2.DeptID GROUP BY T2.DeptID",
            "difficulty": "MEDIUM"
        },
        {
            "query_id": "sample_003",
            "question": "Show all employee names and their salaries.",
            "sql": "SELECT Name, Salary FROM Employees",
            "difficulty": "EASY"
        }
    ]


def setup_sample_database(db_path: str):
    """Set up a sample database for testing"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Departments (
            DeptID INTEGER PRIMARY KEY,
            DeptName TEXT NOT NULL,
            ManagerID INTEGER
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Employees (
            EmpID INTEGER PRIMARY KEY,
            Name TEXT NOT NULL,
            DeptID INTEGER,
            HireDate TEXT,
            Salary REAL,
            FOREIGN KEY (DeptID) REFERENCES Departments(DeptID)
        )
    """)
    
    # Insert sample data
    cursor.execute("INSERT OR REPLACE INTO Departments VALUES (1, 'Engineering', 101)")
    cursor.execute("INSERT OR REPLACE INTO Departments VALUES (2, 'Sales', 102)")
    cursor.execute("INSERT OR REPLACE INTO Departments VALUES (3, 'Marketing', 103)")
    
    # Insert sample employees
    employees = [
        (1, 'John Doe', 1, '2023-01-15', 75000),
        (2, 'Jane Smith', 1, '2023-02-20', 80000),
        (3, 'Bob Johnson', 2, '2022-12-10', 65000),
        (4, 'Alice Brown', 2, '2023-03-05', 70000),
        (5, 'Charlie Davis', 3, '2023-01-30', 60000)
    ]
    
    for emp in employees:
        cursor.execute("INSERT OR REPLACE INTO Employees VALUES (?, ?, ?, ?, ?)", emp)
    
    conn.commit()
    conn.close()
    
    print(f"Sample database created at: {db_path}")


def main():
    """Main evaluation function"""
    parser = argparse.ArgumentParser(description="DIVA-SQL Research Evaluation")
    parser.add_argument("--benchmark", choices=["sample", "bird", "spider"], 
                       default="sample", help="Benchmark to use")
    parser.add_argument("--output-dir", default="results", help="Output directory")
    parser.add_argument("--database-path", default="temp/sample.db", help="Database path")
    
    args = parser.parse_args()
    
    # Create output directory
    Path(args.output_dir).mkdir(exist_ok=True)
    Path("temp").mkdir(exist_ok=True)
    
    # Mock LLM client for demonstration
    class MockLLMClient:
        class Chat:
            class Completions:
                def create(self, **kwargs):
                    class Response:
                        class Choice:
                            class Message:
                                content = "SELECT T2.DeptName FROM Employees AS T1 JOIN Departments AS T2 ON T1.DeptID = T2.DeptID WHERE T1.HireDate > '2022-01-01' GROUP BY T2.DeptID HAVING COUNT(*) > 10"
                        choices = [Choice()]
                    return Response()
        chat = Chat()
    
    llm_client = MockLLMClient()
    
    # Set up evaluation
    evaluator = ResearchEvaluator(args.output_dir)
    
    # Load benchmark data
    if args.benchmark == "sample":
        benchmark_data = create_sample_benchmark()
        setup_sample_database(args.database_path)
    else:
        print(f"Benchmark {args.benchmark} not implemented in this demo")
        return
    
    # Define schema
    schema = {
        "tables": {
            "Employees": ["EmpID", "Name", "DeptID", "HireDate", "Salary"],
            "Departments": ["DeptID", "DeptName", "ManagerID"]
        }
    }
    
    print(f"Running research evaluation with {len(benchmark_data)} queries")
    
    # Run RQ1: Accuracy Evaluation
    rq1_results = evaluator.run_rq1_evaluation(llm_client, benchmark_data, schema, args.database_path)
    
    # Run RQ2: Human Study Setup (using failed queries from RQ1)
    failed_queries = []
    for system_name, results in rq1_results.items():
        for result in results.results_by_query:
            if not result.execution_accuracy:
                failed_queries.append({
                    "query_id": result.query_id,
                    "question": result.natural_language,
                    "sql": result.gold_sql,
                    "predicted_sql": result.predicted_sql,
                    "error_message": result.error_message
                })
    
    rq2_config = evaluator.run_rq2_setup(failed_queries)
    
    # Run RQ3: Error Prevention Analysis
    diva_results = rq1_results.get("DIVA-SQL")
    if diva_results:
        rq3_analysis = evaluator.run_rq3_analysis(diva_results)
    else:
        rq3_analysis = {"message": "DIVA-SQL results not available"}
    
    # Generate final report
    report = evaluator.generate_research_report(rq1_results, rq2_config, rq3_analysis)
    
    print("\n" + "=" * 60)
    print("RESEARCH EVALUATION COMPLETE")
    print("=" * 60)
    print(f"Results saved to: {args.output_dir}")
    print("\nSummary:")
    
    if "DIVA-SQL" in rq1_results:
        diva_ex = rq1_results["DIVA-SQL"].execution_accuracy
        print(f"- DIVA-SQL Execution Accuracy: {diva_ex:.3f}")
    
    print(f"- Human study queries prepared: {len(rq2_config['queries'])}")
    print(f"- Error analysis completed: {rq3_analysis.get('total_nodes', 0)} nodes analyzed")


if __name__ == "__main__":
    main()
