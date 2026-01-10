#!/usr/bin/env python3
"""
DIVA-SQL Cleanup Script
This script removes unnecessary files and folders to optimize the project structure.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

class DIVASQLCleanup:
    def __init__(self, project_root=None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent
        self.backup_dir = self.project_root / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.removed_count = {
            'test_files': 0,
            'databases': 0,
            'documentation': 0,
            'scripts': 0,
            'shell_scripts': 0,
            'other': 0,
            'results': 0
        }
    
    def create_backup_dir(self):
        """Create backup directory for safety"""
        self.backup_dir.mkdir(exist_ok=True)
        print(f"📦 Creating backup directory: {self.backup_dir.name}")
    
    def safe_remove(self, file_path, category='other'):
        """Safely remove a file by moving it to backup"""
        full_path = self.project_root / file_path
        if full_path.exists() and full_path.is_file():
            try:
                # Create subdirectory in backup if needed
                backup_subdir = self.backup_dir / full_path.parent.relative_to(self.project_root)
                backup_subdir.mkdir(parents=True, exist_ok=True)
                
                # Move file to backup
                shutil.move(str(full_path), str(backup_subdir / full_path.name))
                print(f"  ❌ Removed: {file_path}")
                self.removed_count[category] += 1
                return True
            except Exception as e:
                print(f"  ⚠️  Error removing {file_path}: {e}")
                return False
        return False
    
    def safe_remove_dir(self, dir_path, category='other'):
        """Safely remove a directory by moving it to backup"""
        full_path = self.project_root / dir_path
        if full_path.exists() and full_path.is_dir():
            try:
                shutil.move(str(full_path), str(self.backup_dir / full_path.name))
                print(f"  ❌ Removed directory: {dir_path}")
                self.removed_count[category] += 1
                return True
            except Exception as e:
                print(f"  ⚠️  Error removing {dir_path}: {e}")
                return False
        return False
    
    def remove_test_files(self):
        """Remove redundant test files from root directory"""
        print("\n1️⃣  Removing redundant test files...")
        test_files = [
            'basic_test.py',
            'minimal_test.py',
            'simple_query_test.py',
            'quick_complex_test.py',
            'test_complex_queries.py',
            'test_gemini_2_flash.py',
            'test_gemini_basic.py',
            'test_gemini_real_data.py',
            'test_specific_query.py'
        ]
        for file in test_files:
            self.safe_remove(file, 'test_files')
    
    def remove_databases(self):
        """Remove temporary database files"""
        print("\n2️⃣  Removing temporary database files...")
        db_files = [
            'demo_database.db',
            'salary_analysis.db',
            'test_departments.db'
        ]
        for file in db_files:
            self.safe_remove(file, 'databases')
    
    def remove_documentation(self):
        """Remove redundant documentation files"""
        print("\n3️⃣  Removing redundant documentation files...")
        doc_files = [
            'GEMINI_QUICKSTART.md',
            'GEMINI_READY.md',
            'SUCCESS_REPORT.md',
            'QUERY_RESULTS_DEMO.md',
            'academic_benchmark_README.md',
            'benchmark_instructions.md'
        ]
        for file in doc_files:
            self.safe_remove(file, 'documentation')
    
    def remove_scripts(self):
        """Remove redundant Python scripts"""
        print("\n4️⃣  Removing redundant scripts...")
        script_files = [
            'demonstrate_process.py',
            'final_results.py',
            'show_results.py',
            'trace_results.py'
        ]
        for file in script_files:
            self.safe_remove(file, 'scripts')
    
    def remove_shell_scripts(self):
        """Remove redundant shell scripts"""
        print("\n5️⃣  Removing redundant shell scripts...")
        shell_files = [
            'run_academic_benchmark.sh',
            'run_benchmark.sh',
            'run_benchmark_with_rate_limit.sh',
            'run_mini_test.sh',
            'run_paper_benchmark.sh',
            'run_synthetic_benchmark.sh',
            'setup_api_key.sh',
            'setup_gemini.sh'
        ]
        for file in shell_files:
            self.safe_remove(file, 'shell_scripts')
    
    def remove_package_json(self):
        """Remove unnecessary package.json"""
        print("\n6️⃣  Removing unnecessary package file...")
        self.safe_remove('package.json', 'other')
    
    def remove_ds_store(self):
        """Remove macOS .DS_Store files"""
        print("\n7️⃣  Removing macOS system files...")
        count = 0
        for ds_store in self.project_root.rglob('.DS_Store'):
            try:
                ds_store.unlink()
                count += 1
            except Exception as e:
                print(f"  ⚠️  Error removing {ds_store}: {e}")
        print(f"  ❌ Removed {count} .DS_Store files")
    
    def clean_results(self):
        """Clean up old results directory"""
        print("\n8️⃣  Cleaning up old results...")
        result_files = [
            'results/benchmark_results.csv',
            'results/benchmark_summary.json',
            'results/comparison_table.tex',
            'results/paper_benchmark_results.json',
            'results/paper_table.tex',
            'results/test.txt'
        ]
        for file in result_files:
            self.safe_remove(file, 'results')
        
        # Remove old timestamped directories
        result_dirs = [
            'results/paper_results_20250828_185937',
            'results/paper_results_20250828_190338'
        ]
        for dir_path in result_dirs:
            self.safe_remove_dir(dir_path, 'results')
    
    def create_gitignore(self):
        """Create comprehensive .gitignore file"""
        print("\n9️⃣  Creating .gitignore file...")
        gitignore_content = """# Python
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
"""
        gitignore_path = self.project_root / '.gitignore'
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)
        print("  ✅ Created .gitignore")
    
    def create_docs_structure(self):
        """Create consolidated documentation structure"""
        print("\n🔟 Creating consolidated documentation structure...")
        docs_dir = self.project_root / 'docs'
        docs_dir.mkdir(exist_ok=True)
        print("  ✅ Created docs/ directory")
    
    def print_summary(self):
        """Print cleanup summary"""
        total_removed = sum(self.removed_count.values())
        print("\n✅ Cleanup complete!")
        print("\n📊 Summary:")
        print(f"  - Removed redundant test files: {self.removed_count['test_files']} files")
        print(f"  - Removed temporary databases: {self.removed_count['databases']} files")
        print(f"  - Removed redundant documentation: {self.removed_count['documentation']} files")
        print(f"  - Removed redundant scripts: {self.removed_count['scripts']} files")
        print(f"  - Removed redundant shell scripts: {self.removed_count['shell_scripts']} files")
        print(f"  - Removed other files: {self.removed_count['other']} files")
        print(f"  - Cleaned up old results: {self.removed_count['results']} items")
        print(f"  - Total items removed: {total_removed}")
        print(f"\n💾 Backup saved in: {self.backup_dir.name}")
        print("   (You can delete this folder if everything works correctly)")
        print("\n🎯 Next steps:")
        print("  1. Review the changes")
        print("  2. Test the core functionality: python run_diva_gemini_demo.py")
        print("  3. Run tests: python -m pytest tests/")
        print("  4. If everything works, delete the backup folder")
    
    def run(self):
        """Execute the cleanup process"""
        print("🧹 DIVA-SQL Cleanup Script")
        print("==========================\n")
        
        self.create_backup_dir()
        self.remove_test_files()
        self.remove_databases()
        self.remove_documentation()
        self.remove_scripts()
        self.remove_shell_scripts()
        self.remove_package_json()
        self.remove_ds_store()
        self.clean_results()
        self.create_gitignore()
        self.create_docs_structure()
        self.print_summary()

if __name__ == '__main__':
    cleanup = DIVASQLCleanup()
    cleanup.run()
