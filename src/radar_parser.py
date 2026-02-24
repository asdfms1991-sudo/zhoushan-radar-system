"""
雷达数据接入模块 V2.0
支持 TCP/UDP/串口，NMEA 0183 解析
"""

import socket
import serial
import threading
import time
import logging
from typing import Callable, Optional, List
from datetime import datetime

try:
    import pynmea2
except ImportError:
    print("警告: pynmea2 未安装，请运行: pip install pynmea2")
    pynmea2 = None

from src.models import RadarTarget
from src.config import Config


class RadarConnection:
    """雷达连接管理器"""
    
    def __init__(self, config: dict, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.socket = None
        self.serial = None
        self.connected = False
        self.running = False
        self.thread = None
        self.callback = None
    
    def set_callback(self, callback: Callable[[RadarTarget], None]):
        """设置回调"""
        self.callback = callback
    
    def connect(self) -> bool:
        """连接雷达"""
        method = self.config.get('connection', {}).get('method', 'network')
        
        if method == 'network':
            return self._connect_network()
        elif method == 'serial':
            return self._connect_serial()
        else:
            self.logger.error(f"不支持的连接方式: {method}")
            return False
    
    def _connect_network(self) -> bool:
        """网络连接"""
        conn = self.config.get('connection', {})
        ip = conn.get('ip', '192.168.1.100')
        port = conn.get('port', 2000)
        protocol = conn.get('protocol', 'tcp')
        
        self.logger.info(f"连接雷达: {ip}:{port} ({protocol})")
        
        try:
            if protocol == 'tcp':
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(conn.get('timeout', 30))
                self.socket.connect((ip, port))
                self.connected = True
                self.logger.info("雷达 TCP 连接成功")
                return True
            else:
                # UDP
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.socket.bind((ip, port))
                self.connected = True
                self.logger.info(f"雷达 UDP 监听: {ip}:{port}")
                return True
        except Exception as e:
            self.logger.error(f"雷达连接失败: {e}")
            return False
    
    def _connect_serial(self) -> bool:
        """串口连接"""
        conn = self.config.get('connection', {})
        port = conn.get('port', 'COM3')
        baudrate = conn.get('baudrate', 4800)
        
        self.logger.info(f"连接串口: {port} @ {baudrate}")
        
        try:
            self.serial = serial.Serial(port, baudrate, timeout=1)
            self.connected = True
            self.logger.info("雷达串口连接成功")
            return True
        except Exception as e:
            self.logger.error(f"雷达串口连接失败: {e}")
            return False
    
    def start(self):
        """开始接收数据"""
        if not self.connected:
            self.logger.error("未连接，无法启动")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.thread.start()
        self.logger.info("开始接收雷达数据")
    
    def stop(self):
        """停止接收"""
        self.running = False
        if self.socket:
            self.socket.close()
        if self.serial:
            self.serial.close()
        self.logger.info("雷达连接已关闭")
    
    def _receive_loop(self):
        """接收循环"""
        buffer = b''
        
        while self.running:
            try:
                if self.socket:
                    if isinstance(self.socket, socket.socket) and self.socket.type == socket.SOCK_STREAM:
                        data = self.socket.recv(4096)
                    else:
                        data, _ = self.socket.recvfrom(4096)
                elif self.serial:
                    if self.serial.in_waiting:
                        data = self.serial.read(self.serial.in_waiting)
                    else:
                        time.sleep(0.01)
                        continue
                else:
                    break
                
                if not data:
                    continue
                
                buffer += data
                
                # 处理数据
                while b'\n' in buffer:
                    line, buffer = buffer.split(b'\n', 1)
                    line = line.strip().decode('utf-8', errors='ignore')
                    if line:
                        self._process_line(line)
                        
            except Exception as e:
                self.logger.error(f"接收错误: {e}")
                time.sleep(1)
    
    def _process_line(self, line: str):
        """处理NMEA行"""
        if not line:
            return
        
        # 尝试解析NMEA
        if pynmea2:
            try:
                msg = pynmea2.parse(line)
            except Exception:
                pass
        
        # 处理TTM语句
        if 'RATTM' in line or '$RATTM' in line:
            target = self._parse_ttm(line)
            if target and self.callback:
                self.callback(target)
                self.logger.debug(f"雷达目标: {target.target_id} 距离:{target.distance_nm}nm 方位:{target.bearing_deg}°")
    
    def _parse_ttm(self, line: str) -> Optional[RadarTarget]:
        """解析TTM语句"""
        # $RATTM,1,2.5,045,12.3,090,M,T1,A,,,50.0,,A*5C
        try:
            parts = line.split(',')
            if len(parts) < 8:
                return None
            
            target_id = parts[1]
            distance = float(parts[2]) if parts[2] else 0
            bearing = float(parts[3]) if parts[3] else 0
            speed = float(parts[4]) if parts[4] else 0
            course = float(parts[5]) if parts[5] else 0
            target_type = parts[6] if len(parts) > 6 else 'M'
            name = parts[7] if len(parts) > 7 else ''
            status = parts[8] if len(parts) > 8 else 'A'
            
            return RadarTarget(
                target_id=target_id,
                distance_nm=distance,
                bearing_deg=bearing,
                speed_knots=speed,
                course_deg=course,
                target_type=target_type,
                name=name,
                status=status
            )
        except Exception as e:
            self.logger.error(f"解析TTM失败: {e}")
            return None


class RadarParser:
    """雷达数据解析器"""
    
    def __init__(self, config: Config, callback: Optional[Callable] = None):
        self.config = config
        self.callback = callback
        self.logger = logging.getLogger('radar_parser')
        
        radar_config = config.radar_config
        self.enabled = radar_config.get('enabled', True)
        self.filter = radar_config.get('filter', {})
        
        # 连接器
        self.connection = RadarConnection(radar_config, self.logger)
        self.connection.set_callback(self._on_target)
        
        # 状态
        self.connected = False
    
    def _on_target(self, target: RadarTarget):
        """目标回调"""
        # 过滤检查
        if not self._check_filter(target):
            return
        
        if self.callback:
            self.callback(target)
    
    def _check_filter(self, target: RadarTarget) -> bool:
        """过滤检查"""
        min_dist = self.filter.get('min_distance_nm', 0)
        max_dist = self.filter.get('max_distance_nm', 100)
        min_speed = self.filter.get('min_speed_knots', 0)
        
        if target.distance_nm < min_dist or target.distance_nm > max_dist:
            return False
        
        if target.speed_knots < min_speed:
            return False
        
        return True
    
    def connect(self) -> bool:
        """连接"""
        if not self.enabled:
            self.logger.info("雷达功能未启用")
            return True
        
        return self.connection.connect()
    
    def start(self):
        """启动"""
        if self.enabled and self.connected:
            self.connection.start()
    
    def stop(self):
        """停止"""
        self.connection.stop()
    
    @property
    def is_connected(self) -> bool:
        return self.connection.connected


def create_simulator(callback: Callable = None):
    """创建测试模拟器"""
    
    class Simulator:
        def __init__(self):
            self.callback = callback
            self.running = False
            self.thread = None
            self.target_id = 1
        
        def start(self):
            self.running = True
            self.thread = threading.Thread(target=self._simulate, daemon=True)
            self.thread.start()
            print("雷达模拟器已启动")
        
        def stop(self):
            self.running = False
        
        def _simulate(self):
            import random
            while self.running:
                if random.random() > 0.3:
                    target = RadarTarget(
                        target_id=str(self.target_id),
                        distance_nm=random.uniform(0.5, 5.0),
                        bearing_deg=random.uniform(0, 360),
                        speed_knots=random.uniform(5, 20),
                        course_deg=random.uniform(0, 360),
                        name=f"目标{self.target_id}"
                    )
                    self.target_id = (self.target_id % 10) + 1
                    
                    if self.callback:
                        self.callback(target)
                
                time.sleep(1)
    
    return Simulator()


if __name__ == '__main__':
    # 测试
    logging.basicConfig(level=logging.INFO)
    
    from config import Config
    config = Config()
    
    parser = RadarParser(config)
    
    # 使用模拟器
    sim = create_simulator(lambda t: print(f"目标: {t.target_id} 距离:{t.distance_nm}"))
    sim.start()
    
    time.sleep(5)
    sim.stop()
    print("测试完成")
