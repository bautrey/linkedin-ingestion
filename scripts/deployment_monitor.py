#!/usr/bin/env python3
"""
Railway Deployment Monitor

A simple script that monitors Railway deployment by polling the health endpoint
and detecting when the service version changes (indicating successful deployment).

Usage:
    python scripts/deployment_monitor.py [--url URL] [--timeout TIMEOUT] [--interval INTERVAL]

Example:
    python scripts/deployment_monitor.py --url https://smooth-mailbox-production.up.railway.app --timeout 600 --interval 10
"""

import argparse
import json
import sys
import time
import requests
from datetime import datetime, timedelta


def get_service_version(base_url):
    """
    Get the current service version from the health endpoint
    
    Args:
        base_url: Base URL of the service
    
    Returns:
        tuple: (version_string, timestamp, success)
    """
    try:
        health_url = f"{base_url.rstrip('/')}/api/v1/health"
        response = requests.get(health_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            version = data.get('version', 'unknown')
            timestamp = data.get('timestamp', 'unknown')
            return version, timestamp, True
        else:
            return None, None, False
            
    except Exception as e:
        print(f"❌ Error checking health endpoint: {e}")
        return None, None, False


def check_enhanced_endpoints(base_url):
    """
    Check if the enhanced endpoints are available (indicating new deployment)
    
    Args:
        base_url: Base URL of the service
    
    Returns:
        bool: True if enhanced endpoints are available
    """
    try:
        # Check if the enhanced endpoint exists by testing OPTIONS (non-destructive)
        enhanced_url = f"{base_url.rstrip('/')}/api/v1/profiles/enhanced"
        response = requests.options(enhanced_url, timeout=10)
        
        # If we get anything other than 404 Method Not Allowed, the endpoint exists
        return response.status_code != 405
        
    except Exception:
        return False


def monitor_deployment(base_url, timeout_seconds=600, check_interval=10, target_version=None):
    """
    Monitor Railway deployment by polling health endpoint
    
    Args:
        base_url: Base URL to monitor
        timeout_seconds: Maximum time to wait
        check_interval: Seconds between checks
        target_version: Expected version string (optional)
    
    Returns:
        bool: True if deployment detected, False if timeout
    """
    
    print(f"🔍 Starting deployment monitor...")
    print(f"   📡 Monitoring: {base_url}")
    print(f"   ⏰ Timeout: {timeout_seconds} seconds ({timeout_seconds//60} minutes)")
    print(f"   🔄 Check interval: {check_interval} seconds")
    if target_version:
        print(f"   🎯 Target version: {target_version}")
    print()
    
    start_time = datetime.now()
    end_time = start_time + timedelta(seconds=timeout_seconds)
    
    # Get initial version
    initial_version, _, initial_success = get_service_version(base_url)
    if initial_success:
        print(f"📊 Initial version: {initial_version}")
    else:
        print(f"⚠️  Could not get initial version, continuing anyway...")
    
    # Check if enhanced endpoints already exist
    enhanced_available = check_enhanced_endpoints(base_url)
    if enhanced_available:
        print(f"✅ Enhanced endpoints already available!")
        return True
    else:
        print(f"⏳ Enhanced endpoints not yet available, monitoring...")
    
    check_count = 0
    
    while datetime.now() < end_time:
        check_count += 1
        current_time = datetime.now()
        elapsed = current_time - start_time
        
        # Get current version
        current_version, timestamp, success = get_service_version(base_url)
        
        if success:
            # Check for version change
            version_changed = (
                initial_version and 
                current_version and 
                current_version != initial_version
            )
            
            # Check for target version match
            target_reached = (
                target_version and 
                current_version and 
                target_version in current_version
            )
            
            # Check for enhanced endpoints
            enhanced_now_available = check_enhanced_endpoints(base_url)
            
            # Log status
            status_emoji = "🟢" if enhanced_now_available else "🟡"
            print(f"{status_emoji} Check {check_count}: {current_version} | Enhanced: {'✅' if enhanced_now_available else '❌'} | Elapsed: {elapsed.total_seconds():.0f}s")
            
            # Check completion conditions
            if enhanced_now_available:
                print(f"\n🎉 DEPLOYMENT COMPLETE!")
                print(f"   ✅ Enhanced endpoints are now available")
                print(f"   🚀 Version: {current_version}")
                print(f"   ⏱️  Total time: {elapsed.total_seconds():.0f} seconds")
                return True
            
            elif version_changed:
                print(f"   📈 Version changed: {initial_version} → {current_version}")
                # Continue monitoring for enhanced endpoints
            
            elif target_reached:
                print(f"   🎯 Target version reached: {current_version}")
                # Continue monitoring for enhanced endpoints
                
        else:
            print(f"🔴 Check {check_count}: Service unavailable | Elapsed: {elapsed.total_seconds():.0f}s")
        
        # Wait before next check
        time.sleep(check_interval)
    
    # Timeout reached
    elapsed = datetime.now() - start_time
    print(f"\n⏰ Timeout reached after {elapsed.total_seconds():.0f} seconds")
    print(f"   Current version: {current_version if success else 'unknown'}")
    print(f"   Enhanced endpoints: {'✅' if check_enhanced_endpoints(base_url) else '❌'}")
    
    return False


def main():
    """Main function with command-line interface"""
    parser = argparse.ArgumentParser(description="Railway deployment monitor")
    parser.add_argument("--url", 
                       default="https://smooth-mailbox-production.up.railway.app",
                       help="Base URL to monitor (default: Railway production URL)")
    parser.add_argument("--timeout", type=int, default=600, 
                       help="Timeout in seconds (default: 600)")
    parser.add_argument("--interval", type=int, default=10,
                       help="Check interval in seconds (default: 10)")
    parser.add_argument("--target-version", 
                       help="Expected version string to wait for")
    
    args = parser.parse_args()
    
    success = monitor_deployment(
        base_url=args.url,
        timeout_seconds=args.timeout,
        check_interval=args.interval,
        target_version=args.target_version
    )
    
    if success:
        print(f"\n🎉 Deployment monitoring completed successfully!")
        print(f"🔗 You can now test the enhanced endpoints:")
        print(f"   POST {args.url}/api/v1/profiles/enhanced")
        print(f"   POST {args.url}/api/v1/profiles/batch-enhanced")
        sys.exit(0)
    else:
        print(f"\n⚠️  Deployment monitoring ended without confirmation")
        print(f"💡 The deployment may still be in progress")
        sys.exit(1)


if __name__ == "__main__":
    main()
