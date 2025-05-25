import os
import time
import socket
from datetime import datetime
from obsws_python import ReqClient

def check_port(host, port):
    """检查端口是否可访问"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0

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
            # 首先检查端口是否可访问
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
        # 连接 OBS
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