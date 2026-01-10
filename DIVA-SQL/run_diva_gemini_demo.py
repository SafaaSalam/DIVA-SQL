#!/usr/bin/env python3
"""
DIVA-SQL with Google Gemini - Complete Demo Script

This script demonstrates the full DIVA-SQL system with Google's Gemini API
using real database data. It shows semantic decomposition, SQL generation,
verification, and execution.

Usage:
    python3 run_diva_gemini_demo.py [--api-key YOUR_KEY] [--interactive]
"""

import os
import sys
import argparse
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import random
import json
import time

# Add src to path  
sys.path.append(str(Path(__file__).parent / "src"))

try:
    import google.generativeai as genai
    from src.utils.gemini_client import create_gemini_client
    from src.core.pipeline import DIVASQLPipeline
    from src.core.semantic_dag import SemanticDAG, SemanticNode
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure you've installed all dependencies:")
    print("pip3 install google-generativeai")
    sys.exit(1)


class ComprehensiveDemo:
    """Complete DIVA-SQL demonstration with Gemini"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.db_path = "demo_database.db"
        self.setup_database()
        self.setup_pipeline()
    
    def setup_database(self):
        """Create a comprehensive demo database"""
        print("🏗️  Setting up demo database...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Drop existing tables
        tables = ['sales', 'products', 'customers', 'orders', 'employees', 'departments']
        for table in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
        
        # Create modern e-commerce database schema
        
        # Departments
        cursor.execute("""
            CREATE TABLE departments (
                dept_id INTEGER PRIMARY KEY,
                dept_name TEXT NOT NULL,
                budget REAL,
                location TEXT
            )
        """)
        
        # Employees
        cursor.execute("""
            CREATE TABLE employees (
                emp_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                dept_id INTEGER,
                salary REAL,
                hire_date DATE,
                position TEXT,
                FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
            )
        """)
        
        # Customers
        cursor.execute("""
            CREATE TABLE customers (
                customer_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                city TEXT,
                state TEXT,
                registration_date DATE,
                customer_type TEXT
            )
        """)
        
        # Products
        cursor.execute("""
            CREATE TABLE products (
                product_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT,
                price REAL,
                cost REAL,
                stock_quantity INTEGER,
                supplier TEXT
            )
        """)
        
        # Orders
        cursor.execute("""
            CREATE TABLE orders (
                order_id INTEGER PRIMARY KEY,
                customer_id INTEGER,
                order_date DATE,
                total_amount REAL,
                status TEXT,
                shipping_city TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
            )
        """)
        
        # Sales (order details)
        cursor.execute("""
            CREATE TABLE sales (
                sale_id INTEGER PRIMARY KEY,
                order_id INTEGER,
                product_id INTEGER,
                quantity INTEGER,
                unit_price REAL,
                discount REAL DEFAULT 0,
                FOREIGN KEY (order_id) REFERENCES orders(order_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            )
        """)
        
        # Insert sample data
        self.populate_sample_data(cursor)
        conn.commit()
        conn.close()
        
        print(f"✅ Demo database created: {self.db_path}")
    
    def populate_sample_data(self, cursor):
        """Insert realistic sample data"""
        
        # Departments
        departments = [
            (1, 'Sales', 500000, 'New York'),
            (2, 'Engineering', 800000, 'San Francisco'), 
            (3, 'Marketing', 300000, 'Los Angeles'),
            (4, 'Customer Service', 200000, 'Austin'),
            (5, 'Operations', 400000, 'Chicago')
        ]
        cursor.executemany("INSERT INTO departments VALUES (?, ?, ?, ?)", departments)
        
        # Employees
        employees = [
            (1, 'John Smith', 'john.smith@company.com', 1, 75000, '2022-01-15', 'Sales Manager'),
            (2, 'Sarah Johnson', 'sarah.j@company.com', 2, 95000, '2021-06-20', 'Senior Developer'),
            (3, 'Mike Chen', 'mike.chen@company.com', 2, 87000, '2022-03-10', 'Software Engineer'),
            (4, 'Emily Davis', 'emily.d@company.com', 3, 68000, '2021-11-05', 'Marketing Specialist'),
            (5, 'Robert Wilson', 'rob.wilson@company.com', 1, 62000, '2023-02-28', 'Sales Associate'),
            (6, 'Lisa Brown', 'lisa.b@company.com', 4, 55000, '2022-08-14', 'Customer Support'),
            (7, 'David Lee', 'david.lee@company.com', 5, 72000, '2021-12-03', 'Operations Manager'),
            (8, 'Anna Martinez', 'anna.m@company.com', 2, 82000, '2022-07-18', 'DevOps Engineer')
        ]
        cursor.executemany("INSERT INTO employees VALUES (?, ?, ?, ?, ?, ?, ?)", employees)
        
        # Customers
        customers = []
        cities = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego']
        states = ['NY', 'CA', 'IL', 'TX', 'AZ', 'PA', 'TX', 'CA']
        customer_types = ['Premium', 'Standard', 'Basic']
        
        for i in range(1, 51):  # 50 customers
            name = f"Customer {i:02d}"
            email = f"customer{i:02d}@email.com"
            city = random.choice(cities)
            state = random.choice(states)
            reg_date = datetime.now() - timedelta(days=random.randint(30, 730))
            ctype = random.choice(customer_types)
            customers.append((i, name, email, city, state, reg_date.strftime('%Y-%m-%d'), ctype))
        
        cursor.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?, ?)", customers)
        
        # Products
        products = [
            (1, 'Laptop Pro', 'Electronics', 1299.99, 800, 25, 'TechCorp'),
            (2, 'Wireless Headphones', 'Electronics', 199.99, 120, 50, 'AudioTech'),
            (3, 'Office Chair', 'Furniture', 299.99, 180, 15, 'ComfortCo'),
            (4, 'Smartphone X', 'Electronics', 899.99, 550, 30, 'PhonePlus'),
            (5, 'Desk Lamp', 'Furniture', 79.99, 45, 40, 'LightWorks'),
            (6, 'Notebook Set', 'Stationery', 24.99, 8, 100, 'PaperPro'),
            (7, 'Coffee Maker', 'Appliances', 149.99, 90, 20, 'BrewMaster'),
            (8, 'Monitor 27"', 'Electronics', 349.99, 210, 18, 'ScreenTech'),
            (9, 'Keyboard RGB', 'Electronics', 129.99, 75, 35, 'KeyCorp'),
            (10, 'Standing Desk', 'Furniture', 599.99, 350, 8, 'ErgoCorp')
        ]
        cursor.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?)", products)
        
        # Orders and Sales
        order_id = 1
        sale_id = 1
        
        for customer_id in range(1, 51):
            # Each customer has 1-4 orders
            num_orders = random.randint(1, 4)
            
            for _ in range(num_orders):
                order_date = datetime.now() - timedelta(days=random.randint(1, 365))
                status = random.choice(['Completed', 'Pending', 'Shipped', 'Cancelled'])
                shipping_city = random.choice(cities)
                
                # Create order 
                order_total = 0
                order_items = []
                
                # 1-5 items per order
                num_items = random.randint(1, 5)
                selected_products = random.sample(range(1, 11), min(num_items, 10))
                
                for product_id in selected_products:
                    quantity = random.randint(1, 3)
                    # Get product price (simplified - using index)
                    unit_price = products[product_id-1][3]  # price from products list
                    discount = random.choice([0, 0.05, 0.1, 0.15]) if random.random() < 0.3 else 0
                    
                    item_total = quantity * unit_price * (1 - discount)
                    order_total += item_total
                    
                    order_items.append((sale_id, order_id, product_id, quantity, unit_price, discount))
                    sale_id += 1
                
                # Insert order
                cursor.execute("""
                    INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?)
                """, (order_id, customer_id, order_date.strftime('%Y-%m-%d'), 
                     round(order_total, 2), status, shipping_city))
                
                # Insert sales items
                cursor.executemany("""
                    INSERT INTO sales VALUES (?, ?, ?, ?, ?, ?)
                """, order_items)
                
                order_id += 1
        
        print(f"   - Inserted {len(departments)} departments")
        print(f"   - Inserted {len(employees)} employees") 
        print(f"   - Inserted 50 customers")
        print(f"   - Inserted {len(products)} products")
        print(f"   - Inserted {order_id-1} orders with {sale_id-1} items")
    
    def setup_pipeline(self):
        """Initialize DIVA-SQL pipeline with Gemini"""
        print("🤖 Initializing DIVA-SQL with Gemini...")
        
        try:
            self.gemini_client = create_gemini_client(
                api_key=self.api_key,
                model_name="gemini-2.0-flash"
            )
            
            self.pipeline = DIVASQLPipeline(
                self.gemini_client, 
                model_name="gemini-2.0-flash"
            )
            
            print("✅ DIVA-SQL pipeline initialized successfully")
            
        except Exception as e:
            print(f"❌ Error initializing pipeline: {e}")
            sys.exit(1)
    
    def get_database_schema(self):
        """Get database schema for DIVA-SQL"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        schema = {"tables": {}}
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for (table_name,) in tables:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            schema["tables"][table_name] = [col[1] for col in columns]
        
        conn.close()
        return schema
    
    def display_schema(self):
        """Display database schema"""
        schema = self.get_database_schema()
        print("\n📊 Database Schema:")
        print("=" * 50)
        
        for table, columns in schema["tables"].items():
            print(f"🗃️  {table.upper()}")
            for col in columns:
                print(f"   • {col}")
            print()
    
    def run_demonstration_queries(self):
        """Run a set of demonstration queries"""
        schema = self.get_database_schema()
        
        demo_queries = [
            {
                "query": "Show all customers from New York",
                "description": "Simple filtering query",
                "complexity": "Basic"
            },
            {
                "query": "What is the average salary by department?",
                "description": "Aggregation with grouping",
                "complexity": "Medium"
            },
            {
                "query": "Find the top 5 best-selling products",
                "description": "Join, aggregation, and ordering", 
                "complexity": "Medium"
            },
            {
                "query": "Show customers who have spent more than $1000 total",
                "description": "Complex join with aggregation and filtering",
                "complexity": "Hard"
            },
            {
                "query": "Which employees earn more than the average salary in their department?",
                "description": "Subquery with correlated conditions",
                "complexity": "Hard"
            }
        ]
        
        print("\n🎯 Running Demonstration Queries")
        print("=" * 60)
        
        successful = 0
        total = len(demo_queries)
        
        for i, query_info in enumerate(demo_queries, 1):
            print(f"\n🔍 Query {i}/{total}: {query_info['query']}")
            print(f"📝 Description: {query_info['description']}")
            print(f"🎚️  Complexity: {query_info['complexity']}")
            print("-" * 50)
            
            try:
                # Generate SQL using DIVA-SQL
                result = self.pipeline.generate_sql(query_info['query'], schema)
                
                print(f"✅ Status: {result.status.value}")
                print(f"📋 Generated SQL:")
                print(f"   {result.final_sql}")
                print(f"🎯 Confidence: {result.confidence_score:.2f}")
                
                if result.semantic_dag:
                    print(f"🧩 Semantic Decomposition: {len(result.semantic_dag.nodes)} nodes")
                    
                    # Show semantic breakdown
                    execution_order = result.semantic_dag.get_topological_order()
                    print(f"🔄 Execution Steps:")
                    for j, node_id in enumerate(execution_order, 1):
                        node = result.semantic_dag.nodes[node_id]
                        print(f"   {j}. {node.node_type.value}: {node.description}")
                
                # Execute the query
                if result.final_sql:
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    
                    try:
                        cursor.execute(result.final_sql)
                        results = cursor.fetchall()
                        print(f"📊 Execution Result: {len(results)} rows returned")
                        
                        # Show sample results
                        if results:
                            print(f"🗃️  Sample Results (first 3 rows):")
                            for k, row in enumerate(results[:3], 1):
                                print(f"   {k}. {row}")
                        
                        successful += 1
                        
                    except Exception as exec_error:
                        print(f"❌ SQL Execution Error: {exec_error}")
                    finally:
                        conn.close()
                
            except Exception as e:
                print(f"❌ Generation Error: {e}")
            
            print("-" * 50)
            
            # Add delay between queries to respect rate limits
            if i < total:  # Don't delay after the last query
                print("⏳ Pausing to respect API rate limits...")
                time.sleep(2)  # 2-second delay between queries
        
        print(f"\n📈 Demo Results Summary:")
        print(f"✅ Successful queries: {successful}/{total} ({successful/total*100:.1f}%)")
        
        return successful, total
    
    def interactive_mode(self):
        """Interactive query mode"""
        schema = self.get_database_schema()
        
        print("\n🎮 Interactive Mode")
        print("=" * 40)
        print("Type natural language queries and see DIVA-SQL in action!")
        print("Commands: 'schema' (show tables), 'quit' (exit), 'help' (show examples)")
        
        while True:
            try:
                query = input("\n💬 Your query: ").strip()
                
                if query.lower() == 'quit':
                    print("👋 Goodbye!")
                    break
                elif query.lower() == 'schema':
                    self.display_schema()
                    continue
                elif query.lower() == 'help':
                    print("\n💡 Example queries you can try:")
                    examples = [
                        "Show all products with price above $100",
                        "What are the total sales by product category?", 
                        "Find customers with more than 2 orders",
                        "Which department has the highest average salary?",
                        "Show monthly sales trends",
                        "Find products that are low in stock"
                    ]
                    for example in examples:
                        print(f"   • {example}")
                    continue
                elif not query:
                    continue
                
                print(f"\n🤖 Processing: '{query}'")
                print("⏳ Thinking...")
                
                result = self.pipeline.generate_sql(query, schema)
                
                print(f"\n📝 Generated SQL:")
                print(f"   {result.final_sql}")
                print(f"🎯 Confidence: {result.confidence_score:.2f}")
                print(f"⚡ Status: {result.status.value}")
                
                # Show semantic breakdown if available
                if result.semantic_dag and len(result.semantic_dag.nodes) > 1:
                    print(f"\n🧠 Semantic Reasoning:")
                    execution_order = result.semantic_dag.get_topological_order()
                    for j, node_id in enumerate(execution_order, 1):
                        node = result.semantic_dag.nodes[node_id]
                        print(f"   {j}. {node.description}")
                
                # Execute query
                if result.final_sql:
                    try:
                        conn = sqlite3.connect(self.db_path)
                        cursor = conn.cursor()
                        cursor.execute(result.final_sql)
                        results = cursor.fetchall()
                        conn.close()
                        
                        print(f"\n📊 Results: {len(results)} rows")
                        
                        if results:
                            print("🗃️  Data:")
                            for i, row in enumerate(results[:10], 1):  # Show first 10
                                print(f"   {i:2d}. {row}")
                            
                            if len(results) > 10:
                                print(f"   ... and {len(results) - 10} more rows")
                        else:
                            print("   (No results)")
                            
                    except Exception as e:
                        print(f"❌ Execution Error: {e}")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")


