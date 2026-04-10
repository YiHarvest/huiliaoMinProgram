import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_config():
    """从文件加载配置"""
    try:
        # 使用绝对路径读取配置文件
        config_file_path = os.path.join(BASE_DIR, 'config.json')
        with open(config_file_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        config_data = {
            "life_emergence": {
                "ak": "",
                "sk": "",
                "base_url": "https://open.lifeemergence.com"
            },
            "server": {
                "host": "127.0.0.1",
                "port": 8020
            }
        }

    return config_data


def save_config(config_data):
    """保存配置到文件"""
    try:
        # 使用绝对路径保存配置文件
        config_file_path = os.path.join(BASE_DIR, 'config.json')
        with open(config_file_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"保存配置文件失败: {e}")


# 加载配置
config = load_config()
