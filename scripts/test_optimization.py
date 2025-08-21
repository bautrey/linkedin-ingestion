#!/usr/bin/env python3
"""
Test Execution Optimization

This script provides intelligent test selection and parallel execution
strategies to optimize development feedback loops and CI/CD performance.
"""

import os
import subprocess
import sys
import time
import json
from pathlib import Path
from typing import List, Dict, Set, Optional, Any
import hashlib
import argparse


class TestOptimizer:
    """Optimizes test execution through intelligent selection and parallel execution."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.cache_dir = self.project_root / ".pytest_cache" / "optimization"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # File patterns that affect different test categories
        self.test_dependencies = {
            "cassidy": ["app/adapters/cassidy_adapter.py", "app/cassidy/", "app/models/canonical.py"],
            "company": ["app/services/company_service.py", "app/repositories/company_repository.py", "app/models/company.py"],
            "database": ["app/database.py", "app/repositories/", "app/models/"],
            "scoring": ["app/services/scoring_service.py", "app/scoring/", "tests/test_scoring_*"],
            "templates": ["app/services/template_service.py", "app/models/template.py"],
            "api": ["app/api/", "app/endpoints/", "app/controllers/"],
            "workflows": ["app/workflows/", "app/services/"],
        }
    
    def get_changed_files(self, base_branch: str = "main") -> Set[str]:
        """Get list of files changed compared to base branch."""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", f"origin/{base_branch}...HEAD"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            if result.returncode == 0:
                return set(result.stdout.strip().split('\n')) if result.stdout.strip() else set()
        except subprocess.SubprocessError:
            pass
        
        # Fallback: get unstaged and staged changes
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            if result.returncode == 0:
                changed = set(result.stdout.strip().split('\n')) if result.stdout.strip() else set()
                
                # Add staged changes
                result = subprocess.run(
                    ["git", "diff", "--name-only", "--cached"],
                    capture_output=True,
                    text=True,
                    cwd=self.project_root
                )
                if result.returncode == 0:
                    staged = set(result.stdout.strip().split('\n')) if result.stdout.strip() else set()
                    changed.update(staged)
                
                return changed
        except subprocess.SubprocessError:
            pass
        
        return set()
    
    def calculate_affected_tests(self, changed_files: Set[str]) -> Set[str]:
        """Calculate which test categories are affected by changed files."""
        affected_categories = set()
        
        for category, patterns in self.test_dependencies.items():
            for pattern in patterns:
                if any(changed_file.startswith(pattern.rstrip('*')) for changed_file in changed_files):
                    affected_categories.add(category)
                    break
        
        # If no specific categories affected, run all unit tests
        if not affected_categories:
            affected_categories.add("unit")
        
        return affected_categories
    
    def get_selective_test_command(self, categories: Set[str]) -> List[str]:
        """Generate pytest command for selective test execution."""
        base_cmd = ["python", "-m", "pytest", "-v", "--tb=short"]
        
        if "unit" in categories:
            # Run all unit tests if no specific category or if explicitly requested
            base_cmd.extend(["app/tests/", "-m", "unit and not slow"])
        else:
            # Run specific test categories
            test_patterns = []
            marker_patterns = []
            
            for category in categories:
                if category == "cassidy":
                    test_patterns.extend(["-k", "cassidy"])
                elif category in ["company", "database", "scoring", "templates"]:
                    marker_patterns.append(category)
            
            if test_patterns:
                base_cmd.extend(test_patterns)
            if marker_patterns:
                base_cmd.extend(["-m", " or ".join(marker_patterns)])
        
        return base_cmd
    
    def get_parallel_test_command(self, test_cmd: List[str], max_workers: Optional[int] = None) -> List[str]:
        """Add parallel execution to test command."""
        if max_workers is None:
            max_workers = min(os.cpu_count() or 4, 4)  # Cap at 4 workers
        
        # Check if pytest-xdist is available
        try:
            import xdist
            parallel_cmd = test_cmd + ["-n", str(max_workers)]
            return parallel_cmd
        except ImportError:
            print("⚠️  pytest-xdist not available. Install with: pip install pytest-xdist")
            return test_cmd
    
    def cache_test_results(self, test_results: Dict[str, Any]):
        """Cache test results for future optimization."""
        cache_file = self.cache_dir / "test_results.json"
        
        # Load existing cache
        existing_cache = {}
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    existing_cache = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        # Update cache
        existing_cache.update(test_results)
        
        # Write cache
        with open(cache_file, 'w') as f:
            json.dump(existing_cache, f, indent=2)
    
    def get_cached_results(self) -> Dict[str, Any]:
        """Get cached test results."""
        cache_file = self.cache_dir / "test_results.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return {}
    
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate hash of file for change detection."""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except FileNotFoundError:
            return ""
    
    def run_optimized_tests(self, 
                          selective: bool = True,
                          parallel: bool = True,
                          max_workers: Optional[int] = None,
                          base_branch: str = "main") -> int:
        """Run optimized test suite based on changes and caching."""
        
        print("🚀 LinkedIn Ingestion Test Optimizer")
        print("=" * 50)
        
        start_time = time.time()
        
        if selective:
            # Detect changes and run selective tests
            changed_files = self.get_changed_files(base_branch)
            if changed_files:
                print(f"📁 Changed files detected: {len(changed_files)}")
                for file in sorted(changed_files):
                    print(f"   - {file}")
                
                affected_categories = self.calculate_affected_tests(changed_files)
                print(f"🎯 Affected test categories: {', '.join(sorted(affected_categories))}")
                
                test_cmd = self.get_selective_test_command(affected_categories)
            else:
                print("📁 No changes detected, running unit tests")
                test_cmd = ["python", "-m", "pytest", "app/tests/", "-m", "unit and not slow", "-v", "--tb=short"]
        else:
            # Run all safe tests
            print("🔄 Running all safe tests (unit + integration)")
            test_cmd = ["python", "-m", "pytest", "app/tests/", "tests/", "-m", "not production and not external", "-v", "--tb=short"]
        
        if parallel:
            test_cmd = self.get_parallel_test_command(test_cmd, max_workers)
            print(f"⚡ Parallel execution enabled (max workers: {max_workers or 'auto'})")
        
        print(f"🔧 Test command: {' '.join(test_cmd)}")
        print("-" * 50)
        
        # Execute tests
        result = subprocess.run(test_cmd, cwd=self.project_root)
        
        execution_time = time.time() - start_time
        print("-" * 50)
        
        if result.returncode == 0:
            print(f"✅ Tests completed successfully in {execution_time:.2f}s")
        else:
            print(f"❌ Tests failed in {execution_time:.2f}s")
        
        # Cache results for future optimization
        test_results = {
            "last_run": time.time(),
            "execution_time": execution_time,
            "exit_code": result.returncode,
            "command": " ".join(test_cmd)
        }
        self.cache_test_results(test_results)
        
        return result.returncode


