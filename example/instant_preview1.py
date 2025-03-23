import sys
import logging
import os

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton, QGroupBox, QSplitter)
from PySide6.QtCore import (Slot, Signal, QObject)

# 通信相关
import socket
from threading import Thread

# 添加自定义模块路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# 导入自定义模块hkws
from hkws.core import env
from hkws import cm_camera_adpt, config
from example import instant_preview1_cb

# 初始化配置文件
cnf = config.Config()
path = os.path.join('../local_config.ini')
cnf.init_config(path)  # 初始化配置文件路径

if env.is_windows():
    os.chdir(cnf.sdk_path)

# 初始化SDK适配器
adapter = cm_camera_adpt.CameraAdapter()
# 获取用户id
user_id = adapter.common_start(cnf)
if user_id < 0:
    logging.error("初始化Adapter失败")

print("Login successful,the user_id is ", user_id)


class UDPServer(QObject):
    """
    UDP通信类
    """
    command_received = Signal(str, tuple)

    def __init__(self):
        super().__init__()
        IP = "0.0.0.0"
        PORT = 5000
        # 实例化socket对象，指定协议类型为UDP
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 绑定服务器IP和端口
        self.sock.bind(('0.0.0.0', PORT))
        self.running = True

    def start(self):
        Thread(target=self._listen, daemon=True).start()

    def _listen(self):
        while self.running:
            data, addr = self.sock.recvfrom(1024)
            self.command_received.emit(data.decode(), addr)

    def stop(self):
        self.running = False
        self.sock.close()


