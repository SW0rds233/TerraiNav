# 数据库集成部署指南

## 概述

本项目现已集成Railway PostgreSQL数据库，实现以下功能：
1. 用户登录和注册（通过数据库验证）
2. 历史记录管理（保存和查询用户的分析任务）
3. 主页面"最近任务"功能（从数据库加载）

## 数据库表结构

### users 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键，自增 |
| username | String(50) | 用户名，唯一 |
| email | String(100) | 邮箱，唯一 |
| password_hash | String(255) | 密码哈希值 |
| usertype | String(20) | 用户类型（user/admin） |
| created_at | DateTime | 创建时间 |

### history 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键，自增 |
| user_id | Integer | 外键，关联users表 |
| task_name | String(200) | 任务名称 |
| input_image_url | Text | 输入图像URL |
| output_route_url | Text | 输出路线图URL |
| route_data | Text | 巡逻路线数据（JSON字符串） |
| created_at | DateTime | 创建时间 |

## 后端配置

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

新增的依赖：
- `psycopg2-binary`: PostgreSQL数据库驱动
- `sqlalchemy`: ORM框架
- `werkzeug`: 密码哈希工具

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# 阿里云百炼接口密钥
DASHSCOPE_API_KEY=your-dashscope-api-key

# Flask 运行端口
PORT=5000

# Railway PostgreSQL 数据库配置
DATABASE_URL=postgresql://username:password@host:port/database_name
# 示例: postgresql://postgres:password@containers-us-west-xxx.railway.app:5432/railway
```

**获取 Railway 数据库 URL：**
1. 登录 Railway 控制台
2. 进入你的项目
3. 点击 PostgreSQL 服务
4. 在 Variables 标签页找到 `DATABASE_URL`
5. 复制该URL到 `.env` 文件

### 3. 初始化数据库

首次运行时，数据库表会自动创建。如果需要手动初始化：

```python
from database import init_db
init_db()
```

### 4. 启动后端服务

```bash
python api.py
```

服务将在 `http://localhost:5000` 启动

## 前端配置

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# API基础URL
VITE_API_BASE_URL=http://localhost:5000
```

如果后端部署在 Railway，修改为：

```env
VITE_API_BASE_URL=https://your-backend.railway.app
```

### 3. 启动前端开发服务器

```bash
npm run dev
```

前端将在 `http://localhost:5173` 启动

## API 接口说明

### 用户认证

#### 1. 用户登录
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password"
}
```

响应：
```json
{
  "success": true,
  "message": "登录成功",
  "token": "xxx",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "usertype": "admin"
  }
}
```

#### 2. 用户注册
```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "password123"
}
```

响应：
```json
{
  "success": true,
  "message": "注册成功",
  "user": {
    "id": 2,
    "username": "newuser",
    "email": "newuser@example.com",
    "usertype": "user"
  }
}
```

### 历史记录

#### 1. 获取用户历史记录
```http
GET /api/history?user_id=1&limit=20
```

响应：
```json
{
  "success": true,
  "histories": [
    {
      "id": 1,
      "user_id": 1,
      "task_name": "山区地形分析",
      "input_image_url": "http://...",
      "output_route_url": "http://...",
      "route_data": "{\"patrol_points\": [...]}",
      "created_at": "2026-05-12T10:30:00"
    }
  ],
  "count": 1
}
```

#### 2. 获取最近历史记录（首页展示）
```http
GET /api/history/recent?user_id=1&limit=5
```

#### 3. 创建历史记录
```http
POST /api/history
Content-Type: application/json

{
  "user_id": 1,
  "task_name": "地形分析任务",
  "input_image_url": "http://...",
  "output_route_url": "http://...",
  "route_data": "{\"patrol_points\": [...]}"
}
```

#### 4. 获取历史记录详情
```http
GET /api/history/1
```

#### 5. 删除历史记录
```http
DELETE /api/history/1
```

## 部署到 Railway

### 后端部署

1. 在 Railway 创建新项目
2. 选择从 GitHub 部署
3. 设置环境变量：
   - `DASHSCOPE_API_KEY`: 你的阿里云百炼API密钥
   - `DATABASE_URL`: Railway PostgreSQL 数据库URL
4. Railway 会自动检测 `requirements.txt` 并安装依赖
5. 创建 `Procfile`（如果不存在）：
   ```
   web: python api.py
   ```
6. 部署完成后，Railway 会提供一个URL

### 前端部署

1. 在 Railway 或 Vercel 创建新项目
2. 设置环境变量：
   - `VITE_API_BASE_URL`: 你的后端Railway URL
3. 部署完成后，前端会自动连接到后端API

## 测试

### 1. 测试用户注册

1. 访问 `http://localhost:5173/login`
2. 点击"没有账户？注册"
3. 填写用户名、邮箱、密码
4. 点击"注册"
5. 检查数据库 `users` 表是否有新记录

### 2. 测试用户登录

1. 使用注册的账号登录
2. 检查是否能成功跳转到仪表板
3. 检查 `localStorage` 是否保存了 token

### 3. 测试历史记录

1. 登录后，上传地图并进行分析
2. 分析完成后，检查数据库 `history` 表是否有新记录
3. 进入"历史记录"页面，检查是否能看到刚才的任务
4. 检查主页面的"最近任务"板块是否更新

### 4. 测试最近任务

1. 刷新主页面
2. 检查"最近任务"板块是否显示最近的分析任务
3. 点击"刷新"按钮，检查是否能重新加载

## 常见问题

### 1. 数据库连接失败

**错误信息**：`could not connect to server`

**解决方案**：
- 检查 `.env` 中的 `DATABASE_URL` 是否正确
- 确认 Railway PostgreSQL 服务是否正在运行
- 检查防火墙设置

### 2. 登录失败

**错误信息**：`用户名或密码错误`

**解决方案**：
- 检查数据库中是否存在该用户
- 确认密码是否正确
- 检查 `password_hash` 是否正确生成

### 3. 历史记录不显示

**错误信息**：无错误，但历史记录为空

**解决方案**：
- 确认用户已登录
- 检查 `user_id` 是否正确传递
- 查看浏览器控制台是否有错误信息

### 4. CORS 错误

**错误信息**：`Access-Control-Allow-Origin`

**解决方案**：
- 确认后端已正确配置 CORS
- 检查 `api.py` 中的 CORS 配置

## 安全建议

1. **密码安全**：
   - 使用强密码（至少6个字符）
   - 密码已使用 `werkzeug` 进行哈希存储

2. **API 密钥**：
   - 不要将 API 密钥提交到 Git
   - 使用环境变量管理敏感信息

3. **数据库安全**：
   - Railway 提供的数据库URL包含密码，请妥善保管
   - 定期备份数据库

4. **Token 管理**：
   - 当前实现使用简单token，生产环境建议使用JWT
   - Token 保存在 `localStorage`，注意XSS攻击

## 后续优化建议

1. **使用 JWT**：
   - 替换当前的简单token
   - 实现token过期和刷新机制

2. **添加权限控制**：
   - 区分普通用户和管理员
   - 限制某些功能仅管理员可用

3. **添加日志记录**：
   - 记录用户操作
   - 记录API调用

4. **添加数据验证**：
   - 验证输入数据的格式
   - 防止SQL注入

5. **添加单元测试**：
   - 测试数据库操作
   - 测试API接口

## 联系方式

如有问题，请联系：2698889584@qq.com