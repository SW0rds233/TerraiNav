# TerraiNav - 地形适应无人机巡逻系统

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/Vue-3.5-4FC08D.svg)](https://vuejs.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**基于 AI+FAHP+ACO 的智能地形分析、威胁评估与无人机巡逻路径规划系统**

[功能](#核心功能) · [快速开始](#快速开始) · [项目结构](#项目结构) · [技术栈](#技术栈)

</div>

---

## 核心功能

| 功能模块 | 技术方案 | 说明 |
|---------|---------|------|
| 🗺️ **交互式地图** | Leaflet + Esri 卫星影像 | 球面地图选区域、缩放、等高线叠加，自动计算比例尺 |
| 🤖 **AI 地形识别** | 阿里云百炼 Qwen VL | 并行分析地图分块，识别高程/类型/坡度/隐蔽性/通视/威胁等级 |
| 📊 **威胁评估** | FAHP 模糊层次分析法 | 6 因子加权计算威胁分数，生成威胁矩阵 |
| 🛤️ **路径规划** | ACO 蚁群算法 | TSP 求解最优巡逻路线 |
| 🎨 **可视化** | Matplotlib + Leaflet | 热力图 + 巡逻路线图 + 等高线叠加 |
| 👤 **用户系统** | JWT + MySQL/SQLite | 登录注册、历史记录管理 |

---

## 快速开始

### 前置条件

- **Python** 3.8+
- **Node.js** 20+
- **阿里云百炼 API Key**（[申请地址](https://bailian.console.aliyun.com/)）

### 一键启动（推荐）

```bash
# Windows
双击 start.bat

# 或命令行
python start_dev.py
```

脚本自动：检查虚拟环境 → 安装依赖 → 启动后端(5000) + 前端(5173)

### 手动启动

```bash
# 1. 后端
cd backend
pip install -r requirements.txt
python api.py                        # Flask API → http://localhost:5000

# 2. 前端
cd frontend
npm install
npm run dev                          # Vite → http://localhost:5173
```

### 配置 API Key

在 `backend/.env` 中填入：

```env
DASHSCOPE_API_KEY=sk-your-api-key
```

或在前端页面左侧"API 配置"中直接输入。

**默认测试账户**：`admin` / `123456`

---

## 项目结构

```
TerraiNav/
├── start.bat                 # Windows 一键启动
├── start_dev.py              # 开发环境启动脚本（跨平台）
├── backend/
│   ├── api.py                # Flask Web API（REST 端点）
│   ├── agent.py              # AI 地形分析器（阿里云百炼）
│   ├── assess.py             # FAHP 威胁评估器
│   ├── path.py               # ACO 路径规划 + 可视化
│   ├── database.py           # SQLAlchemy 数据库层
│   ├── models.py             # ORM 模型
│   ├── requirements.txt      # Python 依赖
│   ├── .env.example          # 环境变量模板
│   ├── uploads/              # 用户上传图片
│   └── static/output/        # 生成的热力图/路线图
├── frontend/
│   ├── src/
│   │   ├── components/dashboard/
│   │   │   ├── MapAnalysis.vue      # 地图分析主页面
│   │   │   ├── MapSelector.vue      # Leaflet 交互地图组件
│   │   │   ├── MapControls.vue      # 左侧参数控制面板
│   │   │   ├── MapResultPanel.vue   # 结果统计 + 威胁点表格
│   │   │   ├── History.vue          # 历史记录
│   │   │   ├── Settings.vue         # 系统设置
│   │   │   └── Tutorial.vue         # 使用教程
│   │   ├── stores/                  # Pinia 状态管理
│   │   ├── router/                  # Vue Router
│   │   └── views/                   # 页面视图
│   ├── package.json
│   └── vite.config.ts
└── verify_satellite.py       # 卫星瓦片分析质量验证脚本（素材与源码目录）
```

---

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/init` | POST | 初始化 AI 分析器（API Key） |
| `/api/analyze_map_region` | POST | 通过经纬度边界启动分析（无需上传文件） |
| `/api/task_status/<id>` | GET | 轮询后台任务状态与结果 |
| `/api/map_overlay` | POST | 生成等高线叠加图 |
| `/api/tile/<source>/<z>/<x>/<y>.png` | GET | 瓦片服务（卫星/等高线） |
| `/api/auth/login` | POST | 用户登录 |
| `/api/auth/register` | POST | 用户注册 |
| `/api/history` | GET/POST/DELETE | 历史记录管理 |
| `/api/health` | GET | 健康检查 |

---

## 技术栈

| 层次 | 技术 |
|------|------|
| 前端 | Vue 3 + TypeScript + Vite + Pinia + Leaflet |
| 后端 | Flask + SQLAlchemy + Gunicorn |
| AI | 阿里云百炼 DashScope (Qwen VL) |
| 算法 | FAHP + ACO 蚁群 |
| 可视化 | Matplotlib + Leaflet |
| 数据库 | MySQL (Railway) / SQLite (本地) |
| 部署 | Railway + Vercel |

---

## 工作流程

```
用户在地图上选择区域 → 自动计算比例尺
  → 后端下载/拼接卫星瓦片（或构造等高线图）
  → AI 并行分析每块地形（Qwen VL）
  → FAHP 威胁评估（6因子权重）
  → ACO 蚁群路径规划（TSP）
  → 生成热力图 + 巡逻路线 → 返回前端展示
```

---

## 数据来源与版权

- 卫星影像：© Esri, Maxar, Earthstar Geographics
- 高程数据：Open-Meteo Elevation API (Copernicus DEM)
- 本项目仅用于学术研究与教育目的

---

## 联系方式

📧 2698889584@qq.com