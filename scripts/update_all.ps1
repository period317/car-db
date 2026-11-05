# 이 PC(수집 PC)에서 실행: 통합본 재생성 -> 변경 있으면 커밋 -> GitHub 푸시
# 사용: powershell -ExecutionPolicy Bypass -File scripts\update_all.ps1 [-NoPush]
param([switch]$NoPush)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

python -I scripts/build_db.py
python -I scripts/build_benefits.py
python -I scripts/export_bundle.py

# 수집 후 품질 점검: ERROR 가 있으면 게시하지 않는다 (docs/QUALITY_REPORT.md 참고)
python -I scripts/quality_check.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "품질 점검 실패(ERROR). 게시 중단. docs/QUALITY_REPORT.md 를 확인하세요."
    exit 1
}

git add -A
$changes = git status --porcelain
if (-not $changes) { Write-Host "변경 없음. 커밋/푸시 생략."; exit 0 }

$msg = "data refresh " + (Get-Date -Format "yyyy-MM-dd HH:mm")
git commit -m $msg | Out-Host
if (-not $NoPush) {
    $remote = git remote
    if ($remote) { git push | Out-Host } else { Write-Host "원격 저장소 없음: push 생략" }
    # 고정 링크용 gist 갱신 (같은 주소 유지)
    $gist = "aeef56510f90aceae6561d65f9a81335"
    gh gist edit $gist -f car_db_for_ai.md dist/car_db_for_ai.md | Out-Host
    gh gist edit $gist -f testdrive.json data/unified/testdrive.json | Out-Host
    gh gist edit $gist -f offers.jsonl data/unified/offers.jsonl | Out-Host
}
