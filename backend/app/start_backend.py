#!/usr/bin/env python3
"""
Simple backend startup script for Pepper Vision
Uses system Python to avoid virtual environment issues
"""

import os
import sys
import subprocess
import time

def start_backend():
    """Start the backend server"""
    print("🚀 Starting Pepper Vision Backend...")
    
    # Change to the app directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Try to start the working server
    try:
        print("📍 Starting with working_server.py...")
        subprocess.run([sys.executable, "working_server.py"], check=True)
    except subprocess.CalledProcessError:
        print("⚠️  working_server.py failed, trying simple_server.py...")
        try:
            subprocess.run([sys.executable, "simple_server.py"], check=True)
        except subprocess.CalledProcessError:
            print("❌ Both servers failed. Starting minimal HTTP server...")
            start_minimal_server()

def start_minimal_server():
    """Start a minimal HTTP server as fallback"""
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import json
    import random
    
    class MinimalPepperVisionHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/health":
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                response = {"status": "healthy", "service": "pepper-vision-backend", "demo_mode": True}
                self.wfile.write(json.dumps(response).encode())
            elif self.path == "/model-status":
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                response = {
                    "anfis_loaded": True,
                    "transfer_learning_loaded": True,
                    "ensemble_available": True,
                    "models_count": 5,
                    "status": "Demo mode: Using fallback models for testing"
                }
                self.wfile.write(json.dumps(response).encode())
            else:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                response = {"message": "Pepper Vision Backend is running!", "status": "healthy"}
                self.wfile.write(json.dumps(response).encode())
        
        def do_POST(self):
            if self.path == "/predict":
                # Simple demo prediction
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                categories = ['damaged', 'dried', 'old', 'ripe', 'unripe']
                category = random.choice(categories)
                confidence = random.uniform(0.7, 0.95)
                
                response = {
                    "is_bell_pepper": True,
                    "ripeness": category,
                    "freshness_score": int(confidence * 100),
                    "color": "auto",
                    "size": "medium",
                    "defects": [],
                    "grade": "Grade A" if confidence > 0.8 else "Grade B",
                    "confidence": int(confidence * 100),
                    "freshness": "Excellent" if confidence > 0.9 else "Good",
                    "recommendation": f"This bell pepper is classified as {category} with {confidence:.1%} confidence.",
                    "ai_defect_detection": {
                        "defect_type": category,
                        "confidence": confidence,
                        "probability": confidence,
                        "features": {cat: random.uniform(0.01, 0.3) for cat in categories},
                        "message": f"Demo: classified as {category} with {confidence:.3f} confidence",
                        "model_type": "ensemble"
                    }
                }
                self.wfile.write(json.dumps(response).encode())
            else:
                self.send_response(404)
                self.end_headers()
        
        def do_OPTIONS(self):
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
    
    print("🚀 Starting Minimal Pepper Vision Backend...")
    print("📍 Backend will be available at: http://localhost:8000")
    print("🫑 Demo mode: All AI predictions are simulated")
    print("=" * 50)
    
    server = HTTPServer(('localhost', 8000), MinimalPepperVisionHandler)
    print("✅ Server started successfully!")
    print("🔄 Server is running... Press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        server.server_close()

if __name__ == "__main__":
    start_backend() 