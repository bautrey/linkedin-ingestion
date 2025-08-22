#!/usr/bin/env python3
"""
Simple Railway Webhook Format Debugger

Tests the webhook detection logic without requiring external dependencies.
"""

import sys
import json
from datetime import datetime

# Add scripts to path to import webhook listener
sys.path.append('scripts')

def get_sample_railway_payloads():
    """Get sample Railway webhook payloads for testing"""
    return [
        # Build started
        {
            "event": "deployment.started",
            "type": "deployment",
            "status": "BUILDING",
            "deploymentId": "test-deployment-123",
            "service": "smooth-mailbox",
            "environment": "production",
            "timestamp": datetime.now().isoformat()
        },
        
        # Build completed, deployment starting
        {
            "event": "deployment.building",
            "type": "deployment", 
            "status": "DEPLOYING",
            "deploymentId": "test-deployment-123",
            "service": "smooth-mailbox",
            "environment": "production",
            "timestamp": datetime.now().isoformat()
        },
        
        # Deployment successful - should trigger completion
        {
            "event": "deployment.success",
            "type": "deployment",
            "status": "SUCCESS",
            "deploymentId": "test-deployment-123",
            "service": "smooth-mailbox",
            "environment": "production",
            "timestamp": datetime.now().isoformat(),
            "url": "https://smooth-mailbox-production.up.railway.app"
        },
        
        # Alternative success format - should trigger completion
        {
            "status": "DEPLOYED",
            "deployment": {
                "id": "test-deployment-456",
                "status": "SUCCESS",
                "url": "https://smooth-mailbox-production.up.railway.app"
            },
            "timestamp": datetime.now().isoformat()
        },
        
        # Build failure - should NOT trigger completion
        {
            "event": "deployment.failed",
            "type": "deployment",
            "status": "FAILED",
            "deploymentId": "test-deployment-789",
            "service": "smooth-mailbox",
            "environment": "production",
            "error": "Build failed: dependency resolution error",
            "timestamp": datetime.now().isoformat()
        },
        
        # Real Railway webhook example (guessed format)
        {
            "id": "deployment-abc123",
            "status": "DEPLOYED",
            "environment": {
                "name": "production",
                "id": "env-123"
            },
            "service": {
                "name": "smooth-mailbox",
                "id": "svc-456"
            },
            "createdAt": datetime.now().isoformat(),
            "finishedAt": datetime.now().isoformat()
        }
    ]

def create_mock_handler():
    """Create a mock handler to test detection logic"""
    class MockHandler:
        def is_deployment_complete(self, payload):
            """Check if the webhook payload indicates deployment completion"""
            # Common Railway webhook patterns for successful deployments
            success_indicators = [
                payload.get('status') == 'SUCCESS',
                payload.get('status') == 'DEPLOYED',
                payload.get('deployment', {}).get('status') == 'SUCCESS',
                payload.get('event') == 'deployment.success',
                payload.get('type') == 'deployment.completed',
                'success' in str(payload).lower(),
                'deployed' in str(payload).lower()
            ]
            
            return any(success_indicators)
    
    return MockHandler()

