param(
    [datetime]$RunDate = (Get-Date)
)

$runner = Join-Path $PSScriptRoot 'archive-error-and-xml-processing-runner.ps1'
& 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe' -ExecutionPolicy Bypass -File $runner -RunDate $RunDate
exit $LASTEXITCODE
