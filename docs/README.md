# 🌶️ Bell Pepper Vision AI - Complete Documentation

A comprehensive AI-powered bell pepper quality assessment system using ANFIS (Adaptive Neuro-Fuzzy Inference System), YOLO object detection, and advanced computer vision techniques.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Docker Setup](#docker-setup)
- [Development Guide](#development-guide)
- [API Documentation](#api-documentation)
- [ANFIS Technical Details](#anfis-technical-details)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [Security](#security)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

Bell Pepper Vision AI is an intelligent system that combines multiple AI technologies to assess bell pepper quality:

- **ANFIS Model**: 50% - Advanced neuro-fuzzy system for defect detection
- **YOLO Object Detection**: 25% - Real-time object segmentation and detection
- **Computer Vision**: 15% - Color analysis, texture extraction, shape analysis
- **Feature Engineering**: 10% - HSV, GLCM, contour analysis

### Key Capabilities

- 🔍 **Defect Detection**: Identify 6 types of defects (Anthracnose, Blight, Sunscald, Mildew, Rot, Insect Damage)
- 🎨 **Color Grading**: Analyze ripeness and quality based on HSV color space
- 📏 **Size & Shape Analysis**: Measure dimensions, circularity, and solidity
- 🧠 **Active Learning**: Continuously improve model performance
- 📊 **Comprehensive Reporting**: Detailed feature extraction and analysis

## ✨ Features

### Core AI Components

1. **ANFIS Defect Detection**
   - Takagi-Sugeno architecture with 11 input features
   - 7 Gaussian membership functions per input
   - Hybrid training (backpropagation + least squares)
   - Active learning with uncertainty sampling

2. **YOLO Object Detection**
   - YOLOv8-seg for instance segmentation
   - Real-time object detection and cropping
   - Automatic region of interest selection

3. **Computer Vision Analysis**
   - HSV color space analysis
   - GLCM texture features (contrast, homogeneity, entropy)
   - Contour analysis (area, circularity, solidity)
   - Surface defect detection

4. **Synthetic Data Generation**
   - Generate realistic bell pepper images
   - Apply 6 types of defects with realistic parameters
   - Data augmentation for training

### User Interface

- 🎨 **Modern UI**: Dark gradient theme with Shadcn/ui components
- 📱 **Responsive Design**: Works on desktop and mobile devices
- 🔄 **Real-time Processing**: Live image analysis and results
- 📈 **Interactive Charts**: ApexCharts for data visualization
- 📊 **Comprehensive Reports**: Detailed feature breakdown

## 🏗️ Architecture

```
Bell Pepper Vision AI
├── Frontend (React + TypeScript)
│   ├── Image Upload & Processing
│   ├── Real-time Analysis Display
│   ├── ANFIS Training Interface
│   └── Results Visualization
├── Backend (FastAPI + Python)
│   ├── ANFIS Model Training
│   ├── YOLO Object Detection
│   ├── Feature Extraction
│   ├── Synthetic Data Generation
│   └── Active Learning System
└── AI Models
    ├── ANFIS (Defect Classification)
    ├── YOLOv8-seg (Object Detection)
    └── Computer Vision Pipelines
```

### Technology Stack

- **Frontend**: React 18, TypeScript, Vite, Shadcn/ui, ApexCharts
- **Backend**: FastAPI, Python 3.10, Uvicorn
- **AI/ML**: ANFIS, YOLOv8, OpenCV, scikit-image, scikit-learn
- **Data Processing**: NumPy, Pandas, Albumentations
- **Deployment**: Docker, Docker Compose, Nginx

## 🚀 Quick Start

### Prerequisites

- **Docker Desktop**: [Download here](https://www.docker.com/products/docker-desktop/)
- **Git**: For cloning the repository
- **4GB+ RAM**: For AI model processing

### 1. Clone the Repository

```bash
git clone https://github.com/isaackcz/BellPeperAI.git
cd BellPeperAI
```

### 2. Start with Docker

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up --build -d
```

### 3. Access the Application

- **Frontend**: http://localhost:8080
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 4. Test the System

1. Upload a bell pepper image
2. Select the region of interest
3. View comprehensive analysis results
4. Train ANFIS models for defect detection

## 🐳 Docker Setup

### Development Mode

```bash
# Start development environment with hot reload
docker-compose up frontend-dev backend

# Frontend with hot reload: http://localhost:3000
# Backend API: http://localhost:8000
```

### Production Mode

```bash
# Start production environment
docker-compose up frontend backend

# Frontend: http://localhost:8080
# Backend API: http://localhost:8000
```

### Docker Commands

```bash
# Build images
docker-compose build

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Access containers
docker-compose exec backend bash
docker-compose exec frontend sh
```

### Docker Architecture

```
Services:
├── backend: FastAPI application with AI models
├── frontend: React application (production)
└── frontend-dev: React development server

Volumes:
├── uploads: Image uploads and processed files
├── models: Trained ANFIS models
├── training_output: Training logs and outputs
├── synthetic_data: Generated synthetic images
└── data: Dataset files
```

## 🔧 Development Guide

### Docker Development Setup

#### Prerequisites

- Docker Desktop installed and running
- Docker Compose available

#### Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd pepper-vision-grade

# Start all services with Docker
docker-compose up --build

# Or use the provided script
.\run.bat
```

#### Service Access

- **Frontend**: http://localhost:8080
- **Backend API**: http://localhost:8000
- **Models Service**: http://localhost:8001
- **API Documentation**: http://localhost:8000/docs

#### Container Management

```bash
# Stop all services
docker-compose down

# Or use the provided script
.\stop.bat

# View logs
docker-compose logs

# View specific service logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs models
```

### Project Structure

```
BellPeperAI/
├── 📁 backend/
│   ├── 📁 app/
│   │   ├── 📄 main.py                    # FastAPI application
│   │   ├── 📁 utils/
│   │   │   ├── 📄 anfis_trainer.py       # ANFIS model training
│   │   │   ├── 📄 feature_extractor.py   # Feature extraction
│   │   │   ├── 📄 synthetic_data.py      # Synthetic data generation
│   │   │   ├── 📄 active_learning.py     # Active learning system
│   │   │   ├── 📄 training_pipeline.py   # Complete training pipeline
│   │   │   ├── 📄 object_detection.py    # YOLO object detection
│   │   │   ├── 📄 color_grading.py       # Color analysis
│   │   │   └── 📄 grade_ripeness.py      # Grading algorithms
│   │   └── 📁 uploads/                   # Image storage
│   ├── 📄 requirements.txt               # Python dependencies
│   └── 📄 ANFIS_README.md               # Technical documentation
├── 📁 frontend/
│   ├── 📁 src/
│   │   ├── 📁 components/
│   │   │   ├── 📄 ANFISPanel.tsx         # ANFIS training interface
│   │   │   ├── 📄 ResultsPanel.tsx       # Analysis results display
│   │   │   ├── 📄 RegionSelector.tsx     # Object selection
│   │   │   └── 📄 ImageUpload.tsx        # Image upload component
│   │   ├── 📁 pages/
│   │   │   └── 📄 Index.tsx              # Main application page
│   │   └── 📄 main.tsx                   # Application entry point
│   ├── 📄 package.json                   # Node.js dependencies
│   └── 📄 vite.config.ts                 # Vite configuration
├── 📁 docker/                            # Docker configuration files
├── 📁 docs/                              # Documentation
└── 📄 docker-compose.yml                 # Service orchestration
```

## 📚 API Documentation

### Core Endpoints

#### Image Processing

- `POST /predict` - Upload and analyze image
- `POST /select-object` - Select region of interest and extract features
- `GET /uploads/{filename}` - Serve uploaded images

#### ANFIS System

- `GET /model-status` - Check ANFIS model status
- `POST /train-anfis` - Train ANFIS model
- `POST /predict-defect` - Predict defects using ANFIS
- `POST /generate-synthetic` - Generate synthetic training data

#### Health & Monitoring

- `GET /health` - Health check endpoint
- `GET /docs` - Interactive API documentation

### Request/Response Examples

#### Image Analysis

```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@bell_pepper.jpg"
```

Response:
```json
{
  "filename": "bell_pepper_processed.jpg",
  "objects": [
    {
      "bbox": [100, 150, 300, 400],
      "confidence": 0.95,
      "class": "bell_pepper"
    }
  ]
}
```

#### Feature Extraction

```bash
curl -X POST "http://localhost:8000/select-object" \
  -H "Content-Type: application/json" \
  -d '{
    "image_path": "bell_pepper.jpg",
    "bbox": [100, 150, 300, 400]
  }'
```

Response:
```json
{
  "cropped_image": "cropped_bell_pepper.jpg",
  "features": {
    "hue_mean": 45.2,
    "saturation_mean": 78.5,
    "value_mean": 156.8,
    "glcm_contrast": 0.234,
    "glcm_homogeneity": 0.876,
    "circularity": 0.892,
    "solidity": 0.945,
    "grade": "A",
    "ripeness_label": "Ripe"
  }
}
```

## 🧠 ANFIS Technical Details

### Architecture

The ANFIS system uses a Takagi-Sugeno architecture with:

- **11 Input Features**: HSV means/stds, GLCM features, contour properties
- **7 Gaussian Membership Functions**: Per input feature
- **49 Fuzzy Rules**: Complete rule base
- **Hybrid Training**: Backpropagation + least squares optimization

### Feature Extraction

```python
# 11 ANFIS-specific features
features = {
    'h_mean': hue_mean,           # Color analysis
    'h_std': hue_std,
    's_mean': saturation_mean,
    's_std': saturation_std,
    'v_mean': value_mean,
    'v_std': value_std,
    'glcm_contrast': contrast,    # Texture analysis
    'glcm_homogeneity': homogeneity,
    'contour_area': area,         # Shape analysis
    'circularity': circularity,
    'solidity': solidity
}
```

### Training Process

1. **Data Generation**: Mix real (100) + synthetic (500) images
2. **Feature Extraction**: Extract 11 features per image
3. **Model Training**: Hybrid training with early stopping
4. **Active Learning**: Identify uncertain samples and retrain
5. **Evaluation**: Test on real images for validation

### Performance Metrics

- **Target F1-Score**: >90% on real test images
- **False Positive Rate**: <5% for healthy peppers
- **Inference Speed**: <500ms per image on CPU
- **Memory Usage**: <2GB RAM during training

## 🚀 Deployment

### Cloud Deployment Options

#### AWS ECS

```bash
# Deploy to AWS ECS
aws ecs create-cluster --cluster-name bell-pepper-cluster
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

#### Google Cloud Run

```bash
# Deploy to Google Cloud Run
gcloud run deploy bell-pepper-backend --source .
gcloud run deploy bell-pepper-frontend --source .
```

#### Railway

```bash
# Deploy to Railway
railway login
railway init
railway up
```

### Environment Variables

```bash
# Required environment variables
ANFIS_SECRET_KEY=your-secret-key
UPLOAD_DIR=/app/backend/app/uploads
MODEL_PATH=/app/backend/models
TRAINING_OUTPUT_DIR=/app/backend/training_output
SYNTHETIC_DATA_DIR=/app/backend/synthetic_data
DATA_DIR=/app/backend/data
```

### Production Configuration

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  backend:
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
  
  frontend:
    environment:
      - VITE_API_URL=https://api.yourdomain.com
```

## 🤝 Contributing

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** following the coding standards
4. **Test thoroughly** with the provided test suite
5. **Commit your changes**: `git commit -m 'Add amazing feature'`
6. **Push to the branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

### Code Standards

#### Python (Backend)
- **Style**: Follow PEP 8 guidelines
- **Type Hints**: Use type hints for all functions
- **Documentation**: Docstrings for all classes and functions
- **Testing**: Unit tests for all new features

#### TypeScript/React (Frontend)
- **Style**: Use Prettier and ESLint
- **Components**: Functional components with hooks
- **Types**: Define interfaces for all data structures
- **Testing**: Component tests with React Testing Library

### Areas for Contribution

- 🧠 **AI Model Improvements**: Enhance ANFIS, YOLO, or computer vision
- 🎨 **UI/UX Enhancements**: Improve user interface and experience
- 📊 **Data Visualization**: Add new charts and analytics
- 🔧 **Performance Optimization**: Improve speed and efficiency
- 🧪 **Testing**: Add comprehensive test coverage
- 📚 **Documentation**: Improve guides and examples

## 🔒 Security

### Security Features

- **Input Validation**: All user inputs are validated and sanitized
- **File Upload Security**: Restricted file types and size limits
- **CORS Configuration**: Proper cross-origin resource sharing setup
- **Rate Limiting**: API rate limiting to prevent abuse
- **Security Headers**: Comprehensive security headers in nginx

### Vulnerability Reporting

If you discover a security vulnerability:

1. **DO NOT** create a public issue
2. **Email** security details to: security@yourdomain.com
3. **Include** detailed reproduction steps
4. **Wait** for acknowledgment and resolution

### Security Best Practices

- Keep dependencies updated
- Use environment variables for secrets
- Implement proper authentication if needed
- Regular security audits
- Monitor for suspicious activity

## 🔍 Troubleshooting

### Common Issues

#### 1. Docker Build Failures

```bash
# Clean build cache
docker-compose build --no-cache

# Remove all containers and images
docker-compose down --rmi all
docker system prune -a
```

#### 2. Port Conflicts

```bash
# Check what's using the port
netstat -ano | findstr :8000
netstat -ano | findstr :8080

# Kill the process or change ports in docker-compose.yml
```

#### 3. Memory Issues

```bash
# Increase Docker memory limit in Docker Desktop
# Settings > Resources > Memory: 4GB or more
```

#### 4. ANFIS Training Issues

```bash
# Check model status
curl http://localhost:8000/model-status

# Restart training
curl -X POST http://localhost:8000/train-anfis
```

### Performance Optimization

#### Backend Optimization

```python
# Enable async processing
@app.post("/predict")
async def predict_image(file: UploadFile):
    # Process image asynchronously
    result = await process_image_async(file)
    return result
```

#### Frontend Optimization

```typescript
// Use React.memo for expensive components
const ResultsPanel = React.memo(({ results }) => {
  // Component implementation
});

// Implement virtual scrolling for large datasets
import { FixedSizeList as List } from 'react-window';
```

### Monitoring and Logging

```bash
# View application logs
docker-compose logs -f

# Monitor resource usage
docker stats

# Check service health
curl http://localhost:8000/health
```

## 📞 Support

### Getting Help

- **Documentation**: Check this README and API docs
- **Issues**: Create an issue on GitHub for bugs
- **Discussions**: Use GitHub Discussions for questions
- **Email**: Contact support@yourdomain.com

### Community

- **GitHub**: [Repository](https://github.com/isaackcz/BellPeperAI)
- **Discussions**: [GitHub Discussions](https://github.com/isaackcz/BellPeperAI/discussions)
- **Issues**: [GitHub Issues](https://github.com/isaackcz/BellPeperAI/issues)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **ANFIS Research**: Based on Takagi-Sugeno fuzzy inference systems
- **YOLO**: Ultralytics YOLOv8 for object detection
- **OpenCV**: Computer vision library
- **FastAPI**: Modern web framework for APIs
- **React**: Frontend framework
- **Shadcn/ui**: Beautiful UI components

---

**Happy Pepper Vision AI Development! 🌶️🤖**