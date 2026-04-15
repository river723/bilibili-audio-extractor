#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
安装qrcode库的辅助脚本
"""

import subprocess
import sys
import os

def install_qrcode():
    """安装qrcode库"""

    print("=== 安装qrcode库（用于本地二维码生成） ===\n")

    print("正在尝试安装qrcode库...")

    try:
        # 尝试使用pip安装
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "qrcode[pil]"
        ], capture_output=True, text=True, timeout=120)

        if result.returncode == 0:
            print("✓ qrcode库安装成功！")
            print("✓ 现在可以使用本地二维码生成功能")
            return True
        else:
            print("✗ 安装失败:")
            print(result.stderr)
            return False

    except subprocess.TimeoutExpired:
        print("✗ 安装超时，请检查网络连接")
        return False
    except Exception as e:
        print(f"✗ 安装过程中出现错误: {e}")
        return False

def check_installation():
    """检查qrcode是否安装成功"""

    print("\n=== 检查安装结果 ===")

    try:
        import qrcode
        print("✓ qrcode库已成功安装")

        # 测试基本功能
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data("https://www.bilibili.com")
        qr.make(fit=True)
        print("✓ 二维码生成功能正常")

        return True

    except ImportError:
        print("✗ qrcode库未安装")
        return False
    except Exception as e:
        print(f"✗ qrcode库功能异常: {e}")
        return False

def show_alternatives():
    """显示替代方案"""

    print("\n=== 替代方案 ===")
    print("如果无法安装qrcode库，程序仍能正常工作：")
    print("1. 使用外部API生成二维码（https://api.qrserver.com）")
    print("2. 如果外部API失败，显示文字链接")
    print("3. 用户可复制链接到浏览器手动登录")
    print("\n安装qrcode库的优点：")
    print("- 本地生成，无需网络请求")
    print("- 更快速，更稳定")
    print("- 减少外部依赖")

def main():
    """主函数"""

    # 检查是否已安装
    if check_installation():
        print("\nqrcode库已安装，无需重复安装。")
        return

    # 尝试安装
    if install_qrcode():
        # 再次检查
        if check_installation():
            print("\n✓ 安装完成，功能正常！")
        else:
            print("\n⚠ 安装似乎成功，但功能检查失败")
            show_alternatives()
    else:
        print("\n⚠ 安装失败")
        show_alternatives()

if __name__ == "__main__":
    main()