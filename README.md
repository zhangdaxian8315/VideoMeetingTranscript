# 视频会议转录系统

一个完整的视频会议录制、转录和播放系统，包含OBS录制控制、Whisper语音识别和网页播放器。

## 📁 项目结构

```
VideoMeetingTranscript/
├── web/                    # 前端UI文件
│   ├── index.html         # 会议记录中心首页
│   ├── player.html        # 视频播放器页面
│   ├── script.js          # 播放器JavaScript逻辑
│   └── style.css          # 样式文件
├── src/                   # Python脚本
│   ├── obs_controller.py  # OBS录制控制
│   ├── whisper_transcribe.py # Whisper转录
│   └── meeting_recorder.py   # 整合录制脚本
├── recordings/            # 录制文件存储目录（被git忽略）
│   ├── 会议名_日期_时间/
│   │   ├── 视频文件.mkv
│   │   ├── 音频文件_自己.wav
│   │   ├── 音频文件_对方.wav
│   │   └── transcript/
│   │       └── merged.json
├── config/               # 配置文件
├── output/              # 输出文件
├── requirements.txt     # Python依赖
└── README.md           # 项目说明
```

## 🚀 快速开始

### 1. 环境准备
```bash
# 安装Python依赖
pip install -r requirements.txt

# 安装Whisper（如果遇到SSL问题）
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org openai-whisper
```

### 2. 录制会议
```bash
# 启动OBS并开始录制
python src/meeting_recorder.py
```

### 3. 转录音频
```bash
# 转录最新的录制文件
python src/whisper_transcribe.py

# 或指定特定文件
python src/whisper_transcribe.py --audio1 path/to/audio1.wav --audio2 path/to/audio2.wav
```

### 4. 播放和查看
1. 打开 `web/index.html` 查看所有会议记录
2. 点击会议卡片进入播放器页面
3. 手动加载对应的字幕文件（JSON格式）

## 🎯 主要功能

### 录制系统
- ✅ 自动控制OBS录制开始/停止
- ✅ 双音轨录制（自己+对方）
- ✅ 自动文件重命名和组织
- ✅ 音频提取和格式转换

### 转录系统
- ✅ Whisper语音识别
- ✅ 双音轨分别转录
- ✅ 说话人标识
- ✅ 时间戳同步
- ✅ JSON格式输出

### 播放系统
- ✅ 视频播放器
- ✅ 字幕显示和同步
- ✅ 点击字幕跳转
- ✅ 说话人区分显示
- ✅ 键盘快捷键支持

## ⌨️ 快捷键

- **空格键**: 播放/暂停
- **左右箭头**: 快退/快进 5秒
- **点击字幕**: 跳转到对应时间点

## 🔧 配置说明

### OBS设置
- WebSocket服务器: `localhost:4455`
- 密码: `zhang8315`
- 录制格式: MKV (双音轨)

### Whisper设置
- 模型: `small`
- 语言: 英文 (`en`)
- 输出格式: 16kHz单声道PCM WAV

## 📝 文件格式

### 转录JSON格式
```json
[
  {
    "start": 0.0,
    "end": 2.5,
    "text": "Hello, how are you?",
    "speaker": "自己"
  },
  {
    "start": 3.0,
    "end": 5.2,
    "text": "I'm fine, thank you.",
    "speaker": "对方"
  }
]
```

## 🚫 .gitignore

项目已配置忽略以下文件：
- `recordings/` 目录（大型视频文件）
- Python缓存文件
- 系统临时文件
- IDE配置文件

## 🛠️ 故障排除

### 常见问题
1. **OBS连接失败**: 检查WebSocket设置和密码
2. **Whisper安装失败**: 使用`--trusted-host`参数
3. **视频无法播放**: 检查文件路径和格式
4. **字幕无法加载**: 使用手动加载功能

### 性能参考
- 24分钟视频处理时间: ~3分钟
- 转录速度: 约8倍实时速度
- 支持的视频格式: MKV, MP4
- 支持的音频格式: WAV, MP3 