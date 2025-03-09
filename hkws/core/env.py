"""
此文件用来判断当前操作系统
"""
import platform

system_platform = platform.system()


def is_windows():
    return system_platform == "Windows"


def is_linux():
    return system_platform == "Linux"
