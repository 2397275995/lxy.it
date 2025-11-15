# Flask Dashboard 使用指南

## 📋 概述

这是一个基于Flask的前后端分离Dashboard，替代了原来的Streamlit版本。提供了更灵活的定制能力和更好的性能。

## 🚀 快速开始

### 1. 安装依赖

```bash
cd flask_dashboard
pip install -r requirements.txt
```

或者从项目根目录：

```bash
pip install Flask Flask-CORS pandas sqlalchemy pymysql neo4j numpy
```

### 2. 启动服务器

从项目根目录运行：

```bash
python start_flask_dashboard.py
```

或者指定端口和主机：

```bash
python start_flask_dashboard.py --host 0.0.0.0 --port 5000 --debug
```

### 3. 访问Dashboard

在浏览器中打开：`http://localhost:5000`

## 📁 项目结构

```
flask_dashboard/
├── app.py                 # Flask后端API服务器
├── templates/
│   └── index.html         # 前端HTML主页面
├── static/
│   ├── css/
│   │   └── style.css      # 样式文件
│   └── js/
│       └── dashboard.js   # JavaScript交互逻辑
└── requirements.txt       # Python依赖
```

## 🔌 API接口

### 健康检查
- `GET /api/health` - 检查服务器和数据库状态

### 数据接口
- `GET /api/overview` - 获取平台概览数据
- `GET /api/bilibili` - 获取Bilibili数据
- `GET /api/douyin` - 获取Douyin数据
- `GET /api/cross-platform` - 获取跨平台对比数据
- `GET /api/semantic` - 获取语义增强数据
  - 查询参数：
    - `start_date` - 开始日期 (YYYY-MM-DD)
    - `end_date` - 结束日期 (YYYY-MM-DD)
    - `platforms` - 平台列表（可重复）

## 🎨 功能特性

### 已实现功能
- ✅ 平台概览（Overview）
- ✅ Bilibili数据分析
- ✅ Douyin数据分析
- ✅ 跨平台对比分析
- ✅ 语义洞察（Semantic Insights）
- ✅ 响应式设计
- ✅ 自动刷新功能
- ✅ 日期范围过滤
- ✅ 平台筛选

### 待实现功能
- ⏳ Advanced Analytics（高级分析）
- ⏳ Real-Time Monitor（实时监控）
- ⏳ Data Export（数据导出）

## 🔧 配置

### 数据库配置

Dashboard使用项目根目录的数据库配置：
- `config/db_config.py` - MySQL配置
- `config/base_config.py` - 数据存储选项

### 端口配置

默认端口：5000

可以通过命令行参数修改：
```bash
python start_flask_dashboard.py --port 8080
```

## 🐛 故障排除

### 问题1：无法连接数据库

**解决方法**：
1. 检查 `config/db_config.py` 中的数据库配置
2. 确认MySQL服务正在运行
3. 确认 `config/base_config.py` 中 `SAVE_DATA_OPTION = "db"`

### 问题2：端口被占用

**解决方法**：
```bash
# 使用其他端口
python start_flask_dashboard.py --port 5001
```

### 问题3：前端资源加载失败

**解决方法**：
1. 确认 `flask_dashboard/static` 和 `flask_dashboard/templates` 目录存在
2. 检查文件路径是否正确

## 📝 开发说明

### 添加新页面

1. 在 `templates/index.html` 中添加新页面HTML
2. 在 `static/js/dashboard.js` 中添加数据加载函数
3. 在 `app.py` 中添加对应的API接口

### 自定义样式

修改 `static/css/style.css` 文件

### 添加新图表

使用 Chart.js 或 Plotly.js 库，参考现有图表实现

## 🔄 从Streamlit迁移

如果你之前使用Streamlit Dashboard：

1. **数据兼容性**：Flask版本使用相同的数据库，数据完全兼容
2. **功能对比**：大部分功能已迁移，部分高级功能待实现
3. **性能提升**：前后端分离架构提供更好的性能和可扩展性

## 📚 相关文档

- `DASHBOARD_README.md` - 原Streamlit Dashboard文档
- `DASHBOARD_MYSQL_FIX.md` - MySQL连接问题修复指南

