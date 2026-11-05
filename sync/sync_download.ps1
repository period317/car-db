# git 이 없는 PC용: GitHub 에서 ZIP 으로 최신 car_db_for_ai.md 만 내려받기 (공개 저장소 전용)
# 비공개 저장소는 토큰이 필요하므로 git clone 방식(setup_other_pc.ps1)을 권장.
# 사용 예: powershell -ExecutionPolicy Bypass -File sync_download.ps1 -Owner <계정> -Repo car-db -Target C:\car-db-latest
param(
    [Parameter(Mandatory = $true)][string]$Owner,
    [Parameter(Mandatory = $true)][string]$Repo,
    [string]$Branch = "main",
    [string]$Target = "$env:USERPROFILE\car-db-latest"
)
$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path $Target | Out-Null
$zip = Join-Path $env:TEMP "car-db-latest.zip"
$tmp = Join-Path $env:TEMP "car-db-latest-extract"
Invoke-WebRequest -Uri "https://github.com/$Owner/$Repo/archive/refs/heads/$Branch.zip" -OutFile $zip
if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
Expand-Archive -Path $zip -DestinationPath $tmp -Force
$src = Get-ChildItem $tmp -Directory | Select-Object -First 1
Copy-Item (Join-Path $src.FullName "dist\car_db_for_ai.md") $Target -Force
Copy-Item (Join-Path $src.FullName "data\unified\offers.csv") $Target -Force
Copy-Item (Join-Path $src.FullName "data\unified\testdrive.csv") $Target -Force
Write-Host "갱신 완료: $Target (car_db_for_ai.md, offers.csv, testdrive.csv)"
