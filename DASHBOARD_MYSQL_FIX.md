# Dashboard MySQL连接问题修复指南

## 问题描述

运行 `python start_dashboard.py` 后，Dashboard显示错误：
- **错误**: `Database connection failed: Unsupported database type for sync engine: json`
- **原因**: `config/base_config.py` 中 `SAVE_DATA_OPTION = "json"`，但数据存储在MySQL数据库中

## 解决方案

### 步骤1：修改配置文件 ✅

已修改 `MediaCrawler/config/base_config.py`：

```python
# 第65-66行
SAVE_DATA_OPTION = "db"  # 改为 "db" 表示使用MySQL数据库
```

### 步骤2：检查MySQL连接配置

确认 `MediaCrawler/config/db_config.py` 中的MySQL配置正确：

```python
MYSQL_DB_PWD = "123456"      # 你的MySQL密码
MYSQL_DB_USER = "root"       # 你的MySQL用户名
MYSQL_DB_HOST = "localhost"  # MySQL主机地址
MYSQL_DB_PORT = 3306         # MySQL端口
MYSQL_DB_NAME = "pachong"    # 数据库名称
```

### 步骤3：检查MySQL数据库是否有数据

运行检查脚本：

```bash
python check_mysql_data.py
```

或者手动检查：

```bash
mysql -u root -p123456 -e "USE pachong; SELECT COUNT(*) FROM bilibili_video;"
```

### 步骤4：安装pymysql（如果未安装）

Dashboard连接MySQL需要pymysql驱动：

```bash
pip install pymysql
```

### 步骤5：重启Dashboard

修改配置后，重启Dashboard：

```bash
# 停止当前Dashboard（按Ctrl+C）
# 然后重新启动
python start_dashboard.py
```

## 验证步骤

### 1. 检查配置文件

确认 `config/base_config.py` 中：
```python
SAVE_DATA_OPTION = "db"  # 必须是 "db" 或 "mysql"，不能是 "json"
```

### 2. 检查MySQL连接

运行检查脚本：
```bash
python check_mysql_data.py
```

应该看到：
- ✓ pymysql已安装
- ✓ MySQL连接成功
- ✓ 数据库中有表和数据

### 3. 检查数据库表

确认以下表存在且有数据：
- `bilibili_video` - 视频数据
- `bilibili_video_comment` - 评论数据
- `bilibili_up_info` - 创作者数据

## 常见问题

### 问题1：仍然显示 "Unsupported database type"

**原因**: 配置文件未正确修改或Dashboard缓存

**解决**:
1. 确认 `config/base_config.py` 中 `SAVE_DATA_OPTION = "db"`
2. 重启Dashboard（完全停止后重新启动）
3. 清除Streamlit缓存（如果问题持续）

### 问题2：MySQL连接失败

**错误信息**: `Can't connect to MySQL server`

**解决**:
1. 检查MySQL服务是否运行
2. 检查连接配置（主机、端口、用户名、密码）
3. 测试MySQL连接：
   ```bash
   mysql -u root -p123456 -h localhost -P 3306
   ```

### 问题3：数据库不存在

**错误信息**: `Unknown database 'pachong'`

**解决**:
1. 创建数据库：
   ```bash
   mysql -u root -p123456 -e "CREATE DATABASE IF NOT EXISTS pachong;"
   ```
2. 初始化数据库表：
   ```bash
   python main.py --init-db mysql
   ```
3. 同步数据：
   ```bash
   python sync_bilibili_data.py --db-type db
   ```

### 问题4：表中没有数据

**原因**: 数据未同步到MySQL

**解决**:
1. 确认JSON文件存在：`data/bili/json/`
2. 运行同步脚本：
   ```bash
   python sync_bilibili_data.py --db-type db
   ```
3. 检查同步日志，确认数据已导入

### 问题5：pymysql未安装

**错误信息**: `ModuleNotFoundError: No module named 'pymysql'`

**解决**:
```bash
pip install pymysql
```

## 完整流程

### 如果数据已经在MySQL中：

```bash
# 1. 修改配置文件（已完成）
# config/base_config.py: SAVE_DATA_OPTION = "db"

# 2. 检查MySQL连接和数据
python check_mysql_data.py

# 3. 重启Dashboard
python start_dashboard.py
```

### 如果数据还在JSON文件中：

```bash
# 1. 初始化MySQL数据库
python main.py --init-db mysql

# 2. 同步JSON数据到MySQL
python sync_bilibili_data.py --db-type db

# 3. 修改配置文件
# config/base_config.py: SAVE_DATA_OPTION = "db"

# 4. 检查数据
python check_mysql_data.py

# 5. 启动Dashboard
python start_dashboard.py
```

## 配置对比

| 数据存储位置 | SAVE_DATA_OPTION | 说明 |
|------------|-----------------|------|
| MySQL数据库 | `"db"` 或 `"mysql"` | ✅ Dashboard支持 |
| SQLite数据库 | `"sqlite"` | ✅ Dashboard支持 |
| JSON文件 | `"json"` | ❌ Dashboard不支持 |
| CSV文件 | `"csv"` | ❌ Dashboard不支持 |

## 重要提示

1. **Dashboard只支持数据库**: Dashboard只能从MySQL或SQLite数据库读取数据
2. **配置必须一致**: `SAVE_DATA_OPTION` 必须与数据实际存储位置一致
3. **MySQL服务必须运行**: 使用MySQL时，确保MySQL服务正在运行
4. **重启Dashboard**: 修改配置后必须重启Dashboard才能生效

## 检查清单

- [ ] `config/base_config.py` 中 `SAVE_DATA_OPTION = "db"`
- [ ] `config/db_config.py` 中MySQL配置正确
- [ ] pymysql已安装 (`pip install pymysql`)
- [ ] MySQL服务正在运行
- [ ] 数据库 `pachong` 存在
- [ ] 数据库表已创建（运行过 `python main.py --init-db mysql`）
- [ ] 数据库中有数据（运行过 `python sync_bilibili_data.py --db-type db`）
- [ ] Dashboard已重启

## 总结

**问题根源**: `SAVE_DATA_OPTION = "json"` 导致Dashboard无法连接MySQL数据库

**解决方法**: 
1. ✅ 已将 `SAVE_DATA_OPTION` 改为 `"db"`
2. 确认MySQL连接配置正确
3. 确认数据库中有数据
4. 重启Dashboard

修改完成后，Dashboard应该能够正常显示MySQL数据库中的数据了！

