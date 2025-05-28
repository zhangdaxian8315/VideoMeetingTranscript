#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频轨道提取工具
从OBS录制的.mkv视频文件中提取双音轨为独立的.wav文件

作者: VideoMeetingTranscript
创建时间: 2025-01-28
"""

import os
import sys
import argparse
import subprocess
import logging
from pathlib import Path
from typing import Optional, Tuple


class AudioTrackExtractor:
    """音频轨道提取器"""
    
    def __init__(self, log_level: str = "INFO"):
        """
        初始化音频轨道提取器
        
        Args:
            log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        """
        self.setup_logging(log_level)
        self.logger = logging.getLogger(__name__)
        
    def setup_logging(self, level: str) -> None:
        """设置日志配置"""
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def check_ffmpeg_available(self) -> bool:
        """检查ffmpeg是否可用"""
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode == 0:
                self.logger.info("FFmpeg 可用")
                return True
            else:
                self.logger.error("FFmpeg 不可用")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.logger.error(f"检查FFmpeg时出错: {e}")
            return False
    
    def validate_input_file(self, file_path: str) -> bool:
        """
        验证输入文件
        
        Args:
            file_path: 输入文件路径
            
        Returns:
            bool: 文件是否有效
        """
        if not os.path.exists(file_path):
            self.logger.error(f"输入文件不存在: {file_path}")
            return False
            
        if not file_path.lower().endswith('.mkv'):
            self.logger.warning(f"输入文件不是.mkv格式: {file_path}")
            
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            self.logger.error(f"输入文件为空: {file_path}")
            return False
            
        self.logger.info(f"输入文件验证通过: {file_path} (大小: {file_size / 1024 / 1024:.2f} MB)")
        return True
    
    def get_audio_info(self, file_path: str) -> Optional[dict]:
        """
        获取视频文件的音频信息
        
        Args:
            file_path: 视频文件路径
            
        Returns:
            dict: 音频信息，包含音轨数量等
        """
        try:
            cmd = [
                'ffprobe', 
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_streams',
                '-select_streams', 'a',
                file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                self.logger.error(f"获取音频信息失败: {result.stderr}")
                return None
                
            import json
            data = json.loads(result.stdout)
            audio_streams = data.get('streams', [])
            
            self.logger.info(f"检测到 {len(audio_streams)} 个音频轨道")
            for i, stream in enumerate(audio_streams):
                codec = stream.get('codec_name', 'unknown')
                channels = stream.get('channels', 'unknown')
                sample_rate = stream.get('sample_rate', 'unknown')
                self.logger.info(f"  轨道 {i}: {codec}, {channels} 声道, {sample_rate} Hz")
                
            return {
                'audio_track_count': len(audio_streams),
                'streams': audio_streams
            }
            
        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
            self.logger.error(f"获取音频信息时出错: {e}")
            return None
    
    def extract_audio_track(self, input_file: str, output_file: str, track_index: int) -> bool:
        """
        提取指定的音频轨道
        
        Args:
            input_file: 输入视频文件路径
            output_file: 输出音频文件路径
            track_index: 音轨索引 (0, 1, 2...)
            
        Returns:
            bool: 提取是否成功
        """
        try:
            # 构建ffmpeg命令
            cmd = [
                'ffmpeg',
                '-i', input_file,
                '-map', f'0:a:{track_index}',  # 选择指定音轨
                '-acodec', 'pcm_s16le',        # 无压缩PCM编码
                '-ar', '16000',                # 采样率16kHz (适合Whisper)
                '-ac', '1',                    # 单声道
                '-y',                          # 覆盖输出文件
                output_file
            ]
            
            self.logger.info(f"开始提取音轨 {track_index}: {output_file}")
            self.logger.debug(f"FFmpeg命令: {' '.join(cmd)}")
            
            # 执行命令
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                # 检查输出文件
                if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                    file_size = os.path.getsize(output_file)
                    self.logger.info(f"音轨 {track_index} 提取成功: {output_file} (大小: {file_size / 1024 / 1024:.2f} MB)")
                    return True
                else:
                    self.logger.error(f"音轨 {track_index} 提取失败: 输出文件为空或不存在")
                    return False
            else:
                self.logger.error(f"音轨 {track_index} 提取失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"音轨 {track_index} 提取超时")
            return False
        except Exception as e:
            self.logger.error(f"音轨 {track_index} 提取时出错: {e}")
            return False
    
    def extract_dual_tracks(self, input_file: str) -> Tuple[bool, list]:
        """
        提取双音轨
        
        Args:
            input_file: 输入视频文件路径
            
        Returns:
            Tuple[bool, list]: (是否成功, 输出文件列表)
        """
        # 验证输入文件
        if not self.validate_input_file(input_file):
            return False, []
        
        # 检查ffmpeg
        if not self.check_ffmpeg_available():
            return False, []
        
        # 获取音频信息
        audio_info = self.get_audio_info(input_file)
        if not audio_info:
            return False, []
        
        if audio_info['audio_track_count'] < 2:
            self.logger.error(f"音轨数量不足: 检测到 {audio_info['audio_track_count']} 个音轨，需要至少2个")
            return False, []
        
        # 准备输出文件路径 - 修正音轨对应关系
        input_path = Path(input_file)
        output_dir = input_path.parent
        base_name = input_path.stem
        
        output_files = [
            output_dir / f"{base_name}_自己.wav",    # 音轨0 = 自己的声音
            output_dir / f"{base_name}_对方.wav"     # 音轨1 = 对方的声音
        ]
        
        # 提取音轨
        success_count = 0
        extracted_files = []
        
        for i, output_file in enumerate(output_files):
            if self.extract_audio_track(input_file, str(output_file), i):
                success_count += 1
                extracted_files.append(str(output_file))
            else:
                self.logger.error(f"提取音轨 {i} 失败")
        
        if success_count == 2:
            self.logger.info("双音轨提取完成！")
            return True, extracted_files
        else:
            self.logger.error(f"部分音轨提取失败: 成功 {success_count}/2")
            return False, extracted_files


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="从OBS录制的.mkv视频文件中提取双音轨",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python extract_audio_tracks.py ./recordings/meeting_20250528_140000.mkv
  python extract_audio_tracks.py /path/to/video.mkv --log-level DEBUG
        """
    )
    
    parser.add_argument(
        'input_file',
        help='输入的.mkv视频文件路径'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='日志级别 (默认: INFO)'
    )
    
    args = parser.parse_args()
    
    # 创建提取器
    extractor = AudioTrackExtractor(log_level=args.log_level)
    
    try:
        # 执行提取
        success, output_files = extractor.extract_dual_tracks(args.input_file)
        
        if success:
            print("\n✅ 音频轨道提取成功！")
            print("📁 输出文件:")
            for i, file_path in enumerate(output_files):
                track_name = "自己" if i == 0 else "对方"
                print(f"  🎵 音轨 {i} ({track_name}): {file_path}")
            print("\n🎯 文件已准备好送入Whisper进行语音识别")
            sys.exit(0)
        else:
            print("\n❌ 音频轨道提取失败")
            if output_files:
                print("📁 部分成功的文件:")
                for file_path in output_files:
                    print(f"  🎵 {file_path}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 程序异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 