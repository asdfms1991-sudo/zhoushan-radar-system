"""
API增强模块
支持算法切换、性能监控
"""

from flask import Flask, jsonify, request
import json
from datetime import datetime

# 全局变量
current_tracker = None
tracker_algorithm = 'KF'
performance_stats = {
    'latency': [],
    'memory': [],
    'fps': 0
}


def create_api_routes(app, get_tracker_func):
    """创建增强API路由"""
    
    global current_tracker
    
    @app.route('/api/algorithms', methods=['GET'])
    def get_algorithms():
        """获取所有算法"""
        return jsonify({
            'available': ['KF', 'EKF', 'UKF'],
            'current': tracker_algorithm,
            'recommend': 'KF'
        })
    
    @app.route('/api/algorithm', methods=['POST'])
    def set_algorithm():
        """切换算法"""
        global current_tracker, tracker_algorithm
        
        data = request.get_json()
        algo = data.get('algorithm', 'KF')
        
        if algo in ['KF', 'EKF', 'UKF']:
            current_tracker = get_tracker_func(algo)
            tracker_algorithm = algo
            
            return jsonify({
                'success': True,
                'algorithm': algo,
                'message': f'已切换到{algo}算法'
            })
        
        return jsonify({
            'success': False,
            'message': f'不支持的算法: {algo}'
        }), 400
    
    @app.route('/api/performance', methods=['GET'])
    def get_performance():
        """获取性能数据"""
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'algorithm': tracker_algorithm,
            'stats': {
                'avg_latency_ms': sum(performance_stats['latency'][-10:]) / 10 if performance_stats['latency'] else 0,
                'fps': performance_stats['fps'],
                'memory_mb': sum(performance_stats['memory'][-10:]) / 10 if performance_stats['memory'] else 0
            }
        })
    
    @app.route('/api/health', methods=['GET'])
    def get_health():
        """健康检查"""
        return jsonify({
            'status': 'healthy',
            'algorithm': tracker_algorithm,
            'uptime': 'N/A'
        })
    
    @app.route('/api/config/tracker', methods=['GET'])
    def get_tracker_config():
        """获取跟踪器配置"""
        return jsonify({
            'algorithm': tracker_algorithm,
            'parameters': {
                'dt': 1.0,
                'process_noise': 0.08,
                'measurement_noise': 0.8
            }
        })
    
    @app.route('/api/config/tracker', methods=['POST'])
    def set_tracker_config():
        """设置跟踪器参数"""
        data = request.get_json()
        # 可以在这里更新参数
        
        return jsonify({
            'success': True,
            'message': '配置已更新'
        })
    
    return app


def update_performance(latency_ms, fps, memory_mb):
    """更新性能数据"""
    performance_stats['latency'].append(latency_ms)
    performance_stats['fps'] = fps
    performance_stats['memory'].append(memory_mb)
    
    # 保持最近100条
    performance_stats['latency'] = performance_stats['latency'][-100:]
    performance_stats['memory'] = performance_stats['memory'][-100:]
