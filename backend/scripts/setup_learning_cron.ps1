# PowerShell script to setup Windows Task Scheduler for daily learning
# Run this script as Administrator

$TaskName = "AR_Laptop_Learning_Cycle"
$ScriptPath = "E:\z.code\arvr\backend\scripts\run_daily_learning.py"
$PythonPath = "E:\z.code\arvr\.venv\Scripts\python.exe"
$WorkingDir = "E:\z.code\arvr\backend"
$LogPath = "E:\z.code\arvr\backend\logs\learning_cycle.log"

Write-Host "🔧 Setting up daily learning cycle task..." -ForegroundColor Cyan

# Create logs directory if it doesn't exist
$LogDir = Split-Path -Parent $LogPath
if (!(Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
    Write-Host "✅ Created logs directory: $LogDir" -ForegroundColor Green
}

# Remove existing task if it exists
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($ExistingTask) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "🗑️ Removed existing task" -ForegroundColor Yellow
}

# Create task action
$Action = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument "$ScriptPath" `
    -WorkingDirectory $WorkingDir

# Create task trigger (daily at 2:00 AM)
$Trigger = New-ScheduledTaskTrigger -Daily -At 2:00AM

# Create task settings
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1)

# Create task principal (run as current user)
$Principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Highest

# Register the task
Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description "Daily learning cycle for AR Laptop Repair diagnostic system. Discovers patterns and generates questions from successful resolutions." | Out-Null

Write-Host "✅ Task scheduled successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Task Details:" -ForegroundColor White
Write-Host "   Name: $TaskName"
Write-Host "   Schedule: Daily at 2:00 AM"
Write-Host "   Script: $ScriptPath"
Write-Host "   Working Dir: $WorkingDir"
Write-Host "   Logs: $LogPath"
Write-Host ""
Write-Host "🔍 To verify the task:" -ForegroundColor Cyan
Write-Host "   Get-ScheduledTask -TaskName '$TaskName'"
Write-Host ""
Write-Host "▶️ To run the task manually:" -ForegroundColor Cyan
Write-Host "   Start-ScheduledTask -TaskName '$TaskName'"
Write-Host ""
Write-Host "🗑️ To remove the task:" -ForegroundColor Cyan
Write-Host "   Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"
Write-Host ""

# Offer to run test
$RunTest = Read-Host "Would you like to run a test now? (y/n)"
if ($RunTest -eq "y" -or $RunTest -eq "Y") {
    Write-Host ""
    Write-Host "🧪 Running test execution..." -ForegroundColor Yellow
    Start-ScheduledTask -TaskName $TaskName
    Start-Sleep -Seconds 3
    
    # Check task status
    $TaskInfo = Get-ScheduledTaskInfo -TaskName $TaskName
    Write-Host ""
    Write-Host "📊 Task Status:" -ForegroundColor White
    Write-Host "   Last Run: $($TaskInfo.LastRunTime)"
    Write-Host "   Last Result: $($TaskInfo.LastTaskResult)"
    Write-Host ""
    
    if ($TaskInfo.LastTaskResult -eq 0) {
        Write-Host "✅ Test execution successful!" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Test execution may have failed. Check logs." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "🎉 Setup complete!" -ForegroundColor Green
