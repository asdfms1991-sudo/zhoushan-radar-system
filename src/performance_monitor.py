"""
性能监控模块
实时监控算法性能指标
"""

import time
import psutil
from typing import Dict, List
from collections import deque
from datetime import datetime


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        
        # 延迟统计
        self.latency_history = deque(maxlen=window_size)
        self.last_process_time = 0
        
        # 吞吐量
        self.throughput_history = deque(maxlen=window_size)
        self.frame_count = 0
        self.start_time = time.time()
        
        # 内存
        self.memory_history = deque(maxlen=window_size)
        
        # 算法精度（模拟）
        self.error_history = deque(maxlen=window_size)
        
        # 目标数
        self.target_count_history = deque(maxlen=window_size)
    
    def start_process(self):
        """开始处理"""
        self.last_process_time = time.time()
    
    def end_process(self, target_count: int = 0):
        """结束处理"""
        latency = (time.time() - self.last_process_time) * 1000  # 毫秒
        self.latency_history.append(latency)
        
        self.frame_count += 1
        self.target_count_history.append(target_count)
        
        # 内存
        memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        self.memory_history.append(memory)
        
        # 吞吐量
        elapsed = time.time() - self.start_time
        fps = self.frame_count / elapsed if elapsed > 0 else 0
        self.throughput_history.append(fps)
    
    def add_error(self, error: float):
        """添加误差"""
        self.error_history.append(error)
    
    def get_latency_stats(self) -> Dict:
        """延迟统计"""
        if not self.latency_history:
            return {}
        
        data = list(self.latency_history)
        return {
            'current_ms': data[-1],
            'avg_ms': sum(data) / len(data),
            'min_ms': min(data),
            'max_ms': max(data),
            'p95_ms': sorted(data)[int(len(data) * 0.95)] if len(data) > 20 else data[-1]
        }
    
    def get_throughput_stats(self) -> Dict:
        """吞吐量统计"""
        if not self.throughput_history:
            return {}
        
        data = list(self.throughput_history)
        return {
            'current_fps': data[-1],
            'avg_fps': sum(data) / len(data),
            'total_frames': self.frame_count,
            'elapsed_seconds': time.time() - self.start_time
        }
    
    def get_memory_stats(self) -> Dict:
        """内存统计"""
        if not self.memory_history:
            return {}
        
        data = list(self.memory_history)
        return {
            'current_mb': data[-1],
            'avg_mb': sum(data) / len(data),
            'peak_mb': max(data)
        }
    
    def get_accuracy_stats(self) -> Dict:
        """精度统计"""
        if not self.error_history:
            return {}
        
        data = list(self.error_history)
        return {
            'current_error': data[-1],
            'avg_error': sum(data) / len(data),
            'min_error': min(data),
            'max_error': max(data)
        }
    
    def get_target_stats(self) -> Dict:
        """目标统计"""
        if not self.target_count_history:
            return {}
        
        data = list(self.target_count_history)
        return {
            'current_count': data[-1],
            'avg_count': sum(data) / len(data),
            'max_count': max(data)
        }
    
    def get_all_stats(self) -> Dict:
        """获取所有统计"""
        return {
            'timestamp': datetime.now().isoformat(),
            'latency': self.get_latency_stats(),
            'throughput': self.get_throughput_stats(),
            'memory': self.get_memory_stats(),
            'accuracy': self.get_accuracy_stats(),
            'targets': self.get_target_stats()
        }
    
    def get_health_status(self) -> Dict:
        """健康状态"""
        latency = self.get_latency_stats()
        memory = self.get_memory_stats()
        
        # 判断状态
        status = 'healthy'
        issues = []
        
        if latency.get('avg_ms', 0) > 100:
            status = 'warning'
            issues.append('高延迟')
        
        if latency.get('p95_ms', 0) > 200:
            status = 'critical'
            issues.append('严重高延迟')
        
        if memory.get('peak_mb', 0) > 500:
            status = 'warning'
            issues.append('高内存')
        
        return {
            'status': status,
            'issues': issues,
            'score': 100 - len(issues) * 30
        }


# 测试
if __name__ == '__main__':
    monitor = PerformanceMonitor()
    
    # 模拟处理
    for i in range(50):
        monitor.start_process()
        time.sleep(0.01)  # 模拟处理
        monitor.end_process(target_count=10)
        monitor.add_error(0.1 + i * 0.01)
    
    print("性能统计:")
    print(f"延迟: {monitor.get_latency_stats()}")
    print(f"吞吐量: {monitor.get_throughput_stats()}")
    print(f"内存: {monitor.get_memory_stats()}")
    print(f"精度: {monitor.get_accuracy_stats()}")
    print(f"健康: {monitor.get_health_status()}")
