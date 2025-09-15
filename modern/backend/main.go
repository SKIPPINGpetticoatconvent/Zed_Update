package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/gorilla/mux"
	"github.com/rs/cors"
)

// Response represents a standard API response
type Response struct {
	Success bool        `json:"success"`
	Message string      `json:"message"`
	Data    interface{} `json:"data,omitempty"`
}

// UpdateInfo represents update information
type UpdateInfo struct {
	Version     string    `json:"version"`
	ReleaseDate time.Time `json:"release_date"`
	DownloadURL string    `json:"download_url"`
	Description string    `json:"description"`
	Size        int64     `json:"size"`
	SHA256      string    `json:"sha256"`
	Assets      []Asset   `json:"assets,omitempty"`
}

// Asset represents a release asset
type Asset struct {
	Name        string `json:"name"`
	DownloadURL string `json:"download_url"`
	Size        int64  `json:"size"`
	ContentType string `json:"content_type"`
}

// ZedConfig represents Zed updater configuration
type ZedConfig struct {
	ZedInstallPath       string `json:"zed_install_path"`
	GitHubRepo           string `json:"github_repo"`
	BackupEnabled        bool   `json:"backup_enabled"`
	BackupCount          int    `json:"backup_count"`
	AutoCheckEnabled     bool   `json:"auto_check_enabled"`
	CheckIntervalHours   int    `json:"check_interval_hours"`
	AutoDownload         bool   `json:"auto_download"`
	AutoInstall          bool   `json:"auto_install"`
	AutoStartAfterUpdate bool   `json:"auto_start_after_update"`
	ForceDownloadLatest  bool   `json:"force_download_latest"`
}

// Server represents the HTTP server
type Server struct {
	router *mux.Router
	port   string
	config *ZedConfig
}

// NewServer creates a new server instance
func NewServer(port string) *Server {
	s := &Server{
		router: mux.NewRouter(),
		port:   port,
		config: &ZedConfig{
			ZedInstallPath:       `D:\Zed.exe`,
			GitHubRepo:           "TC999/zed-loc",
			BackupEnabled:        true,
			BackupCount:          3,
			AutoCheckEnabled:     true,
			CheckIntervalHours:   24,
			AutoDownload:         true,
			AutoInstall:          false,
			AutoStartAfterUpdate: true,
			ForceDownloadLatest:  true,
		},
	}
	s.setupRoutes()
	return s
}

// setupRoutes configures all API routes
func (s *Server) setupRoutes() {
	api := s.router.PathPrefix("/api/v1").Subrouter()

	// Health check endpoint
	api.HandleFunc("/health", s.handleHealth).Methods("GET")

	// Update related endpoints
	api.HandleFunc("/updates/check", s.handleCheckUpdates).Methods("GET")
	api.HandleFunc("/updates/download", s.handleDownloadUpdate).Methods("POST")
	api.HandleFunc("/updates/install", s.handleInstallUpdate).Methods("POST")

	// System information endpoints
	api.HandleFunc("/system/info", s.handleSystemInfo).Methods("GET")
	api.HandleFunc("/system/status", s.handleSystemStatus).Methods("GET")

	// Configuration endpoints
	api.HandleFunc("/config", s.handleGetConfig).Methods("GET")
	api.HandleFunc("/config", s.handleSetConfig).Methods("POST")

	// Zed specific endpoints
	api.HandleFunc("/zed/version", s.handleGetZedVersion).Methods("GET")
	api.HandleFunc("/zed/start", s.handleStartZed).Methods("POST")
	api.HandleFunc("/zed/backup", s.handleBackupZed).Methods("POST")
}

// handleHealth returns server health status
func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	response := Response{
		Success: true,
		Message: "Server is running",
		Data: map[string]interface{}{
			"timestamp": time.Now(),
			"version":   "1.0.0",
		},
	}
	s.writeJSON(w, http.StatusOK, response)
}

// handleCheckUpdates checks for available updates from GitHub
func (s *Server) handleCheckUpdates(w http.ResponseWriter, r *http.Request) {
	updateInfo, err := s.getLatestReleaseFromGitHub()
	if err != nil {
		s.writeError(w, http.StatusInternalServerError, fmt.Sprintf("Failed to check updates: %v", err))
		return
	}

	response := Response{
		Success: true,
		Message: "Update check completed",
		Data:    updateInfo,
	}
	s.writeJSON(w, http.StatusOK, response)
}

// handleDownloadUpdate handles update download requests
func (s *Server) handleDownloadUpdate(w http.ResponseWriter, r *http.Request) {
	var requestData map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&requestData); err != nil {
		s.writeError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	// Simulate download process
	response := Response{
		Success: true,
		Message: "Download started",
		Data: map[string]interface{}{
			"download_id": "download_123456",
			"progress":    0,
			"status":      "downloading",
		},
	}
	s.writeJSON(w, http.StatusOK, response)
}

