#!/bin/bash

# Safe Railway log viewer that prevents terminal hangs
# Now uses GraphQL API instead of CLI to avoid hanging
# Usage: ./safe_logs.sh [type] [options]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RAILWAY_LOGS_SCRIPT="$SCRIPT_DIR/scripts/railway_logs.py"
RAILWAY_EXAMPLES_SCRIPT="$SCRIPT_DIR/scripts/railway_examples.py"

# Activate virtual environment if it exists
if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
fi

# Use python from virtual environment or system python3
PYTHON_CMD="python3"
if [ -n "$VIRTUAL_ENV" ]; then
    PYTHON_CMD="python"
fi

# Default values
LOG_TYPE="deployment"
LIMIT=50
LAST_HOURS=1
ERRORS_ONLY=false

# Function to display help
show_help() {
    cat << EOF
🚂 Safe Railway Logs - Terminal-Safe Log Retrieval

Usage: 
    $0 [type] [options]            # Get specific log types
    $0 examples [pattern]          # Use pre-built patterns
    $0 help                        # Show this help

Log Types:
    deployment  - Runtime/deployment logs (default)
    build       - Build process logs  
    http        - HTTP request logs
    all         - All log types

Common Options:
    --errors-only          # Only show errors and warnings
    --last-hours N         # Get logs from last N hours (default: 1)
    --last-minutes N       # Get logs from last N minutes
    --limit N             # Maximum logs to retrieve (default: 50)
    --json                # Output in JSON format

Example Patterns:
    errors_last_hour      # All errors from the last hour
    http_5xx              # HTTP 500-level errors
    database_errors       # Database connection errors
    slow_requests         # Potentially slow requests
    memory_warnings       # Memory usage warnings
    deployment_failures   # Recent deployment failures
    recent_builds         # Recent build logs

Examples:
    $0                              # Default: deployment logs, last hour
    $0 deployment --errors-only     # Only deployment errors 
    $0 http --last-minutes 30       # HTTP logs from last 30 minutes
    $0 examples errors_last_hour    # Pre-built error pattern
    $0 build --limit 100            # Last 100 build log entries
    $0 all --json --limit 20        # All logs as JSON

Migration from old 'railway logs':
    railway logs                    → $0
    railway logs --deployment       → $0 deployment  
    railway logs --build           → $0 build

💡 This tool uses Railway's GraphQL API to avoid terminal hanging issues.
EOF
}

# Check if Python script exists
if [ ! -f "$RAILWAY_LOGS_SCRIPT" ]; then
    echo "❌ Railway logs script not found at: $RAILWAY_LOGS_SCRIPT"
    echo "   Make sure you're running this from the project root directory."
    exit 1
fi

# Handle help
if [ "$1" = "help" ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_help
    exit 0
fi

# Handle examples
if [ "$1" = "examples" ]; then
    if [ -z "$2" ]; then
        echo "🚂 Available Example Patterns:"
        echo "================================"
        $PYTHON_CMD "$RAILWAY_EXAMPLES_SCRIPT" --help
        exit 0
    else
        echo "🚂 Running Railway Logs Example: $2"
        exec $PYTHON_CMD "$RAILWAY_EXAMPLES_SCRIPT" "$2"
    fi
fi

# Parse log type
if [[ "$1" =~ ^(deployment|build|http|all)$ ]]; then
    LOG_TYPE="$1"
    shift
fi

# Build command arguments
CMD_ARGS=("$LOG_TYPE")

# Parse additional options
while [[ $# -gt 0 ]]; do
    case $1 in
        --errors-only)
            CMD_ARGS+=("--errors-only")
            shift
            ;;
        --last-hours)
            CMD_ARGS+=("--last-hours" "$2")
            shift 2
            ;;
        --last-minutes)
            CMD_ARGS+=("--last-minutes" "$2")
            shift 2
            ;;
        --last-days)
            CMD_ARGS+=("--last-days" "$2")
            shift 2
            ;;
        --limit)
            CMD_ARGS+=("--limit" "$2")
            shift 2
            ;;
        --json)
            CMD_ARGS+=("--json")
            shift
            ;;
        --filter)
            CMD_ARGS+=("--filter" "$2")
            shift 2
            ;;
        --status-code)
            CMD_ARGS+=("--status-code" "$2")
            shift 2
            ;;
        --method)
            CMD_ARGS+=("--method" "$2")
            shift 2
            ;;
        --since)
            CMD_ARGS+=("--since" "$2")
            shift 2
            ;;
        --until)
            CMD_ARGS+=("--until" "$2")
            shift 2
            ;;
        *)
            echo "❌ Unknown option: $1"
            echo "   Run '$0 help' for usage information"
            exit 1
            ;;
    esac
done

# Add default options if none specified
if [[ ! " ${CMD_ARGS[@]} " =~ " --last-" ]] && [[ ! " ${CMD_ARGS[@]} " =~ " --since" ]]; then
    CMD_ARGS+=("--last-hours" "1")
fi

if [[ ! " ${CMD_ARGS[@]} " =~ " --limit" ]]; then
    CMD_ARGS+=("--limit" "50")
fi

echo "🚂 Railway Logs - Safe API-based log retrieval"
echo "Command: $PYTHON_CMD railway_logs.py ${CMD_ARGS[*]}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# Execute the Python script
exec $PYTHON_CMD "$RAILWAY_LOGS_SCRIPT" "${CMD_ARGS[@]}"
