# ============================================
# HRMS AUTO-START SETUP SCRIPT
# Run this ONCE to enable automatic startup
# ============================================

Write-Host "Setting up HRMS Auto-Start..." -ForegroundColor Green

# Create Task Scheduler job
$TaskName = "SmartHRMS-AutoStart"
$TaskPath = "\SmartHRMS\"
$ScriptPath = "C:\Users\Administrator\Documents\HRMS\smart_hrms\START-HRMS-NOW.bat"

# Remove old task if exists
Write-Host "Cleaning up old tasks..."
Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue | Unregister-ScheduledTask -Confirm:$false -ErrorAction SilentlyContinue

# Create new task
Write-Host "Creating new auto-start task..."
$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$ScriptPath`""
$Trigger = New-ScheduledTaskTrigger -AtStartup
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Path $TaskPath -Force | Out-Null

Write-Host "✅ Auto-start enabled!" -ForegroundColor Green
Write-Host "The app will now start automatically on system startup." -ForegroundColor Yellow
Write-Host ""
Write-Host "To start manually right now, double-click: START-HRMS-NOW.bat" -ForegroundColor Cyan
