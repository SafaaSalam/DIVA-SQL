# DIVA-SQL: Decomposable, Interpretable, and Verifiable Agents for Text-to-SQL

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A novel multi-agent framework for Text-to-SQL generation that addresses the "black box problem" of current LLM-based approaches through semantic decomposition, step-by-step verification, and interpretable query generation.

## ⭐ NEW: Practical Implementation Complete!

**The complete DIVA-SQL framework has been implemented with all research requirements:**

- ✅ **53 SQL Templates** - Comprehensive template library covering basic to complex operations
- ✅ **Three-Stage Verification** - Syntax → Semantic → Execution with auto-fix
- ✅ **Performance Monitoring** - Latency tracking (2.3s simple, 5.8s complex targets)
- ✅ **Feedback Loop** - Diagnostic reporting with localized repair

**📚 Quick Links:**
- **[Implementation Complete](docs/implementation/IMPLEMENTATION_COMPLETE.md)** - Visual overview with diagrams
- **[Quick Start Guide](QUICK_START.md)** - Get started in 5 minutes
- **[Practical Guide](docs/implementation/PRACTICAL_IMPLEMENTATION_GUIDE.md)** - Complete documentation
- **[All Documentation](docs/README.md)** - Complete documentation index
- **[Demo](demos/demo_simple.py)** - Run: `python3 demos/demo_simple.py`

**🎯 What's New:**
- `src/templates/` - 53 SQL templates with intelligent selection
- `src/verification/` - Three-stage verification system
- `src/monitoring/` - Performance tracking with research targets


## 🎯 Overview

DIVA-SQL introduces a three-agent architecture that transforms natural language queries into SQL through interpretable semantic decomposition:

- **🧩 Semantic Decomposer Agent**: Breaks down complex NL queries into semantic Directed Acyclic Graphs (DAGs)
- **⚙️ Clause Generator Agent**: Generates SQL clauses from individual semantic components  
- **✅ Verification & Alignment Agent**: Provides in-line verification and error correction

This approach enables:
- **Higher accuracy** on complex queries through structured decomposition
- **Full interpretability** via semantic DAGs and verification traces
- **Error prevention** through comprehensive in-line verification

## 🏗️ Architecture

```
Natural Language Query
          ↓
    [Decomposer Agent]
          ↓
    Semantic DAG
          ↓
    [Generator Agent] ←→ [Verifier Agent]
          ↓
    Final SQL Query
```

### Key Components

1. **Semantic DAG Representation**: Captures query semantics as interpretable graph structures
2. **Multi-Agent Pipeline**: Specialized agents for decomposition, generation, and verification
3. **Error Taxonomy**: Comprehensive classification of SQL generation errors
4. **Evaluation Framework**: Tools for benchmarking against state-of-the-art baselines

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/diva-sql.git
cd diva-sql

# Run automated setup
python setup.py

# Or manual setup:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Basic Usage

```python
from src.core.pipeline import DIVASQLPipeline
import openai

# Initialize the pipeline
client = openai.OpenAI(api_key="your-api-key")
pipeline = DIVASQLPipeline(client)

# Define your database schema
schema = {
    "employees": ["id", "name", "department_id", "salary", "hire_date"],
    "departments": ["id", "name", "manager_id"]
}

# Generate SQL from natural language
result = pipeline.generate_sql(
    query="What are the names of departments with more than 10 employees?",
    schema=schema
)

print("Generated SQL:", result.sql)
print("Confidence:", result.confidence)
print("Semantic DAG:", result.semantic_dag)
```

### Interactive Demo

```bash
# Launch interactive mode
python -m src.core.pipeline --interactive

# Or explore the Jupyter notebook
jupyter notebook notebooks/diva_sql_demo.ipynb
```

## 📊 Research Evaluation

DIVA-SQL includes a comprehensive evaluation framework for research purposes:

```bash
# Run full research evaluation
python evaluation/run_experiments.py --benchmark sample

# Evaluate on BIRD benchmark (requires setup)
python evaluation/run_experiments.py --benchmark bird --output-dir results/bird

# Generate research report
python evaluation/run_experiments.py --benchmark sample --output-dir results
```

