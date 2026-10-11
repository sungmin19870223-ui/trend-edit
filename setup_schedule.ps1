# THE TREND EDIT - 3시간마다 자동 수집하도록 Windows 작업 스케줄러에 등록
# 실행: PowerShell 에서  .\setup_schedule.ps1
# 해제: Unregister-ScheduledTask -TaskName "TrendEditCollect" -Confirm:$false

$taskName = "TrendEditCollect"
$batPath = Join-Path $PSScriptRoot "run_collect.bat"

$action = New-ScheduledTaskAction -Execute $batPath -WorkingDirectory $PSScriptRoot
# 오늘 06:00 부터 3시간 간격으로 반복 (06·09·12·15·18·21·24·03시)
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date -Hour 6 -Minute 0 -Second 0) -RepetitionInterval (New-TimeSpan -Hours 3)
# 노트북이 배터리 모드여도 실행, 놓친 실행은 켜지는 대로 실행
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 10)

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description "글로벌 트렌드 RSS 수집 (3시간 주기)" -Force | Out-Null
Write-Host "등록 완료: $taskName (3시간마다 run_collect.bat 실행)"
