#!/usr/bin/env python3
"""
Railway Logs CLI Utility

A robust alternative to 'railway logs' that won't hang your terminal.
Uses Railway's GraphQL API to fetch logs in bounded time windows.

Usage Examples:
    # Get last 100 deployment logs
    python railway_logs.py deployment --limit 100
    
    # Get errors from the last hour
    python railway_logs.py deployment --errors-only --last-hours 1
    
    # Get HTTP 5xx errors
    python railway_logs.py http --filter "@httpStatus:>=500"
    
    # Get build logs for a specific time range
    python railway_logs.py build --since "2023-08-24T10:00:00Z" --until "2023-08-24T11:00:00Z"
    
    # Get all recent logs as JSON
    python railway_logs.py all --json --limit 50
"""

import argparse
import sys
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Add the current directory to path so we can import railway_graphql
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from railway_graphql import RailwayGraphQL, RailwayConfig


class RailwayLogsCLI:
    """Command-line interface for Railway logs"""
    
    def __init__(self):
        self.client = None
    
    def _initialize_client(self) -> bool:
        """Initialize the Railway GraphQL client"""
        try:
            self.client = RailwayGraphQL()
            return True
        except Exception as e:
            print(f"❌ Failed to initialize Railway client: {e}", file=sys.stderr)
            print("\n💡 Troubleshooting tips:", file=sys.stderr)
            print("   1. Make sure you're in a Railway project directory", file=sys.stderr)
            print("   2. Run 'railway login' if not authenticated", file=sys.stderr)
            print("   3. Set RAILWAY_TOKEN environment variable", file=sys.stderr)
            return False
    
    def _parse_datetime(self, date_str: str) -> datetime:
        """Parse datetime string in various formats"""
        formats = [
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        raise ValueError(f"Unable to parse date: {date_str}")
    
    def _format_log_entry(self, log: Dict[str, Any], json_output: bool = False) -> str:
        """Format a log entry for display"""
        if json_output:
            return json.dumps(log)
        
        timestamp = log.get('timestamp', 'N/A')
        severity = log.get('severity', 'INFO').upper()
        message = log.get('message', '')
        
        # Parse timestamp for better display
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_str = dt.strftime('%H:%M:%S')
        except:
            time_str = timestamp[:8] if len(timestamp) > 8 else timestamp
        
        # Color-code severity levels
        severity_colors = {
            'ERROR': '\033[91m',    # Red
            'WARN': '\033[93m',     # Yellow
            'WARNING': '\033[93m',  # Yellow
            'INFO': '\033[94m',     # Blue
            'DEBUG': '\033[90m',    # Gray
        }
        
        color = severity_colors.get(severity, '')
        reset = '\033[0m' if color else ''
        
        return f"{time_str} {color}[{severity:5}]{reset} {message}"
    
    def get_deployment_logs(self, args) -> List[Dict[str, Any]]:
        """Get deployment/runtime logs"""
        start_date, end_date = self._calculate_time_range(args)
        
        log_filter = None
        if args.errors_only:
            log_filter = "@level:error OR @level:warn"
        elif args.filter:
            log_filter = args.filter
        
        try:
            logs = self.client.get_deployment_logs(
                start_date=start_date,
                end_date=end_date,
                limit=args.limit,
                log_filter=log_filter
            )
            
            if not logs:
                print("No deployment logs found for the specified criteria")
                return []
            
            return logs
        
        except Exception as e:
            print(f"❌ Failed to fetch deployment logs: {e}", file=sys.stderr)
            return []
    
    def get_build_logs(self, args) -> List[Dict[str, Any]]:
        """Get build logs"""
        start_date, end_date = self._calculate_time_range(args)
        
        try:
            logs = self.client.get_build_logs(
                start_date=start_date,
                end_date=end_date,
                limit=args.limit,
                log_filter=args.filter
            )
            
            if not logs:
                print("No build logs found for the specified criteria")
                return []
            
            return logs
        
        except Exception as e:
            print(f"❌ Failed to fetch build logs: {e}", file=sys.stderr)
            return []
    
    def get_http_logs(self, args) -> List[Dict[str, Any]]:
        """Get HTTP request logs"""
        start_date, end_date = self._calculate_time_range(args)
        
        log_filter = args.filter
        if args.status_code:
            status_filter = f"@httpStatus:{args.status_code}"
            log_filter = f"{log_filter} AND {status_filter}" if log_filter else status_filter
        
        if args.method:
            method_filter = f"@method:{args.method.upper()}"
            log_filter = f"{log_filter} AND {method_filter}" if log_filter else method_filter
        
        try:
            logs = self.client.get_http_logs(
                start_date=start_date,
                end_date=end_date,
                limit=args.limit,
                log_filter=log_filter
            )
            
            if not logs:
                print("No HTTP logs found for the specified criteria")
                return []
            
            return logs
        
        except Exception as e:
            print(f"❌ Failed to fetch HTTP logs: {e}", file=sys.stderr)
            return []
    
    def get_all_logs(self, args) -> List[Dict[str, Any]]:
        """Get all types of logs"""
        all_logs = []
        
        # Get deployment logs
        deployment_logs = self.get_deployment_logs(args)
        for log in deployment_logs:
            log['log_type'] = 'deployment'
        all_logs.extend(deployment_logs)
        
        # Get build logs
        build_logs = self.get_build_logs(args)
        for log in build_logs:
            log['log_type'] = 'build'
        all_logs.extend(build_logs)
        
        # Get HTTP logs
        http_logs = self.get_http_logs(args)
        for log in http_logs:
            log['log_type'] = 'http'
        all_logs.extend(http_logs)
        
        # Sort by timestamp
        all_logs.sort(key=lambda x: x.get('timestamp', ''))
        
        return all_logs
    
    def _calculate_time_range(self, args) -> tuple[Optional[datetime], Optional[datetime]]:
        """Calculate start and end dates based on arguments"""
        start_date = None
        end_date = None
        
        if args.since:
            start_date = self._parse_datetime(args.since)
        
        if args.until:
            end_date = self._parse_datetime(args.until)
        
        if args.last_minutes:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(minutes=args.last_minutes)
        elif args.last_hours:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(hours=args.last_hours)
        elif args.last_days:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=args.last_days)
        
        # Default to last hour if no time range specified
        if not start_date and not end_date:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(hours=1)
        
        return start_date, end_date
    
    def main(self):
        """Main entry point"""
        parser = argparse.ArgumentParser(
            description="Railway Logs - A terminal-safe alternative to 'railway logs'",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s deployment --limit 100
  %(prog)s deployment --errors-only --last-hours 2
  %(prog)s http --status-code 500 --last-minutes 30
  %(prog)s build --since "2023-08-24T10:00:00Z"
  %(prog)s all --json --limit 50
            """
        )
        
        # Subcommands for log types
        subparsers = parser.add_subparsers(dest='log_type', help='Type of logs to retrieve')
        
        # Common arguments for all log types
        def add_common_args(parser):
            parser.add_argument('--limit', type=int, default=100, help='Maximum number of logs to retrieve (default: 100)')
            parser.add_argument('--json', action='store_true', help='Output logs in JSON format')
            parser.add_argument('--filter', help='Custom filter string (Railway filter syntax)')
            
            # Time range options
            time_group = parser.add_mutually_exclusive_group()
            time_group.add_argument('--since', help='Start time (ISO 8601 format)')
            time_group.add_argument('--until', help='End time (ISO 8601 format)')
            time_group.add_argument('--last-minutes', type=int, help='Get logs from last N minutes')
            time_group.add_argument('--last-hours', type=int, help='Get logs from last N hours')
            time_group.add_argument('--last-days', type=int, help='Get logs from last N days')
        
        # Deployment logs
        deployment_parser = subparsers.add_parser('deployment', help='Get deployment/runtime logs')
        add_common_args(deployment_parser)
        deployment_parser.add_argument('--errors-only', action='store_true', help='Only show error and warning logs')
        
        # Build logs
        build_parser = subparsers.add_parser('build', help='Get build logs')
        add_common_args(build_parser)
        
        # HTTP logs
        http_parser = subparsers.add_parser('http', help='Get HTTP request logs')
        add_common_args(http_parser)
        http_parser.add_argument('--status-code', help='Filter by HTTP status code (e.g., 500, >=400)')
        http_parser.add_argument('--method', help='Filter by HTTP method (GET, POST, etc.)')
        
        # All logs
        all_parser = subparsers.add_parser('all', help='Get all types of logs')
        add_common_args(all_parser)
        all_parser.add_argument('--errors-only', action='store_true', help='Only show error and warning logs')
        
        args = parser.parse_args()
        
        if not args.log_type:
            parser.print_help()
            sys.exit(1)
        
        # Initialize client
        if not self._initialize_client():
            sys.exit(1)
        
        # Get logs based on type
        logs = []
        if args.log_type == 'deployment':
            logs = self.get_deployment_logs(args)
        elif args.log_type == 'build':
            logs = self.get_build_logs(args)
        elif args.log_type == 'http':
            logs = self.get_http_logs(args)
        elif args.log_type == 'all':
            logs = self.get_all_logs(args)
        
        # Output logs
        if not logs:
            print("No logs found matching the criteria")
            sys.exit(0)
        
        print(f"Found {len(logs)} log entries:")
        print()
        
        for log in logs:
            print(self._format_log_entry(log, args.json))


if __name__ == "__main__":
    cli = RailwayLogsCLI()
    cli.main()