### Research Questions Addressed

1. **RQ1: Accuracy** - Does DIVA-SQL achieve higher execution accuracy on complex queries?
2. **RQ2: Interpretability** - Can semantic DAGs improve user understanding and debugging?
3. **RQ3: Error Prevention** - How effective is in-line verification at preventing SQL errors?

## 🎯 Key Features

### Semantic Decomposition
- Transforms complex queries into interpretable DAG structures
- Handles nested subqueries, multiple joins, and complex aggregations
- Preserves semantic relationships between query components

### In-Line Verification
- **Schema Alignment**: Validates table/column references
- **Syntax Checking**: Ensures SQL syntax correctness
- **Semantic Consistency**: Verifies logical query structure
- **Error Prevention**: Catches 20+ error patterns across 8 categories

### Interpretability
- Visual DAG representation of query semantics
- Step-by-step verification logs
- Confidence scoring for each generated component
- Human-readable explanations of generated SQL

## 📁 Project Structure

```
diva-sql/
├── src/
│   ├── core/                    # Core pipeline and DAG implementation
│   │   ├── pipeline.py          # Main DIVA-SQL pipeline
│   │   └── semantic_dag.py      # Semantic DAG data structures
│   ├── agents/                  # Three specialized agents
│   │   ├── decomposer.py        # Semantic Decomposer Agent
│   │   ├── generator.py         # Clause Generator Agent
│   │   └── verifier.py          # Verification & Alignment Agent
│   └── utils/                   # Utilities and error taxonomy
│       ├── error_taxonomy.py    # Comprehensive error classification
│       └── prompts.py          # LLM prompt templates
├── evaluation/                  # Research evaluation framework
│   ├── framework.py            # Benchmarking and comparison tools
│   └── run_experiments.py     # Full research evaluation script
├── tests/                      # Unit tests
├── notebooks/                  # Demo and analysis notebooks
├── configs/                    # Configuration files
└── requirements.txt           # Dependencies
```

## 🔬 Research Foundation

This implementation is based on comprehensive research addressing three key research questions:

### RQ1: Accuracy Evaluation
Comparison with state-of-the-art baselines including:
- Zero-shot GPT-4/Claude
- DIN-SQL (Few-shot)
- MAC-SQL (Multi-agent)

**Evaluation Metrics:**
- Execution Accuracy (EX)
- Valid Efficiency Score (VES) 
- Query complexity analysis

### RQ2: Interpretability Study
Human subject evaluation comparing:
- Traditional SQL generation interfaces
- DIVA-SQL semantic DAG interface

**Measured Aspects:**
- Task success rate for debugging incorrect SQL
- Time to identify and fix errors
- User confidence and understanding ratings

### RQ3: Error Prevention Analysis
Systematic evaluation of verification effectiveness:
- Error types caught by in-line verification
- Reduction in common SQL mistakes
- Impact on overall system accuracy

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test modules
python -m pytest tests/test_core.py -v
python -m pytest tests/test_agents.py -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html
```

## 📈 Benchmarking

DIVA-SQL supports evaluation on standard Text-to-SQL benchmarks:

- **BIRD**: Cross-domain, complex SQL queries
- **Spider**: Multi-domain benchmark
- **Custom datasets**: Your own evaluation data

```python
from evaluation.framework import BenchmarkEvaluator, DIVASQLSystem

# Set up evaluation
evaluator = BenchmarkEvaluator("path/to/database.db")
system = DIVASQLSystem(llm_client, model_name="gpt-4")

