@echo off
echo =========================================
echo Bilibili Audio Extractor - Build Script
echo =========================================
echo.

echo Checking Python...
python --version
if errorlevel 1 (
    echo [ERROR] Python is not installed
    echo Please install Python 3.7 or higher
    pause
    exit /b 1
)

echo [OK] Python is installed

echo.
echo Checking PyInstaller...
python -c "import PyInstaller"
if errorlevel 1 (
    echo [WARNING] PyInstaller not found, installing...
    pip install pyinstaller
    if errorlevel 1 (
        echo [ERROR] Failed to install PyInstaller
        pause
        exit /b 1
    )
)

echo [OK] PyInstaller is ready

echo.
echo Checking you-get...
python -c "import you_get"
if errorlevel 1 (
    echo [WARNING] you-get not found, installing...
    pip install you-get
    if errorlevel 1 (
        echo [ERROR] Failed to install you-get
        pause
        exit /b 1
    )
)

echo [OK] you-get is ready

echo.
echo =========================================
echo Starting build process...
echo =========================================
echo.

python build_package.py
if errorlevel 1 (
    echo.
    echo [ERROR] Build failed
    pause
    exit /b 1
)

echo.
echo =========================================
echo Build completed!
echo =========================================
echo.

if exist "output" (
    echo Output files in output directory:
    dir /b "output"
    echo.
    echo To use:
    echo 1. Extract ZIP file
    echo 2. Run "启动程序.bat"
    echo 3. Download FFmpeg from: https://www.gyan.dev/ffmpeg/builds/
)

pause