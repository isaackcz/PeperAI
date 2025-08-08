# Pepper Vision Grade - Batch File Management

## 🚀 Quick Start

### To Start the Complete System:
```bash
run.bat
```

### To Stop All Services:
```bash
stop.bat
```

## 📋 What Each Batch File Does

### `run.bat` - Complete System Startup

This script automatically starts the entire Pepper Vision system:

#### **Step 1: System Requirements Check**
- ✅ Verifies Python 3.8+ is installed
- ✅ Verifies Node.js 16+ is installed  
- ✅ Checks for Docker availability

#### **Step 2: Docker Containers**
- 🐳 Starts Docker containers (if Docker is available)
- ⚠️ Continues if Docker is not available

#### **Step 3: Python Environment**
- 🔧 Activates virtual environment (if available)
- 📦 Installs Python dependencies from `requirements.txt`
- ⚠️ Falls back to system Python if venv is corrupted

#### **Step 4: Backend API Server**
- 🖥️ Starts FastAPI backend server on `http://localhost:8000`
- 🔄 Uses simple server if uvicorn fails
- 📊 Loads trained AI models (Transfer Learning, ANFIS, Ensemble)

#### **Step 5: Frontend Development Server**
- 🌐 Starts React/Vite frontend on `http://localhost:3000`
- 📦 Installs npm dependencies if needed
- 🎨 Opens frontend in default browser

#### **Step 6: System Ready**
- 🎯 All services running and accessible
- 📱 AI-powered bell pepper classification ready
- 🔍 Real-time analysis capabilities active

### `stop.bat` - Complete System Shutdown

This script safely stops all services and cleans up:

#### **Step 1: Frontend Shutdown**
- 🛑 Stops Node.js development server
- 🗂️ Closes frontend service windows

#### **Step 2: Backend Shutdown**
- 🛑 Stops Python API server
- 🛑 Kills uvicorn processes
- 🗂️ Closes backend service windows

#### **Step 3: Docker Cleanup**
- 🐳 Stops all Docker containers
- 🧹 Removes container resources

#### **Step 4: File Cleanup**
- 🗑️ Cleans temporary upload files
- 🗑️ Removes Python cache directories
- 🗑️ Cleans frontend build cache

#### **Step 5: Process Cleanup**
- 🛑 Closes all service windows
- 🧹 Terminates remaining processes

## 🎯 System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │     Docker      │
│                 │    │                 │    │                 │
│ • React/Vite    │◄──►│ • FastAPI       │◄──►│ • Containers    │
│ • AI Interface  │    │ • AI Models     │    │ • Services      │
│ • Real-time UI  │    │ • Image Proc    │    │ • Database      │
│ • Port 3000     │    │ • Port 8000     │    │ • Port 5432     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔧 AI Models Available

### **Transfer Learning (Recommended)**
- 🏆 **Accuracy**: 92.37%
- 🧠 **Type**: Deep Learning (ResNet50V2)
- ⚡ **Speed**: Fast inference
- 🎯 **Best for**: Production use

### **Ensemble AI**
- ⚖️ **Accuracy**: 85.17%
- 🔄 **Type**: Combined (ANFIS + Transfer Learning)
- 🛡️ **Features**: Robust, fallback capability
- 🎯 **Best for**: Balanced performance

### **ANFIS**
- 📊 **Accuracy**: 18.64%
- 🧮 **Type**: Fuzzy Logic
- 🔍 **Features**: Interpretable results
- 🎯 **Best for**: Research/interpretability

## 🚨 Troubleshooting

### **Common Issues & Solutions**

#### **1. Virtual Environment Corrupted**
```
Error: ValueError: source code string cannot contain null bytes
```
**Solution**: The script automatically falls back to system Python

#### **2. Port Already in Use**
```
Error: Address already in use
```
**Solution**: Run `stop.bat` first, then `run.bat`

#### **3. Dependencies Missing**
```
Error: ModuleNotFoundError
```
**Solution**: The script automatically installs dependencies

#### **4. Docker Not Available**
```
Warning: Docker not found
```
**Solution**: System works without Docker - local services only

### **Manual Recovery**

If batch files fail, you can manually start services:

```bash
# Backend (Terminal 1)
cd backend/app
python simple_server.py

# Frontend (Terminal 2)  
cd frontend
npm run dev
```

## 📊 System Requirements

### **Minimum Requirements**
- **OS**: Windows 10/11
- **Python**: 3.8+
- **Node.js**: 16+
- **RAM**: 4GB
- **Storage**: 2GB free space

### **Recommended Requirements**
- **OS**: Windows 11
- **Python**: 3.10+
- **Node.js**: 18+
- **RAM**: 8GB+
- **Storage**: 5GB free space
- **Docker**: Desktop (optional)

## 🎮 Usage Instructions

### **1. Start the System**
```bash
# Double-click or run in terminal
run.bat
```

### **2. Use the AI System**
1. **Upload Image**: Drag & drop or click to upload bell pepper image
2. **Select Model**: Choose AI model (Transfer Learning recommended)
3. **Analyze**: Click "Analyze with AI" button
4. **View Results**: See classification, confidence, and recommendations

### **3. Stop the System**
```bash
# Double-click or run in terminal
stop.bat
```

## 🔍 Monitoring

### **Service Status**
- **Backend**: Check `http://localhost:8000/health`
- **Frontend**: Check `http://localhost:3000`
- **Docker**: Check `docker ps` (if available)

### **Logs**
- **Backend**: Check the "Pepper Vision Backend" window
- **Frontend**: Check the "Pepper Vision Frontend" window
- **System**: Check the main batch file window

## 🎉 Success Indicators

### **System Running Successfully**
- ✅ Frontend opens in browser automatically
- ✅ AI model selector shows available models
- ✅ Image upload works
- ✅ Analysis returns results
- ✅ No error messages in service windows

### **Ready for Production**
- 🚀 All AI models loaded (92.37% accuracy available)
- 🔄 Real-time analysis working
- 🎯 Classification results accurate
- 📱 User-friendly interface active

---

## 📞 Support

If you encounter issues:
1. Run `stop.bat` to clean up
2. Check system requirements
3. Try `run.bat` again
4. Check service windows for error messages

**Happy Bell Pepper Classification! 🫑✨** 