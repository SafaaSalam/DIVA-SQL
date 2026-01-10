#!/bin/bash

# DIVA-SQL Cleanup Script
# This script removes unnecessary files and folders to optimize the project structure

echo "🧹 DIVA-SQL Cleanup Script"
echo "=========================="
echo ""

# Create backup directory
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
echo "📦 Creating backup directory: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# Function to safely remove files
safe_remove() {
    if [ -f "$1" ]; then
        echo "  ❌ Removing: $1"
        mv "$1" "$BACKUP_DIR/" 2>/dev/null || rm "$1"
    fi
}

# Function to safely remove directories
safe_remove_dir() {
    if [ -d "$1" ]; then
        echo "  ❌ Removing directory: $1"
        mv "$1" "$BACKUP_DIR/" 2>/dev/null || rm -rf "$1"
    fi
}

echo ""
echo "1️⃣  Removing redundant test files..."
safe_remove "basic_test.py"
safe_remove "minimal_test.py"
safe_remove "simple_query_test.py"
safe_remove "quick_complex_test.py"
safe_remove "test_complex_queries.py"
safe_remove "test_gemini_2_flash.py"
safe_remove "test_gemini_basic.py"
safe_remove "test_gemini_real_data.py"
safe_remove "test_specific_query.py"

echo ""
echo "2️⃣  Removing temporary database files..."
safe_remove "demo_database.db"
safe_remove "salary_analysis.db"
safe_remove "test_departments.db"

echo ""
echo "3️⃣  Removing redundant documentation files..."
safe_remove "GEMINI_QUICKSTART.md"
safe_remove "GEMINI_READY.md"
safe_remove "SUCCESS_REPORT.md"
safe_remove "QUERY_RESULTS_DEMO.md"
safe_remove "academic_benchmark_README.md"
safe_remove "benchmark_instructions.md"

echo ""
echo "4️⃣  Removing redundant scripts..."
safe_remove "demonstrate_process.py"
safe_remove "final_results.py"
safe_remove "show_results.py"
safe_remove "trace_results.py"

echo ""
echo "5️⃣  Removing redundant shell scripts..."
safe_remove "run_academic_benchmark.sh"
safe_remove "run_benchmark.sh"
safe_remove "run_benchmark_with_rate_limit.sh"
safe_remove "run_mini_test.sh"
safe_remove "run_paper_benchmark.sh"
safe_remove "run_synthetic_benchmark.sh"
safe_remove "setup_api_key.sh"
safe_remove "setup_gemini.sh"

echo ""
echo "6️⃣  Removing unnecessary package file..."
safe_remove "package.json"

echo ""
echo "7️⃣  Removing macOS system files..."
find . -name ".DS_Store" -type f -delete 2>/dev/null
echo "  ❌ Removed all .DS_Store files"

echo ""
echo "8️⃣  Cleaning up old results..."
safe_remove "results/benchmark_results.csv"
safe_remove "results/benchmark_summary.json"
safe_remove "results/comparison_table.tex"
safe_remove "results/paper_benchmark_results.json"
safe_remove "results/paper_table.tex"
safe_remove "results/test.txt"
safe_remove_dir "results/paper_results_20250828_185937"
safe_remove_dir "results/paper_results_20250828_190338"

echo ""
echo "9️⃣  Creating .gitignore file..."
cat > .gitignore << 'EOF'
# Python
*.pyc
*.pyo
*.pyd
__pycache__/
*.so
*.egg
*.egg-info/
dist/
build/
.pytest_cache/
.coverage
htmlcov/

# Virtual Environment
.venv/
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# macOS
.DS_Store
.AppleDouble
.LSOverride

# Environment Variables
.env

# Database Files
*.db
*.sqlite
*.sqlite3

# Results and Logs
results/*.csv
results/*.json
results/*.tex
results/paper_results_*/
results/benchmark_*/
*.log

# Temporary Files
*.tmp
*.bak
backup_*/

# Jupyter Notebook
.ipynb_checkpoints/
*.ipynb_checkpoints

# Distribution
*.tar.gz
*.zip
EOF
echo "  ✅ Created .gitignore"

echo ""
echo "🔟 Creating consolidated documentation structure..."
mkdir -p docs

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📊 Summary:"
echo "  - Removed redundant test files (9 files)"
echo "  - Removed temporary databases (3 files)"
echo "  - Removed redundant documentation (6 files)"
echo "  - Removed redundant scripts (4 files)"
echo "  - Removed redundant shell scripts (8 files)"
echo "  - Removed package.json (1 file)"
echo "  - Cleaned up old results (8 items)"
echo "  - Created .gitignore"
echo ""
echo "💾 Backup saved in: $BACKUP_DIR"
echo "   (You can delete this folder if everything works correctly)"
echo ""
echo "🎯 Next steps:"
echo "  1. Review the changes"
echo "  2. Test the core functionality: python run_diva_gemini_demo.py"
echo "  3. Run tests: python -m pytest tests/"
echo "  4. If everything works, delete the backup folder"
echo ""
