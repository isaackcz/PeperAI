# Device Compatibility Guide

## 🚨 Common Error: Architecture Mismatch

### Problem
The original `docker-compose.oracle.yml` was configured to only build for ARM64 architecture, causing failures on Intel/AMD (x86_64) devices.

### ✅ Solution Applied
Updated the Docker Compose configuration to support multiple architectures:

```yaml
# Support multiple architectures
platforms:
  - linux/arm64   # For Apple Silicon, Oracle Cloud ARM instances
  - linux/amd64   # For Intel/AMD processors
```

## 🔧 Device-Specific Troubleshooting

### Intel/AMD Devices (x86_64)

#### Common Issues:
1. **Architecture mismatch errors**
2. **PyTorch/TensorFlow compatibility issues**
3. **OpenCV compilation problems**

#### Solutions:
```bash
# Force platform specification
docker-compose -f docker-compose.oracle.yml build --platform linux/amd64

# Or set environment variable
export DOCKER_DEFAULT_PLATFORM=linux/amd64
docker-compose -f docker-compose.oracle.yml up --build
```

### Apple Silicon (M1/M2/M3)

#### Common Issues:
1. **Rosetta emulation slowness**
2. **Native ARM64 dependency conflicts**

#### Solutions:
```bash
# Use native ARM64 build
docker-compose -f docker-compose.oracle.yml build --platform linux/arm64

# For development, use native Python
python3 -m venv venv
source venv/bin/activate
pip install -r backend-requirements.txt
```

### Windows Devices

#### Common Issues:
1. **WSL2 Docker integration**
2. **Path separator conflicts**
3. **Memory allocation limits**

#### Solutions:
```powershell
# Ensure WSL2 is enabled
wsl --set-default-version 2

# Increase Docker memory limit (Docker Desktop Settings)
# Recommended: 8GB+ for full ML functionality

# Use Windows-compatible paths
docker-compose -f docker-compose.oracle.yml up --build
```

## 🐳 Docker Build Strategies

### Multi-Architecture Build
```bash
# Create and use buildx builder
docker buildx create --name multiarch --use
docker buildx inspect --bootstrap

# Build for multiple platforms
docker buildx build --platform linux/amd64,linux/arm64 -t pepper-vision .
```

### Platform-Specific Builds
```bash
# For Intel/AMD
docker build --platform linux/amd64 -t pepper-vision-amd64 .

# For ARM64
docker build --platform linux/arm64 -t pepper-vision-arm64 .
```

## 🔍 Dependency Compatibility

### Heavy ML Dependencies
The following packages may cause architecture-specific issues:

- **TensorFlow**: Use `tensorflow-cpu` for better compatibility
- **PyTorch**: Auto-detects architecture but may need specific versions
- **OpenCV**: May require compilation on some architectures
- **Ultralytics**: YOLO models work across architectures

### Lightweight Alternative
For devices with limited resources, use the minimal backend:

```bash
# Use minimal requirements
cp backend-requirements.txt docker/backend-requirements.txt
docker-compose up --build
```

## 🚀 Quick Device Detection

### Check Your Architecture
```bash
# Linux/macOS
uname -m
# x86_64 = Intel/AMD
# arm64 = Apple Silicon
# aarch64 = ARM64

# Windows
echo %PROCESSOR_ARCHITECTURE%
# AMD64 = Intel/AMD 64-bit
# ARM64 = ARM 64-bit
```

### Docker Platform Check
```bash
# Check Docker platform
docker version --format '{{.Server.Arch}}'

# List available platforms
docker buildx ls
```

## 🛠️ Environment-Specific Commands

### Oracle Cloud (ARM64)
```bash
# Optimized for Oracle Cloud ARM instances
docker-compose -f docker-compose.oracle.yml up -d
```

### Local Development (Any Architecture)
```bash
# Auto-detect architecture
docker-compose up --build
```

### Production (Multi-Architecture)
```bash
# Build for current platform
docker-compose -f docker-compose.oracle.yml build
docker-compose -f docker-compose.oracle.yml up -d
```

## 📊 Performance Expectations

### ARM64 Devices
- **Oracle Cloud A1**: Excellent performance, optimized
- **Apple Silicon**: Native performance, fast builds
- **Raspberry Pi**: Limited, use minimal configuration

### x86_64 Devices
- **Intel/AMD Desktop**: Excellent performance
- **Cloud VPS**: Good performance, depends on specs
- **Older Hardware**: May need resource limits

## 🔧 Resource Configuration

### Memory Limits by Device Type
```yaml
# High-end devices (16GB+ RAM)
deploy:
  resources:
    limits:
      memory: 8G
      cpus: '4'

# Mid-range devices (8GB RAM)
deploy:
  resources:
    limits:
      memory: 4G
      cpus: '2'

# Low-end devices (4GB RAM)
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '1'
```

## 🆘 Emergency Fallback

If Docker builds fail completely:

```bash
# Use local Python environment
cd backend/app
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

pip install fastapi uvicorn pillow numpy
python simple_server.py
```

## 📞 Getting Help

1. **Check Docker logs**: `docker-compose logs -f`
2. **Verify architecture**: Use commands above
3. **Try platform flag**: `--platform linux/amd64` or `--platform linux/arm64`
4. **Use minimal config**: Switch to basic requirements
5. **Check system resources**: Ensure sufficient RAM/CPU

---

**Note**: The architecture compatibility fix has been applied to `docker-compose.oracle.yml`. The system now supports both ARM64 and AMD64 architectures automatically.