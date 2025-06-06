import os
import json
import time
import logging
import argparse
from typing import List, Dict
from concurrent.futures import ProcessPoolExecutor, as_completed
import whisper

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def transcribe_segment(args: tuple) -> Dict:
    """
    转录单个音频片段
    
    Args:
        args: (音频分片文件路径, 模型名称, 片段索引, 起始时间)
    
    Returns:
        转录结果字典
    """
    audio_file, model_name, segment_index, segment_start_time = args
    
    # 加载模型
    logger.info(f"🤖 进程 {segment_index} 加载Whisper模型: {model_name}")
    model = whisper.load_model(model_name)
    
    # 转录
    logger.info(f"🎵 进程 {segment_index} 开始转录: {audio_file}")
    result = model.transcribe(
        audio_file,
        language="en",
        no_speech_threshold=0.5,
        condition_on_previous_text=True,
        compression_ratio_threshold=2.4
    )
    
    # 调整时间戳
    for segment in result["segments"]:
        segment["start"] += segment_start_time
        segment["end"] += segment_start_time
    
    logger.info(f"✅ 进程 {segment_index} 完成转录: {audio_file}")
    return result

def parallel_transcribe(audio_parts: List[str], 
                       model: str = "medium",
                       output_dir: str = "output") -> Dict:
    """
    并行转录音频分片
    
    Args:
        audio_parts: 音频分片文件路径列表
        model: Whisper模型名称
        output_dir: 输出目录
    
    Returns:
        合并后的转录结果
    """
    total_start_time = time.time()
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 准备转录任务
    tasks = []
    for i, audio_file in enumerate(audio_parts):
        # 计算起始时间（假设每个分片长度相等）
        segment_start_time = i * 720  # 假设每个分片12分钟（720秒）
        tasks.append((audio_file, model, f"part_{i}", segment_start_time))
    
    # 创建进程池
    num_processes = min(len(tasks), os.cpu_count())
    logger.info(f"🔄 创建进程池: {num_processes}个进程")
    
    # 执行转录任务
    results = []
    with ProcessPoolExecutor(max_workers=num_processes) as executor:
        # 提交所有任务
        future_to_task = {executor.submit(transcribe_segment, task): task for task in tasks}
        
        # 处理完成的任务
        for future in as_completed(future_to_task):
            task = future_to_task[future]
            try:
                result = future.result()
                results.append(result)
                logger.info(f"✅ 完成转录: {task[0]}")
            except Exception as e:
                logger.error(f"❌ 转录失败: {task[0]}, 错误: {str(e)}")
    
    # 合并结果
    logger.info("🔄 合并转录结果...")
    merged_segments = []
    for result in results:
        merged_segments.extend(result["segments"])
    
    # 按时间排序
    merged_segments.sort(key=lambda x: x["start"])
    
    # 保存结果
    output = {
        "segments": merged_segments,
        "model": model
    }
    
    output_file = os.path.join(output_dir, "transcription.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    total_time = time.time() - total_start_time
    logger.info(f"✅ 转录完成！")
    logger.info(f"📄 结果保存到: {output_file}")
    logger.info(f"⏱️ 总耗时: {total_time/60:.1f}分钟")
    
    return output

def main():
    parser = argparse.ArgumentParser(description='并行转录音频分片')
    parser.add_argument('--audio-parts', required=True, nargs='+', help='音频分片文件路径列表')
    parser.add_argument('--model', default='medium', help='Whisper模型名称')
    parser.add_argument('--output-dir', default='output', help='输出目录')
    args = parser.parse_args()
    
    parallel_transcribe(
        args.audio_parts,
        args.model,
        args.output_dir
    )

if __name__ == '__main__':
    main() 