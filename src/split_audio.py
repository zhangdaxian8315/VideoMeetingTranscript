import librosa
import numpy as np
import soundfile as sf
import os
from typing import List, Tuple
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def find_silence_segments(audio: np.ndarray, sr: int, 
                         min_silence_duration: float = 0.5,
                         silence_threshold: float = 0.01) -> List[Tuple[float, float]]:
    """
    查找音频中的静音段
    Returns: 静音段列表，每个元素为(开始时间, 结束时间)
    """
    energy = librosa.feature.rms(y=audio)[0]
    silent_frames = energy < silence_threshold
    silent_segments = []
    start_frame = None
    for i, is_silent in enumerate(silent_frames):
        if is_silent and start_frame is None:
            start_frame = i
        elif not is_silent and start_frame is not None:
            duration = (i - start_frame) * 512 / sr
            if duration >= min_silence_duration:
                silent_segments.append((start_frame * 512 / sr, i * 512 / sr))
            start_frame = None
    # 处理结尾静音
    if start_frame is not None:
        duration = (len(silent_frames) - start_frame) * 512 / sr
        if duration >= min_silence_duration:
            silent_segments.append((start_frame * 512 / sr, len(silent_frames) * 512 / sr))
    return silent_segments

def find_best_split_point(audio: np.ndarray, sr: int, target_time: float, search_window: float = 30.0) -> float:
    """
    在目标时间点附近找到最佳分割点（优先静音区，否则能量最低点）
    Args:
        audio: 音频数据
        sr: 采样率
        target_time: 目标分割时间点
        search_window: 搜索窗口大小（秒），默认30秒
    Returns: 最佳分割点的时间戳
    """
    start_frame = max(0, int((target_time - search_window) * sr))
    end_frame = min(len(audio), int((target_time + search_window) * sr))
    search_audio = audio[start_frame:end_frame]
    silent_segments = find_silence_segments(search_audio, sr, min_silence_duration=1.0, silence_threshold=0.015)
    if silent_segments:
        # 找到最接近目标时间的静音段
        best_segment = min(silent_segments, key=lambda x: abs((x[0] + x[1])/2 - search_window))
        # 返回静音段的中间点（加上窗口起点）
        return (best_segment[0] + best_segment[1]) / 2 + (target_time - search_window)
    # 没有静音段，找能量最低点
    energy = librosa.feature.rms(y=search_audio)[0]
    min_energy_frame = np.argmin(energy)
    return (start_frame + min_energy_frame * 512) / sr

def split_audio_file(input_file: str, output_dir: str, num_parts: int = 4) -> List[str]:
    """
    智能分割音频文件，分割点优先选静音区
    Returns: 分割后的音频文件路径列表
    """
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"📖 加载音频文件: {input_file}")
    audio, sr = librosa.load(input_file, sr=None)
    duration = len(audio) / sr
    target_length = duration / num_parts
    logger.info(f"⏱️ 音频总时长: {duration:.1f}秒")
    logger.info(f"📊 目标分片长度: {target_length:.1f}秒")
    
    # 找到分割点
    split_points = [0]
    for i in range(1, num_parts):
        target_time = i * target_length
        split_point = find_best_split_point(audio, sr, target_time, search_window=30.0)
        split_points.append(split_point)
    split_points.append(duration)
    
    # 验证分割点
    total_duration = 0
    for i in range(len(split_points)-1):
        segment_duration = split_points[i+1] - split_points[i]
        total_duration += segment_duration
        logger.info(f"分片 {i+1} 时长: {segment_duration:.1f}秒")
    
    # 验证总时长
    if abs(total_duration - duration) > 0.1:  # 允许0.1秒的误差
        logger.error(f"❌ 分片总时长 ({total_duration:.1f}秒) 与原音频时长 ({duration:.1f}秒) 不匹配！")
        raise ValueError("分片总时长与原音频时长不匹配")
    logger.info(f"✅ 分片总时长验证通过: {total_duration:.1f}秒")
    
    # 分割并保存音频
    output_files = []
    for i in range(num_parts):
        start_frame = int(split_points[i] * sr)
        end_frame = int(split_points[i+1] * sr)
        segment = audio[start_frame:end_frame]
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = os.path.join(output_dir, f"{base_name}_part{i+1}.wav")
        sf.write(output_file, segment, sr)
        output_files.append(output_file)
        logger.info(f"💾 保存分片 {i+1}: {output_file}")
        logger.info(f"⏱️ 分片时长: {len(segment)/sr:.1f}秒")
        logger.info(f"📍 时间戳: {split_points[i]:.1f}s - {split_points[i+1]:.1f}s")
    
    return output_files

def main():
    import argparse
    parser = argparse.ArgumentParser(description='分割音频文件')
    parser.add_argument('--input', required=True, help='输入音频文件路径')
    parser.add_argument('--output-dir', required=True, help='输出目录')
    parser.add_argument('--num-parts', type=int, default=4, help='分割数量')
    args = parser.parse_args()
    split_audio_file(args.input, args.output_dir, args.num_parts)

if __name__ == '__main__':
    main() 