#!/usr/bin/env python3
"""
DIVA-SQL Project Setup Script

This script sets up the DIVA-SQL project environment and runs initial tests.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def print_step(step, description):
    """Print a step description"""
    print(f"\n[{step}] {description}")


def run_command(command, description):
    """Run a command and handle errors"""
    print(f"Running: {command}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is compatible"""
    print_step("1", "Checking Python version")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} is not supported. Please use Python 3.8+")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True


def setup_virtual_environment():
    """Set up virtual environment"""
    print_step("2", "Setting up virtual environment")
    
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("Virtual environment already exists")
        return True
    
    # Create virtual environment
    if not run_command(f"{sys.executable} -m venv venv", "Creating virtual environment"):
        return False
    
    print("✅ Virtual environment created successfully")
    return True


def install_dependencies():
    """Install project dependencies"""
    print_step("3", "Installing dependencies")
    
    # Determine pip command based on OS
    if platform.system() == "Windows":
        pip_cmd = "venv\\Scripts\\pip"
        python_cmd = "venv\\Scripts\\python"
    else:
        pip_cmd = "venv/bin/pip"
        python_cmd = "venv/bin/python"
    
    # Upgrade pip
    if not run_command(f"{pip_cmd} install --upgrade pip", "Upgrading pip"):
        print("⚠️  Failed to upgrade pip, continuing anyway")
    
    # Install requirements
    if not run_command(f"{pip_cmd} install -r requirements.txt", "Installing requirements"):
        print("❌ Failed to install requirements")
        return False
    
    print("✅ Dependencies installed successfully")
    return True


def run_tests():
    """Run project tests"""
    print_step("4", "Running tests")
    
    # Determine python command
    if platform.system() == "Windows":
        python_cmd = "venv\\Scripts\\python"
    else:
        python_cmd = "venv/bin/python"
    
    test_files = [
        "tests/test_core.py"
    ]
    
    all_passed = True
    for test_file in test_files:
        if Path(test_file).exists():
            print(f"\nRunning {test_file}...")
            if not run_command(f"{python_cmd} {test_file}", f"Running {test_file}"):
                all_passed = False
                print(f"❌ Tests in {test_file} failed")
            else:
                print(f"✅ Tests in {test_file} passed")
        else:
            print(f"⚠️  Test file {test_file} not found")
    
    return all_passed


def create_environment_file():
    """Create .env file template"""
    print_step("5", "Creating environment configuration")
    
    env_file = Path(".env")
    
    if env_file.exists():
        print(".env file already exists")
        return True
    
    env_template = """# DIVA-SQL Environment Configuration
# Copy this file and add your actual API keys

# OpenAI API Key (required for LLM functionality)
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic API Key (optional, for Claude models)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Database Configuration
DATABASE_URL=sqlite:///data/sample.db

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/diva-sql.log

# Evaluation Settings
BENCHMARK_DATA_PATH=data/benchmarks/
RESULTS_OUTPUT_PATH=results/
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_template)
        print("✅ .env template created")
        print("Please edit .env file and add your API keys")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False


def create_directory_structure():
    """Create necessary directories"""
    print_step("6", "Creating directory structure")
    
    directories = [
        "data/benchmarks",
        "data/databases", 
        "results/experiments",
        "logs",
        "temp"
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")
    
    print("✅ Directory structure created")
    return True


def display_usage_examples():
    """Display usage examples"""
    print_step("7", "Usage Examples")
    
    examples = [
        ("Interactive Mode", "python src/main.py interactive"),
        ("Single Query", "python src/main.py query 'Show me all employees'"),
        ("Demo Mode", "python src/main.py demo"),
        ("Run Tests", "python tests/test_core.py"),
        ("Jupyter Notebook", "jupyter notebook notebooks/diva_sql_demo.ipynb")
    ]
    
    print("\nOnce setup is complete, you can use DIVA-SQL as follows:\n")
    
    for description, command in examples:
        print(f"{description}:")
        print(f"  {command}\n")


def main():
    """Main setup function"""
    print_header("DIVA-SQL Project Setup")
    
    print("This script will set up the DIVA-SQL development environment.")
    print("Please ensure you have Python 3.8+ installed.")
    
    # Change to project directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print(f"Working directory: {project_root.absolute()}")
    
    # Setup steps
    steps = [
        ("Python version check", check_python_version),
        ("Virtual environment setup", setup_virtual_environment),
        ("Dependencies installation", install_dependencies),
        ("Test execution", run_tests),
        ("Environment configuration", create_environment_file),
        ("Directory structure", create_directory_structure)
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        try:
            if not step_func():
                failed_steps.append(step_name)
        except Exception as e:
            print(f"❌ Error in {step_name}: {e}")
            failed_steps.append(step_name)
    
    # Summary
    print_header("Setup Summary")
    
    if not failed_steps:
        print("🎉 All setup steps completed successfully!")
        print("\nNext steps:")
        print("1. Edit the .env file and add your API keys")
        print("2. Try running the demo: python src/main.py demo")
        print("3. Explore the Jupyter notebook: jupyter notebook notebooks/diva_sql_demo.ipynb")
        
        display_usage_examples()
        
    else:
        print("❌ Some setup steps failed:")
        for step in failed_steps:
            print(f"  - {step}")
        print("\nPlease resolve these issues and run the setup again.")
        sys.exit(1)
    
    print_header("DIVA-SQL Setup Complete")


if __name__ == "__main__":
    main()
