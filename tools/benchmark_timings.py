#!/usr/bin/env python3
"""
Benchmark Timings - Performance measurement tool for the Football Match Tracking System

This tool measures and records execution time for key operations in the pipeline:
1. JSON fetch operation
2. Merge and enrichment
3. Summary generation
4. Alert processing

Usage:
    - Run directly to generate a baseline benchmark
    - Import benchmark_operation decorator in production code
"""

import time
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from functools import wraps
from typing import Dict, List, Callable, Any, Optional

# Ensure benchmark directory exists
BENCHMARK_DIR = Path(__file__).parent / "benchmarks"
BENCHMARK_DIR.mkdir(exist_ok=True, parents=True)

# File to store benchmark results
BENCHMARK_FILE = BENCHMARK_DIR / "pipeline_benchmarks.json"

def load_benchmarks() -> Dict:
    """Load existing benchmark data."""
    if BENCHMARK_FILE.exists():
        try:
            with open(BENCHMARK_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Could not parse benchmark file {BENCHMARK_FILE}")
    
    # Return default structure if file doesn't exist or can't be parsed
    return {
        "benchmarks": [],
        "summary": {}
    }

def save_benchmarks(data: Dict) -> None:
    """Save benchmark data to file."""
    with open(BENCHMARK_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def benchmark_operation(operation_name: str):
    """
    Decorator to benchmark an operation and record its execution time.
    
    Args:
        operation_name: Name of the operation to benchmark
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Record start time
            start_time = time.time()
            
            # Call original function
            result = func(*args, **kwargs)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Load existing benchmarks
            benchmarks = load_benchmarks()
            
            # Add new benchmark
            benchmark_entry = {
                "timestamp": datetime.now().isoformat(),
                "operation": operation_name,
                "execution_time": execution_time,
                "sys_info": {
                    "python_version": sys.version,
                }
            }
            
            benchmarks["benchmarks"].append(benchmark_entry)
            
            # Update summary statistics
            if "operations" not in benchmarks["summary"]:
                benchmarks["summary"]["operations"] = {}
                
            if operation_name not in benchmarks["summary"]["operations"]:
                benchmarks["summary"]["operations"][operation_name] = {
                    "count": 0,
                    "total_time": 0,
                    "min_time": float('inf'),
                    "max_time": 0,
                    "avg_time": 0
                }
                
            # Update operation stats
            op_stats = benchmarks["summary"]["operations"][operation_name]
            op_stats["count"] += 1
            op_stats["total_time"] += execution_time
            op_stats["min_time"] = min(op_stats["min_time"], execution_time)
            op_stats["max_time"] = max(op_stats["max_time"], execution_time)
            op_stats["avg_time"] = op_stats["total_time"] / op_stats["count"]
            
            # Save updated benchmarks
            save_benchmarks(benchmarks)
            
            # Print benchmark info
            print(f"[BENCHMARK] {operation_name}: {execution_time:.4f}s")
            
            return result
        return wrapper
    return decorator

def run_mock_benchmarks():
    """Run mock benchmarks to generate initial data."""
    @benchmark_operation("json_fetch")
    def mock_json_fetch():
        print("Simulating JSON fetch operation...")
        time.sleep(0.5)  # Simulate work
        return {"matches": [{"id": "1234", "status": "IN_PROGRESS"}]}
    
    @benchmark_operation("merge_and_enrich")
    def mock_merge():
        print("Simulating merge and enrichment operation...")
        time.sleep(0.8)  # Simulate work
        return [{"id": "1234", "status": "IN_PROGRESS", "enriched": True}]
    
    @benchmark_operation("summary_generation")
    def mock_summary():
        print("Simulating summary generation...")
        time.sleep(0.3)  # Simulate work
        return {"summaries": ["Match 1: Team A vs Team B"]}
    
    @benchmark_operation("alert_processing")
    def mock_alerts():
        print("Simulating alert processing...")
        time.sleep(0.2)  # Simulate work
        return {"alerts": []}
    
    # Run mock operations
    data = mock_json_fetch()
    enriched = mock_merge()
    summary = mock_summary()
    alerts = mock_alerts()
    
    print("\nMock benchmark run complete. Results saved to:", BENCHMARK_FILE)

def generate_report():
    """Generate a human-readable report of benchmark results."""
    benchmarks = load_benchmarks()
    
    if not benchmarks["benchmarks"]:
        print("No benchmark data available.")
        return
    
    report = []
    report.append("# Football Match Tracking System - Performance Benchmark Report")
    report.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # Operation statistics
    report.append("## Operation Performance Summary")
    report.append("")
    report.append("| Operation | Count | Avg Time (s) | Min Time (s) | Max Time (s) |")
    report.append("|-----------|-------|--------------|--------------|--------------|")
    
    for op_name, stats in benchmarks["summary"].get("operations", {}).items():
        report.append(f"| {op_name} | {stats['count']} | {stats['avg_time']:.4f} | {stats['min_time']:.4f} | {stats['max_time']:.4f} |")
    
    report.append("")
    report.append("## Recent Benchmark Runs")
    report.append("")
    
    # Show last 10 benchmark runs
    recent_runs = benchmarks["benchmarks"][-10:]
    for i, run in enumerate(recent_runs):
        report.append(f"### Run {i+1} - {run['timestamp']}")
        report.append(f"Operation: {run['operation']}")
        report.append(f"Execution Time: {run['execution_time']:.4f}s")
        report.append("")
    
    report_path = BENCHMARK_DIR / "benchmark_report.md"
    with open(report_path, 'w') as f:
        f.write("\n".join(report))
    
    print(f"Benchmark report generated at: {report_path}")

def main():
    """Main function to run benchmarks and generate report."""
    print("=== Football Match Tracking System - Benchmark Tool ===")
    
    # Run mock benchmarks to generate initial data
    run_mock_benchmarks()
    
    # Generate report
    generate_report()

if __name__ == "__main__":
    main()
