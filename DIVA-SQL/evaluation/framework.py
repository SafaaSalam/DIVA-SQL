"""
Evaluation Framework for DIVA-SQL

This module provides comprehensive evaluation capabilities including:
- Baseline implementations
- Metric calculations (EX, VES)
- Experimental setup for research questions
- Human study infrastructure
"""

from typing import Dict, List, Optional, Any, Tuple
import time
import json
import sqlite3
import pandas as pd
from dataclasses import dataclass
from abc import ABC, abstractmethod
from pathlib import Path

from ..core.pipeline import DIVASQLPipeline, DIVAResult


@dataclass
class EvaluationResult:
    """Result of evaluating a single query"""
    query_id: str
    natural_language: str
    gold_sql: str
    predicted_sql: Optional[str]
    execution_accuracy: bool
    valid_efficiency_score: float
    execution_time: float
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class BenchmarkResults:
    """Results for an entire benchmark"""
    benchmark_name: str
    system_name: str
    total_queries: int
    execution_accuracy: float
    avg_valid_efficiency_score: float
    avg_execution_time: float
    results_by_query: List[EvaluationResult]
    error_analysis: Dict[str, Any]


class Text2SQLSystem(ABC):
    """Abstract base class for Text-to-SQL systems"""
    
    @abstractmethod
    def generate_sql(self, nl_query: str, database_schema: Dict[str, Any], 
                    context: Optional[Dict[str, Any]] = None) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Generate SQL from natural language query
        
        Returns:
            Tuple of (generated_sql, metadata)
        """
        pass
    
    @abstractmethod
    def get_system_name(self) -> str:
        """Return the name of the system"""
        pass


class DIVASQLSystem(Text2SQLSystem):
    """DIVA-SQL system wrapper for evaluation"""
    
    def __init__(self, llm_client, model_name: str = "gpt-4"):
        self.pipeline = DIVASQLPipeline(llm_client, model_name)
    
    def generate_sql(self, nl_query: str, database_schema: Dict[str, Any], 
                    context: Optional[Dict[str, Any]] = None) -> Tuple[Optional[str], Dict[str, Any]]:
        result = self.pipeline.generate_sql(nl_query, database_schema, context)
        
        metadata = {
            "status": result.status.value,
            "confidence_score": result.confidence_score,
            "execution_time": result.execution_time,
            "verification_log": result.verification_log,
            "generation_steps": result.generation_steps,
            "semantic_dag": result.semantic_dag.to_dict() if result.semantic_dag else None
        }
        
        return result.final_sql, metadata
    
    def get_system_name(self) -> str:
        return "DIVA-SQL"


class ZeroShotBaselineSystem(Text2SQLSystem):
    """Zero-shot baseline using direct LLM prompting"""
    
    def __init__(self, llm_client, model_name: str = "gpt-4"):
        self.llm_client = llm_client
        self.model_name = model_name
    
    def generate_sql(self, nl_query: str, database_schema: Dict[str, Any], 
                    context: Optional[Dict[str, Any]] = None) -> Tuple[Optional[str], Dict[str, Any]]:
        
        start_time = time.time()
        
        # Create simple prompt
        schema_str = json.dumps(database_schema, indent=2)
        prompt = f"""
Given the following database schema and natural language query, generate a SQL query.

Schema:
{schema_str}

Question: {nl_query}

