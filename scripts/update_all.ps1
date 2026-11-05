# 이 PC(수집 PC)에서 실행: 통합본 재생성 -> 변경 있으면 커밋 -> GitHub 푸시
# 사용: powershell -ExecutionPolicy Bypass -File scripts\update_all.ps1 [-NoPush]
param([switch]$NoPush)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

python -I scripts/build_db.py
python -I scripts/export_bundle.py

git add -A
$changes = git status --porcelain
if (-not $changes) { Write-Host "변경 없음. 커밋/푸시 생략."; exit 0 }

$msg = "data refresh " + (Get-Date -Format "yyyy-MM-dd HH:mm")
git commit -m $msg | Out-Host
if (-not $NoPush) {
    $remote = git remote
    if ($remote) { git push | Out-Host } else { Write-Host "원격 저장소 없음: push 생략" }
}
