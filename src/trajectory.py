"""
轨迹跟踪模块
用于记录和管理目标轨迹
"""

from collections import deque
from typing import List, Tuple, Optional
from datetime import datetime, timedelta
import math


class TrajectoryPoint:
    """轨迹点"""
    
    def __init__(self, lat: float, lon: float, 
                 speed: float = 0, course: float = 0,
                 timestamp: datetime = None):
        self.lat = lat
        self.lon = lon
        self.speed = speed
        self.course = course
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self) -> dict:
        return {
            'lat': self.lat,
            'lon': self.lon,
            'speed': self.speed,
            'course': self.course,
            'timestamp': self.timestamp.isoformat()
        }


class TargetTrajectory:
    """单目标轨迹"""
    
    def __init__(self, max_length: int = 100):
        """
        Args:
            max_length: 最大轨迹点数量
        """
        self.points = deque(maxlen=max_length)
        self.target_id = None
    
    def add_point(self, lat: float, lon: float,
                 speed: float = 0, course: float = 0):
        """添加轨迹点"""
        point = TrajectoryPoint(lat, lon, speed, course)
        self.points.append(point)
    
    def get_points(self, last_n: int = None) -> List[TrajectoryPoint]:
        """获取轨迹点"""
        if last_n is None:
            return list(self.points)
        return list(self.points)[-last_n:]
    
    def predict_position(self, seconds: float = 10) -> Tuple[float, float]:
        """
        预测未来位置
        
        Args:
            seconds: 预测秒数
            
        Returns:
            (lat, lon) 预测位置
        """
        if len(self.points) < 2:
            # 不足2点，返回最后位置
            if self.points:
                return self.points[-1].lat, self.points[-1].lon
            return 0, 0
        
        # 计算平均速度向量
        p1 = self.points[-2]
        p2 = self.points[-1]
        
        dt = (p2.timestamp - p1.timestamp).total_seconds()
        if dt == 0:
            dt = 1
        
        # 速度（度/秒）
        lat_speed = (p2.lat - p1.lat) / dt
        lon_speed = (p2.lon - p1.lon) / dt
        
        # 预测位置
        pred_lat = p2.lat + lat_speed * seconds
        pred_lon = p2.lon + lon_speed * seconds
        
        return pred_lat, pred_lon
    
    def get_direction(self) -> str:
        """获取航行方向"""
        if not self.points:
            return "未知"
        
        last = self.points[-1]
        
        if last.course < 22.5 or last.course >= 337.5:
            return "北"
        elif 22.5 <= last.course < 67.5:
            return "东北"
        elif 67.5 <= last.course < 112.5:
            return "东"
        elif 112.5 <= last.course < 157.5:
            return "东南"
        elif 157.5 <= last.course < 202.5:
            return "南"
        elif 202.5 <= last.course < 247.5:
            return "西南"
        elif 247.5 <= last.course < 292.5:
            return "西"
        else:
            return "西北"
    
    def get_statistics(self) -> dict:
        """获取轨迹统计"""
        if not self.points:
            return {}
        
        speeds = [p.speed for p in self.points]
        courses = [p.course for p in self.points]
        
        return {
            'point_count': len(self.points),
            'avg_speed': sum(speeds) / len(speeds) if speeds else 0,
            'max_speed': max(speeds) if speeds else 0,
            'min_speed': min(speeds) if speeds else 0,
            'direction': self.get_direction(),
            'duration_seconds': (self.points[-1].timestamp - self.points[0].timestamp).total_seconds()
        }


class TrajectoryManager:
    """轨迹管理器"""
    
    def __init__(self, max_points: int = 100):
        self.trajectories = {}
        self.max_points = max_points
    
    def add_target_point(self, target_id: str, lat: float, lon: float,
                        speed: float = 0, course: float = 0):
        """添加目标轨迹点"""
        if target_id not in self.trajectories:
            self.trajectories[target_id] = TargetTrajectory(self.max_points)
        
        self.trajectories[target_id].add_point(lat, lon, speed, course)
    
    def get_trajectory(self, target_id: str) -> Optional[TargetTrajectory]:
        """获取目标轨迹"""
        return self.trajectories.get(target_id)
    
    def predict_position(self, target_id: str, seconds: float = 10) -> Optional[Tuple[float, float]]:
        """预测目标未来位置"""
        traj = self.trajectories.get(target_id)
        if traj:
            return traj.predict_position(seconds)
        return None
    
    def remove_target(self, target_id: str):
        """移除目标轨迹"""
        if target_id in self.trajectories:
            del self.trajectories[target_id]
    
    def get_all_statistics(self) -> dict:
        """获取所有目标轨迹统计"""
        return {
            tid: traj.get_statistics()
            for tid, traj in self.trajectories.items()
        }


if __name__ == '__main__':
    # 测试
    import time
    
    manager = TrajectoryManager(max_points=50)
    
    # 模拟目标移动
    lat, lon = 30.0, 122.0
    for i in range(20):
        lat += 0.001
        lon += 0.001
        speed = 10 + i * 0.1
        course = 45
        
        manager.add_target_point(f'target_{i%3+1}', lat, lon, speed, course)
        time.sleep(0.01)
    
    # 预测
    for tid in ['target_1', 'target_2', 'target_3']:
        pred = manager.predict_position(tid, seconds=30)
        stats = manager.trajectories[tid].get_statistics()
        print(f"{tid}: 预测30秒后=({pred[0]:.4f},{pred[1]:.4f}), "
              f"方向={stats['direction']}, 平均速度={stats['avg_speed']:.1f}kn")
