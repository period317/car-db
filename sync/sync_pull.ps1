# 다른 PC(소비 PC)용: 저장소 최신본 자동 내려받기 (git pull)
# 이 파일은 저장소를 clone한 폴더 안의 sync\sync_pull.ps1 로 실행됩니다.
$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$log = Join-Path $root "sync.log"
$stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
try {
    $out = git pull --ff-only 2>&1 | Out-String
    Add-Content -Path $log -Value "[$stamp] $($out.Trim())"
} catch {
    Add-Content -Path $log -Value "[$stamp] 실패: $($_.Exception.Message)"
}
