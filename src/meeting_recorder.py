#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会议录制和音频提取整合工具
"""

import os
import sys
import subprocess
import time
from datetime import datetime
from pathlib import Path


def rename_latest_recording(recordings_dir):
    """重命名最新的录制文件为带"会议录制"前缀的格式"""
    try:
        # 查找最新的录制文件（所有.mkv文件）
        recording_files = list(recordings_dir.glob("*.mkv"))
        if recording_files:
            # 按修改时间排序，获取最新的文件
            latest_file = max(recording_files, key=lambda f: f.stat().st_mtime)
            
            # 检查文件是否已经有"会议录制"前缀
            if latest_file.name.startswith("会议录制_"):
                return latest_file
            
            # 检查文件是否是刚刚录制的（5分钟内）
            file_age = time.time() - latest_file.stat().st_mtime
            if file_age > 300:  # 5分钟
                return latest_file
            
            # 生成新的文件名
            file_timestamp = datetime.fromtimestamp(latest_file.stat().st_mtime)
            new_filename = f"会议录制_{file_timestamp.strftime('%Y-%m-%d_%H-%M-%S')}.mkv"
            new_filepath = recordings_dir / new_filename
            
            # 检查新文件名是否已存在
            if new_filepath.exists():
                # 添加序号避免冲突
                counter = 1
                while new_filepath.exists():
                    new_filename = f"会议录制_{file_timestamp.strftime('%Y-%m-%d_%H-%M-%S')}_{counter}.mkv"
                    new_filepath = recordings_dir / new_filename
                    counter += 1
            
            # 执行重命名
            latest_file.rename(new_filepath)
            return new_filepath
            
        return None
        
    except Exception as e:
        print(f"重命名录制文件时出错: {e}")
        return None


def main():
    """主函数"""
    project_root = Path(__file__).parent.parent
    recordings_dir = project_root / "recordings"
    obs_script = project_root / "src" / "obs_controller.py"
    extract_script = project_root / "src" / "extract_audio_tracks.py"
    
    # 调用OBS录制脚本
    try:
        subprocess.run([sys.executable, str(obs_script)], cwd=str(project_root))
    except KeyboardInterrupt:
        pass  # 忽略Ctrl+C中断，继续执行音频提取
    
    # 等待一下确保文件写入完成
    time.sleep(2)
    
    # 手动重命名最新的录制文件
    latest_file = rename_latest_recording(recordings_dir)
    
    # 如果重命名失败，尝试查找其他录制文件
    if not latest_file:
        recording_files = list(recordings_dir.glob("会议录制_*.mkv"))
        if not recording_files:
            recording_files = list(recordings_dir.glob("录制_*.mkv"))
        if not recording_files:
            recording_files = list(recordings_dir.glob("*.mkv"))
        
        if recording_files:
            latest_file = max(recording_files, key=lambda f: f.stat().st_mtime)
    
    # 调用音频提取脚本
    if latest_file:
        subprocess.run([sys.executable, str(extract_script), str(latest_file)], cwd=str(project_root))


if __name__ == "__main__":
    main() 