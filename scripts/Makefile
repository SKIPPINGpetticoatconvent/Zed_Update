# Makefile for Zed Update Manager
# Cross-platform build system for Go backend and Python GUI

.PHONY: all clean build-backend build-frontend test install dev help

# Variables
GO_VERSION = 1.21
PYTHON_VERSION = 3.9
BACKEND_NAME = zed-update-backend
FRONTEND_NAME = zed-update-gui
BUILD_DIR = build
DIST_DIR = dist

# Go build variables
GOOS ?= $(shell go env GOOS)
GOARCH ?= $(shell go env GOARCH)
CGO_ENABLED ?= 0

# Version and build info
VERSION ?= $(shell git describe --tags --always --dirty 2>/dev/null || echo "dev")
BUILD_TIME = $(shell date -u +"%Y-%m-%dT%H:%M:%SZ")
GIT_COMMIT = $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")

# Build flags
LDFLAGS = -ldflags "-X main.Version=${VERSION} -X main.BuildTime=${BUILD_TIME} -X main.GitCommit=${GIT_COMMIT}"

# Default target
all: clean build-backend build-frontend

# Help target
help:
	@echo "Zed Update Manager Build System"
	@echo "================================"
	@echo ""
	@echo "Available targets:"
	@echo "  all              - Build both backend and frontend"
	@echo "  build-backend    - Build Go backend for current platform"
	@echo "  build-frontend   - Build Python GUI for current platform"
	@echo "  cross-compile    - Build for all supported platforms"
	@echo "  test             - Run all tests"
	@echo "  clean            - Clean build artifacts"
	@echo "  install          - Install dependencies"
	@echo "  dev              - Start development environment"
	@echo "  package          - Create distribution packages"
	@echo "  docker           - Build Docker image"
	@echo ""
	@echo "Backend targets:"
	@echo "  backend-linux    - Build backend for Linux"
	@echo "  backend-windows  - Build backend for Windows"
	@echo "  backend-darwin   - Build backend for macOS"
	@echo ""
	@echo "Frontend targets:"
	@echo "  frontend-exe     - Build standalone executable"
	@echo "  frontend-test    - Test frontend imports"
	@echo ""
	@echo "Environment variables:"
	@echo "  VERSION          - Build version (default: git describe)"
	@echo "  GOOS             - Target OS (linux, windows, darwin)"
	@echo "  GOARCH           - Target architecture (amd64, arm64)"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf $(BUILD_DIR)
	rm -rf $(DIST_DIR)
	rm -rf backend/$(BACKEND_NAME)*
	rm -rf frontend/build
	rm -rf frontend/dist
	rm -rf frontend/__pycache__
	rm -rf frontend/*.spec
	@echo "Clean completed."

# Install dependencies
install: install-backend install-frontend

install-backend:
	@echo "Installing Go dependencies..."
	cd backend && go mod download
	cd backend && go mod verify
	@echo "Go dependencies installed."

install-frontend:
	@echo "Installing Python dependencies..."
	cd frontend && pip install -r requirements.txt
	@echo "Python dependencies installed."

# Build backend
build-backend: install-backend
	@echo "Building Go backend for $(GOOS)/$(GOARCH)..."
	@mkdir -p $(BUILD_DIR)/backend
	cd backend && CGO_ENABLED=$(CGO_ENABLED) GOOS=$(GOOS) GOARCH=$(GOARCH) \
		go build $(LDFLAGS) -o ../$(BUILD_DIR)/backend/$(BACKEND_NAME)-$(GOOS)-$(GOARCH)$(if $(filter windows,$(GOOS)),.exe,) .
	@echo "Backend build completed: $(BUILD_DIR)/backend/$(BACKEND_NAME)-$(GOOS)-$(GOARCH)"

# Build frontend
build-frontend: install-frontend
	@echo "Building Python GUI..."
	@mkdir -p $(BUILD_DIR)/frontend
	cd frontend && python -m py_compile main.py
	cp frontend/main.py $(BUILD_DIR)/frontend/
	cp frontend/requirements.txt $(BUILD_DIR)/frontend/
	@echo "Frontend build completed: $(BUILD_DIR)/frontend/"

# Cross-compilation targets
cross-compile: backend-linux backend-windows backend-darwin
	@echo "Cross-compilation completed for all platforms."

backend-linux:
	@$(MAKE) build-backend GOOS=linux GOARCH=amd64

backend-windows:
	@$(MAKE) build-backend GOOS=windows GOARCH=amd64

backend-darwin:
	@$(MAKE) build-backend GOOS=darwin GOARCH=amd64
	@$(MAKE) build-backend GOOS=darwin GOARCH=arm64

# Frontend executable building
frontend-exe: install-frontend
	@echo "Building standalone executable with PyInstaller..."
	@mkdir -p $(BUILD_DIR)/frontend
	cd frontend && pip install pyinstaller
	cd frontend && pyinstaller --onefile --windowed --name $(FRONTEND_NAME) \
		--distpath ../$(BUILD_DIR)/frontend main.py
	@echo "Executable created: $(BUILD_DIR)/frontend/$(FRONTEND_NAME)"

# Testing
test: test-backend test-frontend

test-backend:
	@echo "Running Go tests..."
	cd backend && go test -v ./...
	@echo "Go tests completed."

test-frontend:
	@echo "Testing Python imports..."
	cd frontend && python -c "import tkinter; print('✓ tkinter available')"
	cd frontend && python -c "import requests; print('✓ requests available')"
	cd frontend && python -c "import threading; print('✓ threading available')"
	cd frontend && python -c "import json; print('✓ json available')"
	@echo "Python import tests completed."

# Development environment
dev: install
	@echo "Starting development environment..."
	@echo "Starting backend server..."
	@cd backend && go run main.go &
	@sleep 2
	@echo "Backend started at http://localhost:8080"
	@echo "Starting frontend GUI..."
	@cd frontend && python main.py

# Packaging
package: cross-compile frontend-exe
	@echo "Creating distribution packages..."
	@mkdir -p $(DIST_DIR)

	# Create platform-specific packages
	@echo "Packaging Linux distribution..."
	@mkdir -p $(DIST_DIR)/linux
	cp $(BUILD_DIR)/backend/$(BACKEND_NAME)-linux-amd64 $(DIST_DIR)/linux/
	cp -r $(BUILD_DIR)/frontend/* $(DIST_DIR)/linux/
	cd $(DIST_DIR) && tar -czf $(FRONTEND_NAME)-$(VERSION)-linux.tar.gz linux/

	@echo "Packaging Windows distribution..."
	@mkdir -p $(DIST_DIR)/windows
	cp $(BUILD_DIR)/backend/$(BACKEND_NAME)-windows-amd64.exe $(DIST_DIR)/windows/
	cp -r $(BUILD_DIR)/frontend/* $(DIST_DIR)/windows/
	cd $(DIST_DIR) && zip -r $(FRONTEND_NAME)-$(VERSION)-windows.zip windows/

	@echo "Packaging macOS distribution..."
	@mkdir -p $(DIST_DIR)/darwin
	cp $(BUILD_DIR)/backend/$(BACKEND_NAME)-darwin-amd64 $(DIST_DIR)/darwin/
	cp $(BUILD_DIR)/backend/$(BACKEND_NAME)-darwin-arm64 $(DIST_DIR)/darwin/
	cp -r $(BUILD_DIR)/frontend/* $(DIST_DIR)/darwin/
	cd $(DIST_DIR) && tar -czf $(FRONTEND_NAME)-$(VERSION)-darwin.tar.gz darwin/

	@echo "Distribution packages created in $(DIST_DIR)/"

# Docker support
docker: docker-backend

docker-backend:
	@echo "Building Docker image for backend..."
	docker build -t $(BACKEND_NAME):$(VERSION) -f backend/Dockerfile backend/
	docker tag $(BACKEND_NAME):$(VERSION) $(BACKEND_NAME):latest
	@echo "Docker image built: $(BACKEND_NAME):$(VERSION)"

# Docker Compose for development
docker-dev:
	@echo "Starting development environment with Docker..."
	docker-compose up --build

# Linting and formatting
lint: lint-backend lint-frontend

lint-backend:
	@echo "Running Go linting..."
	cd backend && go fmt ./...
	cd backend && go vet ./...
	@echo "Go linting completed."

lint-frontend:
	@echo "Running Python linting..."
	cd frontend && python -m flake8 main.py --max-line-length=100
	@echo "Python linting completed."

# Security checks
security: security-backend security-frontend

security-backend:
	@echo "Running Go security checks..."
	cd backend && go mod audit || echo "Go audit not available"
	@echo "Go security check completed."

security-frontend:
	@echo "Running Python security checks..."
	cd frontend && pip install safety
	cd frontend && safety check
	@echo "Python security check completed."

# Benchmarks
bench-backend:
	@echo "Running Go benchmarks..."
	cd backend && go test -bench=. -benchmem ./...

# Coverage
coverage: coverage-backend

coverage-backend:
	@echo "Running Go test coverage..."
	cd backend && go test -coverprofile=coverage.out ./...
	cd backend && go tool cover -html=coverage.out -o coverage.html
	@echo "Coverage report generated: backend/coverage.html"

# Release preparation
release: clean test cross-compile frontend-exe package
	@echo "Release $(VERSION) prepared successfully!"
	@echo "Distribution files:"
	@ls -la $(DIST_DIR)/*.tar.gz $(DIST_DIR)/*.zip

# Quick development commands
quick-backend:
	cd backend && go run main.go

quick-frontend:
	cd frontend && python main.py

# Health checks
health-check:
	@echo "Checking system health..."
	@command -v go >/dev/null 2>&1 || { echo "Go is not installed"; exit 1; }
	@command -v python >/dev/null 2>&1 || command -v python3 >/dev/null 2>&1 || { echo "Python is not installed"; exit 1; }
	@echo "✓ Go version: $$(go version)"
	@echo "✓ Python version: $$(python --version 2>&1 || python3 --version 2>&1)"
	@echo "Health check passed!"
