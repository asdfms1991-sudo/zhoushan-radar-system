#!/usr/bin/env python3
"""
快速启动脚本
用于一键启动雷达系统
"""

import subprocess
import sys
import os


def check_python():
    """检查Python版本"""
    print("检查Python版本...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python版本过低: {version.major}.{version.minor}")
        print("需要 Python 3.8 或更高版本")
        return False
    print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
    return True


def check_dependencies():
    """检查依赖"""
    print("\n检查依赖...")
    
    required = ['flask', 'flask_socketio', 'pyserial', 'pynmea2', 'numpy']
    missing = []
    
    for pkg in required:
        try:
            __import__(pkg.replace('-', '_'))
            print(f"  ✅ {pkg}")
        except ImportError:
            print(f"  ❌ {pkg} (未安装)")
            missing.append(pkg)
    
    if missing:
        print(f"\n缺少依赖，请运行：")
        print(f"  pip install -r requirements.txt")
        return False
    
    return True


def check_config():
    """检查配置"""
    print("\n检查配置文件...")
    config_file = "config/config.json"
    
    if not os.path.exists(config_file):
        print(f"❌ 配置文件不存在: {config_file}")
        return False
    
    print(f"✅ 配置文件存在")
    return True


def start_simulator():
    """启动模拟器模式"""
    print("\n启动模拟器模式...")
    print("=" * 50)
    subprocess.run([sys.executable, "main.py", "--simulator"])


def start_normal():
    """启动正常模式"""
    print("\n启动正常模式...")
    print("=" * 50)
    subprocess.run([sys.executable, "main.py"])


def main():
    print("=" * 50)
    print("舟山定海渔港雷达监控系统 V2.0")
    print("=" * 50)
    
    # 检查
    if not check_python():
        return
    
    if not check_dependencies():
        return
    
    if not check_config():
        return
    
    # 选择启动模式
    print("\n请选择启动模式：")
    print("  1. 模拟器模式（测试用）")
    print("  2. 正常模式（连接真实雷达）")
    print("  3. 退出")
    
    choice = input("\n请输入选项 (1/2/3): ").strip()
    
    if choice == '1':
        start_simulator()
    elif choice == '2':
        start_normal()
    else:
        print("退出")


if __name__ == '__main__':
    main()
