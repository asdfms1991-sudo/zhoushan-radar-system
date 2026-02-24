"""
系统健康检查模块
监控各组件状态
"""

import time
import psutil
from datetime import datetime
from typing import Dict, List


class HealthChecker:
    """健康检查器"""

    def __init__(self):
        self.start_time = time.time()
        self.checks = {}
        self.last_check = None

    def check_all(self) -> Dict:
        """执行所有检查"""
        result = {
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': int(time.time() - self.start_time),
            'components': {},
            'overall': 'healthy'
        }

        # CPU检查
        result['components']['cpu'] = self._check_cpu()

        # 内存检查
        result['components']['memory'] = self._check_memory()

        # 磁盘检查
        result['components']['disk'] = self._check_disk()

        # 网络检查
        result['components']['network'] = self._check_network()

        # 进程检查
        result['components']['process'] = self._check_process()

        # 判断整体状态
        statuses = [c.get('status', 'unknown') for c in result['components'].values()]
        if 'critical' in statuses:
            result['overall'] = 'critical'
        elif 'warning' in statuses:
            result['overall'] = 'warning'
        else:
            result['overall'] = 'healthy'

        self.last_check = result
        return result

    def _check_cpu(self) -> Dict:
        """CPU检查"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count()

        status = 'healthy'
        if cpu_percent > 90:
            status = 'critical'
        elif cpu_percent > 70:
            status = 'warning'

        return {
            'status': status,
            'percent': cpu_percent,
            'count': cpu_count,
            'message': f'CPU使用率 {cpu_percent}%'
        }

    def _check_memory(self) -> Dict:
        """内存检查"""
        mem = psutil.virtual_memory()

        status = 'healthy'
        if mem.percent > 90:
            status = 'critical'
        elif mem.percent > 70:
            status = 'warning'

        return {
            'status': status,
            'percent': mem.percent,
            'total_gb': mem.total / (1024**3),
            'available_gb': mem.available / (1024**3),
            'message': f'内存使用 {mem.percent}%'
        }

    def _check_disk(self) -> Dict:
        """磁盘检查"""
        disk = psutil.disk_usage('/')

        status = 'healthy'
        if disk.percent > 95:
            status = 'critical'
        elif disk.percent > 85:
            status = 'warning'

        return {
            'status': status,
            'percent': disk.percent,
            'total_gb': disk.total / (1024**3),
            'free_gb': disk.free / (1024**3),
            'message': f'磁盘使用 {disk.percent}%'
        }

    def _check_network(self) -> Dict:
        """网络检查"""
        net = psutil.net_io_counters()

        return {
            'status': 'healthy',
            'bytes_sent': net.bytes_sent,
            'bytes_recv': net.bytes_recv,
            'packets_sent': net.packets_sent,
            'packets_recv': net.packets_recv
        }

    def _check_process(self) -> Dict:
        """进程检查"""
        process = psutil.Process()

        return {
            'status': 'healthy',
            'pid': process.pid,
            'num_threads': process.num_threads(),
            'memory_mb': process.memory_info().rss / (1024**2)
        }


# 全局实例
health_checker = HealthChecker()