def main():
    """Main demo function"""
    parser = argparse.ArgumentParser(
        description="DIVA-SQL with Google Gemini - Complete Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 run_diva_gemini_demo.py --api-key YOUR_KEY
  python3 run_diva_gemini_demo.py --interactive
  
Environment Variables:
  GOOGLE_API_KEY    Google AI API key (alternative to --api-key)
        """
    )
    
    parser.add_argument('--api-key', help='Google AI API key')
    parser.add_argument('--interactive', action='store_true', help='Run in interactive mode')
    parser.add_argument('--schema-only', action='store_true', help='Only show database schema')
    
    args = parser.parse_args()
    
    # Get API key
    api_key = args.api_key or os.getenv('GOOGLE_API_KEY')
    
    if not api_key:
        print("❌ Google AI API key required!")
        print("\nOptions:")
        print("1. Pass as argument: --api-key YOUR_KEY")
        print("2. Set environment variable: export GOOGLE_API_KEY='YOUR_KEY'") 
        print("3. Get key from: https://aistudio.google.com/app/apikey")
        sys.exit(1)
    
    print("🚀 DIVA-SQL with Google Gemini - Complete Demo")
    print("=" * 60)
    print(f"🤖 Model: gemini-2.0-flash")
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize demo
    demo = ComprehensiveDemo(api_key)
    
    if args.schema_only:
        demo.display_schema()
        return
    
    # Show schema
    demo.display_schema()
    
    if args.interactive:
        demo.interactive_mode()
    else:
        # Run demonstration queries
        successful, total = demo.run_demonstration_queries()
        
        print("\n🎉 Demo Complete!")
        print(f"📈 Final Success Rate: {successful}/{total} ({successful/total*100:.1f}%)")
        print("\nNext steps:")
        print("• Run in interactive mode: python3 run_diva_gemini_demo.py --interactive")
        print("• Explore the database: open demo_database.db with SQLite browser")
        print("• Try your own queries and see DIVA-SQL's semantic decomposition!")


if __name__ == "__main__":
    main()
