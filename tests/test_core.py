"""
Test suite for DIVA-SQL core components
"""

import unittest
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.core.semantic_dag import SemanticDAG, SemanticNode, NodeType
from src.utils.error_taxonomy import ErrorTaxonomy, analyze_sql_errors


class TestSemanticDAG(unittest.TestCase):
    """Test cases for Semantic DAG functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.dag = SemanticDAG("test_query")
        
        # Create test nodes
        self.filter_node = SemanticNode(
            id="filter_test",
            node_type=NodeType.FILTER,
            description="Test filter operation",
            tables=["TestTable"],
            columns=["TestColumn"]
        )
        
        self.select_node = SemanticNode(
            id="select_test",
            node_type=NodeType.SELECT,
            description="Test select operation",
            tables=["TestTable"],
            columns=["TestColumn"]
        )
    
    def test_add_node(self):
        """Test adding nodes to DAG"""
        self.dag.add_node(self.filter_node)
        self.assertEqual(len(self.dag.nodes), 1)
        self.assertIn("filter_test", self.dag.nodes)
    
    def test_add_edge(self):
        """Test adding edges between nodes"""
        self.dag.add_node(self.filter_node)
        self.dag.add_node(self.select_node)
        
        self.dag.add_edge("filter_test", "select_test")
        self.assertEqual(len(self.dag.graph.edges()), 1)
    
    def test_topological_order(self):
        """Test topological ordering of nodes"""
        self.dag.add_node(self.filter_node)
        self.dag.add_node(self.select_node)
        self.dag.add_edge("filter_test", "select_test")
        
        order = self.dag.get_topological_order()
        self.assertEqual(order, ["filter_test", "select_test"])
    
    def test_cycle_prevention(self):
        """Test that cycles are prevented"""
        self.dag.add_node(self.filter_node)
        self.dag.add_node(self.select_node)
        
        self.dag.add_edge("filter_test", "select_test")
        
        # Adding reverse edge should raise error
        with self.assertRaises(ValueError):
            self.dag.add_edge("select_test", "filter_test")
    
    def test_execution_layers(self):
        """Test execution layer grouping"""
        node1 = SemanticNode("node1", NodeType.FILTER, "Test 1")
        node2 = SemanticNode("node2", NodeType.FILTER, "Test 2")
        node3 = SemanticNode("node3", NodeType.SELECT, "Test 3")
        
        self.dag.add_node(node1)
        self.dag.add_node(node2)
        self.dag.add_node(node3)
        
        # node1 and node2 can execute in parallel
        # node3 depends on both
        self.dag.add_edge("node1", "node3")
        self.dag.add_edge("node2", "node3")
        
        layers = self.dag.get_execution_layers()
        self.assertEqual(len(layers), 2)
        self.assertEqual(set(layers[0]), {"node1", "node2"})
        self.assertEqual(layers[1], ["node3"])
    
    def test_serialization(self):
        """Test DAG serialization and deserialization"""
        self.dag.add_node(self.filter_node)
        self.dag.add_node(self.select_node)
        self.dag.add_edge("filter_test", "select_test")
        
        # Test to_dict and from_dict
        dag_dict = self.dag.to_dict()
        restored_dag = SemanticDAG.from_dict(dag_dict)
        
        self.assertEqual(len(restored_dag.nodes), 2)
        self.assertEqual(len(restored_dag.graph.edges()), 1)
        self.assertEqual(restored_dag.query_id, "test_query")


class TestErrorTaxonomy(unittest.TestCase):
    """Test cases for Error Taxonomy functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.taxonomy = ErrorTaxonomy()
    
    def test_taxonomy_initialization(self):
        """Test that taxonomy is properly initialized"""
        self.assertGreater(len(self.taxonomy.error_patterns), 0)
        self.assertEqual(len(self.taxonomy.error_categories), 8)  # Number of categories
    
    def test_pattern_matching(self):
        """Test error pattern matching"""
        # Test ID string comparison error
        sql_with_error = "SELECT * FROM Employee WHERE EmpID = '123'"
        matches = self.taxonomy.find_matching_patterns(sql_with_error)
        
        # Should find the ID string comparison error
        pattern_names = [p.name for p in matches]
        self.assertIn("ID Column String Comparison", pattern_names)
    
    def test_error_analysis(self):
        """Test comprehensive error analysis"""
        problematic_sql = "SELECT Name, COUNT(*) FROM Employee WHERE EmpID = '123'"
        
        analysis = analyze_sql_errors(problematic_sql, self.taxonomy)
        
        self.assertGreater(analysis["total_issues"], 0)
        self.assertIn("patterns_matched", analysis)
        self.assertIn("risk_score", analysis)
        self.assertIn("recommended_actions", analysis)
    
    def test_high_severity_patterns(self):
        """Test high severity pattern detection"""
        high_patterns = self.taxonomy.get_high_severity_patterns()
        
        self.assertGreater(len(high_patterns), 0)
        for pattern in high_patterns:
            self.assertEqual(pattern.severity, "HIGH")
    
    def test_pattern_fixes(self):
        """Test that all patterns have suggested fixes"""
        for pattern in self.taxonomy.error_patterns:
            self.assertIsNotNone(pattern.common_fix)
            self.assertGreater(len(pattern.common_fix), 0)


class TestNodeTypes(unittest.TestCase):
    """Test cases for semantic node types"""
    
    def test_node_creation(self):
        """Test creating nodes of different types"""
        node_types = [
            NodeType.FILTER,
            NodeType.JOIN,
            NodeType.GROUP,
            NodeType.AGGREGATE,
            NodeType.SELECT,
            NodeType.ORDER
        ]
        
        for node_type in node_types:
            node = SemanticNode(
                id=f"test_{node_type.value}",
                node_type=node_type,
                description=f"Test {node_type.value} operation"
            )
            
            self.assertEqual(node.node_type, node_type)
            self.assertIsNotNone(node.description)
    
    def test_node_serialization(self):
        """Test node serialization"""
        node = SemanticNode(
            id="test_node",
            node_type=NodeType.FILTER,
            description="Test node",
            tables=["Table1"],
            columns=["Col1", "Col2"],
            conditions=["Col1 > 0"]
        )
        
        # Test to_dict and from_dict
        node_dict = node.to_dict()
        restored_node = SemanticNode.from_dict(node_dict)
        
        self.assertEqual(restored_node.id, node.id)
        self.assertEqual(restored_node.node_type, node.node_type)
        self.assertEqual(restored_node.tables, node.tables)
        self.assertEqual(restored_node.columns, node.columns)
        self.assertEqual(restored_node.conditions, node.conditions)


if __name__ == "__main__":
    # Run all tests
    unittest.main(verbosity=2)
