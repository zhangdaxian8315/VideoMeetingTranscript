import os
import time
import socket
import subprocess
from datetime import datetime
from obsws_python import ReqClient

def check_port(host, port):
    """检查端口是否可访问"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0

def is_obs_running():
    """检查 OBS 是否正在运行"""
    try:
        result = subprocess.run(['pgrep', '-f', 'OBS'], capture_output=True, text=True)
        return len(result.stdout.strip()) > 0
    except Exception:
        return False

def start_obs():
    """启动 OBS Studio"""
    try:
        print("正在启动 OBS Studio...")
        # 在 macOS 上启动 OBS
        subprocess.Popen(['open', '-a', 'OBS'])
        
        # 等待 OBS 启动
        print("等待 OBS 启动...")
        max_wait_time = 30  # 最多等待30秒
        wait_time = 0
        
        while wait_time < max_wait_time:
            if is_obs_running():
                print("OBS 已启动")
                # 再等待几秒让 WebSocket 服务器启动
                time.sleep(5)
                return True
            time.sleep(1)
            wait_time += 1
            
        print("OBS 启动超时")
        return False
        
    except Exception as e:
        print(f"启动 OBS 失败: {e}")
        return False

class OBSController:
    def __init__(self, password="zhang8315"):
        """初始化 OBS 控制器
        Args:
            password: OBS WebSocket 密码
        """
        self.host = "localhost"
        self.port = 4455
        self.password = password
        self.client = None
        self.recording_start_time = None

    def connect(self):
        """连接到 OBS"""
        try:
            # 首先检查 OBS 是否运行
            if not is_obs_running():
                print("OBS 未运行，正在启动...")
                if not start_obs():
                    return False
            
            # 检查端口是否可访问，如果不行就等待一下
            max_retries = 10
            for i in range(max_retries):
                if check_port(self.host, self.port):
                    break
                print(f"等待 WebSocket 服务器启动... ({i+1}/{max_retries})")
                time.sleep(2)
            
            if not check_port(self.host, self.port):
                print(f"错误：无法连接到 {self.host}:{self.port}")
                print("请检查：")
                print("1. OBS 是否已打开")
                print("2. WebSocket 服务器是否已启用")
                print(f"3. 端口 {self.port} 是否被其他程序占用")
                return False

            self.client = ReqClient(
                host=self.host,
                port=self.port,
                password=self.password
            )
            print("已连接到 OBS")
            return True
        except Exception as e:
            print(f"连接 OBS 失败: {e}")
            print("\n可能的解决方案：")
            print("1. 确认 OBS 已打开")
            print("2. 检查 Tools -> WebSocket Server Settings 中的设置：")
            print("   - 确保 'Enable WebSocket server' 已勾选")
            print(f"   - 确认密码设置为: {self.password}")
            print("3. 如果修改了密码，请更新脚本中的密码")
            print("4. 尝试重启 OBS")
            return False

    def start_recording(self):
        """开始录制视频"""
        try:
            self.client.start_record()
            self.recording_start_time = time.time()
            print("开始录制视频")
        except Exception as e:
            print(f"开始录制视频失败: {e}")
            raise

    def stop_recording(self):
        """停止录制视频"""
        try:
            self.client.stop_record()
            if self.recording_start_time:
                duration = time.time() - self.recording_start_time
                print(f"停止录制视频，录制时长: {duration:.2f} 秒")
            else:
                print("停止录制视频")
        except Exception as e:
            print(f"停止录制视频失败: {e}")
            raise

    def get_record_status(self):
        """获取录制状态"""
        try:
            status = self.client.get_record_status()
            return status
        except Exception as e:
            print(f"获取录制状态失败: {e}")
            return None

    def disconnect(self):
        """断开 OBS 连接"""
        if self.client:
            # ReqClient 会自动处理连接关闭
            print("已断开 OBS 连接")

def main():
    # 创建控制器实例
    controller = OBSController(password="zhang8315")
    
    try:
        # 连接 OBS（会自动启动 OBS 如果没有运行）
        if not controller.connect():
            return
        
        # 开始录制
        controller.start_recording()
        
        print("录制已开始，按 Ctrl+C 停止录制...")
        
        # 保持程序运行，直到用户按 Ctrl+C
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n检测到用户中断，正在停止录制...")
        controller.stop_recording()
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        controller.disconnect()

if __name__ == "__main__":
    main() 