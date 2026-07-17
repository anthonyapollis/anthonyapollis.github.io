param(
    [datetime]$RunDate = (Get-Date)
)

$ErrorActionPreference = 'Stop'

$ArchiveRoot = 'C:\Users\Marble Mpofu\Documents\Codex\archive-error-working'
$ArchiveErrors = Join-Path $ArchiveRoot 'Archive_errors'
$CleanedFiles = Join-Path $ArchiveRoot 'Cleaned_Files'
$RunId = [guid]::NewGuid().ToString('N')
$Stage = Join-Path $env:TEMP ("archive-error-stage-$RunId")
$StageXml = Join-Path $env:TEMP ("archive-error-xml-stage-$RunId")
$Wscp = 'C:\Program Files (x86)\WinSCP\WinSCP.com'
$SessionName = 'agrihub@20.87.214.198'
$RemoteIn = '/home/ftp/CapeFive/in/'
$RemoteErrorXml = '/home/agrihub/live/archive/error_xml'
$PendingCentralXmlDeletes = Join-Path $ArchiveRoot 'pending-central-error-xml-deletions.jsonl'
$DesktopNotebook = 'C:\Users\Marble Mpofu\Desktop\Archive error\Archive Errors _ Code.ipynb'
$Notebook = Join-Path $ArchiveRoot 'Archive Errors _ Code.ipynb'
$Python = 'C:\Users\Marble Mpofu\Anaconda\python.exe'

function Get-TargetDates {
    param([datetime]$Date)
    @($Date.Date, $Date.Date.AddDays(-1), $Date.Date.AddDays(-2)) | Select-Object -Unique
}

function Get-ProbeDates {
    param([datetime[]]$Dates)
    $allDates = foreach ($date in $Dates) {
        foreach ($offset in 0, 1, 2) {
            $date.Date.AddDays(-$offset)
        }
    }
    $allDates | Select-Object -Unique
}

function Ensure-Dir {
    param([string]$Path)
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
}

function Clear-FilesOnly {
    param([string]$Path)
    Ensure-Dir $Path
    Get-ChildItem -LiteralPath $Path -File -ErrorAction SilentlyContinue | Remove-Item -Force
    Get-ChildItem -LiteralPath $Path -Directory -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
}

function Quote-WinScp {
    param([string]$Value)
    '"' + ($Value -replace '"', '""') + '"'
}

function Invoke-WinScp {
    param(
        [string[]]$Commands,
        [switch]$ContinueOnError
    )

    $scriptPath = Join-Path $env:TEMP ("archive-error-winscp-{0}.txt" -f ([guid]::NewGuid().ToString('N')))
    Set-Content -LiteralPath $scriptPath -Value $Commands -Encoding ASCII
    try {
        $output = @(& $Wscp "/script=$scriptPath" 2>&1 | ForEach-Object { $_.ToString() })
        $exitCode = $LASTEXITCODE
        if ($exitCode -ne 0 -and -not $ContinueOnError) {
            throw (($output | Select-Object -Last 30) -join [Environment]::NewLine)
        }
        $output
    }
    finally {
        Remove-Item -LiteralPath $scriptPath -Force -ErrorAction SilentlyContinue
    }
}

function Get-WinScpNames {
    param([string[]]$Lines)

    foreach ($line in $Lines) {
        if ($line -match '^-[-rwx]{9}\s+\d+\s+\S+\s+\S+\s+\d+\s+\S+\s+\d+\s+\S+\s+\d{4}\s+(.+)$') {
            $Matches[1]
        }
    }
}

function Get-RemoteNames {
    param(
        [string]$RemoteDir,
        [string]$Mask = '*'
    )

    $commands = @(
        'option batch abort',
        'option confirm off',
        ('open {0}' -f (Quote-WinScp $SessionName)),
        ('cd {0}' -f (Quote-WinScp $RemoteDir)),
        ('ls {0}' -f $Mask),
        'exit'
    )
    $output = @(Invoke-WinScp -Commands $commands -ContinueOnError)
    if ($output -match 'Cannot get real path|No such file or directory|Error code: 2') {
        return @()
    }
    Get-WinScpNames -Lines $output
}