// handleGetConfig returns current configuration
func (s *Server) handleGetConfig(w http.ResponseWriter, r *http.Request) {
	response := Response{
		Success: true,
		Message: "Configuration retrieved",
		Data:    s.config,
	}
	s.writeJSON(w, http.StatusOK, response)
}

// handleSetConfig updates configuration
func (s *Server) handleSetConfig(w http.ResponseWriter, r *http.Request) {
	var newConfig ZedConfig
	if err := json.NewDecoder(r.Body).Decode(&newConfig); err != nil {
		s.writeError(w, http.StatusBadRequest, "Invalid configuration data")
		return
	}

	s.config = &newConfig

	response := Response{
		Success: true,
		Message: "Configuration updated",
		Data:    s.config,
	}
	s.writeJSON(w, http.StatusOK, response)
}

// handleGetZedVersion gets current Zed version
func (s *Server) handleGetZedVersion(w http.ResponseWriter, r *http.Request) {
	version, err := s.getCurrentZedVersion()
	if err != nil {
		s.writeError(w, http.StatusInternalServerError, fmt.Sprintf("Failed to get Zed version: %v", err))
		return
	}

	response := Response{
		Success: true,
		Message: "Zed version retrieved",
		Data: map[string]interface{}{
			"version": version,
			"path":    s.config.ZedInstallPath,
		},
	}
	s.writeJSON(w, http.StatusOK, response)
}

// handleStartZed starts Zed application
func (s *Server) handleStartZed(w http.ResponseWriter, r *http.Request) {
	err := s.startZedApplication()
	if err != nil {
		s.writeError(w, http.StatusInternalServerError, fmt.Sprintf("Failed to start Zed: %v", err))
		return
	}

	response := Response{
		Success: true,
		Message: "Zed application started",
		Data: map[string]interface{}{
			"path": s.config.ZedInstallPath,
		},
	}
	s.writeJSON(w, http.StatusOK, response)
}

// handleBackupZed creates backup of current Zed installation
func (s *Server) handleBackupZed(w http.ResponseWriter, r *http.Request) {
	backupPath, err := s.createZedBackup()
	if err != nil {
		s.writeError(w, http.StatusInternalServerError, fmt.Sprintf("Failed to create backup: %v", err))
		return
	}

	response := Response{
		Success: true,
		Message: "Backup created successfully",
		Data: map[string]interface{}{
			"backup_path": backupPath,
		},
	}
	s.writeJSON(w, http.StatusOK, response)
}

// getLatestReleaseFromGitHub fetches latest release info from GitHub API
func (s *Server) getLatestReleaseFromGitHub() (*UpdateInfo, error) {
	apiURL := fmt.Sprintf("https://api.github.com/repos/%s/releases/latest", s.config.GitHubRepo)

	client := &http.Client{Timeout: 30 * time.Second}
	req, err := http.NewRequest("GET", apiURL, nil)
	if err != nil {
		return nil, err
	}

	req.Header.Set("User-Agent", "ZedUpdater-Backend/1.0.0")
	req.Header.Set("Accept", "application/vnd.github.v3+json")

	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("GitHub API returned status %d", resp.StatusCode)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var release struct {
		TagName     string    `json:"tag_name"`
		Name        string    `json:"name"`
		Body        string    `json:"body"`
		PublishedAt time.Time `json:"published_at"`
		Assets      []struct {
			Name        string `json:"name"`
			DownloadURL string `json:"browser_download_url"`
			Size        int64  `json:"size"`
			ContentType string `json:"content_type"`
		} `json:"assets"`
	}

	if err := json.Unmarshal(body, &release); err != nil {
		return nil, err
	}

	// Find Windows executable asset
	var downloadURL string
	var assetSize int64
	for _, asset := range release.Assets {
		if strings.Contains(strings.ToLower(asset.Name), "windows") &&
			strings.HasSuffix(strings.ToLower(asset.Name), ".exe") {
			downloadURL = asset.DownloadURL
			assetSize = asset.Size
			break
		}
	}

	if downloadURL == "" && len(release.Assets) > 0 {
		// Fallback to first asset if no Windows-specific one found
		downloadURL = release.Assets[0].DownloadURL
		assetSize = release.Assets[0].Size
	}

	updateInfo := &UpdateInfo{
		Version:     strings.TrimPrefix(release.TagName, "v"),
		ReleaseDate: release.PublishedAt,
		DownloadURL: downloadURL,
		Description: release.Body,
		Size:        assetSize,
	}

	return updateInfo, nil
}

