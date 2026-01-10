# 🔬 How DIVA-SQL Works: Step-by-Step Deep Dive

## 🎯 **DIVA-SQL Architecture: Multi-Agent Text-to-SQL System**

DIVA-SQL stands for **D**ecomposable, **I**nterpretable, **V**erifiable, **A**gent-based SQL generation. It uses **3 specialized AI agents** working together:

```
Natural Language Query
         ↓
   [DECOMPOSER AGENT]    ← Breaks query into semantic steps
         ↓
   [GENERATOR AGENT]     ← Generates SQL for each step  
         ↓
   [VERIFIER AGENT]      ← Validates and fixes SQL
         ↓
     Final SQL Result
```

---

## 🔄 **The Complete DIVA-SQL Process**

### **Phase 1: Semantic Decomposition** 🧠
**Agent:** `SemanticDecomposer`
**Input:** "Show employees with salary above their department average"
**Process:**
1. **Query Analysis**: Identifies query type, complexity, required operations
2. **Component Extraction**: Finds entities (employees, departments, salary)
3. **Dependency Mapping**: Determines operation order (need dept avg → compare with employee salary)
4. **DAG Creation**: Builds directed graph of semantic steps

**Output Example:**
```
Node 1: "Get all employees with their salaries and departments"
Node 2: "Calculate average salary per department" 
Node 3: "Compare each employee salary with their department average"
Node 4: "Filter employees above department average"
```

### **Phase 2: Iterative SQL Generation** ⚙️
**Agent:** `ClauseGenerator`  
**Process:** For each semantic node in execution order:

1. **Context Building**: Gathers previous SQL clauses and schema info
2. **Clause Generation**: Creates SQL fragment for current semantic step
3. **Immediate Verification**: Checks syntax and logic
4. **Retry Logic**: Fixes errors up to max iterations (3x)

**Example Generation for Node 2:**
```sql
-- Generated SQL clause for "Calculate average salary per department"
SELECT dept_id, AVG(salary) as avg_salary 
FROM employees 
GROUP BY dept_id
```

### **Phase 3: Verification & Validation** ✅
**Agent:** `VerificationAgent`
**Process:** For each generated clause:

1. **Syntax Validation**: Checks SQL syntax correctness
2. **Semantic Validation**: Ensures logic matches intent  
3. **Schema Compliance**: Verifies tables/columns exist
4. **Data Type Checking**: Confirms compatible operations
5. **Logic Verification**: Validates business logic

### **Phase 4: Final Composition** 🏗️
**Process:**
1. **Clause Integration**: Combines all verified clauses
2. **Query Optimization**: Applies SQL best practices
3. **Final Validation**: Last check of complete query
4. **Result Packaging**: Creates `DIVAResult` with metadata

---

## 🎯 **Real Example: "Employees Above Department Average"**

Let me trace through the actual process:

### **Step 1: Decomposition**
```python
# Input query analyzed and broken into semantic steps:
dag_nodes = [
    SemanticNode(id="base_data", type=NodeType.BASE_RELATION, 
                 description="Get employees with salary and department info"),
    SemanticNode(id="dept_avg", type=NodeType.AGGREGATION,
                 description="Calculate average salary per department"), 
    SemanticNode(id="comparison", type=NodeType.FILTER,
                 description="Compare employee salary with department average"),
    SemanticNode(id="result", type=NodeType.PROJECTION,
                 description="Select final result columns")
]
```

### **Step 2: Sequential Generation**
```python
# Node 1: Base relation
generated_sql_1 = """
SELECT e.emp_id, e.name, e.salary, e.dept_id, d.dept_name
FROM employees e
JOIN departments d ON e.dept_id = d.dept_id
"""

# Node 2: Aggregation (subquery)  
generated_sql_2 = """
SELECT dept_id, AVG(salary) as avg_salary
FROM employees
GROUP BY dept_id
"""

# Node 3: Comparison logic
generated_sql_3 = """
WHERE e.salary > dept_avg.avg_salary
"""
```

### **Step 3: Verification Results**
```python
verification_log = [
    {"node_id": "base_data", "status": "PASS", "confidence": 0.95},
    {"node_id": "dept_avg", "status": "PASS", "confidence": 0.98}, 
    {"node_id": "comparison", "status": "PASS", "confidence": 0.92},
    {"node_id": "result", "status": "PASS", "confidence": 0.96}
]
```

### **Step 4: Final Composition**
```sql
-- Final composed and optimized SQL:
SELECT e.name, e.position, d.dept_name, e.salary, dept_avg.avg_salary,
       ((e.salary - dept_avg.avg_salary) / dept_avg.avg_salary) * 100 as percent_above
FROM employees e
JOIN departments d ON e.dept_id = d.dept_id  
JOIN (
    SELECT dept_id, AVG(salary) as avg_salary
    FROM employees
    GROUP BY dept_id
) dept_avg ON e.dept_id = dept_avg.dept_id
WHERE e.salary > dept_avg.avg_salary
ORDER BY percent_above DESC
```

---

## 🔧 **Key Technical Components**

### **1. Semantic DAG (Directed Acyclic Graph)**
- **Nodes**: Individual semantic operations 
- **Edges**: Dependencies between operations
- **Execution Order**: Topological sort ensures correct sequence
- **Types**: BASE_RELATION, FILTER, AGGREGATION, JOIN, PROJECTION

### **2. Multi-Agent Coordination**
```python
class DIVASQLPipeline:
    def __init__(self, llm_client, model_name):
        self.decomposer = SemanticDecomposer(llm_client, model_name)
        self.generator = ClauseGenerator(llm_client, model_name)  
        self.verifier = VerificationAgent(llm_client, model_name)
```

### **3. Error Handling & Retries**
- **Max Iterations**: 3 attempts per clause
- **Verification Feedback**: Specific error messages for fixes
- **Partial Success**: Returns best effort even if some steps fail
- **Confidence Scoring**: Each verification includes confidence level

### **4. LLM Integration (Gemini)**
```python
# Our custom Gemini client provides OpenAI-compatible interface
client = create_gemini_client(model_name="gemini-2.0-flash")
pipeline = DIVASQLPipeline(client, model_name="gemini-2.0-flash")
```

---

## 📊 **How We Got Those Results**

### **Database Creation Process:**
1. **Schema Design**: Realistic employee/department tables
2. **Data Population**: 29 employees across 7 departments  
3. **Salary Distribution**: Varied by department (Data Science highest)

### **Query Execution Process:**
1. **DIVA-SQL Processing**: Generated the complex SQL with joins/subqueries
2. **Database Execution**: Ran SQL against SQLite database
3. **Result Formatting**: Processed and displayed results

### **The Magic Happens Here:**
```python
# DIVA-SQL generates this complex query automatically:
result = pipeline.generate_sql(
    "Show employees with salary above their department average",
    schema
)

# Then we execute against real data:
cursor.execute(result.final_sql)
results = cursor.fetchall()
```

---

## 🎯 **Why DIVA-SQL is Powerful**

1. **Decomposable**: Breaks complex queries into manageable steps
2. **Interpretable**: Each step has clear semantic meaning  
3. **Verifiable**: Every SQL clause is validated before use
4. **Robust**: Handles failures gracefully with retries
5. **Scalable**: Works with any LLM (OpenAI, Anthropic, Gemini)

**Bottom Line**: DIVA-SQL doesn't just generate SQL - it *reasons* through the problem step-by-step, like a human SQL expert would! 🚀
