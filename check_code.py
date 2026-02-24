#!/usr/bin/env python3
"""
本地代码质量检查脚本
用法: python check_code.py
"""

import os
import sys
import subprocess
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# 要检查的文件
SRC_FILES = [
    'src/fusion.py',
    'src/radar_parser.py',
    'src/ais_parser.py',
    'src/kalman_filter.py',
    'src/trajectory.py',
    'src/cfar_filter.py',
    'src/api.py',
    'src/models.py',
    'src/config.py',
    'src/logger.py',
    'main.py',
]


def run_pylint(file_path: str) -> dict:
    """运行 Pylint 检查"""
    cmd = [
        'pylint', file_path,
        '--output-format=text',
        '--disable=import-error,trailing-whitespace,wrong-import-order'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # 提取评分
    rating = 0
    for line in result.stdout.split('\n'):
        if 'Your code has been rated at' in line:
            try:
                rating = float(line.split('at ')[1].split('/')[0])
            except:
                pass
    
    return {
        'file': file_path,
        'rating': rating,
        'output': result.stdout
    }


def main():
    print("=" * 60)
    print("雷达系统 - 本地代码质量检查")
    print("=" * 60)
    
    total_rating = 0
    count = 0
    
    for file in SRC_FILES:
        full_path = PROJECT_ROOT / file
        if not full_path.exists():
            print(f"⚠️ 跳过: {file} (不存在)")
            continue
        
        print(f"\n检查: {file}...")
        result = run_pylint(str(full_path))
        
        status = "✅" if result['rating'] >= 7 else "⚠️" if result['rating'] >= 5 else "❌"
        print(f"  {status} 评分: {result['rating']}/10")
        
        total_rating += result['rating']
        count += 1
    
    print("\n" + "=" * 60)
    if count > 0:
        avg = total_rating / count
        print(f"平均评分: {avg:.2f}/10")
        
        if avg >= 8:
            print("✅ 代码质量良好")
        elif avg >= 6:
            print("⚠️ 代码质量一般，建议改进")
        else:
            print("❌ 代码质量较差，需要大幅改进")
    print("=" * 60)


if __name__ == '__main__':
    main()
