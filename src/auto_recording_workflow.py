#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化录制工作流程
完整流程：录制 → 转换 → 整理 → 提取音轨 → 转录

作者: VideoMeetingTranscript
创建时间: 2025-01-28
"""

import os
import sys
import argparse
import subprocess
import time
from pathlib import Path
from datetime import datetime


class AutoRecordingWorkflow:
    """自动化录制工作流程控制器"""
    
    def __init__(self, teacher_name: str, model: str = "small"):
        """
        初始化工作流程控制器
        
        Args:
            teacher_name: 老师名字，作为录制文件前缀
            model: Whisper模型大小
        """
        self.teacher_name = teacher_name
        self.model = model
        self.project_root = Path(__file__).parent.parent
        self.recordings_dir = self.project_root / "recordings"
        
        # 脚本路径
        self.obs_controller_script = self.project_root / "src" / "obs_controller.py"
        self.extract_audio_script = self.project_root / "src" / "extract_audio_tracks.py"
        self.whisper_script = self.project_root / "src" / "whisper_transcribe.py"
        
        print(f"🎬 自动化录制工作流程")
        print(f"👨‍🏫 老师名字: {teacher_name}")
        print(f"🤖 转录模型: {model}")
        print(f"📁 项目根目录: {self.project_root}")
        
    def check_scripts_exist(self):
        """检查所有必需的脚本是否存在"""
        scripts = [
            ("OBS控制器", self.obs_controller_script),
            ("音频提取器", self.extract_audio_script), 
            ("转录脚本", self.whisper_script)
        ]
        
        print("\n🔍 检查必需脚本...")
        for name, script_path in scripts:
            if script_path.exists():
                print(f"  ✅ {name}: {script_path}")
            else:
                print(f"  ❌ {name}: {script_path} (未找到)")
                return False
        return True
    
    def run_recording(self):
        """步骤1: 运行OBS录制"""
        print(f"\n📹 步骤1: 开始录制")
        print(f"🎯 录制前缀: {self.teacher_name}")
        print(f"⏺️  按 Ctrl+C 停止录制...")
        
        try:
            # 调用obs_controller.py进行录制
            cmd = [
                "python3", 
                str(self.obs_controller_script),
                self.teacher_name
            ]
            
            print(f"🔧 执行命令: {' '.join(cmd)}")
            
            # 运行录制脚本
            result = subprocess.run(cmd, cwd=str(self.project_root))
            
            if result.returncode == 0:
                print("✅ 录制阶段完成")
                return True
            else:
                print(f"❌ 录制失败，退出码: {result.returncode}")
                return False
                
        except KeyboardInterrupt:
            print("\n⚠️  录制被用户中断")
            return True
        except Exception as e:
            print(f"❌ 录制过程中出错: {e}")
            return False
    
    def find_latest_recording_folder(self):
        """查找最新的录制文件夹或文件"""
        print(f"\n🔍 步骤2: 查找录制文件")
        
        # 首先查找以teacher_name开头的文件夹（完整流程的情况）
        pattern = f"{self.teacher_name}_*"
        folders = list(self.recordings_dir.glob(pattern))
        
        if folders:
            # 按修改时间排序，获取最新的
            latest_folder = max(folders, key=lambda f: f.stat().st_mtime)
            
            # 查找文件夹中的MP4文件
            mp4_files = list(latest_folder.glob("*.mp4"))
            if mp4_files:
                latest_mp4 = max(mp4_files, key=lambda f: f.stat().st_mtime)
                print(f"📂 找到录制文件夹: {latest_folder.name}")
                print(f"🎬 找到视频文件: {latest_mp4.name}")
                return latest_mp4
        
        # 如果没找到文件夹，查找最新的原始录制文件（录制被中断的情况）
        print(f"📁 未找到以 '{self.teacher_name}' 开头的文件夹，查找最新的录制文件...")
        
        # 查找最新的MKV或MP4文件
        mkv_files = list(self.recordings_dir.glob("*.mkv"))
        mp4_files = list(self.recordings_dir.glob("*.mp4"))
        
        all_video_files = mkv_files + mp4_files
        if not all_video_files:
            print(f"❌ 在录制目录中未找到任何视频文件")
            return None
            
        # 获取最新的视频文件
        latest_video = max(all_video_files, key=lambda f: f.stat().st_mtime)
        
        # 检查文件是否是最近录制的（5分钟内）
        import time
        file_age = time.time() - latest_video.stat().st_mtime
        if file_age > 300:  # 5分钟
            print(f"⚠️  最新视频文件 '{latest_video.name}' 不是最近录制的（{file_age/60:.1f}分钟前）")
            print(f"如果这是你要处理的文件，请手动重命名为以 '{self.teacher_name}' 开头")
            return None
        
        print(f"🎬 找到最新录制文件: {latest_video.name}")
        print(f"📝 这个文件需要先进行重命名和转换")
        
        return latest_video
    
    def process_raw_recording(self, video_path):
        """处理原始录制文件：重命名、转换、整理"""
        print(f"\n🔄 步骤2.5: 处理原始录制文件")
        print(f"📁 原始文件: {video_path.name}")
        
        try:
            # 生成新的文件名
            from datetime import datetime
            now = datetime.now()
            new_filename = f"{self.teacher_name}_{now.strftime('%Y-%m-%d_%H-%M-%S')}.mkv"
            new_filepath = self.recordings_dir / new_filename
            
            # 重命名文件
            print(f"📝 重命名文件: {video_path.name} → {new_filename}")
            video_path.rename(new_filepath)
            
            if new_filepath.suffix.lower() == '.mkv':
                # 转换MKV为MP4
                print(f"🔄 转换MKV为MP4...")
                mp4_path = new_filepath.with_suffix('.mp4')
                
                cmd = [
                    'ffmpeg',
                    '-i', str(new_filepath),
                    '-map', '0',  # 映射所有输入流
                    '-c', 'copy',  # 直接复制所有流，不重新编码
                    '-y',  # 覆盖已存在的文件
                    str(mp4_path)
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"✅ 转换完成: {mp4_path.name}")
                    
                    # 创建文件夹并移动文件
                    folder_name = mp4_path.stem
                    target_folder = self.recordings_dir / folder_name
                    target_folder.mkdir(exist_ok=True)
                    
                    # 移动MP4文件到文件夹
                    mp4_in_folder = target_folder / mp4_path.name
                    mp4_path.rename(mp4_in_folder)
                    
                    # 删除MKV文件
                    if new_filepath.exists():
                        new_filepath.unlink()
                        print(f"🗑️  已删除MKV文件")
                    
                    print(f"📂 文件已整理到: {folder_name}/")
                    
                    return mp4_in_folder
                else:
                    print(f"❌ 转换失败: {result.stderr}")
                    return None
            else:
                # 已经是MP4格式，直接整理
                folder_name = new_filepath.stem
                target_folder = self.recordings_dir / folder_name
                target_folder.mkdir(exist_ok=True)
                
                mp4_in_folder = target_folder / new_filepath.name
                new_filepath.rename(mp4_in_folder)
                
                print(f"📂 文件已整理到: {folder_name}/")
                return mp4_in_folder
                
        except Exception as e:
            print(f"❌ 处理原始录制文件时出错: {e}")
            return None
    
    def extract_audio_tracks(self, mp4_path):
        """步骤3: 提取音频轨道"""
        print(f"\n🎵 步骤3: 提取音频轨道")
        print(f"📁 源文件: {mp4_path}")
        
        try:
            # 调用extract_audio_tracks.py提取音轨1和2
            cmd = [
                "python3",
                str(self.extract_audio_script),
                str(mp4_path),
                "--tracks", "1", "2"
            ]
            
            print(f"🔧 执行命令: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd, 
                cwd=str(self.project_root),
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ 音频轨道提取完成")
                print(result.stdout)
                
                # 返回生成的音频文件路径
                folder = mp4_path.parent
                base_name = mp4_path.stem
                self_audio = folder / f"{base_name}_自己.wav"
                other_audio = folder / f"{base_name}_对方.wav"
                
                return self_audio, other_audio
            else:
                print(f"❌ 音频提取失败: {result.stderr}")
                return None, None
                
        except Exception as e:
            print(f"❌ 音频提取过程中出错: {e}")
            return None, None
    
    def transcribe_audio(self, self_audio, other_audio):
        """步骤4: 转录音频"""
        print(f"\n🤖 步骤4: 转录音频")
        print(f"🎤 自己的音频: {self_audio.name}")
        print(f"🎤 对方的音频: {other_audio.name}")
        print(f"🧠 使用模型: {self.model}")
        
        try:
            # 生成输出文件路径
            output_path = self_audio.parent / f"{self_audio.stem.replace('_自己', '')}_transcription.json"
            
            # 调用whisper_transcribe.py进行转录
            cmd = [
                "python3",
                str(self.whisper_script),
                "--self-audio", str(self_audio),
                "--other-audio", str(other_audio),
                "--output", str(output_path),
                "--model", self.model
            ]
            
            print(f"🔧 执行命令: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                cwd=str(self.project_root),
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ 音频转录完成")
                print(result.stdout)
                return output_path
            else:
                print(f"❌ 转录失败: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"❌ 转录过程中出错: {e}")
            return None
    
    def show_final_results(self, mp4_path, transcription_path):
        """显示最终结果"""
        print(f"\n🎉 工作流程完成！")
        print(f"📂 录制文件夹: {mp4_path.parent}")
        print(f"📹 视频文件: {mp4_path.name}")
        
        if transcription_path and transcription_path.exists():
            print(f"📄 转录文件: {transcription_path.name}")
            
            # 显示转录统计
            try:
                import json
                with open(transcription_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                total_segments = len(data)
                self_segments = len([item for item in data if item['speaker'] == '自己'])
                other_segments = len([item for item in data if item['speaker'] == '对方'])
                
                print(f"📊 转录统计:")
                print(f"   总片段数: {total_segments}")
                print(f"   自己: {self_segments} 片段")
                print(f"   对方: {other_segments} 片段")
                
                if data:
                    duration = data[-1]['end'] - data[0]['start']
                    print(f"   录制时长: {duration:.1f} 秒")
                    
            except Exception as e:
                print(f"⚠️  读取转录文件统计时出错: {e}")
        
        print(f"\n🎯 所有文件位置: {mp4_path.parent}")
    
    def run_workflow(self):
        """运行完整工作流程"""
        start_time = time.time()
        
        # 检查脚本
        if not self.check_scripts_exist():
            print("❌ 缺少必需的脚本文件")
            return False
        
        try:
            # 步骤1: 录制
            if not self.run_recording():
                print("❌ 录制失败，工作流程终止")
                return False
            
                                     # 步骤2: 查找录制文件
            video_path = self.find_latest_recording_folder()
            if not video_path:
                print("❌ 未找到录制文件，工作流程终止")
                return False
            
            # 检查是否需要处理原始录制文件
            if video_path.parent == self.recordings_dir:
                # 文件在根目录，需要处理
                mp4_path = self.process_raw_recording(video_path)
                if not mp4_path:
                    print("❌ 处理原始录制文件失败，工作流程终止")
                    return False
            else:
                # 文件已经在子文件夹中，直接使用
                mp4_path = video_path
            
            # 步骤3: 提取音频
            self_audio, other_audio = self.extract_audio_tracks(mp4_path)
            if not self_audio or not other_audio:
                print("❌ 音频提取失败，工作流程终止")
                return False
            
            # 步骤4: 转录
            transcription_path = self.transcribe_audio(self_audio, other_audio)
            if not transcription_path:
                print("❌ 转录失败，但前面的步骤已完成")
                transcription_path = None
            
            # 显示最终结果
            self.show_final_results(mp4_path, transcription_path)
            
            total_time = time.time() - start_time
            print(f"\n⏱️  工作流程总耗时: {total_time/60:.1f} 分钟")
            
            return True
            
        except KeyboardInterrupt:
            print("\n⚠️  工作流程被用户中断")
            return False
        except Exception as e:
            print(f"❌ 工作流程中出现异常: {e}")
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="自动化录制工作流程：录制 → 转换 → 整理 → 提取音轨 → 转录",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python3 src/auto_recording_workflow.py SamT
  python3 src/auto_recording_workflow.py SamT medium
  python3 src/auto_recording_workflow.py "John Smith" large
  python3 src/auto_recording_workflow.py 王老师 small
        """
    )
    
    parser.add_argument(
        'teacher_name',
        help='老师名字，作为录制文件前缀'
    )
    
    parser.add_argument(
        'model',
        nargs='?',
        default='small',
        choices=['tiny', 'base', 'small', 'medium', 'large'],
        help='Whisper模型大小 (默认: small)'
    )
    
    args = parser.parse_args()
    
    # 创建工作流程控制器
    workflow = AutoRecordingWorkflow(
        teacher_name=args.teacher_name,
        model=args.model
    )
    
    # 运行工作流程
    success = workflow.run_workflow()
    
    if success:
        print("\n🎊 工作流程成功完成！")
        sys.exit(0)
    else:
        print("\n💥 工作流程未能完全完成")
        sys.exit(1)


if __name__ == "__main__":
    main() 