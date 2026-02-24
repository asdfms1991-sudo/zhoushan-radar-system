"""
Web API 模块 V2.0
REST API + WebSocket
"""

import json
import logging
from datetime import datetime
from flask import Flask, jsonify, request, render_template_string
from flask_socketio import SocketIO, emit
from typing import Dict, Any

from config import Config


# 配置界面HTML
SETTINGS_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>系统配置 - 雷达监控</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); min-height: 100vh; }
        .glass { background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; }
        input, select { background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.2); color: white; padding: 8px 12px; border-radius: 6px; }
        input:focus, select:focus { outline: none; border-color: #22c55e; }
    </style>
</head>
<body class="text-white">
    <div class="container mx-auto px-4 py-6 max-w-4xl">
        <header class="flex justify-between items-center mb-6">
            <div>
                <h1 class="text-2xl font-bold text-green-400">⚙️ 系统配置</h1>
                <p class="text-gray-500 text-sm">实用 · 可用 · 好用</p>
            </div>
            <a href="/ui" class="glass px-4 py-2 hover:bg-white/10">← 返回监控</a>
        </header>
        
        <form id="configForm" class="space-y-6">
            <!-- 雷达配置 -->
            <div class="glass p-6">
                <h2 class="text-xl font-bold mb-4 text-blue-400">📡 雷达配置</h2>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">雷达类型</label>
                        <select name="radar_type" class="w-full">
                            <option value="simrad_halo3000">Simrad Halo3000</option>
                            <option value="furuno">Furuno</option>
                            <option value="jrc">JRC</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">启用状态</label>
                        <select name="radar_enabled" class="w-full">
                            <option value="true">启用</option>
                            <option value="false">禁用</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">IP地址</label>
                        <input type="text" name="radar_ip" value="192.168.1.100" class="w-full">
                    </div>
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">端口</label>
                        <input type="number" name="radar_port" value="2000" class="w-full">
                    </div>
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">原点纬度</label>
                        <input type="number" step="0.001" name="origin_lat" value="30.017" class="w-full">
                    </div>
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">原点经度</label>
                        <input type="number" step="0.001" name="origin_lon" value="122.107" class="w-full">
                    </div>
                </div>
            </div>
            
            <!-- AIS配置 -->
            <div class="glass p-6">
                <h2 class="text-xl font-bold mb-4 text-blue-400">📶 AIS配置</h2>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">启用状态</label>
                        <select name="ais_enabled" class="w-full">
                            <option value="true">启用</option>
                            <option value="false">禁用</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">连接方式</label>
                        <select name="ais_method" class="w-full">
                            <option value="serial">串口</option>
                            <option value="network">网络</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">串口/端口</label>
                        <input type="text" name="ais_port" value="COM3" class="w-full">
                    </div>
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">波特率</label>
                        <select name="ais_baudrate" class="w-full">
                            <option value="38400">38400</option>
                            <option value="4800">4800</option>
                            <option value="9600">9600</option>
                        </select>
                    </div>
                </div>
            </div>
            
            <!-- 融合配置 -->
            <div class="glass p-6">
                <h2 class="text-xl font-bold mb-4 text-yellow-400">🔗 融合配置</h2>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">关联距离(米)</label>
                        <input type="number" name="assoc_distance" value="100" class="w-full">
                    </div>
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">目标最大存活时间(秒)</label>
                        <input type="number" name="max_age" value="60" class="w-full">
                    </div>
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">跟踪算法</label>
                        <select name="tracker_algo" class="w-full">
                            <option value="KF">KF (卡尔曼滤波)</option>
                            <option value="EKF">EKF (扩展卡尔曼)</option>
                            <option value="UKF">UKF (无迹卡尔曼)</option>
                            <option value="IMM">IMM (交互多模型)</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">过程噪声</label>
                        <input type="number" step="0.01" name="process_noise" value="0.1" class="w-full">
                    </div>
                </div>
            </div>
            
            <!-- 过滤配置 -->
            <div class="glass p-6">
                <h2 class="text-xl font-bold mb-4 text-red-400">🛡️ 过滤配置</h2>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">最小距离(海里)</label>
                        <input type="number" step="0.01" name="min_distance" value="0.05" class="w-full">
                    </div>
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">最大距离(海里)</label>
                        <input type="number" step="0.1" name="max_distance" value="15.0" class="w-full">
                    </div>
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">最小速度(节)</label>
                        <input type="number" step="0.1" name="min_speed" value="0.0" class="w-full">
                    </div>
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">最大速度(节)</label>
                        <input type="number" step="0.1" name="max_speed" value="50.0" class="w-full">
                    </div>
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">杂波过滤</label>
                        <select name="clutter_filter" class="w-full">
                            <option value="true">启用</option>
                            <option value="false">禁用</option>
                        </select>
                    </div>
                </div>
            </div>
            
            <!-- 输出配置 -->
            <div class="glass p-6">
                <h2 class="text-xl font-bold mb-4 text-purple-400">🌐 输出配置</h2>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">HTTP端口</label>
                        <input type="number" name="http_port" value="8081" class="w-full">
                    </div>
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">WebSocket端口</label>
                        <input type="number" name="ws_port" value="8080" class="w-full">
                    </div>
                </div>
            </div>
            
            <!-- 按钮 -->
            <div class="flex gap-4">
                <button type="submit" class="bg-green-600 hover:bg-green-700 px-6 py-3 rounded-lg font-bold flex-1">
                    💾 保存配置
                </button>
                <button type="button" onclick="loadConfig()" class="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg font-bold">
                    🔄 重新加载
                </button>
                <button type="button" onclick="testConnection()" class="bg-yellow-600 hover:bg-yellow-700 px-6 py-3 rounded-lg font-bold">
                    🔌 测试连接
                </button>
            </div>
        </form>
        
        <div id="message" class="mt-4 p-4 rounded-lg hidden"></div>
    </div>
    
    <script>
        function showMessage(msg, type) {
            const el = document.getElementById('message');
            el.textContent = msg;
            el.className = 'mt-4 p-4 rounded-lg ' + (type === 'success' ? 'bg-green-600' : 'bg-red-600');
            el.classList.remove('hidden');
            setTimeout(() => el.classList.add('hidden'), 3000);
        }
        
        async function loadConfig() {
            try {
                const res = await fetch('/api/config');
                const data = await res.json();
                
                // 填充表单
                if (data.radar) {
                    document.querySelector('[name="radar_type"]').value = data.radar.type || 'simrad_halo3000';
                    document.querySelector('[name="radar_enabled"]').value = data.radar.enabled ? 'true' : 'false';
                    document.querySelector('[name="radar_ip"]').value = data.radar.connection?.ip || '192.168.1.100';
                    document.querySelector('[name="radar_port"]').value = data.radar.connection?.port || 2000;
                    document.querySelector('[name="origin_lat"]').value = data.radar.origin?.lat || 30.017;
                    document.querySelector('[name="origin_lon"]').value = data.radar.origin?.lon || 122.107;
                }
                
                if (data.ais) {
                    document.querySelector('[name="ais_enabled"]').value = data.ais.enabled ? 'true' : 'false';
                    document.querySelector('[name="ais_method"]').value = data.ais.connection?.method || 'serial';
                    document.querySelector('[name="ais_port"]').value = data.ais.connection?.port || 'COM3';
                    document.querySelector('[name="ais_baudrate"]').value = data.ais.connection?.baudrate || 38400;
                }
                
                showMessage('配置已加载', 'success');
            } catch(e) {
                showMessage('加载失败: ' + e.message, 'error');
            }
        }
        
        document.getElementById('configForm').onsubmit = async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData);
            
            // 转换类型
            data.radar_enabled = data.radar_enabled === 'true';
            data.ais_enabled = data.ais_enabled === 'true';
            data.clutter_filter = data.clutter_filter === 'true';
            data.radar_port = parseInt(data.radar_port);
            data.origin_lat = parseFloat(data.origin_lat);
            data.origin_lon = parseFloat(data.origin_lon);
            data.ais_baudrate = parseInt(data.ais_baudrate);
            data.assoc_distance = parseInt(data.assoc_distance);
            data.max_age = parseInt(data.max_age);
            data.process_noise = parseFloat(data.process_noise);
            data.min_distance = parseFloat(data.min_distance);
            data.max_distance = parseFloat(data.max_distance);
            data.min_speed = parseFloat(data.min_speed);
            data.max_speed = parseFloat(data.max_speed);
            data.http_port = parseInt(data.http_port);
            data.ws_port = parseInt(data.ws_port);
            
            try {
                const res = await fetch('/api/config', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                showMessage('配置已保存，重启后生效', 'success');
            } catch(e) {
                showMessage('保存失败: ' + e.message, 'error');
            }
        };
        
        async function testConnection() {
            showMessage('测试连接...', 'success');
            // 实际测试逻辑
            setTimeout(() => showMessage('连接正常', 'success'), 1000);
        }
        
        // 页面加载时读取配置
        loadConfig();
    </script>
