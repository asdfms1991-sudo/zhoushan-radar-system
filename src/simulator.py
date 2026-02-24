"""
模拟数据生成器
用于生成测试和验证的模拟雷达/AIS数据
"""

import numpy as np
import json
from datetime import datetime, timedelta


class RadarSimulator:
    """雷达数据模拟器"""
    
    def __init__(self, origin_lat=30.017, origin_lon=122.107):
        self.origin_lat = origin_lat
        self.origin_lon = origin_lon
    
    def generate_target(self, target_id, lat, lon, speed, course):
        """生成雷达目标"""
        # 计算距离和方位角
        distance_nm = self._calculate_distance_nm(lat, lon)
        bearing = self._calculate_bearing(lat, lon)
        
        return {
            'id': target_id,
            'type': 'radar',
            'lat': lat,
            'lon': lon,
            'distance_nm': distance_nm,
            'bearing_deg': bearing,
            'speed_knots': speed,
            'course_deg': course,
            'timestamp': datetime.now().isoformat(),
            'signal_strength': np.random.uniform(-50, -20),
            'snr': np.random.uniform(10, 30)
        }
    
    def _calculate_distance_nm(self, lat, lon):
        """计算距离（海里）"""
        import math
        R = 3440.065  # 地球半径（海里）
        dlat = math.radians(lat - self.origin_lat)
        dlon = math.radians(lon - self.origin_lon)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(self.origin_lat)) * math.cos(math.radians(lat)) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
    
    def _calculate_bearing(self, lat, lon):
        """计算方位角"""
        import math
        dlon = math.radians(lon - self.origin_lon)
        y = math.sin(dlon) * math.cos(math.radians(lat))
        x = math.cos(math.radians(self.origin_lat)) * math.sin(math.radians(lat)) - math.sin(math.radians(self.origin_lat)) * math.cos(math.radians(lat)) * math.cos(dlon)
        bearing = math.degrees(math.atan2(y, x))
        return (bearing + 360) % 360
    
    def generate_batch(self, num_targets=10, area_size=0.1):
        """批量生成目标"""
        targets = []
        
        for i in range(num_targets):
            lat = self.origin_lat + np.random.uniform(-area_size, area_size)
            lon = self.origin_lon + np.random.uniform(-area_size, area_size)
            speed = np.random.uniform(0, 30)
            course = np.random.uniform(0, 360)
            
            targets.append(self.generate_target(f'R{i+1:03d}', lat, lon, speed, course))
        
        return targets


