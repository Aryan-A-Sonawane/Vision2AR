# Start Backend Server
# This script activates the virtual environment and starts the FastAPI server

Write-Host "🚀 Starting AR Laptop Troubleshooter Backend..." -ForegroundColor Cyan
Write-Host ""

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "E:\z.code\arvr\.venv\Scripts\Activate.ps1"

# Change to backend directory
Set-Location "E:\z.code\arvr\backend"

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  WARNING: .env file not found!" -ForegroundColor Red
    Write-Host "Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "Please edit .env with your credentials before running again." -ForegroundColor Yellow
    Write-Host ""
}

# Start the server
Write-Host "Starting FastAPI server on http://localhost:8000" -ForegroundColor Green
Write-Host "API documentation: http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

python main.py