Generate only the SQL query without any explanation:
"""
        
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            
            sql = response.choices[0].message.content.strip()
            
            # Clean up common formatting issues
            if sql.startswith("```sql"):
                sql = sql[6:]
            if sql.endswith("```"):
                sql = sql[:-3]
            sql = sql.strip()
            
            metadata = {
                "execution_time": time.time() - start_time,
                "model_used": self.model_name,
                "prompt_type": "zero_shot"
            }
            
            return sql, metadata
            
        except Exception as e:
            metadata = {
                "execution_time": time.time() - start_time,
                "error": str(e)
            }
            return None, metadata
    
    def get_system_name(self) -> str:
        return f"Zero-Shot-{self.model_name}"


class SQLExecutor:
    """Handles SQL execution for evaluation"""
    
    def __init__(self, database_path: str):
        self.database_path = database_path
    
    def execute_sql(self, sql: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Execute SQL query and return results with timing
        """
        start_time = time.time()
        
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Set timeout
            conn.execute(f"PRAGMA busy_timeout = {timeout * 1000}")
            
            cursor.execute(sql)
            results = cursor.fetchall()
            column_names = [description[0] for description in cursor.description] if cursor.description else []
            
            conn.close()
            
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            
            return {
                "success": True,
                "results": results,
                "column_names": column_names,
                "row_count": len(results),
                "execution_time_ms": execution_time
            }
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return {
                "success": False,
                "error": str(e),
                "execution_time_ms": execution_time
            }
    
    def compare_results(self, result1: List[Any], result2: List[Any]) -> bool:
        """
        Compare two query results for equality
        """
        if len(result1) != len(result2):
            return False
        
        # Convert to sets for unordered comparison
        set1 = set(tuple(row) if isinstance(row, (list, tuple)) else (row,) for row in result1)
        set2 = set(tuple(row) if isinstance(row, (list, tuple)) else (row,) for row in result2)
        
        return set1 == set2


class MetricsCalculator:
    """Calculates evaluation metrics"""
    
    @staticmethod
    def calculate_execution_accuracy(results: List[EvaluationResult]) -> float:
        """Calculate Execution Accuracy (EX)"""
        if not results:
            return 0.0
        
        correct = sum(1 for r in results if r.execution_accuracy)
        return correct / len(results)
    
    @staticmethod
    def calculate_valid_efficiency_score(results: List[EvaluationResult]) -> float:
        """Calculate Valid Efficiency Score (VES)"""
        if not results:
            return 0.0
        
        total_score = sum(r.valid_efficiency_score for r in results)
        return total_score / len(results)
    
    @staticmethod
    def calculate_ves_for_query(execution_accuracy: bool, execution_time_ms: float, 
                              baseline_time_ms: float = 1000.0) -> float:
        """
        Calculate VES for a single query
        
        VES = EX * efficiency_penalty
        where efficiency_penalty = min(1.0, baseline_time / actual_time)
        """
        if not execution_accuracy:
            return 0.0
        
        if execution_time_ms <= 0:
            return 1.0
        
        efficiency_penalty = min(1.0, baseline_time_ms / execution_time_ms)
        return efficiency_penalty
    
    @staticmethod
    def analyze_errors(results: List[EvaluationResult]) -> Dict[str, Any]:
        """Analyze error patterns in results"""
        total_queries = len(results)
        failed_queries = [r for r in results if not r.execution_accuracy]
        
        error_types = {}
        for result in failed_queries:
            if result.error_message:
                # Categorize errors (simplified)
                error_msg = result.error_message.lower()
                if "syntax" in error_msg:
                    error_types["syntax_error"] = error_types.get("syntax_error", 0) + 1
                elif "table" in error_msg or "column" in error_msg:
                    error_types["schema_error"] = error_types.get("schema_error", 0) + 1
                elif "timeout" in error_msg:
                    error_types["timeout_error"] = error_types.get("timeout_error", 0) + 1
                else:
                    error_types["other_error"] = error_types.get("other_error", 0) + 1
            else:
                error_types["result_mismatch"] = error_types.get("result_mismatch", 0) + 1
        
        return {
            "total_queries": total_queries,
            "failed_queries": len(failed_queries),
            "success_rate": (total_queries - len(failed_queries)) / total_queries if total_queries > 0 else 0,
            "error_breakdown": error_types,
            "avg_execution_time": sum(r.execution_time for r in results) / len(results) if results else 0
        }


