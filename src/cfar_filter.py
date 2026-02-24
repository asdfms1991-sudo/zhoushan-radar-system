"""
CFAR检测和杂波过滤模块
用于雷达目标检测和噪声过滤
"""

import numpy as np
from typing import List, Tuple


class CFARDetector:
    """
    CFAR (Constant False Alarm Rate) 检测器
    
    用于自适应阈值目标检测
    """
    
    def __init__(self, guard_cells: int = 2, ref_cells: int = 16, 
                 p_fa: float = 1e-4):
        """
        初始化 CFAR 检测器
        
        Args:
            guard_cells: 保护单元数
            ref_cells: 参考单元数
            p_fa: 虚警概率
        """
        self.guard_cells = guard_cells
        self.ref_cells = ref_cells
        self.p_fa = p_fa
        
        # 计算阈值因子（CA-CFAR）
        self.alpha = self._calculate_alpha()
    
    def _calculate_alpha(self) -> float:
        """计算CA-CFAR阈值因子"""
        n = 2 * self.ref_cells
        alpha = n * (self.p_fa ** (-1/n) - 1)
        return alpha
    
    def detect(self, signal: np.ndarray) -> np.ndarray:
        """
        CFAR检测
        
        Args:
            signal: 输入信号
            
        Returns:
            检测结果（1=有目标，0=无目标）
        """
        n = len(signal)
        results = np.zeros(n)
        
        for i in range(self.guard_cells + self.ref_cells, 
                      n - self.guard_cells - self.ref_cells):
            # 参考单元
            ref_left = signal[i - self.ref_cells - self.guard_cells:
                            i - self.guard_cells]
            ref_right = signal[i + self.guard_cells:
                              i + self.guard_cells + self.ref_cells]
            ref_cells = np.concatenate([ref_left, ref_right])
            
            # 噪声估计（平均）
            noise_estimate = np.mean(ref_cells)
            
            # 阈值
            threshold = self.alpha * noise_estimate
            
            # 检测
            if signal[i] > threshold:
                results[i] = 1
        
        return results


class ClutterFilter:
    """
    杂波过滤器
    
    用于过滤固定目标、陆地和噪声
    """
    
    def __init__(self, 
                 min_speed: float = 0.5,      # 最小速度（节）
                 max_speed: float = 50.0,      # 最大速度（节）
                 min_distance: float = 0.05,   # 最小距离（海里）
                 max_distance: float = 20.0):   # 最大距离（海里）
        self.min_speed = min_speed
        self.max_speed = max_speed
        self.min_distance = min_distance
        self.max_distance = max_distance
    
    def filter_targets(self, targets: List[dict]) -> List[dict]:
        """
        过滤目标
        
        Args:
            targets: 目标列表
            
        Returns:
            过滤后的目标列表
        """
        filtered = []
        
        for target in targets:
            # 速度过滤
            speed = target.get('speed_knots', 0)
            if speed < self.min_speed or speed > self.max_speed:
                continue
            
            # 距离过滤
            distance = target.get('distance_nm', 0)
            if distance < self.min_distance or distance > self.max_distance:
                continue
            
            filtered.append(target)
        
        return filtered
    
    def filter_static_targets(self, targets: List[dict]) -> List[dict]:
        """过滤静止目标"""
        return [t for t in targets if t.get('speed_knots', 0) >= self.min_speed]


class SpeedFilter:
    """速度过滤器"""
    
    def __init__(self, min_speed: float = 0.5, max_speed: float = 50.0):
        self.min_speed = min_speed
        self.max_speed = max_speed
    
    def is_valid(self, speed: float) -> bool:
        """速度是否有效"""
        return self.min_speed <= speed <= self.max_speed


class DistanceFilter:
    """距离过滤器"""
    
    def __init__(self, min_distance: float = 0.05, max_distance: float = 20.0):
        self.min_distance = min_distance
        self.max_distance = max_distance
    
    def is_valid(self, distance: float) -> bool:
        """距离是否有效"""
        return self.min_distance <= distance <= self.max_distance


if __name__ == '__main__':
    # 测试CFAR
    print("=== CFAR测试 ===")
    cfar = CFARDetector(guard_cells=2, ref_cells=16)
    
    # 生成测试信号
    signal = np.random.randn(100) * 0.1
    signal[50] = 1.0  # 添加目标
    
    results = cfar.detect(signal)
    targets = np.where(results == 1)[0]
    print(f"检测到目标位置: {targets}")
    
    # 测试杂波过滤
    print("\n=== 杂波过滤测试 ===")
    clutter = ClutterFilter(min_speed=1.0, max_speed=30.0,
                          min_distance=0.1, max_distance=10.0)
    
    test_targets = [
        {'id': '1', 'speed_knots': 0.3, 'distance_nm': 1.0},  # 速度太慢
        {'id': '2', 'speed_knots': 10.0, 'distance_nm': 1.0},  # 有效
        {'id': '3', 'speed_knots': 15.0, 'distance_nm': 0.02}, # 距离太近
        {'id': '4', 'speed_knots': 20.0, 'distance_nm': 5.0},  # 有效
    ]
    
    filtered = clutter.filter_targets(test_targets)
    print(f"过滤前: {len(test_targets)}个")
    print(f"过滤后: {len(filtered)}个")
    print(f"保留: {[t['id'] for t in filtered]}")