function Test-RemoteDirExists {
    param([string]$RemoteDir)

    $commands = @(
        'option batch abort',
        'option confirm off',
        ('open {0}' -f (Quote-WinScp $SessionName)),
        ('cd {0}' -f (Quote-WinScp $RemoteDir)),
        'pwd',
        'exit'
    )
    $output = @(Invoke-WinScp -Commands $commands -ContinueOnError)
    -not ($output -match 'Cannot get real path|No such file or directory|Error code: 2')
}

function Read-PendingCentralXmlDeletes {
    if (-not (Test-Path -LiteralPath $PendingCentralXmlDeletes)) { return @() }

    $records = @()
    foreach ($line in @(Get-Content -LiteralPath $PendingCentralXmlDeletes -ErrorAction SilentlyContinue)) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        try {
            $record = $line | ConvertFrom-Json
            if ($record.RemotePath -and $record.XmlName -and $record.Clean -and $record.DeleteAfter) {
                $records += $record
            }
        }
        catch {
            # Keep moving if one pending line is malformed; the run summary will still show remaining work.
        }
    }
    $records
}

function Write-PendingCentralXmlDeletes {
    param([object[]]$Records)

    Ensure-Dir (Split-Path -Parent $PendingCentralXmlDeletes)
    if (@($Records).Count -eq 0) {
        Remove-Item -LiteralPath $PendingCentralXmlDeletes -Force -ErrorAction SilentlyContinue
        return
    }

    $lines = foreach ($record in $Records) {
        $record | ConvertTo-Json -Compress
    }
    Set-Content -LiteralPath $PendingCentralXmlDeletes -Value $lines -Encoding ASCII
}

function Add-PendingCentralXmlDeletes {
    param(
        [System.IO.FileInfo[]]$MatchedXmlFiles,
        [hashtable]$SourceByClean,
        [datetime]$Date
    )

    $records = @(Read-PendingCentralXmlDeletes)
    $known = @{}
    foreach ($record in $records) {
        $known[[string]$record.RemotePath] = $true
    }

    $added = 0
    foreach ($xml in @($MatchedXmlFiles)) {
        $clean = $xml.Name -replace '\.error\.xml$', ''
        if (-not $SourceByClean.ContainsKey($clean)) { continue }

        $remotePath = [string]$SourceByClean[$clean]
        if ($remotePath -notlike "$RemoteErrorXml/*") { continue }
        if ($known.ContainsKey($remotePath)) { continue }

        $records += [pscustomobject]@{
            RecordedAt = (Get-Date).ToString('s')
            RunDate = $Date.Date.ToString('yyyy-MM-dd')
            DeleteAfter = $Date.Date.AddDays(1).ToString('yyyy-MM-dd')
            XmlName = $xml.Name
            Clean = $clean
            RemotePath = $remotePath
        }
        $known[$remotePath] = $true
        $added++
    }

    Write-PendingCentralXmlDeletes -Records $records
    $added
}

function Invoke-DueCentralXmlCleanup {
    param(
        [hashtable]$ProcessedByName,
        [datetime]$Date
    )

    $records = @(Read-PendingCentralXmlDeletes)
    if ($records.Count -eq 0) {
        return [pscustomobject]@{ Checked = 0; Deleted = 0; Failures = 0; Remaining = 0 }
    }

    $keep = @()
    $due = @()
    foreach ($record in $records) {
        try {
            $deleteAfter = [datetime]$record.DeleteAfter
        }
        catch {
            $keep += $record
            continue
        }

        if ($deleteAfter.Date -le $Date.Date) {
            $due += $record
        }
        else {
            $keep += $record
        }
    }

    $checked = 0
    $deleted = 0
    $failureCount = 0
    $safeToDelete = @()
    foreach ($record in $due) {
        $clean = [string]$record.Clean
        if ($ProcessedByName.ContainsKey($clean)) {
            $safeToDelete += $record
            $checked++
        }
        else {
            $keep += $record
        }
    }

    if ($safeToDelete.Count -gt 0) {
        $commands = @(
            'option batch continue',
            'option confirm off',
            ('open {0}' -f (Quote-WinScp $SessionName))
        )
        foreach ($record in $safeToDelete) {
            $commands += ('rm {0}' -f (Quote-WinScp ([string]$record.RemotePath)))
        }
        $commands += 'exit'

        $deleteOutput = @(Invoke-WinScp -Commands $commands -ContinueOnError)
        $failureCount = @($deleteOutput | Where-Object { $_ -match 'Permission denied|Error deleting file|No such file or directory' }).Count

        $remainingNames = @(Get-RemoteNames -RemoteDir $RemoteErrorXml -Mask '*.error.xml')
        $remainingByName = @{}
        foreach ($name in $remainingNames) {
            $remainingByName[$name.ToLowerInvariant()] = $true
        }

        foreach ($record in $safeToDelete) {
            $xmlName = [string]$record.XmlName
            if (-not $remainingByName.ContainsKey($xmlName.ToLowerInvariant())) {
                $deleted++
            }
            else {
                $keep += $record
            }
        }
    }

    $uniqueKeep = @()
    $seen = @{}
    foreach ($record in $keep) {
        $key = [string]$record.RemotePath
        if ($seen.ContainsKey($key)) { continue }
        $seen[$key] = $true
        $uniqueKeep += $record
    }
    Write-PendingCentralXmlDeletes -Records $uniqueKeep

    [pscustomobject]@{
        Checked = $checked
        Deleted = $deleted
        Failures = $failureCount
        Remaining = $uniqueKeep.Count
    }
}

