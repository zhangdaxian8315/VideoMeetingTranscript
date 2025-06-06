#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扫描recordings目录，生成会议列表JS文件
"""

import os
import json
import subprocess
from datetime import datetime
from pathlib import Path

def get_video_duration(video_path):
    """获取视频时长（分钟）"""
    try:
        # 使用ffprobe获取视频时长
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(video_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            duration = float(result.stdout.strip())
            return f"{int(duration/60)}分钟"
    except Exception as e:
        print(f"警告: 无法读取视频时长 {video_path}: {e}")
    return "未知"

def scan_recordings():
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    recordings_dir = project_root / "recordings"
    output_file = project_root / "web" / "recordings_list.js"
    
    # 确保recordings目录存在
    if not recordings_dir.exists():
        print(f"错误: recordings目录不存在: {recordings_dir}")
        return
    
    # 扫描目录
    meetings = []
    for item in recordings_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            # 解析文件夹名称
            try:
                # 假设文件夹名称格式为: Name_YYYY-MM-DD HH-MM-SS
                name, date_str = item.name.rsplit('_', 1)
                date = datetime.strptime(date_str, '%Y-%m-%d %H-%M-%S')
                
                # 查找视频文件
                video_files = list(item.glob('*.mkv')) + list(item.glob('*.mp4'))
                duration = "未知"
                if video_files:
                    # 读取第一个视频文件的时长
                    duration = get_video_duration(video_files[0])
                
                meetings.append({
                    "name": name,
                    "date": date.isoformat(),
                    "displayDate": date.strftime('%Y-%m-%d %H-%M-%S'),
                    "duration": duration,
                    "folderName": item.name,
                    "hasVideo": True,
                    "hasSubtitle": True
                })
            except Exception as e:
                print(f"警告: 无法解析文件夹名称 {item.name}: {e}")
    
    # 按日期排序
    meetings.sort(key=lambda x: x["date"], reverse=True)
    
    # 保存JS文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('const recordingsList = ')
        json.dump(meetings, f, ensure_ascii=False, indent=2)
        f.write(';')
    
    print(f"✅ 已扫描 {len(meetings)} 个会议记录")
    print(f"📝 结果已保存到: {output_file}")

if __name__ == "__main__":
    scan_recordings() 