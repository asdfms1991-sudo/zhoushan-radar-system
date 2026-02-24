"""
单元测试
测试雷达系统各模块
"""

import pytest
import numpy as np
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.advanced_tracker import KFTracker, TrackerFactory
from src.fusion import FusionEngine
from src.config import Config
from src.alert import AlertManager
from src.classifier import TargetClassifier


class TestKFTracker:
    """测试卡尔曼滤波"""

    def test_create(self):
        tracker = KFTracker()
        assert tracker is not None

    def test_initialize(self):
        tracker = KFTracker()
        x, y = tracker.process(10.0, 20.0)
        assert x == 10.0
        assert y == 20.0

    def test_tracking(self):
        tracker = KFTracker()
        errors = []
        x = y = 0

        for i in range(20):
            x += 1.5
            y += 0.5
            mx = x + np.random.randn() * 0.3
            my = y + np.random.randn() * 0.3
            ex, ey = tracker.process(mx, my)
            error = np.sqrt((ex - x)**2 + (ey - y)**2)
            errors.append(error)

        # 平均误差应该小于1
        assert np.mean(errors) < 1.0

    def test_get_state(self):
        tracker = KFTracker()
        tracker.process(10.0, 20.0)
        state = tracker.get_state()
        assert 'x' in state
        assert 'y' in state
        assert 'speed' in state


class TestTrackerFactory:
    """测试跟踪器工厂"""

    def test_create_kf(self):
        tracker = TrackerFactory.create('KF')
        assert isinstance(tracker, KFTracker)

    def test_list_algorithms(self):
        algos = TrackerFactory.list_algorithms()
        assert 'KF' in algos
        assert 'EKF' in algos
        assert 'UKF' in algos


class TestFusionEngine:
    """测试融合引擎"""

    def test_create(self):
        config = Config()
        fusion = FusionEngine(config)
        assert fusion is not None

    def test_add_radar_target(self):
        config = Config()
        fusion = FusionEngine(config)

        # 创建一个简单的RadarTarget对象
        from src.models import RadarTarget
        target = RadarTarget(
            target_id='test1',
            distance_nm=1.0,
            bearing_deg=90.0,
            speed_knots=10.0,
            course_deg=0.0
        )
        fusion.add_radar_target(target)
        assert len(fusion.radar_targets) > 0


class TestAlertManager:
    """测试告警管理"""

    def test_create(self):
        manager = AlertManager()
        assert manager is not None

    def test_check_speed_high(self):
        manager = AlertManager()
        target = {'id': 't1', 'speed_knots': 35, 'distance_nm': 1.0}
        alerts = manager.check_target(target)
        assert len(alerts) > 0

    def test_check_speed_normal(self):
        manager = AlertManager()
        target = {'id': 't1', 'speed_knots': 10, 'distance_nm': 1.0}
        alerts = manager.check_target(target)
        # 正常速度不应该触发告警
        assert len(alerts) == 0


class TestClassifier:
    """测试目标分类"""

    def test_create(self):
        classifier = TargetClassifier()
        assert classifier is not None

    def test_classify_with_mmsi(self):
        classifier = TargetClassifier()
        target = {
            'id': 't1',
            'mmsi': '200000001',
            'speed_knots': 10,
            'distance_nm': 1.0
        }
        result = classifier.classify_target(target)
        assert 'ship_type' in result
        assert 'region' in result


class TestConfig:
    """测试配置"""

    def test_load(self):
        config = Config()
        assert config is not None
        assert 'radar' in config.config

    def test_get(self):
        config = Config()
        radar = config.get('radar')
        assert radar is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
