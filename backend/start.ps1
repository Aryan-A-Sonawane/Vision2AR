# Start Backend Script
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host " AR Laptop Troubleshooter - Backend Server" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# Set environment variables
$env:HF_HOME = "E:\z.code\arvr\.cache"
$env:DEBUG = "False"

# Change to backend directory
Set-Location E:\z.code\arvr\backend
Write-Host "Working directory: $(Get-Location)" -ForegroundColor Yellow
Write-Host ""

# Start server
Write-Host "Starting Knowledge-Based Diagnosis Engine..." -ForegroundColor Green
Write-Host ""

& E:\z.code\arvr\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000
