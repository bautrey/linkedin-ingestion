#!/usr/bin/env python3
"""
Test Performance Report and Optimization Metrics

This script analyzes test performance, identifies bottlenecks, and provides
optimization recommendations for the LinkedIn ingestion project.
"""

import json
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys


class TestPerformanceAnalyzer:
    """Analyzes test performance and provides optimization recommendations."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.cache_dir = self.project_root / ".pytest_cache" / "optimization"
        self.performance_data = {}
    
    def run_performance_benchmark(self) -> Dict[str, Any]:
        """Run comprehensive performance benchmark of the test suite."""
        print("🔍 Running Test Performance Benchmark")
        print("=" * 50)
        
        benchmarks = {}
        
        # Benchmark 1: Unit tests (fast, isolated)
        print("📊 Benchmarking unit tests...")
        start_time = time.time()
        result = subprocess.run([
            "python", "-m", "pytest", 
            "app/tests/", 
            "-m", "unit and not slow",
            "--tb=short", "-q", "--durations=10"
        ], capture_output=True, text=True, cwd=self.project_root)
        
        benchmarks["unit_tests"] = {
            "duration": time.time() - start_time,
            "exit_code": result.returncode,
            "test_count": self._extract_test_count(result.stdout),
            "slowest_tests": self._extract_slow_tests(result.stdout)
        }
        print(f"   Unit tests: {benchmarks['unit_tests']['duration']:.2f}s")
        
        # Benchmark 2: Parallel execution test
        print("⚡ Testing parallel execution performance...")
        start_time = time.time()
        result = subprocess.run([
            "python", "-m", "pytest", 
            "app/tests/", 
            "-m", "unit and not slow",
            "-n", "2",  # Use 2 workers
            "--tb=short", "-q"
        ], capture_output=True, text=True, cwd=self.project_root)
        
        benchmarks["parallel_tests"] = {
            "duration": time.time() - start_time,
            "exit_code": result.returncode,
            "workers": 2,
            "speedup": benchmarks["unit_tests"]["duration"] / (time.time() - start_time) if result.returncode == 0 else 0
        }
        print(f"   Parallel tests: {benchmarks['parallel_tests']['duration']:.2f}s (speedup: {benchmarks['parallel_tests']['speedup']:.2f}x)")
        
        # Benchmark 3: Test discovery overhead
        print("🔍 Measuring test discovery overhead...")
        start_time = time.time()
        result = subprocess.run([
            "python", "-m", "pytest", 
            "--collect-only", "-q"
        ], capture_output=True, text=True, cwd=self.project_root)
        
        benchmarks["test_discovery"] = {
            "duration": time.time() - start_time,
            "exit_code": result.returncode,
            "total_tests": self._extract_collected_count(result.stdout)
        }
        print(f"   Test discovery: {benchmarks['test_discovery']['duration']:.2f}s")
        
        self.performance_data = benchmarks
        self._save_benchmark_results(benchmarks)
        
        return benchmarks
    
    def _extract_test_count(self, output: str) -> int:
        """Extract test count from pytest output."""
        for line in output.split('\n'):
            if " passed" in line:
                try:
                    return int(line.split()[0])
                except (ValueError, IndexError):
                    pass
        return 0
    
    def _extract_slow_tests(self, output: str) -> List[Dict[str, str]]:
        """Extract slowest tests from pytest output."""
        slow_tests = []
        in_durations = False
        
        for line in output.split('\n'):
            if "slowest" in line and "durations" in line:
                in_durations = True
                continue
            elif in_durations and line.startswith('='):
                break
            elif in_durations and line.strip():
                parts = line.strip().split()
                if len(parts) >= 3:
                    duration = parts[0]
                    test_name = parts[-1] if '::' in parts[-1] else ' '.join(parts[2:])
                    slow_tests.append({
                        "duration": duration,
                        "test": test_name
                    })
        
        return slow_tests[:5]  # Top 5 slowest tests
    
    def _extract_collected_count(self, output: str) -> int:
        """Extract collected test count from pytest output."""
        for line in output.split('\n'):
            if "collected" in line:
                try:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if "collected" in part and i > 0:
                            return int(parts[i-1])
                except (ValueError, IndexError):
                    pass
        return 0
    
    def _save_benchmark_results(self, results: Dict[str, Any]):
        """Save benchmark results to cache."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = self.cache_dir / "performance_benchmarks.json"
        
        # Load existing data
        existing_data = {}
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    existing_data = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        # Add timestamp and save
        results["timestamp"] = time.time()
        existing_data[str(int(time.time()))] = results
        
        # Keep only last 10 benchmark runs
        if len(existing_data) > 10:
            oldest_keys = sorted(existing_data.keys())[:-10]
            for key in oldest_keys:
                del existing_data[key]
        
        with open(cache_file, 'w') as f:
            json.dump(existing_data, f, indent=2)
    
    def generate_performance_report(self) -> str:
        """Generate comprehensive performance report."""
        if not self.performance_data:
            # Try to load from cache
            cache_file = self.cache_dir / "performance_benchmarks.json"
            if cache_file.exists():
                try:
                    with open(cache_file, 'r') as f:
                        cached_data = json.load(f)
                        if cached_data:
                            latest_key = max(cached_data.keys())
                            self.performance_data = cached_data[latest_key]
                except (json.JSONDecodeError, FileNotFoundError):
                    pass
        
        report = []
        report.append("📈 LinkedIn Ingestion Test Performance Report")
        report.append("=" * 55)
        
        if not self.performance_data:
            report.append("No performance data available. Run benchmark first.")
            return "\n".join(report)
        
        # Unit test performance
        unit_data = self.performance_data.get("unit_tests", {})
        if unit_data:
            report.append(f"\n🚀 Unit Test Performance:")
            report.append(f"   Tests executed: {unit_data.get('test_count', 'unknown')}")
            report.append(f"   Total duration: {unit_data.get('duration', 0):.2f}s")
            if unit_data.get('test_count', 0) > 0:
                avg_time = unit_data.get('duration', 0) / unit_data.get('test_count', 1)
                report.append(f"   Average per test: {avg_time:.3f}s")
            
            slow_tests = unit_data.get('slowest_tests', [])
            if slow_tests:
                report.append(f"\n   📊 Slowest Unit Tests:")
                for test in slow_tests[:3]:
                    report.append(f"      {test.get('duration', 'N/A')}: {test.get('test', 'Unknown')}")
        
        # Parallel execution performance
        parallel_data = self.performance_data.get("parallel_tests", {})
        if parallel_data:
            report.append(f"\n⚡ Parallel Execution:")
            report.append(f"   Workers: {parallel_data.get('workers', 'unknown')}")
            report.append(f"   Duration: {parallel_data.get('duration', 0):.2f}s")
            speedup = parallel_data.get('speedup', 0)
            if speedup > 0:
                report.append(f"   Speedup: {speedup:.2f}x")
                efficiency = speedup / parallel_data.get('workers', 1) * 100
                report.append(f"   Efficiency: {efficiency:.1f}%")
        
        # Test discovery performance
        discovery_data = self.performance_data.get("test_discovery", {})
        if discovery_data:
            report.append(f"\n🔍 Test Discovery:")
            report.append(f"   Total tests found: {discovery_data.get('total_tests', 'unknown')}")
            report.append(f"   Discovery time: {discovery_data.get('duration', 0):.2f}s")
        
        # Performance recommendations
        report.append(f"\n💡 Performance Recommendations:")
        
        # Check if parallel execution is beneficial
        if parallel_data.get('speedup', 0) > 1.2:
            report.append(f"   ✅ Parallel execution is beneficial (use -n 2 or more)")
        elif parallel_data.get('speedup', 0) > 0:
            report.append(f"   ⚠️  Parallel execution shows modest improvement")
        
        # Check for slow tests
        slow_tests = unit_data.get('slowest_tests', [])
        if slow_tests:
            slow_durations = [float(t.get('duration', '0').rstrip('s')) for t in slow_tests if t.get('duration')]
            if slow_durations and max(slow_durations) > 5.0:
                report.append(f"   🐌 Consider optimizing slow tests (>5s each)")
                report.append(f"      - Add @pytest.mark.slow for long-running tests")
                report.append(f"      - Use mocks to avoid real API calls")
        
        # Test discovery recommendations
        discovery_time = discovery_data.get('duration', 0)
        if discovery_time > 2.0:
            report.append(f"   📁 Test discovery is slow ({discovery_time:.2f}s)")
            report.append(f"      - Consider reducing test file imports")
            report.append(f"      - Use more specific test patterns")
        
        # Overall recommendations
        total_tests = discovery_data.get('total_tests', 0)
        unit_duration = unit_data.get('duration', 0)
        if total_tests > 0 and unit_duration > 0:
            tests_per_second = unit_data.get('test_count', 0) / unit_duration
            report.append(f"\n📊 Test Execution Rate: {tests_per_second:.1f} tests/second")
            
            if tests_per_second < 5:
                report.append(f"   📈 Optimization Priority: HIGH")
                report.append(f"      - Focus on reducing test execution time")
                report.append(f"      - Implement more aggressive mocking")
            elif tests_per_second < 10:
                report.append(f"   📈 Optimization Priority: MEDIUM")
                report.append(f"      - Consider selective test execution")
            else:
                report.append(f"   📈 Optimization Priority: LOW")
                report.append(f"      - Current performance is good")
        
        report.append(f"\n🔧 Quick Optimization Commands:")
        report.append(f"   ./scripts/test_runners.sh fast    # Run only fast tests")
        report.append(f"   python scripts/test_optimization.py    # Smart test selection")
        report.append(f"   pytest -n auto    # Auto-detect optimal worker count")
        
        return "\n".join(report)
    
    def compare_with_baseline(self, baseline_file: Optional[str] = None) -> str:
        """Compare current performance with baseline."""
        # This would implement comparison with historical data
        return "Baseline comparison not implemented yet"


def main():
    """Main entry point for performance analysis."""
    if len(sys.argv) > 1 and sys.argv[1] == "benchmark":
        analyzer = TestPerformanceAnalyzer()
        print("Running comprehensive benchmark...")
        analyzer.run_performance_benchmark()
        print("\nGenerating performance report...")
        report = analyzer.generate_performance_report()
        print(report)
    else:
        # Just generate report from cached data
        analyzer = TestPerformanceAnalyzer()
        report = analyzer.generate_performance_report()
        print(report)


if __name__ == "__main__":
    main()
