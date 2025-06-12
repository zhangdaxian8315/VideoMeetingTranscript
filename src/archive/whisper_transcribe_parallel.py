#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用OpenAI Whisper进行语音识别并生成结构化JSON文件 (简单并行优化版本)
基于原始脚本的简单并行化处理
"""

import os
import sys
import json
import argparse
import time
from pathlib import Path
import ssl
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

# 绕过SSL证书验证
ssl._create_default_https_context = ssl._create_unverified_context

import whisper


def transcribe_audio(audio_file, speaker_name, model):
    """
    使用Whisper转录音频文件 (原始函数的并行版本)
    
    Args:
        audio_file: 音频文件路径
        speaker_name: 说话人名称 ("自己" 或 "对方")
        model: Whisper模型
    
    Returns:
        list: 转录结果列表，每个元素包含start, end, text, speaker
    """
    print(f"🎵 正在转录 {speaker_name} 的音频: {audio_file.name}")
    
    # 使用Whisper进行转录，包含时间戳
    result = model.transcribe(str(audio_file), word_timestamps=True, language='en')
    
    transcriptions = []
    
    # 处理segments（句子级别的时间戳）
    for segment in result['segments']:
        text = segment['text'].strip()
        # 过滤掉空的或太短的文本
        if text and len(text) > 0:
            transcriptions.append({
                "start": round(segment['start'], 2),
                "end": round(segment['end'], 2),
                "text": text,
                "speaker": speaker_name
            })
    
    print(f"✅ {speaker_name} 转录完成，共 {len(transcriptions)} 个片段")
    return transcriptions


def merge_and_sort_transcriptions(transcriptions_list):
    """
    合并多个转录结果并按时间戳排序 (原始函数)
    
    Args:
        transcriptions_list: 转录结果列表的列表
    
    Returns:
        list: 合并并排序后的转录结果
    """
    # 合并所有转录结果
    all_transcriptions = []
    for transcriptions in transcriptions_list:
        all_transcriptions.extend(transcriptions)
    
    # 按开始时间排序
    all_transcriptions.sort(key=lambda x: x['start'])
    
    return all_transcriptions


def find_audio_files(recordings_dir):
    """
    查找最新的音频文件对 (原始函数)
    
    Args:
        recordings_dir: 录制目录
    
    Returns:
        tuple: (自己.wav文件路径, 对方.wav文件路径) 或 (None, None)
    """
    # 查找所有的音频文件
    self_files = list(recordings_dir.glob("*_自己.wav"))
    other_files = list(recordings_dir.glob("*_对方.wav"))
    
    if not self_files or not other_files:
        return None, None
    
    # 获取最新的文件对（基于文件名中的时间戳）
    self_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    other_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    
    # 找到匹配的文件对
    for self_file in self_files:
        base_name = self_file.name.replace("_自己.wav", "")
        other_file = recordings_dir / f"{base_name}_对方.wav"
        if other_file.exists():
            return self_file, other_file
    
    return None, None


def main():
    """主函数 - 基于原始脚本的并行化版本"""
    parser = argparse.ArgumentParser(description="使用Whisper进行语音识别并生成JSON文件 (并行版本)")
    parser.add_argument("--self-audio", type=str, help="自己的音频文件路径")
    parser.add_argument("--other-audio", type=str, help="对方的音频文件路径")
    parser.add_argument("--output", type=str, default="output.json", help="输出JSON文件路径")
    parser.add_argument("--model", type=str, default="small", help="Whisper模型大小 (tiny, base, small, medium, large)")
    
    args = parser.parse_args()
    
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    recordings_dir = project_root / "recordings"
    
    # 确定音频文件路径
    if args.self_audio and args.other_audio:
        self_audio = Path(args.self_audio)
        other_audio = Path(args.other_audio)
    else:
        print("🔍 自动查找最新的音频文件...")
        self_audio, other_audio = find_audio_files(recordings_dir)
        
        if not self_audio or not other_audio:
            print("❌ 未找到音频文件对")
            print("请确保recordings目录中有 *_自己.wav 和 *_对方.wav 文件")
            print("或者使用 --self-audio 和 --other-audio 参数指定文件路径")
            sys.exit(1)
    
    # 检查文件是否存在
    if not self_audio.exists():
        print(f"❌ 自己的音频文件不存在: {self_audio}")
        sys.exit(1)
    
    if not other_audio.exists():
        print(f"❌ 对方的音频文件不存在: {other_audio}")
        sys.exit(1)
    
    print(f"📁 找到音频文件:")
    print(f"  🎤 自己: {self_audio.name}")
    print(f"  🎤 对方: {other_audio.name}")
    
    # 加载Whisper模型
    print(f"\n🤖 加载Whisper模型: {args.model}")
    try:
        model = whisper.load_model(args.model)
        print("✅ 模型加载成功")
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        sys.exit(1)
    
    # 并行转录音频文件 (这是唯一的改动)
    print("\n🎵 开始并行语音识别...")
    
    try:
        start_time = time.time()
        
        # 使用ThreadPoolExecutor并行处理两个音频文件
        with ThreadPoolExecutor(max_workers=2) as executor:
            # 提交两个转录任务
            future_self = executor.submit(transcribe_audio, self_audio, "自己", model)
            future_other = executor.submit(transcribe_audio, other_audio, "对方", model)
            
            # 等待结果，添加错误处理
            try:
                self_transcriptions = future_self.result()
            except Exception as e:
                print(f"⚠️ 自己的音频转录失败: {e}")
                self_transcriptions = []
            
            try:
                other_transcriptions = future_other.result()
            except Exception as e:
                print(f"⚠️ 对方的音频转录失败: {e}")
                other_transcriptions = []
        
        parallel_time = time.time() - start_time
        print(f"⚡ 并行转录耗时: {parallel_time:.1f}秒")
        
        # 生成单独的输出文件路径
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = project_root / output_path
        
        # 生成单独文件的路径
        output_dir = output_path.parent
        output_stem = output_path.stem
        output_suffix = output_path.suffix
        
        self_output_path = output_dir / f"{output_stem}_自己{output_suffix}"
        other_output_path = output_dir / f"{output_stem}_对方{output_suffix}"
        
        # 保存单独的转录结果
        print("\n💾 保存单独转录结果...")
        
        with open(self_output_path, 'w', encoding='utf-8') as f:
            json.dump(self_transcriptions, f, ensure_ascii=False, indent=2)
        print(f"📄 自己的转录: {self_output_path}")
        
        with open(other_output_path, 'w', encoding='utf-8') as f:
            json.dump(other_transcriptions, f, ensure_ascii=False, indent=2)
        print(f"📄 对方的转录: {other_output_path}")
        
        # 合并并排序
        print("\n🔄 合并和排序转录结果...")
        all_transcriptions = merge_and_sort_transcriptions([self_transcriptions, other_transcriptions])
        
        # 输出合并的JSON文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_transcriptions, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 转录完成！")
        print(f"📄 合并文件: {output_path}")
        print(f"📊 总计 {len(all_transcriptions)} 个语音片段")
        print(f"📈 统计: 自己 {len(self_transcriptions)} 片段, 对方 {len(other_transcriptions)} 片段")
        
        # 显示前几个结果作为预览
        if all_transcriptions:
            print("\n📝 转录预览:")
            for i, item in enumerate(all_transcriptions[:5]):
                print(f"  {i+1}. [{item['start']:.1f}s-{item['end']:.1f}s] {item['speaker']}: {item['text']}")
            
            if len(all_transcriptions) > 5:
                print(f"  ... 还有 {len(all_transcriptions) - 5} 个片段")
        
    except Exception as e:
        print(f"❌ 转录过程中出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 