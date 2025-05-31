#!/usr/bin/env python3
"""
Repository Management Script

This script performs the following tasks:
1. Cleans all outputs from Jupyter notebooks in the repository
2. Runs Python tests
3. Runs mypy for type checking
4. Runs black for code formatting
5. Runs isort for import sorting

Usage:
    ./repo_manager.py [options]

Options:
    --clean-notebooks  Clean notebook outputs only
    --test             Run tests only
    --mypy             Run mypy only
    --black            Run black only
    --isort            Run isort only
    --all              Run all tasks (default)
    --help             Show this help message

Example:
    ./repo_manager.py --clean-notebooks --test
"""

import argparse
import json
import os
import subprocess
import sys


def clean_notebook_outputs(notebook_path):
    """Clean outputs from a single Jupyter notebook."""
    try:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            notebook = json.load(f)
        
        # Remove outputs from cells
        for cell in notebook['cells']:
            if cell['cell_type'] == 'code':
                cell['outputs'] = []
                cell['execution_count'] = None
        
        # Write the cleaned notebook back
        with open(notebook_path, 'w', encoding='utf-8') as f:
            json.dump(notebook, f, indent=1)
        
        print(f"✓ Cleaned outputs from {notebook_path}")
        return True
    except Exception as e:
        print(f"✗ Error cleaning {notebook_path}: {e}", file=sys.stderr)
        return False


def find_and_clean_notebooks(repo_path='.'):
    """Find all Jupyter notebooks in the repository and clean their outputs."""
    print("\n=== Cleaning Jupyter Notebook Outputs ===")
    
    # Find all .ipynb files, excluding hidden directories and .ipynb_checkpoints
    notebooks = []
    for root, dirs, files in os.walk(repo_path):
        # Skip hidden directories and .ipynb_checkpoints
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '.ipynb_checkpoints']
        
        for file in files:
            if file.endswith('.ipynb'):
                notebooks.append(os.path.join(root, file))
    
    if not notebooks:
        print("No notebooks found.")
        return True
    
    print(f"Found {len(notebooks)} notebooks.")
    
    # Clean all notebooks
    results = [clean_notebook_outputs(nb) for nb in notebooks]
    
    success = all(results)
    if success:
        print("✅ All notebooks cleaned successfully.")
    else:
        print("⚠️ Some notebooks could not be cleaned.", file=sys.stderr)
    
    return success

