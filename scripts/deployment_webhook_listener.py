#!/usr/bin/env python3
"""
Railway Deployment Webhook Listener

A simple HTTP server that listens for Railway deployment webhooks
and notifies when deployments are complete.

Usage:
    python scripts/deployment_webhook_listener.py [--port PORT] [--timeout TIMEOUT]

Example:
    python scripts/deployment_webhook_listener.py --port 3000 --timeout 300
"""

import argparse
import json
import signal
import sys
import threading
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

class DeploymentWebhookHandler(BaseHTTPRequestHandler):
    """HTTP request handler for Railway deployment webhooks"""
    
    def __init__(self, *args, completion_event=None, **kwargs):
        self.completion_event = completion_event
        super().__init__(*args, **kwargs)
    
    def do_POST(self):
        """Handle POST requests from Railway webhooks"""
        try:
            # Get content length and read the request body
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            # Parse the webhook payload
            try:
                payload = json.loads(post_data.decode('utf-8'))
                self.log_webhook_received(payload)
                
                # Check if this is a deployment completion event
                if self.is_deployment_complete(payload):
                    self.log_deployment_complete(payload)
                    if self.completion_event:
                        self.completion_event.set()
                
            except json.JSONDecodeError:
                # Handle form-encoded data or plain text
                payload_str = post_data.decode('utf-8')
                self.log_message(f"📨 Webhook received (non-JSON): {payload_str[:200]}")
                
                # Simple string matching for deployment completion
                if any(keyword in payload_str.lower() for keyword in ['success', 'complete', 'deployed']):
                    self.log_message("🎉 Deployment appears to be complete (string match)")
                    if self.completion_event:
                        self.completion_event.set()
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "received"}).encode())
            
        except Exception as e:
            self.log_message(f"❌ Error processing webhook: {e}")
            self.send_response(500)
            self.end_headers()
    
    def do_GET(self):
        """Handle GET requests for health checks"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = {
            "status": "listening",
            "timestamp": datetime.now().isoformat(),
            "message": "Railway deployment webhook listener is running"
        }
        self.wfile.write(json.dumps(response, indent=2).encode())
    
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
    
    def log_webhook_received(self, payload):
        """Log webhook receipt with key details"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Extract key information from payload
        status = payload.get('status', 'unknown')
        event = payload.get('event', payload.get('type', 'unknown'))
        deployment_id = payload.get('deploymentId', payload.get('id', 'unknown'))
        
        print(f"📨 [{timestamp}] Webhook received:")
        print(f"   Status: {status}")
        print(f"   Event: {event}")
        print(f"   Deployment ID: {deployment_id}")
        
        if self.server.debug:
            print(f"   Full payload: {json.dumps(payload, indent=2)}")
    
    def log_deployment_complete(self, payload):
        """Log deployment completion with celebration"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n🎉 [{timestamp}] DEPLOYMENT COMPLETE!")
        print(f"   ✅ Railway deployment finished successfully")
        print(f"   🚀 Service should be updated with new endpoints")
        print(f"   🔗 You can now test the enhanced endpoints\n")
    
    def log_message(self, message):
        """Log a message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")


def create_webhook_server(port, completion_event, debug=False):
    """Create and configure the webhook server"""
    
    class WebhookServer(HTTPServer):
        def __init__(self, *args, **kwargs):
            self.debug = debug
            super().__init__(*args, **kwargs)
    
    def handler(*args, **kwargs):
        return DeploymentWebhookHandler(*args, completion_event=completion_event, **kwargs)
    
    server = WebhookServer(("", port), handler)
    server.debug = debug
    return server


def wait_for_deployment(port=3000, timeout=300, debug=False):
    """
    Start webhook listener and wait for deployment completion
    
    Args:
        port: Port to listen on
        timeout: Maximum time to wait in seconds
        debug: Enable debug logging
    
    Returns:
        bool: True if deployment completed, False if timeout
    """
    
    completion_event = threading.Event()
    server = create_webhook_server(port, completion_event, debug)
    
    # Start server in a separate thread
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    
    print(f"🎧 Railway deployment webhook listener started")
    print(f"   📡 Listening on: http://localhost:{port}")
    print(f"   ⏰ Timeout: {timeout} seconds")
    print(f"   🔧 Configure this URL in Railway project settings")
    print(f"   📋 Webhook URL: http://localhost:{port}")
    print(f"\n   To configure in Railway:")
    print(f"   1. Go to your Railway project dashboard")
    print(f"   2. Click on Settings -> Webhooks")
    print(f"   3. Add webhook URL: http://localhost:{port}")
    print(f"   4. Enable 'Build and Deploy Webhooks'\n")
    
    # Set up signal handler for graceful shutdown
    def signal_handler(signum, frame):
        print(f"\n⚠️  Received signal {signum}, shutting down...")
        server.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Wait for completion or timeout
    try:
        if completion_event.wait(timeout=timeout):
            print(f"✅ Deployment completed successfully!")
            server.shutdown()
            return True
        else:
            print(f"⏰ Timeout reached ({timeout}s). Deployment may still be in progress.")
            server.shutdown()
            return False
            
    except KeyboardInterrupt:
        print(f"\n⚠️  Interrupted by user")
        server.shutdown()
        return False


def main():
    """Main function with command-line interface"""
    parser = argparse.ArgumentParser(description="Railway deployment webhook listener")
    parser.add_argument("--port", type=int, default=3000, help="Port to listen on (default: 3000)")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds (default: 300)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    print(f"🚀 Starting Railway deployment webhook listener...")
    
    success = wait_for_deployment(
        port=args.port,
        timeout=args.timeout,
        debug=args.debug
    )
    
    if success:
        print(f"🎉 Webhook listener completed successfully")
        sys.exit(0)
    else:
        print(f"⚠️  Webhook listener ended without confirmation")
        sys.exit(1)


if __name__ == "__main__":
    main()
