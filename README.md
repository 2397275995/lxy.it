# 🔥 Social Media Comments Crawler - 社交媒体评论爬虫

一个功能强大的**多平台社交媒体数据采集工具**，支持小红书、抖音、快手、B站、微博、贴吧、知乎等主流平台的公开信息抓取和数据分析。

## 📖 项目简介

本项目基于 [Playwright](https://playwright.dev/) 浏览器自动化框架，通过保留登录态的浏览器上下文环境获取数据，无需复杂的 JS 逆向工程，大幅降低技术门槛。

### 🔧 技术原理

- **核心技术**：基于 [Playwright](https://playwright.dev/) 浏览器自动化框架登录保存登录态
- **无需JS逆向**：利用保留登录态的浏览器上下文环境，通过 JS 表达式获取签名参数
- **优势特点**：无需逆向复杂的加密算法，大幅降低技术门槛

## ✨ 功能特性

| 平台   | 关键词搜索 | 指定帖子ID爬取 | 二级评论 | 指定创作者主页 | 登录态缓存 | IP代理池 | 生成评论词云图 |
| ------ | ---------- | -------------- | -------- | -------------- | ---------- | -------- | -------------- |
| 小红书 | ✅          | ✅              | ✅        | ✅              | ✅          | ✅        | ✅              |
| 抖音   | ✅          | ✅              | ✅        | ✅              | ✅          | ✅        | ✅              |
| 快手   | ✅          | ✅              | ✅        | ✅              | ✅          | ✅        | ✅              |
| B 站   | ✅          | ✅              | ✅        | ✅              | ✅          | ✅        | ✅              |
| 微博   | ✅          | ✅              | ✅        | ✅              | ✅          | ✅        | ✅              |
| 贴吧   | ✅          | ✅              | ✅        | ✅              | ✅          | ✅        | ✅              |
| 知乎   | ✅          | ✅              | ✅        | ✅              | ✅          | ✅        | ✅              |

### 🎯 核心功能

- ✅ **多平台支持**：支持7大主流社交媒体平台
- ✅ **数据存储**：支持 MySQL、SQLite、MongoDB、CSV、JSON 等多种存储方式
- ✅ **数据分析**：内置 Flask Dashboard 和 Streamlit Dashboard 进行数据可视化
- ✅ **语义分析**：支持 LLM 语义增强，提取主题、实体和情感分析
- ✅ **知识图谱**：支持 Neo4j 知识图谱存储和可视化
- ✅ **IP代理池**：支持多种代理服务商，自动管理代理IP
- ✅ **登录态缓存**：自动保存和复用登录状态，减少登录频率

## 🚀 快速开始

### 📋 前置依赖

- Python 3.8+
- Node.js (用于执行部分 JS 代码)
- MySQL/SQLite/MongoDB (可选，用于数据存储)

### 🔧 安装步骤

1. **克隆仓库**

```bash
git clone https://gitlab.com/2397275995/social-media-comments-pachong.git
cd social-media-comments-pachong/MediaCrawler
```

2. **安装 Python 依赖**

```bash
pip install -r requirements.txt
```

3. **安装 Playwright 浏览器**

```bash
playwright install
playwright install-deps
```

4. **配置环境变量**

复制并编辑配置文件：

```bash
# 编辑数据库配置
vim config/db_config.py

# 编辑平台配置（如需要）
vim config/xhs_config.py  # 小红书配置
vim config/dy_config.py   # 抖音配置
# ... 其他平台配置
```

### 📝 基本使用

#### 1. 爬取小红书数据

```bash
python main.py xhs --keywords "关键词1,关键词2" --max_note_count 10
```

#### 2. 爬取抖音数据

```bash
python main.py douyin --keywords "关键词" --max_aweme_count 20
```

#### 3. 爬取B站数据

```bash
python main.py bilibili --keywords "关键词" --max_video_count 30
```

#### 4. 启动数据分析 Dashboard

**Flask Dashboard (推荐)**

```bash
python start_flask_dashboard.py
# 访问 http://localhost:5000
```

**Streamlit Dashboard**

```bash
python start_dashboard.py
# 访问 http://localhost:8501
```

## 📊 数据分析功能

### Flask Dashboard

基于 Flask 的前后端分离 Dashboard，提供：

- 📈 平台概览数据统计
- 📊 各平台详细数据分析
- 🔗 跨平台对比分析
- 🧠 语义洞察（主题提取、情感分析）
- 📅 时间线可视化

### 语义分析

支持使用 LLM 对评论进行语义增强：

```bash
# 运行语义处理流水线
python run_semantic_pipeline.py
```

功能包括：
- 情感分析（正面/中性/负面）
- 主题提取
- 实体识别（人物、组织、地点、产品等）
- 内容摘要

## 📁 项目结构

```
MediaCrawler/
├── main.py                 # 主入口文件
├── config/                 # 配置文件目录
│   ├── db_config.py        # 数据库配置
│   ├── xhs_config.py       # 小红书配置
│   └── ...                 # 其他平台配置
├── media_platform/         # 各平台爬虫实现
│   ├── xhs/               # 小红书
│   ├── douyin/            # 抖音
│   ├── bilibili/          # B站
│   └── ...                # 其他平台
├── database/              # 数据库相关
│   ├── models.py          # 数据模型
│   └── db.py              # 数据库连接
├── flask_dashboard/       # Flask Dashboard
│   ├── app.py             # Flask 后端
│   ├── templates/         # HTML 模板
│   └── static/            # 静态资源
├── services/              # 服务层
│   ├── semantic_pipeline.py  # 语义处理流水线
│   └── llm_client.py      # LLM 客户端
└── store/                 # 数据存储实现
    ├── mongodb_store_base.py
    └── ...
```

## 🔧 配置说明

### 数据库配置

编辑 `config/db_config.py`：

```python
# MySQL 配置
mysql_db_config = {
    'host': 'localhost',
    'port': 3306,
    'user': 'your_user',
    'password': 'your_password',
    'db_name': 'your_database'
}

# SQLite 配置
sqlite_db_config = {
    'db_path': './database/sqlite_tables.db'
}
```

### 平台配置

各平台的配置在 `config/` 目录下，包括：
- 登录方式配置
- 爬取参数配置
- 代理配置（可选）

## 📚 文档

- [Dashboard 使用指南](DASHBOARD_README.md)
- [Flask Dashboard 使用指南](flask_dashboard/README.md)
- [语义分析快速开始](QUICK_START_SEMANTIC.md)
- [Neo4j 同步说明](NEO4J_SYNC_README.md)
- [常见问题](docs/常见问题.md)

## ⚠️ 免责声明

> **重要提示：**
> 
> 本项目仅供学习和研究使用，禁止用于商业用途。任何人或组织不得将本项目用于非法用途或侵犯他人合法权益。
> 
> 使用本项目进行数据采集时，请遵守：
> - 目标平台的用户协议和服务条款
> - 相关法律法规（如《网络安全法》、《数据安全法》等）
> - robots.txt 协议
> - 合理的爬取频率，避免对目标服务器造成压力
> 
> 对于因使用本项目而引起的任何法律责任，本项目不承担任何责任。使用本项目即表示您同意本免责声明的所有条款和条件。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目基于原项目 [MediaCrawler](https://github.com/NanmiCoder/MediaCrawler) 进行修改和扩展。

## 🙏 致谢

- 感谢原项目 [MediaCrawler](https://github.com/NanmiCoder/MediaCrawler) 的开源贡献
- 感谢所有贡献者的支持

## 📮 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue: [GitLab Issues](https://gitlab.com/2397275995/social-media-comments-pachong/-/issues)

---

**⭐ 如果这个项目对您有帮助，请给个 Star 支持一下！**

