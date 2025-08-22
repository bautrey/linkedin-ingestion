#!/usr/bin/env python3
"""
Railway Webhook Testing & Debugging System

This script provides comprehensive testing for the Railway webhook listener
without requiring actual deployments. It can:

1. Mock Railway webhook payloads
2. Test webhook listener responses
3. Debug webhook payload formats
4. Test different Railway webhook scenarios

Usage:
    python scripts/test_webhook_system.py --test-listener
    python scripts/test_webhook_system.py --mock-railway-webhook
    python scripts/test_webhook_system.py --debug-webhook-format
    python scripts/test_webhook_system.py --full-test-suite
"""

import argparse
import json
import requests
import threading
import time
import sys
from datetime import datetime
from typing import Dict, List, Any

# Import our webhook listener
sys.path.append('scripts')
from deployment_webhook_listener import wait_for_deployment, create_webhook_server

class RailwayWebhookTester:
    """Test and debug Railway webhook functionality"""
    
    def __init__(self, listener_port=3000):
        self.listener_port = listener_port
        self.base_url = f"http://localhost:{listener_port}"
        
    def get_sample_railway_payloads(self) -> List[Dict[str, Any]]:
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
            
            # Deployment successful
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
            
            # Alternative success format
            {
                "status": "DEPLOYED",
                "deployment": {
                    "id": "test-deployment-456",
                    "status": "SUCCESS",
                    "url": "https://smooth-mailbox-production.up.railway.app"
                },
                "timestamp": datetime.now().isoformat()
            },
            
            # Build failure
            {
                "event": "deployment.failed",
                "type": "deployment",
                "status": "FAILED",
                "deploymentId": "test-deployment-789",
                "service": "smooth-mailbox",
                "environment": "production",
                "error": "Build failed: dependency resolution error",
                "timestamp": datetime.now().isoformat()
            }
        ]
    
    def test_webhook_listener_basic(self) -> bool:
        """Test basic webhook listener functionality"""
        print("🧪 Testing basic webhook listener...")
        
        # Start listener in background
        completion_event = threading.Event()
        server = create_webhook_server(self.listener_port, completion_event, debug=True)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        
        # Give server time to start
        time.sleep(1)
        
        try:
            # Test health check
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code != 200:
                print(f"❌ Health check failed: {response.status_code}")
                return False
            
            print("✅ Health check passed")
            
            # Test webhook reception
            test_payload = {
                "event": "deployment.success",
                "status": "SUCCESS",
                "deploymentId": "test-123"
            }
            
            response = requests.post(
                self.base_url,
                json=test_payload,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            if response.status_code != 200:
                print(f"❌ Webhook POST failed: {response.status_code}")
                return False
            
            print("✅ Webhook POST accepted")
            
            # Check if completion event was set
            if completion_event.wait(timeout=2):
                print("✅ Deployment completion detected correctly")
                return True
            else:
                print("❌ Deployment completion NOT detected")
                return False
                
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            return False
        finally:
            server.shutdown()
    
    def test_all_webhook_payloads(self) -> Dict[str, bool]:
        """Test all sample webhook payloads"""
        print("🧪 Testing all webhook payload formats...")
        
        results = {}
        
        for i, payload in enumerate(self.get_sample_railway_payloads()):
            payload_name = f"payload_{i+1}_{payload.get('event', payload.get('status', 'unknown'))}"
            print(f"\n📨 Testing {payload_name}...")
            
            # Start fresh listener for each test
            completion_event = threading.Event()
            server = create_webhook_server(self.listener_port + i + 1, completion_event, debug=False)
            server_thread = threading.Thread(target=server.serve_forever, daemon=True)
            server_thread.start()
            time.sleep(0.5)
            
            try:
                response = requests.post(
                    f"http://localhost:{self.listener_port + i + 1}",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=3
                )
                
                # Check if this should trigger completion
                should_complete = any([
                    payload.get('status') == 'SUCCESS',
                    payload.get('status') == 'DEPLOYED',
                    payload.get('deployment', {}).get('status') == 'SUCCESS',
                    payload.get('event') == 'deployment.success'
                ])
                
                completed = completion_event.wait(timeout=1)
                
                if should_complete and completed:
                    print(f"✅ {payload_name}: Correctly detected completion")
                    results[payload_name] = True
                elif not should_complete and not completed:
                    print(f"✅ {payload_name}: Correctly ignored (non-completion)")
                    results[payload_name] = True
                elif should_complete and not completed:
                    print(f"❌ {payload_name}: Should have detected completion but didn't")
                    results[payload_name] = False
                else:
                    print(f"❌ {payload_name}: Incorrectly detected completion")
                    results[payload_name] = False
                    
            except Exception as e:
                print(f"❌ {payload_name}: Error - {e}")
                results[payload_name] = False
            finally:
                server.shutdown()
        
        return results
    
    def mock_railway_deployment_sequence(self, delay_between_webhooks=2) -> bool:
        """Mock a full Railway deployment sequence"""
        print("🎭 Mocking full Railway deployment sequence...")
        
        # Start listener
        completion_event = threading.Event()
        server = create_webhook_server(self.listener_port, completion_event, debug=True)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        time.sleep(1)
        
        try:
            # Send deployment sequence
            payloads = self.get_sample_railway_payloads()[:4]  # Skip failure case
            
            for i, payload in enumerate(payloads):
                print(f"\n📤 Sending webhook {i+1}/{len(payloads)}: {payload.get('event', payload.get('status'))}...")
                
                response = requests.post(
                    self.base_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=5
                )
                
                if response.status_code != 200:
                    print(f"❌ Webhook {i+1} failed: {response.status_code}")
                    return False
                
                print(f"✅ Webhook {i+1} sent successfully")
                
                # Check if completion was triggered early (should only be on last webhook)
                if completion_event.is_set() and i < len(payloads) - 1:
                    print(f"⚠️  Completion triggered early on webhook {i+1}")
                
                if i < len(payloads) - 1:  # Don't delay after last webhook
                    time.sleep(delay_between_webhooks)
            
            # Wait for final completion
            if completion_event.wait(timeout=5):
                print("🎉 Full deployment sequence completed successfully!")
                return True
            else:
                print("❌ Deployment sequence did not trigger completion")
                return False
                
        except Exception as e:
            print(f"❌ Mock deployment failed: {e}")
            return False
        finally:
            server.shutdown()
    
    def debug_webhook_format_issues(self):
        """Debug potential webhook format issues"""
        print("🔍 Debugging Railway webhook format issues...")
        print("\n📋 Expected Railway webhook patterns:")
        
        patterns = [
            "event: 'deployment.success'",
            "status: 'SUCCESS'", 
            "status: 'DEPLOYED'",
            "deployment.status: 'SUCCESS'",
            "type: 'deployment.completed'"
        ]
        
        for pattern in patterns:
            print(f"   - {pattern}")
        
        print("\n🧪 Testing detection logic with sample payloads:")
        
        from deployment_webhook_listener import DeploymentWebhookHandler
        handler = DeploymentWebhookHandler()
        
        for i, payload in enumerate(self.get_sample_railway_payloads()):
            result = handler.is_deployment_complete(payload)
            status = "✅ DETECTED" if result else "❌ NOT DETECTED"
            print(f"   Payload {i+1}: {status} - {payload.get('event', payload.get('status', 'unknown'))}")
    
    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        print("📊 Generating comprehensive webhook test report...\n")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "summary": {}
        }
        
        # Test 1: Basic functionality
        print("=" * 60)
        print("TEST 1: Basic Webhook Listener Functionality")
        print("=" * 60)
        report["tests"]["basic_functionality"] = self.test_webhook_listener_basic()
        
        # Test 2: All payload formats
        print("\n" + "=" * 60)
        print("TEST 2: All Webhook Payload Formats")
        print("=" * 60)
        report["tests"]["payload_formats"] = self.test_all_webhook_payloads()
        
        # Test 3: Full deployment sequence
        print("\n" + "=" * 60)
        print("TEST 3: Full Deployment Sequence")
        print("=" * 60)
        report["tests"]["deployment_sequence"] = self.mock_railway_deployment_sequence()
        
        # Test 4: Debug format issues
        print("\n" + "=" * 60)
        print("TEST 4: Debug Format Issues")
        print("=" * 60)
        self.debug_webhook_format_issues()
        
        # Generate summary
        basic_passed = report["tests"]["basic_functionality"]
        payload_results = report["tests"]["payload_formats"]
        payload_passed = sum(1 for v in payload_results.values() if v)
        payload_total = len(payload_results)
        sequence_passed = report["tests"]["deployment_sequence"]
        
        report["summary"] = {
            "basic_functionality": "PASS" if basic_passed else "FAIL",
            "payload_formats": f"{payload_passed}/{payload_total} PASS",
            "deployment_sequence": "PASS" if sequence_passed else "FAIL",
            "overall_status": "PASS" if (basic_passed and sequence_passed and payload_passed == payload_total) else "FAIL"
        }
        
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        for test, result in report["summary"].items():
            status_emoji = "✅" if "PASS" in str(result) and "FAIL" not in str(result) else "❌"
            print(f"{status_emoji} {test.replace('_', ' ').title()}: {result}")
        
        return report