class BenchmarkEvaluator:
    """Main benchmark evaluation class"""
    
    def __init__(self, database_path: str):
        self.executor = SQLExecutor(database_path)
        self.metrics_calculator = MetricsCalculator()
    
    def evaluate_system(self, system: Text2SQLSystem, 
                       benchmark_data: List[Dict[str, Any]],
                       database_schema: Dict[str, Any]) -> BenchmarkResults:
        """
        Evaluate a Text-to-SQL system on a benchmark
        
        Args:
            system: The system to evaluate
            benchmark_data: List of benchmark queries with gold SQL
            database_schema: Database schema information
            
        Returns:
            BenchmarkResults with detailed evaluation
        """
        results = []
        
        for i, query_data in enumerate(benchmark_data):
            print(f"Evaluating query {i+1}/{len(benchmark_data)}: {query_data.get('query_id', i)}")
            
            result = self._evaluate_single_query(
                system, query_data, database_schema
            )
            results.append(result)
        
        # Calculate aggregate metrics
        execution_accuracy = self.metrics_calculator.calculate_execution_accuracy(results)
        avg_ves = self.metrics_calculator.calculate_valid_efficiency_score(results)
        avg_execution_time = sum(r.execution_time for r in results) / len(results)
        error_analysis = self.metrics_calculator.analyze_errors(results)
        
        return BenchmarkResults(
            benchmark_name="Custom",
            system_name=system.get_system_name(),
            total_queries=len(results),
            execution_accuracy=execution_accuracy,
            avg_valid_efficiency_score=avg_ves,
            avg_execution_time=avg_execution_time,
            results_by_query=results,
            error_analysis=error_analysis
        )
    
    def _evaluate_single_query(self, system: Text2SQLSystem,
                              query_data: Dict[str, Any],
                              database_schema: Dict[str, Any]) -> EvaluationResult:
        """Evaluate a single query"""
        
        query_id = query_data.get("query_id", "unknown")
        nl_query = query_data["question"]
        gold_sql = query_data["sql"]
        
        start_time = time.time()
        
        # Generate SQL using the system
        predicted_sql, metadata = system.generate_sql(nl_query, database_schema)
        
        generation_time = time.time() - start_time
        
        if not predicted_sql:
            return EvaluationResult(
                query_id=query_id,
                natural_language=nl_query,
                gold_sql=gold_sql,
                predicted_sql=None,
                execution_accuracy=False,
                valid_efficiency_score=0.0,
                execution_time=generation_time,
                error_message="No SQL generated",
                metadata=metadata
            )
        
        # Execute both gold and predicted SQL
        gold_result = self.executor.execute_sql(gold_sql)
        predicted_result = self.executor.execute_sql(predicted_sql)
        
        # Check execution accuracy
        execution_accuracy = False
        error_message = None
        
        if not predicted_result["success"]:
            error_message = f"Execution failed: {predicted_result['error']}"
        elif not gold_result["success"]:
            error_message = f"Gold query execution failed: {gold_result['error']}"
        else:
            # Compare results
            execution_accuracy = self.executor.compare_results(
                gold_result["results"], predicted_result["results"]
            )
            if not execution_accuracy:
                error_message = "Results do not match gold standard"
        
        # Calculate VES
        ves = self.metrics_calculator.calculate_ves_for_query(
            execution_accuracy,
            predicted_result.get("execution_time_ms", 0),
            gold_result.get("execution_time_ms", 1000)
        )
        
        return EvaluationResult(
            query_id=query_id,
            natural_language=nl_query,
            gold_sql=gold_sql,
            predicted_sql=predicted_sql,
            execution_accuracy=execution_accuracy,
            valid_efficiency_score=ves,
            execution_time=generation_time,
            error_message=error_message,
            metadata={
                **metadata,
                "gold_execution": gold_result,
                "predicted_execution": predicted_result
            }
        )
    
    def compare_systems(self, systems: List[Text2SQLSystem],
                       benchmark_data: List[Dict[str, Any]],
                       database_schema: Dict[str, Any]) -> Dict[str, BenchmarkResults]:
        """
        Compare multiple systems on the same benchmark
        """
        results = {}
        
        for system in systems:
            print(f"\nEvaluating system: {system.get_system_name()}")
            system_results = self.evaluate_system(system, benchmark_data, database_schema)
            results[system.get_system_name()] = system_results
        
        return results
    
    def generate_comparison_report(self, comparison_results: Dict[str, BenchmarkResults]) -> str:
        """
        Generate a detailed comparison report
        """
        report_lines = []
        report_lines.append("DIVA-SQL Evaluation Report")
        report_lines.append("=" * 50)
        
        # Summary table
        report_lines.append("\nSummary Results:")
        report_lines.append(f"{'System':<20} {'EX (%)':<10} {'VES':<10} {'Avg Time (s)':<15}")
        report_lines.append("-" * 55)
        
        for system_name, results in comparison_results.items():
            report_lines.append(
                f"{system_name:<20} "
                f"{results.execution_accuracy*100:<10.1f} "
                f"{results.avg_valid_efficiency_score:<10.3f} "
                f"{results.avg_execution_time:<15.2f}"
            )
        
        # Detailed analysis
        report_lines.append("\nDetailed Analysis:")
        for system_name, results in comparison_results.items():
            report_lines.append(f"\n{system_name}:")
            report_lines.append(f"  Total Queries: {results.total_queries}")
            report_lines.append(f"  Execution Accuracy: {results.execution_accuracy:.3f}")
            report_lines.append(f"  Valid Efficiency Score: {results.avg_valid_efficiency_score:.3f}")
            report_lines.append(f"  Average Execution Time: {results.avg_execution_time:.2f}s")
            
            # Error analysis
            error_analysis = results.error_analysis
            report_lines.append(f"  Success Rate: {error_analysis['success_rate']:.3f}")
            report_lines.append(f"  Error Breakdown:")
            for error_type, count in error_analysis['error_breakdown'].items():
                report_lines.append(f"    {error_type}: {count}")
        
        return "\n".join(report_lines)


