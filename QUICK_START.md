# DIVA-SQL Quick Reference

## Quick Links

- **Implementation Summary**: `IMPLEMENTATION_SUMMARY.md`
- **Complete Guide**: `PRACTICAL_IMPLEMENTATION_GUIDE.md`
- **Implementation Plan**: `IMPLEMENTATION_PLAN.md`
- **Simple Demo**: `python3 demo_simple.py`

## What's New

### 🎯 Template Library (53 Templates)
**Location**: `src/templates/`

```python
from src.templates import TemplateLibrary, TemplateSelector

# Get template
library = TemplateLibrary()
template = library.get_template("FT002")

# Instantiate
sql = template.instantiate({
    "columns": "*", "table": "employees",
    "column": "salary", "operator": ">", "value": "50000"
})
```

**Categories**:
- Basic SELECT (10) | Filtering (8) | Joins (12)
- Aggregation (8) | Grouping (5) | Subqueries (6) | CTEs (4)

### 🔍 Three-Stage Verification
**Location**: `src/verification/`

```python
from src.verification import FeedbackLoop

loop = FeedbackLoop(schema, enable_auto_fix=True)
result = loop.verify_sql(sql, sample_data=data)
print(loop.generate_feedback_report(result))
```

**Stages**:
1. **Syntax** - SQL grammar, parentheses, clause order
2. **Semantic** - Schema validation, table/column existence
3. **Execution** - Runtime testing, performance validation

### ⚡ Performance Monitoring
**Location**: `src/monitoring/`

```python
from src.monitoring import PerformanceTracker, QueryComplexity

tracker = PerformanceTracker()
id = tracker.start_tracking("q1", QueryComplexity.SIMPLE)
# ... do work ...
metric = tracker.end_tracking(id)
```

**Targets**: Simple 2.3s | Complex 5.8s

## File Structure

```
src/
├── templates/          # NEW: 53 SQL templates
│   ├── template_library.py
│   └── template_selector.py
├── verification/       # NEW: 3-stage verification
│   ├── syntax_verifier.py
│   ├── semantic_verifier.py
│   ├── execution_verifier.py
│   └── feedback_loop.py
└── monitoring/         # NEW: Performance tracking
    └── performance_tracker.py
```

## Common Tasks

### Generate SQL from Template
```python
from src.templates import TemplateLibrary

library = TemplateLibrary()
template = library.get_template("BS002")  # Select specific columns
sql = template.instantiate({"columns": "name, salary", "table": "employees"})
```

### Verify SQL (All Stages)
```python
from src.verification import FeedbackLoop

feedback_loop = FeedbackLoop(schema)
result = feedback_loop.verify_sql(sql, sample_data=data)

if result.overall_valid:
    print("✓ All stages passed!")
else:
    for fb in result.feedback:
        print(f"{fb.severity.value}: {fb.message}")
```

### Track Performance
```python
from src.monitoring import PerformanceTracker, QueryComplexity

tracker = PerformanceTracker()
id = tracker.start_tracking("query_001", QueryComplexity.SIMPLE)

tracker.start_stage(id, "decomposition")
# ... work ...
tracker.end_stage(id, "decomposition")

metric = tracker.end_tracking(id)
print(f"Total: {metric.total_time_ms:.2f}ms")
```

## Template IDs Quick Reference

### Basic SELECT
- `BS001` - Select all
- `BS002` - Select specific columns
- `BS003` - Select distinct
- `BS006` - With LIMIT
- `BS008` - With ORDER BY

### Filtering
- `FT001` - WHERE equality
- `FT002` - WHERE comparison
- `FT003` - WHERE AND
- `FT005` - WHERE IN
- `FT006` - WHERE BETWEEN

### Joins
- `JN001` - INNER JOIN
- `JN002` - LEFT JOIN
- `JN003` - RIGHT JOIN
- `JN006` - Self JOIN
- `JN007` - Multiple JOINs

### Aggregation
- `AG001` - COUNT all
- `AG003` - SUM
- `AG004` - AVG
- `AG005` - MIN/MAX

### Grouping
- `GP001` - Simple GROUP BY
- `GP002` - GROUP BY with HAVING

### Subqueries
- `SQ001` - Subquery in WHERE
- `SQ003` - Correlated subquery
- `SQ004` - EXISTS subquery

### CTEs
- `CT001` - Simple CTE
- `CT002` - Multiple CTEs
- `CT003` - Recursive CTE

## Error Types

### Syntax Errors
- Invalid syntax
- Unbalanced parentheses
- Invalid keyword order
- Missing clause

### Semantic Errors
- Table not found
- Column not found
- Type mismatch
- Invalid JOIN

### Execution Errors
- Runtime error
- Timeout
- Empty result (warning)
- Performance warning

## Performance Targets

| Query Type | Target | Metric |
|------------|--------|--------|
| Simple     | 2.3s   | Average |
| Complex    | 5.8s   | Average |

## Demo Commands

```bash
# Simple overview
python3 demo_simple.py

# Full demo (requires dependencies)
python3 demo_practical_implementation.py
```

## Research Requirements Status

✅ Environment Setup (Python 3.9, Gemini 2.0 Flash, sqlparse, SQLAlchemy)
✅ Semantic Decomposer (existing, uses Gemini)
✅ Template-Based Generator (53 templates)
✅ Three-Stage Verification (syntax → semantic → execution)
✅ Performance Monitoring (2.3s/5.8s targets)
⏳ Training Data (12,500 pairs - future)

## Next Steps

1. **Integration** - Connect new components to existing pipeline
2. **Training** - Prepare 12,500 query-graph pairs
3. **Evaluation** - Test on Spider and BIRD benchmarks
4. **Optimization** - Fine-tune for performance targets

## Support

- Full documentation: `PRACTICAL_IMPLEMENTATION_GUIDE.md`
- Implementation details: `IMPLEMENTATION_SUMMARY.md`
- Roadmap: `IMPLEMENTATION_PLAN.md`