def create_performance_report():
    """Create a performance report of test execution times."""
    optimizer = TestOptimizer()
    cache = optimizer.get_cached_results()
    
    print("📊 Test Performance Report")
    print("=" * 40)
    
    if cache:
        print(f"Last run: {time.ctime(cache.get('last_run', 0))}")
        print(f"Execution time: {cache.get('execution_time', 0):.2f}s")
        print(f"Exit code: {cache.get('exit_code', 'unknown')}")
        print(f"Command: {cache.get('command', 'unknown')}")
    else:
        print("No cached results available")
    
    print("\n🎯 Optimization Recommendations:")
    print("1. Use selective testing during development: --selective")
    print("2. Enable parallel execution: --parallel")
    print("3. Run only fast tests for quick feedback: --fast-only")
    print("4. Use test markers to run specific components")


def main():
    parser = argparse.ArgumentParser(description="LinkedIn Ingestion Test Optimizer")
    parser.add_argument("--selective", action="store_true", default=True,
                      help="Run only tests affected by changes (default: True)")
    parser.add_argument("--no-selective", dest="selective", action="store_false",
                      help="Disable selective test execution")
    parser.add_argument("--parallel", action="store_true", default=True,
                      help="Enable parallel test execution (default: True)")
    parser.add_argument("--no-parallel", dest="parallel", action="store_false",
                      help="Disable parallel test execution")
    parser.add_argument("--workers", type=int, help="Number of parallel workers")
    parser.add_argument("--base-branch", default="main", help="Base branch for change detection")
    parser.add_argument("--report", action="store_true", help="Show performance report")
    parser.add_argument("--install-deps", action="store_true", help="Install optimization dependencies")
    
    args = parser.parse_args()
    
    if args.install_deps:
        print("📦 Installing test optimization dependencies...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "pytest-xdist", "pytest-cov", "pytest-benchmark"
        ])
        return result.returncode
    
    if args.report:
        create_performance_report()
        return 0
    
    optimizer = TestOptimizer()
    return optimizer.run_optimized_tests(
        selective=args.selective,
        parallel=args.parallel,
        max_workers=args.workers,
        base_branch=args.base_branch
    )


if __name__ == "__main__":
    sys.exit(main())
