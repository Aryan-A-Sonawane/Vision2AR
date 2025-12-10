# Start ML-Powered Diagnosis System V2
Write-Host "Starting ML-Powered Laptop Diagnosis System V2..." -ForegroundColor Green

# Activate virtual environment
E:\z.code\arvr\.venv\Scripts\Activate.ps1

# Set environment variables
$env:DEBUG="False"
$env:TRANSFORMERS_CACHE="E:\z.code\arvr\.cache"

# Optional: Set LLM API keys for advanced question generation
# $env:OPENAI_API_KEY="your-key-here"
# $env:ANTHROPIC_API_KEY="your-key-here"

Write-Host "`n📦 Loading ML models (this may take a moment on first run)..." -ForegroundColor Yellow

# Change to backend directory
Set-Location E:\z.code\arvr\backend

# Start the backend
Write-Host "`n🚀 Starting backend on http://localhost:8000" -ForegroundColor Cyan
Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor Gray
Write-Host "`nFeatures:" -ForegroundColor Yellow
Write-Host "  ✓ Multi-modal input (text + images + video)" -ForegroundColor Green
Write-Host "  ✓ Dynamic question generation" -ForegroundColor Green
Write-Host "  ✓ Computer vision analysis" -ForegroundColor Green
Write-Host "  ✓ Semantic understanding" -ForegroundColor Green
Write-Host "`nPress Ctrl+C to stop`n" -ForegroundColor Gray

python main_v2.py
