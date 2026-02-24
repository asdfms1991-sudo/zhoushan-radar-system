#!/usr/bin/env python3
"""
雷达系统安全检查脚本
使用bandit进行安全扫描
"""

import subprocess
import json
import os
from pathlib import Path


def scan_directory(directory: str) -> dict:
    """扫描目录安全问题"""
    result = subprocess.run(
        ['bandit', '-r', directory, '-f', 'json'],
        capture_output=True,
        text=True
    )
    
    try:
        data = json.loads(result.stdout)
        return data.get('metrics', {}).get('_totals', {})
    except:
        return {}


def check_dependencies() -> dict:
    """检查依赖安全问题"""
    result = subprocess.run(
        ['safety', 'check', '--json'],
        capture_output=True,
        text=True
    )
    
    try:
        data = json.loads(result.stdout)
        return {
            'vulnerabilities': len(data.get('vulnerabilities', [])),
            'details': data
        }
    except:
        return {'vulnerabilities': 0}


def main():
    print("=" * 50)
    print("雷达系统 - 安全检查")
    print("=" * 50)
    
    # 扫描代码
    print("\n📊 代码安全扫描...")
    code_issues = scan_directory('src')
    print(f"  高危: {code_issues.get('SEVERITY.HIGH', 0)}")
    print(f"  中危: {code_issues.get('SEVERITY.MEDIUM', 0)}")
    print(f"  低危: {code_issues.get('SEVERITY.LOW', 0)}")
    
    # 检查依赖
    print("\n📦 依赖安全检查...")
    dep_issues = check_dependencies()
    print(f"  漏洞数: {dep_issues.get('vulnerabilities', 0)}")
    
    # 总结
    print("\n" + "=" * 50)
    total_issues = (code_issues.get('SEVERITY.HIGH', 0) + 
                   code_issues.get('SEVERITY.MEDIUM', 0) +
                   dep_issues.get('vulnerabilities', 0))
    
    if total_issues == 0:
        print("✅ 安全检查通过！")
    else:
        print(f"⚠️ 发现 {total_issues} 个问题，请检查！")
    print("=" * 50)


if __name__ == '__main__':
    main()
