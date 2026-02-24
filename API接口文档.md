# API接口文档

---

## 基础信息

| 项目 | 值 |
|------|-----|
| 基础URL | http://localhost:8081 |
| 协议 | HTTP / WebSocket |

---

## HTTP API

### 1. 获取所有目标

**GET** `/api/targets`

返回雷达、AIS、融合目标

**响应示例：**
```json
{
  "radar": [
    {
      "id": "1",
      "lat": 30.017,
      "lon": 122.107,
      "distance_nm": 1.5,
      "bearing_deg": 45.0,
      "speed_knots": 12.0,
      "course_deg": 90.0,
      "timestamp": "2026-02-24T10:00:00"
    }
  ],
  "ais": [
    {
      "id": "A123456789",
      "mmsi": "123456789",
      "name": "测试船舶1",
      "lat": 30.018,
      "lon": 122.108,
      "speed_knots": 10.0,
      "course_deg": 85.0,
      "timestamp": "2026-02-24T10:00:00"
    }
  ],
  "fused": [
    {
      "id": "F1",
      "lat": 30.017,
      "lon": 122.107,
      "speed_knots": 12.0,
      "course_deg": 90.0,
      "source_type": "radar",
      "has_ais": false,
      "has_radar": true,
      "timestamp": "2026-02-24T10:00:00"
    }
  ],
  "stats": {
    "radar_targets": 1,
    "ais_targets": 1,
    "fused_targets": 1,
    "radar_only": 0,
    "ais_only": 0
  }
}
```

---

### 2. 获取单个目标详情

**GET** `/api/target/{target_id}`

**响应示例：**
```json
{
  "id": "F1",
  "lat": 30.017,
  "lon": 122.107,
  "speed_knots": 12.0,
  "course_deg": 90.0,
  "kalman_lat": 30.0171,
  "kalman_lon": 122.1071,
  "predict_lat": 30.0200,
  "predict_lon": 122.1100,
  "trajectory_points": 50,
  "timestamp": "2026-02-24T10:00:00"
}
```

---

### 3. 获取轨迹

**GET** `/api/trajectory/{target_id}`

**查询参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| last_n | int | 返回最近N个点 |

**响应示例：**
```json
{
  "target_id": "F1",
  "points": [
    {"lat": 30.010, "lon": 122.100, "timestamp": "2026-02-24T09:55:00"},
    {"lat": 30.015, "lon": 122.105, "timestamp": "2026-02-24T09:56:00"}
  ]
}
```

---

### 4. 获取系统状态

**GET** `/api/status`

**响应示例：**
```json
{
  "system": {
    "name": "舟山定海渔港雷达监控系统",
    "version": "2.0.0",
    "uptime_seconds": 3600
  },
  "modules": {
    "radar": "connected",
    "ais": "connected",
    "fusion": "active",
    "storage": "active"
  }
}
```

---

### 5. 获取配置

**GET** `/api/config`

返回当前配置

---

## WebSocket API

### 连接

```
ws://localhost:8081/ws
```

### 消息格式

**订阅目标更新：**

```json
{
  "action": "subscribe",
  "channel": "targets"
}
```

**接收目标数据：**

```json
{
  "type": "target_update",
  "data": {
    "radar": [...],
    "ais": [...],
    "fused": [...]
  }
}
```

---

## 错误码

| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 404 | 目标不存在 |
| 500 | 服务器错误 |

---

## 使用示例

### cURL

```bash
# 获取所有目标
curl http://localhost:8081/api/targets

# 获取单个目标
curl http://localhost:8081/api/target/F1

# 获取轨迹
curl http://localhost:8081/api/trajectory/F1?last_n=10
```

### Python

```python
import requests

# 获取所有目标
response = requests.get('http://localhost:8081/api/targets')
data = response.json()
print(f"雷达目标: {data['stats']['radar_targets']}")
print(f"AIS目标: {data['stats']['ais_targets']}")
print(f"融合目标: {data['stats']['fused_targets']}")
```

---

**版本：V2.0.0**
**更新日期：2026-02-24**
