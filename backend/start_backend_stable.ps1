# Stable Backend Startup Script
# Keeps backend running with detailed output

$env:DEBUG = "False"
$env:TRANSFORMERS_CACHE = "E:\z.code\arvr\.cache"
$env:HF_HOME = "E:\z.code\arvr\.cache"

Set-Location E:\z.code\arvr\backend

Write-Host "="*70 -ForegroundColor Cyan
Write-Host " STARTING AR LAPTOP TROUBLESHOOTER BACKEND" -ForegroundColor Cyan
Write-Host "="*70 -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend will start on http://localhost:8000" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""
Write-Host "="*70 -ForegroundColor Cyan
Write-Host ""

# Run with proper error handling
try {
    & E:\z.code\arvr\.venv\Scripts\python.exe main.py
} catch {
    Write-Host ""
    Write-Host "ERROR: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
