<#
  TD2 Loot Advisor Companion — local/mobile release preflight.

  This script never uploads an APK/AAB, signs a Play submission, changes
  Firebase, or reads the contents of google-services.json. It provides a
  repeatable local check before a user performs a real-device test.
#>
[CmdletBinding()]
param(
    [switch]$BuildAab,
    [switch]$RequireDevice,
    [switch]$RequireFirebaseConfig
)

$ErrorActionPreference = 'Stop'
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$root = Split-Path -Parent $PSScriptRoot
$mobile = Join-Path $root 'mobile'
$flutterCandidates = @(
    (Get-Command flutter -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue),
    (Join-Path $env:USERPROFILE 'tools\flutter\bin\flutter.bat'),
    'C:\flutter\bin\flutter.bat',
    'C:\src\flutter\bin\flutter.bat'
) | Where-Object { $_ -and (Test-Path $_) }
$flutter = $flutterCandidates | Select-Object -First 1
if (-not $flutter) { throw 'Flutter bulunamadı. flutter komutunu PATH''e ekleyin veya C:\Users\PC\tools\flutter kurulumunu doğrulayın.' }

function Invoke-Flutter([string[]]$Arguments) {
    & $flutter @Arguments
    if ($LASTEXITCODE -ne 0) { throw "flutter $($Arguments -join ' ') başarısız oldu" }
}

Write-Host 'TD2 Companion local preflight'
Write-Host "Flutter: $flutter"
Push-Location $mobile
try {
    Invoke-Flutter @('pub', 'get')
    Invoke-Flutter @('analyze')
    Invoke-Flutter @('test')

    $config = Join-Path $mobile 'android\app\google-services.json'
    $hasConfig = Test-Path $config
    Write-Host ("Firebase config: " + $(if ($hasConfig) { 'local file present (contents not read)' } else { 'not present' }))
    if ($RequireFirebaseConfig -and -not $hasConfig) {
        throw 'Firebase yapılandırması isteniyor ama google-services.json bulunamadı.'
    }
    if ($hasConfig) {
        git -C $root check-ignore -q -- mobile/android/app/google-services.json
        if ($LASTEXITCODE -ne 0) { throw 'google-services.json Git tarafından yok sayılmıyor; devam etmek güvenli değil.' }
        Write-Host 'Firebase config Git tarafından yok sayılıyor.'
    }

    $adbCandidates = @(
        (Get-Command adb -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue),
        (Join-Path $env:USERPROFILE 'tools\android-sdk\platform-tools\adb.exe'),
        (Join-Path $env:LOCALAPPDATA 'Android\Sdk\platform-tools\adb.exe')
    ) | Where-Object { $_ -and (Test-Path $_) }
    $adb = $adbCandidates | Select-Object -First 1
    $online = @()
    if ($adb) {
        $raw = & $adb devices
        $online = @($raw | Where-Object { $_ -match "`tdevice$" })
        Write-Host ("Connected Android devices: " + $online.Count)
    } else {
        Write-Warning 'adb bulunamadı; cihaz testi atlandı.'
    }
    if ($RequireDevice -and $online.Count -lt 1) { throw 'Gerçek Android cihaz bağlı değil.' }

    if ($BuildAab) {
        Invoke-Flutter @('build', 'appbundle', '--release')
        $aab = Join-Path $mobile 'build\app\outputs\bundle\release\app-release.aab'
        if (-not (Test-Path $aab)) { throw 'Release AAB oluşturulmadı.' }
        $item = Get-Item $aab
        Write-Host "Release AAB: $($item.FullName) ($($item.Length) bytes)"
    }
} finally {
    Pop-Location
}

Write-Host 'Preflight PASS. This result does not authorize store upload or release.'
