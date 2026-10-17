# Project checks: tests, compilation, secrets, unwanted files, start.bat line endings.
# Messages are ASCII on purpose: PowerShell 5.1 reads BOM-less scripts in the ANSI codepage.
$root = 'C:\ZCPROJ'
$python = "$root\.venv\Scripts\python.exe"
$failed = @()

$files = Get-ChildItem $root -Recurse -File |
  Where-Object { $_.FullName -notmatch '\\(\.venv|__pycache__|\.pytest_cache|\.claude)\\' }

Write-Output '== pytest'
Push-Location "$root\backend"
& $python -m pytest -q
if ($LASTEXITCODE -ne 0) { $failed += 'pytest' }

Write-Output '== compile'
& $python -m compileall -q app tests
if ($LASTEXITCODE -ne 0) { $failed += 'compile' }
Pop-Location

Write-Output '== secrets'
$secret = 'sk-ant-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|ANTHROPIC_API_KEY\s*=\s*["'']?sk-ant-[A-Za-z0-9]'
$hits = $files | Select-String -Pattern $secret
if ($hits) { $hits | ForEach-Object { Write-Output "  $($_.Path):$($_.LineNumber)" }; $failed += 'secrets' }

Write-Output '== unwanted files'
$bad = $files | Where-Object { $_.Name -match '(^\.env$|\.db$|logo)' -or $_.Extension -in '.png', '.jpg', '.ico' }
if ($bad) { $bad | ForEach-Object { Write-Output "  $($_.FullName)" }; $failed += 'files' }
$brand = $files | Select-String -Pattern '0047BB|ingos' -List
if ($brand) { $brand | ForEach-Object { Write-Output "  brand trace: $($_.Path):$($_.LineNumber)" }; $failed += 'brand' }

Write-Output '== start.bat CRLF'
$text = [IO.File]::ReadAllText("$root\start.bat")
if (($text -split "`n").Count -ne ($text -split "`r`n").Count) { $failed += 'start.bat has LF line endings' }

if ($failed) { Write-Output "FAILED: $($failed -join ', ')"; exit 1 }
Write-Output 'OK: all checks passed'
