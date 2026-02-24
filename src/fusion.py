"""
目标融合引擎 V2.1
修正：雷达覆盖所有目标，AIS是子集
"""

import math
import logging
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Callable

from src.config import Config
from src.models import RadarTarget, AISTarget, FusedTarget

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TargetFusion:
    """目标融合引擎 - 修正版"""

    def __init__(self, config: Config, callback: Optional[Callable] = None):
        self.config = config
        self.callback = callback
        self.logger = logging.getLogger('fusion')

        fusion_config = config.fusion_config
        self.enabled = fusion_config.get('enabled', True)

        # 融合参数
        self.association_distance = fusion_config.get(
            'association_distance_m', 100)
        self.max_age = fusion_config.get('max_age_seconds', 60)

        # 目标存储
        self.radar_targets: Dict[str, RadarTarget] = {}
        self.ais_targets: Dict[str, AISTarget] = {}
        self.fused_targets: Dict[str, FusedTarget] = {}

        # 匹配记录
        self.matched_ais = set()  # 已匹配的AIS

        # 雷达原点
        self.radar_origin = (0.0, 0.0)

    def set_radar_origin(self, lon: float, lat: float):
        self.radar_origin = (lon, lat)
        self.logger.info(f"雷达原点: ({lon}, {lat})")

    def add_radar_target(self, target: RadarTarget):
        """添加雷达目标"""
        self.radar_targets[target.target_id] = target
        self._fuse_radar_target(target)

    def add_ais_target(self, target: AISTarget):
        """添加AIS目标"""
        self.ais_targets[target.mmsi] = target

        # 先尝试与现有雷达目标匹配
        matched_radar = self._find_matching_radar(target.lat, target.lon)

        if matched_radar:
            # 有匹配的雷达目标，创建融合目标
            self.matched_ais.add(target.mmsi)

            # 转换雷达位置到地理坐标
            lat, lon = self._radar_to_geo(
                matched_radar.distance_nm,
                matched_radar.bearing_deg,
                self.radar_origin[1],
                self.radar_origin[0]
            )

            fused_id = f"F{target.mmsi}"

            fused = FusedTarget(
                fused_id=fused_id,
                radar_target=matched_radar,
                ais_target=target,
                source_type='fused',
                lat=lat,
                lon=lon,
                speed_knots=target.speed_knots or matched_radar.speed_knots,
                course_deg=target.course_deg or matched_radar.course_deg,
                confidence=0.9
            )
            self.fused_targets[fused_id] = fused

            if self.callback:
                self.callback(fused)
        else:
            # 没有匹配的雷达目标，仅AIS
            self._fuse_ais_only(target)

    def _fuse_radar_target(self, radar_target: RadarTarget):
        """
        融合雷达目标
        核心逻辑：雷达检测到所有船舶，尝试找匹配的AIS
        """
        # 转换雷达位置到地理坐标
        lat, lon = self._radar_to_geo(
            radar_target.distance_nm,
            radar_target.bearing_deg,
            self.radar_origin[1],
            self.radar_origin[0]
        )

        # 查找匹配的AIS（在范围内）
        matched_ais = self._find_matching_ais(lat, lon)

        if matched_ais:
            # 融合目标：雷达+AIS双重确认
            self.matched_ais.add(matched_ais.mmsi)
            fused_id = f"F{matched_ais.mmsi}"  # 用MMSI作为ID

            fused = FusedTarget(
                fused_id=fused_id,
                radar_target=radar_target,
                ais_target=matched_ais,
                source_type='fused',
                lat=lat,
                lon=lon,
                speed_knots=matched_ais.speed_knots or radar_target.speed_knots,
                course_deg=matched_ais.course_deg or radar_target.course_deg,
                confidence=0.9  # 高置信度
            )
        else:
            # 仅雷达目标：没有匹配的AIS
            fused_id = f"R{radar_target.target_id}"

            fused = FusedTarget(
                fused_id=fused_id,
                radar_target=radar_target,
                source_type='radar',
                lat=lat,
                lon=lon,
                speed_knots=radar_target.speed_knots,
                course_deg=radar_target.course_deg,
                confidence=0.7
            )

        self.fused_targets[fused_id] = fused

        if self.callback:
            self.callback(fused)

        self.logger.debug(
            f"雷达目标: {radar_target.target_id} -> {fused_id} ({fused.source_type})")

    def _fuse_ais_only(self, ais_target: AISTarget):
        """
        处理仅有AIS的目标
        这种情况可能是：雷达未检测到（如遮挡、距离太远）
        """
        # 查找是否已有匹配的雷达目标
        matched_radar = self._find_matching_radar(
            ais_target.lat, ais_target.lon)

        if matched_radar:
            # 已有雷达匹配，忽略（已在_radar中处理）
            pass
        else:
            # 仅AIS目标
            fused_id = f"A{ais_target.mmsi}"

            fused = FusedTarget(
                fused_id=fused_id,
                ais_target=ais_target,
                source_type='ais',
                lat=ais_target.lat,
                lon=ais_target.lon,
                speed_knots=ais_target.speed_knots,
                course_deg=ais_target.course_deg,
                heading_deg=ais_target.heading_deg,
                confidence=0.8
            )

            self.fused_targets[fused_id] = fused

            if self.callback:
                self.callback(fused)

            self.logger.debug(f"AIS目标: {ais_target.mmsi} -> {fused_id} (仅AIS)")

    def _find_matching_ais(self, lat: float,
                           lon: float) -> Optional[AISTarget]:
        """查找匹配的AIS目标"""
        for ais in self.ais_targets.values():
            if ais.mmsi in self.matched_ais:
                continue  # 已匹配
            distance = self._haversine_distance(lat, lon, ais.lat, ais.lon)
            if distance < self.association_distance:
                return ais
        return None

    def _find_matching_radar(self, lat: float,
                             lon: float) -> Optional[RadarTarget]:
        """查找匹配的雷达目标"""
        for radar in self.radar_targets.values():
            r_lat, r_lon = self._radar_to_geo(
                radar.distance_nm,
                radar.bearing_deg,
                self.radar_origin[1],
                self.radar_origin[0]
            )
            distance = self._haversine_distance(lat, lon, r_lat, r_lon)
            if distance < self.association_distance:
                return radar
        return None

    def _radar_to_geo(self, distance_nm: float, bearing_deg: float,
                      ref_lat: float, ref_lon: float) -> tuple:
        """雷达极坐标 -> 地理坐标"""
        distance_m = distance_nm * 1852
        distance_deg = distance_m / 111000

        bearing_rad = math.radians(bearing_deg)

        lat = ref_lat + distance_deg * math.cos(bearing_rad)
        lon = ref_lon + distance_deg * \
            math.sin(bearing_rad) / math.cos(math.radians(ref_lat))

        return (lat, lon)

    def _haversine_distance(self, lat1: float, lon1: float,
                            lat2: float, lon2: float) -> float:
        """Haversine距离（米）"""
        R = 6371000
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def get_fused_targets(self) -> List[FusedTarget]:
        """获取所有融合目标"""
        # 清理过期目标
        now = datetime.now()
        expired = []
        for fid, target in self.fused_targets.items():
            if (now - target.timestamp).total_seconds() > self.max_age:
                expired.append(fid)
        for fid in expired:
            del self.fused_targets[fid]

        return list(self.fused_targets.values())

    def get_stats(self) -> dict:
        """获取统计"""
        fused = self.get_fused_targets()

        radar_only = sum(1 for t in fused if t.source_type == 'radar')
        ais_only = sum(1 for t in fused if t.source_type == 'ais')
        fused_count = sum(1 for t in fused if t.source_type == 'fused')

        return {
            'radar_targets': len(self.radar_targets),
            'ais_targets': len(self.ais_targets),
            'fused_targets': len(fused),
            'radar_only': radar_only,
            'ais_only': ais_only,
            'fused_count': fused_count
        }