def analyze_webhook_detection():
    """Analyze webhook detection logic"""
    print("🔍 Railway Webhook Detection Analysis")
    print("=" * 50)
    
    handler = create_mock_handler()
    payloads = get_sample_railway_payloads()
    
    print("\n📋 Expected Railway webhook patterns:")
    patterns = [
        "event: 'deployment.success'",
        "status: 'SUCCESS'", 
        "status: 'DEPLOYED'",
        "deployment.status: 'SUCCESS'",
        "type: 'deployment.completed'",
        "Contains 'success' (string match)",
        "Contains 'deployed' (string match)"
    ]
    
    for pattern in patterns:
        print(f"   ✓ {pattern}")
    
    print(f"\n🧪 Testing detection logic with {len(payloads)} sample payloads:")
    print("-" * 50)
    
    for i, payload in enumerate(payloads):
        result = handler.is_deployment_complete(payload)
        event_or_status = payload.get('event', payload.get('status', 'unknown'))
        status_emoji = "✅ DETECTED" if result else "❌ NOT DETECTED"
        
        print(f"{i+1:2d}. {status_emoji} - {event_or_status}")
        
        # Show which indicators matched
        if result:
            matched_indicators = []
            if payload.get('status') == 'SUCCESS':
                matched_indicators.append("status: 'SUCCESS'")
            if payload.get('status') == 'DEPLOYED':
                matched_indicators.append("status: 'DEPLOYED'")
            if payload.get('deployment', {}).get('status') == 'SUCCESS':
                matched_indicators.append("deployment.status: 'SUCCESS'")
            if payload.get('event') == 'deployment.success':
                matched_indicators.append("event: 'deployment.success'")
            if payload.get('type') == 'deployment.completed':
                matched_indicators.append("type: 'deployment.completed'")
            if 'success' in str(payload).lower():
                matched_indicators.append("contains 'success'")
            if 'deployed' in str(payload).lower():
                matched_indicators.append("contains 'deployed'")
            
            print(f"    🎯 Matched: {', '.join(matched_indicators)}")
        
        print(f"    📄 Payload: {json.dumps(payload, indent=6)[:100]}...")
        print()

def identify_potential_issues():
    """Identify potential issues with webhook setup"""
    print("\n🚨 Potential Issues with Railway Webhook System:")
    print("=" * 50)
    
    issues = [
        {
            "issue": "Railway webhook URL not configured",
            "description": "Webhook URL must be set in Railway project settings",
            "solution": "Go to Railway Dashboard > Project > Settings > Webhooks"
        },
        {
            "issue": "Localhost webhook URL not accessible from Railway",
            "description": "Railway can't reach http://localhost:3000 from their servers",
            "solution": "Use ngrok or similar to create public tunnel, or use public webhook endpoint"
        },
        {
            "issue": "Webhook payload format mismatch",
            "description": "Actual Railway webhook format might differ from expected patterns",
            "solution": "Capture real webhook payload from Railway for analysis"
        },
        {
            "issue": "Multiple deployments triggered",
            "description": "Railway might send multiple webhooks causing listener to exit early",
            "solution": "Modify listener to handle multiple deployment notifications"
        },
        {
            "issue": "Network/firewall issues",
            "description": "Local firewall or network config blocking webhook requests",
            "solution": "Check firewall settings, try different port"
        }
    ]
    
    for i, issue in enumerate(issues, 1):
        print(f"{i}. ❌ {issue['issue']}")
        print(f"   📝 Problem: {issue['description']}")
        print(f"   💡 Solution: {issue['solution']}")
        print()

def suggest_improvements():
    """Suggest improvements to webhook system"""
    print("💡 Suggested Improvements:")
    print("=" * 30)
    
    improvements = [
        "Add webhook URL validation and reachability test",
        "Create ngrok integration for public webhook endpoint", 
        "Implement webhook payload logging for format analysis",
        "Add retry logic for webhook listener",
        "Create webhook configuration wizard",
        "Add webhook testing with mock Railway payloads",
        "Implement fallback to polling-based deployment detection"
    ]
    
    for i, improvement in enumerate(improvements, 1):
        print(f"{i}. 🔧 {improvement}")

def main():
    print("🚀 Railway Webhook Format Debugger")
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    analyze_webhook_detection()
    identify_potential_issues() 
    suggest_improvements()
    
    print("\n" + "=" * 50)
    print("🎯 CONCLUSION:")
    print("The webhook detection logic appears correct for standard Railway webhook formats.")
    print("The main issue is likely that Railway cannot reach the localhost webhook URL.")
    print("Consider using a public tunnel (ngrok) or the polling-based deployment monitor instead.")

if __name__ == "__main__":
    main()
