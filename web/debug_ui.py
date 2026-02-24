<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>雷达系统调试工具</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.socket.io/4.5.0/socket.io.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #0a0a1a; color: #e2e8f0; font-family: 'Consolas', monospace; }
        .json-view { background: #1e1e1e; padding: 10px; border-radius: 4px; max-height: 300px; overflow: auto; }
        .json-key { color: #9cdcfe; }
        .json-string { color: #ce9178; }
        .json-number { color: #b5cea8; }
        .json-boolean { color: #569cd6; }
    </style>
</head>
<body class="p-4">
    <div class="max-w-7xl mx-auto">
        <!-- 头部 -->
        <header class="mb-4 flex justify-between items-center">
            <div>
                <h1 class="text-2xl font-bold text-yellow-400">🔧 雷达系统调试工具</h1>
                <p class="text-gray-500">实时数据监控</p>
            </div>
            <div class="flex gap-2">
                <button onclick="clearLog()" class="px-3 py-1 bg-red-600 rounded">清空</button>
                <button onclick="togglePause()" id="pauseBtn" class="px-3 py-1 bg-yellow-600 rounded">暂停</button>
            </div>
        </header>
        
        <!-- 状态 -->
        <div class="grid grid-cols-5 gap-3 mb-4">
            <div class="glass p-3">
                <div class="text-gray-400 text-xs">连接状态</div>
                <div id="connectionStatus" class="text-lg font-bold text-gray">--</div>
            </div>
            <div class="glass p-3">
                <div class="text-gray-400 text-xs">消息数</div>
                <div id="msgCount" class="text-lg font-bold text-green-400">0</div>
            </div>
            <div class="glass p-3">
                <div class="text-gray-400 text-xs">雷达目标</div>
                <div id="radarCount" class="text-lg font-bold text-green-400">0</div>
            </div>
            <div class="glass p-3">
                <div class="text-gray-400 text-xs">AIS目标</div>
                <div id="aisCount" class="text-lg font-bold text-blue-400">0</div>
            </div>
            <div class="glass p-3">
                <div class="text-gray-400 text-xs">融合目标</div>
                <div id="fusedCount" class="text-lg font-bold text-yellow-400">0</div>
            </div>
        </div>
        
        <!-- 实时数据 -->
        <div class="grid grid-cols-2 gap-4">
            <!-- 原始数据 -->
            <div class="glass p-3">
                <h3 class="font-bold text-green-400 mb-2">📡 原始数据 (最新)</h3>
                <div id="rawData" class="json-view text-sm"></div>
            </div>
            
            <!-- 融合数据 -->
            <div class="glass p-3">
                <h3 class="font-bold text-yellow-400 mb-2">🎯 融合数据 (最新)</h3>
                <div id="fusedData" class="json-view text-sm"></div>
            </div>
        </div>
        
        <!-- 消息日志 -->
        <div class="glass p-3 mt-4">
            <h3 class="font-bold text-blue-400 mb-2">📋 消息日志</h3>
            <div id="msgLog" class="text-xs" style="max-height: 200px; overflow: auto;"></div>
        </div>
    </div>

    <script>
        let paused = false;
        let msgCount = 0;
        
        const socket = io();
        
        socket.on('connect', () => {
            document.getElementById('connectionStatus').textContent = '🟢 已连接';
            document.getElementById('connectionStatus').className = 'text-lg font-bold text-green-400';
            log('系统已连接');
        });
        
        socket.on('disconnect', () => {
            document.getElementById('connectionStatus').textContent = '🔴 断开';
            document.getElementById('connectionStatus').className = 'text-lg font-bold text-red-400';
            log('连接断开');
        });
        
        socket.on('target_update', (data) => {
            if (paused) return;
            
            msgCount++;
            document.getElementById('msgCount').textContent = msgCount;
            
            // 更新计数
            document.getElementById('radarCount').textContent = data.radar?.length || 0;
            document.getElementById('aisCount').textContent = data.ais?.length || 0;
            document.getElementById('fusedCount').textContent = data.fused?.length || 0;
            
            // 显示原始数据
            document.getElementById('rawData').innerHTML = formatJSON({
                radar: data.radar,
                ais: data.ais
            });
            
            // 显示融合数据
            document.getElementById('fusedData').innerHTML = formatJSON({
                fused: data.fused,
                stats: data.stats
            });
            
            // 记录日志
            log(`收到更新: 雷达${data.radar?.length||0} AIS${data.ais?.length||0} 融合${data.fused?.length||0}`);
        });
        
        function formatJSON(obj) {
            const json = JSON.stringify(obj, null, 2);
            return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, (match) => {
                let cls = 'json-number';
                if (/^"/.test(match)) {
                    if (/:$/.test(match)) {
                        cls = 'json-key';
                    } else {
                        cls = 'json-string';
                    }
                } else if (/true|false/.test(match)) {
                    cls = 'json-boolean';
                }
                return '<span class="' + cls + '">' + match + '</span>';
            });
        }
        
        function log(msg) {
            const log = document.getElementById('msgLog');
            const time = new Date().toLocaleTimeString();
            log.innerHTML = `<div>[${time}] ${msg}</div>` + log.innerHTML;
            if (log.children.length > 50) log.lastChild.remove();
        }
        
        function togglePause() {
            paused = !paused;
            document.getElementById('pauseBtn').textContent = paused ? '继续' : '暂停';
            log(paused ? '已暂停' : '已继续');
        }
        
        function clearLog() {
            document.getElementById('msgLog').innerHTML = '';
            log('日志已清空');
        }
    </script>
</body>
</html>
