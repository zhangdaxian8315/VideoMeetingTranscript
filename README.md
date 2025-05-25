# 视频会议录制与学习系统

这是一个用于录制视频会议并进行后续学习的系统。目前实现了第一阶段：通过 Python 脚本控制 OBS 进行会议录制。

## 第一阶段：会议录制

### 前置要求

1. 安装 OBS Studio
2. 安装 OBS WebSocket 插件
3. Python 3.7+

### 安装步骤

1. 安装 OBS WebSocket 插件：
   - 访问 [OBS WebSocket 插件页面](https://github.com/obsproject/obs-websocket/releases)
   - 下载最新版本的 macOS 安装包
   - 安装插件

2. 配置 OBS WebSocket：
   - 打开 OBS
   - 进入 Tools -> WebSocket Server Settings
   - 设置密码（请记住这个密码）
   - 确保服务器已启用

3. 安装 Python 依赖：
```bash
pip install -r requirements.txt
```

4. 配置录制设置：
   - 打开 `config/config.yaml`
   - 修改 WebSocket 密码
   - 根据需要调整其他设置

### 使用方法

1. 在 OBS 中设置好录制场景（默认场景名为 "MeetingCapture"）
2. 运行录制脚本：
```bash
python src/recorder/obs_controller.py
```

3. 录制控制：
   - 脚本会自动开始录制
   - 按 Ctrl+C 可以手动停止录制
   - 如果设置了 `auto_stop: true`，达到最大时长后会自动停止

### 输出

录制的视频文件将保存在 `output/recordings` 目录下，文件名格式为：`meeting_YYYYMMDD_HHMMSS.mp4` 