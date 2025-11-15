# 快手数据同步到Dashboard使用指南

## 概述

本指南说明如何将快手爬取的JSON数据同步到数据库，以便在Dashboard中查看和分析。

## 功能特性

- ✅ 支持从JSON文件同步视频数据到MySQL/SQLite数据库
- ✅ 支持从JSON文件同步评论数据到数据库
- ✅ 自动去重，避免重复数据
- ✅ 支持增量同步，只更新已存在的数据
- ✅ 完整的错误处理和日志记录

## 使用步骤

### 步骤1: 确认数据文件位置

快手数据JSON文件应位于以下目录：
```
MediaCrawler/data/kuaishou/json/
```

文件命名规则：
- 视频数据：包含 `content` 或 `video` 的文件名
- 评论数据：包含 `comment` 的文件名

### 步骤2: 确认数据库配置

确保 `config/base_config.py` 中配置正确：

```python
SAVE_DATA_OPTION = "db"  # 使用MySQL数据库
# 或
SAVE_DATA_OPTION = "sqlite"  # 使用SQLite数据库
```

确保 `config/db_config.py` 中数据库连接配置正确（如果使用MySQL）。

### 步骤3: 运行同步脚本

#### 方法1: 使用默认配置

```bash
python sync_kuaishou_data.py
```

这将：
- 从 `data/kuaishou/json/` 目录读取所有JSON文件
- 同步到配置文件中指定的数据库（`SAVE_DATA_OPTION`）

#### 方法2: 指定数据库类型

```bash
# 同步到MySQL
python sync_kuaishou_data.py --db-type db

# 同步到SQLite
python sync_kuaishou_data.py --db-type sqlite
```

#### 方法3: 指定数据目录

```bash
python sync_kuaishou_data.py --data-dir /path/to/kuaishou/json
```

#### 方法4: 组合使用

```bash
python sync_kuaishou_data.py --data-dir data/kuaishou/json --db-type db
```

## 同步过程说明

### 视频数据同步

脚本会：
1. 读取所有包含 `content` 或 `video` 的JSON文件
2. 解析视频数据
3. 检查数据库中是否已存在（根据 `video_id`）
4. 如果不存在，创建新记录
5. 如果已存在，更新记录（保留 `add_ts`，更新其他字段）

### 评论数据同步

脚本会：
1. 读取所有包含 `comment` 的JSON文件
2. 解析评论数据
3. 检查数据库中是否已存在（根据 `comment_id`）
4. 如果不存在，创建新记录
5. 如果已存在，更新记录

## 数据字段映射

### 视频数据字段

| JSON字段 | 数据库字段 | 说明 |
|---------|-----------|------|
| video_id | video_id | 视频ID（主键） |
| title | title | 视频标题 |
| desc | desc | 视频描述 |
| create_time | create_time | 创建时间（时间戳） |
| user_id | user_id | 用户ID |
| nickname | nickname | 用户昵称 |
| liked_count | liked_count | 点赞数 |
| viewd_count | viewd_count | 观看数 |
| video_url | video_url | 视频URL |
| source_keyword | source_keyword | 来源关键词 |

### 评论数据字段

| JSON字段 | 数据库字段 | 说明 |
|---------|-----------|------|
| comment_id | comment_id | 评论ID（主键） |
| video_id | video_id | 关联的视频ID |
| content | content | 评论内容 |
| create_time | create_time | 创建时间（时间戳） |
| user_id | user_id | 用户ID |
| nickname | nickname | 用户昵称 |
| sub_comment_count | sub_comment_count | 子评论数 |

## 验证同步结果

### 方法1: 使用检查脚本

```bash
python check_mysql_data.py
```

### 方法2: 直接查询数据库

```sql
-- MySQL
mysql -u root -p -e "USE pachong; SELECT COUNT(*) FROM kuaishou_video;"
mysql -u root -p -e "USE pachong; SELECT COUNT(*) FROM kuaishou_video_comment;"

-- SQLite
sqlite3 database/sqlite_tables.db "SELECT COUNT(*) FROM kuaishou_video;"
sqlite3 database/sqlite_tables.db "SELECT COUNT(*) FROM kuaishou_video_comment;"
```

### 方法3: 启动Dashboard查看

```bash
# Streamlit Dashboard
python start_dashboard.py

# Flask Dashboard
python start_flask_dashboard.py
```

然后在Dashboard中查看"快手分析"页面。

## 常见问题

### Q1: 同步时提示"数据目录不存在"

**A:** 检查数据目录路径是否正确，确保JSON文件在 `data/kuaishou/json/` 目录下。

### Q2: 同步时提示"无法获取数据库引擎"

**A:** 检查数据库配置：
1. 确认 `config/base_config.py` 中 `SAVE_DATA_OPTION` 设置正确
2. 确认 `config/db_config.py` 中数据库连接信息正确
3. 确认数据库服务正在运行（MySQL需要启动服务）

### Q3: 同步后Dashboard看不到数据

**A:** 检查以下几点：
1. 确认数据已成功同步到数据库（使用验证方法）
2. 确认Dashboard使用的数据库配置与同步时一致
3. 重启Dashboard服务

### Q4: 如何只同步部分数据？

**A:** 可以将要同步的JSON文件单独放在一个目录，然后使用 `--data-dir` 参数指定。

### Q5: 同步会覆盖现有数据吗？

**A:** 不会完全覆盖。脚本使用"upsert"策略：
- 如果记录不存在，创建新记录
- 如果记录已存在，更新除主键外的其他字段
- `add_ts` 字段在更新时保持不变

## 完整工作流程示例

```bash
# 1. 爬取快手数据（数据会保存到JSON文件）
python main.py --platform ks --keywords "游戏,王者"

# 2. 同步JSON数据到数据库
python sync_kuaishou_data.py --db-type db

# 3. 验证数据
python check_mysql_data.py

# 4. 启动Dashboard查看
python start_dashboard.py
# 或
python start_flask_dashboard.py

# 5. 在Dashboard中查看"快手分析"页面
```

## 与Neo4j同步

如果需要将数据同步到Neo4j图数据库，可以运行：

```bash
# 同步所有平台数据到Neo4j（包括快手）
python sync_to_neo4j.py

# 或只同步快手平台
python -c "from services.neo4j_sync import Neo4jSyncService; service = Neo4jSyncService(); service.sync_platform('kuaishou'); service.close()"
```

## 注意事项

1. **数据备份**: 同步前建议备份数据库
2. **数据量**: 大量数据同步可能需要较长时间，请耐心等待
3. **错误处理**: 如果同步过程中出现错误，脚本会记录详细日志
4. **重复运行**: 可以安全地重复运行同步脚本，不会产生重复数据

## 更新日志

- 2025-01-XX: 初始版本，支持视频和评论数据同步

