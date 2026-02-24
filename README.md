# 舟山定海渔港雷达监控系统 V2.0

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

## 📡 系统简介

用于舟山定海渔港的雷达监控与目标融合系统，支持：

- **雷达目标检测** - Simrad Halo3000 支持
- **AIS船舶识别** - 自动融合
- **多算法跟踪** - KF/EKF/UKF/IMM
- **告警系统** - 速度/距离/区域
- **Web管理界面** - 实时监控

## 🚀 快速开始

```bash
# 克隆项目
git clone https://github.com/ASDFMS1991-sudo/zhoushan-radar-system.git
cd zhoushan-radar-system

# 安装依赖
pip install -r requirements.txt

# 运行（模拟器模式）
python main.py --simulator
```

访问 http://localhost:8081/ui

## 📁 项目结构

```
├── src/               # 源代码
│   ├── radar_parser.py    # 雷达解析
│   ├── ais_parser.py     # AIS解析
│   ├── fusion.py         # 目标融合
│   ├── advanced_tracker.py # 跟踪算法
│   ├── alert.py          # 告警系统
│   └── api.py            # Web API
├── config/            # 配置文件
├── web/              # Web界面(已废弃)
├── tests/            # 单元测试
├── main.py           # 主程序
└── run.py            # 启动脚本
```

## ⚙️ 配置

编辑 `config/config.json`：

```json
{
  "radar": {
    "connection": {
      "ip": "192.168.1.100",
      "port": 2000
    }
  },
  "ais": {
    "connection": {
      "port": "COM3",
      "baudrate": 38400
    }
  }
}
```

## 📊 API接口

| 接口 | 说明 |
|------|------|
| /ui | 监控界面 |
| /settings | 配置界面 |
| /alerts | 告警配置 |
| /tools | 工具页面 |
| /api/targets | 目标数据 |
| /api/logs/export | 导出日志 |

## 🔗 参考项目

- [ais-vessel-tracking](https://github.com/glecdev/ais-vessel-tracking) - 企业级AIS跟踪
- [QAIS](https://github.com/J1SpatialExploration/QAIS) - QGIS AIS可视化
- [indo-pacific-ais-visualizer](https://github.com/ManiBhushan0831/indo-pacific-ais-visualizer) - AIS实时可视化

## 📄 许可证

MIT License

## 👤 作者

- GitHub: [@ASDFMS1991-sudo](https://github.com/ASDFMS1991-sudo)
# 测试
