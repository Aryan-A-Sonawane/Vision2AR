# Start Backend Script
E:\z.code\arvr\.venv\Scripts\Activate.ps1
Set-Location E:\z.code\arvr\backend
$env:DEBUG="False"
$env:TRANSFORMERS_CACHE="E:\z.code\arvr\.cache"
uvicorn main:app --host 0.0.0.0 --port 8000
