"""
AIS 数据接入模块 V2.1
使用 pyais 库进行正确解析
"""

import socket
import serial
import threading
import time
import logging
from typing import Callable, Optional
from datetime import datetime

try:
    import pynmea2
    import pyais
except ImportError:
    print("警告: pynmea2 或 pyais 未安装")

from src.models import AISTarget
from src.config import Config


class AISConnection:
    """AIS连接管理器"""
    
    def __init__(self, config: dict, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.socket = None
        self.serial = None
        self.connected = False
        self.running = False
        self.thread = None
        self.callback = None
    
    def set_callback(self, callback: Callable):
        self.callback = callback
    
    def connect(self) -> bool:
        # 优先网络模式
        network = self.config.get('or_network', {})
        if network.get('enabled', False):
            return self._connect_network(network)
        return self._connect_serial(self.config.get('connection', {}))
    
    def _connect_network(self, config: dict) -> bool:
        ip = config.get('ip', '127.0.0.1')
        port = config.get('port', 5001)
        self.logger.info(f"AIS网络: {ip}:{port}")
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind((ip, port))
            self.connected = True
            return True
        except Exception as e:
            self.logger.error(f"AIS网络失败: {e}")
            return False
    
    def _connect_serial(self, config: dict) -> bool:
        port = config.get('port', 'COM3')
        baudrate = config.get('baudrate', 38400)
        self.logger.info(f"AIS串口: {port} @ {baudrate}")
        try:
            self.serial = serial.Serial(port, baudrate, timeout=1)
            self.connected = True
            return True
        except Exception as e:
            self.logger.error(f"AIS串口失败: {e}")
            return False
    
    def start(self):
        if not self.connected:
            return
        self.running = True
        self.thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.thread.start()
        self.logger.info("开始接收AIS数据")
    
    def stop(self):
        self.running = False
        if self.socket: self.socket.close()
        if self.serial: self.serial.close()
    
    def _receive_loop(self):
        buffer = b''
        while self.running:
            try:
                if self.socket:
                    data, _ = self.socket.recvfrom(4096)
                elif self.serial:
                    if self.serial.in_waiting:
                        data = self.serial.read(self.serial.in_waiting)
                    else:
                        time.sleep(0.01)
                        continue
                else:
                    break
                if data:
                    buffer += data
                    while b'\n' in buffer:
                        line, buffer = buffer.split(b'\n', 1)
                        line = line.strip().decode('utf-8', errors='ignore')
                        if line:
                            self._process_line(line)
            except Exception as e:
                self.logger.error(f"AIS错误: {e}")
                time.sleep(1)
    
    def _process_line(self, line: str):
        if 'AIVDM' in line or '!AIV' in line:
            target = self._parse_ais(line)
            if target and self.callback:
                self.callback(target)
                self.logger.debug(f"AIS: {target.mmsi} {target.name}")
    
    def _parse_ais(self, line: str) -> Optional[AISTarget]:
        """使用 pyais 解析 AIS 消息"""
        try:
            msg = pyais.decode(line)
            
            # 提取字段
            mmsi = str(msg.mmsi)
            lat = getattr(msg, 'lat', 0) or 0
            lon = getattr(msg, 'lon', 0) or 0
            speed = getattr(msg, 'speed', 0) or 0
            course = getattr(msg, 'course', 0) or 0
            heading = getattr(msg, 'heading', 0) or 0
            if heading == 511:  # 无效值
                heading = 0
            
            return AISTarget(
                mmsi=mmsi,
                name=f"船{mmsi[-6:]}",
                lat=lat,
                lon=lon,
                speed_knots=speed,
                course_deg=course,
                heading_deg=heading
            )
        except Exception as e:
            self.logger.debug(f"AIS解析跳过: {e}")
            return None


class AISParser:
    """AIS解析器"""
    
    def __init__(self, config: Config, callback: Optional[Callable] = None):
        self.config = config
        self.callback = callback
        self.logger = logging.getLogger('ais_parser')
        
        ais_config = config.ais_config
        self.enabled = ais_config.get('enabled', True)
        
        self.connection = AISConnection(ais_config, self.logger)
        self.connection.set_callback(self._on_target)
        self.connected = False
    
    def _on_target(self, target: AISTarget):
        if self.callback:
            self.callback(target)
    
    def connect(self) -> bool:
        if not self.enabled:
            return True
        return self.connection.connect()
    
    def start(self):
        if self.enabled and self.connected:
            self.connection.start()
    
    def stop(self):
        self.connection.stop()
    
    @property
    def is_connected(self) -> bool:
        return self.connection.connected


def create_simulator(callback=None):
    """创建测试模拟器"""
    import random
    
    class Simulator:
        def __init__(self):
            self.callback = callback
            self.running = False
            self.thread = None
            self.mmsi = 200000000
        
        def start(self):
            self.running = True
            self.thread = threading.Thread(target=self._simulate, daemon=True)
            self.thread.start()
            print("AIS模拟器已启动")
        
        def stop(self):
            self.running = False
        
        def _simulate(self):
            while self.running:
                if random.random() > 0.7:
                    self.mmsi += 1
                    target = AISTarget(
                        mmsi=str(self.mmsi),
                        name=f"测试船{self.mmsi % 1000}",
                        lat=30.0 + random.uniform(-0.05, 0.05),
                        lon=122.0 + random.uniform(-0.05, 0.05),
                        speed_knots=random.uniform(5, 15),
                        course_deg=random.uniform(0, 360),
                        heading_deg=int(random.uniform(0, 360))
                    )
                    if self.callback:
                        self.callback(target)
                time.sleep(2)
    
    return Simulator()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    from config import Config
    config = Config()
    parser = AISParser(config)
    sim = create_simulator(lambda t: print(f"AIS: {t.mmsi}"))
    sim.start()
    time.sleep(5)
    sim.stop()
