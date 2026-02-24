<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>舟山定海渔港雷达监控系统 V2.0</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://cdn.socket.io/4.5.0/socket.io.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #0a0a1a; color: #e2e8f0; font-family: 'Segoe UI', system-ui, sans-serif; }
        #map { height: 500px; width: 100%; border-radius: 8px; }
        .glass { background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; }
        .target-marker { border-radius: 50%; border: 2px solid white; }
    </style>
</head>
<body>
    <div class="container mx-auto px-4 py-4">
        <!-- 头部 -->
        <header class="flex justify-between items-center mb-4">
            <div>
                <h1 class="text-2xl font-bold text-green-400">舟山定海渔港雷达监控</h1>
                <p class="text-gray-500">V2.0 - 地图版</p>
            </div>
            <div class="flex gap-2">
                <button onclick="switchView('radar')" class="px-4 py-2 bg-green-600 rounded hover:bg-green-700">雷达图</button>
                <button onclick="switchView('map')" class="px-4 py-2 bg-blue-600 rounded hover:bg-blue-700">地图</button>
            </div>
        </header>
        
        <!-- 统计 -->
        <div class="grid grid-cols-4 gap-3 mb-4">
            <div class="glass p-3 border-l-4 border-green-500">
                <div class="text-gray-400 text-sm">雷达目标</div>
                <div class="text-2xl font-bold text-green-400" id="radarCount">0</div>
            </div>
            <div class="glass p-3 border-l-4 border-blue-500">
                <div class="text-gray-400 text-sm">AIS目标</div>
                <div class="text-2xl font-bold text-blue-400" id="aisCount">0</div>
            </div>
            <div class="glass p-3 border-l-4 border-yellow-500">
                <div class="text-gray-400 text-sm">融合目标</div>
                <div class="text-2xl font-bold text-yellow-400" id="fusedCount">0</div>
            </div>
            <div class="glass p-3 border-l-4 border-purple-500">
                <div class="text-gray-400 text-sm">在线状态</div>
                <div class="text-2xl font-bold text-purple-400" id="status">--</div>
            </div>
        </div>
        
        <!-- 主视图 -->
        <div class="grid grid-cols-3 gap-4">
            <!-- 地图/雷达视图 -->
            <div class="col-span-2 glass p-3">
                <div id="radarView" class="relative">
                    <div id="radarContainer" style="width:100%;height:500px;background:#000;border-radius:8px;position:relative;">
                        <!-- 雷达图Placeholder -->
                        <div id="radarDisplay" style="width:100%;height:100%;position:relative;"></div>
                    </div>
                </div>
                <div id="mapView" class="hidden">
                    <div id="map"></div>
                </div>
            </div>
            
            <!-- 目标列表 -->
            <div class="glass p-3">
                <h3 class="font-bold mb-2">目标列表</h3>
                <div id="targetList" class="space-y-2 max-h-[450px] overflow-auto">
                    <div class="text-gray-500 text-center py-4">等待数据...</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // 初始化地图
        const center = [30.017, 122.107]; // 舟山定海
        const map = L.map('map').setView(center, 13);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap'
        }).addTo(map);
        
        // 标记物
        const markers = {};
        let currentView = 'radar';
        
        function switchView(view) {
            currentView = view;
            document.getElementById('radarView').classList.toggle('hidden', view !== 'radar');
            document.getElementById('mapView').classList.toggle('hidden', view !== 'map');
            if (view === 'map') setTimeout(() => map.invalidateSize(), 100);
        }
        
        // WebSocket连接
        const socket = io();
        
        socket.on('connect', () => {
            document.getElementById('status').textContent = '在线';
            document.getElementById('status').className = 'text-2xl font-bold text-green-400';
        });
        
        socket.on('disconnect', () => {
            document.getElementById('status').textContent = '离线';
            document.getElementById('status').className = 'text-2xl font-bold text-red-400';
        });
        
        socket.on('target_update', (data) => {
            updateDisplay(data);
        });
        
        function updateDisplay(data) {
            // 更新计数
            document.getElementById('radarCount').textContent = data.radar?.length || 0;
            document.getElementById('aisCount').textContent = data.ais?.length || 0;
            document.getElementById('fusedCount').textContent = data.fused?.length || 0;
            
            // 更新地图标记
            if (currentView === 'map') {
                updateMarkers(data.fused || []);
            }
            
            // 更新目标列表
            updateList(data.fused || []);
        }
        
        function updateMarkers(targets) {
            // 清除旧标记
            Object.values(markers).forEach(m => map.removeLayer(m));
            
            // 添加新标记
            targets.forEach(t => {
                const color = t.source_type === 'radar' ? '#22c55e' : 
                            t.source_type === 'ais' ? '#3b82f6' : '#f59e0b';
                
                const marker = L.circleMarker([t.lat, t.lon], {
                    radius: 8,
                    fillColor: color,
                    color: '#fff',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.8
                }).addTo(map);
                
                marker.bindPopup(`
                    <b>${t.id}</b><br>
                    速度: ${t.speed_knots?.toFixed(1)} kn<br>
                    航向: ${t.course_deg?.toFixed(0)}°
                `);
                
                markers[t.id] = marker;
            });
        }
        
        function updateList(targets) {
            const list = document.getElementById('targetList');
            if (!targets.length) {
                list.innerHTML = '<div class="text-gray-500 text-center py-4">无目标</div>';
                return;
            }
            
            list.innerHTML = targets.map(t => {
                const color = t.source_type === 'radar' ? 'text-green-400' : 
                            t.source_type === 'ais' ? 'text-blue-400' : 'text-yellow-400';
                return `
                    <div class="glass p-2 flex justify-between items-center">
                        <div>
                            <div class="font-bold ${color}">${t.id}</div>
                            <div class="text-xs text-gray-500">${t.name || '-'}</div>
                        </div>
                        <div class="text-right text-sm">
                            <div>${t.speed_knots?.toFixed(1)} kn</div>
                            <div>${t.course_deg?.toFixed(0)}°</div>
                        </div>
                    </div>
                `;
            }).join('');
        }
        
        // 初始加载
        fetch('/api/targets').then(r => r.json()).then(updateDisplay);
    </script>
</body>
</html>
