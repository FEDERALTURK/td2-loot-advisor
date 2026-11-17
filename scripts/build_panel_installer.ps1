$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$version = "1.0.0"
$python = (Get-Command python).Source

Write-Host "[1/4] Panel Python syntax kontrolü"
& $python -m py_compile td2_panel.py

Write-Host "[2/4] PyInstaller onedir build"
if (Test-Path dist\TD2LootAdvisorPanel) { Remove-Item dist\TD2LootAdvisorPanel -Recurse -Force }
& $python -m PyInstaller --noconfirm --clean --onedir --noconsole --name TD2LootAdvisorPanel --icon icon\td2.ico td2_panel.py
if (-not (Test-Path dist\TD2LootAdvisorPanel\TD2LootAdvisorPanel.exe)) { throw "Panel EXE oluşturulamadı" }

Write-Host "[3/4] EXE smoke test"
$p = Start-Process -FilePath (Join-Path $root "dist\TD2LootAdvisorPanel\TD2LootAdvisorPanel.exe") -PassThru
Start-Sleep -Seconds 3
if ($p.HasExited) { throw "Panel EXE açılışta kapandı (exit $($p.ExitCode))" }
$p.CloseMainWindow() | Out-Null
$p.WaitForExit(3000)
if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force }

Write-Host "[4/4] Inno Setup installer"
$iscc = @(
  "$env:ProgramFiles(x86)\Inno Setup 6\ISCC.exe",
  "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
  "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) { Write-Warning "Inno Setup bulunamadı; dist EXE hazır, installer atlandı."; exit 2 }
if (-not (Test-Path installer)) { New-Item installer -ItemType Directory | Out-Null }
& $iscc "/Q" "/DAppVersion=$version" scripts\panel_installer.iss
if (-not (Test-Path "installer\TD2LootAdvisorPanel_Setup_$version.exe")) { throw "Installer oluşturulamadı" }
Write-Host "Tamamlandı: installer\TD2LootAdvisorPanel_Setup_$version.exe"
