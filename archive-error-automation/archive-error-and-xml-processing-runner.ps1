param(
    [datetime]$RunDate = (Get-Date)
)

$fullRunner = Join-Path $PSScriptRoot 'archive-error-and-xml-processing-full.ps1'
& $fullRunner -RunDate $RunDate
