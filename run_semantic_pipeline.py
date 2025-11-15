from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from config.semantic_config import COMMENT_LLM_API_KEY
from services.semantic_pipeline import CommentSemanticPipeline, PipelineOptions
from tools.utils import logger

app = typer.Typer(help="评论语义增强与知识图谱同步流水线")


@app.command()
def run(
    json_path: str = typer.Argument(..., help="评论 JSON 文件或目录路径"),
    platform: str = typer.Option(None, help="平台标识，例如 bilibili/weibo 等"),
    source_table: str = typer.Option(None, help="原始数据来源表名"),
    language: str = typer.Option(None, help="评论语言，默认读取配置"),
    batch_size: int = typer.Option(None, help="大模型批处理大小"),
    limit: Optional[int] = typer.Option(None, help="仅处理前 N 条评论"),
    comment_id_field: str = typer.Option("comment_id", help="评论 ID 字段名"),
    content_field: str = typer.Option("content", help="评论内容字段名"),
    created_at_field: str = typer.Option("create_time", help="评论创建时间字段名"),
    user_id_field: Optional[str] = typer.Option("user_id", help="用户 ID 字段名"),
) -> None:
    """执行评论语义处理流水线。"""

    # 检查 API 密钥配置
    if not COMMENT_LLM_API_KEY:
        logger.error(
            "未找到 LLM API 密钥！\n"
            "请设置环境变量 COMMENT_LLM_API_KEY 或 OPENAI_API_KEY。\n"
            "详细配置说明请参考：SEMANTIC_CONFIG_README.md"
        )
        raise typer.Exit(code=1)

    defaults = PipelineOptions()
    options = PipelineOptions(
        platform=platform or defaults.platform,
        source_table=source_table or defaults.source_table,
        language=language or defaults.language,
        batch_size=batch_size or defaults.batch_size,
        comment_id_field=comment_id_field,
        content_field=content_field,
        created_at_field=created_at_field,
        user_id_field=user_id_field,
        limit=limit,
    )

    try:
        pipeline = CommentSemanticPipeline(options=options)
        enriched = pipeline.run(Path(json_path))
        logger.info("共写入 %s 条语义增强评论。", len(enriched))
    except ValueError as e:
        if "API 密钥" in str(e) or "API key" in str(e).lower():
            logger.error(str(e))
            raise typer.Exit(code=1)
        raise


if __name__ == "__main__":
    app()

