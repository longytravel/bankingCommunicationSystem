# Lloyds Banking Communication System Launcher
param(
    [switch]$TestMode,
    [string]$TestLetter,
    [string]$TestLanguage,
    [switch]$MockMode,
    [switch]$ClearCache,
    [switch]$Help
)

if ($Help) {
    Write-Host ""
    Write-Host "Lloyds Banking Communication System - Launch Options" -ForegroundColor Green
    Write-Host "=================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Usage: .\run.ps1 [options]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Yellow
    Write-Host "  -TestMode       Run with only 5 customers for quick testing"
    Write-Host "  -MockMode       Skip all API calls (UI testing only)"
    Write-Host "  -ClearCache     Clear all cached data before running"
    Write-Host "  -TestLetter     Test with specific letter file"
    Write-Host "  -TestLanguage   Test with specific language"
    Write-Host "  -Help           Show this help message"
    Write-Host ""
    exit
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Lloyds Banking Communication System  " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path ".\venv")) {
    Write-Host "Virtual environment not found. Creating..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "Virtual environment created." -ForegroundColor Green
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Set environment variables for testing
if ($TestMode) {
    $env:QUICK_TEST_MODE = "true"
    $env:TEST_SAMPLE_SIZE = "5"
    Write-Host "Quick Test Mode: Processing 5 customers only" -ForegroundColor Yellow
}

if ($MockMode) {
    $env:USE_MOCK_DATA = "true"
    Write-Host "Mock Mode: No API calls will be made" -ForegroundColor Yellow
}

if ($ClearCache) {
    if (Test-Path ".\data\cache") {
        Remove-Item -Path ".\data\cache\*" -Force -Recurse
        Write-Host "Cache cleared" -ForegroundColor Green
    }
}

# Check dependencies
Write-Host "Checking dependencies..." -ForegroundColor Yellow
$pipList = pip list 2>$null
if ($pipList -notlike "*streamlit*") {
    Write-Host "Installing required packages..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

# Launch Streamlit
Write-Host ""
Write-Host "Launching application..." -ForegroundColor Green
Write-Host "Browser will open at http://localhost:8501" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

streamlit run src/main.py --server.port 8501 --browser.serverAddress localhost
