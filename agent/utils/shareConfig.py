# 共享的配置
from .dataProcess import dataProcess

config_instance = None

def init_config(data: dict):
    global config_instance
    config_instance = dataProcess(data)

def get_config():
    return config_instance