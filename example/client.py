import socket
import sys

class CameraClient:
    def __init__(self, server_ip='127.0.0.1', port=5000):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(5)  # 设置5秒超时
        self.server_addr = (server_ip, port)

    def send_command(self, cmd):
        """发送命令并等待服务器响应"""
        self.sock.sendto(cmd.encode(), self.server_addr)
        try:
            response, _ = self.sock.recvfrom(1024)
            return response.decode()
        except socket.timeout:
            return "Error: 请求超时，未收到服务器响应"

if __name__ == "__main__":
    client = CameraClient()

    print("球机控制客户端")
    print("可用命令：")
    print("  login <ip> <port> <user> <pwd>")
    print("  start_preview")
    print("  stop_preview")
    print("  ptz (direction：up，down，left，right)")
    print("  exit")
    while True:
        try:
            # 获取用户输入
            cmd = input(">> ").strip()

            # 退出条件
            if cmd.lower() in ('exit', 'quit'):
                break

            # 空输入处理
            if not cmd:
                continue

            # 发送命令并显示响应
            print(f"[发送] {cmd}")
            response = client.send_command(cmd)
            print(f"[响应] {response}")

        except KeyboardInterrupt:
            print("\n检测到中断，正在退出...")
            break
        except Exception as e:
            print(f"发生错误: {str(e)}")