"""
系统自检模块
启动时检查各组件状态
"""

import sys
import importlib
from typing import Dict, List


class SystemChecker:
    """系统自检器"""

    def __init__(self):
        self.checks = []

    def run_all_checks(self) -> Dict:
        """运行所有检查"""
        result = {
            'status': 'pass',
            'checks': [],
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'warnings': 0
            }
        }

        # Python版本检查
        self._check_python_version()

        # 依赖包检查
        self._check_dependencies()

        # 配置文件检查
        self._check_config()

        # 目录检查
        self._check_directories()

        # 端口检查
        self._check_ports()

        # 更新结果
        result['checks'] = self.checks
        for check in self.checks:
            result['summary']['total'] += 1
            if check['status'] == 'pass':
                result['summary']['passed'] += 1
            elif check['status'] == 'fail':
                result['summary']['failed'] += 1
            elif check['status'] == 'warning':
                result['summary']['warnings'] += 1

        if result['summary']['failed'] > 0:
            result['status'] = 'fail'
        elif result['summary']['warnings'] > 0:
            result['status'] = 'warning'

        return result

    def _add_check(self, name: str, status: str, message: str):
        """添加检查结果"""
        self.checks.append({
            'name': name,
            'status': status,
            'message': message
        })

    def _check_python_version(self):
        """检查Python版本"""
        version = sys.version_info
        if version.major >= 3 and version.minor >= 8:
            self._add_check('Python版本', 'pass', f'{version.major}.{version.minor}.{version.micro}')
        else:
            self._add_check('Python版本', 'fail', f'需要Python 3.8+，当前{version.major}.{version.minor}')

    def _check_dependencies(self):
        """检查依赖包"""
        required = [
            'flask', 'flask_socketio', 'numpy', 'pynmea2', 'pyserial'
        ]

        missing = []
        for pkg in required:
            try:
                importlib.import_module(pkg)
            except ImportError:
                missing.append(pkg)

        if missing:
            self._add_check('依赖包', 'fail', f'缺少: {", ".join(missing)}')
        else:
            self._add_check('依赖包', 'pass', f'{len(required)}个已安装')

    def _check_config(self):
        """检查配置文件"""
        import os
        config_file = 'config/config.json'

        if os.path.exists(config_file):
            self._add_check('配置文件', 'pass', config_file)
        else:
            self._add_check('配置文件', 'warning', '使用默认配置')

    def _check_directories(self):
        """检查目录"""
        import os
        dirs = ['logs', 'data', 'config']

        missing = []
        for d in dirs:
            if not os.path.exists(d):
                try:
                    os.makedirs(d, exist_ok=True)
                except:
                    missing.append(d)

        if missing:
            self._add_check('目录', 'warning', f'已创建: {", ".join(missing)}')
        else:
            self._add_check('目录', 'pass', '全部存在')

    def _check_ports(self):
        """检查端口可用性"""
        import socket

        ports_to_check = [8081]
        available = []
        unavailable = []

        for port in ports_to_check:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            try:
                result = sock.connect_ex(('127.0.0.1', port))
                if result == 0:
                    unavailable.append(port)
                else:
                    available.append(port)
            except:
                pass
            finally:
                sock.close()

        if unavailable:
            self._add_check('端口', 'warning', f'端口{unavailable[0]}已被占用')
        else:
            self._add_check('端口', 'pass', '8081可用')


def run_system_check() -> Dict:
    """运行系统自检"""
    checker = SystemChecker()
    return checker.run_all_checks()
