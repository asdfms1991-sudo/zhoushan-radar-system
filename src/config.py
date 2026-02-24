"""
配置管理模块 V2.0
支持配置热加载、分级配置、环境变量
"""

import json
import os
import logging
from pathlib import Path
from typing import Any, Optional
from datetime import datetime


class Config:
    """配置管理类"""
    
    DEFAULT_CONFIG = {
        "system": {
            "name": "舟山定海渔港雷达监控系统",
            "version": "2.0.0",
            "log_level": "INFO",
            "data_dir": "data",
            "log_dir": "logs"
        },
        "radar": {
            "enabled": True,
            "type": "simrad_halo3000",
            "connection": {
                "method": "network",
                "ip": "192.168.1.100",
                "port": 2000,
                "protocol": "tcp",
                "timeout": 30,
                "retry_interval": 5
            },
            "origin": {
                "lon": 122.107,  # 舟山定海
                "lat": 30.017
            },
            "filter": {
                "min_distance_nm": 0.05,
                "max_distance_nm": 15.0,
                "min_speed_knots": 0.0,
                "max_speed_knots": 50.0,
                "clutter_filter": True,
                "min_track_age": 2
            }
        },
        "ais": {
            "enabled": True,
            "connection": {
                "method": "serial",
                "port": "COM3",
                "baudrate": 38400,
                "timeout": 10
            },
            "or_network": {
                "enabled": False,
                "ip": "127.0.0.1",
                "port": 5001
            }
        },
        "fusion": {
            "enabled": True,
            "association_distance_m": 100,
            "max_age_seconds": 60,
            "kalman": {
                "process_noise": 0.1,
                "measurement_noise": 1.0
            },
            "cfar": {
                "guard_cells": 2,
                "ref_cells": 16,
                "p_fa": 0.0001
            },
            "clutter": {
                "min_speed": 0.5,
                "max_speed": 50.0,
                "min_distance": 0.05,
                "max_distance": 20.0
            },
            "storage": {
                "enabled": True,
                "path": "data/trajectories",
                "format": "json"
            }
        },
        "output": {
            "websocket": {
                "enabled": True,
                "host": "127.0.0.1",  # 调试用，生产环境改为具体IP
                "port": 8080
            },
            "http": {
                "enabled": True,
                "host": "127.0.0.1",  # 调试用，生产环境改为具体IP
                "port": 8081
            },
            "database": {
                "enabled": False,
                "type": "sqlite",
                "path": "data/radar.db"
            }
        },
        "monitoring": {
            "health_check_interval": 60,
            "log_rotation": {
                "enabled": True,
                "max_size_mb": 100,
                "backup_count": 5
            }
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化配置"""
        self.logger = logging.getLogger('config')
        self.config_path = config_path
        self.config = {}
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                self._merge_config(user_config)
                self.logger.info(f"已加载配置文件: {self.config_path}")
            except Exception as e:
                self.logger.error(f"加载配置文件失败: {e}")
                self._use_default()
        else:
            self._use_default()
            self.logger.info("使用默认配置")
    
    def _merge_config(self, user_config: dict):
        """合并用户配置与默认配置"""
        self.config = self._deep_merge(self.DEFAULT_CONFIG, user_config)
    
    def _deep_merge(self, default: dict, user: dict) -> dict:
        """深度合并字典"""
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    def _use_default(self):
        """使用默认配置"""
        self.config = self.DEFAULT_CONFIG.copy()
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项，支持点号访问"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value
    
    def set(self, key: str, value: Any):
        """设置配置项"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
    
    def save(self, path: Optional[str] = None):
        """保存配置到文件"""
        save_path = path or self.config_path or 'config.json'
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            self.logger.info(f"配置已保存: {save_path}")
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
    
    @property
    def radar_config(self) -> dict:
        return self.config.get('radar', {})
    
    @property
    def ais_config(self) -> dict:
        return self.config.get('ais', {})
    
    @property
    def fusion_config(self) -> dict:
        return self.config.get('fusion', {})
    
    @property
    def output_config(self) -> dict:
        return self.config.get('output', {})
    
    @property
    def monitoring_config(self) -> dict:
        return self.config.get('monitoring', {})
    
    def __repr__(self):
        return f"Config(version={self.get('system.version')}, radar={self.radar_config.get('enabled')}, ais={self.ais_config.get('enabled')})"


def load_config(config_path: Optional[str] = None) -> Config:
    """加载配置的便捷函数"""
    return Config(config_path)


if __name__ == '__main__':
    # 测试配置
    config = Config()
    print(json.dumps(config.config, indent=2, ensure_ascii=False))