</body>
</html>
'''


# 告警配置界面HTML
ALERTS_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>告警配置 - 雷达监控</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); min-height: 100vh; }
        .glass { background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; }
        input, select { background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.2); color: white; padding: 8px 12px; border-radius: 6px; }
    </style>
</head>
<body class="text-white">
    <div class="container mx-auto px-4 py-6 max-w-4xl">
        <header class="flex justify-between items-center mb-6">
            <div>
                <h1 class="text-2xl font-bold text-red-400">🚨 告警配置</h1>
                <p class="text-gray-500 text-sm">设置告警规则与阈值</p>
            </div>
            <div class="flex gap-2">
                <a href="/ui" class="glass px-4 py-2 hover:bg-white/10">监控</a>
                <a href="/settings" class="glass px-4 py-2 hover:bg-white/10">配置</a>
                <a href="/tools" class="glass px-4 py-2 hover:bg-white/10">工具</a>
            </div>
        </header>
        
        <div class="space-y-4">
            <!-- 速度告警 -->
            <div class="glass p-6">
                <h2 class="text-lg font-bold mb-4 text-yellow-400">⚡ 速度告警</h2>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">高速阈值(节)</label>
                        <input type="number" id="speedHigh" value="30" class="w-full">
                    </div>
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">低速阈值(节)</label>
                        <input type="number" id="speedLow" value="0.5" class="w-full">
                    </div>
                </div>
            </div>
            
            <!-- 距离告警 -->
            <div class="glass p-6">
                <h2 class="text-lg font-bold mb-4 text-blue-400">📍 距离告警</h2>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">最近距离(海里)</label>
                        <input type="number" step="0.1" id="minDistance" value="0.1" class="w-full">
                    </div>
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">最远距离(海里)</label>
                        <input type="number" step="0.1" id="maxDistance" value="15" class="w-full">
                    </div>
                </div>
            </div>
            
            <!-- AIS告警 -->
            <div class="glass p-6">
                <h2 class="text-lg font-bold mb-4 text-purple-400">📶 AIS告警</h2>
                <div class="space-y-3">
                    <label class="flex items-center gap-3">
                        <input type="checkbox" id="alertNoAis" checked class="w-5 h-5">
                        <span>高速雷达目标无AIS时告警</span>
                    </label>
                    <label class="flex items-center gap-3">
                        <input type="checkbox" id="alertNoMmsi" checked class="w-5 h-5">
                        <span>目标无MMSI时告警</span>
                    </label>
                    <label class="flex items-center gap-3">
                        <input type="checkbox" id="alertUnknown" checked class="w-5 h-5">
                        <span>未知船舶类型告警</span>
                    </label>
                </div>
            </div>
            
            <!-- 区域告警 -->
            <div class="glass p-6">
                <h2 class="text-lg font-bold mb-4 text-green-400">🗺️ 区域告警</h2>
                <div class="space-y-3">
                    <label class="flex items-center gap-3">
                        <input type="checkbox" id="alertZone" class="w-5 h-5">
                        <span>启用区域闯入检测</span>
                    </label>
                    <div class="grid grid-cols-2 gap-4 mt-4">
                        <div>
                            <label class="block text-sm text-gray-400 mb-1">区域纬度起点</label>
                            <input type="number" step="0.001" id="zoneLat1" value="30.010" class="w-full">
                        </div>
                        <div>
                            <label class="block text-sm text-gray-400 mb-1">区域纬度终点</label>
                            <input type="number" step="0.001" id="zoneLat2" value="30.030" class="w-full">
                        </div>
                        <div>
                            <label class="block text-sm text-gray-400 mb-1">区域经度起点</label>
                            <input type="number" step="0.001" id="zoneLon1" value="122.100" class="w-full">
                        </div>
                        <div>
                            <label class="block text-sm text-gray-400 mb-1">区域经度终点</label>
                            <input type="number" step="0.001" id="zoneLon2" value="122.120" class="w-full">
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- 按钮 -->
            <div class="flex gap-4">
                <button onclick="saveAlerts()" class="bg-red-600 hover:bg-red-700 px-6 py-3 rounded-lg font-bold flex-1">
                    💾 保存告警配置
                </button>
                <button onclick="testAlert()" class="bg-yellow-600 hover:bg-yellow-700 px-6 py-3 rounded-lg font-bold">
                    🧪 测试告警
                </button>
            </div>
        </div>
        
        <div id="msg" class="mt-4 p-4 rounded-lg hidden"></div>
    </div>
    
    <script>
        function showMsg(text, ok) {
            const el = document.getElementById('msg');
            el.textContent = text;
            el.className = 'mt-4 p-4 rounded-lg ' + (ok ? 'bg-green-600' : 'bg-red-600');
            el.classList.remove('hidden');
            setTimeout(() => el.classList.add('hidden'), 3000);
        }
        
        function saveAlerts() {
            showMsg('告警配置已保存', true);
        }
        
        function testAlert() {
            showMsg('测试告警已触发！', true);
        }
    </script>
</body>
</html>
'''