// getCurrentZedVersion attempts to get current Zed version
func (s *Server) getCurrentZedVersion() (string, error) {
	if _, err := os.Stat(s.config.ZedInstallPath); os.IsNotExist(err) {
		return "", fmt.Errorf("Zed executable not found at %s", s.config.ZedInstallPath)
	}

	// Try to get version info using file properties (Windows specific)
	// For now, return a placeholder version
	return "1.0.0", nil
}

// startZedApplication starts the Zed application
func (s *Server) startZedApplication() error {
	if _, err := os.Stat(s.config.ZedInstallPath); os.IsNotExist(err) {
		return fmt.Errorf("Zed executable not found at %s", s.config.ZedInstallPath)
	}

	// Start Zed process in background
	// This is a simplified implementation
	go func() {
		// In a real implementation, use os/exec to start the process
		log.Printf("Starting Zed from: %s", s.config.ZedInstallPath)
	}()

	return nil
}

// createZedBackup creates a backup of the current Zed installation
func (s *Server) createZedBackup() (string, error) {
	if !s.config.BackupEnabled {
		return "", fmt.Errorf("backup is disabled")
	}

	if _, err := os.Stat(s.config.ZedInstallPath); os.IsNotExist(err) {
		return "", fmt.Errorf("Zed executable not found at %s", s.config.ZedInstallPath)
	}

	// Create backup directory
	backupDir := filepath.Join(filepath.Dir(s.config.ZedInstallPath), "backups")
	if err := os.MkdirAll(backupDir, 0755); err != nil {
		return "", err
	}

	// Generate backup filename with timestamp
	timestamp := time.Now().Format("20060102_150405")
	backupPath := filepath.Join(backupDir, fmt.Sprintf("Zed_backup_%s.exe", timestamp))

	// Copy file (simplified - in real implementation, use io.Copy)
	log.Printf("Creating backup: %s -> %s", s.config.ZedInstallPath, backupPath)

	return backupPath, nil
}

// handleInstallUpdate handles update installation requests
func (s *Server) handleInstallUpdate(w http.ResponseWriter, r *http.Request) {
	var requestData map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&requestData); err != nil {
		s.writeError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	// Simulate installation process
	response := Response{
		Success: true,
		Message: "Installation started",
		Data: map[string]interface{}{
			"install_id": "install_789012",
			"progress":   0,
			"status":     "installing",
		},
	}
	s.writeJSON(w, http.StatusOK, response)
}

// handleSystemInfo returns system information
func (s *Server) handleSystemInfo(w http.ResponseWriter, r *http.Request) {
	systemInfo := map[string]interface{}{
		"os":           "windows",
		"architecture": "amd64",
		"go_version":   "1.21",
		"server_port":  s.port,
	}

	response := Response{
		Success: true,
		Message: "System information retrieved",
		Data:    systemInfo,
	}
	s.writeJSON(w, http.StatusOK, response)
}

// handleSystemStatus returns current system status
func (s *Server) handleSystemStatus(w http.ResponseWriter, r *http.Request) {
	status := map[string]interface{}{
		"uptime":    time.Since(time.Now().Add(-time.Hour)),
		"memory":    "Available",
		"disk":      "Available",
		"network":   "Connected",
		"timestamp": time.Now(),
	}

	response := Response{
		Success: true,
		Message: "System status retrieved",
		Data:    status,
	}
	s.writeJSON(w, http.StatusOK, response)
}

// writeJSON writes a JSON response
func (s *Server) writeJSON(w http.ResponseWriter, status int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)

	if err := json.NewEncoder(w).Encode(data); err != nil {
		log.Printf("Error encoding JSON: %v", err)
	}
}

// writeError writes an error response
func (s *Server) writeError(w http.ResponseWriter, status int, message string) {
	response := Response{
		Success: false,
		Message: message,
	}
	s.writeJSON(w, status, response)
}

// Start starts the HTTP server
func (s *Server) Start() error {
	// Setup CORS
	c := cors.New(cors.Options{
		AllowedOrigins: []string{"*"},
		AllowedMethods: []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowedHeaders: []string{"*"},
	})

	handler := c.Handler(s.router)

	log.Printf("Starting server on port %s", s.port)
	return http.ListenAndServe(":"+s.port, handler)
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	server := NewServer(port)

	log.Printf("Zed Update Backend Server starting...")
	log.Printf("Server will be available at http://localhost:%s", port)
	log.Printf("Health check: http://localhost:%s/api/v1/health", port)

	if err := server.Start(); err != nil {
		log.Fatalf("Server failed to start: %v", err)
	}
}
