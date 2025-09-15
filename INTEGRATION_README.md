# Zed Update Manager - Go Backend + Python GUI Integration

A cross-platform update management system with a Go HTTP API backend and Python Tkinter GUI frontend, integrated with GitHub Actions for automated builds.

## 🏗️ Architecture

```
Zed_Update/
├── backend/                 # Go HTTP API Server
│   ├── main.go             # Main server application
│   ├── go.mod              # Go module dependencies
│   └── go.sum              # Go dependency checksums
├── frontend/               # Python GUI Application
│   ├── main.py             # Main GUI application
│   └── requirements.txt    # Python dependencies
├── .github/
│   └── workflows/
│       └── build.yml       # GitHub Actions build pipeline
├── start.bat               # Windows startup script
├── start.sh                # Linux/macOS startup script
└── INTEGRATION_README.md   # This file
```

## 🚀 Features

### Go Backend (Port 8080)
- **RESTful API** with JSON responses
- **CORS enabled** for cross-origin requests
- **Health monitoring** endpoint
- **System information** retrieval
- **Update management** (check, download, install)
- **Concurrent request handling** with Gorilla Mux
- **Cross-platform builds** (Linux, Windows, macOS)

### Python GUI Frontend
- **Modern Tkinter interface** with ttk widgets
- **Real-time backend communication** via HTTP requests
- **Threading support** for non-blocking operations
- **Progress tracking** with visual indicators
- **Activity logging** with timestamps
- **Connection status monitoring**
- **System information display**

### GitHub Actions CI/CD
- **Multi-platform builds** (Ubuntu, Windows, macOS)
- **Go cross-compilation** for multiple architectures
- **Python executable packaging** with PyInstaller
- **Integration testing** with backend/frontend communication
- **Automated releases** with versioned artifacts

## 📋 Prerequisites