function Invoke-MatchedCentralXmlCleanup {
    param(
        [System.IO.FileInfo[]]$MatchedXmlFiles,
        [hashtable]$SourceByClean,
        [datetime]$Date
    )

    $targets = @()
    foreach ($xml in @($MatchedXmlFiles)) {
        $clean = $xml.Name -replace '\.error\.xml$', ''
        if (-not $SourceByClean.ContainsKey($clean)) { continue }

        $remotePath = [string]$SourceByClean[$clean]
        if ($remotePath -notlike "$RemoteErrorXml/*") { continue }

        $targets += [pscustomobject]@{
            Xml = $xml
            XmlName = $xml.Name
            Clean = $clean
            RemotePath = $remotePath
        }
    }

    if ($targets.Count -eq 0) {
        return [pscustomobject]@{ Checked = 0; Deleted = 0; Failures = 0; PendingAdded = 0 }
    }

    $commands = @(
        'option batch continue',
        'option confirm off',
        ('open {0}' -f (Quote-WinScp $SessionName))
    )
    foreach ($target in $targets) {
        $commands += ('rm {0}' -f (Quote-WinScp ([string]$target.RemotePath)))
    }
    $commands += 'exit'

    $deleteOutput = @(Invoke-WinScp -Commands $commands -ContinueOnError)
    $failureCount = @($deleteOutput | Where-Object { $_ -match 'Permission denied|Error deleting file' }).Count

    $remainingNames = @(Get-RemoteNames -RemoteDir $RemoteErrorXml -Mask '*.error.xml')
    $remainingByName = @{}
    foreach ($name in $remainingNames) {
        $remainingByName[$name.ToLowerInvariant()] = $true
    }

    $deleted = 0
    $stillPresent = @()
    foreach ($target in $targets) {
        if ($remainingByName.ContainsKey(([string]$target.XmlName).ToLowerInvariant())) {
            $stillPresent += $target.Xml
        }
        else {
            $deleted++
        }
    }

    $pendingAdded = 0
    if ($stillPresent.Count -gt 0) {
        $pendingAdded = Add-PendingCentralXmlDeletes -MatchedXmlFiles $stillPresent -SourceByClean $SourceByClean -Date $Date
    }

    [pscustomobject]@{
        Checked = $targets.Count
        Deleted = $deleted
        Failures = $failureCount
        PendingAdded = $pendingAdded
    }
}

function Copy-TopLevelFiles {
    param(
        [string]$Source,
        [string]$Destination
    )
    Clear-FilesOnly $Destination
    Get-ChildItem -LiteralPath $Source -File -ErrorAction SilentlyContinue | Copy-Item -Destination $Destination -Force
}

$targetDates = @(Get-TargetDates -Date $RunDate)
$probeDates = @(Get-ProbeDates -Dates $targetDates)