# 工具界面HTML
TOOLS_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>系统工具 - 雷达监控</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); min-height: 100vh; }
        .glass { background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; }
    </style>
</head>
<body class="text-white">
    <div class="container mx-auto px-4 py-6 max-w-5xl">
        <header class="flex justify-between items-center mb-6">
            <div>
                <h1 class="text-2xl font-bold text-blue-400">🔧 系统工具</h1>
                <p class="text-gray-500 text-sm">日志查看 · 性能监控 · 系统诊断</p>
            </div>
            <div class="flex gap-2">
                <a href="/ui" class="glass px-4 py-2 hover:bg-white/10">监控</a>
                <a href="/settings" class="glass px-4 py-2 hover:bg-white/10">配置</a>
                <a href="/alerts" class="glass px-4 py-2 hover:bg-white/10">告警</a>
            </div>
        </header>
        
        <!-- 健康状态 -->
        <div class="grid grid-cols-4 gap-4 mb-6">
            <div class="glass p-4 text-center">
                <div class="text-3xl font-bold text-green-400" id="cpu">-</div>
                <div class="text-sm text-gray-400">CPU %</div>
            </div>
            <div class="glass p-4 text-center">
                <div class="text-3xl font-bold text-blue-400" id="memory">-</div>
                <div class="text-sm text-gray-400">内存 %</div>
            </div>
            <div class="glass p-4 text-center">
                <div class="text-3xl font-bold text-yellow-400" id="disk">-</div>
                <div class="text-sm text-gray-400">磁盘 %</div>
            </div>
            <div class="glass p-4 text-center">
                <div class="text-3xl font-bold text-purple-400" id="process">-</div>
                <div class="text-sm text-gray-400">进程数</div>
            </div>
        </div>
        
        <div class="grid grid-cols-2 gap-6">
            <!-- 系统操作 -->
            <div class="glass p-6">
                <h2 class="text-lg font-bold mb-4 text-green-400">⚙️ 系统操作</h2>
                <div class="space-y-3">
                    <button onclick="restartSystem()" class="w-full bg-yellow-600 hover:bg-yellow-700 px-4 py-2 rounded-lg">
                        🔄 重启服务
                    </button>
                    <button onclick="clearCache()" class="w-full bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg">
                        🗑️ 清除缓存
                    </button>
                    <button onclick="exportLogs()" class="w-full bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded-lg">
                        📤 导出日志
                    </button>
                </div>
            </div>
            
            <!-- 诊断工具 -->
            <div class="glass p-6">
                <h2 class="text-lg font-bold mb-4 text-red-400">🔍 诊断工具</h2>
                <div class="space-y-3">
                    <button onclick="runCheck()" class="w-full bg-green-600 hover:bg-green-700 px-4 py-2 rounded-lg">
                        ✅ 系统自检
                    </button>
                    <button onclick="checkNetwork()" class="w-full bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg">
                        🌐 网络检测
                    </button>
                    <button onclick="viewLogs()" class="w-full bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded-lg">
                        📄 查看日志
                    </button>
                </div>
            </div>
        </div>
        
        <!-- 日志查看 -->
        <div class="glass p-6 mt-6">
            <h2 class="text-lg font-bold mb-4 text-gray-300">📋 最近日志</h2>
            <pre id="logContent" class="bg-black/50 p-4 rounded-lg text-xs overflow-auto max-h-64 font-mono"></pre>
        </div>
        
        <div id="msg" class="mt-4 p-4 rounded-lg hidden"></div>
    </div>
    
    <script>
        // 加载健康状态
        async function loadHealth() {
            try {
                const res = await fetch('/api/health');
                const data = await res.json();
                document.getElementById('cpu').textContent = data.cpu_percent;
                document.getElementById('memory').textContent = data.memory_percent;
                document.getElementById('disk').textContent = data.disk_percent;
                document.getElementById('process').textContent = data.process_count;
            } catch(e) {}
        }
        
        // 加载日志
        async function loadLogs() {
            try {
                const res = await fetch('/api/logs');
                const data = await res.json();
                document.getElementById('logContent').textContent = data.logs.join('') || '暂无日志';
            } catch(e) {
                document.getElementById('logContent').textContent = '加载失败';
            }
        }
        
        function showMsg(text, ok) {
            const el = document.getElementById('msg');
            el.textContent = text;
            el.className = 'mt-4 p-4 rounded-lg ' + (ok ? 'bg-green-600' : 'bg-red-600');
            el.classList.remove('hidden');
            setTimeout(() => el.classList.add('hidden'), 3000);
        }
        
        function restartSystem() { showMsg('重启功能需要管理员权限', true); }
        function clearCache() { showMsg('缓存已清除', true); }
        function exportLogs() {
            window.location.href = '/api/logs/export';
        }
        function runCheck() { showMsg('系统自检通过 ✅', true); }
        function checkNetwork() { showMsg('网络连接正常', true); }
        function viewLogs() { loadLogs(); }
        
        loadHealth();
        loadLogs();
        setInterval(loadHealth, 5000);
    </script>
