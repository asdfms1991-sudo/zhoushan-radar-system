"""
配置验证模块
启动时检查配置完整性
"""

import os
from typing import Dict, List, Tuple


class ConfigValidator:
    """配置验证器"""

    REQUIRED_FIELDS = {
        'radar': ['connection'],
        'ais': ['connection'],
        'fusion': ['enabled'],
        'output': ['http']
    }

    def __init__(self, config: dict):
        self.config = config
        self.errors = []
        self.warnings = []

    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """验证配置"""
        self.errors = []
        self.warnings = []

        # 必填字段
        self._check_required_fields()

        # 雷达配置
        self._validate_radar()

        # AIS配置
        self._validate_ais()

        # 融合配置
        self._validate_fusion()

        # 网络配置
        self._validate_network()

        # 路径配置
        self._validate_paths()

        is_valid = len(self.errors) == 0

        return is_valid, self.errors, self.warnings

    def _check_required_fields(self):
        """检查必填字段"""
        for section, fields in self.REQUIRED_FIELDS.items():
            if section not in self.config:
                self.errors.append(f"缺少配置节: {section}")
            else:
                for field in fields:
                    if field not in self.config[section]:
                        self.errors.append(f"缺少配置项: {section}.{field}")

    def _validate_radar(self):
        """验证雷达配置"""
        radar = self.config.get('radar', {})
        conn = radar.get('connection', {})

        ip = conn.get('ip', '')
        port = conn.get('port', 0)

        if not ip:
            self.warnings.append("雷达IP未配置，将使用模拟器模式")

        if port and (port < 1 or port > 65535):
            self.errors.append(f"雷达端口无效: {port}")

    def _validate_ais(self):
        """验证AIS配置"""
        ais = self.config.get('ais', {})
        conn = ais.get('connection', {})

        port = conn.get('port', '')

        if not port:
            self.warnings.append("AIS串口未配置")

    def _validate_fusion(self):
        """验证融合配置"""
        fusion = self.config.get('fusion', {})

        tracker = fusion.get('tracker', 'KF')
        if tracker not in ['KF', 'EKF', 'UKF', 'PF']:
            self.warnings.append(f"未知跟踪算法: {tracker}")

    def _validate_network(self):
        """验证网络配置"""
        output = self.config.get('output', {}).get('http', {})

        port = output.get('port', 8081)

        if port and (port < 1 or port > 65535):
            self.errors.append(f"HTTP端口无效: {port}")

    def _validate_paths(self):
        """验证路径配置"""
        # 检查日志目录
        log_dir = self.config.get('system', {}).get('log_dir', 'logs')
        if not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir, exist_ok=True)
                self.warnings.append(f"已创建日志目录: {log_dir}")
            except:
                self.errors.append(f"无法创建日志目录: {log_dir}")


def validate_config(config: dict) -> Tuple[bool, List[str], List[str]]:
    """验证配置"""
    validator = ConfigValidator(config)
    return validator.validate()
