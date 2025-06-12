# Archive 文件夹

这个文件夹包含了一些暂时不使用的脚本文件，主要是实验性质或者备用的实现。

## 文件说明

### 转录相关
- `whisper_transcribe_parallel.py` - 简单并行版本的Whisper转录脚本
- `faster_whisper_transcribe.py` - 使用Faster-Whisper库的转录脚本（更快的实现）
- `parallel_transcribe.py` - 进程池并行转录实现

### 工具脚本
- `meeting_recorder.py` - 早期的会议录制整合工具
- `merge_segments.py` - 合并转录片段的工具

## 使用说明

这些文件已被更新的实现替代：
- 主要转录：使用 `../whisper_transcribe.py`
- 自动化工作流程：使用 `../auto_recording_workflow.py`
- OBS控制：使用 `../obs_controller.py`
- 音频提取：使用 `../extract_audio_tracks.py`

如果需要使用这些脚本，可以移回上级目录或直接在这里运行。 