$summary = [ordered]@{
    Dates = ($targetDates | ForEach-Object { $_.ToString('yyyy-MM-dd') }) -join ','
    ProbeDates = ($probeDates | ForEach-Object { $_.ToString('yyyy-MM-dd') }) -join ','
    ZipCount = 0
    NonZipCount = 0
    ExtractedCount = 0
    ProcessedCandidates = 0
    SkippedMissingErrorFolders = 0
    XmlCopied = 0
    ProcessedCopied = 0
    UploadedCount = 0
    ImmediateCentralXmlChecked = 0
    PendingCentralXmlRecorded = 0
    DueCentralXmlChecked = 0
    DeletedCentralXml = 0
    CentralXmlDeleteFailures = 0
    CentralXmlPendingRemaining = 0
    ErrorFolderCleanupAfterUpload = $true
    DeletedErrorFolderFiles = 0
    ErrorFolderDeleteFailures = 0
    ErrorFolderCleanupRetries = 0
    RemainingErrorFolderFilesAfterCleanup = 0
    NotebookRan = $false
    NotebookExitCode = $null
    Failures = @()
}

try {
    Clear-FilesOnly $ArchiveErrors
    Clear-FilesOnly $CleanedFiles
    Clear-FilesOnly $Stage
    Clear-FilesOnly $StageXml

    $pullCommands = @(
        'option batch continue',
        'option confirm off',
        'option reconnecttime 300',
        ('open {0}' -f (Quote-WinScp $SessionName))
    )
    $existingErrorDirs = @()
    foreach ($date in $targetDates) {
        $ym = $date.ToString('yyyyMM')
        $dd = $date.ToString('dd')
        $remoteError = "/home/agrihub/live/archive/$ym/$dd/Error/"
        if (-not (Test-RemoteDirExists -RemoteDir $remoteError)) {
            $summary.SkippedMissingErrorFolders++
            continue
        }

        $existingErrorDirs += [pscustomobject]@{
            Date = $date
            RemoteError = $remoteError
        }
        $pullCommands += ('lcd {0}' -f (Quote-WinScp $ArchiveErrors))
        $pullCommands += ('cd {0}' -f (Quote-WinScp $remoteError))
        $pullCommands += 'get *.zip'
        $pullCommands += 'get *.ZIP'
        $pullCommands += ('lcd {0}' -f (Quote-WinScp $CleanedFiles))
        $pullCommands += 'get * -filemask=|*.zip;*.ZIP;*.error.xml;*.ERROR.XML'
    }
    $pullCommands += 'exit'
    $null = Invoke-WinScp -Commands $pullCommands

    $summary.ZipCount = @(Get-ChildItem -LiteralPath $ArchiveErrors -File -ErrorAction SilentlyContinue).Count
    $summary.NonZipCount = @(Get-ChildItem -LiteralPath $CleanedFiles -File -ErrorAction SilentlyContinue).Count

    foreach ($zip in @(Get-ChildItem -LiteralPath $ArchiveErrors -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -match '^\.(zip|ZIP)$' })) {
        Expand-Archive -LiteralPath $zip.FullName -DestinationPath $CleanedFiles -Force
        $summary.ExtractedCount++
    }

    $processedByName = @{}
    foreach ($date in $probeDates) {
        $ym = $date.ToString('yyyyMM')
        $dd = $date.ToString('dd')
        $remoteProcessed = "/home/agrihub/live/archive/$ym/$dd/Processed/"
        foreach ($name in @(Get-RemoteNames -RemoteDir $remoteProcessed)) {
            if (-not $processedByName.ContainsKey($name)) {
                $processedByName[$name] = "$remoteProcessed$name"
            }
        }
    }
    $summary.ProcessedCandidates = $processedByName.Count

    $dueCentralCleanup = Invoke-DueCentralXmlCleanup -ProcessedByName $processedByName -Date $RunDate
    $summary.DueCentralXmlChecked = $dueCentralCleanup.Checked
    $summary.DeletedCentralXml = $dueCentralCleanup.Deleted
    $summary.CentralXmlDeleteFailures = $dueCentralCleanup.Failures
    $summary.CentralXmlPendingRemaining = $dueCentralCleanup.Remaining
    if ($summary.CentralXmlDeleteFailures -gt 0) {
        $summary.Failures += "Central error_xml delayed cleanup reported $($summary.CentralXmlDeleteFailures) delete failure line(s)."
    }

    $xmlSourceByClean = @{}

    if ($processedByName.Count -gt 0) {
        $centralXmlNames = @(Get-RemoteNames -RemoteDir $RemoteErrorXml -Mask '*.error.xml')
        $xmlProbeCommands = @(
            'option batch continue',
            'option confirm off',
            ('open {0}' -f (Quote-WinScp $SessionName)),
            ('lcd {0}' -f (Quote-WinScp $StageXml))
        )
        foreach ($xmlName in $centralXmlNames) {
            $clean = $xmlName -replace '\.error\.xml$', ''
            if ($processedByName.ContainsKey($clean) -and -not $xmlSourceByClean.ContainsKey($clean)) {
                $xmlProbeCommands += ('get {0}' -f (Quote-WinScp "$RemoteErrorXml/$xmlName"))
                $xmlSourceByClean[$clean] = "$RemoteErrorXml/$xmlName"
            }
        }
        $xmlProbeCommands += 'exit'
        if ($xmlProbeCommands.Count -gt 5) {
            $null = Invoke-WinScp -Commands $xmlProbeCommands -ContinueOnError
        }
    }

    $matchedXml = @(Get-ChildItem -LiteralPath $StageXml -File -Filter '*.error.xml' -ErrorAction SilentlyContinue)
    foreach ($xml in $matchedXml) {
        $clean = $xml.Name -replace '\.error\.xml$', ''
        if (-not $xmlSourceByClean.ContainsKey($clean)) {
            $xmlSourceByClean[$clean] = "$RemoteErrorXml/$($xml.Name)"
        }
    }
    $summary.XmlCopied = $matchedXml.Count

    if ($matchedXml.Count -gt 0) {
        $processedCopyCommands = @(
            'option batch abort',
            'option confirm off',
            ('open {0}' -f (Quote-WinScp $SessionName)),
            ('lcd {0}' -f (Quote-WinScp $CleanedFiles))
        )
        foreach ($xml in $matchedXml) {
            $clean = $xml.Name -replace '\.error\.xml$', ''
            if ($processedByName.ContainsKey($clean)) {
                $processedCopyCommands += ('get {0}' -f (Quote-WinScp $processedByName[$clean]))
                $summary.ProcessedCopied++
            }
        }
        $processedCopyCommands += 'exit'
        $null = Invoke-WinScp -Commands $processedCopyCommands
    }

    $nonXmlExtracted = @(Get-ChildItem -LiteralPath $CleanedFiles -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -notmatch '\.error\.xml$' -and $_.Extension -ne '.xml' })
    if ($nonXmlExtracted.Count -gt 0) {
        if (-not (Test-Path $Python)) { throw "Python not found: $Python" }
        if (-not (Test-Path $Notebook) -and (Test-Path $DesktopNotebook)) {
            Copy-Item -LiteralPath $DesktopNotebook -Destination $Notebook -Force
        }
        if (-not (Test-Path $Notebook)) { throw "Notebook not found: $Notebook" }
        $summary.NotebookRan = $true
        $quotedNotebook = '"{0}"' -f $Notebook
        $env:TMP = $env:TEMP = (Join-Path $env:TEMP 'codex-jupyter-tmp')
        $env:JUPYTER_RUNTIME_DIR = (Join-Path $env:TEMP 'runtime')
        $env:JUPYTER_CONFIG_DIR = (Join-Path $env:TEMP 'config')
        $env:IPYTHONDIR = (Join-Path $env:TEMP 'ipython')
        New-Item -ItemType Directory -Force -Path $env:TEMP, $env:JUPYTER_RUNTIME_DIR, $env:JUPYTER_CONFIG_DIR, $env:IPYTHONDIR | Out-Null
        $process = Start-Process -FilePath $Python -ArgumentList @('-m','jupyter','nbconvert','--to','notebook','--execute','--inplace','--ExecutePreprocessor.kernel_name=python3',$quotedNotebook) -PassThru -Wait -NoNewWindow
        $summary.NotebookExitCode = $process.ExitCode
        if ($process.ExitCode -ne 0) { throw "Notebook execution failed with exit code $($process.ExitCode)" }
    }

    Copy-TopLevelFiles -Source $CleanedFiles -Destination $Stage
    $stageFiles = @(Get-ChildItem -LiteralPath $Stage -File -ErrorAction SilentlyContinue)
    if ($stageFiles.Count -gt 0) {
        $uploadCommands = @(
            'option batch abort',
            'option confirm off',
            'option reconnecttime 300',
            ('open {0}' -f (Quote-WinScp $SessionName)),
            ('lcd {0}' -f (Quote-WinScp $Stage)),
            ('cd {0}' -f (Quote-WinScp $RemoteIn)),
            'put *',
            'exit'
        )
        $null = Invoke-WinScp -Commands $uploadCommands
        $summary.UploadedCount = $stageFiles.Count
    }

    if ($stageFiles.Count -gt 0 -and $matchedXml.Count -gt 0) {
        $immediateCentralCleanup = Invoke-MatchedCentralXmlCleanup -MatchedXmlFiles $matchedXml -SourceByClean $xmlSourceByClean -Date $RunDate
        $summary.ImmediateCentralXmlChecked = $immediateCentralCleanup.Checked
        $summary.DeletedCentralXml += $immediateCentralCleanup.Deleted
        $summary.CentralXmlDeleteFailures += $immediateCentralCleanup.Failures
        $summary.PendingCentralXmlRecorded = $immediateCentralCleanup.PendingAdded
        $summary.CentralXmlPendingRemaining = @(Read-PendingCentralXmlDeletes).Count
        if ($immediateCentralCleanup.Failures -gt 0) {
            $summary.Failures += "Central error_xml immediate cleanup reported $($immediateCentralCleanup.Failures) delete failure line(s)."
        }
    }

    $deleteCommands = @(
        'option batch continue',
        'option confirm off',
        ('open {0}' -f (Quote-WinScp $SessionName))
    )
    $cleanupErrorDirs = @($existingErrorDirs)
    foreach ($errorDir in $cleanupErrorDirs) {
        $remoteError = $errorDir.RemoteError
        $summary.DeletedErrorFolderFiles += @(Get-RemoteNames -RemoteDir $remoteError -Mask '*').Count
        $deleteCommands += ('cd {0}' -f (Quote-WinScp $remoteError))
        $deleteCommands += 'rm *'
    }
    $deleteCommands += 'exit'
    $deleteOutput = @(Invoke-WinScp -Commands $deleteCommands -ContinueOnError)
    $summary.ErrorFolderDeleteFailures = @($deleteOutput | Where-Object { $_ -match 'Permission denied|Error deleting file' }).Count
    if ($summary.ErrorFolderDeleteFailures -gt 0) {
        $summary.Failures += "Remote Error folder cleanup reported $($summary.ErrorFolderDeleteFailures) delete failure line(s)."
    }

    $remainingByDir = @{}
    foreach ($errorDir in $cleanupErrorDirs) {
        $remoteError = $errorDir.RemoteError
        $remaining = @(Get-RemoteNames -RemoteDir $remoteError -Mask '*').Count
        $remainingByDir[$remoteError] = $remaining
        $summary.RemainingErrorFolderFilesAfterCleanup += $remaining
    }

    if ($summary.RemainingErrorFolderFilesAfterCleanup -gt 0) {
        $retryCommands = @(
            'option batch continue',
            'option confirm off',
            ('open {0}' -f (Quote-WinScp $SessionName))
        )
        foreach ($remoteError in @($remainingByDir.Keys | Where-Object { $remainingByDir[$_] -gt 0 })) {
            $retryCommands += ('cd {0}' -f (Quote-WinScp $remoteError))
            $retryCommands += 'rm *'
        }
        $retryCommands += 'exit'
        $summary.ErrorFolderCleanupRetries++
        $retryOutput = @(Invoke-WinScp -Commands $retryCommands -ContinueOnError)
        $summary.ErrorFolderDeleteFailures += @($retryOutput | Where-Object { $_ -match 'Permission denied|Error deleting file' }).Count

        $summary.RemainingErrorFolderFilesAfterCleanup = 0
        foreach ($errorDir in $cleanupErrorDirs) {
            $remoteError = $errorDir.RemoteError
            $summary.RemainingErrorFolderFilesAfterCleanup += @(Get-RemoteNames -RemoteDir $remoteError -Mask '*').Count
        }
    }

    if ($summary.RemainingErrorFolderFilesAfterCleanup -gt 0) {
        $summary.Failures += "Remote Error folder cleanup left $($summary.RemainingErrorFolderFilesAfterCleanup) file(s) after retry."
    }

    Clear-FilesOnly $ArchiveErrors
    Clear-FilesOnly $CleanedFiles
}
catch {
    $summary.Failures += $_.Exception.Message
    throw
}
finally {
    $summary | ConvertTo-Json -Compress
}