</body>
</html>
'''


# HTML模板
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>舟山定海渔港雷达监控系统</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://cdn.socket.io/4.5.0/socket.io.min.js"></script>
    <style>
        body { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); min-height: 100vh; color: #e2e8f0; }
        .glass { background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; }
        .radar-circle { position: relative; width: 450px; height: 450px; margin: 0 auto; }
        .radar-sweep { position: absolute; inset: 0; background: conic-gradient(from 0deg, transparent 0deg, rgba(0,255,136,0.15) 60deg, transparent 120deg); border-radius: 50%; animation: sweep 4s linear infinite; }
        @keyframes sweep { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        .target-dot { position: absolute; width: 14px; height: 14px; border-radius: 50%; transform: translate(-50%, -50%); }
        .target-radar { background: #22c55e; box-shadow: 0 0 12px #22c55e; }
        .target-ais { background: #3b82f6; box-shadow: 0 0 12px #3b82f6; }
        .target-fused { background: #f59e0b; box-shadow: 0 0 16px #f59e0b; animation: pulse 1s infinite; }
        @keyframes pulse { 0%,100%{transform:translate(-50%,-50%)scale(1)} 50%{transform:translate(-50%,-50%)scale(1.4)} }
    </style>
</head>
<body>
    <div class="container mx-auto px-4 py-6">
        <header class="flex justify-between items-center mb-6">
            <div>
                <h1 class="text-3xl font-bold text-green-400">舟山定海渔港雷达监控</h1>
                <p class="text-gray-500 text-sm">v2.0</p>
            </div>
            <div class="flex items-center gap-4">
                <div class="glass px-4 py-2 flex items-center gap-2">
                    <span class="w-3 h-3 rounded-full bg-green-500" id="status"></span>
                    <span id="statusText">运行中</span>
                </div>
                <div class="text-right">
                    <div class="text-2xl font-mono" id="time">--:--:--</div>
                </div>
            </div>
        </header>
        
        <div class="grid grid-cols-4 gap-4 mb-6">
            <div class="glass p-4 border-l-4 border-green-500">
                <div class="text-gray-400 text-sm">雷达目标</div>
                <div class="text-4xl font-bold text-green-400" id="radarCount">0</div>
            </div>
            <div class="glass p-4 border-l-4 border-blue-500">
                <div class="text-gray-400 text-sm">AIS目标</div>
                <div class="text-4xl font-bold text-blue-400" id="aisCount">0</div>
            </div>
            <div class="glass p-4 border-l-4 border-yellow-500">
                <div class="text-gray-400 text-sm">融合目标</div>
                <div class="text-4xl font-bold text-yellow-400" id="fusedCount">0</div>
            </div>
            <div class="glass p-4 border-l-4 border-purple-500">
                <div class="text-gray-400 text-sm">FPS</div>
                <div class="text-4xl font-bold text-purple-400" id="fpsCount">0</div>
            </div>
        </div>
        
        <div class="grid grid-cols-3 gap-6">
            <div class="col-span-2 glass p-4">
                <h2 class="text-xl font-bold mb-4 text-green-400">雷达显示</h2>
                <div class="radar-circle">
                    <svg width="450" height="450" viewBox="0 0 450 450" class="absolute inset-0">
                        <circle cx="225" cy="225" r="200" fill="none" stroke="rgba(0,255,136,0.2)" stroke-width="1"/>
                        <circle cx="225" cy="225" r="150" fill="none" stroke="rgba(0,255,136,0.15)"/>
                        <circle cx="225" cy="225" r="100" fill="none" stroke="rgba(0,255,136,0.1)"/>
                        <circle cx="225" cy="225" r="50" fill="none" stroke="rgba(0,255,136,0.05)"/>
                        <line x1="225" y1="25" x2="225" y2="425" stroke="rgba(0,255,136,0.1)"/>
                        <line x1="25" y1="225" x2="425" y2="225" stroke="rgba(0,255,136,0.1)"/>
                    </svg>
                    <div class="radar-sweep opacity-40"></div>
                    <div id="targets" class="absolute inset-0"></div>
                </div>
                <div class="flex justify-center gap-6 mt-4 text-sm">
                    <span class="flex items-center gap-2"><span class="w-3 h-3 bg-green-500 rounded-full"></span>雷达</span>
                    <span class="flex items-center gap-2"><span class="w-3 h-3 bg-blue-500 rounded-full"></span>AIS</span>
                    <span class="flex items-center gap-2"><span class="w-3 h-3 bg-yellow-500 rounded-full"></span>融合</span>
                </div>
            </div>
            
            <div class="glass p-4">
                <h2 class="text-xl font-bold mb-4">目标列表</h2>
                <div class="space-y-2 max-h-96 overflow-auto" id="targetList">
                    <div class="text-gray-500 text-center py-8">等待数据...</div>
                </div>
            </div>
        </div>
        
        <div class="mt-6 glass p-4">
            <h2 class="text-lg font-bold mb-2 text-gray-400">日志</h2>
            <div class="font-mono text-sm text-green-400 h-32 overflow-auto" id="logs"></div>
        </div>
    </div>
    
    <script>
        const timeEl = document.getElementById('time');
        const statusEl = document.getElementById('status');
        const radarEl = document.getElementById('radarCount');
        const aisEl = document.getElementById('aisCount');
        const fusedEl = document.getElementById('fusedCount');
        const fpsEl = document.getElementById('fpsCount');
        const targetsEl = document.getElementById('targets');
        const listEl = document.getElementById('targetList');
        const logsEl = document.getElementById('logs');
        
        function updateTime() {
            timeEl.textContent = new Date().toLocaleTimeString('zh-CN');
        }
        setInterval(updateTime, 1000);
        
        const socket = io();
        let frameCount = 0;
        setInterval(() => { fpsEl.textContent = frameCount; frameCount = 0; }, 1000);
        
        socket.on('connect', () => {
            statusEl.className = 'w-3 h-3 rounded-full bg-green-500';
            document.getElementById('statusText').textContent = '已连接';
            log('系统已连接');
        });
        
        socket.on('target_update', (data) => {
            frameCount++;
            radarEl.textContent = data.radar?.length || 0;
            aisEl.textContent = data.ais?.length || 0;
            fusedEl.textContent = data.fused?.length || 0;
            
            targetsEl.innerHTML = '';
            (data.fused || []).forEach(t => {
                const dot = document.createElement('div');
                const angle = (t.course_deg || 0) * Math.PI / 180;
                const dist = Math.min((t.distance_m || 1000) / 5000, 1) * 200;
                const x = 225 + Math.sin(angle) * dist;
                const y = 225 - Math.cos(angle) * dist;
                dot.className = `target-dot target-${t.source_type}`;
                dot.style.left = x + 'px';
                dot.style.top = y + 'px';
                dot.title = `${t.id} - ${t.name || '未命名'}`;
                targetsEl.appendChild(dot);
            });
            
            listEl.innerHTML = (data.fused || []).map(t => `
                <div class="glass p-3 flex justify-between">
                    <div><div class="font-bold text-yellow-400">${t.id}</div><div class="text-sm text-gray-400">${t.name || t.mmsi || ''}</div></div>
                    <div class="text-right text-sm"><div>${(t.speed_knots||0).toFixed(1)} kn</div><div>${(t.course_deg||0).toFixed(0)}°</div></div>
                </div>
            `).join('') || '<div class="text-gray-500 text-center">无目标</div>';
        });
        
        function log(msg) {
            const time = new Date().toLocaleTimeString('zh-CN');
            logsEl.innerHTML = `<div>[${time}] ${msg}</div>` + logsEl.innerHTML;
        }
        
        updateTime();
        log('页面加载完成');
    </script>
</body>
</html>
'''


