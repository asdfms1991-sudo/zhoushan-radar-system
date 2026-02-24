"""
数据模型定义 V2.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import math


class TargetType(Enum):
    """目标类型"""
    RADAR = "radar"
    AIS = "ais"
    FUSED = "fused"


class TargetStatus(Enum):
    """目标状态"""
    NEW = "new"
    TRACKING = "tracking"
    LOST = "lost"
    FUSED = "fused"


@dataclass
class Position:
    """位置"""
    lat: float = 0.0      # 纬度
    lon: float = 0.0      # 经度
    
    def to_dict(self) -> dict:
        return {'lat': round(self.lat, 6), 'lon': round(self.lon, 6)}


@dataclass
class RadarTarget:
    """雷达目标"""
    target_id: str
    distance_nm: float           # 距离（海里）
    bearing_deg: float          # 方位角（度）
    speed_knots: float        # 速度（节）
    course_deg: float         # 航向（度）
    target_type: str = 'M'    # 目标类型
    name: str = ''
    status: str = 'A'          # 状态
    signal_strength: float = 0  # 信号强度
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def distance_m(self) -> float:
        return self.distance_nm * 1852
    
    @property
    def speed_ms(self) -> float:
        return self.speed_knots * 0.514444
    
    @property
    def position(self) -> Position:
        return Position()
    
    def to_dict(self) -> dict:
        return {
            'type': 'radar',
            'id': self.target_id,
            'name': self.name,
            'distance_nm': round(self.distance_nm, 3),
            'distance_m': round(self.distance_m, 1),
            'bearing_deg': round(self.bearing_deg, 1),
            'speed_knots': round(self.speed_knots, 1),
            'speed_ms': round(self.speed_ms, 2),
            'course_deg': round(self.course_deg, 1),
            'target_type': self.target_type,
            'status': self.status,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class AISTarget:
    """AIS目标"""
    mmsi: str
    name: str = ''
    lat: float = 0.0
    lon: float = 0.0
    speed_knots: float = 0.0
    course_deg: float = 0.0
    heading_deg: int = 0
    ship_type: str = ''
    imo: str = ''
    call_sign: str = ''
    dest: str = ''
    eta: str = ''
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def speed_ms(self) -> float:
        return self.speed_knots * 0.514444
    
    @property
    def position(self) -> Position:
        return Position(lat=self.lat, lon=self.lon)
    
    def to_dict(self) -> dict:
        return {
            'type': 'ais',
            'mmsi': self.mmsi,
            'name': self.name,
            'lat': round(self.lat, 6),
            'lon': round(self.lon, 6),
            'speed_knots': round(self.speed_knots, 1),
            'speed_ms': round(self.speed_ms, 2),
            'course_deg': round(self.course_deg, 1),
            'heading_deg': self.heading_deg,
            'ship_type': self.ship_type,
            'imo': self.imo,
            'call_sign': self.call_sign,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class FusedTarget:
    """融合目标"""
    fused_id: str
    radar_target: Optional[RadarTarget] = None
    ais_target: Optional[AISTarget] = None
    source_type: str = 'radar'  # radar/ais/fused
    lat: float = 0.0
    lon: float = 0.0
    speed_knots: float = 0.0
    course_deg: float = 0.0
    heading_deg: int = 0
    confidence: float = 1.0
    status: str = 'tracking'
    timestamp: datetime = field(default_factory=datetime.now)
    history: List[Dict] = field(default_factory=list)
    
    @property
    def speed_ms(self) -> float:
        return self.speed_knots * 0.514444
    
    @property
    def position(self) -> Position:
        return Position(lat=self.lat, lon=self.lon)
    
    def update(self, radar_target: RadarTarget = None, ais_target: AISTarget = None):
        """更新融合目标"""
        if radar_target:
            self.radar_target = radar_target
            self.speed_knots = radar_target.speed_knots
            self.course_deg = radar_target.course_deg
        
        if ais_target:
            self.ais_target = ais_target
            self.lat = ais_target.lat
            self.lon = ais_target.lon
            if ais_target.speed_knots > 0:
                self.speed_knots = ais_target.speed_knots
            if ais_target.heading_deg > 0:
                self.heading_deg = ais_target.heading_deg
        
        # 更新融合状态
        has_radar = self.radar_target is not None
        has_ais = self.ais_target is not None
        
        if has_radar and has_ais:
            self.source_type = 'fused'
            self.confidence = 0.9
        elif has_ais:
            self.source_type = 'ais'
            self.confidence = 0.8
        else:
            self.source_type = 'radar'
            self.confidence = 0.7
        
        self.timestamp = datetime.now()
        
        # 记录历史
        self.history.append({
            'lat': self.lat,
            'lon': self.lon,
            'speed': self.speed_knots,
            'timestamp': self.timestamp.isoformat()
        })
        
        # 保持最近100条历史
        if len(self.history) > 100:
            self.history = self.history[-100:]
    
    def to_dict(self) -> dict:
        return {
            'type': 'fused',
            'id': self.fused_id,
            'source_type': self.source_type,
            'has_radar': self.radar_target is not None,
            'has_ais': self.ais_target is not None,
            'lat': round(self.lat, 6),
            'lon': round(self.lon, 6),
            'speed_knots': round(self.speed_knots, 1),
            'speed_ms': round(self.speed_ms, 2),
            'course_deg': round(self.course_deg, 1),
            'heading_deg': self.heading_deg,
            'confidence': round(self.confidence, 2),
            'status': self.status,
            'name': self.ais_target.name if self.ais_target else self.radar_target.name if self.radar_target else '',
            'mmsi': self.ais_target.mmsi if self.ais_target else '',
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class SystemStatus:
    """系统状态"""
    running: bool = False
    radar_connected: bool = False
    ais_connected: bool = False
    radar_targets_count: int = 0
    ais_targets_count: int = 0
    fused_targets_count: int = 0
    uptime_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)
    start_time: Optional[datetime] = None
    
    def add_error(self, error: str):
        self.errors.append(f"{datetime.now().isoformat()}: {error}")
        if len(self.errors) > 100:
            self.errors = self.errors[-100:]
    
    def to_dict(self) -> dict:
        return {
            'running': self.running,
            'radar_connected': self.radar_connected,
            'ais_connected': self.ais_connected,
            'radar_targets': self.radar_targets_count,
            'ais_targets': self.ais_targets_count,
            'fused_targets': self.fused_targets_count,
            'uptime_seconds': round(self.uptime_seconds, 1),
            'errors': self.errors[-10:] if self.errors else [],
            'start_time': self.start_time.isoformat() if self.start_time else None
        }


@dataclass
class TargetUpdate:
    """目标更新消息"""
    action: str  # add, update, remove
    target_type: str  # radar, ais, fused
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            'action': self.action,
            'target_type': self.target_type,
            'data': self.data,
            'timestamp': self.timestamp.isoformat()
        }
