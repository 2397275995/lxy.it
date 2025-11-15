# 快速开始：语义增强功能配置

## 问题解决

如果遇到 `ValueError: 未找到 COMMENT_LLM_API_KEY 或 OPENAI_API_KEY` 错误，请按照以下步骤操作：

## 快速配置（3 步）

### 步骤 1：设置环境变量

根据你的操作系统选择对应的命令：

#### Windows PowerShell（推荐）
```powershell
# 设置 LLM API 密钥
$env:COMMENT_LLM_API_KEY="your-api-key-here"

# 可选：设置模型名称
$env:COMMENT_LLM_MODEL="gpt-4o-mini"

# 可选：设置 Neo4j 配置
$env:NEO4J_URI="bolt://localhost:7687"
$env:NEO4J_USER="neo4j"
$env:NEO4J_PASSWORD="your-neo4j-password"
```

#### Windows CMD
```cmd
set COMMENT_LLM_API_KEY=your-api-key-here
set COMMENT_LLM_MODEL=gpt-4o-mini
set NEO4J_URI=bolt://localhost:7687
set NEO4J_USER=neo4j
set NEO4J_PASSWORD=your-neo4j-password
```

#### Linux/macOS
```bash
export COMMENT_LLM_API_KEY="your-api-key-here"
export COMMENT_LLM_MODEL="gpt-4o-mini"
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="your-neo4j-password"
```

### 步骤 2：验证配置

运行以下命令验证配置是否正确：

```bash
python -c "from config.semantic_config import COMMENT_LLM_API_KEY; print('✅ API Key 已设置' if COMMENT_LLM_API_KEY else '❌ API Key 未设置')"
```

### 步骤 3：运行语义处理流水线

```bash
python run_semantic_pipeline.py ./data/bili/json --platform bilibili --limit 10
```

> 提示：使用 `--limit 10` 可以先处理少量数据进行测试。

## 永久配置（推荐）

### 方法 1：Windows 系统环境变量

1. 右键"此电脑" → "属性"
2. 点击"高级系统设置"
3. 点击"环境变量"
4. 在"用户变量"中添加：
   - 变量名：`COMMENT_LLM_API_KEY`
   - 变量值：`your-api-key-here`
5. 点击"确定"保存

### 方法 2：使用 .env 文件

1. 在项目根目录创建 `.env` 文件
2. 添加以下内容：
   ```env
   COMMENT_LLM_API_KEY=your-api-key-here
   COMMENT_LLM_MODEL=gpt-4o-mini
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your-neo4j-password
   ```
3. 安装 python-dotenv：
   ```bash
   pip install python-dotenv
   ```
4. 在代码中加载（如果需要）：
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```

## 获取 API 密钥

### OpenAI API
1. 访问 https://platform.openai.com/api-keys
2. 登录并创建新的 API 密钥
3. 复制密钥并设置到环境变量

### 其他兼容 OpenAI API 的服务
- **DeepSeek**: https://platform.deepseek.com/
- **其他兼容服务**: 使用兼容 OpenAI API 格式的服务

## 常见问题

### Q: 设置环境变量后仍然报错？
A: 确保在**同一个终端窗口**中设置环境变量并运行脚本。关闭终端后环境变量会失效（除非设置了系统环境变量）。

### Q: 可以使用 OPENAI_API_KEY 吗？
A: 可以。如果没有设置 `COMMENT_LLM_API_KEY`，系统会自动尝试使用 `OPENAI_API_KEY`。

### Q: Neo4j 未配置会影响功能吗？
A: 不会。如果 Neo4j 未配置，语义处理流水线会跳过图谱写入步骤，但仍会正常写入 MySQL 数据库。

### Q: 如何验证配置是否生效？
A: 运行以下命令：
```bash
python -c "from config.semantic_config import COMMENT_LLM_API_KEY, COMMENT_LLM_MODEL; print(f'API Key: {\"已设置\" if COMMENT_LLM_API_KEY else \"未设置\"}'); print(f'Model: {COMMENT_LLM_MODEL}')"
```

## 下一步

配置完成后，运行完整的语义处理流程：

```bash
# 处理评论数据
python run_semantic_pipeline.py ./data/bili/json --platform bilibili

# 启动 Dashboard 查看结果
python start_dashboard.py
```

更多详细信息请参考：
- [SEMANTIC_CONFIG_README.md](./SEMANTIC_CONFIG_README.md) - 完整配置说明
- [DASHBOARD_README.md](./DASHBOARD_README.md) - Dashboard 使用指南