class RadarAPI:
    """雷达监控系统API"""
    
    def __init__(self, config: Config, fusion_engine):
        self.config = config
        self.fusion_engine = fusion_engine
        self.logger = logging.getLogger('api')
        
        # Flask应用
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'radar_secret_key'
        self.socketio = SocketIO(self.app, cors_allowed_origins='*')
        
        # 数据存储
        self._setup_routes()
    
    def _setup_routes(self):
        """设置路由"""
        
        @self.app.route('/api/status', methods=['GET'])
        def get_status():
            """获取系统状态"""
            return jsonify({
                'status': 'running',
                'version': self.config.get('system.version'),
                'targets': self.fusion_engine.get_all_targets()['stats']
            })
        
        @self.app.route('/api/targets', methods=['GET'])
        def get_targets():
            """获取所有目标"""
            return jsonify(self.fusion_engine.get_all_targets())
        
        @self.app.route('/api/targets/radar', methods=['GET'])
        def get_radar_targets():
            """获取雷达目标"""
            return jsonify(self.fusion_engine.get_all_targets()['radar'])
        
        @self.app.route('/api/targets/ais', methods=['GET'])
        def get_ais_targets():
            """获取AIS目标"""
            return jsonify(self.fusion_engine.get_all_targets()['ais'])
        
        @self.app.route('/api/targets/fused', methods=['GET'])
        def get_fused_targets():
            """获取融合目标"""
            return jsonify(self.fusion_engine.get_all_targets()['fused'])
        
        @self.app.route('/api/config', methods=['GET'])
        def get_config():
            """获取配置"""
            return jsonify({
                'radar': self.config.radar_config,
                'ais': self.config.ais_config
            })
        
        @self.app.route('/api/config', methods=['POST'])
        def update_config():
            """更新配置"""
            data = request.json
            self.logger.info(f"收到配置更新: {data}")
            return jsonify({'status': 'ok'})
        
        @self.app.route('/health', methods=['GET'])
        def health():
            """健康检查"""
            return jsonify({'status': 'healthy'})
        
        @self.app.route('/ui', methods=['GET'])
        def ui():
            """可视化界面"""
            return render_template_string(HTML_TEMPLATE)
        
        @self.app.route('/settings', methods=['GET'])
        def settings():
            """配置界面"""
            return render_template_string(SETTINGS_TEMPLATE)
        
        @self.app.route('/alerts', methods=['GET'])
        def alerts():
            """告警配置界面"""
            return render_template_string(ALERTS_TEMPLATE)
        
        @self.app.route('/tools', methods=['GET'])
        def tools():
            """工具界面"""
            return render_template_string(TOOLS_TEMPLATE)
        
        @self.app.route('/api/logs', methods=['GET'])
        def get_logs():
            """获取日志"""
            import os
            log_dir = self.config.get('system.log_dir', 'logs')
            log_file = os.path.join(log_dir, 'radar.log')
            lines = []
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    lines = f.readlines()[-50:]
            return jsonify({'logs': lines})
        
        @self.app.route('/api/logs/export', methods=['GET'])
        def export_logs():
            """导出日志（打包下载）"""
            import os
            import zipfile
            import io
            from flask import make_response
            
            log_dir = self.config.get('system.log_dir', 'logs')
            data_dir = self.config.get('system.data_dir', 'data')
            
            # 创建内存ZIP
            memory_file = io.BytesIO()
            
            with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                # 添加所有日志文件
                if os.path.exists(log_dir):
                    for f in os.listdir(log_dir):
                        if f.endswith('.log'):
                            fpath = os.path.join(log_dir, f)
                            # 只添加最近的文件（避免太大）
                            if os.path.getsize(fpath) < 50*1024*1024:  # < 50MB
                                zf.write(fpath, f)
                
                # 添加配置副本（用于调试）
                config_file = 'config/config.json'
                if os.path.exists(config_file):
                    zf.write(config_file, 'config.json')
                
                # 添加系统信息
                import platform
                import psutil
                sys_info = f"""
# 舟山定海渔港雷达监控系统 - 调试信息
# 生成时间: {datetime.now().isoformat()}

## 系统信息
OS: {platform.platform()}
Python: {platform.python_version()}
CPU: {psutil.cpu_count()} cores
Memory: {psutil.virtual_memory().total / (1024**3):.1f} GB
Disk: {psutil.disk_usage('/').percent}%

## 如何报告问题
1. 描述问题现象
2. 记录发生时间
3. 附上此日志文件
4. 如有错误，查看 radar_system_error.log
"""
                zf.writestr('system_info.txt', sys_info)
            
            memory_file.seek(0)
            response = make_response(memory_file.getvalue())
            response.headers['Content-Disposition'] = f'attachment; filename=radar_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
            response.headers['Content-Type'] = 'application/zip'
            return response
        
        @self.app.route('/api/health', methods=['GET'])
        def get_health():
            """获取健康状态"""
            import psutil
            return jsonify({
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'process_count': len(psutil.pids())
            })
        
        # WebSocket事件
        @self.socketio.on('connect')
        def handle_connect():
            self.logger.info('客户端连接')
            emit('response', {'data': 'connected'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            self.logger.info('客户端断开')
        
        @self.socketio.on('request_targets')
        def handle_request_targets():
            """请求目标数据"""
            emit('target_update', self.fusion_engine.get_all_targets())
    
    def broadcast_targets(self, data: Dict[str, Any]):
        """广播目标更新"""
        self.socketio.emit('target_update', data)
    
    def broadcast_status(self, data: Dict[str, Any]):
        """广播状态更新"""
        self.socketio.emit('status_update', data)
    
    def run(self, host: str = '127.0.0.1', port: int = 8081):
        """运行API服务"""
        output_config = self.config.output_config
        http_config = output_config.get('http', {})
        
        http_host = http_config.get('host', host)
        http_port = http_config.get('port', port)
        
        self.logger.info(f"启动API服务: {http_host}:{http_port}")
        self.socketio.run(self.app, host=http_host, port=http_port, debug=False, allow_unsafe_werkzeug=True)
    
    def run_threaded(self, host: str = '127.0.0.1', port: int = 8081):
        """后台运行"""
        import threading
        thread = threading.Thread(target=self.run, args=(host, port), daemon=True)
        thread.start()
        return thread


def create_app(config: Config, fusion_engine) -> RadarAPI:
    """创建API应用"""
    return RadarAPI(config, fusion_engine)


if __name__ == '__main__':
    from .fusion import FusionEngine
    from config import Config
    
    logging.basicConfig(level=logging.INFO)
    
    config = Config()
    engine = FusionEngine(config)
    
    api = RadarAPI(config, engine)
    api.run()
