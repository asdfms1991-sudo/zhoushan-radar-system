"""
增强版雷达可视化界面
"""

ENHANCED_HTML = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>舟山定海渔港雷达监控系统 V2.1</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.socket.io/4.5.0/socket.io.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: linear-gradient(135deg, #0a0a1a 0%, #1a1a2e 50%, #0f172a 100%);
            min-height: 100vh;
            color: #e2e8f0;
            font-family: 'Segoe UI', system-ui, sans-serif;
        }
        
        /* 雷达容器 */
        .radar-container {
            position: relative;
            width: 500px;
            height: 500px;
            margin: 0 auto;
        }
        
        /* 雷达扫描 */
        .radar-sweep {
            position: absolute;
            width: 100%;
            height: 100%;
            border-radius: 50%;
            background: conic-gradient(
                from 0deg,
                transparent 0deg,
                rgba(0, 255, 136, 0.15) 30deg,
                rgba(0, 255, 136, 0.25) 60deg,
                transparent 90deg
            );
            animation: sweep 4s linear infinite;
        }
        
        @keyframes sweep {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        
        /* 雷达圆圈 */
        .radar-rings {
            position: absolute;
            width: 100%;
            height: 100%;
            border-radius: 50%;
        }
        
        .radar-rings::before,
        .radar-rings::after {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            border: 1px solid rgba(0, 255, 136, 0.2);
            border-radius: 50%;
        }
        
        .radar-rings::before {
            width: 66%;
            height: 66%;
            border-color: rgba(0, 255, 136, 0.15);
        }
        
        .radar-rings::after {
            width: 33%;
            height: 33%;
            border-color: rgba(0, 255, 136, 0.1);
        }
        
        /* 目标点 */
        .target {
            position: absolute;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            transform: translate(-50%, -50%);
            transition: all 0.3s ease;
        }
        
        .target-radar {
            background: #22c55e;
            box-shadow: 0 0 12px #22c55e, 0 0 24px rgba(34, 197, 94, 0.5);
        }
        
        .target-ais {
            background: #3b82f6;
            box-shadow: 0 0 12px #3b82f6, 0 0 24px rgba(59, 130, 246, 0.5);
        }
        
        .target-fused {
            background: #f59e0b;
            box-shadow: 0 0 16px #f59e0b, 0 0 32px rgba(245, 158, 11, 0.6);
            animation: pulse 1s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { transform: translate(-50%, -50%) scale(1); }
            50% { transform: translate(-50%, -50%) scale(1.3); }
        }
        
        /* 轨迹 */
        .trail {
            position: absolute;
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.3);
            transform: translate(-50%, -50%);
        }
        
        /* 玻璃效果 */
        .glass {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
        }
        
        /* 状态指示 */
        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            animation: blink 2s ease-in-out infinite;
        }
        
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
    </style>
