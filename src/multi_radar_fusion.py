"""
多雷达融合模块
支持多台雷达数据融合
"""

from typing import Dict, List
import math


class MultiRadarFusion:
    """多雷达融合引擎"""
    
    def __init__(self):
        self.stations: Dict[str, dict] = {}
        self.fused_targets: Dict[str, dict] = {}
        self.association_distance_m = 500
    
    def add_radar(self, station_id: str, name: str, lat: float, lon: float):
        """添加雷达站"""
        self.stations[station_id] = {
            'id': station_id,
            'name': name,
            'lat': lat,
            'lon': lon,
            'targets': {}
        }
    
    def add_target(self, station_id: str, target: dict):
        """添加目标"""
        if station_id not in self.stations:
            self.add_radar(station_id, station_id, 0, 0)
        
        target['station_id'] = station_id
        self.stations[station_id]['targets'][target.get('id', '')] = target
    
    def fuse(self) -> List[dict]:
        """融合所有雷达站数据"""
        self.fused_targets = {}
        
        # 收集所有目标
        all_targets = []
        for station in self.stations.values():
            for target in station['targets'].values():
                all_targets.append(target)
        
        # 简单融合：按ID聚合
        used = set()
        results = []
        
        for i, target in enumerate(all_targets):
            if i in used:
                continue
            
            tid = target.get('id', f'tmp_{i}')
            fused = {
                'id': tid,
                'lat': target.get('lat', 0),
                'lon': target.get('lon', 0),
                'speed_knots': target.get('speed_knots', 0),
                'course_deg': target.get('course_deg', 0),
                'station_ids': [target.get('station_id', 'unknown')],
                'is_fused': False,
                'source_count': 1
            }
            
            # 查找相近目标
            for j, other in enumerate(all_targets):
                if j <= i or j in used:
                    continue
                if self._is_close(target, other):
                    fused['station_ids'].append(other.get('station_id', 'unknown'))
                    fused['source_count'] += 1
                    used.add(j)
            
            if fused['source_count'] > 1:
                fused['is_fused'] = True
            
            used.add(i)
            results.append(fused)
            self.fused_targets[fused['id']] = fused
        
        return results
    
    def _is_close(self, t1: dict, t2: dict) -> bool:
        """检查两目标是否相近"""
        d = self._distance(
            t1.get('lat', 0), t1.get('lon', 0),
            t2.get('lat', 0), t2.get('lon', 0)
        )
        return d < self.association_distance_m
    
    def _distance(self, lat1, lon1, lat2, lon2) -> float:
        """计算距离（米）"""
        R = 6371000
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    def get_stats(self) -> dict:
        """获取统计"""
        return {
            'stations': len(self.stations),
            'targets': sum(len(s['targets']) for s in self.stations.values()),
            'fused': len(self.fused_targets)
        }


if __name__ == '__main__':
    fusion = MultiRadarFusion()
    fusion.add_radar('r1', '雷达1', 30.017, 122.107)
    fusion.add_target('r1', {'id': 'T1', 'lat': 30.018, 'lon': 122.108, 'speed_knots': 10})
    result = fusion.fuse()
    print(f"融合结果: {len(result)} 目标")
    print(f"统计: {fusion.get_stats()}")
