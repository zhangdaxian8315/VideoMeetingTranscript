#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用OpenAI Whisper进行语音识别并生成结构化JSON文件
"""

import os
import sys
import json
import argparse
from pathlib import Path
import ssl
import urllib.request
import time
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor

# 绕过SSL证书验证
ssl._create_default_https_context = ssl._create_unverified_context

import whisper


def format_time(seconds):
    """格式化时间显示"""
    if seconds < 60:
        return f"{seconds:.1f}秒"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}分钟"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}小时"


def transcribe_audio(audio_file, speaker_name, model):
    """
    使用Whisper转录音频文件
    
    Args:
        audio_file: 音频文件路径
        speaker_name: 说话人名称 ("自己" 或 "对方")
        model: Whisper模型
    
    Returns:
        list: 转录结果列表，每个元素包含start, end, text, speaker
    """
    print(f"🎵 正在转录 {speaker_name} 的音频: {audio_file.name}")
    
    # 获取音频文件信息
    file_size = os.path.getsize(audio_file) / (1024 * 1024)  # MB
    print(f"📊 音频文件大小: {file_size:.1f} MB")
    
    # 使用Whisper进行转录，包含时间戳
    print(f"🔄 开始Whisper转录处理...")
    start_time = time.time()
    
    try:
        # 获取音频时长
        import librosa
        audio_duration = librosa.get_duration(path=str(audio_file))
        print(f"⏱️ 音频时长: {format_time(audio_duration)}")
        
        # 预处理阶段
        print(f"🔧 开始音频预处理...")
        preprocess_start = time.time()
        
        # 执行转录
        print(f"🤖 开始模型推理...")
        inference_start = time.time()
        result = model.transcribe(
            str(audio_file),
            word_timestamps=True,
            language='en',
            beam_size=5,
            temperature=0.4,
            condition_on_previous_text=False,
            no_speech_threshold=0.2,
            logprob_threshold=-2.0
        )
        
        inference_time = time.time() - inference_start
        processing_time = time.time() - start_time
        print(f"⏱️ 模型推理耗时: {format_time(inference_time)}")
        print(f"⏱️ 总处理耗时: {format_time(processing_time)}")
        
    except Exception as e:
        print(f"❌ Whisper转录失败: {e}")
        raise e
    
    print(f"📝 开始处理转录结果...")
    transcriptions = []
    
    # 处理segments（句子级别的时间戳）
    total_segments = len(result.get('segments', []))
    meaningful_segments = 0
    print(f"📋 检测到 {total_segments} 个语音段落")
    
    process_start_time = time.time()
    
    for i, segment in enumerate(result['segments']):
        # 每10个段落显示进度
        if i % 10 == 0 and i > 0:
            print(f"📈 处理进度: {i}/{total_segments} ({i/total_segments*100:.1f}%)")
        
        text = segment['text'].strip()
        # 检查是否有实际内容（不是"Yeah"等无意义内容）
        if text.lower() not in ["yeah", "um", "uh", "ah", "mm", "hmm"]:
            meaningful_segments += 1
        
        # 过滤掉空的或太短的文本
        if text and len(text) > 0:
            transcriptions.append({
                "start": round(segment['start'], 2),
                "end": round(segment['end'], 2),
                "text": text,
                "speaker": speaker_name
            })
    
    process_time = time.time() - process_start_time
    print(f"✅ {speaker_name} 转录完成，共 {len(transcriptions)} 个片段")
    print(f"📊 统计: 总段落数 {total_segments}, 有意义段落 {meaningful_segments}")
    print(f"⏱️ 结果处理耗时: {format_time(process_time)}")
    print(f"⏱️ 总耗时: {format_time(processing_time + process_time)}")
    return transcriptions


def merge_and_sort_transcriptions(transcriptions_list):
    """
    合并多个转录结果并按时间戳排序
    
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
    查找最新的音频文件对
    
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
    """主函数"""
    total_start_time = time.time()
    
    parser = argparse.ArgumentParser(description="使用Whisper进行语音识别并生成JSON文件")
    parser.add_argument("--self-audio", type=str, help="自己的音频文件路径")
    parser.add_argument("--other-audio", type=str, help="对方的音频文件路径")
    parser.add_argument("--single-audio", type=str, help="单独转录一个音频文件路径")
    parser.add_argument("--speaker-name", type=str, default="说话人", help="单独转录时的说话人名称")
    parser.add_argument("--output", type=str, default="output.json", help="输出JSON文件路径")
    parser.add_argument("--model", type=str, default="small", help="Whisper模型大小 (tiny, base, small, medium, large)")
    
    args = parser.parse_args()
    
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    recordings_dir = project_root / "recordings"
    
    # 检查是否是单音频模式
    if args.single_audio:
        # 单音频模式
        single_audio = Path(args.single_audio)
        
        if not single_audio.exists():
            print(f"❌ 音频文件不存在: {single_audio}")
            sys.exit(1)
        
        print(f"📁 单音频转录模式:")
        print(f"  🎤 音频文件: {single_audio.name}")
        print(f"  👤 说话人: {args.speaker_name}")
        
        # 加载Whisper模型
        print(f"\n🤖 加载Whisper模型: {args.model}")
        print(f"⏳ 正在加载模型，请稍候...")
        model_load_start = time.time()
        try:
            model = whisper.load_model(args.model)
            model_load_time = time.time() - model_load_start
            print(f"✅ 模型加载成功 (耗时: {format_time(model_load_time)})")
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            sys.exit(1)
        
        # 转录音频文件
        print("\n🎵 开始语音识别...")
        print(f"🎯 目标文件: {single_audio}")
        print(f"👤 说话人标识: {args.speaker_name}")
        print(f"🔧 使用模型: {args.model}")
        
        try:
            transcriptions = transcribe_audio(single_audio, args.speaker_name, model)
            
            # 输出到JSON文件
            output_path = Path(args.output)
            if not output_path.is_absolute():
                output_path = project_root / output_path
            
            save_start_time = time.time()
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(transcriptions, f, ensure_ascii=False, indent=2)
            save_time = time.time() - save_start_time
            
            print(f"\n✅ 转录完成！")
            print(f"📄 输出文件: {output_path}")
            print(f"📊 总计 {len(transcriptions)} 个语音片段")
            print(f"⏱️ 保存文件耗时: {format_time(save_time)}")
            
            # 显示前几个结果作为预览
            if transcriptions:
                print("\n📝 转录预览:")
                for i, item in enumerate(transcriptions[:5]):
                    print(f"  {i+1}. [{item['start']:.1f}s-{item['end']:.1f}s] {item['speaker']}: {item['text']}")
                
                if len(transcriptions) > 5:
                    print(f"  ... 还有 {len(transcriptions) - 5} 个片段")
            
        except Exception as e:
            print(f"❌ 转录过程中出错: {e}")
            sys.exit(1)
        
        total_time = time.time() - total_start_time
        print(f"\n⏱️ 总耗时: {format_time(total_time)}")
        return
    
    # 双音频模式
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
            print("或者使用 --single-audio 参数转录单个音频文件")
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
    print(f"⏳ 正在加载模型，请稍候...")
    model_load_start = time.time()
    try:
        model = whisper.load_model(args.model)
        model_load_time = time.time() - model_load_start
        print(f"✅ 模型加载成功 (耗时: {format_time(model_load_time)})")
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        sys.exit(1)
    
    # 转录音频文件
    print("\n🎵 开始语音识别...")
    
    try:
        # 使用 ProcessPoolExecutor 并行转录两个音频
        with ProcessPoolExecutor(max_workers=2) as executor:
            self_future = executor.submit(transcribe_audio, self_audio, "自己", model)
            other_future = executor.submit(transcribe_audio, other_audio, "对方", model)
            
            # 等待两个转录任务完成
            self_transcriptions = self_future.result()
            other_transcriptions = other_future.result()
        
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
        save_start_time = time.time()
        
        with open(self_output_path, 'w', encoding='utf-8') as f:
            json.dump(self_transcriptions, f, ensure_ascii=False, indent=2)
        print(f"📄 自己的转录: {self_output_path}")
        
        with open(other_output_path, 'w', encoding='utf-8') as f:
            json.dump(other_transcriptions, f, ensure_ascii=False, indent=2)
        print(f"📄 对方的转录: {other_output_path}")
        
        # 合并并排序
        print("\n🔄 合并和排序转录结果...")
        merge_start_time = time.time()
        all_transcriptions = merge_and_sort_transcriptions([self_transcriptions, other_transcriptions])
        merge_time = time.time() - merge_start_time
        print(f"⏱️ 合并耗时: {format_time(merge_time)}")
        
        # 输出合并的JSON文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_transcriptions, f, ensure_ascii=False, indent=2)
        
        save_time = time.time() - save_start_time
        print(f"⏱️ 保存文件耗时: {format_time(save_time)}")
        
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
    
    total_time = time.time() - total_start_time
    print(f"\n⏱️ 总耗时: {format_time(total_time)}")


if __name__ == "__main__":
    main() 