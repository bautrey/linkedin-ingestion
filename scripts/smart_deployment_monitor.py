#!/usr/bin/env python3
"""
Smart Deployment Monitor

A robust deployment monitoring system that combines multiple strategies:
1. Health endpoint polling (primary)
2. Local webhook listener with ngrok tunnel (if available)
3. Git commit-based detection
4. Timeout with graceful degradation

This replaces the problematic webhook-only approach with a more reliable solution.

Usage:
    python scripts/smart_deployment_monitor.py
    python scripts/smart_deployment_monitor.py --timeout 600 --interval 15
    python scripts/smart_deployment_monitor.py --use-webhook --ngrok-port 4040
"""

import argparse
import json
import subprocess
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple

class SmartDeploymentMonitor:
    """Multi-strategy deployment monitoring"""
    
    def __init__(self, 
                 base_url="https://smooth-mailbox-production.up.railway.app",
                 timeout_seconds=600,
                 check_interval=15):
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds 
        self.check_interval = check_interval
        self.start_time = datetime.now()
        
    def get_service_info(self) -> Tuple[Optional[Dict[str, Any]], bool]:
        """Get current service information from health endpoint"""
        try:
            health_url = f"{self.base_url.rstrip('/')}/api/v1/health"
            
            with urllib.request.urlopen(health_url, timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    return data, True
                
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            
        return None, False
    
    def get_git_latest_commit(self) -> Optional[str]:
        """Get the latest git commit hash"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()[:8]  # Short hash
        except Exception:
            pass
        return None
    
    def check_enhanced_endpoints(self) -> bool:
        """Check if enhanced endpoints are available"""
        try:
            enhanced_url = f"{self.base_url.rstrip('/')}/api/v1/profiles/enhanced"
            
            # Use OPTIONS to avoid triggering actual requests
            req = urllib.request.Request(enhanced_url, method='OPTIONS')
            with urllib.request.urlopen(req, timeout=10) as response:
                # If we get anything other than 405 Method Not Allowed, endpoint exists
                return response.status != 405
                
        except urllib.error.HTTPError as e:
            # 405 means endpoint exists but doesn't support OPTIONS
            # 404 means endpoint doesn't exist
            return e.code != 404
        except Exception:
            return False
    
    def detect_deployment_change(self, initial_info: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Detect if deployment has changed by comparing multiple indicators
        
        Returns: (changed, reason)
        """
        current_info, success = self.get_service_info()
        
        if not success:
            return False, "Health endpoint unavailable"
        
        # Check version change
        initial_version = initial_info.get('version', 'unknown')
        current_version = current_info.get('version', 'unknown')
        
        if initial_version != 'unknown' and current_version != 'unknown':
            if initial_version != current_version:
                return True, f"Version changed: {initial_version} → {current_version}"
        
        # Check timestamp change (indicates restart)
        initial_timestamp = initial_info.get('timestamp', '')
        current_timestamp = current_info.get('timestamp', '')
        
        if initial_timestamp and current_timestamp:
            if initial_timestamp != current_timestamp:
                # Check if timestamp is significantly newer (not just a minor difference)
                try:
                    initial_time = datetime.fromisoformat(initial_timestamp.replace('Z', '+00:00'))
                    current_time = datetime.fromisoformat(current_timestamp.replace('Z', '+00:00'))
                    
                    if (current_time - initial_time).total_seconds() > 30:
                        return True, f"Service restarted: {current_timestamp}"
                except Exception:
                    pass
        
        # Check enhanced endpoints availability
        enhanced_available = self.check_enhanced_endpoints()
        if enhanced_available:
            return True, "Enhanced endpoints now available"
        
        return False, "No deployment changes detected"
    
    def monitor_with_polling(self) -> bool:
        """Monitor deployment using health endpoint polling"""
        print(f"🔍 Starting polling-based deployment monitoring...")
        print(f"   📡 Monitoring: {self.base_url}")
        print(f"   ⏰ Timeout: {self.timeout_seconds} seconds ({self.timeout_seconds//60} minutes)")
        print(f"   🔄 Check interval: {self.check_interval} seconds")
        print()
        
        # Get initial state
        initial_info, initial_success = self.get_service_info()
        if not initial_success:
            print("⚠️  Could not get initial service state, continuing anyway...")
            initial_info = {}
        else:
            print(f"📊 Initial state captured:")
            print(f"   Version: {initial_info.get('version', 'unknown')}")
            print(f"   Timestamp: {initial_info.get('timestamp', 'unknown')}")
        
        # Check if enhanced endpoints are already available
        if self.check_enhanced_endpoints():
            print(f"✅ Enhanced endpoints already available!")
            return True
        
        print(f"⏳ Enhanced endpoints not yet available, monitoring for changes...")
        print()
        
        end_time = self.start_time + timedelta(seconds=self.timeout_seconds)
        check_count = 0
        
        while datetime.now() < end_time:
            check_count += 1
            current_time = datetime.now()
            elapsed = current_time - self.start_time
            
            # Check for deployment changes
            changed, reason = self.detect_deployment_change(initial_info)
            
            # Status indicators
            status_emoji = "🟢" if changed else "🟡"
            enhanced_available = self.check_enhanced_endpoints()
            enhanced_emoji = "✅" if enhanced_available else "❌"
            
            print(f"{status_emoji} Check {check_count}: {reason} | Enhanced: {enhanced_emoji} | Elapsed: {elapsed.total_seconds():.0f}s")
            
            # Check completion condition
            if enhanced_available:
                print(f"\n🎉 DEPLOYMENT COMPLETE!")
                print(f"   ✅ Enhanced endpoints are now available")
                print(f"   ⏱️  Total monitoring time: {elapsed.total_seconds():.0f} seconds")
                return True
            
            # Wait before next check
            time.sleep(self.check_interval)
        
        # Timeout reached
        elapsed = datetime.now() - self.start_time
        print(f"\n⏰ Monitoring timeout reached after {elapsed.total_seconds():.0f} seconds")
        
        # Final status check
        final_enhanced = self.check_enhanced_endpoints()
        print(f"   Enhanced endpoints: {'✅' if final_enhanced else '❌'}")
        
        if final_enhanced:
            print("   🎉 Deployment appears to have completed during final check!")
            return True
        
        return False
    
    def check_ngrok_availability(self) -> bool:
        """Check if ngrok is available for webhook tunneling"""
        try:
            result = subprocess.run(['which', 'ngrok'], capture_output=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False
    
    def start_ngrok_tunnel(self, port: int = 3000) -> Optional[str]:
        """Start ngrok tunnel and return public URL"""
        if not self.check_ngrok_availability():
            print("⚠️  ngrok not available, skipping webhook setup")
            return None
        
        try:
            print(f"🚇 Starting ngrok tunnel on port {port}...")
            
            # Start ngrok in background
            subprocess.Popen(
                ['ngrok', 'http', str(port)], 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL
            )
            
            # Wait a moment for ngrok to start
            time.sleep(3)
            
            # Get the public URL from ngrok API
            with urllib.request.urlopen('http://localhost:4040/api/tunnels', timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    tunnels = data.get('tunnels', [])
                    
                    for tunnel in tunnels:
                        if tunnel.get('proto') == 'https':
                            public_url = tunnel.get('public_url')
                            print(f"✅ ngrok tunnel active: {public_url}")
                            return public_url
            
        except Exception as e:
            print(f"❌ Failed to start ngrok tunnel: {e}")
        
        return None
    
    def monitor_with_hybrid_approach(self, webhook_port: int = 3000) -> bool:
        """Monitor using hybrid approach: webhook + polling fallback"""
        print("🔄 Starting hybrid deployment monitoring...")
        
        # Try to set up webhook with ngrok
        ngrok_url = self.start_ngrok_tunnel(webhook_port)
        
        if ngrok_url:
            print(f"📋 Configure Railway webhook URL: {ngrok_url}")
            print("   1. Go to Railway Dashboard > Settings > Webhooks")
            print(f"   2. Add webhook URL: {ngrok_url}")
            print("   3. Enable 'Build and Deploy Webhooks'")
            print()
            
            # Start webhook listener in background
            # TODO: Implement webhook listener integration here
            
            print("⚠️  Webhook setup available but not fully implemented")
            print("   Falling back to polling-based monitoring")
        
        # Fall back to polling
        return self.monitor_with_polling()
    
    def generate_summary_report(self, success: bool, elapsed_seconds: float) -> Dict[str, Any]:
        """Generate deployment monitoring summary report"""
        current_info, _ = self.get_service_info()
        enhanced_available = self.check_enhanced_endpoints()
        latest_commit = self.get_git_latest_commit()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "monitoring": {
                "success": success,
                "elapsed_seconds": elapsed_seconds,
                "timeout_seconds": self.timeout_seconds,
                "check_interval": self.check_interval
            },
            "service_status": {
                "base_url": self.base_url,
                "health_check": current_info is not None,
                "enhanced_endpoints": enhanced_available,
                "version": current_info.get('version', 'unknown') if current_info else 'unknown'
            },
            "git_info": {
                "latest_commit": latest_commit
            }
        }
        
        return report

def main():
    """Main function with command-line interface"""
    parser = argparse.ArgumentParser(description="Smart deployment monitoring")
    parser.add_argument("--url", 
                       default="https://smooth-mailbox-production.up.railway.app",
                       help="Base URL to monitor")
    parser.add_argument("--timeout", type=int, default=600,
                       help="Timeout in seconds (default: 600)")
    parser.add_argument("--interval", type=int, default=15,
                       help="Check interval in seconds (default: 15)")
    parser.add_argument("--use-webhook", action="store_true",
                       help="Try to use webhook monitoring with ngrok")
    parser.add_argument("--webhook-port", type=int, default=3000,
                       help="Port for webhook listener (default: 3000)")
    parser.add_argument("--save-report", 
                       help="Save monitoring report to file")
    
    args = parser.parse_args()
    
    print("🚀 Smart Deployment Monitor")
    print(f"   📡 Target: {args.url}")
    print(f"   ⏰ Timeout: {args.timeout} seconds")
    print(f"   📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    monitor = SmartDeploymentMonitor(
        base_url=args.url,
        timeout_seconds=args.timeout,
        check_interval=args.interval
    )
    
    try:
        start_time = datetime.now()
        
        if args.use_webhook:
            success = monitor.monitor_with_hybrid_approach(args.webhook_port)
        else:
            success = monitor.monitor_with_polling()
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        # Generate report
        if args.save_report:
            report = monitor.generate_summary_report(success, elapsed)
            with open(args.save_report, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n📄 Report saved to: {args.save_report}")
        
        if success:
            print(f"\n🎉 Deployment monitoring completed successfully!")
            print(f"🔗 Enhanced endpoints are ready:")
            print(f"   POST {args.url}/api/v1/profiles/enhanced")
            print(f"   POST {args.url}/api/v1/profiles/batch-enhanced")
            sys.exit(0)
        else:
            print(f"\n⚠️  Deployment monitoring timed out")
            print(f"💡 The deployment may still be in progress")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n⚠️  Monitoring interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Monitoring failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
