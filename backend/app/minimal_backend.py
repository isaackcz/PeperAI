#!/usr/bin/env python3
"""
Minimal working backend for Pepper Vision
Uses only standard Python libraries - no external dependencies
"""

import os
import json
import random
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import cgi
import io

# Create uploads directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class PepperVisionHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == "/health":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {
                "status": "healthy", 
                "service": "pepper-vision-backend", 
                "demo_mode": True
            }
            self.wfile.write(json.dumps(response).encode())
            
        elif parsed_path.path == "/model-status":
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
            response = {
                "message": "Pepper Vision Backend is running!", 
                "status": "healthy",
                "demo_mode": True
            }
            self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == "/predict":
            # Handle image prediction
            self.handle_prediction()
        elif parsed_path.path == "/select-object":
            # Handle object selection
            self.handle_object_selection()
        else:
            self.send_response(404)
            self.end_headers()
    
    def handle_prediction(self):
        """Handle image prediction request"""
        try:
            # Parse multipart form data
            content_type = self.headers.get('Content-Type', '')
            if 'multipart/form-data' in content_type:
                # Parse the form data
                form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={'REQUEST_METHOD': 'POST'}
                )
                
                # Get model type
                model_type = form.getvalue('model_type', 'ensemble')
                
                # Get image file
                image_file = form['image']
                if image_file.filename:
                    # Save the uploaded image
                    file_id = str(uuid.uuid4())
                    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{image_file.filename}")
                    
                    with open(file_path, 'wb') as f:
                        f.write(image_file.file.read())
                    
                    # Generate demo prediction
                    prediction = self.generate_demo_prediction(model_type)
                    
                    # Send response
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    
                    self.wfile.write(json.dumps(prediction).encode())
                else:
                    self.send_error(400, "No image file provided")
            else:
                self.send_error(400, "Invalid content type")
                
        except Exception as e:
            print(f"Error in prediction: {e}")
            self.send_error(500, f"Internal server error: {str(e)}")
    
    def handle_object_selection(self):
        """Handle object selection request"""
        try:
            # Parse multipart form data
            content_type = self.headers.get('Content-Type', '')
            if 'multipart/form-data' in content_type:
                form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={'REQUEST_METHOD': 'POST'}
                )
                
                # Get coordinates
                click_x = int(form.getvalue('click_x', 0))
                click_y = int(form.getvalue('click_y', 0))
                
                # Get image file
                image_file = form['image']
                if image_file.filename:
                    # Save the uploaded image
                    file_id = str(uuid.uuid4())
                    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{image_file.filename}")
                    
                    with open(file_path, 'wb') as f:
                        f.write(image_file.file.read())
                    
                    # Generate demo region
                    region = [click_x - 50, click_y - 50, 100, 100]
                    
                    # Send response
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    
                    response = {
                        "cropped_image": f"/uploads/{file_id}_{image_file.filename}",
                        "region": region
                    }
                    self.wfile.write(json.dumps(response).encode())
                else:
                    self.send_error(400, "No image file provided")
            else:
                self.send_error(400, "Invalid content type")
                
        except Exception as e:
            print(f"Error in object selection: {e}")
            self.send_error(500, f"Internal server error: {str(e)}")
    
    def generate_demo_prediction(self, model_type):
        """Generate a demo prediction"""
        categories = ['damaged', 'dried', 'old', 'ripe', 'unripe']
        category = random.choice(categories)
        
        # Different confidence ranges for different models
        if model_type == "transfer":
            confidence = random.uniform(0.7, 0.98)
        elif model_type == "anfis":
            confidence = random.uniform(0.6, 0.95)
        else:  # ensemble
            confidence = random.uniform(0.75, 0.96)
        
        # Create realistic probabilities
        probabilities = {}
        for cat in categories:
            if cat == category:
                probabilities[cat] = confidence
            else:
                probabilities[cat] = random.uniform(0.01, 0.3)
        
        return {
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
                "features": probabilities,
                "message": f"{model_type.title()} demo: classified as {category} with {confidence:.3f} confidence",
                "model_type": model_type
            }
        }
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def main():
    """Start the server"""
    print("🚀 Starting Pepper Vision Backend (Minimal HTTP Server)...")
    print("📍 Backend will be available at: http://localhost:8000")
    print("🫑 Demo mode: All AI predictions are simulated")
    print("=" * 50)
    
    try:
        server = HTTPServer(('localhost', 8000), PepperVisionHandler)
        print("✅ Server started successfully!")
        print("🔄 Server is running... Press Ctrl+C to stop")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        server.server_close()
    except Exception as e:
        print(f"❌ Error starting server: {e}")

if __name__ == "__main__":
    main()