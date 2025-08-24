#!/usr/bin/env python3
"""
Simple Railway Logs Fetcher

A hybrid approach that uses the Railway CLI with proper timeout handling
to avoid terminal hanging issues.
"""

import subprocess
import sys
import json
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional


def run_railway_command_with_timeout(cmd: List[str], timeout: int = 10) -> tuple[int, str, str]:
    """Run railway command with timeout"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 124, "", f"Command timed out after {timeout} seconds"
    except Exception as e:
        return 1, "", str(e)


def get_railway_logs(log_type: str = "deployment", limit: int = 100, json_output: bool = False) -> List[Dict[str, Any]]:
    """Get Railway logs using CLI with timeout protection"""
    
    # Build command
    cmd = ["railway", "logs"]
    
    if log_type == "build":
        cmd.append("--build")
    elif log_type == "deployment":
        cmd.append("--deployment")
    
    if json_output:
        cmd.append("--json")
    
    print(f"🚂 Running: {' '.join(cmd)} (with {limit} line limit)")
    
    # Run with timeout
    returncode, stdout, stderr = run_railway_command_with_timeout(cmd, timeout=15)
    
    if returncode == 124:
        print("⚠️ Railway logs command timed out - this is expected behavior")
        print("   We'll process whatever output we captured...")
    elif returncode != 0:
        print(f"❌ Railway command failed: {stderr}")
        return []
    
    if not stdout.strip():
        print("📭 No log output received")
        return []
    
    # Process output
    lines = stdout.strip().split('\n')
    processed_logs = []
    
    # Limit output
    if limit > 0:
        lines = lines[:limit]
    
    if json_output:
        # Parse JSON logs
        for line in lines:
            line = line.strip()
            if line and line.startswith('{'):
                try:
                    log_entry = json.loads(line)
                    processed_logs.append(log_entry)
                except json.JSONDecodeError:
                    # Fallback for non-JSON lines
                    processed_logs.append({
                        'timestamp': datetime.utcnow().isoformat() + 'Z',
                        'message': line,
                        'severity': 'INFO'
                    })
    else:
        # Parse text logs
        for i, line in enumerate(lines):
            line = line.strip()
            if line:
                processed_logs.append({
                    'index': i,
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'message': line,
                    'severity': 'INFO'
                })
    
    return processed_logs


def format_log_entry(log: Dict[str, Any], json_format: bool = False) -> str:
    """Format a log entry for display"""
    if json_format:
        return json.dumps(log, indent=2)
    
    # Extract components
    timestamp = log.get('timestamp', 'N/A')
    severity = log.get('severity', 'INFO').upper()
    message = log.get('message', '')
    
    # Format timestamp
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        time_str = dt.strftime('%H:%M:%S')
    except:
        time_str = timestamp[:8] if len(timestamp) > 8 else timestamp
    
    # Color-code severity
    colors = {
        'ERROR': '\033[91m',   # Red
        'WARN': '\033[93m',    # Yellow
        'WARNING': '\033[93m', # Yellow
        'INFO': '\033[94m',    # Blue
        'DEBUG': '\033[90m',   # Gray
    }
    
    color = colors.get(severity, '')
    reset = '\033[0m' if color else ''
    
    return f"{time_str} {color}[{severity:5}]{reset} {message}"


def main():
    parser = argparse.ArgumentParser(
        description="Simple Railway Logs - Terminal-safe log retrieval",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s deployment --limit 50
  %(prog)s build --limit 20
  %(prog)s deployment --json
        """
    )
    
    parser.add_argument(
        'log_type',
        choices=['deployment', 'build'],
        help='Type of logs to retrieve'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=100,
        help='Maximum number of log lines to retrieve (default: 100)'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output logs in JSON format'
    )
    
    args = parser.parse_args()
    
    print("🚂 Railway Logs - Simple CLI Wrapper")
    print("=" * 50)
    
    # Fetch logs
    logs = get_railway_logs(
        log_type=args.log_type,
        limit=args.limit,
        json_output=args.json
    )
    
    if not logs:
        print("\n📭 No logs found")
        return
    
    print(f"\n📋 Retrieved {len(logs)} log entries:")
    print("-" * 50)
    
    # Display logs
    for log in logs:
        print(format_log_entry(log, args.json))


if __name__ == "__main__":
    main()