def load_bird_benchmark(data_path: str) -> List[Dict[str, Any]]:
    """
    Load BIRD benchmark data
    """
    # This is a placeholder - in practice, you'd load from BIRD dataset files
    sample_data = [
        {
            "query_id": "bird_001",
            "question": "What are the names of departments with more than 10 employees hired after 2022?",
            "sql": "SELECT T1.DeptName FROM Departments AS T1 JOIN Employees AS T2 ON T1.DeptID = T2.DeptID WHERE T2.HireDate > '2022-01-01' GROUP BY T1.DeptID HAVING COUNT(*) > 10",
            "difficulty": "HARD"
        },
        {
            "query_id": "bird_002", 
            "question": "How many employees work in the Sales department?",
            "sql": "SELECT COUNT(*) FROM Employees AS T1 JOIN Departments AS T2 ON T1.DeptID = T2.DeptID WHERE T2.DeptName = 'Sales'",
            "difficulty": "EASY"
        }
    ]
    
    return sample_data


def load_spider_benchmark(data_path: str) -> List[Dict[str, Any]]:
    """
    Load Spider benchmark data
    """
    # This is a placeholder - in practice, you'd load from Spider dataset files
    sample_data = [
        {
            "query_id": "spider_001",
            "question": "Show the name of all employees.",
            "sql": "SELECT Name FROM Employees",
            "difficulty": "EASY"
        }
    ]
    
    return sample_data


# Example usage
if __name__ == "__main__":
    # Mock LLM client for testing
    class MockLLMClient:
        class Chat:
            class Completions:
                def create(self, **kwargs):
                    class Response:
                        class Choice:
                            class Message:
                                content = "SELECT T1.DeptName FROM Departments AS T1 JOIN Employees AS T2 ON T1.DeptID = T2.DeptID WHERE T2.HireDate > '2022-01-01' GROUP BY T1.DeptID HAVING COUNT(*) > 10"
                        choices = [Choice()]
                    return Response()
        chat = Chat()
    
    # Set up evaluation
    database_path = ":memory:"  # In-memory SQLite for testing
    evaluator = BenchmarkEvaluator(database_path)
    
    # Create systems to compare
    diva_system = DIVASQLSystem(MockLLMClient())
    baseline_system = ZeroShotBaselineSystem(MockLLMClient())
    
    # Load benchmark data
    benchmark_data = load_bird_benchmark("path/to/bird/data")
    
    schema = {
        "tables": {
            "Employees": ["EmpID", "Name", "DeptID", "HireDate"],
            "Departments": ["DeptID", "DeptName"]
        }
    }
    
    # Compare systems
    comparison_results = evaluator.compare_systems(
        [diva_system, baseline_system],
        benchmark_data,
        schema
    )
    
    # Generate report
    report = evaluator.generate_comparison_report(comparison_results)
    print(report)
