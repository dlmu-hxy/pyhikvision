import logging
import os
from ctypes import *

from hkws.config import Config
from hkws.model import base, alarm


# from hkws import cm_camera_adpt


# 海康威视基础类

class BaseAdapter:
    # 动态sdk文件 .so .dll
    so_list = []  # 存储加载的SDK动态库文件路径

    def set_lib(self, so_list: []):  # 设置动态库文件列表
        self.so_list = so_list

    def get_lib(self):  # 获取当前加载的动态库文件列表
        return self.so_list

    # 常规启动，初始化SDK到用户注册设备
    def common_start(self, cnf: Config):
        userId = -1
        self.add_lib(cnf.SDKPath, cnf.Suffix)
        # 加载动态库
        if len(self.so_list) == 0:
            return userId
        if not self.init_sdk():
            return userId
        userId = self.login(cnf.IP, cnf.Port, cnf.User, cnf.Password)
        if userId < 0:
            self.print_error("common_start 失败: the error code is")
        return userId

    # 递归加载目录下所有so文件
    def add_lib(self, path, suffix):
        files = os.listdir(path)
        # 使用os.listdir(path)获取目录path中的所有文件和子目录，并将它们存储在files列表中

        for file in files:
            if not os.path.isdir(path + file):
                # 当前文件不是目录
                if file.endswith(suffix):
                    # 文件名以suffix结尾
                    self.so_list.append(path + file)
                    # 将该文件的路径（path + file）添加到so_list列表中
            else:
                self.add_lib(path + file + "/", suffix)
                # 当前文件是目录,递归调用add_lib方法,进入该目录继续查找

    # 重点：python调用sdk指定方法，函数名，参数列表
    def call_cpp(self, func_name, *args):
        # 遍历so_list，尝试加载动态库并调用指定函数
        for so_lib in self.so_list:
            try:
                lib = cdll.LoadLibrary(so_lib)
                try:
                    """"
                    使用eval动态生成函数调用，eval将lib.%s中的%s替换为func_name，从而形成如lib.func_name的格式，执行动态库中的函数。
                    然后，将*args传递给该函数。执行后，返回值赋给value变量。
                    """
                    value = eval("lib.%s" % func_name)(*args)
                    logging.info("调用的库：" + so_lib)
                    logging.info("执行成功,返回值：" + str(value))
                    return value
                except:
                    continue
            except:
                logging.info("库文件载入失败：" + so_lib)
                continue
        logging.error("没有找到接口！")
        return False

    def init_sdk(self):
        """
        初始化海康威视 sdk
        :return:
        """
        init_res = self.call_cpp("NET_DVR_Init")  # 调用SDK的NET_DVR_Init接口初始化SDK，返回值True or False
        if init_res:
            logging.info("SDK初始化成功")
            return True
        else:
            self.print_error("NET_DVR_GetLastError 初始化SDK失败: the error code is ")
            return False

    # 设置sdk初始化参数
    def set_sdk_config(self, enumType, sdkPath):
        req = base.NET_DVR_LOCAL_SDK_PATH()
        sPath = bytes(sdkPath, "ascii")
        i = 0
        for o in sPath:
            req.sPath[i] = o
            i += 1

        ptr = byref(req)
        res = self.call_cpp("NET_DVR_SetSDKInitCfg", enumType, ptr)
        if res < 0:
            self.print_error("NET_DVR_SetSDKInitCfg 启动预览失败: the error code is")
        return res

    # 释放sdk
    def sdk_clean(self):
        result = self.call_cpp("NET_DVR_Cleanup")
        logging.info("释放资源", result)

    # 设备登录
    def login(self, address="192.168.1.64", port=8000, user="admin", pwd="jqf64078"):
        # 设置连接时间
        set_overtime = self.call_cpp("NET_DVR_SetConnectTime", 5000, 4)  # 设置超时
        if not set_overtime:
            self.print_error("NET_DVR_SetConnectTime 设置超时错误信息失败：the error code is ")
            return False
        # 设置重连
        self.call_cpp("NET_DVR_SetReconnect", 10000, True)

        b_address = bytes(address, "ascii")
        b_user = bytes(user, "ascii")
        b_pwd = bytes(pwd, "ascii")

        struLoginInfo = base.NET_DVR_USER_LOGIN_INFO()
        struLoginInfo.bUseAsynLogin = 0  # 同步登陆
        i = 0
        for o in b_address:
            struLoginInfo.sDeviceAddress[i] = o
            i += 1

        struLoginInfo.wPort = port
        i = 0
        for o in b_user:
            struLoginInfo.sUserName[i] = o
            i += 1

        i = 0
        for o in b_pwd:
            struLoginInfo.sPassword[i] = o
            i += 1

        device_info = base.NET_DVR_DEVICEINFO_V40()
        loginInfo1 = byref(struLoginInfo)
        loginInfo2 = byref(device_info)
        user_id = self.call_cpp("NET_DVR_Login_V40", loginInfo1, loginInfo2)
        if user_id == -1:  # -1表示失败，其他值表示返回的用户ID值。
            self.print_error("NET_DVR_Login_V40 用户登录失败: the error code is ")
        return user_id

    # 设备登出
    def logout(self, userId=0):
        result = self.call_cpp("NET_DVR_Logout", userId)
        logging.info("登出", result)

    # 设置报警回调函数
    def setup_alarm_chan_v31(self, cbFunc, user_id):
        result = self.call_cpp("NET_DVR_SetDVRMessageCallBack_V31", cbFunc, user_id)
        if result == -1:
            self.print_error(
                "NET_DVR_SetDVRMessageCallBack_V31 初始化SDK失败: the error code is "
            )
        return result

    # 设置报警布防
    def setup_alarm_chan_v41(self, user_id=0):
        structure_l = alarm.NET_DVR_SETUPALARM_PARAM()
        structure_l.dwSize = sizeof(structure_l)
        structure_l.byFaceAlarmDetection = 0
        structure_l_ref = byref(structure_l)
        result = self.call_cpp("NET_DVR_SetupAlarmChan_V41", user_id, structure_l_ref)
        if result == -1:
            self.print_error("NET_DVR_SetupAlarmChan_V41 报警布防: the error code is ")
        return result

    # 报警撤防
    def close_alarm(self, alarm_result):
        return self.call_cpp("NET_DVR_CloseAlarmChan_V30", alarm_result)

    # 获取SDK版本，2个高字节表示主版本，2个低字节表示次版本。如0x00030000：表示版本为3.0。
    def get_sdk_version(self):
        return self.call_cpp("NET_DVR_GetSDKVersion")

    # 获取SDK的版本号和Build信息
    # SDK的版本号和build信息。2个高字节表示版本号 ：25~32位表示主版本号，17~24位表示次版本号；2个低字节表示build信息。 如0x03000101：表示版本号为3.0，build 号是0101。
    def get_sdk_build_version(self):
        return self.call_cpp("NET_DVR_GetSDKBuildVersion")

    # 获取当前SDK状态信息失败
    def get_sdk_state(self):
        op = base.NET_DVR_SDKSTATE()
        pSDKState = byref(op)
        res = self.call_cpp("NET_DVR_GetSDKState", pSDKState)
        if not res:
            self.print_error("NET_DVR_GetSDKState 获取当前SDK状态信息失败: the error code is ")
        return res, op

    # 获取当前SDK的功能信息
    def get_sdk_abl(self):
        op = base.NET_DVR_SDKABL()
        pSDKAbl = byref(op)
        res = self.call_cpp("NET_DVR_GetSDKAbility", pSDKAbl)
        if not res:
            self.print_error("NET_DVR_GetSDKAbility 获取当前SDK功能信息失败: the error code is ")
        return res, op

    def activate_device(self, ip="192.168.1.64", port=8000, pwd="jqf64078"):
        """
        激活设备
        :param ip: IP
        :param port: 端口
        :param pwd: 密码
        :return:
        """
        # 转换为ASCII字节
        b_ip = bytes(ip, "ascii")
        b_pwd = bytes(pwd, "ascii")

        input = base.NET_DVR_ACTIVATECFG()  # 实例化结构体对象input
        input.dwSize = sizeof(input)

        i = 0
        # 逐字节复制密码到结构体的字符数组
        for o in b_pwd:
            input.sPassword[i] = o
            i += 1

        input_ref = byref(input)  # 获取结构体的指针
        # 调用SDK函数
        res = self.call_cpp("NET_DVR_ActivateDevice", b_ip, port, input_ref)
        if not res:
            self.print_error("NET_DVR_ActivateDevice 激活设备失败: the error code is ")
        return res

    def print_error(self, msg=""):
        """
        错误描述
        :param msg:错误前缀
        :return:
        """
        # 调用NET_DVR_GetLastError函数，返回最后操作的错误码
        error_info = self.call_cpp("NET_DVR_GetLastError")
        logging.error(msg + str(error_info))