</head>
<body>
    <div class="container mx-auto px-4 py-6">
        <!-- 头部 -->
        <header class="flex justify-between items-center mb-6">
            <div>
                <h1 class="text-3xl font-bold text-green-400">舟山定海渔港雷达监控</h1>
                <p class="text-gray-500">V2.1 增强版</p>
            </div>
            <div class="flex items-center gap-4">
                <div class="glass px-4 py-2 flex items-center gap-2">
                    <span class="status-dot bg-green-500"></span>
                    <span id="statusText">运行中</span>
                </div>
                <div class="text-right">
                    <div class="text-2xl font-mono" id="time">--:--:--</div>
                </div>
            </div>
        </header>
        
        <!-- 统计卡片 -->
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
                <div class="text-gray-400 text-sm">刷新率</div>
                <div class="text-4xl font-bold text-purple-400" id="fpsCount">0</div>
            </div>
        </div>
        
        <!-- 主内容 -->
        <div class="grid grid-cols-3 gap-6">
            <!-- 雷达显示 -->
            <div class="col-span-2 glass p-4">
                <h2 class="text-xl font-bold mb-4 text-green-400 flex items-center gap-2">
                    <span class="w-3 h-3 bg-green-500 rounded-full animate-pulse"></span>
                    雷达显示
                </h2>
                
                <div class="radar-container">
                    <div class="radar-rings"></div>
                    <div class="radar-sweep"></div>
                    <div id="radarDisplay"></div>
                </div>
                
                <!-- 图例 -->
                <div class="flex justify-center gap-6 mt-4 text-sm">
                    <span class="flex items-center gap-2">
                        <span class="w-3 h-3 rounded-full bg-green-500"></span> 雷达
                    </span>
                    <span class="flex items-center gap-2">
                        <span class="w-3 h-3 rounded-full bg-blue-500"></span> AIS
                    </span>
                    <span class="flex items-center gap-2">
                        <span class="w-3 h-3 rounded-full bg-yellow-500"></span> 融合
                    </span>
                </div>
            </div>
            
            <!-- 目标列表 -->
            <div class="glass p-4">
                <h2 class="text-xl font-bold mb-4">目标列表</h2>
                <div class="space-y-2 max-h-96 overflow-auto" id="targetList">
                    <div class="text-gray-500 text-center py-8">等待数据...</div>
                </div>
            </div>
        </div>
        
        <!-- 日志 -->
        <div class="mt-6 glass p-4">
            <h2 class="text-lg font-bold mb-2 text-gray-400">系统日志</h2>
            <div class="font-mono text-sm text-green-400 h-32 overflow-auto" id="logs"></div>
        </div>
    </div>
    
    <script>
        // 更新时间和连接
        const timeEl = document.getElementById('time');
        const statusEl = document.getElementById('statusText');
        const radarEl = document.getElementById('radarCount');
        const aisEl = document.getElementById('aisCount');
        const fusedEl = document.getElementById('fusedCount');
        const fpsEl = document.getElementById('fpsCount');
        const displayEl = document.getElementById('radarDisplay');
        const listEl = document.getElementById('targetList');
        const logsEl = document.getElementById('logs');
        
        function updateTime() {
            timeEl.textContent = new Date().toLocaleTimeString('zh-CN');
        }
        setInterval(updateTime, 1000);
        updateTime();
        
        // Socket.IO 连接
        const socket = io();
        let frameCount = 0;
        let lastTime = Date.now();
        
        setInterval(() => {
            const now = Date.now();
            const fps = Math.round(frameCount * 1000 / (now - lastTime));
            fpsEl.textContent = fps;
            frameCount = 0;
            lastTime = now;
        }, 1000);
        
        socket.on('connect', () => {
            statusEl.textContent = '已连接';
            log('系统已连接');
        });
        
        socket.on('disconnect', () => {
            statusEl.textContent = '断开';
            log('连接断开');
        });
        
        socket.on('target_update', (data) => {
            frameCount++;
            updateDisplay(data);
        });
        
        function updateDisplay(data) {
            radarEl.textContent = data.radar?.length || 0;
            aisEl.textContent = data.ais?.length || 0;
            fusedEl.textContent = data.fused?.length || 0;
            
            // 更新雷达显示
            displayEl.innerHTML = '';
            (data.fused || []).forEach(t => {
                const type = t.source_type || 'radar';
                const el = document.createElement('div');
                el.className = `target target-${type}`;
                
                // 坐标转换 (简化)
                const angle = (t.course_deg || 0) * Math.PI / 180;
                const dist = Math.min((t.distance_m || 1000) / 5000, 1);
                const x = 250 + Math.sin(angle) * dist * 220;
                const y = 250 - Math.cos(angle) * dist * 220;
                
                el.style.left = x + 'px';
                el.style.top = y + 'px';
                el.title = `${t.id} - 速度:${t.speed_knots}kn 航向:${t.course_deg}°`;
                displayEl.appendChild(el);
            });
            
            // 更新列表
            listEl.innerHTML = (data.fused || []).map(t => {
                const colors = { radar: 'text-green-400', ais: 'text-blue-400', fused: 'text-yellow-400' };
                const type = t.source_type || 'radar';
                return `
                    <div class="glass p-3 flex justify-between items-center">
                        <div>
                            <div class="font-bold ${colors[type]}">${t.id}</div>
                            <div class="text-sm text-gray-400">${t.name || t.mmsi || '-'}</div>
                        </div>
                        <div class="text-right text-sm">
                            <div>${(t.speed_knots || 0).toFixed(1)} kn</div>
                            <div>${(t.course_deg || 0).toFixed(0)}°</div>
                        </div>
                    </div>
                `;
            }).join('') || '<div class="text-gray-500 text-center">无目标</div>';
        }
        
        function log(msg) {
            const time = new Date().toLocaleTimeString('zh-CN');
            logsEl.innerHTML = `<div>[${time}] ${msg}</div>` + logsEl.innerHTML;
        }
        
        log('页面加载完成');
    </script>
</body>
</html>
'''

# 将此HTML添加到api.py中作为ENHANCED_HTML变量
print("Enhanced UI created")
