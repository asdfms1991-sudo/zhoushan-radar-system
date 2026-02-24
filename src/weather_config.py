"""
天气模式配置模块
根据天气/海况自动调整雷达参数
"""

from typing import Dict, Optional
from enum import Enum


class WeatherMode(Enum):
    """天气模式"""
    CALM = "calm"          # 平静
    MODERATE = "moderate"  # 中等
    ROUGH = "rough"       # 恶劣
    STORM = "storm"       # 暴雨


class WeatherConfig:
    """天气模式配置"""
    
    # 预设配置
    PRESETS = {
        WeatherMode.CALM: {
            'name': '平静海况',
            'sea_state': '0-1级',
            'cfar': {
                'guard_cells': 2,
                'ref_cells': 16,
                'p_fa': 1e-3,  # 宽松
            },
            'kalman': {
                'process_noise': 0.05,  # 低
                'measurement_noise': 0.5,
            },
            'clutter': {
                'min_speed': 0.3,
                'max_speed': 50.0,
                'min_distance': 0.05,
            },
            'filter': {
                'enabled': True,
                'threshold': 0.3,
            }
        },
        WeatherMode.MODERATE: {
            'name': '中等海况',
            'sea_state': '2-3级',
            'cfar': {
                'guard_cells': 2,
                'ref_cells': 16,
                'p_fa': 1e-4,  # 标准
            },
            'kalman': {
                'process_noise': 0.1,
                'measurement_noise': 1.0,
            },
            'clutter': {
                'min_speed': 0.5,
                'max_speed': 50.0,
                'min_distance': 0.1,
            },
            'filter': {
                'enabled': True,
                'threshold': 0.5,
            }
        },
        WeatherMode.ROUGH: {
            'name': '恶劣海况',
            'sea_state': '4-5级',
            'cfar': {
                'guard_cells': 4,
                'ref_cells': 24,
                'p_fa': 1e-5,  # 严格
            },
            'kalman': {
                'process_noise': 0.3,  # 高
                'measurement_noise': 2.0,
            },
            'clutter': {
                'min_speed': 1.0,
                'max_speed': 45.0,
                'min_distance': 0.2,
            },
            'filter': {
                'enabled': True,
                'threshold': 0.7,
            }
        },
        WeatherMode.STORM: {
            'name': '暴雨/极恶劣',
            'sea_state': '>5级',
            'cfar': {
                'guard_cells': 6,
                'ref_cells': 32,
                'p_fa': 1e-6,  # 极严格
            },
            'kalman': {
                'process_noise': 0.5,
                'measurement_noise': 5.0,
            },
            'clutter': {
                'min_speed': 2.0,
                'max_speed': 40.0,
                'min_distance': 0.3,
            },
            'filter': {
                'enabled': True,
                'threshold': 0.9,
            }
        }
    }
    
    def __init__(self, mode: WeatherMode = WeatherMode.MODERATE):
        self.current_mode = mode
        self.config = self.PRESETS[mode].copy()
    
    def set_mode(self, mode: WeatherMode):
        """设置天气模式"""
        self.current_mode = mode
        self.config = self.PRESETS[mode].copy()
    
    def get_cfar_config(self) -> dict:
        """获取CFAR配置"""
        return self.config.get('cfar', {})
    
    def get_kalman_config(self) -> dict:
        """获取Kalman配置"""
        return self.config.get('kalman', {})
    
    def get_clutter_config(self) -> dict:
        """获取杂波过滤配置"""
        return self.config.get('clutter', {})
    
    def get_filter_config(self) -> dict:
        """获取过滤配置"""
        return self.config.get('filter', {})
    
    def get_all_config(self) -> dict:
        """获取完整配置"""
        return {
            'mode': self.current_mode.value,
            'mode_name': self.config.get('name', ''),
            'sea_state': self.config.get('sea_state', ''),
            'cfar': self.get_cfar_config(),
            'kalman': self.get_kalman_config(),
            'clutter': self.get_clutter_config(),
            'filter': self.get_filter_config()
        }
    
    @classmethod
    def get_available_modes(cls) -> list:
        """获取所有可用模式"""
        return [
            {
                'mode': m.value,
                'name': cls.PRESETS[m].get('name', ''),
                'sea_state': cls.PRESETS[m].get('sea_state', '')
            }
            for m in WeatherMode
        ]


class AdaptiveWeatherController:
    """自适应天气控制器"""
    
    def __init__(self):
        self.weather_config = WeatherConfig(WeatherMode.MODERATE)
        self.auto_mode = False
    
    def enable_auto_mode(self):
        """启用自动模式"""
        self.auto_mode = True
    
    def disable_auto_mode(self):
        """禁用自动模式"""
        self.auto_mode = False
    
    def set_manual_mode(self, mode: WeatherMode):
        """手动设置模式"""
        self.auto_mode = False
        self.weather_config.set_mode(mode)
    
    def update_by_detection(self, clutter_level: float):
        """
        根据检测到的杂波级别自动调整
        
        Args:
            clutter_level: 杂波级别 (0-1)
        """
        if not self.auto_mode:
            return
        
        # 自动选择模式
        if clutter_level < 0.25:
            self.weather_config.set_mode(WeatherMode.CALM)
        elif clutter_level < 0.5:
            self.weather_config.set_mode(WeatherMode.MODERATE)
        elif clutter_level < 0.75:
            self.weather_config.set_mode(WeatherMode.ROUGH)
        else:
            self.weather_config.set_mode(WeatherMode.STORM)
    
    def get_current_config(self) -> dict:
        """获取当前配置"""
        return self.weather_config.get_all_config()


# 测试
if __name__ == '__main__':
    controller = AdaptiveWeatherController()
    
    # 列出所有模式
    print("可用天气模式:")
    for m in WeatherConfig.get_available_modes():
        print(f"  {m['mode']}: {m['name']} ({m['sea_state']})")
    
    # 测试手动模式
    print("\n当前模式:", controller.weather_config.current_mode.value)
    print("CFAR配置:", controller.weather_config.get_cfar_config())
    
    # 测试自动模式
    controller.enable_auto_mode()
    controller.update_by_detection(0.8)
    print("\n自动调整为:", controller.weather_config.current_mode.value)
