@echo off

REM Bilibili Audio Extractor - Unified Build & Install Script
REM This script handles both dependency installation and package building

chcp 65001 > nul

echo ====================================================
echo B站音频提取器 - 统一安装与打包脚本
echo ====================================================
echo.

set "MODE=build"
if "%1"=="install" set "MODE=install"

if "%MODE%"=="install" (
    echo 模式: 仅安装依赖
) else (
    echo 模式: 完整打包（包含依赖安装）
)
echo.

REM 检查Python
echo 检查Python环境...
python --version > nul 2>&1
if errorlevel 1 (
    echo [错误] Python未安装或未添加到系统PATH
    echo 请先安装Python 3.7或更高版本
    pause
    exit /b 1
)

echo [成功] Python环境正常

echo.

REM 检查pip
echo 检查pip...
python -m pip --version > nul 2>&1
if errorlevel 1 (
    echo [错误] pip未安装
    echo 请确保pip已正确安装
    pause
    exit /b 1
)

echo [成功] pip可用

echo.

REM 更新pip
echo 更新pip...
python -m pip install --upgrade pip > nul 2>&1
if errorlevel 0 (
    echo [成功] pip更新完成
) else (
    echo [警告] pip更新失败，将继续使用当前版本
)

echo.

echo ====================================================

if "%MODE%"=="install" (
    echo 开始安装依赖...
    echo ====================================================
    echo.

    REM 仅安装模式
    cd /d "%~dp0" && python build_package.py install

    if errorlevel 1 (
        echo.
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )

    echo.
    echo ====================================================
    echo [成功] 依赖安装完成!
    echo ====================================================
    echo.
    echo 您现在可以运行B站音频提取器了:
    echo python gui_extractor_simple.py
    echo.
    echo 或者运行完整打包:
    echo build_package.bat
    echo.

) else (
    echo 开始完整打包流程...
    echo ====================================================
    echo.

    REM 检查PyInstaller
    echo 检查PyInstaller...
    python -c "import PyInstaller" > nul 2>&1
    if errorlevel 1 (
        echo [警告] PyInstaller未安装，正在安装...
        pip install pyinstaller > nul 2>&1
        if errorlevel 1 (
            echo [错误] PyInstaller安装失败
            pause
            exit /b 1
        )
        echo [成功] PyInstaller安装完成
    ) else (
        echo [成功] PyInstaller已安装
    )

    echo.
    echo 检查you-get...
    python -c "import you_get" > nul 2>&1
    if errorlevel 1 (
        echo [警告] you-get未安装，正在安装...
        pip install you-get > nul 2>&1
        if errorlevel 1 (
            echo [错误] you-get安装失败
            pause
            exit /b 1
        )
        echo [成功] you-get安装完成
    ) else (
        echo [成功] you-get已安装
    )

    echo.
    echo ====================================================
    echo 开始构建安装包（包含依赖安装）...
    echo ====================================================
    echo.

    REM 完整打包模式
    cd /d "%~dp0" && python build_package.py

    if errorlevel 1 (
        echo.
        echo [错误] 打包失败
        pause
        exit /b 1
    )
 
    echo.
    echo ====================================================
    echo [成功] 打包完成!
    echo ====================================================
    echo.

    if exist "output" (
        echo 输出文件:
        dir /b "output"
        echo.
        echo 使用方法:
        echo 1. 解压ZIP文件
        echo 2. 运行 "启动程序.bat"
        echo 3. 下载FFmpeg: https://www.gyan.dev/ffmpeg/builds/
        echo.
        echo 注意: 此安装包已包含qrcode库，支持本地二维码生成
    )
)

echo.
echo 按任意键退出...
pause > nul