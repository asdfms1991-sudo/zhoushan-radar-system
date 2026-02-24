#!/usr/bin/env python3
"""
命令行入口
提供CLI操作
"""

import click
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.config import Config
from src.fusion import FusionEngine
from src.advanced_tracker import TrackerFactory
from src.system_check import run_system_check
from src.health_check import health_checker


@click.group()
def cli():
    """舟山定海渔港雷达监控系统 CLI"""
    pass


@cli.command()
def check():
    """系统自检"""
    click.echo("运行系统自检...")
    result = run_system_check()

    click.echo(f"\n状态: {result['status'].upper()}")
    click.echo(f"总计: {result['summary']['total']} 项")

    for check in result['checks']:
        status_icon = {
            'pass': '✅',
            'fail': '❌',
            'warning': '⚠️'
        }.get(check['status'], '❓')

        click.echo(f"{status_icon} {check['name']}: {check['message']}")


@cli.command()
def health():
    """健康检查"""
    click.echo("运行健康检查...")
    result = health_checker.check_all()

    click.echo(f"\n整体状态: {result['overall'].upper()}")
    click.echo(f"运行时长: {result['uptime_seconds']}秒")

    for name, info in result['components'].items():
        status = info.get('status', 'unknown')
        icon = {'healthy': '✅', 'warning': '⚠️', 'critical': '❌'}.get(status, '❓')
        click.echo(f"{icon} {name}: {info.get('message', '')}")


@cli.command()
def info():
    """显示系统信息"""
    click.echo("舟山定海渔港雷达监控系统 V2.0")
    click.echo("")

    # 算法
    algos = TrackerFactory.list_algorithms()
    click.echo(f"可用算法: {', '.join(algos)}")
    click.echo(f"推荐算法: KF")

    # 配置
    config = Config()
    radar = config.get('radar', {})
    ais = config.get('ais', {})

    click.echo("")
    click.echo("雷达配置:")
    click.echo(f"  IP: {radar.get('connection', {}).get('ip', '未配置')}")
    click.echo(f"  端口: {radar.get('connection', {}).get('port', '未配置')}")

    click.echo("")
    click.echo("AIS配置:")
    click.echo(f"  串口: {ais.get('connection', {}).get('port', '未配置')}")


@cli.command()
@click.option('--algo', default='KF', help='跟踪算法')
def test_tracker(algo):
    """测试跟踪算法"""
    click.echo(f"测试算法: {algo}")

    tracker = TrackerFactory.create(algo)

    errors = []
    x = y = 0
    for i in range(50):
        x += 1.5
        y += 0.5
        mx = x + np.random.randn() * 0.3
        my = y + np.random.randn() * 0.3
        ex, ey = tracker.process(mx, my)
        error = np.sqrt((ex - x)**2 + (ey - y)**2)
        errors.append(error)

    import numpy as np
    mean_error = np.mean(errors)

    click.echo(f"平均误差: {mean_error:.4f}")

    if mean_error < 0.5:
        click.echo("✅ 测试通过")
    else:
        click.echo("⚠️ 误差较大")


if __name__ == '__main__':
    cli()
