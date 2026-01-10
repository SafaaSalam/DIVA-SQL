"""
Semantic DAG (Directed Acyclic Graph) representation for DIVA-SQL

This module provides the core data structures and operations for representing
the semantic decomposition of natural language queries as DAGs.
"""

from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import networkx as nx
import json


class NodeType(Enum):
    """Types of semantic operations in the DAG"""
    FILTER = "filter"
    JOIN = "join"
    GROUP = "group"
    AGGREGATE = "aggregate"
    SELECT = "select"
    ORDER = "order"
    LIMIT = "limit"
    SUBQUERY = "subquery"
    UNION = "union"
    HAVING = "having"


@dataclass
class SemanticNode:
    """
    Represents a single semantic operation in the DAG
    """
    id: str
    node_type: NodeType
    description: str  # Natural language description
    tables: List[str] = field(default_factory=list)
    columns: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)
    sql_clause: Optional[str] = None  # Generated SQL for this node
    verification_status: Optional[str] = None  # PENDING, PASS, FAIL
    error_details: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation"""
        return {
            "id": self.id,
            "node_type": self.node_type.value,
            "description": self.description,
            "tables": self.tables,
            "columns": self.columns,
            "conditions": self.conditions,
            "sql_clause": self.sql_clause,
            "verification_status": self.verification_status,
            "error_details": self.error_details,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SemanticNode':
        """Create node from dictionary representation"""
        return cls(
            id=data["id"],
            node_type=NodeType(data["node_type"]),
            description=data["description"],
            tables=data.get("tables", []),
            columns=data.get("columns", []),
            conditions=data.get("conditions", []),
            sql_clause=data.get("sql_clause"),
            verification_status=data.get("verification_status"),
            error_details=data.get("error_details"),
            metadata=data.get("metadata", {})
        )


class SemanticDAG:
    """
    Manages the semantic DAG structure and operations
    """
    
    def __init__(self, query_id: Optional[str] = None):
        self.query_id = query_id
        self.graph = nx.DiGraph()
        self.nodes: Dict[str, SemanticNode] = {}
        self.root_nodes: Set[str] = set()
        self.leaf_nodes: Set[str] = set()
    
    def add_node(self, node: SemanticNode) -> None:
        """Add a semantic node to the DAG"""
        self.nodes[node.id] = node
        self.graph.add_node(node.id, data=node)
        self._update_root_leaf_nodes()
    
    def add_edge(self, parent_id: str, child_id: str) -> None:
        """Add a dependency edge (parent -> child)"""
        if parent_id not in self.nodes or child_id not in self.nodes:
            raise ValueError("Both nodes must exist before adding edge")
        
        self.graph.add_edge(parent_id, child_id)
        self._update_root_leaf_nodes()
        
        # Verify DAG property
        if not nx.is_directed_acyclic_graph(self.graph):
            self.graph.remove_edge(parent_id, child_id)
            raise ValueError("Adding this edge would create a cycle")
    
    def get_node(self, node_id: str) -> Optional[SemanticNode]:
        """Get a node by ID"""
        return self.nodes.get(node_id)
    
    def get_topological_order(self) -> List[str]:
        """Get nodes in topological order for execution"""
        return list(nx.topological_sort(self.graph))
    
    def get_execution_order(self) -> List[str]:
        """Alias for get_topological_order for backward compatibility"""
        return self.get_topological_order()
    
    def get_dependencies(self, node_id: str) -> List[str]:
        """Get direct dependencies (predecessors) of a node"""
        return list(self.graph.predecessors(node_id))
    
    def get_dependents(self, node_id: str) -> List[str]:
        """Get direct dependents (successors) of a node"""
        return list(self.graph.successors(node_id))
    
    def get_execution_layers(self) -> List[List[str]]:
        """
        Group nodes into execution layers where nodes in the same layer
        can be executed in parallel
        """
        layers = []
        remaining_nodes = set(self.nodes.keys())
        
        while remaining_nodes:
            # Find nodes with no remaining dependencies
            ready_nodes = []
            for node_id in remaining_nodes:
                deps = set(self.get_dependencies(node_id))
                if not deps.intersection(remaining_nodes):
                    ready_nodes.append(node_id)
            
            if not ready_nodes:
                raise ValueError("Circular dependency detected")
            
            layers.append(ready_nodes)
            remaining_nodes -= set(ready_nodes)
        
        return layers
    
    def update_node_status(self, node_id: str, status: str, 
                          sql_clause: Optional[str] = None,
                          error_details: Optional[str] = None) -> None:
        """Update the verification status of a node"""
        if node_id in self.nodes:
            node = self.nodes[node_id]
            node.verification_status = status
            if sql_clause:
                node.sql_clause = sql_clause
            if error_details:
                node.error_details = error_details
    
    def get_failed_nodes(self) -> List[SemanticNode]:
        """Get all nodes that failed verification"""
        return [node for node in self.nodes.values() 
                if node.verification_status == "FAIL"]
    
    def get_ready_nodes(self) -> List[SemanticNode]:
        """Get nodes ready for SQL generation (dependencies satisfied)"""
        ready = []
        for node_id in self.nodes:
            # Check if all dependencies are verified
            deps = self.get_dependencies(node_id)
            if all(self.nodes[dep_id].verification_status == "PASS" 
                   for dep_id in deps):
                node = self.nodes[node_id]
                if node.verification_status in [None, "PENDING"]:
                    ready.append(node)
        return ready
    
    def _update_root_leaf_nodes(self) -> None:
        """Update the sets of root and leaf nodes"""
        self.root_nodes = {n for n in self.nodes if self.graph.in_degree(n) == 0}
        self.leaf_nodes = {n for n in self.nodes if self.graph.out_degree(n) == 0}
    
    def to_dict(self) -> Dict[str, Any]:
        """Export DAG to dictionary format"""
        return {
            "query_id": self.query_id,
            "nodes": {node_id: node.to_dict() for node_id, node in self.nodes.items()},
            "edges": list(self.graph.edges()),
            "root_nodes": list(self.root_nodes),
            "leaf_nodes": list(self.leaf_nodes)
        }
    
    def to_json(self) -> str:
        """Export DAG to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SemanticDAG':
        """Create DAG from dictionary representation"""
        dag = cls(query_id=data.get("query_id"))
        
        # Add nodes
        for node_data in data["nodes"].values():
            node = SemanticNode.from_dict(node_data)
            dag.add_node(node)
        
        # Add edges
        for parent_id, child_id in data["edges"]:
            dag.add_edge(parent_id, child_id)
        
        return dag
    
    @classmethod
    def from_json(cls, json_str: str) -> 'SemanticDAG':
        """Create DAG from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def visualize(self) -> str:
        """Generate a text-based visualization of the DAG"""
        lines = [f"Semantic DAG (Query: {self.query_id})"]
        lines.append("=" * 50)
        
        # Show execution layers
        layers = self.get_execution_layers()
        for i, layer in enumerate(layers):
            lines.append(f"\nLayer {i + 1}:")
            for node_id in layer:
                node = self.nodes[node_id]
                status = node.verification_status or "PENDING"
                lines.append(f"  [{status}] {node_id}: {node.description}")
                if node.sql_clause:
                    lines.append(f"       SQL: {node.sql_clause}")
                if node.error_details:
                    lines.append(f"       ERROR: {node.error_details}")
        
        return "\n".join(lines)


# Example usage and test cases
if __name__ == "__main__":
    # Create a sample DAG for the query:
    # "What are the names of departments with more than 10 employees hired after 2022?"
    
    dag = SemanticDAG("sample_query_1")
    
    # Node A: Filter employees hired after 2022
    node_a = SemanticNode(
        id="filter_employees",
        node_type=NodeType.FILTER,
        description="Find employees hired after 2022",
        tables=["Employees"],
        columns=["HireDate"],
        conditions=["HireDate > '2022-01-01'"]
    )
    
    # Node B: Group by department and count
    node_b = SemanticNode(
        id="group_count",
        node_type=NodeType.GROUP,
        description="Count employees by department, keep departments with > 10",
        tables=["Employees"],
        columns=["DeptID"],
        conditions=["COUNT(*) > 10"]
    )
    
    # Node C: Get department names
    node_c = SemanticNode(
        id="get_dept_names",
        node_type=NodeType.SELECT,
        description="Get department names",
        tables=["Departments"],
        columns=["DeptName"]
    )
    
    # Add nodes to DAG
    dag.add_node(node_a)
    dag.add_node(node_b)
    dag.add_node(node_c)
    
    # Add dependencies
    dag.add_edge("filter_employees", "group_count")
    dag.add_edge("group_count", "get_dept_names")
    
    # Print visualization
    print(dag.visualize())
    
    # Export to JSON
    print("\nJSON Export:")
    print(dag.to_json())
