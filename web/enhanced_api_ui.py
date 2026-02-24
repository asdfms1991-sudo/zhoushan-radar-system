<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>雷达监控系统 V2.0</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.socket.io/4.5.0/socket.io.min.js"></script>
    <style>
        body { background: #0a0a1a; color: #e2e8f0; }
        .glass { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; }
    </style>
</head>
<body>
    <div class="container mx-auto px-4 py-4">
        <!-- 头部 -->
        <header class="flex justify-between items-center mb-4">
            <div>
                <h1 class="text-2xl font-bold text-green-400">舟山定海渔港雷达监控 V2.0</h1>
                <p class="text-gray-500">增强版 - 算法可切换</p>
            </div>
            <div class="flex gap-2">
                <button onclick="switchView('radar')" class="px-3 py-1 bg-green-600 rounded">雷达图</button>
                <button onclick="switchView('map')" class="px-3 py-1 bg-blue-600 rounded">地图</button>
                <button onclick="switchView('debug')" class="px-3 py-1 bg-yellow-600 rounded">调试</button>
                <button onclick="switchView('config')" class="px-3 py-1 bg-purple-600 rounded">配置</button>
            </div>
        </header>
        
        <!-- 统计 -->
        <div class="grid grid-cols-5 gap-3 mb-4">
            <div class="glass p-3">
                <div class="text-gray-400 text-xs">雷达目标</div>
                <div class="text-2xl font-bold text-green-400" id="radarCount">0</div>
            </div>
            <div class="glass p-3">
                <div class="text-gray-400 text-xs">AIS目标</div>
                <div class="text-2xl font-bold text-blue-400" id="aisCount">0</div>
            </div>
            <div class="glass p-3">
                <div class="text-gray-400 text-xs">融合目标</div>
                <div class="text-2xl font-bold text-yellow-400" id="fusedCount">0</div>
            </div>
            <div class="glass p-3">
                <div class="text-gray-400 text-xs">算法</div>
                <div class="text-2xl font-bold text-purple-400" id="currentAlgo">KF</div>
            </div>
            <div class="glass p-3">
                <div class="text-gray-400 text-xs">FPS</div>
                <div class="text-2xl font-bold" id="fpsCount">0</div>
            </div>
        </div>
        
        <!-- 配置面板 -->
        <div id="configPanel" class="hidden mb-4">
            <div class="glass p-4">
                <h3 class="font-bold text-purple-400 mb-3">⚙️ 算法配置</h3>
                
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-gray-400 mb-2">选择算法</label>
                        <select id="algorithmSelect" class="w-full p-2 bg-gray-800 rounded border">
                            <option value="KF">KF (卡尔曼滤波) - 推荐</option>
                            <option value="EKF">EKF (扩展卡尔曼)</option>
                            <option value="UKF">UKF (无迹卡尔曼)</option>
                        </select>
                        <button onclick="changeAlgorithm()" class="mt-2 px-4 py-2 bg-purple-600 rounded">应用</button>
                    </div>
                    
                    <div>
                        <label class="block text-gray-400 mb-2">算法说明</label>
                        <div class="text-sm text-gray-500">
                            <p><span class="text-green-400">KF</span> - 线性最优，稳定性最好</p>
                            <p><span class="text-blue-400">EKF</span> - 适用于非线性场景</p>
                            <p><span class="text-yellow-400">UKF</span> - 精度最高</p>
                        </div>
                    </div>
                </div>
                
                <hr class="my-4 border-gray-700">
                
                <h3 class="font-bold text-purple-400 mb-3">📊 性能监控</h3>
                <div class="grid grid-cols-3 gap-4">
                    <div>
                        <div class="text-gray-400">延迟</div>
                        <div class="text-xl" id="latency">-- ms</div>
                    </div>
                    <div>
                        <div class="text-gray-400">内存</div>
                        <div class="text-xl" id="memory">-- MB</div>
                    </div>
                    <div>
                        <div class="text-gray-400">健康</div>
                        <div class="text-xl text-green-400" id="health">正常</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 主视图 -->
        <div class="grid grid-cols-3 gap-4">
            <div class="col-span-2 glass p-3">
                <div id="radarView">
                    <div style="width:100%;height:450px;background:#000;border-radius:8px;position:relative;">
                        <canvas id="radarCanvas" width="600" height="450"></canvas>
                    </div>
                </div>
                <div id="mapView" class="hidden">
                    <div id="map" style="height:450px;background:#111;border-radius:8px;" class="flex items-center justify-center text-gray-500">
                        地图功能需集成Leaflet
                    </div>
                </div>
                <div id="debugView" class="hidden">
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <h4 class="text-green-400 mb-2">原始数据</h4>
                            <pre id="rawData" class="text-xs bg-black p-2 rounded max-h-80 overflow-auto"></pre>
                        </div>
                        <div>
                            <h4 class="text-yellow-400 mb-2">融合数据</h4>
                            <pre id="fusedData" class="text-xs bg-black p-2 rounded max-h-80 overflow-auto"></pre>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="glass p-3">
                <h3 class="font-bold mb-2">目标列表</h3>
                <div id="targetList" class="space-y-2 max-h-96 overflow-auto"></div>
            </div>
        </div>
    </div>

    <script>
        let currentView = 'radar';
        
        function switchView(view) {
            currentView = view;
            document.getElementById('radarView').classList.toggle('hidden', view !== 'radar');
            document.getElementById('mapView').classList.toggle('hidden', view !== 'map');
            document.getElementById('debugView').classList.toggle('hidden', view !== 'debug');
            document.getElementById('configPanel').classList.toggle('hidden', view !== 'config');
        }
        
        // 获取算法列表
        fetch('/api/algorithms').then(r => r.json()).then(d => {
            document.getElementById('currentAlgo').textContent = d.current;
            document.getElementById('algorithmSelect').value = d.current;
        });
        
        // 切换算法
        function changeAlgorithm() {
            const algo = document.getElementById('algorithmSelect').value;
            fetch('/api/algorithm', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({algorithm: algo})
            }).then(r => r.json()).then(d => {
                if(d.success) {
                    document.getElementById('currentAlgo').textContent = algo;
                    alert('算法已切换: ' + algo);
                }
            });
        }
        
        // WebSocket
        const socket = io();
        
        socket.on('target_update', (data) => {
            // 更新计数
            document.getElementById('radarCount').textContent = data.radar?.length || 0;
            document.getElementById('aisCount').textContent = data.ais?.length || 0;
            document.getElementById('fusedCount').textContent = data.fused?.length || 0;
            
            // 更新目标列表
            const list = document.getElementById('targetList');
            list.innerHTML = (data.fused || []).map(t => 
                `<div class="glass p-2 flex justify-between">
                    <div><span class="font-bold text-green-400">${t.id}</span></div>
                    <div class="text-sm">${(t.speed_knots||0).toFixed(1)}kn</div>
                </div>`
            ).join('') || '<div class="text-gray-500">无目标</div>';
            
            // 更新调试数据
            document.getElementById('rawData').textContent = JSON.stringify({radar:data.radar,ais:data.ais}, null, 2);
            document.getElementById('fusedData').textContent = JSON.stringify(data.fused, null, 2);
        });
        
        // 性能监控
        setInterval(() => {
            fetch('/api/performance').then(r=>r.json()).then(d => {
                document.getElementById('latency').textContent = d.stats.avg_latency_ms.toFixed(1) + ' ms';
                document.getElementById('memory').textContent = d.stats.memory_mb.toFixed(0) + ' MB';
                document.getElementById('fpsCount').textContent = d.stats.fps.toFixed(0);
            });
        }, 2000);
        
        // 初始加载
        fetch('/api/targets').then(r=>r.json()).then(d => {
            document.getElementById('radarCount').textContent = d.stats?.radar_targets || 0;
            document.getElementById('aisCount').textContent = d.stats?.ais_targets || 0;
            document.getElementById('fusedCount').textContent = d.stats?.fused_targets || 0;
        });
    </script>
</body>
</html>
