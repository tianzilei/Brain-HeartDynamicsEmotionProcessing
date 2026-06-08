# Session_01.ps1 — Install font, patch, and run Session_01
$psychopyPython = "C:\Program Files\PsychoPy\python.exe"
$fontSource = Join-Path $PSScriptRoot "Noto Sans SC.truetype"
$fontTargetDir = "$env:APPDATA\psychopy3\fonts"
$targetFile = "Session_01_lastrun.py"
$utf8NoBom = New-Object System.Text.UTF8Encoding $false

# ---- Install Font ----
$fontTarget = Join-Path $fontTargetDir "Noto Sans SC.truetype"

if (Test-Path $fontTarget) {
    Write-Host "[OK] Font already installed: Noto Sans SC.truetype"
} elseif (Test-Path $fontSource) {
    if (-not (Test-Path $fontTargetDir)) {
        New-Item -ItemType Directory -Path $fontTargetDir -Force | Out-Null
        Write-Host "Created: $fontTargetDir"
    }
    Copy-Item -Path $fontSource -Destination $fontTargetDir
    Write-Host "[OK] Installed: Noto Sans SC.truetype -> $fontTargetDir"
} else {
    Write-Host "[!] Font file not found: $fontSource"
}

# ---- Patch ----
$filePath = Join-Path $PSScriptRoot $targetFile

if (Test-Path $filePath) {
    $content = Get-Content -Path $filePath -Raw -Encoding UTF8
    $injection = "import datetime`r`ndate_str = datetime.datetime.now().strftime('%Y%m%d')`r`n"
    $pattern = '(# information about this experiment\r?\n\s*)'

    if ($content -match $pattern) {
        $newContent = $content -replace $pattern, "`${1}$injection"
        if ($newContent -ne $content) {
            [System.IO.File]::WriteAllText($filePath, $newContent, $utf8NoBom)
            Write-Host "[OK] Patched $targetFile"
        }
} else {
    Write-Host "[!] Already patched: $targetFile"
}
} else {
    Write-Host "[!] $targetFile not found."
    exit 1
}

# ---- Fix Common Bugs ----
& {
    $content = Get-Content -Path $filePath -Raw -Encoding UTF8
    
    # Step 1: Fix 0bN syntax errors (0b2, 0b3, etc.)
    $fixed = $content -replace '\b0b(\d+)\b', '$1'
    
    # Step 2: Fix sendMessage(N) runtime errors -> sendMessage(bytes(chr(N), 'utf-8'))
    $fixed = $fixed -replace '\.sendMessage\((\d+)\)', '.sendMessage(bytes(chr($1), ''utf-8''))'
    
    if ($fixed -ne $content) {
        [System.IO.File]::WriteAllText($filePath, $fixed, $utf8NoBom)
        Write-Host "[OK] Fixed common bugs in $targetFile"
    } else {
        Write-Host "[OK] No bugs found in $targetFile"
    }
}

# ---- Check COM Port ----
# Win32 MessageBox via P/Invoke - no COM/Forms dependency
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public class WinMsg {
    [DllImport("user32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    public static extern int MessageBoxW(IntPtr hWnd, string text, string caption, uint type);
    public static int Error(string text, string caption)   { return MessageBoxW(IntPtr.Zero, text, caption, 0x1010); }
    public static int Warn(string text, string caption)    { return MessageBoxW(IntPtr.Zero, text, caption, 0x1030); }
}
'@

# Step 1: Read configured COM port from lastrun.py
$content = Get-Content -Path $filePath -Raw -Encoding UTF8
$configuredPort = if ($content -match "port='(COM\d+)'") { $Matches[1] } else { $null }

# Step 2: Get available COM ports on this system
$comPorts = [System.IO.Ports.SerialPort]::GetPortNames()

# Step 3: Validate
if ($comPorts.Count -eq 0) {
    $null = [WinMsg]::Error("No COM port detected! Please connect the serial device and try again.", "Hardware Error")
    exit 2
}

if ($configuredPort -and $configuredPort -notin $comPorts) {
    $null = [WinMsg]::Warn("Configured port ${configuredPort} not found!`nAvailable ports: $($comPorts -join ', ')`nPlease update the PsychoPy experiment (.psyexp) serial port setting and re-export.", "Port Mismatch")
    exit 3
}

Write-Host "[OK] COM port: $configuredPort (available: $($comPorts -join ', '))"

# ---- Run ----
Write-Host "--- Running $targetFile ---"
& $psychopyPython $filePath 2>&1
