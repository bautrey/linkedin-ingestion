#!/bin/bash

# Safe Railway log viewer that prevents terminal hangs
# Usage: ./safe_logs.sh [lines]

LINES=${1:-20}
TIMEOUT_DURATION=5

echo "Attempting to get Railway logs safely..."
echo "⚠️  This will timeout after ${TIMEOUT_DURATION} seconds to prevent hanging"
echo ""

# Try to use built-in timeout if available, otherwise use a background job approach
if command -v gtimeout &> /dev/null; then
    echo "Using gtimeout..."
    gtimeout ${TIMEOUT_DURATION} railway logs --json | head -${LINES}
elif command -v timeout &> /dev/null; then
    echo "Using timeout..."
    timeout ${TIMEOUT_DURATION} railway logs --json | head -${LINES}
else
    echo "Using background job approach..."
    # Run railway logs in background and kill it after timeout
    railway logs --json | head -${LINES} &
    LOGS_PID=$!
    
    # Kill the process after timeout
    (sleep ${TIMEOUT_DURATION} && kill $LOGS_PID 2>/dev/null) &
    TIMEOUT_PID=$!
    
    # Wait for logs to complete or timeout
    wait $LOGS_PID 2>/dev/null
    LOGS_EXIT_CODE=$?
    
    # Clean up timeout process
    kill $TIMEOUT_PID 2>/dev/null
    
    if [ $LOGS_EXIT_CODE -ne 0 ]; then
        echo "⚠️  Logs command timed out or failed. Use 'railway open' to view logs in browser."
    fi
fi

echo ""
echo "💡 For full logs without timeout risk, use: railway open"
echo "   This opens the Railway dashboard in your browser with full log access."
