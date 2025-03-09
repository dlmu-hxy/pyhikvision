# 直接传入窗口句柄，时效性最高，但是数据无法操作
import logging  # 记录日志
import os  # 操作文件和路径
import sys  # 与Python解释器和系统交
import tkinter  # 创建图形用户界面（GUI）的标准库
from tkinter import ttk, Button, Label, Entry, StringVar
from hkws.core import env
from hkws import cm_camera_adpt, config
from example import instant_preview1_cb

# 获取当前脚本的目录
curPath = os.path.abspath(os.path.dirname(__file__))
# split函数将路径分为目录和文件名，[0]取父目录
rootPath = os.path.split(curPath)[0]
# 取根目录
PathProject = os.path.split(rootPath)[0]
# 添加这些路径到sys.path，使得Python能够导入这些路径下的模块。
sys.path.append(rootPath)
sys.path.append(PathProject)

# 初始化配置文件
# 创建Config类对象cnf，使用对象cnf调用Config类中的方法和属性
cnf = config.Config()
path = os.path.join('../local_config.ini')
cnf.init_config(path)  # 初始化配置文件路径

if env.is_windows():
    os.chdir(cnf.sdk_path)

# 初始化SDK适配器
adapter = cm_camera_adpt.CameraAdapter()
userId = adapter.common_start(cnf)
if userId < 0:
    logging.error("初始化Adapter失败")
    os._exit(0)

print("Login successful,the user_id is ", userId)


# 实现云台控制
def click_left():
    adapter.ptz_control(lRealPlayHandle, 23, 0)


def click_right():
    adapter.ptz_control(lRealPlayHandle, 24, 0)


def click_up():
    adapter.ptz_control(lRealPlayHandle, 21, 0)


def click_down():
    adapter.ptz_control(lRealPlayHandle, 22, 0)


if __name__ == '__main__':
    win = tkinter.Tk()
    win.title("hikvision")
    win.resizable(0, 0)
    win.overrideredirect(True)
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    ww = 800
    wh = 650
    x = (sw - ww) / 2
    y = (sh - wh) / 2
    win.geometry("%dx%d+%d+%d" % (ww, wh, x, y))

    cv = tkinter.Canvas(win, bg='white', width=ww, height=wh)
    cv.place(x=20, y=10)

    hwnd = cv.winfo_id()

    # 创建按键
    btn_left = Button(win, text="  左  ",
                      command=click_left).place(x=100, y=530)

    btn_right = Button(win, text="  右  ",
                       command=click_right).place(x=180, y=530)

    btn_top = Button(win, text="  上  ", command=click_up).place(x=145, y=495)

    btn_down = Button(win, text="  下  ",
                      command=click_down).place(x=145, y=565)

    lbl_ip = Label(win, text="IP地址", fg="#111").place(x=480, y=490)

    ent_ip = Entry(win).place(x=550, y=490)

    lbl_port = Label(win, text="端口", fg="#111").place(x=480, y=515)

    ent_port = Entry(win).place(x=550, y=515)

    lbl_name = Label(win, text="登录名", fg="#111").place(x=480, y=540)

    ent_name = Entry(win).place(x=550, y=540)

    lbl_password = Label(win, text="密码", fg="#111").place(x=480, y=565)

    password = StringVar()
    password_entry = ttk.Entry(
        win,
        textvariable=password,
        show='*'
    )
    password_entry.place(x=550, y=565)

    # separator = ttk.Separator(win, orient='horizontal')
    # separator.place(x=10, y=600, width=790)

    btn_q = Button(win, text=' 退出 ', command=win.quit)
    btn_q.place(x=660, y=610)

    # 启动实时预览
    lRealPlayHandle = adapter.start_preview(hwnd, None, userId)
    if lRealPlayHandle < 0:
        adapter.logout(userId)
        adapter.sdk_clean()
        os._exit(2)

    print("start preview 成功", lRealPlayHandle)
    callback = adapter.callback_real_data(lRealPlayHandle, instant_preview1_cb.f_real_data_call_back, userId)
    print("callback", callback)

    win.mainloop()
    adapter.stop_preview(lRealPlayHandle)
    adapter.logout(userId)
    adapter.sdk_clean()
