# 操作系统判断
import platform

systemPlatFrom = platform.system()


def isWindows():
    return systemPlatFrom == "Windows"


def isLinux():
    return systemPlatFrom == "Linux"
