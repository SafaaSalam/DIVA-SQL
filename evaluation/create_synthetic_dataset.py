#!/usr/bin/env python3
"""
Create a synthetic test dataset for DIVA-SQL benchmarking

This script creates a small synthetic dataset for testing the benchmark evaluation pipeline
without having to download the full Spider and BIRD datasets.
"""

import os
import sys
import json
import sqlite3
from pathlib import Path

# Set up directories
BENCHMARK_DIR = Path(__file__).parent.parent / "data" / "benchmarks"
SYNTHETIC_DIR = BENCHMARK_DIR / "synthetic"
DB_DIR = SYNTHETIC_DIR / "database"
DB_PATH = DB_DIR / "employees.sqlite"

# Define the schema for the employees database
EMPLOYEE_SCHEMA = """
CREATE TABLE departments (
    department_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    location TEXT,
    budget REAL
);

CREATE TABLE employees (
    employee_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    position TEXT,
    salary REAL,
    department_id INTEGER,
    hire_date TEXT,
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
);

CREATE TABLE projects (
    project_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    start_date TEXT,
    end_date TEXT,
    budget REAL,
    department_id INTEGER,
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
);

CREATE TABLE employee_projects (
    employee_id INTEGER,
    project_id INTEGER,
    role TEXT,
    PRIMARY KEY (employee_id, project_id),
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);
"""

# Sample data
DEPARTMENTS = [
    (1, "Engineering", "Building A", 1500000.0),
    (2, "Marketing", "Building B", 800000.0),
    (3, "Human Resources", "Building A", 500000.0),
    (4, "Finance", "Building C", 750000.0),
    (5, "Sales", "Building B", 1200000.0),
]

EMPLOYEES = [
    (1, "John Smith", "Senior Engineer", 120000.0, 1, "2019-05-15"),
    (2, "Emily Jones", "Marketing Specialist", 75000.0, 2, "2020-01-10"),
    (3, "David Wilson", "HR Manager", 90000.0, 3, "2018-11-01"),
    (4, "Sarah Brown", "Financial Analyst", 85000.0, 4, "2021-03-22"),
    (5, "Michael Lee", "Sales Director", 110000.0, 5, "2017-08-14"),
    (6, "Laura Martinez", "Junior Engineer", 70000.0, 1, "2021-09-30"),
    (7, "Robert Johnson", "Marketing Manager", 95000.0, 2, "2019-02-28"),
    (8, "Jennifer Garcia", "HR Specialist", 65000.0, 3, "2022-01-15"),
    (9, "James Taylor", "Senior Accountant", 92000.0, 4, "2020-07-07"),
    (10, "Linda Chen", "Sales Representative", 72000.0, 5, "2021-04-18"),
    (11, "Thomas White", "Principal Engineer", 135000.0, 1, "2018-06-11"),
    (12, "Jessica Lewis", "Content Specialist", 68000.0, 2, "2022-02-01"),
]

PROJECTS = [
    (1, "Website Redesign", "2022-01-01", "2022-06-30", 250000.0, 2),
    (2, "Mobile App Development", "2022-02-15", "2022-12-31", 500000.0, 1),
    (3, "Annual Budget Planning", "2022-09-01", "2022-11-30", 100000.0, 4),
    (4, "Employee Training Program", "2022-03-15", "2022-05-30", 75000.0, 3),
    (5, "Sales Growth Initiative", "2022-06-01", "2023-01-31", 300000.0, 5),
]

EMPLOYEE_PROJECTS = [
    (1, 2, "Lead Developer"),
    (6, 2, "Junior Developer"),
    (11, 2, "Architect"),
    (2, 1, "Content Manager"),
    (7, 1, "Project Manager"),
    (12, 1, "Designer"),
    (3, 4, "Coordinator"),
    (8, 4, "Trainer"),
    (4, 3, "Analyst"),
    (9, 3, "Lead Planner"),
    (5, 5, "Director"),
    (10, 5, "Field Agent"),
]

