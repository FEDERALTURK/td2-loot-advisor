param(
    [Parameter(Mandatory=$true)][string]$ScriptPath,
    [Parameter(Mandatory=$true)][string]$OutputFolder
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$segments = Get-Content -LiteralPath $ScriptPath -Raw -Encoding UTF8 | ConvertFrom-Json
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.SelectVoice('Microsoft Tolga')
$synth.Rate = -1
$synth.Volume = 100
for ($i = 0; $i -lt $segments.Count; $i++) {
    $path = Join-Path $OutputFolder ('voice-{0:D2}.wav' -f ($i + 1))
    $synth.SetOutputToWaveFile($path)
    $synth.Speak($segments[$i].body)
    $synth.SetOutputToNull()
}
$synth.Dispose()