class BallControlSystem(QMainWindow):
    def __init__(self):
        """
        初始化布局和控件
        """
        super().__init__()
        self.setWindowTitle("球机控制系统")
        self.setGeometry(100, 100, 1000, 700)
        self.lRealPlayHandle = None
        self.is_logged_in = False

        # 通信相关
        self.udp_server = UDPServer()
        self.udp_server.command_received.connect(self.handle_command)
        self.udp_server.start()

        # 主窗口布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # 左右分割器
        self.splitter = QSplitter()
        main_layout.addWidget(self.splitter)

        # 左侧功能区
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        self.splitter.addWidget(left_widget)

        # 右侧视频显示区
        self.video_label = QLabel()
        self.video_label.setStyleSheet("background-color: #333333;")
        self.splitter.addWidget(self.video_label)

        # 设置左右分割区域宽度
        self.splitter.setSizes([240, 960])

        # 设备配置模块
        self.create_device_config(left_layout)
        # 预览控制模块
        self.create_preview_control(left_layout)
        # 云台控制模块
        self.create_ptz_control(left_layout)

    def create_device_config(self, layout):
        """
        此函数实现设备配置组件
        :param layout: 布局
        :return:
        """
        group_box = QGroupBox("设备配置")
        group_layout = QVBoxLayout(group_box)

        # 设备IP
        self.ip_label = QLabel("设备IP:")
        self.ip_edit = QLineEdit()
        self.ip_edit.setPlaceholderText("Enter ip")

        # 调试用
        self.ip_edit.setText("192.168.1.64")

        group_layout.addWidget(self.ip_label)
        group_layout.addWidget(self.ip_edit)

        # 端口
        self.port_label = QLabel("端口:")
        self.port_edit = QLineEdit()
        self.port_edit.setPlaceholderText("Enter port")

        # 调试用
        self.port_edit.setText("8000")

        group_layout.addWidget(self.port_label)
        group_layout.addWidget(self.port_edit)

        # 用户名
        self.user_label = QLabel("用户名:")
        self.user_edit = QLineEdit()
        self.user_edit.setPlaceholderText("Enter username")

        # 调试用
        self.user_edit.setText("admin")

        group_layout.addWidget(self.user_label)
        group_layout.addWidget(self.user_edit)

        # 密码
        self.pwd_label = QLabel("密码:")
        self.pwd_edit = QLineEdit()
        self.pwd_edit.setPlaceholderText("Enter password")

        # 调试用
        self.pwd_edit.setText("jqf64078")

        self.pwd_edit.setEchoMode(QLineEdit.Password)  # 密文输入
        group_layout.addWidget(self.pwd_label)
        group_layout.addWidget(self.pwd_edit)

        # 状态
        self.status_label = QLabel("状态: 未登录")
        group_layout.addWidget(self.status_label)

        # 登录按钮
        self.login_btn = QPushButton("登录")
        self.login_btn.setStyleSheet("background-color: #3498db; color: white; border: none; padding: 8px;")
        self.login_btn.clicked.connect(self.on_login_clicked)
        group_layout.addWidget(self.login_btn)

        layout.addWidget(group_box)

    def create_preview_control(self, layout):
        """
        此函数实现预览组件
        :param layout: 布局
        :return:
        """
        group_box = QGroupBox("预览控制")  # 分组框组件
        group_layout = QVBoxLayout(group_box)

        # 开始预览按钮 创建-设置格式-连接槽函数-设置布局
        self.preview_btn = QPushButton("开始预览")
        self.preview_btn.setStyleSheet("background-color: #3498db; color: white; border: none; padding: 8px;")
        self.preview_btn.clicked.connect(self.on_preview_clicked)
        group_layout.addWidget(self.preview_btn)

        # 停止预览按钮
        self.stop_preview_btn = QPushButton("停止预览")
        self.stop_preview_btn.setStyleSheet("background-color: #ff0000; color: white; border: none; padding: 8px;")
        self.stop_preview_btn.clicked.connect(self.on_stop_preview_clicked)
        group_layout.addWidget(self.stop_preview_btn)

        layout.addWidget(group_box)

    def create_ptz_control(self, layout):
        """
        此函数实现云台控制组件
        :param layout: 布局
        :return:
        """
        group_box = QGroupBox("云台控制")
        group_layout = QVBoxLayout(group_box)

        # 上
        self.up_btn = QPushButton("↑")
        self.up_btn.setStyleSheet("background-color: #333333; color: white; border: none;")
        # 连接槽函数
        self.up_btn.clicked.connect(lambda: self.on_ptz_control(21))

        # 下
        self.down_btn = QPushButton("↓")
        self.down_btn.setStyleSheet("background-color: #333333; color: white; border: none;")
        self.down_btn.clicked.connect(lambda: self.on_ptz_control(22))

        # 左
        self.left_btn = QPushButton("←")
        self.left_btn.setStyleSheet("background-color: #333333; color: white; border: none;")
        self.left_btn.clicked.connect(lambda: self.on_ptz_control(23))

        # 右
        self.right_btn = QPushButton("→")
        self.right_btn.setStyleSheet("background-color: #333333; color: white; border: none;")
        self.right_btn.clicked.connect(lambda: self.on_ptz_control(24))

        group_layout.addWidget(self.up_btn)
        group_layout.addWidget(self.down_btn)
        group_layout.addWidget(self.left_btn)
        group_layout.addWidget(self.right_btn)

        layout.addWidget(group_box)

    def closeEvent(self, event):
        """
        处理窗口关闭事件
        :param event:
        :return: 事件
        """
        if self.lRealPlayHandle is not None:
            adapter.stop_preview(self.lRealPlayHandle)
        adapter.logout(user_id)
        adapter.sdk_clean()
        self.udp_server.stop()
        event.accept()

    @Slot()
    def on_login_clicked(self):
        """
        登录按钮槽函数
        :return:
        """
        # 获取用户输入信息
        ip = self.ip_edit.text()
        port = self.port_edit.text()
        user = self.user_edit.text()
        pwd = self.pwd_edit.text()

        # 处理状态栏文本
        if user_id is not None and user_id >= 0:
            self.is_logged_in = True
            self.status_label.setText(f"状态: 已登录，用户ID: {user_id}")
        else:
            self.is_logged_in = False
            self.status_label.setText("状态: 未登录")

    @Slot()
    def on_preview_clicked(self):
        """
        预览按钮槽函数，未登录状态不能进行预览
        :return:
        """
        if not self.is_logged_in:
            return
        if self.lRealPlayHandle is None:
            # 获取视频显示区域的句柄
            hwnd = self.video_label.winId()
            self.lRealPlayHandle = adapter.start_preview(hwnd, None, user_id)
            if self.lRealPlayHandle < 0:
                logging.error("启动预览失败")
                return
            print("start preview 成功", self.lRealPlayHandle)
            self.status_label.setText("状态: 预览已开始")
            # 注册回调函数
            callback = adapter.callback_real_data(self.lRealPlayHandle, instant_preview1_cb.f_real_data_call_back,
                                                  user_id)
            print("callback", callback)

    def on_stop_preview_clicked(self):
        """
        停止预览按钮槽函数
        :return:
        """
        if self.lRealPlayHandle is not None:
            adapter.stop_preview(self.lRealPlayHandle)
            self.lRealPlayHandle = None
            self.status_label.setText("状态: 预览已停止")
            self.video_label.setStyleSheet("background-color: #333333;")

    @Slot(int)
    def on_ptz_control(self, dwPTZCommand):
        """
        云台控制槽函数，未登录或未预览不能进行云台控制
        :param dwPTZCommand: 云台控制命令
        :return:
        """
        if not self.is_logged_in or self.lRealPlayHandle is None:
            return

        adapter.ptz_control(self.lRealPlayHandle, dwPTZCommand, 0)

    def handle_command(self, cmd: str, addr: tuple):
        """
        处理命令
        :param cmd: 命令
        :param addr: 地址
        :return:
        """
        parts = cmd.split()  # 分割命令
        response = '错误的命令'
        try:
            # 登录命令
            if (parts[0] == 'login' and len(parts) == 5):
                # 格式：login [IP] [PORT] [USER] [PWD]
                ip, port, user, pwd = parts[1:]
                user_id = adapter.login(ip, int(port), user, pwd)

                if user_id is not None and user_id >= 0:
                    response = 'OK: login success'
                    self.is_logged_in = True
                else:
                    response = 'ERROR: login failed'

            # 启动预览命令
            elif (parts[0] == 'start_preview'):
                if self.is_logged_in:
                    self.on_preview_clicked()
                    response = 'OK: preview success'
                else:
                    response = 'ERROR: preview failed'

            # 停止预览命令
            elif (parts[0] == 'stop_preview'):
                if self.is_logged_in and self.lRealPlayHandle is not None:
                    self.on_stop_preview_clicked()
                    response = 'OK: preview stopped'
                else:
                    response = 'ERROR: stop_preview failed'

            # 云台控制命令
            elif (parts[0] == 'ptz'):
                direction_map = {
                    "up": 21, "down": 22,
                    "left": 23, "right": 24
                }
                if self.is_logged_in and self.lRealPlayHandle is not None:
                    if parts[1] in direction_map:
                        self.on_ptz_control(direction_map[parts[1]])
                        response = f"OK: ptz {parts[1]}"
                    else:
                        response = "ERROR: cmd not in direction_map"
                else:
                    response = "ERROR: ptz failed"

            self.udp_server.sock.sendto(response.encode(), addr)

        except Exception as e:
            self.udp_server.sock.sendto(str(e).encode(), addr)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BallControlSystem()
    window.show()
    sys.exit(app.exec())
