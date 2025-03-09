import configparser
from hkws.core import env


class Config:
    """
    配置文件类
    """
    sdk_path = ""
    user = "admin"
    password = "jqf64078"
    port = 8000
    ip = "192.168.1.64"
    suffix = ".so"

    def init_config(self, path):
        """
        初始化配置文件
        :param path: 配置文件路径
        :return:
        """
        cnf = configparser.ConfigParser()
        cnf.read(path)
        self.sdk_path = cnf.get("DEFAULT", "sdk_path")
        self.user = cnf.get("DEFAULT", "user")
        self.password = cnf.get("DEFAULT", "password")
        self.port = cnf.getint("DEFAULT", "port")
        self.ip = cnf.get("DEFAULT", "ip")
        if env.is_windows():
            self.suffix = ".dll"
        return
