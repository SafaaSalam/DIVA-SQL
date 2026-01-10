# DIVA-SQL Quick Reference Guide

## 🚀 Getting Started

### 1. Setup Environment
```bash
# Install dependencies
python3 -m pip install -r requirements.txt

# Or use the setup script
python3 setup.py

# Configure API key
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### 2. Run Demo
```bash
# Run the main demo
python3 run_diva_gemini_demo.py
```

### 3. Run Tests
```bash
# Run all tests
python3 -m pytest tests/ -v

# Run specific test
python3 -m pytest tests/test_core.py -v
```

## 📁 Project Structure

```
DIVA-SQL/
├── src/                    # Core implementation
│   ├── agents/            # Three specialized agents
│   ├── core/              # Pipeline and DAG
│   └── utils/             # Utilities and helpers
├── evaluation/            # Evaluation framework
├── tests/                 # Unit tests
├── notebooks/             # Jupyter demos
├── data/                  # Benchmark datasets
├── results/               # Evaluation results
└── docs/                  # Documentation
```

## 🎯 Core Components

### Semantic Decomposer Agent
**File**: `src/agents/decomposer.py`
**Purpose**: Breaks down NL queries into semantic DAG
**Key Method**: `decompose_query(query, schema)`

### Template-Based Generator
**File**: `src/agents/generator.py`
**Purpose**: Generates SQL using 53 pre-defined templates
**Key Method**: `generate_sql(dag_node, context)`

### Three-Stage Verifier
**File**: `src/agents/verifier.py`
**Purpose**: Syntax, semantic, and execution verification
**Key Method**: `verify_sql(sql, schema, database)`

### Main Pipeline
**File**: `src/core/pipeline.py`
**Purpose**: Orchestrates the entire DIVA-SQL process
**Key Method**: `generate_sql(query, schema)`

## 🔧 Common Tasks

### Run Evaluation
```bash
# Run full evaluation
python3 evaluation/run_experiments.py --benchmark sample

# Run academic benchmark
python3 evaluation/academic_benchmark.py

# Run mini test
python3 evaluation/mini_test.py
```

### Work with Notebooks
```bash
# Start Jupyter
jupyter notebook notebooks/diva_sql_demo.ipynb
```

### Generate Results
```bash
# Results will be saved in results/ directory
python3 evaluation/run_experiments.py --output-dir results/
```

## 📊 Evaluation Metrics

- **EX (Execution Accuracy)**: Percentage of queries that execute correctly
- **EM (Exact Match)**: Percentage of queries that match exactly
- **VES (Valid Efficiency Score)**: Efficiency of valid queries

## 🔍 Key Files

| File | Purpose |
|------|---------|
| `run_diva_gemini_demo.py` | Main demo script |
| `setup.py` | Environment setup |
| `requirements.txt` | Python dependencies |
| `.env.example` | Environment variables template |
| `README.md` | Main documentation |
| `HOW_DIVA_SQL_WORKS.md` | Technical explanation |

## 🛠️ Development Workflow

### 1. Make Changes
Edit files in `src/` directory

### 2. Test Changes
```bash
python3 -m pytest tests/ -v
```

### 3. Run Demo
```bash
python3 run_diva_gemini_demo.py
```

### 4. Evaluate
```bash
python3 evaluation/run_experiments.py
```

## 🐛 Troubleshooting

### API Key Issues
```bash
# Check .env file exists
ls -la .env

# Verify API key is set
cat .env | grep GOOGLE_API_KEY
```

### Import Errors
```bash
# Ensure you're in the project root
cd /Users/apple/Desktop/DIVA-SQL

# Reinstall dependencies
python3 -m pip install -r requirements.txt
```

### Database Errors
```bash
# Database files are auto-generated
# If issues occur, they will be recreated
```

## 📚 Documentation

- **Main README**: `README.md` - Overview and usage
- **Technical Guide**: `HOW_DIVA_SQL_WORKS.md` - How it works
- **Evaluation README**: `evaluation/README.md` - Evaluation details
- **Cleanup Analysis**: `CLEANUP_ANALYSIS.md` - What was cleaned up
- **Optimization Summary**: `OPTIMIZATION_SUMMARY.md` - Optimization results

## 🎓 Research Components

### RQ1: Accuracy Evaluation
**Location**: `evaluation/benchmark_eval.py`
**Metrics**: EX, EM, VES
**Datasets**: Spider, BIRD

### RQ2: Interpretability Study
**Location**: `notebooks/diva_sql_demo.ipynb`
**Features**: DAG visualization, step-by-step breakdown

### RQ3: Error Prevention Analysis
**Location**: `src/utils/error_taxonomy.py`
**Coverage**: 20+ error patterns, 8 categories

## 🔐 Environment Variables

Required in `.env` file:
```bash
GOOGLE_API_KEY=your_gemini_api_key_here
```

Optional:
```bash
DATABASE_PATH=path/to/database.db
LOG_LEVEL=INFO
```

## 📦 Dependencies

Core libraries (from `requirements.txt`):
- `google-generativeai` - Gemini 2.0 Flash API
- `sqlparse` - SQL parsing and formatting
- `SQLAlchemy` - Database abstraction
- `sqlite3` - SQLite engine (built-in)
- `psycopg2` - PostgreSQL engine

## 🎯 Next Steps

1. ✅ Review the cleanup results
2. ⏳ Test core functionality
3. ⏳ Run evaluation benchmarks
4. ⏳ Explore the demo notebook
5. ⏳ Read the technical documentation

## 🗑️ Cleanup

### Remove Backup (After Verification)
```bash
# Once you've verified everything works
rm -rf backup_20260107_225654

# Optionally remove cleanup scripts
rm cleanup.py cleanup.sh CLEANUP_ANALYSIS.md
```

## 💡 Tips

- Use `python3` instead of `python` on macOS
- Keep `.env` file secure (it's gitignored)
- Database files are auto-generated (don't commit them)
- Results directory is for temporary outputs
- All core logic is in `src/` directory

## 📞 Support

- Check `README.md` for detailed documentation
- Review `HOW_DIVA_SQL_WORKS.md` for technical details
- Explore `notebooks/diva_sql_demo.ipynb` for examples
- Check `evaluation/README.md` for evaluation guide

---

**Last Updated**: 2026-01-07
**Version**: Optimized Structure
**Status**: Production Ready ✅
