<#
.SYNOPSIS
    Downloads CHB-MIT subjects chb01 and chb03 from PhysioNet.
.DESCRIPTION
    Uses wget if available, otherwise falls back to Invoke-WebRequest.
    Downloads EDF files + summary/annotation files for subjects 01 and 03 only.
    Saves to: data/raw/chbmit/
.NOTES
    CHB-MIT is Open Access - no login required.
    Base URL: https://physionet.org/files/chbmit/1.0.0/
    Full dataset is 42.6 GB; this script downloads only ~6-8 GB (chb01 + chb03).
#>

param(
    [string]$OutputDir = "data\raw\chbmit",
    [switch]$DryRun
)

$BASE_URL  = "https://physionet.org/files/chbmit/1.0.0"
$SUBJECTS  = @("chb01", "chb03")
$ROOT_META = @("RECORDS", "RECORDS-WITH-SEIZURES", "SUBJECT-INFO", "SHA256SUMS.txt")

# ── Ensure output directory exists ─────────────────────────────────────────────
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
Write-Host "`n=== CHB-MIT Download Script ===" -ForegroundColor Cyan
Write-Host "Output: $OutputDir" -ForegroundColor Cyan
if ($DryRun) { Write-Host "[DRY-RUN MODE - no files will be downloaded]" -ForegroundColor Yellow }

# ── Helper: Download a single file ─────────────────────────────────────────────
function Download-File {
    param([string]$Url, [string]$Destination)

    $dir = Split-Path $Destination -Parent
    New-Item -ItemType Directory -Force -Path $dir | Out-Null

    if (Test-Path $Destination) {
        Write-Host "  [SKIP] Already exists: $Destination" -ForegroundColor DarkGray
        return
    }

    if ($DryRun) {
        Write-Host "  [DRY]  Would download: $Url -> $Destination" -ForegroundColor DarkYellow
        return
    }

    Write-Host "  [DOWN] $Url" -ForegroundColor Green

    # Try wget first (WSL / GNU wget on Windows)
    $wgetPath = (Get-Command wget -ErrorAction SilentlyContinue)?.Source
    if ($wgetPath) {
        & wget -q -c -O $Destination $Url
    } else {
        # Fallback: PowerShell Invoke-WebRequest
        try {
            Invoke-WebRequest -Uri $Url -OutFile $Destination -UseBasicParsing
        } catch {
            Write-Host "  [ERR]  Failed: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

# ── Download root metadata files ───────────────────────────────────────────────
Write-Host "`n[1/3] Root metadata files..." -ForegroundColor Magenta
foreach ($meta in $ROOT_META) {
    $url  = "$BASE_URL/$meta"
    $dest = Join-Path $OutputDir $meta
    Download-File -Url $url -Destination $dest
}

# ── Fetch file index for each subject ─────────────────────────────────────────
Write-Host "`n[2/3] Fetching subject file lists from PhysioNet..." -ForegroundColor Magenta

foreach ($subject in $SUBJECTS) {
    Write-Host "`n  Subject: $subject" -ForegroundColor Cyan

    # Download summary/annotation file (contains seizure onset/offset times)
    $summaryUrl  = "$BASE_URL/$subject/$subject-summary.txt"
    $summaryDest = Join-Path $OutputDir "$subject\$subject-summary.txt"
    Download-File -Url $summaryUrl -Destination $summaryDest

    # Fetch the index page to get EDF file list
    $indexUrl = "$BASE_URL/$subject/"
    try {
        $response = Invoke-WebRequest -Uri $indexUrl -UseBasicParsing
        # Parse all .edf file links from the index
        $edfFiles = ($response.Links | Where-Object { $_.href -match '\.edf$' } | Select-Object -ExpandProperty href)

        if ($edfFiles.Count -eq 0) {
            # Fallback: try to extract from raw HTML
            $edfFiles = [regex]::Matches($response.Content, 'href="([^"]+\.edf)"') | ForEach-Object { $_.Groups[1].Value }
        }

        Write-Host "  Found $($edfFiles.Count) EDF files for $subject" -ForegroundColor DarkCyan

        foreach ($edf in $edfFiles) {
            # Ensure we only process the filename, not a full URL
            $fileName = $edf -replace '^.*/', ''
            $url      = "$BASE_URL/$subject/$fileName"
            $dest     = Join-Path $OutputDir "$subject\$fileName"
            Download-File -Url $url -Destination $dest
        }

        # Also download .seizure annotation files if present
        $seizureFiles = [regex]::Matches($response.Content, 'href="([^"]+\.seizure)"') | ForEach-Object { $_.Groups[1].Value }
        foreach ($sf in $seizureFiles) {
            $fileName = $sf -replace '^.*/', ''
            $url      = "$BASE_URL/$subject/$fileName"
            $dest     = Join-Path $OutputDir "$subject\$fileName"
            Download-File -Url $url -Destination $dest
        }

    } catch {
        Write-Host "  [ERR] Could not fetch index for $subject : $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "  Tip: Try running: wget -r -N -c -np --include='$subject/' $BASE_URL/" -ForegroundColor Yellow
    }
}

Write-Host "`n[3/3] Done!" -ForegroundColor Green
Write-Host "Files saved to: $OutputDir" -ForegroundColor Green
Write-Host "Next step: Run 'python scripts/preprocess.py --dataset chbmit'" -ForegroundColor Cyan