class AISSimulator:
    """AIS数据模拟器"""
    
    SHIP_TYPES = ['fishing', 'cargo', 'tanker', 'passenger', 'yacht']
    
    def __init__(self):
        pass
    
    def generate_target(self, mmsi, name, lat, lon, speed, course, ship_type=None):
        """生成AIS目标"""
        return {
            'id': mmsi,
            'type': 'ais',
            'mmsi': mmsi,
            'name': name,
            'lat': lat,
            'lon': lon,
            'speed_knots': speed,
            'course_deg': course,
            'heading': course,
            'ship_type': ship_type or np.random.choice(self.SHIP_TYPES),
            'imo': f'IMO{np.random.randint(9000000, 9999999)}',
            'callsign': f'{chr(65+np.random.randint(0,26))}{chr(65+np.random.randint(0,26))}{chr(65+np.random.randint(0,26))}',
            'destination': 'ZHOSHAN',
            'eta': (datetime.now() + timedelta(days=np.random.randint(1, 7))).strftime('%Y-%m-%d %H:%M'),
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_batch(self, num_targets=5, area_size=0.1, origin_lat=30.017, origin_lon=122.107):
        """批量生成目标"""
        targets = []
        
        for i in range(num_targets):
            mmsi = f'2{np.random.randint(0, 9)}{np.random.randint(100000, 999999)}'
            name = f'SHIP_{i+1:03d}'
            lat = origin_lat + np.random.uniform(-area_size, area_size)
            lon = origin_lon + np.random.uniform(-area_size, area_size)
            speed = np.random.uniform(5, 25)
            course = np.random.uniform(0, 360)
            ship_type = np.random.choice(self.SHIP_TYPES)
            
            targets.append(self.generate_target(mmsi, name, lat, lon, speed, course, ship_type))
        
        return targets


class ScenarioSimulator:
    """场景模拟器 - 生成复杂测试场景"""
    
    def __init__(self):
        self.radar_sim = RadarSimulator()
        self.ais_sim = AISSimulator()
    
    def generate_simple_scene(self):
        """简单场景"""
        radar_targets = self.radar_sim.generate_batch(5)
        ais_targets = self.ais_sim.generate_batch(3)
        
        return {
            'radar': radar_targets,
            'ais': ais_targets,
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_tracking_scene(self):
        """跟踪场景 - 单目标长时间跟踪"""
        targets = []
        
        # 单一目标跟踪
        lat, lon = 30.02, 122.11
        for i in range(50):
            lat += 0.001
            lon += 0.001
            speed = 10 + np.random.randn() * 0.5
            course = 45 + np.random.randn() * 2
            
            targets.append({
                'id': 'TRACK_001',
                'lat': lat,
                'lon': lon,
                'speed_knots': speed,
                'course_deg': course,
                'timestamp': (datetime.now() + timedelta(seconds=i)).isoformat()
            })
        
        return targets
    
    def generate_fusion_scene(self):
        """融合场景 - 雷达和AIS目标位置接近"""
        radar_targets = []
        ais_targets = []
        
        for i in range(5):
            lat = 30.02 + i * 0.002
            lon = 122.11 + i * 0.002
            
            # 雷达目标
            radar_targets.append(self.radar_sim.generate_target(f'R{i+1:03d}', lat, lon, 12, 45))
            
            # AIS目标（位置接近但不完全相同）
            ais_targets.append(self.ais_sim.generate_target(
                f'2{np.random.randint(0,9)}{np.random.randint(100000,999999)}',
                f'FUSION_{i+1}',
                lat + np.random.uniform(-0.0001, 0.0001),
                lon + np.random.uniform(-0.0001, 0.0001),
                12, 45
            ))
        
        return {
            'radar': radar_targets,
            'ais': ais_targets,
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_weather_scene(self):
        """天气场景 - 不同天气条件"""
        weather_modes = ['calm', 'moderate', 'rough', 'storm']
        scenes = {}
        
        for mode in weather_modes:
            # 杂波级别随天气增加
            clutter_factor = {'calm': 0.1, 'moderate': 0.3, 'rough': 0.6, 'storm': 0.9}[mode]
            
            targets = self.radar_sim.generate_batch(
                num_targets=int(10 * (1 - clutter_factor))
            )
            
            # 添加一些虚假目标（杂波）
            for _ in range(int(5 * clutter_factor)):
                targets.append(self.radar_sim.generate_target(
                    f'CLUTTER_{np.random.randint(100,999)}',
                    self.radar_sim.origin_lat + np.random.uniform(-0.05, 0.05),
                    self.radar_sim.origin_lon + np.random.uniform(-0.05, 0.05),
                    np.random.uniform(0, 1),  # 低速
                    np.random.uniform(0, 360)
                ))
            
            scenes[mode] = {
                'weather': mode,
                'targets': targets,
                'clutter_level': clutter_factor
            }
        
        return scenes


# 测试
if __name__ == '__main__':
    print("=" * 50)
    print("模拟数据生成测试")
    print("=" * 50)
    
    # 测试简单场景
    scene = ScenarioSimulator()
    simple = scene.generate_simple_scene()
    print(f"\n简单场景: 雷达{len(simple['radar'])}个, AIS{len(simple['ais'])}个")
    
    # 测试融合场景
    fusion = scene.generate_fusion_scene()
    print(f"融合场景: 雷达{len(fusion['radar'])}个, AIS{len(fusion['ais'])}个")
    
    # 测试天气场景
    weather = scene.generate_weather_scene()
    print(f"\n天气场景:")
    for mode, data in weather.items():
        print(f"  {mode}: {len(data['targets'])}个目标, 杂波级别:{data['clutter_level']}")
