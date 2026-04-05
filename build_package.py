#!/usr/bin/env python3
"""
B站音频提取器 - 简易打包工具
"""

import os
import sys
import subprocess
import shutil
import json
import zipfile
from pathlib import Path

class PackageBuilder:
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.build_dir = self.project_dir / "build"
        self.output_dir = self.project_dir / "output"
        self.version = "2.1.0"
        self.app_name = "B站音频提取器"

    def check_dependencies(self):
        print("检查依赖...")
        try:
            import PyInstaller
            print("[OK] PyInstaller已安装")
        except ImportError:
            print("[ERROR] PyInstaller未安装")
            return False

        try:
            import you_get
            print("[OK] you-get已安装")
        except ImportError:
            print("[ERROR] you-get未安装")
            return False

        return True

    def create_exe(self):
        print("\n创建可执行文件...")
        self.build_dir.mkdir(exist_ok=True)

        cmd = [
            'pyinstaller',
            '--onefile',
            '--windowed',
            f'--name={self.app_name}',
            '--distpath', str(self.build_dir),
            '--workpath', str(self.build_dir / "temp"),
            'gui_extractor_enhanced.py'
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_dir)
            if result.returncode == 0:
                print("[OK] 可执行文件创建成功")
                return True
            else:
                print(f"[ERROR] 创建失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"[ERROR] 创建异常: {e}")
            return False

    def create_youget_bundle(self):
        print("\n创建you-get捆绑包...")
        youget_dir = self.build_dir / "you-get"
        youget_dir.mkdir(exist_ok=True)  # 创建输出目录

        try:
            import you_get
            youget_path = Path(you_get.__file__).parent  # 获取you-get安装路径

            for item in youget_path.rglob('*'):  # 遍历you-get所有文件
                if item.is_file():
                    relative_path = item.relative_to(youget_path)
                    target_path = youget_dir / relative_path
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, target_path)

            print("[OK] you-get捆绑包创建成功")
            return True
        except Exception as e:
            print(f"[ERROR] you-get捆绑失败: {e}")
            return False

    def create_launch_script(self):
        print("\n创建启动脚本...")

        script = """@echo off
REM Bilibili Audio Extractor Launch Script
setlocal

REM 设置环境变量
set PYTHONPATH=%~dp0you-get;%PYTHONPATH%

REM 检查FFmpeg
where ffmpeg >nul 2>&1
if %errorlevel% neq 0 (
    echo FFmpeg未找到!
    echo 请下载FFmpeg并添加到系统PATH
    echo 下载地址: https://www.gyan.dev/ffmpeg/builds/
    pause
    exit /b 1
)

echo Starting Bilibili Audio Extractor...

REM Launch program
"%~dp0B站音频提取器.exe"

if %errorlevel% neq 0 (
    echo 程序启动失败
    pause
    exit /b 1
)

endlocal
"""

        with open(self.build_dir / "启动程序.bat", 'w', encoding='gbk') as f:
            f.write(script)

        print("[OK] 启动脚本创建成功")
        return True

    def create_readme(self):
        print("\n创建说明文档...")

        readme = """B站音频提取器 v2.0.0
==================

功能特色
--------
- 从B站视频提取高质量音频
- 支持FLAC无损和MP3格式
- 三种音频质量选择
- 配置记忆功能
- 视频文件保留选项

快速开始
--------
1. 运行 "启动程序.bat"
2. 输入B站视频链接
3. 选择音频质量
4. 点击"开始提取音频"

首次使用准备
------------
1. 下载FFmpeg:
   - 访问: https://www.gyan.dev/ffmpeg/builds/
   - 下载: ffmpeg-git-full.7z
   - 解压并将ffmpeg.exe添加到系统PATH

2. 运行程序:
   - 双击 "启动程序.bat"
   - 等待程序启动

使用方法
--------
1. 在"视频URL"输入框粘贴B站链接
2. 选择输出目录 (可选)
3. 选择音频质量:
   - 原始质量: 保持原始参数，音质最佳
   - CD音质: 标准CD音质，平衡音质和文件大小
   - MP3音质: 文件小，适合存储和分享
4. 选择是否保留视频文件
5. 点击"开始提取音频"

注意事项
--------
- 需要稳定的网络连接
- 确保有足够的磁盘空间
- 首次使用需要下载FFmpeg
- 遵守相关法律法规

常见问题
--------
Q: 程序无法启动?
A: 请确保已安装FFmpeg并添加到系统PATH

Q: 下载失败?
A: 检查网络连接，或尝试不同的下载策略

Q: 输出文件在哪里?
A: 在设置的输出目录中，文件名基于视频标题

技术支持
--------
如有问题，请查看常见问题或联系开发者

享受您的无损音乐之旅!
"""

        with open(self.build_dir / "使用说明.txt", 'w', encoding='utf-8') as f:
            f.write(readme)

        print("[OK] 说明文档创建成功")
        return True

    def create_package(self):
        print("\n创建安装包...")
        self.output_dir.mkdir(exist_ok=True)

        zip_name = self.output_dir / f"Bilibili_Audio_Extractor_v{self.version}_Portable.zip"

        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in self.build_dir.rglob('*'):
                if file_path.is_file() and 'temp' not in file_path.parts:
                    arcname = file_path.relative_to(self.build_dir)
                    zipf.write(file_path, arcname)

        print(f"[OK] 安装包创建完成: {zip_name}")
        return True

    def cleanup(self):
        print("\n清理临时文件...")
        temp_dir = self.build_dir / "temp"
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

        spec_file = self.project_dir / f"{self.app_name}.spec"
        if spec_file.exists():
            spec_file.unlink()

        print("[OK] 清理完成")

    def build(self):
        print(f"开始构建{self.app_name}安装包")
        print("=" * 50)

        if not self.check_dependencies():
            return False

        steps = [
            ("创建可执行文件", self.create_exe),
            ("创建you-get捆绑包", self.create_youget_bundle),
            ("创建启动脚本", self.create_launch_script),
            ("创建说明文档", self.create_readme),
            ("创建安装包", self.create_package)
        ]

        for name, func in steps:
            if not func():
                print(f"[ERROR] {name}失败")
                return False

        self.cleanup()

        print("\n" + "=" * 50)
        print("[SUCCESS] 构建完成!")
        print(f"输出目录: {self.output_dir}")
        print("=" * 50)

        return True

def main():
    builder = PackageBuilder()
    if builder.build():
        print("\n构建成功!")
        return 0
    else:
        print("\n构建失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())