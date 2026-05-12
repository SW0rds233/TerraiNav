# Railway MySQL 数据库配置指南

## 概述

本项目使用 MySQL 数据库，部署在 Railway 平台上。Railway 提供了两种网络连接方式：

### 1. Private Networking (推荐)
- **地址**: `mysql.railway.internal:3306`
- **用途**: Railway 内部服务之间的连接
- **优点**: 
  - ✅ 更快（低延迟）
  - ✅ 更安全（不暴露到公网）
  - ✅ 免费（内部通信不产生额外费用）
  - ✅ 更稳定

### 2. Public Networking
- **地址**: `yamabiko.proxy.rlwy.net:17973`
- **用途**: 从外部工具连接数据库
- **适用场景**:
  - 本地开发环境连接远程数据库
  - 使用 MySQL Workbench、Navicat 等工具管理数据库
  - 调试和测试

## 配置步骤

### 在 Railway 中配置环境变量

1. 登录 Railway 控制台
2. 选择你的后端服务
3. 点击 "Variables" 标签
4. 添加以下环境变量：

```bash
# 生产环境（使用私有网络）
DATABASE_URL=mysql+pymysql://username:password@mysql.railway.internal:3306/database_name

# 或者从 Railway 数据库服务获取完整的连接字符串
# Railway 会自动提供正确的 DATABASE_URL
```

### 获取 Railway 数据库连接信息

1. 在 Railway 中选择你的 MySQL 数据库服务
2. 点击 "Connect" 按钮
3. 复制提供的连接字符串
4. 格式通常为：
   ```
   mysql://root:password@mysql.railway.internal:3306/railway
   ```

### 本地开发环境配置

如果需要在本地开发时连接到 Railway 的 MySQL 数据库：

1. 创建或编辑 `backend/.env` 文件：
   ```bash
   # 使用公网地址（仅用于本地开发）
   DATABASE_URL=mysql+pymysql://username:password@yamabiko.proxy.rlwy.net:17973/database_name
   ```

2. 或者使用本地 SQLite 数据库（推荐用于本地开发）：
   ```bash
   # 不设置 DATABASE_URL，会自动使用 SQLite
   # DATABASE_URL=
   ```

## DATABASE_URL 格式说明

### MySQL 格式（推荐）
```
mysql+pymysql://username:password@host:port/database_name
```

### 参数说明
- `username`: 数据库用户名
- `password`: 数据库密码
- `host`: 数据库主机地址
  - 生产环境: `mysql.railway.internal`
  - 本地开发（公网）: `yamabiko.proxy.rlwy.net:17973`
- `port`: 数据库端口（MySQL 默认 3306）
- `database_name`: 数据库名称

### 示例

#### 生产环境（Railway 内部）
```bash
DATABASE_URL=mysql+pymysql://root:abc123@mysql.railway.internal:3306/railway
```

#### 本地开发（连接 Railway 公网）
```bash
DATABASE_URL=mysql+pymysql://root:abc123@yamabiko.proxy.rlwy.net:17973/railway
```

#### 本地开发（使用 SQLite）
```bash
# 不设置或注释掉 DATABASE_URL
# DATABASE_URL=
```

## 代码已自动处理

项目代码已经包含以下自动处理逻辑：

1. **自动添加 pymysql 驱动**
   ```python
   if DATABASE_URL.startswith("mysql://"):
       DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)
   ```

2. **自动降级到 SQLite**
   如果无法连接到远程数据库，会自动使用本地 SQLite：
   ```python
   try:
       # 尝试连接远程数据库
       engine = create_engine(DATABASE_URL, ...)
   except Exception:
       # 降级到 SQLite
       DATABASE_URL = "sqlite:///terrainav.db"
       engine = create_engine(DATABASE_URL, ...)
   ```

3. **详细的日志输出**
   - 显示数据库类型和驱动
   - 显示连接状态
   - 隐藏密码信息

## 验证配置

### 方法 1: 使用诊断脚本

```bash
cd backend
python test_db.py
```

### 方法 2: 查看 Railway 日志

在 Railway 控制台查看后端服务日志，应该看到：

```
INFO - 使用数据库: mysql.railway.internal:3306/railway
INFO - 检测到MySQL数据库，使用pymysql驱动
INFO - 数据库连接测试成功
INFO - 数据库表创建成功
```

### 方法 3: 测试 API

```bash
# 测试注册
curl -X POST https://your-app.railway.app/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "test123456"
  }'

# 测试登录
curl -X POST https://your-app.railway.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "test123456"
  }'
```

## 常见问题

### Q1: 连接超时
**原因**: 可能使用了错误的网络地址
**解决**: 
- 生产环境使用 `mysql.railway.internal:3306`
- 本地开发使用 `yamabiko.proxy.rlwy.net:17973`

### Q2: 认证失败
**原因**: 用户名或密码错误
**解决**: 
- 在 Railway 数据库服务中重新生成连接字符串
- 确保使用最新的密码

### Q3: 表不存在
**原因**: 数据库未初始化
**解决**: 
- 首次启动会自动创建表
- 检查日志中的 "数据库表创建成功" 消息

### Q4: 性能问题
**原因**: 使用了公网地址
**解决**: 
- 生产环境务必使用私有网络 `mysql.railway.internal`
- 公网地址仅用于本地开发

## 安全建议

1. **永远不要在代码中硬编码数据库凭据**
2. **使用 Railway 的环境变量存储敏感信息**
3. **定期更换数据库密码**
4. **限制公网访问，仅使用私有网络**
5. **启用 SSL 连接（如果需要）**

## 部署检查清单

- [ ] 在 Railway 后端服务中设置了 `DATABASE_URL` 环境变量
- [ ] 使用私有网络地址 `mysql.railway.internal:3306`
- [ ] 确认 `requirements.txt` 包含 `pymysql>=1.0.0`
- [ ] 查看日志确认数据库连接成功
- [ ] 测试用户注册和登录功能
- [ ] 验证数据正确存储在 MySQL 数据库中

## 技术支持

如果遇到问题，请提供以下信息：

1. Railway 日志中的错误信息
2. `DATABASE_URL` 的格式（隐藏密码）
3. 使用的网络地址（私有/公网）
4. 诊断脚本的输出结果

---

**最后更新**: 2025-05-12
**适用版本**: v1.0.0+