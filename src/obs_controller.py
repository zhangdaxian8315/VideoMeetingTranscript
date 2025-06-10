import os
import time
import socket
import subprocess
import argparse
from datetime import datetime
from pathlib import Path
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
    def __init__(self, password="zhang8315", prefix="会议录制"):
        """初始化 OBS 控制器
        Args:
            password: OBS WebSocket 密码
            prefix: 录制文件前缀，默认为"会议录制"
        """
        self.host = "localhost"
        self.port = 4455
        self.password = password
        self.prefix = prefix  # 添加前缀属性
        self.client = None
        self.recording_start_time = None
        
        # 设置项目录制目录
        self.project_root = Path(__file__).parent.parent  # 获取项目根目录
        self.recordings_dir = self.project_root / "recordings"
        
        # 确保录制目录存在
        self.recordings_dir.mkdir(exist_ok=True)

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
            
            # 连接成功后设置录制输出配置
            self.setup_recording_output()
            
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

    def setup_recording_output(self):
        """设置录制输出目录"""
        try:
            # 设置录制目录
            print(f"📁 设置录制目录: {self.recordings_dir}")
            self.client.set_record_directory(str(self.recordings_dir))
            
            print("✅ 录制目录设置完成")
            
            # 生成预期的文件名（使用自定义前缀）
            now = datetime.now()
            self.target_filename = f"{self.prefix}_{now.strftime('%Y-%m-%d_%H-%M-%S')}.mkv"
            self.target_filepath = self.recordings_dir / self.target_filename
            
        except Exception as e:
            print(f"⚠️  设置录制目录失败: {e}")
            print("录制将使用 OBS 的默认设置")
            # 设置默认目标文件名（使用自定义前缀）
            now = datetime.now()
            self.target_filename = f"{self.prefix}_{now.strftime('%Y-%m-%d_%H-%M-%S')}.mkv"
            self.target_filepath = self.recordings_dir / self.target_filename

    def get_recording_config(self):
        """获取当前录制配置信息"""
        try:
            # 获取录制目录
            record_dir_response = self.client.get_record_directory()
            # 直接访问返回对象的属性，而不是datain
            record_dir = getattr(record_dir_response, 'recordDirectory', '未知')
            
            print(f"📁 当前录制目录: {record_dir}")
            
            return {
                'record_directory': record_dir
            }
            
        except Exception as e:
            print(f"获取录制配置失败: {e}")
            return None

    def start_recording(self):
        """开始录制视频"""
        try:
            # 显示当前录制配置
            print("\n🎬 录制配置信息:")
            self.get_recording_config()
            
            self.client.start_record()
            self.recording_start_time = time.time()
            
            print(f"\n🎥 开始录制视频")
            print(f"📁 文件将保存为: {self.target_filepath}")
            
        except Exception as e:
            print(f"开始录制视频失败: {e}")
            raise

    def stop_recording(self):
        """停止录制视频"""
        try:
            self.client.stop_record()
            if self.recording_start_time:
                duration = time.time() - self.recording_start_time
                print(f"⏹️  停止录制视频，录制时长: {duration:.2f} 秒")
                
                # 显示录制文件位置
                print(f"📁 录制文件已保存到: {self.recordings_dir}")
                
                # 等待一下确保文件写入完成
                time.sleep(1)
                
                # 查找并重命名最新的录制文件
                self.rename_latest_recording()
                
                # 转换 MKV 为 MP4
                self.convert_to_mp4()
                
                # 整理录制文件（创建文件夹、移动MP4、删除MKV）
                self.organize_recording_files()
                
            else:
                print("⏹️  停止录制视频")
        except Exception as e:
            print(f"停止录制视频失败: {e}")
            raise

    def convert_to_mp4(self):
        """将最新的 MKV 文件转换为 MP4 格式"""
        try:
            # 查找最新的 MKV 文件（使用自定义前缀）
            mkv_files = list(self.recordings_dir.glob(f"{self.prefix}_*.mkv"))
            if not mkv_files:
                print(f"⚠️  未找到需要转换的 MKV 文件（前缀: {self.prefix}）")
                return
                
            latest_mkv = max(mkv_files, key=lambda f: f.stat().st_mtime)
            mp4_path = latest_mkv.with_suffix('.mp4')
            
            print(f"\n🔄 开始转换视频格式:")
            print(f"   源文件: {latest_mkv.name}")
            print(f"   目标文件: {mp4_path.name}")
            
            # 使用 ffmpeg 进行无损转换（复制所有流，包括多音频轨道）
            cmd = [
                'ffmpeg',
                '-i', str(latest_mkv),
                '-map', '0',  # 映射所有输入流
                '-c', 'copy',  # 直接复制所有流，不重新编码
                '-y',  # 覆盖已存在的文件
                str(mp4_path)
            ]
            
            # 执行转换命令
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if process.returncode == 0:
                # 转换成功，显示文件大小
                mp4_size = mp4_path.stat().st_size / 1024 / 1024  # MB
                print(f"✅ 转换完成: {mp4_path.name} ({mp4_size:.2f} MB)")
                print(f"🎯 网页播放推荐使用 MP4 文件")
            else:
                print(f"⚠️  转换失败: {process.stderr}")
                
        except Exception as e:
            print(f"转换视频格式时出错: {e}")
            print("⚠️  请手动使用以下命令转换:")
            print(f"   ffmpeg -i \"{latest_mkv}\" -c copy \"{mp4_path}\"")

    def organize_recording_files(self):
        """整理录制文件：创建文件夹、移动MP4、删除MKV"""
        try:
            # 查找最新的 MP4 文件（使用自定义前缀）
            mp4_files = list(self.recordings_dir.glob(f"{self.prefix}_*.mp4"))
            if not mp4_files:
                print(f"⚠️  未找到需要整理的 MP4 文件（前缀: {self.prefix}）")
                return
                
            latest_mp4 = max(mp4_files, key=lambda f: f.stat().st_mtime)
            
            # 获取文件名（不包含扩展名）作为文件夹名
            folder_name = latest_mp4.stem  # 例如：Daxian_2024-01-15_14-30-25
            target_folder = self.recordings_dir / folder_name
            
            print(f"\n📁 开始整理录制文件:")
            print(f"   创建文件夹: {folder_name}")
            
            # 创建文件夹
            target_folder.mkdir(exist_ok=True)
            
            # 移动 MP4 文件到文件夹中
            mp4_in_folder = target_folder / latest_mp4.name
            latest_mp4.rename(mp4_in_folder)
            print(f"   ✅ MP4 文件已移动到: {folder_name}/{latest_mp4.name}")
            
            # 查找并删除对应的 MKV 文件
            mkv_name = latest_mp4.name.replace('.mp4', '.mkv')
            mkv_path = self.recordings_dir / mkv_name
            
            if mkv_path.exists():
                mkv_path.unlink()  # 删除文件
                print(f"   🗑️  已删除 MKV 文件: {mkv_name}")
            else:
                print(f"   ⚠️  未找到对应的 MKV 文件: {mkv_name}")
            
            # 显示最终结果
            mp4_size = mp4_in_folder.stat().st_size / 1024 / 1024  # MB
            print(f"\n🎉 录制文件整理完成!")
            print(f"📂 文件夹: {target_folder}")
            print(f"🎬 视频文件: {latest_mp4.name} ({mp4_size:.2f} MB)")
            print(f"🎯 可使用以下命令提取音频:")
            print(f"   python3 src/extract_audio_tracks.py \"{mp4_in_folder}\"")
            
        except Exception as e:
            print(f"整理录制文件时出错: {e}")

    def rename_latest_recording(self):
        """重命名最新的录制文件为带自定义前缀的格式"""
        try:
            # 查找最新的录制文件（所有.mkv文件）
            recording_files = list(self.recordings_dir.glob("*.mkv"))
            if recording_files:
                # 按修改时间排序，获取最新的文件
                latest_file = max(recording_files, key=lambda f: f.stat().st_mtime)
                
                # 检查文件是否是刚刚录制的（5分钟内）
                file_age = time.time() - latest_file.stat().st_mtime
                if file_age > 300:  # 5分钟
                    print("⚠️  最新文件不是刚录制的，跳过重命名")
                    return
                
                # 生成新的文件名（使用自定义前缀）
                file_timestamp = datetime.fromtimestamp(latest_file.stat().st_mtime)
                new_filename = f"{self.prefix}_{file_timestamp.strftime('%Y-%m-%d_%H-%M-%S')}.mkv"
                new_filepath = self.recordings_dir / new_filename
                
                # 检查新文件名是否已存在
                if new_filepath.exists():
                    print(f"⚠️  目标文件名已存在: {new_filename}")
                    # 添加序号避免冲突
                    counter = 1
                    while new_filepath.exists():
                        new_filename = f"{self.prefix}_{file_timestamp.strftime('%Y-%m-%d_%H-%M-%S')}_{counter}.mkv"
                        new_filepath = self.recordings_dir / new_filename
                        counter += 1
                
                # 执行重命名
                latest_file.rename(new_filepath)
                file_size = new_filepath.stat().st_size / 1024 / 1024  # MB
                
                print(f"✅ 文件重命名成功:")
                print(f"   原文件名: {latest_file.name}")
                print(f"   新文件名: {new_filename}")
                print(f"📹 录制文件: {new_filename} ({file_size:.2f} MB)")
                print(f"🎯 可使用以下命令提取音频:")
                print(f"   python3 src/extract_audio_tracks.py \"{new_filepath}\"")
                
            else:
                print("📁 录制目录中未找到录制文件")
                
        except Exception as e:
            print(f"重命名录制文件时出错: {e}")
            # 如果重命名失败，仍然显示原文件信息
            self.show_latest_recording()

    def show_latest_recording(self):
        """显示最新的录制文件"""
        try:
            # 查找最新的录制文件（所有.mkv文件）
            recording_files = list(self.recordings_dir.glob("*.mkv"))
            if recording_files:
                # 按修改时间排序，获取最新的文件
                latest_file = max(recording_files, key=lambda f: f.stat().st_mtime)
                file_size = latest_file.stat().st_size / 1024 / 1024  # MB
                print(f"📹 最新录制文件: {latest_file.name} ({file_size:.2f} MB)")
                print(f"🎯 可使用以下命令提取音频:")
                print(f"   python3 src/extract_audio_tracks.py \"{latest_file}\"")
            else:
                print("📁 录制目录中未找到录制文件")
        except Exception as e:
            print(f"查找录制文件时出错: {e}")

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
            print("🔌 已断开 OBS 连接")

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='OBS 录制控制器')
    parser.add_argument('prefix', nargs='?', 
                       default='会议录制',
                       help='录制文件前缀，默认为"会议录制"')
    parser.add_argument('--password', 
                       default='zhang8315',
                       help='OBS WebSocket 密码，默认为"zhang8315"')
    
    args = parser.parse_args()
    
    # 创建控制器实例，使用自定义前缀
    controller = OBSController(password=args.password, prefix=args.prefix)
    
    print(f"🎬 录制文件前缀设置为: {args.prefix}")
    
    try:
        # 连接 OBS（会自动启动 OBS 如果没有运行）
        if not controller.connect():
            return
        
        # 开始录制
        controller.start_recording()
        
        print("\n⏺️  录制已开始，按 Ctrl+C 停止录制...")
        
        # 保持程序运行，直到用户按 Ctrl+C
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  检测到用户中断，正在停止录制...")
        controller.stop_recording()
    except Exception as e:
        print(f"💥 发生错误: {e}")
    finally:
        controller.disconnect()

if __name__ == "__main__":
    main() 