def run_tests(repo_path='.', with_coverage=True):
    """Run Python tests using pytest, optionally with coverage."""
    print("\n=== Running Python Tests ===")
    
    cmd = ["pytest", "-v", "test"]
    
    if with_coverage:
        cmd = [
            "coverage",
            "run",
            "--source=src",
            "-m",
            "pytest",
            "-v",
            "test",
        ]
    
    # Use pytest to run tests
    try:
        # Run pytest with the configured command
        result = subprocess.run(
            cmd, 
            cwd=repo_path,
            check=False,
            capture_output=True,
            text=True
        )
        
        # Display the output
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        if result.returncode == 0:
            print("✅ All tests passed.")
            if with_coverage:
                print("✅ Coverage report generated. Run coverage html && open htmlcov/index.html for details.")
            return True
        else:
            print(f"⚠️ Tests failed with return code {result.returncode}", file=sys.stderr)
            return False
    except FileNotFoundError:
        required_packages = "pytest"
        if with_coverage:
            required_packages += ", pytest-cov"
        
        print(f"⚠️ Required packages not found. Please install them with: pip install {required_packages}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"⚠️ Error running tests: {e}", file=sys.stderr)
        return False


def run_mypy(repo_path='.'):
    """Run mypy for type checking."""
    print("\n=== Running Mypy Type Checking ===")
    
    try:
        # Run mypy on the current directory
        result = subprocess.run(
            ["mypy", "src"], 
            cwd=repo_path,
            check=False,
            capture_output=True,
            text=True
        )
        
        # Display the output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        if result.returncode == 0:
            print("✅ Mypy type checking passed.")
            return True
        else:
            print(f"⚠️ Mypy found issues with return code {result.returncode}", file=sys.stderr)
            return False
    except FileNotFoundError:
        print("⚠️ mypy not found. Please install it with: pip install mypy", file=sys.stderr)
        return False
    except Exception as e:
        print(f"⚠️ Error running mypy: {e}", file=sys.stderr)
        return False


def run_black(repo_path='.'):
    """Run black for code formatting."""
    print("\n=== Running Black Code Formatter ===")
    
    try:
        # Run black in check mode first to see what would be changed
        check_result = subprocess.run(
            ["black", "--check", "src", "test"], 
            cwd=repo_path,
            check=False,
            capture_output=True,
            text=True
        )
        
        # If black --check finds files to format, run black to format them
        if check_result.returncode != 0:
            print("The following files would be reformatted:")
            print(check_result.stdout)
            
            # Run black to format the files
            format_result = subprocess.run(
                ["black", "src", "test"], 
                cwd=repo_path,
                check=False,
                capture_output=True,
                text=True
            )
            
            if format_result.returncode == 0:
                print("✅ Files reformatted with Black.")
                return True
            else:
                print(f"⚠️ Black formatting failed with return code {format_result.returncode}", file=sys.stderr)
                print(format_result.stderr, file=sys.stderr)
                return False
        else:
            print("✅ All files already formatted with Black.")
            return True
    except FileNotFoundError:
        print("⚠️ black not found. Please install it with: pip install black", file=sys.stderr)
        return False
    except Exception as e:
        print(f"⚠️ Error running black: {e}", file=sys.stderr)
        return False


def run_isort(repo_path='.'):
    """Run isort for import sorting."""
    print("\n=== Running isort Import Sorter ===")
    
    try:
        # Run isort in check mode first to see what would be changed
        check_result = subprocess.run(
            ["isort", "--check-only", "--profile", "black", "src", "test"], 
            cwd=repo_path,
            check=False,
            capture_output=True,
            text=True
        )
        
        # If isort check finds files to sort, run isort to sort them
        if check_result.returncode != 0:
            print("The following files need import sorting:")
            print(check_result.stdout)
            
            # Run isort to sort the imports
            sort_result = subprocess.run(
                ["isort", "--profile", "black", "src", "test"], 
                cwd=repo_path,
                check=False,
                capture_output=True,
                text=True
            )
            
            if sort_result.returncode == 0:
                print("✅ Files sorted with isort.")
                return True
            else:
                print(f"⚠️ isort failed with return code {sort_result.returncode}", file=sys.stderr)
                print(sort_result.stderr, file=sys.stderr)
                return False
        else:
            print("✅ All imports already sorted correctly.")
            return True
    except FileNotFoundError:
        print("⚠️ isort not found. Please install it with: pip install isort", file=sys.stderr)
        return False
    except Exception as e:
        print(f"⚠️ Error running isort: {e}", file=sys.stderr)
        return False


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Repository management script for cleaning notebooks and running code quality tools.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument('--clean-notebooks', action='store_true', help='Clean notebook outputs only')
    parser.add_argument('--test', action='store_true', help='Run tests only')
    parser.add_argument('--mypy', action='store_true', help='Run mypy only')
    parser.add_argument('--black', action='store_true', help='Run black only')
    parser.add_argument('--isort', action='store_true', help='Run isort only')
    parser.add_argument('--all', action='store_true', help='Run all tasks (default)')
    
    args = parser.parse_args()
    
    # If no specific tasks are specified, run all
    if not (args.clean_notebooks or args.test or args.mypy or args.black or args.isort or args.all):
        args.all = True
    
    return args


def main():
    args = parse_arguments()
    
    # Track overall success
    success = True
    
    # Run the selected tasks
    if args.clean_notebooks or args.all:
        success = find_and_clean_notebooks() and success
    
    if args.test or args.all:
        success = run_tests() and success
    
    if args.mypy or args.all:
        success = run_mypy() and success
    
    if args.black or args.all:
        success = run_black() and success
    
    if args.isort or args.all:
        success = run_isort() and success
    
    # Print summary
    print("\n=== Summary ===")
    if success:
        print("✅ All tasks completed successfully.")
        return 0
    else:
        print("⚠️ Some tasks failed. Check the output for details.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())