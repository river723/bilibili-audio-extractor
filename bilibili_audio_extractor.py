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
from typing import Optional, Tuple, Dict, List
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

        # 检查ffprobe
        try:
            subprocess.run(['ffprobe', '-version'],
                         capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing_deps.append('ffprobe (FFmpeg组件)')

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

    def download_video(self, url: str, format_choice: str = None) -> Optional[Path]:
        """使用you-get下载视频"""
        logger.info(f"开始下载视频: {url}")

        try:
            # 构建you-get命令
            cmd = ['you-get', '--output-dir', str(self.temp_dir)]

            # 添加格式选择
            if format_choice:
                cmd.extend(['--format', format_choice])
                logger.info(f"使用指定格式: {format_choice}")

            cmd.append(url)

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

    def get_available_audio_formats(self, url: str) -> List[Dict]:
        """获取视频可用的音频格式"""
        logger.info(f"检测可用音频格式: {url}")

        formats = []
        seen_descriptions = set()  # 用于去重

        # 使用you-get获取视频信息
        try:
            cmd = ['you-get', '--json', url]
            result = subprocess.run(cmd, capture_output=True, text=False)

            if result.returncode == 0 and result.stdout:
                try:
                    # 尝试解码输出
                    try:
                        stdout_text = result.stdout.decode('utf-8')
                    except UnicodeDecodeError:
                        stdout_text = result.stdout.decode('gbk', errors='ignore')

                    video_info = json.loads(stdout_text)

                    # 从视频信息中提取可用的格式
                    if 'streams' in video_info:
                        streams = video_info['streams']

                        if isinstance(streams, dict):
                            # streams是字典结构，键是格式名称，值是流信息
                            for stream_key, stream_info in streams.items():
                                if isinstance(stream_info, dict):
                                    quality = stream_info.get('quality', '')
                                    container = stream_info.get('container', '')
                                    size = stream_info.get('size', 'unknown')

                                    if quality and container:
                                        # 解析质量信息，提取分辨率
                                        resolution = ''

                                        # 从quality字段提取分辨率
                                        if '1080' in quality or '1080' in stream_key:
                                            resolution = '1080p'
                                        elif '720' in quality or '720' in stream_key:
                                            resolution = '720p'
                                        elif '480' in quality or '480' in stream_key:
                                            resolution = '480p'
                                        elif '360' in quality or '360' in stream_key:
                                            resolution = '360p'
                                        elif 'hd' in stream_key.lower():
                                            resolution = '高清'

                                        # 创建描述（只显示分辨率）
                                        if resolution:
                                            description = f"{resolution} ({container})"
                                        else:
                                            description = f"{quality} ({container})"

                                        # 生成对应的you-get格式参数
                                        # 优先使用分辨率作为参数
                                        if 'flv' in stream_key.lower():
                                            format_param = 'flv'
                                        elif resolution == '1080p':
                                            format_param = 'hd2'
                                        elif resolution == '720p':
                                            format_param = 'hd1'
                                        elif resolution == '360p':
                                            format_param = '360p'
                                        elif resolution == '480p':
                                            format_param = '480p'
                                        else:
                                            format_param = resolution or 'mp4'

                                        # 去重：如果已经有相同描述的格式，跳过
                                        if description not in seen_descriptions:
                                            seen_descriptions.add(description)
                                            formats.append({
                                                'quality': format_param,
                                                'container': container,
                                                'size': size,
                                                'description': description,
                                                'original_key': stream_key
                                            })
                        elif isinstance(streams, list):
                            # streams是列表结构（旧版本格式）
                            for stream in streams:
                                if isinstance(stream, dict) and stream.get('quality') and stream.get('container'):
                                    description = f"{stream['quality']} ({stream['container']})"

                                    # 去重：如果已经有相同描述的格式，跳过
                                    if description not in seen_descriptions:
                                        seen_descriptions.add(description)
                                        formats.append({
                                            'quality': stream['quality'],
                                            'container': stream['container'],
                                            'size': stream.get('size', 'unknown'),
                                            'description': description,
                                            'original_key': stream.get('quality', '')
                                        })

                    logger.info(f"成功检测到 {len(formats)} 个格式")

                except Exception as e:
                    logger.warning(f"解析视频信息失败: {e}")

            # 如果没有找到具体格式信息，提供默认选项
            if not formats:
                logger.info("使用默认格式选项")
                formats = [
                    {'quality': 'hd2', 'container': 'mp4', 'description': '1080p (MP4, 高质量)', 'original_key': 'hd2'},
                    {'quality': 'hd1', 'container': 'mp4', 'description': '720p (MP4, 标准质量)', 'original_key': 'hd1'},
                    {'quality': 'flv', 'container': 'flv', 'description': 'FLV格式 (高质量)', 'original_key': 'flv'},
                    {'quality': '360p', 'container': 'mp4', 'description': '360p (低质量，免登录)', 'original_key': '360p'}
                ]

        except Exception as e:
            logger.warning(f"获取格式信息失败: {e}，使用默认选项")
            formats = [
                {'quality': 'hd2', 'container': 'mp4', 'description': '1080p (MP4, 高质量)', 'original_key': 'hd2'},
                {'quality': 'hd1', 'container': 'mp4', 'description': '720p (MP4, 标准质量)', 'original_key': 'hd1'},
                {'quality': 'flv', 'container': 'flv', 'description': 'FLV格式 (高质量)', 'original_key': 'flv'},
                {'quality': '360p', 'container': 'mp4', 'description': '360p (低质量，免登录)', 'original_key': '360p'}
            ]

        return formats

    def extract_audio_to_flac(self, video_path: Path,
                            title: str = None,
                            quality_choice: str = "original") -> Optional[Path]:
        """提取音频并转换为指定质量的音频格式"""
        logger.info(f"开始提取音频: {video_path}")

        try:
            # 生成输出文件名
            if title:
                safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
                suffix = self._get_quality_suffix(quality_choice)
                output_file = self.output_dir / f"{safe_title}_{suffix}.flac"
            else:
                suffix = self._get_quality_suffix(quality_choice)
                output_file = self.output_dir / f"{video_path.stem}_{suffix}.flac"

            # 根据用户选择设置音频参数
            cmd = ['ffmpeg', '-i', str(video_path), '-vn']

            if quality_choice == "original":
                # 保持原始质量 (FLAC无损)
                cmd.extend([
                    '-c:a', 'flac',
                    '-compression_level', '12',
                    '-y'
                ])
                logger.info("使用原始质量 (FLAC无损)")
            elif quality_choice == "hires":
                # Hi-Res音质 (FLAC, 96kHz, 24bit)
                cmd.extend([
                    '-c:a', 'flac',
                    '-compression_level', '12',
                    '-ar', '96000',
                    '-sample_fmt', 's32',
                    '-b:a', '1536k',
                    '-y'
                ])
                logger.info("使用Hi-Res音质 (FLAC, 96kHz, 24bit)")
            elif quality_choice == "cd":
                # CD音质 (FLAC, 44.1kHz, 16bit)
                cmd.extend([
                    '-c:a', 'flac',
                    '-compression_level', '12',
                    '-ar', '44100',
                    '-sample_fmt', 's16',
                    '-b:a', '1411k',
                    '-y'
                ])
                logger.info("使用CD音质 (FLAC, 44.1kHz, 16bit)")
            elif quality_choice == "mp3_high":
                # 高音质MP3 (MP3, 320kbps)
                output_file = output_file.with_suffix('.mp3')
                cmd.extend([
                    '-c:a', 'libmp3lame',
                    '-b:a', '320k',
                    '-y'
                ])
                logger.info("使用高音质MP3 (MP3, 320kbps)")
            elif quality_choice == "mp3_standard":
                # 标准MP3音质 (MP3, 128kbps)
                output_file = output_file.with_suffix('.mp3')
                cmd.extend([
                    '-c:a', 'libmp3lame',
                    '-b:a', '128k',
                    '-y'
                ])
                logger.info("使用标准MP3音质 (MP3, 128kbps)")
            else:
                # 默认使用原始质量
                cmd.extend([
                    '-c:a', 'flac',
                    '-compression_level', '12',
                    '-y'
                ])
                logger.info("使用默认原始质量 (FLAC无损)")

            cmd.append(str(output_file))

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                logger.error(f"音频提取失败: {result.stderr}")
                return None

            if output_file.exists():
                logger.info(f"音频文件已创建: {output_file}")
                logger.info(f"文件大小: {output_file.stat().st_size / (1024*1024):.2f} MB")
                return output_file
            else:
                logger.error("音频文件未生成")
                return None

        except Exception as e:
            logger.error(f"音频提取过程出错: {e}")
            return None

    def _get_quality_suffix(self, quality_choice: str) -> str:
        """获取质量选项对应的后缀"""
        suffix_map = {
            "original": "原始质量",
            "hires": "HiRes音质",
            "cd": "CD音质",
            "mp3_high": "高音质MP3",
            "mp3_standard": "标准MP3"
        }
        return suffix_map.get(quality_choice, "音频")

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

    def check_audio_streams(self, video_path: Path) -> dict:
        """检查视频文件中的音频流信息"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_streams',
                '-select_streams', 'a',
                str(video_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                info = json.loads(result.stdout)
                if 'streams' in info and len(info['streams']) > 0:
                    audio_stream = info['streams'][0]
                    logger.info(f"音频流信息: {audio_stream}")
                    return audio_stream
            return {}
        except Exception as e:
            logger.warning(f"检查音频流信息失败: {e}")
            return {}

    def process_url(self, url: str, format_choice: str = None, quality_choice: str = None) -> Tuple[bool, str]:
        """处理单个B站URL"""
        logger.info(f"处理URL: {url}")

        # 验证URL
        if not self.validate_bilibili_url(url):
            return False, "无效的B站视频链接"

        # 获取视频信息
        video_info = self.get_video_info(url)
        title = video_info.get('title', '未知标题')

        logger.info(f"视频标题: {title}")

        # 显示可用格式并让用户选择
        if format_choice is None:
            available_formats = self.get_available_audio_formats(url)
            print("\n=== 可下载的音频格式 ===")
            for i, fmt in enumerate(available_formats, 1):
                print(f"{i}. {fmt['description']}")

            while True:
                try:
                    choice = input(f"\n请选择下载格式 (1-{len(available_formats)}，默认1): ").strip()
                    if choice == "":
                        format_choice = available_formats[0]['quality']
                        break
                    elif choice.isdigit() and 1 <= int(choice) <= len(available_formats):
                        format_choice = available_formats[int(choice)-1]['quality']
                        break
                    else:
                        print(f"请输入 1-{len(available_formats)} 之间的数字")
                except (KeyboardInterrupt, EOFError):
                    return False, "用户取消操作"

            print(f"已选择格式: {format_choice}")

        # 显示音频质量选项并让用户选择
        quality_options = [
            ("original", "原始质量 (FLAC无损)"),
            ("hires", "Hi-Res音质 (FLAC, 96kHz, 24bit)"),
            ("cd", "CD音质 (FLAC, 44.1kHz, 16bit)"),
            ("mp3_high", "高音质MP3 (MP3, 320kbps)"),
            ("mp3_standard", "标准MP3音质 (MP3, 128kbps)")
        ]

        if quality_choice is None:
            print("\n=== 音频输出质量 ===")
            for i, (key, desc) in enumerate(quality_options, 1):
                print(f"{i}. {desc}")

            while True:
                try:
                    choice = input(f"\n请选择输出质量 (1-{len(quality_options)}，默认1): ").strip()
                    if choice == "":
                        quality_choice = quality_options[0][0]
                        break
                    elif choice.isdigit() and 1 <= int(choice) <= len(quality_options):
                        quality_choice = quality_options[int(choice)-1][0]
                        break
                    else:
                        print(f"请输入 1-{len(quality_options)} 之间的数字")
                except (KeyboardInterrupt, EOFError):
                    return False, "用户取消操作"

            print(f"已选择质量: {dict(quality_options)[quality_choice]}")

        # 下载视频
        video_path = self.download_video(url, format_choice)
        if not video_path:
            return False, "视频下载失败"

        # 检查音频流质量
        audio_info = self.check_audio_streams(video_path)
        if audio_info:
            sample_rate = audio_info.get('sample_rate', '44100')
            channels = audio_info.get('channels', 2)
            logger.info(f"源音频 - 采样率: {sample_rate}Hz, 声道: {channels}")

        # 提取音频
        audio_path = self.extract_audio_to_flac(video_path, title, quality_choice)

        # 清理临时文件
        try:
            video_path.unlink()
            logger.info("临时文件已清理")
        except Exception as e:
            logger.warning(f"清理临时文件失败: {e}")

        if audio_path:
            return True, f"音频提取成功: {audio_path}"
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
    parser.add_argument('--format', '-f', help='指定下载格式 (如: hd2, hd1, flv, 360p)')
    parser.add_argument('--quality', '-q',
                       choices=['original', 'hires', 'cd', 'mp3_high', 'mp3_standard'],
                       help='指定输出音频质量')
    parser.add_argument('--auto', '-a', action='store_true',
                       help='自动模式，跳过用户交互，使用默认选项')
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

    print(f"OK: {deps_msg}")

    if args.cleanup:
        extractor.cleanup_temp_files()
        return 0

    if not args.url:
        print("请输入B站视频链接")
        print("用法: python bilibili_audio_extractor.py <URL> [选项]")
        print("\n选项:")
        print("  --format, -f FORMAT    指定下载格式 (hd2, hd1, flv, 360p)")
        print("  --quality, -q QUALITY  指定输出质量 (original, hires, cd, mp3_high, mp3_standard)")
        print("  --auto, -a             自动模式，跳过用户交互")
        print("  --output, -o DIR       指定输出目录")
        print("  --cleanup              清理临时文件")
        return 1

    # 处理URL
    if args.auto:
        # 自动模式，使用命令行参数或默认值
        format_choice = args.format if args.format else 'hd2'
        quality_choice = args.quality if args.quality else 'original'
        success, message = extractor.process_url(args.url, format_choice, quality_choice)
    else:
        # 交互模式，用户可以覆盖命令行参数
        success, message = extractor.process_url(args.url, args.format, args.quality)

    print(message)

    if success:
        print(f"\n输出目录: {extractor.output_dir}")
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())