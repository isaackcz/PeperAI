# 🌶️ Bell Pepper Vision AI

An intelligent AI-powered system for bell pepper quality assessment using ANFIS (Adaptive Neuro-Fuzzy Inference System), YOLO object detection, and advanced computer vision techniques.

## 🚀 Quick Start

### 🌐 Deploy Online (FREE) - 2 Minutes!

**Get your app online instantly with GitHub Pages:**

1. **Fork this repository** (click Fork button above)
2. **Enable GitHub Pages**: Settings → Pages → Source: GitHub Actions
3. **Deploy**: Actions tab → "Deploy to GitHub Pages" → Run workflow
4. **Access**: `https://YOUR_USERNAME.github.io/pepper-vision-grade-main`

📖 **[Complete GitHub Deployment Guide](DEPLOY_TO_GITHUB.md)**

### 🐳 Local Docker Deployment

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

## 🔧 Troubleshooting

### ❌ Command Window Closes Immediately

If `run.bat` opens and closes immediately:

**Quick Fixes:**
```bash
# 1. Run diagnostics
.\diagnose_startup_issues.bat

# 2. Check device compatibility
.\test_device_compatibility.bat

# 3. Fix window closing issue
.\fix_window_closing.bat
```

**Common Causes:**
- Docker Desktop not installed or running
- Running from wrong directory
- Ports 8000, 8001, 8080 already in use
- System compatibility issues

**Manual Alternative:**
```bash
docker --version
docker-compose up -d
start http://localhost:8080
```

📖 **[Complete Device Compatibility Guide](DEVICE_COMPATIBILITY_GUIDE.md)**

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

## 🌐 Deployment Options

| Platform | Cost | Setup Time | AI Processing | Best For |
|----------|------|------------|---------------|----------|
| **[GitHub Pages](DEPLOY_TO_GITHUB.md)** | Free | 2 min | Demo | Portfolio/Demo |
| **[Vercel](GITHUB_DEPLOYMENT_GUIDE.md#vercel)** | Free | 5 min | Demo | Testing |
| **[Railway](RAILWAY_DEPLOYMENT_GUIDE.md)** | Free tier | 10 min | Full | Production |
| **[Oracle Cloud](ORACLE_QUICK_START.md)** | Free | 15 min | Full | Enterprise |
| **Local Docker** | Free | 5 min | Full | Development |

## 📚 Documentation

For comprehensive documentation, see the [docs folder](docs/README.md):

- [Complete Documentation](docs/README.md) - Full setup and usage guide
- [GitHub Deployment](DEPLOY_TO_GITHUB.md) - Deploy online in 2 minutes
- [GitHub Deployment Guide](GITHUB_DEPLOYMENT_GUIDE.md) - All GitHub options
- [Railway Deployment](RAILWAY_DEPLOYMENT_GUIDE.md) - Full AI deployment
- [Oracle Cloud Setup](ORACLE_QUICK_START.md) - Enterprise deployment
- [Docker Setup](docs/README.md#docker-setup) - Local development
- [API Reference](docs/README.md#api-documentation) - API endpoints

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