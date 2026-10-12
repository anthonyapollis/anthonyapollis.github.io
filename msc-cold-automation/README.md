# MSC Cold automation

This folder contains the portable Python processor used for MSC Cold batches.
It does not upload files to WinSCP or CapeFive.

## Requirements

- Python 3.9 or newer
- 7-Zip for extracting `.7z` attachments

The processor itself uses only the Python standard library.

## Batch procedure

1. Download the latest MSC Cold `.7z` attachment.
2. Confirm that the batch has not already been processed.
3. Create a batch folder containing `IN` and `OUT` folders.
4. Extract the attachment and copy its files into `IN`.
5. Select the next two-letter suffix. Never use a suffix ending in `Z`.
6. Check whether different input filenames will map to the same output name.
7. Run the processor.
8. Verify the input count, output count, and skipped-file count.
9. Zip the contents of `OUT` for return by email.

Example folder structure:

```text
Batch_31_02102026_AW/
  IN/
  OUT/
```

Run the processor from PowerShell:

```powershell
python .\process_msc_cold_batch.py "C:\Path\To\Batch_31_02102026_AW" --suffix AW
```

## What the processor changes

- It replaces the last two characters of each filename extension with the
  supplied suffix.
- From line 7 onward, lines with at least 219 characters have character
  positions 215 through 219 replaced with `00:00`.
- Cleaned files are written to `OUT` using UTF-8 and LF line endings.
- A suffix ending in `Z` is rejected.

If `OUT` contains fewer files than `IN`, multiple inputs produced the same
output filename. Report those collision groups; the later file processed for a
name overwrites the earlier one.

## Prompt for another Codex installation

Open this repository on the other PC and use this prompt:

```text
Run the latest MSC Cold batch using msc-cold-automation/README.md and
process_msc_cold_batch.py. Find the latest MSC Cold archive in Downloads,
avoid reprocessing an existing batch, use the next suffix, never use a suffix
ending in Z, check filename collisions before processing, create and verify a
cleaned ZIP, and do not upload anything to WinSCP or CapeFive.
```

Do not commit source attachments, extracted batch files, cleaned outputs,
credentials, or connection details to GitHub.