def main():
    """Main function with command-line interface"""
    parser = argparse.ArgumentParser(description="Railway webhook testing and debugging")
    parser.add_argument("--port", type=int, default=3000, help="Base port for testing (default: 3000)")
    parser.add_argument("--test-listener", action="store_true", help="Test basic webhook listener")
    parser.add_argument("--test-payloads", action="store_true", help="Test all webhook payload formats")
    parser.add_argument("--mock-deployment", action="store_true", help="Mock full deployment sequence")
    parser.add_argument("--debug-format", action="store_true", help="Debug webhook format issues")
    parser.add_argument("--full-test-suite", action="store_true", help="Run complete test suite")
    parser.add_argument("--save-report", help="Save test report to file")
    
    args = parser.parse_args()
    
    if not any([args.test_listener, args.test_payloads, args.mock_deployment, 
                args.debug_format, args.full_test_suite]):
        args.full_test_suite = True  # Default to full suite
    
    tester = RailwayWebhookTester(args.port)
    
    print("🚀 Railway Webhook Testing System")
    print(f"   🔧 Base port: {args.port}")
    print(f"   📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        if args.full_test_suite:
            report = tester.generate_test_report()
            if args.save_report:
                with open(args.save_report, 'w') as f:
                    json.dump(report, f, indent=2)
                print(f"\n📄 Report saved to: {args.save_report}")
            
        else:
            if args.test_listener:
                tester.test_webhook_listener_basic()
            
            if args.test_payloads:
                tester.test_all_webhook_payloads()
            
            if args.mock_deployment:
                tester.mock_railway_deployment_sequence()
            
            if args.debug_format:
                tester.debug_webhook_format_issues()
        
        print("\n🎉 Testing completed!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Testing failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
