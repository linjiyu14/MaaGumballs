# 共享的配置
from .configProcess import configProcess

config_instance = None

def init_config(data: dict):
    global config_instance
    config_instance = configProcess(data)

def get_config():
    return config_instance