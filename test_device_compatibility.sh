#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================"
echo "    Device Compatibility Test"
echo "========================================"
echo

echo -e "${BLUE}🔍 Checking system architecture...${NC}"
echo "Architecture: $(uname -m)"
echo "System: $(uname -s)"
echo "Kernel: $(uname -r)"
echo

# Determine platform
ARCH=$(uname -m)
case $ARCH in
    x86_64)
        PLATFORM="linux/amd64"
        ARCH_TYPE="Intel/AMD 64-bit"
        ;;
    arm64|aarch64)
        PLATFORM="linux/arm64"
        ARCH_TYPE="ARM 64-bit"
        ;;
    *)
        PLATFORM="auto-detect"
        ARCH_TYPE="Unknown ($ARCH)"
        ;;
esac

echo "Detected: $ARCH_TYPE"
echo "Docker Platform: $PLATFORM"
echo

echo -e "${BLUE}🐳 Checking Docker availability...${NC}"
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✅ Docker is available${NC}"
    docker --version
else
    echo -e "${RED}❌ Docker is not available${NC}"
    echo "Please install Docker from https://docker.com"
    exit 1
fi
echo

echo -e "${BLUE}🔧 Checking Docker platform support...${NC}"
if docker buildx version &> /dev/null; then
    echo -e "${GREEN}✅ Docker Buildx is available (multi-platform support)${NC}"
    docker buildx ls
else
    echo -e "${YELLOW}⚠️  Docker Buildx not available (limited platform support)${NC}"
fi
echo

echo -e "${BLUE}📊 Checking system resources...${NC}"
echo "Memory:"
if command -v free &> /dev/null; then
    free -h
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Total: $(sysctl -n hw.memsize | awk '{print $1/1024/1024/1024 " GB"}')"
fi
echo
echo "CPU Cores:"
if command -v nproc &> /dev/null; then
    echo "Cores: $(nproc)"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Cores: $(sysctl -n hw.ncpu)"
fi
echo

echo -e "${BLUE}🧪 Testing Docker build capability...${NC}"
echo "Testing basic Docker functionality..."
if docker run --rm hello-world &> /dev/null; then
    echo -e "${GREEN}✅ Docker can run containers successfully${NC}"
else
    echo -e "${RED}❌ Docker cannot run containers${NC}"
    echo "Please check Docker daemon is running"
fi
echo

echo -e "${BLUE}🎯 Recommended configuration for your device:${NC}"
echo "- Platform: $PLATFORM"
echo "- Architecture: $ARCH_TYPE"

if [[ "$ARCH" == "x86_64" ]]; then
    echo "- Use: docker-compose -f docker-compose.oracle.yml up --build"
    echo "- For better performance, ensure 8GB+ RAM available for Docker"
elif [[ "$ARCH" == "arm64" ]] || [[ "$ARCH" == "aarch64" ]]; then
    echo "- Use: docker-compose -f docker-compose.oracle.yml up --build"
    echo "- Native ARM64 performance expected"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "- Apple Silicon detected: Excellent native performance"
    fi
else
    echo "- Platform: Auto-detect"
    echo "- May need manual platform specification"
fi
echo

echo -e "${BLUE}🚀 Quick start commands:${NC}"
echo "1. Full system: ./run.bat (Windows) or chmod +x start.sh && ./start.sh (Linux/macOS)"
echo "2. Oracle deployment: docker-compose -f docker-compose.oracle.yml up -d"
echo "3. Development mode: cd docker && ./build-dev.bat"
echo

echo -e "${BLUE}🔧 Platform-specific commands:${NC}"
echo "Force AMD64: docker-compose -f docker-compose.oracle.yml build --platform linux/amd64"
echo "Force ARM64: docker-compose -f docker-compose.oracle.yml build --platform linux/arm64"
echo "Multi-platform: docker buildx build --platform linux/amd64,linux/arm64 ."
echo

echo -e "${BLUE}📚 For detailed troubleshooting, see:${NC}"
echo "- DEVICE_COMPATIBILITY_GUIDE.md"
echo "- DEVELOPMENT-SETUP.md"
echo "- ORACLE_CLOUD_DEPLOYMENT_GUIDE.md"
echo

echo "========================================"
echo "Test completed."

# Make the script executable
chmod +x "$0" 2>/dev/null || true