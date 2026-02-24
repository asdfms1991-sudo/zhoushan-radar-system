"""
历史回放模块
用于轨迹历史数据的查询和回放
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class HistoryPlayer:
    """历史回放器"""
    
    def __init__(self, storage_path: str = "data/trajectories"):
        self.storage_path = Path(storage_path)
    
    def get_target_history(self, target_id: str, 
                          start_time: datetime = None,
                          end_time: datetime = None) -> List[dict]:
        """
        获取目标历史轨迹
        
        Args:
            target_id: 目标ID
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            轨迹点列表
        """
        import os
        safe_id = target_id.replace('/', '_').replace('\\', '_')
        file_path = self.storage_path / f"{safe_id}.json"
        
        if not file_path.exists():
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            points = data.get('trajectory', [])
            
            # 时间过滤
            if start_time or end_time:
                filtered = []
                for point in points:
                    ts = point.get('timestamp', '')
                    if isinstance(ts, str):
                        try:
                            pt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                        except:
                            continue
                    else:
                        continue
                    
                    if start_time and pt < start_time:
                        continue
                    if end_time and pt > end_time:
                        continue
                    
                    filtered.append(point)
                
                return filtered
            
            return points
            
        except Exception as e:
            print(f"读取历史失败: {e}")
            return []
    
    def get_all_targets_at_time(self, timestamp: datetime) -> List[dict]:
        """
        获取指定时间点的所有目标位置
        
        Args:
            timestamp: 时间点
            
        Returns:
            目标列表
        """
        # 遍历所有轨迹文件
        results = []
        
        for file_path in self.storage_path.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                target_id = data.get('target_id', file_path.stem)
                trajectory = data.get('trajectory', [])
                
                # 找到最接近的时间点
                closest = None
                min_diff = float('inf')
                
                for point in trajectory:
                    ts = point.get('timestamp', '')
                    if isinstance(ts, str):
                        try:
                            pt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                            diff = abs((pt - timestamp).total_seconds())
                            if diff < min_diff:
                                min_diff = diff
                                closest = point
                        except:
                            continue
                
                if closest and min_diff < 60:  # 60秒内
                    closest['target_id'] = target_id
                    results.append(closest)
                    
            except Exception as e:
                continue
        
        return results
    
    def get_statistics(self, target_id: str = None) -> dict:
        """获取统计信息"""
        import os
        
        if target_id:
            safe_id = target_id.replace('/', '_').replace('\\', '_')
            file_path = self.storage_path / f"{safe_id}.json"
            
            if not file_path.exists():
                return {}
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                trajectory = data.get('trajectory', [])
                if not trajectory:
                    return {}
                
                speeds = [p.get('speed_knots', 0) for p in trajectory if 'speed_knots' in p]
                
                return {
                    'target_id': target_id,
                    'total_points': len(trajectory),
                    'avg_speed': sum(speeds) / len(speeds) if speeds else 0,
                    'max_speed': max(speeds) if speeds else 0,
                    'min_speed': min(speeds) if speeds else 0,
                    'first_timestamp': trajectory[0].get('timestamp', ''),
                    'last_timestamp': trajectory[-1].get('timestamp', '')
                }
            except:
                return {}
        
        # 全部统计
        total_points = 0
        file_count = 0
        
        for file_path in self.storage_path.glob("*.json"):
            file_count += 1
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    total_points += len(data.get('trajectory', []))
            except:
                continue
        
        return {
            'total_targets': file_count,
            'total_points': total_points
        }


# 测试
if __name__ == '__main__':
    player = HistoryPlayer('data/trajectories')
    
    # 测试统计
    stats = player.get_statistics()
    print(f"统计: {stats}")
