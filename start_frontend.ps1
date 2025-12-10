# Start Frontend Development Server
# This script installs dependencies and starts the Next.js dev server

Write-Host "🎨 Setting up AR Laptop Troubleshooter Frontend..." -ForegroundColor Cyan
Write-Host ""

# Change to frontend directory
Set-Location "E:\z.code\arvr\frontend"

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
    npm install
    Write-Host "✓ Dependencies installed!" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "✓ Dependencies already installed" -ForegroundColor Green
    Write-Host ""
}

# Start the development server
Write-Host "🚀 Starting Next.js development server..." -ForegroundColor Green
Write-Host "Frontend will be available at: http://localhost:3000" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

npm run dev
