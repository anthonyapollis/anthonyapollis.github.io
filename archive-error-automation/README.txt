ARCHIVE ERROR / XML AUTOMATION BACKUP

Main entry point:
  archive-error-and-xml-processing-runner.ps1

Included:
  - Full PowerShell workflow
  - Runner, launcher, and scheduled-task wrappers
  - Python/Jupyter processing notebook

Required software and configuration:
  - Windows PowerShell
  - WinSCP installed at C:\Program Files (x86)\WinSCP\WinSCP.com
  - WinSCP saved session named agrihub@20.87.214.198
  - Anaconda Python at C:\Users\Marble Mpofu\Anaconda\python.exe
  - Jupyter available in that Python environment

Normal manual run:
  powershell.exe -ExecutionPolicy Bypass -File .\archive-error-and-xml-processing-runner.ps1 -RunDate (Get-Date)

The scripts currently use:
  C:\Users\Marble Mpofu\Documents\Codex\archive-error-working

Deleting Codex chats does not delete this ZIP or these local files.
Keep another copy on an external drive or approved cloud storage for disaster recovery.
