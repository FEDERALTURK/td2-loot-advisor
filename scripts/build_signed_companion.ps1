param(
    [string]$BuildName,
    [int]$BuildNumber = 0
)

$ErrorActionPreference = 'Stop'

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$mobileRoot = Join-Path $projectRoot 'mobile'
$androidRoot = Join-Path $mobileRoot 'android'
$keystore = Join-Path $projectRoot 'td2-companion-beta.jks'
$properties = Join-Path $androidRoot 'key.properties'
$flutter = 'C:\Users\PC\tools\flutter\bin\flutter.bat'

if (-not (Test-Path -LiteralPath $keystore)) {
    throw "Keystore bulunamadı: $keystore"
}
if (-not (Test-Path -LiteralPath $flutter)) {
    throw "Flutter bulunamadı: $flutter"
}

$secureStorePassword = Read-Host 'Keystore parolası' -AsSecureString
$secureKeyPassword = Read-Host 'Key parolası (aynıysa tekrar girin)' -AsSecureString
$storePtr = [IntPtr]::Zero
$keyPtr = [IntPtr]::Zero

try {
    $storePtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureStorePassword)
    $keyPtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKeyPassword)
    $storePassword = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($storePtr)
    $keyPassword = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($keyPtr)

    $keystoreForGradle = $keystore.Replace('\', '/')
    $propertiesText = @"
storeFile=$keystoreForGradle
storePassword=$storePassword
keyAlias=td2-companion-beta
keyPassword=$keyPassword
"@
    # Java Properties treats a UTF-8 BOM as part of the first key name.  Write
    # BOM-free UTF-8 so Gradle can read `storeFile` reliably on Windows.
    [System.IO.File]::WriteAllText($properties, $propertiesText, [System.Text.UTF8Encoding]::new($false))

    Push-Location $mobileRoot
    try {
        $buildArgs = @('build', 'apk', '--release', '-PplayRelease=true')
        if ($BuildName) { $buildArgs += @('--build-name', $BuildName) }
        if ($BuildNumber -gt 0) { $buildArgs += @('--build-number', [string]$BuildNumber) }
        & $flutter @buildArgs
        if ($LASTEXITCODE -ne 0) {
            throw "İmzalı Companion APK build başarısız oldu (exit $LASTEXITCODE)."
        }
    }
    finally {
        Pop-Location
    }
}
finally {
    Remove-Item -LiteralPath $properties -Force -ErrorAction SilentlyContinue
    if ($storePtr -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($storePtr)
    }
    if ($keyPtr -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($keyPtr)
    }
    Remove-Variable storePassword, keyPassword, secureStorePassword, secureKeyPassword -ErrorAction SilentlyContinue
}

Write-Host 'İmzalı APK yerel olarak üretildi; key.properties temizlendi.'
