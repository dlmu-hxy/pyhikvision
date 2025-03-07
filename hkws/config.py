# 读取.ini配置文件
import configparser

from hkws.core import env

# 定义配置文件类
class Config:
    SDKPath = ""
    User = "admin"
    Password = "jqf64078"
    Port = 8000
    IP = "192.168.1.64"
    Suffix = ".so"              # 文件后缀

    # 定义读取.ini配置文件的方法：从指定的配置文件路径加载配置
    def InitConfig(self, path):
        cnf = configparser.ConfigParser()
        cnf.read(path)
        self.SDKPath = cnf.get("DEFAULT", "SDKPath")
        self.User = cnf.get("DEFAULT", "User")
        self.Password = cnf.get("DEFAULT", "Password")
        self.Port = cnf.getint("DEFAULT", "Port")
        self.IP = cnf.get("DEFAULT", "IP")
        # 根据操作系统设置文件后缀
        if env.isWindows():
            self.Suffix = ".dll"
        return
