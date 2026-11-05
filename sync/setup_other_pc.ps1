# 다른 PC에서 한 번만 실행: 저장소 clone + 매일 자동 pull 작업 등록
# 사용 예:
#   powershell -ExecutionPolicy Bypass -File setup_other_pc.ps1 -RepoUrl https://github.com/<계정>/car-db.git -Target C:\car-db -Time 09:00
param(
    [Parameter(Mandatory = $true)][string]$RepoUrl,
    [string]$Target = "$env:USERPROFILE\car-db",
    [string]$Time = "09:00"
)
$ErrorActionPreference = "Stop"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "git 이 설치돼 있지 않습니다. sync_download.ps1(ZIP 방식)을 쓰거나 git 설치 후 다시 실행하세요."
    exit 1
}
if (-not (Test-Path (Join-Path $Target ".git"))) {
    git clone $RepoUrl $Target
} else {
    Write-Host "이미 clone 되어 있음: $Target"
}

$script = Join-Path $Target "sync\sync_pull.ps1"
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$script`""
$trigger = New-ScheduledTaskTrigger -Daily -At $Time
Register-ScheduledTask -TaskName "CarDB-Sync" -Action $action -Trigger $trigger -Description "car-db 최신본 자동 다운로드" -Force | Out-Null
Write-Host "완료: 매일 $Time 에 $Target 을 자동 갱신합니다. 즉시 한 번 실행: Start-ScheduledTask -TaskName CarDB-Sync"
Write-Host "AI에게는 $Target\dist\car_db_for_ai.md 를 읽게 하세요."
