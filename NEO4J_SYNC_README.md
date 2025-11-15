# Neo4j数据同步服务使用指南

## 概述

本服务实现了跨平台数据同步到Neo4j图数据库的功能，支持将所有平台（Bilibili、Douyin、Kuaishou、Weibo、Xiaohongshu、Zhihu）的内容、评论、创作者数据同步到Neo4j，用于知识图谱分析和可视化。

## 功能特性

- ✅ 支持所有平台的视频/笔记内容同步
- ✅ 支持所有平台的评论数据同步
- ✅ 支持创作者信息同步
- ✅ 自动建立内容-创作者关系
- ✅ 自动建立评论-内容关系
- ✅ 支持关键词节点创建
- ✅ 批量处理，提高效率

## 配置要求

### 1. Neo4j配置

在 `config/semantic_config.py` 中配置Neo4j连接信息：

```python
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "your-password"
NEO4J_DATABASE = "neo4j"
```

或者通过环境变量设置：

```bash
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="your-password"
export NEO4J_DATABASE="neo4j"
```

### 2. 数据库配置

确保已配置好MySQL或SQLite数据库，数据已通过爬虫收集。

## 使用方法

### 方法1: 直接运行同步脚本

```bash
python sync_to_neo4j.py
```

### 方法2: 在代码中调用

```python
from services.neo4j_sync import sync_all_to_neo4j

# 同步所有平台数据
sync_all_to_neo4j(batch_size=100)
```

### 方法3: 同步指定平台

```python
from services.neo4j_sync import Neo4jSyncService

service = Neo4jSyncService()
# 只同步快手平台
service.sync_platform('kuaishou', batch_size=100)
service.close()
```

## 数据模型

### 节点类型

1. **Content节点**: 内容节点（视频/笔记）
   - 属性: content_id, platform, title, user_id, nickname, create_time, source_keyword
   - 标签: Content

2. **Comment节点**: 评论节点
   - 属性: comment_id, platform, content, user_id, nickname, create_time
   - 标签: Comment

3. **Creator节点**: 创作者节点
   - 属性: user_id, platform, nickname, fans, follows
   - 标签: Creator

4. **User节点**: 评论者节点
   - 属性: user_id, platform, nickname
   - 标签: User

5. **Keyword节点**: 关键词节点
   - 属性: name
   - 标签: Keyword

### 关系类型

1. **CREATED**: Creator -> Content (创作者创建内容)
2. **COMMENTS_ON**: Comment -> Content (评论属于内容)
3. **WROTE**: User -> Comment (用户发表评论)
4. **HAS_KEYWORD**: Content -> Keyword (内容包含关键词)

## 查询示例

### 查询某个平台的所有内容

```cypher
MATCH (c:Content {platform: 'kuaishou'})
RETURN c LIMIT 10
```

### 查询内容及其创作者

```cypher
MATCH (creator:Creator)-[:CREATED]->(content:Content)
WHERE content.platform = 'kuaishou'
RETURN creator, content LIMIT 10
```

### 查询内容及其评论

```cypher
MATCH (comment:Comment)-[:COMMENTS_ON]->(content:Content)
WHERE content.platform = 'kuaishou'
RETURN content, comment LIMIT 10
```

### 查询热门关键词

```cypher
MATCH (content:Content)-[:HAS_KEYWORD]->(keyword:Keyword)
WHERE content.platform = 'kuaishou'
RETURN keyword.name, count(*) as count
ORDER BY count DESC LIMIT 10
```

## 注意事项

1. **首次同步**: 首次同步可能需要较长时间，取决于数据量大小
2. **增量同步**: 服务支持增量同步，已存在的节点会更新，不会重复创建
3. **批处理大小**: 默认批处理大小为100，可根据Neo4j性能调整
4. **数据量限制**: 默认每个表最多同步10000条记录，可在代码中调整

## 故障排查

### Neo4j连接失败

- 检查Neo4j服务是否运行
- 检查连接配置是否正确
- 检查防火墙设置

### 同步速度慢

- 减小batch_size参数
- 检查数据库查询性能
- 检查Neo4j服务器性能

### 数据不完整

- 检查源数据库是否有数据
- 检查表名是否正确
- 查看日志了解详细错误信息

## 与Dashboard集成

同步到Neo4j的数据可以在Dashboard的"Semantic Insights"页面中查看，包括：
- 实体关系图谱
- 关键词关联分析
- 跨平台数据关联

## 更新日志

- 2024-01-XX: 初始版本，支持所有平台数据同步

