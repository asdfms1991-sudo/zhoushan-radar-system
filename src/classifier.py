"""
目标分类模块
基于AIS信息对船舶进行分类
"""

from typing import Dict, Optional


# AIS船型分类映射
SHIP_TYPE_MAP = {
    # 钓鱼船
    'fishing': ['fishing', 'fish', 'trawler'],
    # 货船
    'cargo': ['cargo', 'container', 'bulk', 'tanker'],
    # 客船
    'passenger': ['passenger', 'ferry', 'cruise', 'ro-ro'],
    # 渔船
    'tanker': ['tanker', 'oil', 'chemical', 'lng', 'lpg'],
    # 拖船
    'tug': ['tug', 'towing'],
    # 游艇
    'yacht': ['yacht', 'pleasure', 'sailing'],
    # 工作船
    'work': ['work', 'construction', 'dredging'],
    # 军事/执法
    'military': ['military', 'navy', 'coast guard', 'patrol'],
    # 未知
    'unknown': ['unknown', 'other', '']
}

# 基于MMSI前缀的区域分类
MMSI_PREFIX_MAP = {
    '200': '中国内河',
    '210': '中国',
    '370': '中国香港',
    '412': '中国',
    '413': '中国',
    '477': '中国香港',
    '536': '中国台湾',
    '416': '中国台湾',
}

# 基于航速的机动性分类
SPEED_CATEGORIES = {
    'anchored': (0, 0.5),      # 锚泊
    'slow': (0.5, 3),         # 低速
    'normal': (3, 15),         # 正常
    'fast': (15, 25),          # 高速
    'very_fast': (25, 999)    # 极速
}


class TargetClassifier:
    """目标分类器"""
    
    def __init__(self):
        self.ship_type_map = SHIP_TYPE_MAP
        self.mmsi_prefix_map = MMSI_PREFIX_MAP
    
    def classify_ship_type(self, ais_target: dict) -> str:
        """
        基于AIS信息分类船型
        
        Args:
            ais_target: AIS目标数据
            
        Returns:
            船型分类: fishing/cargo/passenger/tanker/tug/yacht/work/military/unknown
        """
        ship_type = ais_target.get('ship_type', '').lower()
        
        # 直接匹配
        if not ship_type:
            return 'unknown'
        
        for category, keywords in self.ship_type_map.items():
            for keyword in keywords:
                if keyword in ship_type:
                    return category
        
        # 基于MMSI猜测
        mmsi = ais_target.get('mmsi', '')
        if mmsi.startswith('200') or mmsi.startswith('210'):
            return 'cargo'  # 中国渔船多为200开头
        
        return 'unknown'
    
    def classify_by_mmsi(self, mmsi: str) -> str:
        """
        基于MMSI前缀分类区域
        
        Args:
            mmsi: MMSI码
            
        Returns:
            区域分类
        """
        if not mmsi:
            return 'unknown'
        
        prefix = mmsi[:3]
        return self.mmsi_prefix_map.get(prefix, 'other')
    
    def classify_speed_category(self, speed_knots: float) -> str:
        """
        基于速度分类机动性
        
        Args:
            speed_knots: 速度（节）
            
        Returns:
            机动性分类: anchored/slow/normal/fast/very_fast
        """
        for category, (min_speed, max_speed) in SPEED_CATEGORIES.items():
            if min_speed <= speed_knots < max_speed:
                return category
        return 'unknown'
    
    def classify_target(self, target: dict) -> dict:
        """
        综合分类目标
        
        Args:
            target: 目标数据
            
        Returns:
            分类结果字典
        """
        result = {
            'ship_type': 'unknown',
            'region': 'unknown',
            'speed_category': 'unknown',
            'has_ais': bool(target.get('mmsi')),
            'is_small': False,
            'is_suspicious': False
        }
        
        # 如果有AIS信息，进行详细分类
        if target.get('mmsi'):
            result['ship_type'] = self.classify_ship_type(target)
            result['region'] = self.classify_by_mmsi(target.get('mmsi', ''))
        
        # 速度分类
        speed = target.get('speed_knots', 0)
        result['speed_category'] = self.classify_speed_category(speed)
        
        # 判断是否为小型目标（无AIS且低速）
        if not target.get('mmsi') and speed < 3:
            result['is_small'] = True
        
        # 判断是否可疑
        # 条件：无AIS + 高速 + 距离近
        if (not target.get('mmsi') and 
            speed > 15 and 
            target.get('distance_nm', 999) < 1):
            result['is_suspicious'] = True
        
        return result
    
    def classify_targets(self, targets: list) -> list:
        """批量分类"""
        return [self.classify_target(t) for t in targets]


# 测试
if __name__ == '__main__':
    classifier = TargetClassifier()
    
    test_targets = [
        {'id': '1', 'mmsi': '200000001', 'speed_knots': 10, 'ship_type': 'fishing', 'distance_nm': 1.0},
        {'id': '2', 'mmsi': '', 'speed_knots': 0.3, 'distance_nm': 0.2},  # 可疑
        {'id': '3', 'mmsi': '370123456', 'speed_knots': 20, 'ship_type': 'container', 'distance_nm': 5.0},
    ]
    
    for target in test_targets:
        result = classifier.classify_target(target)
        print(f"目标 {target['id']}:")
        print(f"  船型: {result['ship_type']}")
        print(f"  区域: {result['region']}")
        print(f"  速度分类: {result['speed_category']}")
        print(f"  可疑: {result['is_suspicious']}")
        print()
