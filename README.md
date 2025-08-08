# 🌶️ Bell Pepper Vision AI

An intelligent AI-powered system for bell pepper quality assessment using ANFIS (Adaptive Neuro-Fuzzy Inference System), YOLO object detection, and advanced computer vision techniques.

## 🚀 Quick Start

### Docker Deployment

```bash
# Clone the repository
git clone https://github.com/isaackcz/BellPeperAI.git
cd BellPeperAI

# Start all services
docker-compose up --build

# Or use the provided script
.\run.bat
```

### Access the Application

- **Frontend**: http://localhost:8080
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🎯 Key Features

- 🔍 **Defect Detection**: Identify 6 types of defects using ANFIS
- 🎨 **Color Grading**: Analyze ripeness and quality
- 📏 **Size & Shape Analysis**: Measure dimensions and properties
- 🧠 **Active Learning**: Continuously improve model performance
- 📊 **Comprehensive Reporting**: Detailed feature extraction

## 🏗️ Architecture

- **ANFIS Model**: 50% - Advanced neuro-fuzzy system
- **YOLO Object Detection**: 25% - Real-time segmentation
- **Computer Vision**: 15% - Color, texture, shape analysis
- **Feature Engineering**: 10% - HSV, GLCM, contour analysis

## 📚 Documentation

For comprehensive documentation, see the [docs folder](docs/README.md):

- [Complete Documentation](docs/README.md) - Full setup and usage guide
- [Docker Setup](docs/README.md#docker-setup) - Docker configuration
- [API Reference](docs/README.md#api-documentation) - API endpoints
- [Development Guide](docs/README.md#development-guide) - Docker development
- [Deployment](docs/README.md#deployment) - Production deployment

## 🛠️ Technology Stack

- **Frontend**: React 18, TypeScript, Vite, Shadcn/ui
- **Backend**: FastAPI, Python 3.10, Uvicorn
- **AI/ML**: ANFIS, YOLOv8, OpenCV, scikit-image
- **Deployment**: Docker, Docker Compose, Nginx

## 🤝 Contributing

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for contribution guidelines.

## 📄 License

This project is licensed under the MIT License - see [LICENSE](docs/LICENSE) for details.

---

**Happy Pepper Vision AI Development! 🌶️🤖**