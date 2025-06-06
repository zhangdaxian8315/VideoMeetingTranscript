#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from pathlib import Path

def merge_continuous_segments(transcriptions):
    """
    合并同一说话人的连续片段，但保持对话的自然顺序
    
    Args:
        transcriptions: 转录结果列表
    
    Returns:
        list: 合并后的转录结果
    """
    # 按时间排序所有片段
    sorted_segments = sorted(transcriptions, key=lambda x: x['start'])
    
    # 合并后的结果
    merged_segments = []
    current = sorted_segments[0]
    
    for next_seg in sorted_segments[1:]:
        # 如果是同一个说话人
        if current['speaker'] == next_seg['speaker']:
            # 检查时间间隔
            if next_seg['start'] - current['end'] < 5.5:
                # 检查是否有对方的话穿插
                has_interruption = False
                for seg in sorted_segments:
                    # 如果找到对方的话，且时间戳在当前片段和下一个片段之间
                    if (seg['speaker'] != current['speaker'] and
                        seg['start'] > current['start'] and
                        seg['end'] < next_seg['end']):
                        has_interruption = True
                        break
                
                # 如果没有对方的话穿插，则合并
                if not has_interruption:
                    current = {
                        'start': current['start'],
                        'end': next_seg['end'],
                        'text': current['text'] + ' ' + next_seg['text'],
                        'speaker': current['speaker']
                    }
                    continue
        
        # 如果不能合并，保存当前片段，并开始新的片段
        merged_segments.append(current)
        current = next_seg
    
    # 添加最后一个片段
    merged_segments.append(current)
    
    # 按开始时间排序
    merged_segments.sort(key=lambda x: x['start'])
    return merged_segments

def main():
    # 读取原始JSON文件
    input_file = Path("debug_audio/SamT_完整_优化参数_合并.json")
    output_file = Path("debug_audio/SamT_完整_优化参数_合并_优化.json")
    
    print(f"📖 读取文件: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        transcriptions = json.load(f)
    
    print(f"📊 原始片段数: {len(transcriptions)}")
    
    # 合并连续片段
    print("🔄 合并连续片段...")
    merged_transcriptions = merge_continuous_segments(transcriptions)
    
    print(f"📊 合并后片段数: {len(merged_transcriptions)}")
    print(f"📈 减少了 {len(transcriptions) - len(merged_transcriptions)} 个片段")
    
    # 保存结果
    print(f"💾 保存到: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged_transcriptions, f, ensure_ascii=False, indent=2)
    
    # 显示前几个结果作为预览
    print("\n📝 合并后预览:")
    for i, item in enumerate(merged_transcriptions[:5]):
        print(f"  {i+1}. [{item['start']:.1f}s-{item['end']:.1f}s] {item['speaker']}: {item['text']}")

if __name__ == "__main__":
    main() 