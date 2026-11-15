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

    @"
storeFile=$keystore
storePassword=$storePassword
keyAlias=td2-companion-beta
keyPassword=$keyPassword
"@ | Set-Content -LiteralPath $properties -Encoding utf8

    Push-Location $mobileRoot
    try {
        & $flutter build apk --release -PplayRelease=true
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