### Development Requirements
- **Go 1.21+** - [Download Go](https://golang.org/dl/)
- **Python 3.9+** - [Download Python](https://python.org/downloads/)
- **Git** - For version control
- **Internet connection** - For downloading dependencies

### Runtime Requirements
- **Operating System**: Windows 10+, Ubuntu 18.04+, macOS 10.14+
- **RAM**: 256MB minimum
- **Disk Space**: 100MB for installation
- **Network**: Local network access for GUI-backend communication

## 🛠️ Installation & Setup

### Option 1: Quick Start (Recommended)

#### Windows
```cmd
# Clone the repository
git clone <repository-url>
cd Zed_Update

# Run the startup script
start.bat
```

#### Linux/macOS
```bash
# Clone the repository
git clone <repository-url>
cd Zed_Update

# Make script executable and run
chmod +x start.sh
./start.sh
```

### Option 2: Manual Setup

#### 1. Install Go Dependencies
```bash
cd backend
go mod tidy
go mod download
```

#### 2. Install Python Dependencies
```bash
cd frontend
pip install -r requirements.txt
```

#### 3. Start Backend
```bash
cd backend
go run main.go
```

#### 4. Start Frontend (in new terminal)
```bash
cd frontend
python main.py
```

## 🔌 API Endpoints

### Backend Server (http://localhost:8080)

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| `GET` | `/api/v1/health` | Server health check | Server status and version |
| `GET` | `/api/v1/system/info` | System information | OS, architecture, Go version |
| `GET` | `/api/v1/system/status` | System status | Memory, disk, network status |
| `GET` | `/api/v1/updates/check` | Check for updates | Available update information |
| `POST` | `/api/v1/updates/download` | Download update | Download progress and ID |
| `POST` | `/api/v1/updates/install` | Install update | Installation progress and ID |

### Example API Response
```json
{
  "success": true,
  "message": "Update check completed",
  "data": {
    "version": "2.0.0",
    "release_date": "2024-01-15T10:30:00Z",
    "download_url": "https://github.com/example/releases/v2.0.0.zip",
    "description": "Latest version with bug fixes and new features"
  }
}
```

## 🖥️ GUI Features

### Main Interface Components

1. **Connection Status Panel**
   - Backend connectivity indicator
   - Version information display
   - Manual reconnection button

2. **System Information Panel**
   - OS and architecture details
   - Server configuration
   - System status monitoring
   - Refresh functionality

3. **Update Management Panel**
   - Update availability checking
   - Download progress tracking
   - Installation management
   - Update information display

4. **Progress Tracking**
   - Visual progress bar
   - Status text updates
   - Real-time operation feedback

5. **Activity Log**
   - Timestamped operation logs
   - Error message display
   - Clear log functionality

## 🔧 Configuration

### Environment Variables

#### Backend Configuration
```bash
# Server port (default: 8080)
export PORT=8080

# CORS settings (default: *)
export CORS_ORIGINS="http://localhost:3000,http://localhost:8000"
```

#### Frontend Configuration
```python
# In frontend/main.py
self.backend_url = "http://localhost:8080/api/v1"  # Backend URL
```

### Customization Options

#### Backend Customization
- Modify `backend/main.go` for additional API endpoints
- Update `go.mod` for additional Go dependencies
- Configure CORS settings for production deployment

#### Frontend Customization
- Modify `frontend/main.py` for UI changes
- Update `requirements.txt` for additional Python packages
- Customize themes and layouts in the GUI code

## 🚢 Deployment

### Development Deployment
```bash
# Start both services locally
./start.sh    # Linux/macOS
start.bat     # Windows
```

### Production Deployment

#### Docker Deployment (Backend)
```dockerfile
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY backend/ .
RUN go mod download
RUN go build -o backend main.go

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/
COPY --from=builder /app/backend .
EXPOSE 8080
CMD ["./backend"]
```

#### Executable Distribution
The GitHub Actions workflow automatically creates:
- Go binaries for multiple platforms
- Python executables with PyInstaller
- Release packages with both components

## 🧪 Testing

### Manual Testing
1. **Backend Health Check**
   ```bash
   curl http://localhost:8080/api/v1/health
   ```

2. **GUI Functionality**
   - Launch GUI application
   - Test all buttons and features
   - Verify backend connectivity

### Automated Testing
GitHub Actions runs:
- Go unit tests
- Python import tests
- Integration tests
- Cross-platform builds

### Test Commands
```bash
# Backend tests
cd backend
go test -v ./...

# Frontend tests (manual)
cd frontend
python -c "import tkinter; print('GUI available')"
python -c "import requests; print('HTTP client available')"
```

## 🔍 Troubleshooting

### Common Issues

#### Backend Not Starting
```
Error: listen tcp :8080: bind: address already in use
```
**Solution**: Kill process using port 8080 or use different port
```bash
# Windows
netstat -ano | findstr :8080
taskkill /PID <PID> /F

# Linux/macOS
sudo lsof -i :8080
sudo kill -9 <PID>
```

#### GUI Connection Failed
```
Failed to connect to backend: Connection refused
```
**Solution**: Ensure backend is running first
```bash
# Check backend status
curl http://localhost:8080/api/v1/health
```

#### Python Dependencies Error
```
ModuleNotFoundError: No module named 'requests'
```
**Solution**: Install Python requirements
```bash
pip install -r frontend/requirements.txt
```

#### Go Dependencies Error
```
go: cannot find main module
```
**Solution**: Initialize Go module
```bash
cd backend
go mod init zed-update-backend
go mod tidy
```

### Debug Mode

#### Backend Debug
```bash
cd backend
go run -race main.go  # Race condition detection
```

#### Frontend Debug
```python
# Add to frontend/main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📊 Performance

### System Requirements
- **CPU**: 1 core minimum
- **RAM**: 256MB minimum
- **Disk**: 100MB for installation
- **Network**: Local network access

### Performance Metrics
- **Backend Response Time**: < 100ms
- **GUI Responsiveness**: < 50ms
- **Memory Usage**: < 100MB combined
- **Startup Time**: < 5 seconds

## 🔒 Security

### Security Features
- **CORS Protection**: Configurable origin restrictions
- **Input Validation**: JSON request validation
- **Error Handling**: Secure error messages
- **Local Communication**: Backend-frontend on localhost

### Security Best Practices
1. **Production Deployment**:
   - Configure specific CORS origins
   - Use HTTPS for external access
   - Implement authentication if needed

2. **Development**:
   - Keep dependencies updated
   - Follow secure coding practices
   - Validate all user inputs

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request
5. GitHub Actions runs CI/CD

### Code Style
- **Go**: Follow `gofmt` standards
- **Python**: Follow PEP 8 guidelines
- **Git**: Use conventional commit messages

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Getting Help
1. Check this README for common issues
2. Review GitHub Issues for similar problems
3. Create new issue with detailed description

### Issue Template
```markdown
**Environment**:
- OS: [Windows 10/Ubuntu 20.04/macOS 12]
- Go Version: [1.21.x]
- Python Version: [3.9.x]

**Problem Description**:
[Detailed description of the issue]

**Steps to Reproduce**:
1. [First step]
2. [Second step]
3. [Result]

**Expected Behavior**:
[What should happen]

**Actual Behavior**:
[What actually happens]

**Logs**:
[Any error messages or logs]
```

---

**Built with ❤️ using Go and Python**