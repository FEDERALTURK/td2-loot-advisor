<#
  TD2 Loot Advisor Companion — Play Internal Testing preflight.

  No Play Console upload, account modification or secret disclosure occurs.
  The optional signed build uses only the owner's local upload key; passwords
  are never printed or written by this script.
#>
[CmdletBinding()]
param(
    [switch]$RequireDevice,
    [switch]$RequireUploadKey,
    [switch]$BuildSignedAab
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$mobile = Join-Path $root 'mobile'
$android = Join-Path $mobile 'android'
$keyProperties = Join-Path $android 'key.properties'
$keystore = Join-Path $android 'upload-keystore.jks'

function Assert-Ignored([string]$RelativePath) {
    git -C $root check-ignore -q -- $RelativePath
    if ($LASTEXITCODE -ne 0) {
        throw "$RelativePath Git tarafindan yok sayilmiyor; sirrinizin depoya girmesi riski nedeniyle durduruldu."
    }
}

Write-Host 'TD2 Companion Play Internal Testing preflight'

# Reuse the source and device checks. This does not build or sign anything by itself.
$baseArgs = @('-ExecutionPolicy', 'Bypass', '-File', (Join-Path $PSScriptRoot 'mobile_preflight.ps1'))
if ($RequireDevice) { $baseArgs += '-RequireDevice' }
& powershell @baseArgs
if ($LASTEXITCODE -ne 0) { throw 'Temel mobil on-kontrol basarisiz oldu.' }

$hasKeyProperties = Test-Path $keyProperties
$hasKeystore = Test-Path $keystore
Write-Host ("Upload key.properties: " + $(if ($hasKeyProperties) { 'local file present (contents not read)' } else { 'not present' }))
Write-Host ("Upload keystore: " + $(if ($hasKeystore) { 'local file present' } else { 'not present' }))
if ($hasKeyProperties) { Assert-Ignored 'mobile/android/key.properties' }
if ($hasKeystore) { Assert-Ignored 'mobile/android/upload-keystore.jks' }

if ($RequireUploadKey -and (-not $hasKeyProperties -or -not $hasKeystore)) {
    throw 'Imzali Play AAB icin yerel key.properties ve upload-keystore.jks gereklidir.'
}

if ($BuildSignedAab) {
    if (-not $hasKeyProperties -or -not $hasKeystore) {
        throw 'BuildSignedAab istendi ama upload key dosyalari bulunamadi.'
    }
    $flutter = Get-Command flutter -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue
    if (-not $flutter) { $flutter = Join-Path $env:USERPROFILE 'tools\flutter\bin\flutter.bat' }
    if (-not (Test-Path $flutter)) { throw 'Flutter bulunamadi.' }
    Push-Location $mobile
    try {
        & $flutter build appbundle --release --android-project-arg=playRelease=true
        if ($LASTEXITCODE -ne 0) { throw 'Imzali AAB derlemesi basarisiz oldu.' }
        $aab = Join-Path $mobile 'build\app\outputs\bundle\release\app-release.aab'
        if (-not (Test-Path $aab)) { throw 'Imzali AAB olusturulamadi.' }
        $item = Get-Item $aab
        Write-Host "Signed AAB ready: $($item.FullName) ($($item.Length) bytes)"
    } finally {
        Pop-Location
    }
}

Write-Host 'Play preflight PASS. This does not upload to Play Console or authorize a release.'