# Define example queries
SAMPLE_QUERIES = [
    {
        "id": "synthetic-1",
        "question": "List all employees with their departments.",
        "query": "SELECT e.name, d.name FROM employees e JOIN departments d ON e.department_id = d.department_id;"
    },
    {
        "id": "synthetic-2",
        "question": "Find employees with salary greater than 100000.",
        "query": "SELECT name, salary FROM employees WHERE salary > 100000;"
    },
    {
        "id": "synthetic-3",
        "question": "What is the average salary in each department?",
        "query": "SELECT d.name, AVG(e.salary) as avg_salary FROM employees e JOIN departments d ON e.department_id = d.department_id GROUP BY d.name;"
    },
    {
        "id": "synthetic-4",
        "question": "List employees working on the Mobile App Development project.",
        "query": "SELECT e.name, ep.role FROM employees e JOIN employee_projects ep ON e.employee_id = ep.employee_id JOIN projects p ON ep.project_id = p.project_id WHERE p.name = 'Mobile App Development';"
    },
    {
        "id": "synthetic-5",
        "question": "Show departments and their total budget allocation including project budgets.",
        "query": "SELECT d.name, d.budget + COALESCE(SUM(p.budget), 0) as total_budget FROM departments d LEFT JOIN projects p ON d.department_id = p.department_id GROUP BY d.department_id;"
    }
]

def create_database():
    """Create the synthetic SQLite database"""
    os.makedirs(DB_DIR, exist_ok=True)
    
    # Remove existing DB if it exists
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    # Create and populate the database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables
    cursor.executescript(EMPLOYEE_SCHEMA)
    
    # Insert data
    cursor.executemany("INSERT INTO departments VALUES (?, ?, ?, ?)", DEPARTMENTS)
    cursor.executemany("INSERT INTO employees VALUES (?, ?, ?, ?, ?, ?)", EMPLOYEES)
    cursor.executemany("INSERT INTO projects VALUES (?, ?, ?, ?, ?, ?)", PROJECTS)
    cursor.executemany("INSERT INTO employee_projects VALUES (?, ?, ?)", EMPLOYEE_PROJECTS)
    
    conn.commit()
    conn.close()

def create_spider_format():
    """Create files in Spider benchmark format"""
    os.makedirs(SYNTHETIC_DIR, exist_ok=True)
    
    # Create tables.json
    tables_data = {
        "employees": {
            "table_name": "employees",
            "column_names": ["employee_id", "name", "position", "salary", "department_id", "hire_date"],
            "column_types": ["number", "text", "text", "number", "number", "text"]
        },
        "departments": {
            "table_name": "departments", 
            "column_names": ["department_id", "name", "location", "budget"],
            "column_types": ["number", "text", "text", "number"]
        },
        "projects": {
            "table_name": "projects",
            "column_names": ["project_id", "name", "start_date", "end_date", "budget", "department_id"],
            "column_types": ["number", "text", "text", "text", "number", "number"]
        },
        "employee_projects": {
            "table_name": "employee_projects",
            "column_names": ["employee_id", "project_id", "role"],
            "column_types": ["number", "number", "text"]
        }
    }
    
    # Create dev.json with sample queries
    dev_data = []
    for item in SAMPLE_QUERIES:
        dev_item = {
            "db_id": "employees",
            "question": item["question"],
            "query": item["query"]
        }
        dev_data.append(dev_item)
    
    # Save files
    with open(SYNTHETIC_DIR / "tables.json", "w") as f:
        json.dump(tables_data, f, indent=2)
        
    with open(SYNTHETIC_DIR / "dev.json", "w") as f:
        json.dump(dev_data, f, indent=2)

def main():
    print("Creating synthetic dataset for DIVA-SQL benchmark testing")
    create_database()
    create_spider_format()
    print(f"Created synthetic dataset at {SYNTHETIC_DIR}")
    print(f"Database file: {DB_PATH}")
    print(f"Contains {len(SAMPLE_QUERIES)} sample queries")

if __name__ == "__main__":
    main()
