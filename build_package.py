#!/usr/bin/env python3
"""
B站音频提取器 - 统一安装与打包工具

此脚本整合了所有依赖安装和打包功能，提供完整的解决方案
"""

import os
import sys
import subprocess
import shutil
import json
import zipfile
import time
from pathlib import Path

class UnifiedInstaller:
    """统一安装器"""

    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.build_dir = self.project_dir / "build"
        self.output_dir = self.project_dir / "output"
        self.version = "2.3.0"
        self.app_name = "B站音频提取器"
        self.log_file = Path.home() / ".bilibili_audio_extractor" / "install_log.txt"
        self.log_file.parent.mkdir(exist_ok=True)

    def log_message(self, message):
        """记录日志"""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")

    def print_status(self, message, status_type="info"):
        """打印状态消息"""
        try:
            if status_type == "info":
                print(f"ℹ {message}")
            elif status_type == "success":
                print(f"✓ {message}")
            elif status_type == "warning":
                print(f"⚠ {message}")
            elif status_type == "error":
                print(f"✗ {message}")
            else:
                print(message)
        except UnicodeEncodeError:
            # Fallback for Windows encoding issues
            if status_type == "info":
                print(f"INFO: {message}")
            elif status_type == "success":
                print(f"SUCCESS: {message}")
            elif status_type == "warning":
                print(f"WARNING: {message}")
            elif status_type == "error":
                print(f"ERROR: {message}")
            else:
                print(message)

    def run_command(self, cmd, timeout=120):
        """运行命令并返回结果"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)

    def check_core_dependencies(self):
        """检查核心依赖"""
        self.print_status("检查核心依赖...", "info")
        self.log_message("开始检查核心依赖")

        # 检查you-get
        try:
            import you_get
            self.print_status("you-get 已安装", "success")
            self.log_message("you-get 检查通过")
        except ImportError:
            self.print_status("you-get 未安装", "error")
            self.log_message("you-get 未安装")
            return False

        # 检查FFmpeg
        success, stdout, stderr = self.run_command(['ffmpeg', '-version'])
        if success:
            self.print_status("FFmpeg 已安装", "success")
            self.log_message("FFmpeg 检查通过")
        else:
            self.print_status("FFmpeg 未安装，请从 https://ffmpeg.org 下载安装", "error")
            self.log_message("FFmpeg 未安装")
            return False

        return True

    def install_all_dependencies(self):
        """安装所有Python依赖"""
        self.print_status("\n安装Python依赖...", "info")
        self.log_message("开始安装Python依赖")

        dependencies = {
            "qrcode[pil]": "qrcode库（本地二维码生成）",
            "Pillow": "Pillow库（图像处理）",
            "requests": "requests库（网络请求）",
            "mutagen": "mutagen库（音频元数据）"
        }

        results = {}

        for package, description in dependencies.items():
            self.print_status(f"检查 {description}...", "info")

            # 检查是否已安装
            if package == "qrcode[pil]":
                check_cmd = "import qrcode"
            else:
                check_cmd = f"import {package.split('[')[0].lower()}"

            try:
                exec(check_cmd)
                self.print_status(f"{description} 已安装", "success")
                results[package] = True
                continue
            except ImportError:
                pass

            # 安装依赖
            self.print_status(f"正在安装 {description}...", "info")
            success, stdout, stderr = self.run_command([
                sys.executable, "-m", "pip", "install", package
            ], timeout=300)

            if success:
                self.print_status(f"{description} 安装成功", "success")
                results[package] = True
                self.log_message(f"{package} 安装成功")
            else:
                self.print_status(f"{description} 安装失败: {stderr[:100]}", "warning")
                results[package] = False
                self.log_message(f"{package} 安装失败: {stderr}")

        return results

    def verify_installation(self):
        """验证安装结果"""
        self.print_status("\n验证安装结果...", "info")
        self.log_message("开始验证安装结果")

        verification_results = {}

        # 验证qrcode
        try:
            import qrcode
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data("https://www.bilibili.com")
            qr.make(fit=True)
            verification_results["qrcode"] = True
            self.print_status("qrcode 功能验证成功", "success")
        except Exception as e:
            verification_results["qrcode"] = False
            self.print_status(f"qrcode 功能验证失败: {e}", "warning")

        # 验证Pillow
        try:
            from PIL import Image
            verification_results["Pillow"] = True
            self.print_status("Pillow 功能验证成功", "success")
        except Exception as e:
            verification_results["Pillow"] = False
            self.print_status(f"Pillow 功能验证失败: {e}", "warning")

        return verification_results

    def show_installation_summary(self, install_results, verification_results):
        """显示安装摘要"""
        print("\n" + "="*60)
        self.print_status("安装摘要", "info")
        print("="*60)

        print("\n依赖安装状态:")
        try:
            for package, success in install_results.items():
                status = "✓ 已安装" if success else "⚠ 安装失败"
                print(f"  - {package}: {status}")

            print("\n功能验证状态:")
            for lib, success in verification_results.items():
                status = "✓ 正常" if success else "⚠ 异常"
                print(f"  - {lib}: {status}")
        except UnicodeEncodeError:
            for package, success in install_results.items():
                status = "已安装" if success else "安装失败"
                print(f"  - {package}: {status}")

            print("\n功能验证状态:")
            for lib, success in verification_results.items():
                status = "正常" if success else "异常"
                print(f"  - {lib}: {status}")

        print("\n功能说明:")
        if verification_results.get("qrcode", False):
            self.print_status("本地二维码生成已启用（推荐）", "success")
        else:
            self.print_status("将使用外部API生成二维码", "warning")
            print("    用户仍可正常使用，但需要网络连接")

        self.log_message("安装摘要已显示")

    def run_installation_only(self):
        """仅运行安装（不打包）"""
        print("="*60)
        print("B站音频提取器 - 依赖安装程序")
        print("="*60)
        print()

        self.log_message("开始依赖安装流程")

        try:
            # 1. 检查核心依赖
            if not self.check_core_dependencies():
                self.print_status("核心依赖检查失败，请先安装必要的依赖", "error")
                self.log_message("核心依赖检查失败")
                return False

            # 2. 安装Python依赖
            install_results = self.install_all_dependencies()

            # 3. 验证安装
            verification_results = self.verify_installation()

            # 4. 显示摘要
            self.show_installation_summary(install_results, verification_results)

            self.print_status("\n依赖安装完成！", "success")
            print("现在可以正常运行B站音频提取器了！")
            print("运行命令: python gui_extractor_simple.py")

            self.log_message("依赖安装流程完成")
            return True

        except Exception as e:
            self.print_status(f"安装过程中出现错误: {e}", "error")
            self.log_message(f"安装错误: {e}")
            return False

class PackageBuilder(UnifiedInstaller):
    """打包构建器"""

    def check_build_dependencies(self):
        """检查打包依赖"""
        print("检查打包依赖...")
        try:
            import PyInstaller
            print("[OK] PyInstaller已安装")
        except ImportError:
            print("[ERROR] PyInstaller未安装")
            return False
        return True

    def create_exe(self):
        """创建可执行文件"""
        print("\n创建可执行文件...")
        self.build_dir.mkdir(exist_ok=True)

        cmd = [
            'pyinstaller',
            '--onefile',
            '--windowed',
            '--noconsole',  # 完全禁止控制台窗口
            '--disable-windowed-traceback',  # 禁用窗口化模式的跟踪回溯
            f'--name={self.app_name}',
            '--distpath', str(self.build_dir),
            '--workpath', str(self.build_dir / "temp"),
            '--clean',  # 清理临时文件
            '--hidden-import=you_get',  # 显式包含you-get模块
            '--collect-submodules=you_get',  # 收集所有子模块
            'gui_extractor_simple.py'
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
        """创建you-get捆绑包"""
        print("\n创建you-get捆绑包...")
        youget_dir = self.build_dir / "you-get"
        youget_dir.mkdir(exist_ok=True)

        try:
            import you_get
            youget_path = Path(you_get.__file__).parent

            for item in youget_path.rglob('*'):
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
        """创建启动脚本（简化版，不再需要）"""
        print("\n跳过启动脚本创建（EXE可直接运行）...")
        print("[OK] EXE文件现在可以直接运行，无需启动脚本")
        return True

    def create_readme(self):
        """创建说明文档"""
        print("\n创建说明文档...")

        readme = f"""B站音频提取器 v{self.version}
