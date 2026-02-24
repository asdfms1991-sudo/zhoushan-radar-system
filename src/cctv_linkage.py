"""
CCTV联动模块
用于与CCTV系统联动，跟踪目标
"""

from typing import Dict, List, Optional, Callable
from datetime import datetime


class CCTVCamera:
    """CCTV摄像头"""
    
    def __init__(self, camera_id: str, name: str, 
                 lat: float, lon: float,
                 pan: float = 0, tilt: float = 0, zoom: float = 1):
        self.camera_id = camera_id
        self.name = name
        self.lat = lat
        self.lon = lon
        self.pan = pan      # 水平角度
        self.tilt = tilt    # 垂直角度
        self.zoom = zoom    # 缩放
    
    def to_dict(self) -> dict:
        return {
            'camera_id': self.camera_id,
            'name': self.name,
            'lat': self.lat,
            'lon': self.lon,
            'pan': self.pan,
            'tilt': self.tilt,
            'zoom': self.zoom
        }


class CCTVLinkage:
    """CCTV联动控制器"""
    
    def __init__(self):
        self.cameras: Dict[str, CCTVCamera] = {}
        self.current_tracking: Dict[str, str] = {}  # target_id -> camera_id
        self.callbacks: List[Callable] = []
    
    def add_camera(self, camera: CCTVCamera):
        """添加摄像头"""
        self.cameras[camera.camera_id] = camera
    
    def add_camera_by_params(self, camera_id: str, name: str, 
                           lat: float, lon: float) -> bool:
        """添加摄像头（简化参数）"""
        camera = CCTVCamera(camera_id, name, lat, lon)
        self.cameras[camera_id] = camera
        return True
    
    def remove_camera(self, camera_id: str):
        """移除摄像头"""
        if camera_id in self.cameras:
            del self.cameras[camera_id]
    
    def find_nearest_camera(self, lat: float, lon: float) -> Optional[CCTVCamera]:
        """找到最近的摄像头"""
        if not self.cameras:
            return None
        
        import math
        
        nearest = None
        min_distance = float('inf')
        
        for camera in self.cameras.values():
            # 简化距离计算
            distance = math.sqrt(
                (camera.lat - lat)**2 + (camera.lon - lon)**2
            )
            if distance < min_distance:
                min_distance = distance
                nearest = camera
        
        return nearest
    
    def track_target(self, target_id: str, lat: float, lon: float) -> dict:
        """跟踪目标"""
        # 找到最近的摄像头
        camera = self.find_nearest_camera(lat, lon)
        
        if not camera:
            return {
                'success': False,
                'message': 'No camera available'
            }
        
        # 计算摄像头朝向（简化）
        import math
        delta_lat = lat - camera.lat
        delta_lon = lon - camera.lon
        
        # 计算方向角
        if delta_lon == 0:
            direction = 90 if delta_lat > 0 else 270
        else:
            direction = math.degrees(math.atan2(delta_lat, delta_lon))
        
        # 更新跟踪
        self.current_tracking[target_id] = camera.camera_id
        
        # 触发回调
        self._trigger_callbacks({
            'target_id': target_id,
            'camera_id': camera.camera_id,
            'camera_name': camera.name,
            'direction': direction,
            'timestamp': datetime.now().isoformat()
        })
        
        return {
            'success': True,
            'target_id': target_id,
            'camera': camera.to_dict(),
            'direction': direction,
            'message': f'Tracking {target_id} on {camera.name}'
        }
    
    def stop_tracking(self, target_id: str) -> bool:
        """停止跟踪"""
        if target_id in self.current_tracking:
            del self.current_tracking[target_id]
            return True
        return False
    
    def get_tracking_status(self) -> dict:
        """获取跟踪状态"""
        status = {}
        for target_id, camera_id in self.current_tracking.items():
            camera = self.cameras.get(camera_id)
            status[target_id] = {
                'camera_id': camera_id,
                'camera_name': camera.name if camera else 'Unknown'
            }
        return status
    
    def register_callback(self, callback: Callable):
        """注册回调"""
        self.callbacks.append(callback)
    
    def _trigger_callbacks(self, data: dict):
        """触发回调"""
        for callback in self.callbacks:
            try:
                callback(data)
            except Exception as e:
                print(f"CCTV callback error: {e}")
    
    def get_all_cameras(self) -> List[dict]:
        """获取所有摄像头"""
        return [c.to_dict() for c in self.cameras.values()]
    
    def get_statistics(self) -> dict:
        """获取统计"""
        return {
            'total_cameras': len(self.cameras),
            'tracking_count': len(self.current_tracking),
            'cameras': list(self.cameras.keys())
        }


# 测试
if __name__ == '__main__':
    cctv = CCTVLinkage()
    
    # 添加摄像头
    cctv.add_camera_by_params('cam1', '港口摄像头1', 30.017, 122.107)
    cctv.add_camera_by_params('cam2', '港口摄像头2', 30.020, 122.110)
    
    # 跟踪目标
    result = cctv.track_target('target_1', 30.018, 122.108)
    print(result)
    
    # 获取状态
    print(f"\n跟踪状态: {cctv.get_tracking_status()}")
    print(f"\n统计: {cctv.get_statistics()}")
