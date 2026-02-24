<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>舟山定海渔港雷达监控系统 V2.1</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://cdn.socket.io/4.5.0/socket.io.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #0a0a1a; color: #e2e8f0; font-family: 'Segoe UI', system-ui, sans-serif; }
        .glass { background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; }
        .alert-critical { border-left: 4px solid #ef4444; background: rgba(239,68,68,0.1); }
        .alert-warning { border-left: 4px solid #f59e0b; background: rgba(245,158,11,0.1); }
        .alert-info { border-left: 4px solid #3b82f6; background: rgba(59,130,246,0.1); }
    </style>
</head>
<body>
    <div class="container mx-auto px-4 py-4">
        <!-- 头部 -->
        <header class="flex justify-between items-center mb-4">
            <div>
                <h1 class="text-2xl font-bold text-green-400">舟山定海渔港雷达监控 V2.1</h1>
                <p class="text-gray-500">增强版 - 含告警/分类/回放</p>
            </div>
            <div class="flex gap-2">
                <button onclick="switchView('radar')" class="px-3 py-1 bg-green-600 rounded hover:bg-green-700 text-sm">雷达</button>
                <button onclick="switchView('map')" class="px-3 py-1 bg-blue-600 rounded hover:bg-blue-700 text-sm">地图</button>
                <button onclick="switchView('alerts')" class="px-3 py-1 bg-red-600 rounded hover:bg-red-700 text-sm">告警 <span id="alertCount" class="bg-white text-red-600 px-1 rounded text-xs">0</span></button>
            </div>
        </header>
        
        <!-- 统计 -->
        <div class="grid grid-cols-6 gap-3 mb-4">
            <div class="glass p-2 border-l-4 border-green-500">
                <div class="text-gray-400 text-xs">雷达</div>
                <div class="text-xl font-bold text-green-400" id="radarCount">0</div>
            </div>
            <div class="glass p-2 border-l-4 border-blue-500">
                <div class="text-gray-400 text-xs">AIS</div>
                <div class="text-xl font-bold text-blue-400" id="aisCount">0</div>
            </div>
            <div class="glass p-2 border-l-4 border-yellow-500">
                <div class="text-gray-400 text-xs">融合</div>
                <div class="text-xl font-bold text-yellow-400" id="fusedCount">0</div>
            </div>
            <div class="glass p-2 border-l-4 border-red-500">
                <div class="text-gray-400 text-xs">告警</div>
                <div class="text-xl font-bold text-red-400" id="criticalCount">0</div>
            </div>
            <div class="glass p-2 border-l-4 border-purple-500">
                <div class="text-gray-400 text-xs">FPS</div>
                <div class="text-xl font-bold text-purple-400" id="fpsCount">0</div>
            </div>
            <div class="glass p-2 border-l-4 border-gray-500">
                <div class="text-gray-400 text-xs">状态</div>
                <div class="text-xl font-bold" id="status">--</div>
            </div>
        </div>
        
        <!-- 主视图 -->
        <div class="grid grid-cols-3 gap-4">
            <!-- 地图 -->
            <div class="col-span-2 glass p-3">
                <div id="radarView" class="relative">
                    <div id="radarContainer" style="width:100%;height:450px;background:#000;border-radius:8px;"></div>
                </div>
                <div id="mapView" class="hidden">
                    <div id="map" style="height:450px;border-radius:8px;"></div>
                </div>
            </div>
            
            <!-- 右侧面板 -->
            <div class="space-y-3">
                <!-- 告警列表 -->
                <div id="alertPanel" class="glass p-3 hidden">
                    <h3 class="font-bold text-red-400 mb-2">🚨 告警</h3>
                    <div id="alertList" class="space-y-2 max-h-[200px] overflow-auto"></div>
                </div>
                
                <!-- 目标列表 -->
                <div class="glass p-3">
                    <h3 class="font-bold mb-2">🎯 目标列表</h3>
                    <div id="targetList" class="space-y-2 max-h-[380px] overflow-auto"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // 初始化地图
        const map = L.map('map').setView([30.017, 122.107], 13);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
        
        let markers = {};
        let alerts = [];
        let currentView = 'radar';
        
        function switchView(view) {
            currentView = view;
            document.getElementById('radarView').classList.toggle('hidden', view !== 'radar');
            document.getElementById('mapView').classList.toggle('hidden', view !== 'map');
            document.getElementById('alertPanel').classList.toggle('hidden', view !== 'alerts');
            if (view === 'map') setTimeout(() => map.invalidateSize(), 100);
        }
        
        const socket = io();
        
        socket.on('connect', () => {
            document.getElementById('status').textContent = '🟢';
            document.getElementById('status').className = 'text-xl font-bold text-green-400';
        });
        
        socket.on('disconnect', () => {
            document.getElementById('status').textContent = '🔴';
            document.getElementById('status').className = 'text-xl font-bold text-red-400';
        });
        
        socket.on('target_update', updateDisplay);
        
        function updateDisplay(data) {
            document.getElementById('radarCount').textContent = data.radar?.length || 0;
            document.getElementById('aisCount').textContent = data.ais?.length || 0;
            document.getElementById('fusedCount').textContent = data.fused?.length || 0;
            
            if (currentView === 'map') {
                updateMarkers(data.fused || []);
            }
            
            updateList(data.fused || []);
        }
        
        function updateMarkers(targets) {
            Object.values(markers).forEach(m => map.removeLayer(m));
            
            targets.forEach(t => {
                const colors = { radar: '#22c55e', ais: '#3b82f6', fused: '#f59e0b' };
                const color = colors[t.source_type] || '#fff';
                
                const marker = L.circleMarker([t.lat, t.lon], {
                    radius: 8, fillColor: color, color: '#fff', weight: 2
                }).addTo(map);
                
                marker.bindPopup(`<b>${t.id}</b><br>${t.speed_knots?.toFixed(1)}kn<br>${t.course_deg?.toFixed(0)}°`);
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
                const colors = { radar: 'text-green-400', ais: 'text-blue-400', fused: 'text-yellow-400' };
                const color = colors[t.source_type] || 'text-gray-400';
                const shipType = t.ship_type || '-';
                return `
                    <div class="glass p-2 flex justify-between items-center">
                        <div>
                            <div class="font-bold ${color}">${t.id}</div>
                            <div class="text-xs text-gray-500">${shipType}</div>
                        </div>
                        <div class="text-right text-sm">
                            <div>${t.speed_knots?.toFixed(1)} kn</div>
                            <div>${t.course_deg?.toFixed(0)}°</div>
                        </div>
                    </div>
                `;
            }).join('');
        }
        
        fetch('/api/targets').then(r => r.json()).then(updateDisplay);
    </script>
</body>
</html>
