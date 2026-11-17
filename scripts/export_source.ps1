param(
    [string]$Output = (Join-Path (Get-Location) "..\TD2LootAdvisor-source-export.zip")
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$temp = Join-Path ([System.IO.Path]::GetTempPath()) ("td2-export-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $temp | Out-Null

$excludedPath = '(^|[\\/])(build|dist|cache|logs|models|node_modules|project_review|web_deploy|Claude outputs|private|brag-output-[^\\/]+)([\\/]|$)'
$excludedFile = '(^|[\\/])(.env($|\\.)|.*\\.(jks|keystore|bak)$|builds\.json$|stash\.json$|progress\.json$|tasks\.json$|sessions\.json$)'

# Export only Git-tracked source files. This avoids copying generated Flutter,
# Gradle, Node, cache and runtime trees that can be very large or change while
# the export is running.
$tracked = & git -C $root ls-files
if ($LASTEXITCODE -ne 0) { throw "git ls-files failed" }
foreach ($relative in $tracked) {
    if ($relative -match $excludedPath -or $relative -match $excludedFile) { continue }
    $source = Join-Path $root $relative
    $target = Join-Path $temp $relative
    $parent = Split-Path -Parent $target
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
    Copy-Item -LiteralPath $source -Destination $target -Force
}

# Include local developer templates created by this setup, never credentials.
foreach ($relative in @('.env.example', 'TD2 Loot Advisor.code-workspace', '.vscode\tasks.json', '.vscode\launch.json', 'scripts\export_source.ps1')) {
    $source = Join-Path $root $relative
    if (Test-Path -LiteralPath $source) {
        $target = Join-Path $temp $relative
        New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force | Out-Null
        Copy-Item -LiteralPath $source -Destination $target -Force
    }
}

$destination = [System.IO.Path]::GetFullPath($Output)
Compress-Archive -Path (Join-Path $temp "*") -DestinationPath $destination -CompressionLevel Optimal -Force
Remove-Item -LiteralPath $temp -Recurse -Force
Write-Output "Safe source export created: $destination"
