#!/usr/bin/env python3
"""
Railway Logs - Common Usage Examples

This module provides pre-built patterns for common Railway log queries
to help you get insights quickly without writing complex filter strings.

Usage:
    python railway_examples.py [pattern_name]
    
Available patterns:
    errors_last_hour     - All errors and warnings from the last hour
    http_5xx             - HTTP 500-level errors from the last 2 hours  
    slow_requests        - Requests taking >5s (if logged appropriately)
    database_errors      - Database connection and query errors
    memory_warnings      - Memory usage warnings
    deployment_failures  - Recent deployment failures
    recent_builds        - Last 5 build logs
"""

import sys
import argparse
from datetime import datetime, timedelta
from railway_logs import RailwayLogsCLI


class RailwayExamples:
    """Pre-defined Railway log query patterns"""
    
    def __init__(self):
        self.cli = RailwayLogsCLI()
    
    def errors_last_hour(self):
        """Get all errors and warnings from the last hour"""
        print("🔍 Fetching errors and warnings from the last hour...")
        
        class Args:
            log_type = 'deployment'
            errors_only = True
            last_hours = 1
            limit = 200
            json = False
            filter = None
            since = None
            until = None
            last_minutes = None
            last_days = None
            status_code = None
            method = None
        
        if not self.cli._initialize_client():
            return
        
        logs = self.cli.get_deployment_logs(Args())
        
        if not logs:
            print("✅ No errors found in the last hour!")
            return
        
        print(f"❌ Found {len(logs)} error/warning entries:")
        print("─" * 60)
        
        for log in logs:
            print(self.cli._format_log_entry(log))
    
    def http_5xx(self):
        """Get HTTP 500-level errors from the last 2 hours"""
        print("🔍 Fetching HTTP 5xx errors from the last 2 hours...")
        
        class Args:
            log_type = 'http'
            errors_only = False
            last_hours = 2
            limit = 100
            json = False
            filter = "@httpStatus:>=500"
            since = None
            until = None
            last_minutes = None
            last_days = None
            status_code = None
            method = None
        
        if not self.cli._initialize_client():
            return
        
        logs = self.cli.get_http_logs(Args())
        
        if not logs:
            print("✅ No HTTP 5xx errors found!")
            return
        
        print(f"❌ Found {len(logs)} HTTP 5xx errors:")
        print("─" * 60)
        
        for log in logs:
            print(self.cli._format_log_entry(log))
    
    def slow_requests(self):
        """Find potentially slow requests (basic pattern matching)"""
        print("🔍 Looking for slow requests and timeouts...")
        
        class Args:
            log_type = 'deployment'
            errors_only = False
            last_hours = 2
            limit = 100
            json = False
            filter = "timeout OR slow OR \"response time\" OR \"took\" OR \"duration\""
            since = None
            until = None
            last_minutes = None
            last_days = None
            status_code = None
            method = None
        
        if not self.cli._initialize_client():
            return
        
        logs = self.cli.get_deployment_logs(Args())
        
        if not logs:
            print("✅ No slow request indicators found!")
            return
        
        print(f"⏱️  Found {len(logs)} potential slow request entries:")
        print("─" * 60)
        
        for log in logs:
            print(self.cli._format_log_entry(log))
    
    def database_errors(self):
        """Find database-related errors"""
        print("🔍 Looking for database connection and query errors...")
        
        class Args:
            log_type = 'deployment'
            errors_only = True
            last_hours = 4
            limit = 100
            json = False
            filter = "database OR postgres OR sql OR connection OR \"could not connect\" OR \"timeout\" OR \"deadlock\""
            since = None
            until = None
            last_minutes = None
            last_days = None
            status_code = None
            method = None
        
        if not self.cli._initialize_client():
            return
        
        logs = self.cli.get_deployment_logs(Args())
        
        if not logs:
            print("✅ No database errors found!")
            return
        
        print(f"🗄️  Found {len(logs)} database-related errors:")
        print("─" * 60)
        
        for log in logs:
            print(self.cli._format_log_entry(log))
    
    def memory_warnings(self):
        """Find memory usage warnings and OOM events"""
        print("🔍 Looking for memory warnings and out-of-memory events...")
        
        class Args:
            log_type = 'deployment'
            errors_only = False
            last_hours = 6
            limit = 100
            json = False
            filter = "memory OR oom OR \"out of memory\" OR \"killed\" OR \"malloc\""
            since = None
            until = None
            last_minutes = None
            last_days = None
            status_code = None
            method = None
        
        if not self.cli._initialize_client():
            return
        
        logs = self.cli.get_deployment_logs(Args())
        
        if not logs:
            print("✅ No memory warnings found!")
            return
        
        print(f"💾 Found {len(logs)} memory-related entries:")
        print("─" * 60)
        
        for log in logs:
            print(self.cli._format_log_entry(log))
    
    def deployment_failures(self):
        """Find recent deployment failures"""
        print("🔍 Looking for deployment failures and build errors...")
        
        class Args:
            log_type = 'build'
            errors_only = False
            last_hours = 24
            limit = 50
            json = False
            filter = "@level:error OR failed OR failure OR \"build failed\" OR \"deployment failed\""
            since = None
            until = None
            last_minutes = None
            last_days = None
            status_code = None
            method = None
        
        if not self.cli._initialize_client():
            return
        
        logs = self.cli.get_build_logs(Args())
        
        if not logs:
            print("✅ No deployment failures found!")
            return
        
        print(f"🚨 Found {len(logs)} deployment failure entries:")
        print("─" * 60)
        
        for log in logs:
            print(self.cli._format_log_entry(log))
    
    def recent_builds(self):
        """Get the last 5 build logs"""
        print("🔍 Fetching recent build logs...")
        
        class Args:
            log_type = 'build'
            errors_only = False
            last_hours = 24
            limit = 50
            json = False
            filter = None
            since = None
            until = None
            last_minutes = None
            last_days = None
            status_code = None
            method = None
        
        if not self.cli._initialize_client():
            return
        
        logs = self.cli.get_build_logs(Args())
        
        if not logs:
            print("📦 No recent builds found!")
            return
        
        print(f"📦 Recent build logs ({len(logs)} entries):")
        print("─" * 60)
        
        for log in logs[:20]:  # Show only first 20 for readability
            print(self.cli._format_log_entry(log))
        
        if len(logs) > 20:
            print(f"... and {len(logs) - 20} more entries")


def main():
    parser = argparse.ArgumentParser(
        description="Railway Logs - Common Usage Examples",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available patterns:
  errors_last_hour     - All errors and warnings from the last hour
  http_5xx             - HTTP 500-level errors from the last 2 hours  
  slow_requests        - Requests taking >5s (if logged appropriately)
  database_errors      - Database connection and query errors
  memory_warnings      - Memory usage warnings
  deployment_failures  - Recent deployment failures
  recent_builds        - Last 5 build logs

Examples:
  %(prog)s errors_last_hour
  %(prog)s http_5xx
  %(prog)s database_errors
        """
    )
    
    parser.add_argument(
        'pattern',
        choices=[
            'errors_last_hour',
            'http_5xx',
            'slow_requests',
            'database_errors',
            'memory_warnings',
            'deployment_failures',
            'recent_builds'
        ],
        help='Log pattern to search for'
    )
    
    args = parser.parse_args()
    
    examples = RailwayExamples()
    pattern_func = getattr(examples, args.pattern)
    
    print(f"🚂 Railway Logs - {args.pattern.replace('_', ' ').title()}")
    print("=" * 60)
    print()
    
    try:
        pattern_func()
    except Exception as e:
        print(f"❌ Error running pattern '{args.pattern}': {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
