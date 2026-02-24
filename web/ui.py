"""
Web 可视化界面
包含雷达图、目标列表、状态显示
"""

from flask import Flask, render_template_string, jsonify, request
from flask_socketio import SocketIO, emit
import logging
from datetime import datetime


class RadarWebUI:
    """雷达监控系统 Web UI"""
    
    HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>舟山定海渔港雷达监控系统</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #e0e0e0;
        }
        .radar-sweep {
            position: absolute;
            width: 400px;
            height: 400px;
            border-radius: 50%;
            background: conic-gradient(from 0deg, transparent 0deg, rgba(0, 255, 0, 0.3) 30deg, transparent 60deg);
            animation: sweep 4s linear infinite;
        }
        @keyframes sweep {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        .glass-panel {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
        }
        .target-dot {
            position: absolute;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            transform: translate(-50%, -50%);
            transition: all 0.3s ease;
        }
        .target-radar { background: #00ff88; box-shadow: 0 0 10px #00ff88; }
        .target-ais { background: #00aaff; box-shadow: 0 0 10px #00aaff; }
        .target-fused { background: #ffaa00; box-shadow: 0 0 15px #ffaa00; animation: pulse 1s infinite; }
        @keyframes pulse {
            0%, 100% { transform: translate(-50%, -50%) scale(1); }
            50% { transform: translate(-50%, -50%) scale(1.3); }
        }
        .stat-card {
            background: linear-gradient(145deg, rgba(0,255,136,0.1), rgba(0,170,255,0.1));
            border-left: 4px solid #00ff88;
        }
    </style>
</head>
<body>
    <div class="container mx-auto px-4 py-6">
        <!-- Header -->
        <header class="flex justify-between items-center mb-6">
            <div>
                <h1 class="text-3xl font-bold bg-gradient-to-r from-green-400 to-blue-500 bg-clip-text text-transparent">
                    舟山定海渔港雷达监控系统
                </h1>
                <p class="text-gray-400 text-sm mt-1">Zhoushan Dinghai Fishery Port Radar System v2.0</p>
            </div>
            <div class="flex items-center gap-4">
                <div class="glass-panel px-4 py-2 flex items-center gap-2">
                    <span class="w-3 h-3 rounded-full" id="connectionStatus"></span>
                    <span id="connectionText">连接中...</span>
                </div>
                <div class="text-right">
                    <div class="text-2xl font-mono" id="currentTime">--:--:--</div>
                </div>
            </div>
        </header>
        
        <!-- Stats -->
        <div class="grid grid-cols-4 gap-4 mb-6">
            <div class="stat-card glass-panel p-4">
                <div class="text-gray-400 text-sm">雷达目标</div>
                <div class="text-3xl font-bold text-green-400" id="radarCount">0</div>
            </div>
            <div class="glass-panel p-4" style="border-left-color: #00aaff;">
                <div class="text-gray-400 text-sm">AIS目标</div>
                <div class="text-3xl font-bold text-blue-400" id="aisCount">0</div>
            </div>
            <div class="glass-panel p-4" style="border-left-color: #ffaa00;">
                <div class="text-gray-400 text-sm">融合目标</div>
                <div class="text-3xl font-bold text-yellow-400" id="fusedCount">0</div>
            </div>
            <div class="glass-panel p-4" style="border-left-color: #ff5555;">
                <div class="text-gray-400 text-sm">系统状态</div>
                <div class="text-xl font-bold text-green-400" id="systemStatus">正常</div>
            </div>
        </div>
        
        <!-- Main Content -->
        <div class="grid grid-cols-3 gap-6">
            <!-- Radar Display -->
            <div class="col-span-2 glass-panel p-4">
                <h2 class="text-xl font-bold mb-4 flex items-center gap-2">
                    <span class="w-3 h-3 bg-green-400 rounded-full animate-pulse"></span>
                    雷达显示
                </h2>
                <div class="relative" style="height: 500px;">
                    <!-- Radar Circles -->
                    <div class="absolute inset-0 flex items-center justify-center">
                        <svg width="450" height="450" viewBox="0 0 450 450">
                            <!-- Radar circles -->
                            <circle cx="225" cy="225" r="200" fill="none" stroke="rgba(0,255,136,0.2)" stroke-width="1"/>
                            <circle cx="225" cy="225" r="150" fill="none" stroke="rgba(0,255,136,0.15)" stroke-width="1"/>
                            <circle cx="225" cy="225" r="100" fill="none" stroke="rgba(0,255,136,0.1)" stroke-width="1"/>
                            <circle cx="225" cy="225" r="50" fill="none" stroke="rgba(0,255,136,0.05)" stroke-width="1"/>
                            <!-- Cross lines -->
                            <line x1="225" y1="25" x2="225" y2="425" stroke="rgba(0,255,136,0.1)" stroke-width="1"/>
                            <line x1="25" y1="225" x2="425" y2="225" stroke="rgba(0,255,136,0.1)" stroke-width="1"/>
                            <!-- Diagonal lines -->
                            <line x1="83" y1="83" x2="367" y2="367" stroke="rgba(0,255,136,0.05)" stroke-width="1"/>
                            <line x1="367" y1="83" x2="83" y2="367" stroke="rgba(0,255,136,0.05)" stroke-width="1"/>
                        </svg>
                    </div>
                    <!-- Sweep effect -->
                    <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
                        <div class="radar-sweep opacity-30"></div>
                    </div>
                    <!-- Target markers -->
                    <div id="radarTargets" class="absolute inset-0"></div>
                </div>
                <div class="flex justify-center gap-6 mt-4 text-sm">
                    <div class="flex items-center gap-2">
                        <span class="w-3 h-3 rounded-full bg-green-400"></span>
                        <span>雷达目标</span>
                    </div>
                    <div class="flex items-center gap-2">
                        <span class="w-3 h-3 rounded-full bg-blue-400"></span>
                        <span>AIS目标</span>
                    </div>
                    <div class="flex items-center gap-2">
                        <span class="w-3 h-3 rounded-full bg-yellow-400 animate-pulse"></span>
                        <span>融合目标</span>
                    </div>
                </div>
            </div>
            
            <!-- Target List -->
            <div class="glass-panel p-4">
                <h2 class="text-xl font-bold mb-4">目标列表</h2>
                <div class="space-y-2 max-h-96 overflow-y-auto" id="targetList">
                    <div class="text-gray-500 text-center py-8">等待数据...</div>
                </div>
            </div>
        </div>
        
        <!-- Logs -->
        <div class="mt-6 glass-panel p-4">
            <h2 class="text-xl font-bold mb-4">系统日志</h2>
            <div class="font-mono text-sm text-green-400 max-h-40 overflow-y-auto" id="logPanel">
            </div>
        </div>
    </div>
    
    <script>
        // Update time
        function updateTime() {
            const now = new Date();
            document.getElementById('currentTime').textContent = now.toLocaleTimeString('zh-CN');
        }
        setInterval(updateTime, 1000);
        
        // Socket.IO connection
        const socket = io();
        
        socket.on('connect', function() {
            document.getElementById('connectionStatus').className = 'w-3 h-3 rounded-full bg-green-400';
            document.getElementById('connectionText').textContent = '已连接';
            addLog('系统已连接到服务器');
        });
        
        socket.on('disconnect', function() {
            document.getElementById('connectionStatus').className = 'w-3 h-3 rounded-full bg-red-400';
            document.getElementById('connectionText').textContent = '断开连接';
        });
        
        socket.on('target_update', function(data) {
            updateTargets(data);
        });
        
        function updateTargets(data) {
            // Update counts
            document.getElementById('radarCount').textContent = data.radar ? data.radar.length : 0;
            document.getElementById('aisCount').textContent = data.ais ? data.ais.length : 0;
            document.getElementById('fusedCount').textContent = data.fused ? data.fused.length : 0;
            
            // Update radar display
            const radarContainer = document.getElementById('radarTargets');
            radarContainer.innerHTML = '';
            
            // Draw targets
            if (data.fused) {
                data.fused.forEach(target => {
                    const dot = document.createElement('div');
                    // Convert to radar coordinates (simplified)
                    const angle = target.course_deg || 0;
                    const distance = target.distance_nm || 0;
                    const x = 225 + Math.sin(angle * Math.PI / 180) * distance * 40;
                    const y = 225 - Math.cos(angle * Math.PI / 180) * distance * 40;
                    
                    dot.className = `target-dot target-${target.source_type}`;
                    dot.style.left = `${x}px`;
                    dot.style.top = `${y}px`;
                    dot.title = `${target.id} - ${target.name || '未命名'}`;
                    radarContainer.appendChild(dot);
                });
            }
            
            // Update target list
            const listContainer = document.getElementById('targetList');
            if (data.fused && data.fused.length > 0) {
                listContainer.innerHTML = data.fused.map(t => `
                    <div class="glass-panel p-3 flex justify-between items-center">
                        <div>
                            <div class="font-bold text-yellow-400">${t.id}</div>
                            <div class="text-sm text-gray-400">${t.name || '未命名'}</div>
                        </div>
                        <div class="text-right text-sm">
                            <div>速度: ${t.speed_knots.toFixed(1)} kn</div>
                            <div>航向: ${t.course_deg.toFixed(0)}°</div>
                        </div>
                    </div>
                `).join('');
            }
        }
        
        function addLog(message) {
            const logPanel = document.getElementById('logPanel');
            const time = new Date().toLocaleTimeString('zh-CN');
            logPanel.innerHTML = `<div>[${time}] ${message}</div>` + logPanel.innerHTML;
        }
        
        // Initial time
        updateTime();
        addLog('页面加载完成');
    </script>
</body>
</html>
'''
    
    def __init__(self, app, socketio):
        self.app = app
        self.socketio = socketio
        self._setup_routes()
    
    def _setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template_string(self.HTML_TEMPLATE)


def create_ui(app, socketio):
    """创建UI"""
    ui = RadarWebUI(app, socketio)
    return ui
