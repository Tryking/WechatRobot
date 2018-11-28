"""
工具类
"""
import time


def get_now_time_str():
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
