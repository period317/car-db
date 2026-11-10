# 이 PC(수집 PC)에서 실행: 통합본 재생성 -> 변경 있으면 커밋 -> GitHub 푸시
# 사용: powershell -ExecutionPolicy Bypass -File scripts\update_all.ps1 [-NoPush]
param([switch]$NoPush)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Step($label, [string[]]$pyArgs) {
    python -I @pyArgs
    if ($LASTEXITCODE -ne 0) { Write-Host "[$label] 실패. 게시 중단."; exit 1 }
}

# 직전 게시본(커밋된 benefits.jsonl)을 변경 비교용으로 보관
$prevBen = Join-Path $env:TEMP "benefits_prev.jsonl"
git show HEAD:data/unified/benefits.jsonl 2>$null | Out-File -Encoding utf8 $prevBen

Step "원본 통합" @("scripts/build_db.py")
Step "혜택 정리" @("scripts/build_benefits.py")
Step "원문 대조" @("scripts/verify_evidence.py")
Step "이력 누적" @("scripts/update_history.py")      # 덮어쓰지 않고 새 항목·변경·종료만 data/history 에 덧붙임
Step "변경 비교" @("scripts/diff_benefits.py", $prevBen)
Step "AI용 파일" @("scripts/export_bundle.py")

# 수집 후 품질 점검: ERROR 가 있으면 게시하지 않는다 (docs/QUALITY_REPORT.md, VERIFY_CHECKLIST.md 참고)
python -I scripts/quality_check.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "품질 점검 실패(ERROR). 게시 중단. docs/QUALITY_REPORT.md 와 docs/VERIFY_CHECKLIST.md 를 확인하세요."
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
    # 수집 가이드 문서도 gist에 별도 파일로 올린다(car_db_for_ai.md 부록에도 같은 내용이 들어 있음)
    $gfiles = @(gh gist view $gist --files)
    # docs/ 문서 4개 + 누적 이력(csv). gist 에 이미 있으면 내용 교체(-f), 없으면 새 파일로 추가(--add)
    foreach ($f in @("docs/PROGRESS_SUMMARY.md", "docs/COLLECTION_GUIDE.md", "docs/SITE_GUIDE.md", "docs/HANDOFF.md", "docs/LESSONS.md", "data/history/benefits_history.csv", "data/unified/benefits.csv", "data/unified/benefits_purchase.csv", "data/unified/benefits_finance.csv", "data/unified/benefits_testdrive.csv")) {
        $name = Split-Path -Leaf $f
        if ($gfiles -contains $name) {
            gh gist edit $gist -f $name $f | Out-Host
        } else {
            gh gist edit $gist --add $f | Out-Host
        }
    }
}