==================

功能特色
--------
- 从B站视频提取高质量音频
- 支持FLAC无损和MP3格式
- 本地二维码生成（已预装qrcode库）
- 配置记忆功能
- 视频文件保留选项
- 🎯 一键运行（EXE可直接双击）

快速开始
--------
1. 双击 "B站音频提取器.exe"
2. 输入B站视频链接
3. 点击"开始提取音频"

首次使用准备
------------
1. 下载FFmpeg:
   - 访问: https://www.gyan.dev/ffmpeg/builds/
   - 下载: ffmpeg-git-full.7z
   - 解压并将ffmpeg.exe添加到系统PATH

2. 运行程序:
   - 直接双击 "B站音频提取器.exe"
   - 等待程序启动

使用方法
--------
1. 在"视频URL"输入框粘贴B站链接
2. 选择输出目录 (可选)
3. 点击"开始提取音频"

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
        """创建安装包"""
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

    def create_inno_script(self):
        """生成Inno Setup配置脚本"""
        print("\n生成Inno Setup脚本...")

        # Inno Setup脚本内容
        iss_content = f"""[Setup]
AppName={self.app_name}
AppVersion={self.version}
AppPublisher=Audio Extractor
AppSupportURL=https://github.com/river723/bilibili-audio-extractor
DefaultDirName={{autopf}}\\{self.app_name}
DefaultGroupName={self.app_name}
AllowNoIcons=yes
LicenseFile=
InfoBeforeFile=
OutputDir={self.output_dir}
OutputBaseFilename={self.app_name}_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ShowLanguageDialog=no
LanguageDetectionMethod=uilanguage
UsePreviousLanguage=no
ShowUndisplayableLanguages=no

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"; Flags: unchecked

[Files]
Source: "{self.build_dir}\\B站音频提取器.exe"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "{self.build_dir}\\you-get\\*"; DestDir: "{{app}}\\you-get"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{self.build_dir}\\使用说明.txt"; DestDir: "{{app}}"; Flags: ignoreversion

[Icons]
Name: "{{group}}\\{self.app_name}"; Filename: "{{app}}\\B站音频提取器.exe"
Name: "{{group}}\\{{cm:UninstallProgram,{self.app_name}}}"; Filename: "{{uninstallexe}}"
Name: "{{autodesktop}}\\{self.app_name}"; Filename: "{{app}}\\B站音频提取器.exe"; Tasks: desktopicon

[Run]
Filename: "{{app}}\\B站音频提取器.exe"; Description: "{{cm:LaunchProgram,{self.app_name}}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: dirifempty; Name: "{{app}}\\you-get"
Type: dirifempty; Name: "{{app}}"
"""

        # 保存.iss脚本
        iss_path = self.build_dir / "setup.iss"
        with open(iss_path, 'w', encoding='utf-8') as f:
            f.write(iss_content)

        print(f"[OK] Inno Setup脚本生成: {iss_path}")
        return True

    def compile_inno_installer(self):
        """使用ISCC编译Inno Setup脚本"""
        print("\n编译Inno Setup安装程序...")

        # 尝试多个可能的ISCC位置
        possible_paths = [
            Path("C:/Program Files (x86)/Inno Setup 6/ISCC.exe"),
            Path("C:/Program Files/Inno Setup 6/ISCC.exe"),
            Path("C:/Program Files (x86)/Inno Setup 5/ISCC.exe"),
            Path("C:/Program Files/Inno Setup 5/ISCC.exe"),
        ]

        iscc_path = None
        for path in possible_paths:
            if path.exists():
                iscc_path = path
                break

        if iscc_path is None:
            print("[WARNING] ISCC.exe未找到，跳过Inno Setup编译")
            print("[提示] 请从 https://jrsoftware.org/isinfo.php 下载安装Inno Setup")
            return False

        try:
            iss_file = self.build_dir / "setup.iss"
            result = subprocess.run(
                [str(iscc_path), str(iss_file)],
                capture_output=True,
                text=True,
                cwd=str(self.project_dir)
            )

            if result.returncode == 0:
                print("[OK] Inno Setup安装程序编译成功")
                setup_exe = self.output_dir / f"{self.app_name}_Setup.exe"
                if setup_exe.exists():
                    print(f"[OK] 生成安装程序: {setup_exe}")
                    return True
                else:
                    print("[ERROR] 安装程序文件未找到")
                    return False
            else:
                print(f"[ERROR] 编译失败: {result.stderr}")
                return False

        except Exception as e:
            print(f"[ERROR] 编译异常: {e}")
            return False

    def create_inno_setup_installer(self):
        """创建Inno Setup安装程序（完整流程）"""
        print("\n[*] 创建Inno Setup安装程序...")

        # 检查是否有ISCC
        possible_paths = [
            Path("C:/Program Files (x86)/Inno Setup 6/ISCC.exe"),
            Path("C:/Program Files/Inno Setup 6/ISCC.exe"),
            Path("C:/Program Files (x86)/Inno Setup 5/ISCC.exe"),
            Path("C:/Program Files/Inno Setup 5/ISCC.exe"),
        ]

        iscc_exists = any(path.exists() for path in possible_paths)

        if not iscc_exists:
            print("[INFO] 跳过Inno Setup编译（ISCC未安装）")
            print("[建议] 从 https://jrsoftware.org/isinfo.php 下载安装Inno Setup，然后重新运行")
            return True  # 不影响整体打包流程

        # 执行Inno Setup流程
        if not self.create_inno_script():
            return False

        if not self.compile_inno_installer():
            return False

        return True

    def cleanup(self):
        """清理临时文件"""
        print("\n清理临时文件...")
        temp_dir = self.build_dir / "temp"
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

        spec_file = self.project_dir / f"{self.app_name}.spec"
        if spec_file.exists():
            spec_file.unlink()

        # 清理build目录中的旧文件（除了EXE和说明文档）
        if self.build_dir.exists():
            for item in self.build_dir.iterdir():
                if item.is_file() and item.suffix in ['.bat', '.vbs']:
                    item.unlink()
                    print(f"清理旧文件: {item.name}")

        print("[OK] 清理完成")

    def build_package(self):
        """构建安装包"""
        print(f"开始构建{self.app_name}安装包")
        print("=" * 50)

        if not self.check_build_dependencies():
            return False

        # 先安装依赖
        print("\n" + "=" * 20 + " 安装依赖 " + "=" * 20)
        if not self.run_installation_only():
            print("[WARNING] 依赖安装存在问题，继续打包...")

        print("\n" + "=" * 20 + " 开始打包 " + "=" * 20)

        steps = [
            ("创建可执行文件", self.create_exe),
            ("创建you-get捆绑包", self.create_youget_bundle),
            ("创建说明文档", self.create_readme),
            ("创建ZIP安装包", self.create_package),
            ("创建Inno Setup安装程序", self.create_inno_setup_installer),
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
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == "install":
        # 仅安装依赖模式
        builder = UnifiedInstaller()
        success = builder.run_installation_only()
        return 0 if success else 1
    else:
        # 完整打包模式
        builder = PackageBuilder()
        success = builder.build_package()
        return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())