class FusionEngine:
    """融合引擎主类"""

    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger('fusion_engine')

        self.fusion = TargetFusion(config, self._on_fused)
        self.callbacks = []

        self.radar_targets = {}
        self.ais_targets = {}
        self.fused_targets = {}

    def _on_fused(self, target: FusedTarget):
        self.fused_targets[target.fused_id] = target
        for callback in self.callbacks:
            callback(target)

    def add_radar_target(self, target: RadarTarget):
        self.radar_targets[target.target_id] = target
        self.fusion.add_radar_target(target)

    def add_ais_target(self, target: AISTarget):
        self.ais_targets[target.mmsi] = target
        self.fusion.add_ais_target(target)

    def register_callback(self, callback: Callable):
        self.callbacks.append(callback)

    def get_all_targets(self) -> dict:
        stats = self.fusion.get_stats()
        return {
            'radar': [t.to_dict() for t in self.radar_targets.values()],
            'ais': [t.to_dict() for t in self.ais_targets.values()],
            'fused': [t.to_dict() for t in self.fusion.get_fused_targets()],
            'stats': stats
        }


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    from config import Config
    config = Config()
    engine = FusionEngine(config)
    engine.fusion.set_radar_origin(122.0, 30.0)

    import random

    # 模拟雷达检测到10个目标
    for i in range(10):
        target = RadarTarget(
            target_id=str(i + 1),
            distance_nm=random.uniform(0.5, 5.0),
            bearing_deg=random.uniform(0, 360),
            speed_knots=random.uniform(5, 15),
            course_deg=random.uniform(0, 360)
        )
        engine.add_radar_target(target)

    # 模拟AIS（其中3个在雷达范围内）
    for i in range(3):
        target = AISTarget(
            mmsi=f"200{100000 + i}",

            lat=30.0 + random.uniform(-0.001, 0.001),
            lon=122.0 + random.uniform(-0.001, 0.001),
            speed_knots=random.uniform(8, 12),
            course_deg=random.uniform(0, 360)
        )
        engine.add_ais_target(target)

    import time
    time.sleep(0.5)

    data = engine.get_all_targets()
    stats = data['stats']

    print(f"\n=== 融合结果 ===")
    print(f"雷达检测: {stats['radar_targets']} 个")
    print(f"AIS报告: {stats['ais_targets']} 个")
    print(f"融合目标: {stats['fused_targets']} 个")
    print(f"  - 雷达单独: {stats['radar_only']} 个")
    print(f"  - AIS单独: {stats['ais_only']} 个")
    print(f"  - 融合确认: {stats['fused_count']} 个")
    print("=" * 20)
