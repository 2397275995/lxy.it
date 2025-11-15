"""
语义增强与知识图谱相关配置。

优先读取环境变量，便于在不同部署环境下灵活调整。
"""

from __future__ import annotations

import os

# LLM 配置
COMMENT_LLM_PROVIDER = os.getenv("COMMENT_LLM_PROVIDER", "openai")
COMMENT_LLM_MODEL = "Qwen/Qwen2.5-Coder-32B-Instruct"
COMMENT_LLM_BASE_URL = "https://api-inference.modelscope.cn/v1/"
COMMENT_LLM_API_KEY = "ms-233666e2-c7fe-4cbf-8315-631eb1d8899e"
COMMENT_LLM_MAX_RETRIES = int(os.getenv("COMMENT_LLM_MAX_RETRIES", "3"))
COMMENT_LLM_BATCH_SIZE = int(os.getenv("COMMENT_LLM_BATCH_SIZE", "20"))

# Neo4j 配置
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "15236574008a")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

# Pipeline 运行控制
SEMANTIC_PIPELINE_DEFAULT_PLATFORM = os.getenv(
    "SEMANTIC_PIPELINE_DEFAULT_PLATFORM", "generic"
)
SEMANTIC_PIPELINE_SOURCE_TABLE = os.getenv(
    "SEMANTIC_PIPELINE_SOURCE_TABLE", "raw_comments"
)
SEMANTIC_PIPELINE_OUTPUT_LANG = os.getenv("SEMANTIC_PIPELINE_OUTPUT_LANG", "zh")

