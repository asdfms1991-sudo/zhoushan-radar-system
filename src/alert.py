"""
告警模块
用于雷达目标异常检测和告警
"""

from typing import List, Dict, Optional, Callable
from datetime import datetime
from enum import Enum


class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertRule:
    """告警规则"""
    
    def __init__(self, name: str, level: AlertLevel, condition: callable, message: str = ""):
        self.name = name
        self.level = level
        self.condition = condition
        self.message = message
    
    def check(self, target: dict) -> bool:
        """检查目标是否触发告警"""
        try:
            return self.condition(target)
        except:
            return False


class AlertManager:
    """告警管理器"""
    
    def __init__(self):
        self.rules: List[AlertRule] = []
        self.alerts: List[dict] = []
        self.callbacks: List[Callable] = []
        self.max_alerts = 1000  # 最多保留1000条告警
        
        # 初始化默认规则
        self._init_default_rules()
    
    def _init_default_rules(self):
        """初始化默认告警规则"""
        
        # 1. 速度告警（速度过快）
        self.add_rule(AlertRule(
            name="speed_high",
            level=AlertLevel.WARNING,
            condition=lambda t: t.get('speed_knots', 0) > 30,
            message="目标速度过快"
        ))
        
        # 2. 速度告警（速度为0，可能是静止目标）
        self.add_rule(AlertRule(
            name="speed_zero",
            level=AlertLevel.INFO,
            condition=lambda t: t.get('speed_knots', 0) < 0.5 and t.get('speed_knots', 0) >= 0,
            message="目标静止"
        ))
        
        # 3. 距离告警（太近）
        self.add_rule(AlertRule(
            name="distance_close",
            level=AlertLevel.CRITICAL,
            condition=lambda t: t.get('distance_nm', 999) < 0.3,
            message="目标距离过近"
        ))
        
        # 4. 距离告警（太远）
        self.add_rule(AlertRule(
            name="distance_far",
            level=AlertLevel.INFO,
            condition=lambda t: t.get('distance_nm', 0) > 10,
            message="目标距离过远"
        ))
        
        # 5. AIS告警（无AIS的小型目标）
        self.add_rule(AlertRule(
            name="no_ais_small",
            level=AlertLevel.WARNING,
            condition=lambda t: t.get('source_type') == 'radar' and t.get('speed_knots', 0) > 5,
            message="高速雷达目标无AIS"
        ))
        
        # 6. 方向告警（直冲向港口）
        self.add_rule(AlertRule(
            name="heading_port",
            level=AlertLevel.CRITICAL,
            condition=lambda t: 270 < t.get('course_deg', 0) < 90,
            message="目标直冲向港口"
        ))
    
    def add_rule(self, rule: AlertRule):
        """添加告警规则"""
        self.rules.append(rule)
    
    def remove_rule(self, name: str):
        """删除告警规则"""
        self.rules = [r for r in self.rules if r.name != name]
    
    def check_target(self, target: dict) -> List[dict]:
        """检查目标是否触发告警"""
        triggered = []
        
        for rule in self.rules:
            if rule.check(target):
                alert = {
                    'id': f"{rule.name}_{target.get('id', 'unknown')}",
                    'target_id': target.get('id'),
                    'rule': rule.name,
                    'level': rule.level.value,
                    'message': rule.message,
                    'target': target,
                    'timestamp': datetime.now().isoformat()
                }
                triggered.append(alert)
                self._add_alert(alert)
        
        return triggered
    
    def check_targets(self, targets: List[dict]) -> List[dict]:
        """批量检查目标"""
        all_alerts = []
        for target in targets:
            alerts = self.check_target(target)
            all_alerts.extend(alerts)
        
        # 触发回调
        for alert in all_alerts:
            self._trigger_callbacks(alert)
        
        return all_alerts
    
    def _add_alert(self, alert: dict):
        """添加告警到历史"""
        self.alerts.append(alert)
        
        # 限制数量
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[-self.max_alerts:]
    
    def register_callback(self, callback: Callable):
        """注册告警回调"""
        self.callbacks.append(callback)
    
    def _trigger_callbacks(self, alert: dict):
        """触发回调"""
        for callback in self.callbacks:
            try:
                callback(alert)
            except Exception as e:
                print(f"告警回调错误: {e}")
    
    def get_alerts(self, level: str = None, limit: int = 100) -> List[dict]:
        """获取告警历史"""
        alerts = self.alerts
        
        if level:
            alerts = [a for a in alerts if a['level'] == level]
        
        return alerts[-limit:]
    
    def get_active_alerts(self) -> List[dict]:
        """获取活跃告警（未确认）"""
        return [a for a in self.alerts if not a.get('acknowledged', False)]
    
    def acknowledge_alert(self, alert_id: str):
        """确认告警"""
        for alert in self.alerts:
            if alert['id'] == alert_id:
                alert['acknowledged'] = True
                alert['acknowledged_at'] = datetime.now().isoformat()
    
    def clear_alerts(self):
        """清空告警历史"""
        self.alerts = []
    
    def get_statistics(self) -> dict:
        """获取告警统计"""
        stats = {
            'total': len(self.alerts),
            'by_level': {},
            'by_rule': {}
        }
        
        for alert in self.alerts:
            level = alert['level']
            rule = alert['rule']
            
            stats['by_level'][level] = stats['by_level'].get(level, 0) + 1
            stats['by_rule'][rule] = stats['by_rule'].get(rule, 0) + 1
        
        return stats


# 测试
if __name__ == '__main__':
    manager = AlertManager()
    
    # 测试目标
    test_targets = [
        {'id': '1', 'speed_knots': 35, 'distance_nm': 1.0, 'source_type': 'radar', 'course_deg': 45},
        {'id': '2', 'speed_knots': 0.3, 'distance_nm': 0.2, 'source_type': 'radar', 'course_deg': 90},
        {'id': 'A123456', 'speed_knots': 10, 'distance_nm': 2.0, 'source_type': 'ais', 'course_deg': 180},
    ]
    
    # 检查
    alerts = manager.check_targets(test_targets)
    
    print(f"触发告警数: {len(alerts)}")
    for alert in alerts:
        print(f"  [{alert['level']}] {alert['rule']}: {alert['message']}")
    
    # 统计
    stats = manager.get_statistics()
    print(f"\n统计: {stats}")
