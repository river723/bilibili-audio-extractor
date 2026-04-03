#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站音频提取器 - Python演示版本
功能：从B站视频提取高质量FLAC音频
"""

import os
import sys
import json
import subprocess
import re
import argparse
from pathlib import Path
from typing import Optional, Tuple
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BilibiliAudioExtractor:
    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir) if output_dir else Path.home() / "B站音频提取"
        self.temp_dir = Path(os.getenv('TEMP', '/tmp')) / "bilibili_audio_extractor"
        self._setup_directories()

    def _setup_directories(self):
        """创建必要的目录"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def check_dependencies(self) -> Tuple[bool, str]:
        """检查必要的依赖"""
        missing_deps = []

        # 检查FFmpeg
        try:
            subprocess.run(['ffmpeg', '-version'],
                         capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing_deps.append('FFmpeg')

        # 检查you-get
        try:
            subprocess.run(['you-get', '--version'],
                         capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing_deps.append('you-get')

        if missing_deps:
            return False, f"缺少依赖: {', '.join(missing_deps)}"
        return True, "所有依赖已安装"

    def validate_bilibili_url(self, url: str) -> bool:
        """验证B站URL格式"""
        patterns = [
            r'https?://www\.bilibili\.com/video/[AaBb][Vv]\w+',
            r'https?://b23\.tv/[AaBb][Vv]\w+',
            r'https?://www\.bilibili\.com/video/[Bb][Vv]\w+',
        ]

        return any(re.match(pattern, url) for pattern in patterns)

    def download_video(self, url: str) -> Optional[Path]:
        """使用you-get下载视频"""
        logger.info(f"开始下载视频: {url}")

        try:
            # 构建you-get命令
            cmd = [
                'you-get',
                '--format=flv',  # 选择高质量格式
                '--output-dir', str(self.temp_dir),
                url
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                logger.error(f"下载失败: {result.stderr}")
                return None

            # 查找下载的文件
            video_files = list(self.temp_dir.glob('*.mp4')) + \
                         list(self.temp_dir.glob('*.flv')) + \
                         list(self.temp_dir.glob('*.mkv'))

            if video_files:
                logger.info(f"视频下载完成: {video_files[0]}")
                return video_files[0]
            else:
                logger.error("未找到下载的视频文件")
                return None

        except Exception as e:
            logger.error(f"下载过程出错: {e}")
            return None

    def extract_audio_to_flac(self, video_path: Path,
                            title: str = None) -> Optional[Path]:
        """提取音频并转换为FLAC格式"""
        logger.info(f"开始提取音频: {video_path}")

        try:
            # 生成输出文件名
            if title:
                safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
                output_file = self.output_dir / f"{safe_title}.flac"
            else:
                output_file = self.output_dir / f"{video_path.stem}.flac"

            # 构建FFmpeg命令
            cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-vn',  # 不复制视频
                '-c:a', 'flac',  # FLAC编码
                '-compression_level', '12',  # 最高压缩级别
                '-ar', '48000',  # 采样率48kHz
                '-sample_fmt', 's32',  # 32位采样
                '-y',  # 覆盖输出文件
                str(output_file)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                logger.error(f"音频提取失败: {result.stderr}")
                return None

            if output_file.exists():
                logger.info(f"FLAC音频文件已创建: {output_file}")
                logger.info(f"文件大小: {output_file.stat().st_size / (1024*1024):.2f} MB")
                return output_file
            else:
                logger.error("FLAC文件未生成")
                return None

        except Exception as e:
            logger.error(f"音频提取过程出错: {e}")
            return None

    def get_video_info(self, url: str) -> dict:
        """获取视频信息"""
        try:
            cmd = ['you-get', '--json', url]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                logger.warning(f"无法获取视频信息: {result.stderr}")
                return {}
        except Exception as e:
            logger.warning(f"获取视频信息失败: {e}")
            return {}

    def process_url(self, url: str) -> Tuple[bool, str]:
        """处理单个B站URL"""
        logger.info(f"处理URL: {url}")

        # 验证URL
        if not self.validate_bilibili_url(url):
            return False, "无效的B站视频链接"

        # 获取视频信息
        video_info = self.get_video_info(url)
        title = video_info.get('title', '未知标题')

        logger.info(f"视频标题: {title}")

        # 下载视频
        video_path = self.download_video(url)
        if not video_path:
            return False, "视频下载失败"

        # 提取音频
        flac_path = self.extract_audio_to_flac(video_path, title)

        # 清理临时文件
        try:
            video_path.unlink()
            logger.info("临时文件已清理")
        except Exception as e:
            logger.warning(f"清理临时文件失败: {e}")

        if flac_path:
            return True, f"音频提取成功: {flac_path}"
        else:
            return False, "音频提取失败"

    def cleanup_temp_files(self):
        """清理临时文件"""
        try:
            for file in self.temp_dir.glob('*'):
                if file.is_file():
                    file.unlink()
            logger.info("临时文件已清理")
        except Exception as e:
            logger.warning(f"清理临时文件失败: {e}")

def main():
    parser = argparse.ArgumentParser(description='B站音频提取器')
    parser.add_argument('url', nargs='?', help='B站视频链接')
    parser.add_argument('--output', '-o', help='输出目录')
    parser.add_argument('--cleanup', action='store_true',
                       help='清理临时文件')

    args = parser.parse_args()

    extractor = BilibiliAudioExtractor(args.output)

    # 检查依赖
    deps_ok, deps_msg = extractor.check_dependencies()
    if not deps_ok:
        print(f"错误: {deps_msg}")
        print("请安装缺失的依赖:")
        print("1. FFmpeg: https://ffmpeg.org/download.html")
        print("2. you-get: pip install you-get")
        return 1

    print(f"✓ {deps_msg}")

    if args.cleanup:
        extractor.cleanup_temp_files()
        return 0

    if not args.url:
        print("请输入B站视频链接")
        print("用法: python bilibili_audio_extractor.py <URL> [--output DIR]")
        return 1

    # 处理URL
    success, message = extractor.process_url(args.url)
    print(message)

    if success:
        print(f"\n输出目录: {extractor.output_dir}")
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())