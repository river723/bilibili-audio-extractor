#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
B站音频提取器 - 统一安装方案验证脚本

此脚本验证新的统一安装方案是否正常工作
"""

import subprocess
import sys
import time
from pathlib import Path

def print_status(message, status_type="info"):
    """打印状态消息"""
    try:
        if status_type == "success":
            print(f"✓ {message}")
        elif status_type == "error":
            print(f"✗ {message}")
        elif status_type == "warning":
            print(f"⚠ {message}")
        else:
            print(f"ℹ {message}")
    except UnicodeEncodeError:
        # Fallback for Windows encoding issues
        if status_type == "success":
            print(f"SUCCESS: {message}")
        elif status_type == "error":
            print(f"ERROR: {message}")
        elif status_type == "warning":
            print(f"WARNING: {message}")
        else:
            print(f"INFO: {message}")

def test_unified_installer():
    """测试统一安装器"""
    print("=" * 60)
    print("B站音频提取器 - 统一安装方案验证")
    print("=" * 60)
    print()

    # 测试build_package.py的install模式
    print_status("测试依赖安装模式...", "info")

    try:
        result = subprocess.run(
            [sys.executable, "build_package.py", "install"],
            capture_output=True,
            text=True,
            timeout=600  # 10分钟超时
        )

        if result.returncode == 0:
            print_status("依赖安装模式测试成功", "success")
            return True
        else:
            print_status(f"依赖安装模式测试失败: {result.stderr[:200]}", "error")
            return False

    except subprocess.TimeoutExpired:
        print_status("依赖安装超时", "warning")
        return False
    except Exception as e:
        print_status(f"测试异常: {e}", "error")
        return False

def test_qrcode_functionality():
    """测试qrcode功能"""
    print_status("\n测试qrcode功能...", "info")

    try:
        import qrcode
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data("https://www.bilibili.com/video/BV1Hs4y1B7T2")
        qr.make(fit=True)

        # 生成图像
        img = qr.make_image(fill_color="black", back_color="white")

        print_status("qrcode库功能正常", "success")
        return True

    except ImportError:
        print_status("qrcode库未安装", "warning")
        return False
    except Exception as e:
        print_status(f"qrcode功能测试失败: {e}", "error")
        return False

def test_pillow_functionality():
    """测试Pillow功能"""
    print_status("测试Pillow功能...", "info")

    try:
        from PIL import Image, ImageTk
        print_status("Pillow库功能正常", "success")
        return True
    except ImportError:
        print_status("Pillow库未安装", "warning")
        return False
    except Exception as e:
        print_status(f"Pillow功能测试失败: {e}", "error")
        return False

def main():
    """主函数"""

    # 运行统一安装器测试
    install_success = test_unified_installer()

    # 测试核心功能
    qrcode_success = test_qrcode_functionality()
    pillow_success = test_pillow_functionality()

    print("\n" + "=" * 60)
    print_status("测试结果摘要", "info")
    print("=" * 60)

    try:
        print(f"\n统一安装器: {'✓ 正常' if install_success else '✗ 失败'}")
        print(f"qrcode功能: {'✓ 正常' if qrcode_success else '⚠ 未安装'}")
        print(f"Pillow功能: {'✓ 正常' if pillow_success else '⚠ 未安装'}")
    except UnicodeEncodeError:
        print(f"\n统一安装器: {'正常' if install_success else '失败'}")
        print(f"qrcode功能: {'正常' if qrcode_success else '未安装'}")
        print(f"Pillow功能: {'正常' if pillow_success else '未安装'}")

    if install_success and qrcode_success and pillow_success:
        print_status("\n所有测试通过！统一安装方案工作正常", "success")
        print("\n您现在可以：")
        print("1. 运行: python gui_extractor_simple.py")
        print("2. 或打包: 一键打包.bat")
        return True
    else:
        print_status("\n部分测试未通过，但程序仍能正常运行", "warning")
        print("\n功能说明:")
        if not qrcode_success:
            print("- 将使用外部API生成二维码（需要网络）")
        if not pillow_success:
            print("- Pillow库缺失可能影响图像处理")
        print("\n建议重新运行: 一键打包.bat install")
        return False

if __name__ == "__main__":
    success = main()

    print("\n按任意键退出...")
    try:
        input()
    except:
        pass

    sys.exit(0 if success else 1)