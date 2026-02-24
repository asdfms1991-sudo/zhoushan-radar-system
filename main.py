"""
舟山定海渔港雷达监控系统 V2.0
主程序入口
"""

import sys
import os
import argparse
import logging
import signal
import time
import threading
from datetime import datetime
from pathlib import Path

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 本地模块
from src.config import Config
from src.logger import setup_logger
from src.radar_parser import RadarParser, create_simulator as create_radar_sim
from src.ais_parser import AISParser, create_simulator as create_ais_sim
from src.fusion import FusionEngine
from src.api import RadarAPI
from src.kalman_filter import MultiTargetKalmanFilter
from src.trajectory import TrajectoryManager
from src.cfar_filter import CFARDetector, ClutterFilter, SpeedFilter
from src.storage import TrajectoryStorage
from src.alert import AlertManager, AlertLevel
from src.classifier import TargetClassifier
from src.performance_monitor import PerformanceMonitor


class RadarSystem:
    """雷达系统主类"""

    def __init__(self, config_path=None):
        # 初始化配置
        self.config = Config(config_path)
        self.logger = self._init_logger()

        # 初始化组件
        self.radar_parser = None
        self.ais_parser = None
        self.fusion_engine = None
        self.api = None
        self.kalman_filter = None
        self.trajectory_manager = None
        self.cfar_detector = None
        self.clutter_filter = None
        self.storage = None
        self.alert_manager = None
        self.classifier = None
        self.performance_monitor = None

        self.running = False

    def _init_logger(self):
        """初始化日志"""
        log_level = self.config.get('system.log_level', 'INFO')
        return setup_logger('radar_system')

    def initialize(self):
        """初始化系统"""
        self.logger.info("初始化雷达系统...")

        # 初始化雷达解析器
        radar_config = self.config.get('radar', {})
        if radar_config.get('enabled', True):
            self.radar_parser = RadarParser(self.config)

        # 初始化AIS解析器
        ais_config = self.config.get('ais', {})
        if ais_config.get('enabled', True):
            self.ais_parser = AISParser(self.config)

        # 初始化融合引擎
        self.fusion_engine = FusionEngine(self.config)
        self.fusion_engine.register_callback(self._on_target_update)

        # 初始化高级模块
        self._init_advanced_modules()

        # 初始化API
        self.api = RadarAPI(self.config, self.fusion_engine)

        self.logger.info("系统初始化完成")

    def _init_advanced_modules(self):
        """初始化高级模块"""
        # Kalman滤波
        self.kalman_filter = MultiTargetKalmanFilter()

        # 轨迹管理
        self.trajectory_manager = TrajectoryManager(max_points=100)

        # CFAR检测
        cfar_config = self.config.fusion_config.get('cfar', {})
        self.cfar_detector = CFARDetector(
            guard_cells=cfar_config.get('guard_cells', 2),
            ref_cells=cfar_config.get('ref_cells', 16),
            p_fa=cfar_config.get('p_fa', 1e-4)
        )

        # 杂波过滤
        clutter_config = self.config.fusion_config.get('clutter', {})
        self.clutter_filter = ClutterFilter(
            min_speed=clutter_config.get('min_speed', 0.5),
            max_speed=clutter_config.get('max_speed', 50.0),
            min_distance=clutter_config.get('min_distance', 0.05),
            max_distance=clutter_config.get('max_distance', 20.0)
        )

        # 轨迹存储
        storage_config = self.config.fusion_config.get('storage', {})
        if storage_config.get('enabled', True):
            self.storage = TrajectoryStorage(
                storage_path=storage_config.get('path', 'data/trajectories')
            )

        # 告警管理
        self.alert_manager = AlertManager()

        # 目标分类
        self.classifier = TargetClassifier()

        # 性能监控
        self.performance_monitor = PerformanceMonitor()

        self.logger.info("高级模块初始化完成")

    def _on_target_update(self, target):
        """目标更新回调"""
        # 转换为字典
        if hasattr(target, '__dict__'):
            target = target.__dict__
        elif not isinstance(target, dict):
            return

        if not target:
            return

        target_id = target.get('id', '')
        lat = target.get('lat', 0)
        lon = target.get('lon', 0)
        speed = target.get('speed_knots', 0)
        course = target.get('course_deg', 0)

        # Kalman滤波
        if self.kalman_filter:
            self.kalman_filter.update_target(target_id, lat, lon)
            kf = self.kalman_filter.filters.get(target_id)
            if kf:
                state = kf.get_state()
                target['kalman_lat'] = state.get('x', lat)
                target['kalman_lon'] = state.get('y', lon)

        # 轨迹记录
        if self.trajectory_manager:
            self.trajectory_manager.add_target_point(target_id, lat, lon, speed, course)
            pred = self.trajectory_manager.predict_position(target_id, seconds=30)
            if pred:
                target['predict_lat'], target['predict_lon'] = pred

        # 杂波过滤
        if self.clutter_filter:
            speed_filter = SpeedFilter(
                min_speed=self.clutter_filter.min_speed,
                max_speed=self.clutter_filter.max_speed
            )
            target['_clutter_passed'] = speed_filter.is_valid(speed)

        # 轨迹持久化
        if self.storage and target_id:
            traj_data = {
                'timestamp': target.get('timestamp', datetime.now().isoformat()),
                'lat': lat,
                'lon': lon,
                'speed_knots': speed,
                'course_deg': course
            }
            self.storage.save_trajectory(target_id, traj_data)

        # 目标分类
        if self.classifier:
            class_result = self.classifier.classify_target(target)
            target['classification'] = class_result

        # 告警检测
        if self.alert_manager:
            alerts = self.alert_manager.check_target(target)
            if alerts:
                self.logger.warning(f"告警: {alerts}")

    def start(self, simulator=False):
        """启动系统"""
        self.running = True

        # 信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self.logger.info("启动雷达系统...")

        # 模拟器模式
        if simulator:
            self._start_simulator()
        else:
            # 正常模式
            self._start_normal()

        # 启动API
        if self.api:
            self.logger.info("启动API服务...")
            api_thread = threading.Thread(target=self.api.run, daemon=True)
            api_thread.start()

        # 等待
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def _start_simulator(self):
        """启动模拟器"""
        self.logger.info("模拟器模式")

        # 创建模拟器（带回调）
        radar_sim = create_radar_sim(lambda t: self.fusion_engine.add_radar_target(t) if t else None)
        ais_sim = create_ais_sim(lambda t: self.fusion_engine.add_ais_target(t) if t else None)

        # 启动线程
        radar_thread = threading.Thread(target=self._run_simulator, args=(radar_sim, ais_sim), daemon=True)
        radar_thread.start()

    def _run_simulator(self, radar_sim, ais_sim):
        """运行模拟器"""
        # 启动模拟器（使用回调）
        radar_sim.start()
        
        # AIS模拟器也启动
        if hasattr(ais_sim, 'start'):
            ais_sim.start()
        
        # 等待
        while self.running:
            time.sleep(1)

    def _start_normal(self):
        """正常模式"""
        self.logger.info("正常模式")

    def stop(self):
        """停止系统"""
        self.logger.info("收到停止信号，正在关闭...")
        self.running = False

    def _signal_handler(self, signum, frame):
        """信号处理"""
        self.stop()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='舟山定海渔港雷达监控系统')
    parser.add_argument('--config', default=None, help='配置文件路径')
    parser.add_argument('--simulator', action='store_true', help='模拟器模式')
    args = parser.parse_args()

    # 创建系统
    system = RadarSystem(args.config)

    # 初始化
    system.initialize()

    # 启动
    system.start(simulator=args.simulator)


if __name__ == '__main__':
    main()