# Run evaluation
results = evaluator.evaluate_system(system, benchmark_data, schema)
print(f"Execution Accuracy: {results.execution_accuracy:.3f}")
print(f"Average VES: {results.avg_valid_efficiency_score:.3f}")
```

## 🤝 Contributing

We welcome contributions! Areas where you can help:

1. **Additional Baselines**: Implement more comparison systems
2. **Error Patterns**: Extend the error taxonomy with new patterns
3. **Evaluation**: Add support for more benchmarks
4. **Optimizations**: Improve performance and efficiency
5. **Documentation**: Enhance examples and tutorials

Please see `CONTRIBUTING.md` for detailed guidelines.

## 📄 Citation

If you use DIVA-SQL in your research, please cite:

```bibtex
@article{diva-sql-2024,
  title={DIVA-SQL: Decomposable, Interpretable, and Verifiable Agents for Text-to-SQL Generation},
  author={[Authors]},
  journal={[Journal]},
  year={2024}
}
```

## 📧 Contact

For questions about the research or implementation:
- Open an issue on GitHub
- Email: [your-email@university.edu]

## 📜 License

This project is licensed under the MIT License - see the `LICENSE` file for details.

## 🙏 Acknowledgments

- Built on top of OpenAI GPT and Anthropic Claude APIs
- Inspired by research in interpretable AI and multi-agent systems
- Evaluation framework adapted from BIRD and Spider benchmarks

---

**DIVA-SQL** - Making Text-to-SQL generation interpretable, verifiable, and more accurate through multi-agent decomposition.

## Abstract

DIVA-SQL is a novel multi-agent framework that reframes Text-to-SQL as a transparent and verifiable reasoning process. Unlike monolithic approaches, DIVA-SQL employs three specialized agents:

1. **Semantic Decomposer Agent**: Breaks down natural language queries into interpretable DAGs
2. **Clause Generator Agent**: Generates SQL clauses for individual semantic steps
3. **Verification & Alignment Agent**: Provides in-line verification and error correction

## Key Features

- **Proactive Error Prevention**: Catches and corrects errors during generation
- **Enhanced Interpretability**: Provides transparent reasoning through semantic DAGs
- **Multi-step Verification**: Schema alignment, execution sanity, and error pattern detection
- **Human-in-the-loop**: Enables targeted corrections when verification fails

## Project Structure

```
DIVA-SQL/
├── src/
│   ├── agents/
│   │   ├── decomposer.py        # Semantic Decomposer Agent
│   │   ├── generator.py         # Clause Generator Agent
│   │   └── verifier.py         # Verification & Alignment Agent
│   ├── core/
│   │   ├── pipeline.py         # Main DIVA-SQL pipeline
│   │   ├── semantic_dag.py     # DAG representation and operations
│   │   └── database.py         # Database connection and operations
│   └── utils/
│       ├── error_taxonomy.py   # Error classification and patterns
│       ├── prompts.py          # Agent-specific prompts
│       └── metrics.py          # Evaluation metrics (EX, VES)
├── evaluation/
│   ├── baselines/              # Baseline implementations
│   ├── datasets/               # BIRD, Spider dataset handlers
│   ├── experiments/            # Experimental configurations
│   └── human_study/            # User study implementation
├── tests/
├── configs/
└── notebooks/                  # Analysis and visualization
```

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```python
from src.core.pipeline import DIVASQLPipeline

# Initialize the pipeline
diva = DIVASQLPipeline()

# Generate SQL from natural language
result = diva.generate_sql(
    query="What are the names of departments with more than 10 employees hired after 2022?",
    database_schema=schema
)

print(f"Generated SQL: {result.sql}")
print(f"Semantic DAG: {result.semantic_dag}")
print(f"Verification Status: {result.verification_log}")
```

## Research Questions

- **RQ1 (Accuracy)**: Does DIVA-SQL achieve higher execution accuracy on complex queries compared to SOTA baselines?
- **RQ2 (Interpretability)**: Does the decomposed output enable more effective error identification and correction?
- **RQ3 (Error Prevention)**: How effective is in-line verification compared to post-hoc repair methods?

## Evaluation

The framework is evaluated on:
- **BIRD Benchmark**: Complex, realistic database queries
- **Spider Benchmark**: Standard generalizability testing
- **Human Study**: Interpretability and trust assessment

## Citation

```bibtex
@article{diva-sql-2025,
  title={DIVA-SQL: Decomposable, Interpretable, and Verifiable Agents for Text-to-SQL Generation},
  author={[Your Name]},
  journal={[Target Venue]},
  year={2025}
}
```
