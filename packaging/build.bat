@echo off
setlocal EnableDelayedExpansion
::
:: Proteus Windows build script
::
:: Usage:
::   packaging\build.bat             -- full build (venv + tests + PyInstaller)
::   packaging\build.bat --skip-tests -- skip pytest step
::

set "PROJECT_DIR=%~dp0.."
cd /d "%PROJECT_DIR%"

echo === Proteus Build Script (Windows) ===
echo.

:: ---- Parse args ----
set "SKIP_TESTS=0"
for %%A in (%*) do (
    if /I "%%A"=="--skip-tests" set "SKIP_TESTS=1"
)

:: ---- Check Python ----
where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: python not found. Install Python 3.10+ and add it to PATH.
    exit /b 1
)
for /f "tokens=*" %%V in ('python --version 2^>^&1') do echo Using %%V

:: ---- Create venv if needed ----
if not exist ".venv\" (
    echo.
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 ( echo ERROR: Failed to create venv. & exit /b 1 )
)
set "PYTHON=.venv\Scripts\python.exe"
set "PIP=.venv\Scripts\pip.exe"

:: ---- Install dependencies ----
echo.
echo Installing dependencies...
"%PYTHON%" -m pip install --upgrade pip --quiet
"%PYTHON%" -m pip install -e ".[dev]" --quiet
if errorlevel 1 ( echo ERROR: pip install failed. & exit /b 1 )

:: ---- Run tests ----
if "%SKIP_TESTS%"=="0" (
    echo.
    echo Running tests...
    "%PYTHON%" -m pytest tests/ -v
    if errorlevel 1 ( echo ERROR: Tests failed. Aborting build. & exit /b 1 )
) else (
    echo.
    echo Skipping tests.
)

:: ---- Run PyInstaller ----
echo.
echo Building Proteus...
"%PYTHON%" -m PyInstaller --clean --noconfirm packaging\Proteus.spec
if errorlevel 1 ( echo ERROR: PyInstaller build failed. & exit /b 1 )

:: ---- Archive ----
echo.
echo Archiving...
set "ARCHIVE=Proteus-windows.zip"
if exist "%ARCHIVE%" del "%ARCHIVE%"
powershell -NoProfile -Command ^
    "Compress-Archive -Path 'dist\Proteus' -DestinationPath '%ARCHIVE%'"
if errorlevel 1 (
    echo WARNING: Archive step failed. The dist\Proteus\ folder is still usable.
) else (
    echo Archive: %ARCHIVE%
)

:: ---- Report ----
echo.
echo === Build complete ===
if exist "dist\Proteus\Proteus.exe" (
    echo Output: dist\Proteus\Proteus.exe
) else (
    echo Output directory: dist\
)
