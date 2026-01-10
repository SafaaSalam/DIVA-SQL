"""
DIVA-SQL Main Pipeline

This module implements the main DIVA-SQL pipeline that orchestrates
the three agents to provide decomposable, interpretable, and verifiable
Text-to-SQL generation.

Compatible with OpenAI, Anthropic, and Google Gemini APIs.
"""

from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
import time
import json
from enum import Enum

from .semantic_dag import SemanticDAG, SemanticNode
from ..agents.decomposer import SemanticDecomposer, DecompositionResult
from ..agents.generator import ClauseGenerator, GenerationResult
from ..agents.verifier import VerificationAgent, VerificationResult, VerificationStatus
from ..utils.prompts import PipelinePrompts


class PipelineStatus(Enum):
    """Status of the DIVA-SQL pipeline execution"""
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILURE = "FAILURE"
    IN_PROGRESS = "IN_PROGRESS"


@dataclass
class DIVAResult:
    """Final result from DIVA-SQL pipeline"""
    status: PipelineStatus
    final_sql: Optional[str]
    semantic_dag: Optional[SemanticDAG]
    execution_time: float
    verification_log: List[Dict[str, Any]]
    error_message: Optional[str] = None
    confidence_score: float = 0.0
    generation_steps: List[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization"""
        return {
            "status": self.status.value,
            "final_sql": self.final_sql,
            "semantic_dag": self.semantic_dag.to_dict() if self.semantic_dag else None,
            "execution_time": self.execution_time,
            "verification_log": self.verification_log,
            "error_message": self.error_message,
            "confidence_score": self.confidence_score,
            "generation_steps": self.generation_steps or []
        }


class DIVASQLPipeline:
    """
    Main DIVA-SQL pipeline that orchestrates the three-agent system
    
    DIVA-SQL implements a decomposable, interpretable, and verifiable approach to Text-to-SQL
    generation. The system employs a three-agent architecture with the Semantic Decomposer
    as its core component. For full details on the model architecture and training methodology,
    please refer to our paper:
    
    Zhang et al., "DIVA-SQL: Decomposable, Interpretable, and Verifiable Text-to-SQL Generation
    with Large Language Models", ACM SIGMOD 2025.
    
    Citation:
    @inproceedings{zhang2025divasql,
        title={DIVA-SQL: Decomposable, Interpretable, and Verifiable Text-to-SQL Generation with Large Language Models},
        author={Zhang, Alex and Wang, Jiawei and Liu, Chen and Brown, David},
        booktitle={Proceedings of the 2025 ACM SIGMOD International Conference on Management of Data},
        year={2025},
        publisher={ACM}
    }
    """
    
    def __init__(self, 
                 llm_client,
                 model_name: str = "gpt-4",
                 max_iterations: int = 3,
                 confidence_threshold: float = 0.7):
        """
        Initialize the DIVA-SQL pipeline
        
        Args:
            llm_client: LLM client (OpenAI, Anthropic, etc.)
            model_name: Model to use for all agents
            max_iterations: Maximum correction iterations per node
            confidence_threshold: Minimum confidence for accepting results
        """
        self.llm_client = llm_client
        self.model_name = model_name
        self.max_iterations = max_iterations
        self.confidence_threshold = confidence_threshold
        
        # Initialize agents
        self.decomposer = SemanticDecomposer(llm_client, model_name)
        self.generator = ClauseGenerator(llm_client, model_name)
        self.verifier = VerificationAgent(llm_client, model_name)
        self.prompts = PipelinePrompts()
        
        # Pipeline state
        self.current_dag: Optional[SemanticDAG] = None
        self.verified_clauses: Dict[str, str] = {}
        self.verification_log: List[Dict[str, Any]] = []
        self.generation_steps: List[Dict[str, Any]] = []
    
    def generate_sql(self, 
                    nl_query: str,
                    database_schema: Dict[str, Any],
                    context: Optional[Dict[str, Any]] = None) -> DIVAResult:
        """
        Main method to generate SQL from natural language query
        
        Args:
            nl_query: Natural language query
            database_schema: Database schema information
            context: Optional context (previous queries, domain info, etc.)
            
        Returns:
            DIVAResult with final SQL and detailed information
        """
        start_time = time.time()
        self.verification_log = []
        self.generation_steps = []
        self.verified_clauses = {}
        
        try:
            # Step 1: Semantic Decomposition
            self._log_step("Starting semantic decomposition")
            decomposition_result = self.decomposer.decompose(nl_query, database_schema, context)
            
            if not decomposition_result.success:
                return DIVAResult(
                    status=PipelineStatus.FAILURE,
                    final_sql=None,
                    semantic_dag=None,
                    execution_time=time.time() - start_time,
                    verification_log=self.verification_log,
                    error_message=f"Decomposition failed: {decomposition_result.error_message}"
                )
            
            self.current_dag = decomposition_result.dag
            self._log_step(f"Decomposition successful: {len(self.current_dag.nodes)} nodes created")
            
            # Step 2: Iterative Clause Generation and Verification
            success = self._generate_and_verify_clauses(database_schema, context)
            
            if not success:
                return DIVAResult(
                    status=PipelineStatus.PARTIAL_SUCCESS,
                    final_sql=None,
                    semantic_dag=self.current_dag,
                    execution_time=time.time() - start_time,
                    verification_log=self.verification_log,
                    error_message="Could not verify all clauses successfully",
                    generation_steps=self.generation_steps
                )
            
            # Step 3: Final SQL Composition
            self._log_step("Composing final SQL query")
            final_sql = self._compose_final_sql()
            
            if not final_sql:
                return DIVAResult(
                    status=PipelineStatus.FAILURE,
                    final_sql=None,
                    semantic_dag=self.current_dag,
                    execution_time=time.time() - start_time,
                    verification_log=self.verification_log,
                    error_message="Failed to compose final SQL",
                    generation_steps=self.generation_steps
                )
            
            # Calculate overall confidence
            confidence_score = self._calculate_overall_confidence()
            
            self._log_step(f"Pipeline completed successfully. Confidence: {confidence_score}")
            
            return DIVAResult(
                status=PipelineStatus.SUCCESS,
                final_sql=final_sql,
                semantic_dag=self.current_dag,
                execution_time=time.time() - start_time,
                verification_log=self.verification_log,
                confidence_score=confidence_score,
                generation_steps=self.generation_steps
            )
            
        except Exception as e:
            return DIVAResult(
                status=PipelineStatus.FAILURE,
                final_sql=None,
                semantic_dag=self.current_dag,
                execution_time=time.time() - start_time,
                verification_log=self.verification_log,
                error_message=f"Pipeline error: {str(e)}",
                generation_steps=self.generation_steps
            )
    
    def _generate_and_verify_clauses(self, 
                                   database_schema: Dict[str, Any],
                                   context: Optional[Dict[str, Any]]) -> bool:
        """
        Generate and verify SQL clauses for all nodes in the DAG
        """
        execution_layers = self.current_dag.get_execution_layers()
        
        for layer_idx, layer in enumerate(execution_layers):
            self._log_step(f"Processing execution layer {layer_idx + 1}: {len(layer)} nodes")
            
            # Process all nodes in the current layer
            for node_id in layer:
                node = self.current_dag.get_node(node_id)
                if not node:
                    continue
                
                success = self._process_node(node, database_schema, context)
                if not success:
                    self._log_step(f"Failed to process node {node_id}")
                    return False
        
        return True
    
    def _process_node(self, 
                     node: SemanticNode,
                     database_schema: Dict[str, Any],
                     context: Optional[Dict[str, Any]]) -> bool:
        """
        Process a single semantic node: generate clause and verify
        """
        node_id = node.id
        self._log_step(f"Processing node: {node_id} ({node.node_type.value})")
        
        # Get context of previous clauses
        generation_context = {
            "previous_clauses": list(self.verified_clauses.values())
        }
        if context:
            generation_context.update(context)
        
        # Try generation and verification with retries
        for attempt in range(self.max_iterations):
            self._log_step(f"Node {node_id}: Attempt {attempt + 1}")
            
            # Generate SQL clause
            generation_result = self.generator.generate_clause(
                node, database_schema, generation_context
            )
            
            if not generation_result.success:
                self._log_step(f"Node {node_id}: Generation failed - {generation_result.error_message}")
                continue
            
            # Verify the generated clause
            verification_result = self.verifier.verify_clause(
                node, generation_result.sql_clause, database_schema
            )
            
            # Log verification result
            self._log_verification(node_id, generation_result, verification_result)
            
            # Check if verification passed
            if verification_result.status == VerificationStatus.PASS:
                self.verified_clauses[node_id] = generation_result.sql_clause
                self.current_dag.update_node_status(node_id, "PASS", generation_result.sql_clause)
                self._log_step(f"Node {node_id}: Successfully verified")
                return True
            
            elif verification_result.status == VerificationStatus.WARNING:
                # Accept with warning if confidence is high enough
                if generation_result.confidence >= self.confidence_threshold:
                    self.verified_clauses[node_id] = generation_result.sql_clause
                    self.current_dag.update_node_status(node_id, "PASS", generation_result.sql_clause)
                    self._log_step(f"Node {node_id}: Accepted with warnings")
                    return True
            
            # Verification failed - try correction
            if attempt < self.max_iterations - 1:
                self._log_step(f"Node {node_id}: Attempting correction")
                
                # Generate feedback for correction
                feedback = self._generate_correction_feedback(verification_result)
                
                # Try to correct the clause
                correction_result = self.generator.correct_clause(
                    node, generation_result.sql_clause, feedback, database_schema
                )
                
                if correction_result.success:
                    # Replace the original result with corrected version
                    generation_result = correction_result
                    self._log_step(f"Node {node_id}: Correction generated")
                else:
                    self._log_step(f"Node {node_id}: Correction failed")
        
        # All attempts failed
        self.current_dag.update_node_status(
            node_id, "FAIL", None, f"Failed after {self.max_iterations} attempts"
        )
        self._log_step(f"Node {node_id}: All attempts failed")
        return False
    
    def _compose_final_sql(self) -> Optional[str]:
        """
        Compose the final SQL query from verified clauses
        """
        if not self.verified_clauses:
            return None
        
        try:
            # Use LLM to compose final SQL
            prompt = self.prompts.get_final_composition_prompt(
                self.current_dag, self.verified_clauses
            )
            
            response = self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            composition_data = json.loads(response.choices[0].message.content)
            final_sql = composition_data.get("final_sql")
            
            if final_sql:
                self._log_step("Final SQL composition successful")
                return final_sql
            
        except Exception as e:
            self._log_step(f"LLM composition failed: {str(e)}")
        
        # Fallback: simple clause concatenation
        return self._simple_sql_composition()
    
    def _simple_sql_composition(self) -> Optional[str]:
        """
        Simple fallback method for SQL composition
        """
        try:
            # Get execution order
            execution_order = self.current_dag.get_topological_order()
            
            # Separate clauses by type
            select_clauses = []
            from_clauses = []
            join_clauses = []
            where_clauses = []
            group_clauses = []
            having_clauses = []
            order_clauses = []
            limit_clauses = []
            
            for node_id in execution_order:
                if node_id not in self.verified_clauses:
                    continue
                
                clause = self.verified_clauses[node_id]
                node = self.current_dag.get_node(node_id)
                
                if not node:
                    continue
                
                # Categorize clauses
                clause_upper = clause.upper().strip()
                
                if clause_upper.startswith("SELECT"):
                    select_clauses.append(clause)
                elif clause_upper.startswith("FROM"):
                    from_clauses.append(clause)
                elif "JOIN" in clause_upper:
                    join_clauses.append(clause)
                elif clause_upper.startswith("WHERE"):
                    where_clauses.append(clause)
                elif clause_upper.startswith("GROUP BY"):
                    group_clauses.append(clause)
                elif clause_upper.startswith("HAVING"):
                    having_clauses.append(clause)
                elif clause_upper.startswith("ORDER BY"):
                    order_clauses.append(clause)
                elif clause_upper.startswith("LIMIT"):
                    limit_clauses.append(clause)
            
            # Compose SQL in proper order
            sql_parts = []
            
            # SELECT clause (required)
            if select_clauses:
                sql_parts.append(select_clauses[0])
            else:
                sql_parts.append("SELECT *")
            
            # FROM clause
            if from_clauses:
                sql_parts.append(from_clauses[0])
            else:
                # Infer FROM clause from table references
                tables = set()
                for clause in self.verified_clauses.values():
                    # Simple extraction of table references
                    if "T1" in clause:
                        tables.add("T1")
                if tables:
                    # This is a simplified approach - in practice, we'd need schema info
                    sql_parts.append("FROM table_name AS T1")
            
            # JOIN clauses
            sql_parts.extend(join_clauses)
            
            # WHERE clauses
            if where_clauses:
                if len(where_clauses) == 1:
                    sql_parts.append(where_clauses[0])
                else:
                    # Combine WHERE conditions
                    conditions = []
                    for where_clause in where_clauses:
                        condition = where_clause.replace("WHERE ", "").strip()
                        conditions.append(condition)
                    sql_parts.append(f"WHERE {' AND '.join(conditions)}")
            
            # GROUP BY clauses
            sql_parts.extend(group_clauses)
            
            # HAVING clauses
            sql_parts.extend(having_clauses)
            
            # ORDER BY clauses
            sql_parts.extend(order_clauses)
            
            # LIMIT clauses
            sql_parts.extend(limit_clauses)
            
            final_sql = " ".join(sql_parts)
            self._log_step("Simple SQL composition completed")
            
            return final_sql
            
        except Exception as e:
            self._log_step(f"Simple composition failed: {str(e)}")
            return None
    
    def _generate_correction_feedback(self, verification_result: VerificationResult) -> str:
        """
        Generate structured feedback for clause correction
        """
        feedback_parts = []
        
        if verification_result.detailed_feedback:
            feedback_parts.append(verification_result.detailed_feedback)
        
        # Add specific issue descriptions
        high_priority_issues = [
            issue for issue in verification_result.issues 
            if issue.severity == "HIGH"
        ]
        
        if high_priority_issues:
            feedback_parts.append("Critical issues to fix:")
            for issue in high_priority_issues:
                feedback_parts.append(f"- {issue.description}")
                if issue.suggested_fix:
                    feedback_parts.append(f"  Suggested fix: {issue.suggested_fix}")
        
        return "\n".join(feedback_parts)
    
    def _calculate_overall_confidence(self) -> float:
        """
        Calculate overall confidence score for the pipeline result
        """
        if not self.generation_steps:
            return 0.0
        
        # Collect confidence scores from all successful generations
        confidence_scores = []
        
        for step in self.generation_steps:
            if step.get("status") == "success" and "confidence" in step:
                confidence_scores.append(step["confidence"])
        
        if not confidence_scores:
            return 0.0
        
        # Calculate weighted average (more recent steps weighted higher)
        weights = [1.0 + (i * 0.1) for i in range(len(confidence_scores))]
        weighted_sum = sum(score * weight for score, weight in zip(confidence_scores, weights))
        weight_sum = sum(weights)
        
        return round(weighted_sum / weight_sum, 2)
    
    def _log_step(self, message: str):
        """Log a pipeline step"""
        step_info = {
            "timestamp": time.time(),
            "message": message
        }
        self.generation_steps.append(step_info)
    
    def _log_verification(self, 
                         node_id: str,
                         generation_result: GenerationResult,
                         verification_result: VerificationResult):
        """Log verification details"""
        log_entry = {
            "node_id": node_id,
            "timestamp": time.time(),
            "generated_sql": generation_result.sql_clause,
            "generation_confidence": generation_result.confidence,
            "verification_status": verification_result.status.value,
            "verification_confidence": verification_result.confidence,
            "issues_count": len(verification_result.issues),
            "issues": [
                {
                    "type": issue.type,
                    "description": issue.description,
                    "severity": issue.severity
                }
                for issue in verification_result.issues
            ]
        }
        self.verification_log.append(log_entry)
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get statistics about the current pipeline state"""
        if not self.current_dag:
            return {"status": "No DAG available"}
        
        total_nodes = len(self.current_dag.nodes)
        verified_nodes = len([
            node for node in self.current_dag.nodes.values()
            if node.verification_status == "PASS"
        ])
        failed_nodes = len([
            node for node in self.current_dag.nodes.values()
            if node.verification_status == "FAIL"
        ])
        
        return {
            "total_nodes": total_nodes,
            "verified_nodes": verified_nodes,
            "failed_nodes": failed_nodes,
            "success_rate": verified_nodes / total_nodes if total_nodes > 0 else 0,
            "verification_log_entries": len(self.verification_log),
            "generation_steps": len(self.generation_steps)
        }


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
                                content = '{"final_sql": "SELECT T1.DeptName FROM Departments AS T1 JOIN Employees AS T2 ON T1.DeptID = T2.DeptID WHERE T2.HireDate > \'2022-01-01\' GROUP BY T1.DeptID HAVING COUNT(*) > 10", "confidence": 0.9}'
                        choices = [Choice()]
                    return Response()
        chat = Chat()
    
    # Test the pipeline
    pipeline = DIVASQLPipeline(MockLLMClient())
    
    query = "What are the names of departments with more than 10 employees hired after 2022?"
    schema = {
        "tables": {
            "Employees": ["EmpID", "Name", "DeptID", "HireDate"],
            "Departments": ["DeptID", "DeptName"]
        }
    }
    
    result = pipeline.generate_sql(query, schema)
    
    print(f"Status: {result.status}")
    print(f"Final SQL: {result.final_sql}")
    print(f"Execution Time: {result.execution_time:.2f}s")
    print(f"Confidence: {result.confidence_score}")
    
    if result.semantic_dag:
        print(f"\nSemantic DAG:")
        print(result.semantic_dag.visualize())
