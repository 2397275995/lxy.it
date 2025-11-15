from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from neo4j import GraphDatabase
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session as OrmSession, sessionmaker
from sqlalchemy import select

from config import (
    COMMENT_LLM_BATCH_SIZE,
    COMMENT_LLM_MAX_RETRIES,
    NEO4J_DATABASE,
    NEO4J_PASSWORD,
    NEO4J_URI,
    NEO4J_USER,
    SEMANTIC_PIPELINE_DEFAULT_PLATFORM,
    SEMANTIC_PIPELINE_OUTPUT_LANG,
    SEMANTIC_PIPELINE_SOURCE_TABLE,
)
from database.db import get_db_engine
from database.models import Base, CommentEntityRelation, CommentSemantic, SemanticEntity
from services.llm_client import CommentInput, CommentSemanticLLMResult, SemanticLLMClient
from tools.utils import logger

CommentDict = Dict[str, object]


@dataclass(slots=True)
class PipelineOptions:
    """语义处理流水线的配置项。"""

    platform: str = SEMANTIC_PIPELINE_DEFAULT_PLATFORM
    source_table: str = SEMANTIC_PIPELINE_SOURCE_TABLE
    language: str = SEMANTIC_PIPELINE_OUTPUT_LANG
    batch_size: int = COMMENT_LLM_BATCH_SIZE
    comment_id_field: str = "comment_id"
    content_field: str = "content"
    created_at_field: Optional[str] = "create_time"
    user_id_field: Optional[str] = "user_id"
    limit: Optional[int] = None


@dataclass(slots=True)
class CommentRecord:
    """提取后的评论记录。"""

    comment_id: str
    content: str
    created_at: Optional[int]
    user_id: Optional[str]
    platform: str
    source_table: str
    language: str
    raw: CommentDict


@dataclass(slots=True)
class EnrichedComment:
    """包含原始评论与语义结果。"""

    record: CommentRecord
    semantic: CommentSemanticLLMResult

    @property
    def unique_id(self) -> str:
        return f"{self.record.platform}:{self.record.comment_id}"


class CommentSemanticPipeline:
    """评论语义处理与入库流程。"""

    def __init__(
        self,
        llm_client: Optional[SemanticLLMClient] = None,
        options: Optional[PipelineOptions] = None,
        engine=None,
        neo4j_driver=None,
    ) -> None:
        self.options = options or PipelineOptions()
        self.llm_client = llm_client or SemanticLLMClient()
        self.engine = engine or get_db_engine()
        if not self.engine:
            raise RuntimeError("无法获取数据库引擎，请确认数据库配置正确。")

        # 自动创建表（如果不存在）
        self._ensure_tables_exist()

        self.SessionFactory = sessionmaker(bind=self.engine)

        self.neo4j_driver = neo4j_driver or self._init_neo4j_driver()
        if not self.neo4j_driver:
            logger.warning("Neo4j 未配置或初始化失败，图谱写入步骤将被跳过。")

    def _ensure_tables_exist(self) -> None:
        """确保所需的数据库表存在，如果不存在则创建。"""
        try:
            # 只创建语义相关的表
            tables_to_create = [
                CommentSemantic.__table__,
                SemanticEntity.__table__,
                CommentEntityRelation.__table__,
            ]
            Base.metadata.create_all(self.engine, tables=tables_to_create, checkfirst=True)
            logger.info("语义相关表已确保存在：comment_semantic, semantic_entity, comment_entity_relation")
        except Exception as exc:  # noqa: BLE001
            logger.warning("创建表时出现警告（表可能已存在）: %s", exc)
            # 不抛出异常，允许继续执行

    def _init_neo4j_driver(self):
        if not NEO4J_URI or not NEO4J_USER or not NEO4J_PASSWORD:
            return None
        try:
            driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            # 测试连接
            with driver.session(database=NEO4J_DATABASE) as session:
                session.run("RETURN 1 AS ok")
            return driver
        except Exception as exc:  # noqa: BLE001
            logger.error("初始化 Neo4j 失败: %s", exc)
            return None

    def run(self, json_path: Path | str) -> List[EnrichedComment]:
        """执行从 JSON 到数据库/图谱的全流程。"""

        path = Path(json_path)
        if not path.exists():
            raise FileNotFoundError(f"未找到 JSON 文件或目录：{json_path}")

        comments = list(self._load_comments(path))
        if not comments:
            logger.warning("在 %s 未找到任何评论记录。", path)
            return []

        logger.info("准备处理 %s 条评论，batch_size=%s", len(comments), self.options.batch_size)

        enriched_records: List[EnrichedComment] = []
        for batch in self._batched(comments, self.options.batch_size):
            enriched_batch = self._process_batch(batch)
            if not enriched_batch:
                continue
            self._persist_batch(enriched_batch)
            enriched_records.extend(enriched_batch)

        logger.info("流水线执行完成，共处理 %s 条评论。", len(enriched_records))
        return enriched_records

    def _load_comments(self, path: Path) -> Iterable[CommentRecord]:
        """从 JSON 文件或目录加载评论。"""

        files: List[Path]
        if path.is_file():
            files = [path]
        else:
            files = sorted(list(path.glob("*.json")))

        counter = 0
        for file_path in files:
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                logger.error("解析 JSON 失败 %s: %s", file_path, exc)
                continue

            items = self._extract_items_from_json(data)
            if not items:
                logger.warning(
                    "文件 %s 中未找到评论数据。JSON 结构可能不匹配。支持的格式：数组或包含 'comments'/'data'/'items'/'list' 键的对象。",
                    file_path,
                )
                # 显示文件的实际结构
                if isinstance(data, dict):
                    logger.debug("JSON 文件顶层键: %s", list(data.keys())[:10])
                elif isinstance(data, list) and data:
                    logger.debug("JSON 文件是数组，第一个元素键: %s", list(data[0].keys())[:10] if isinstance(data[0], dict) else type(data[0]))
                continue
            
            parsed_count = 0
            for item in items:
                record = self._parse_comment(item)
                if record:
                    yield record
                    counter += 1
                    parsed_count += 1
                    if self.options.limit and counter >= self.options.limit:
                        logger.info("已达到 limit=%s，停止继续读取。", self.options.limit)
                        return
            
            if parsed_count == 0 and items:
                logger.warning(
                    "文件 %s 中有 %s 条记录，但无法解析（字段 '%s' 或 '%s' 未找到或为空）。请检查字段名参数。",
                    file_path,
                    len(items),
                    self.options.comment_id_field,
                    self.options.content_field,
                )
                # 显示第一条记录的字段名供参考
                if items and isinstance(items[0], dict):
                    logger.info("第一条记录的可用字段: %s", list(items[0].keys())[:15])

    def _extract_items_from_json(self, data: object) -> List[CommentDict]:
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict):
            for key in ("comments", "data", "items", "list"):
                value = data.get(key)
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, dict)]
        return []

    def _parse_comment(self, raw: CommentDict) -> Optional[CommentRecord]:
        comment_id = raw.get(self.options.comment_id_field)
        content = raw.get(self.options.content_field)

        if not comment_id or not content:
            # 添加调试信息：如果字段不匹配，尝试常见字段名
            if not comment_id:
                # 尝试常见的 comment_id 字段名变体
                for field in ("comment_id", "id", "cid", "commentId"):
                    if field in raw:
                        logger.debug(
                            "字段 '%s' 未找到，但发现 '%s' 字段。请检查 --comment-id-field 参数。",
                            self.options.comment_id_field,
                            field,
                        )
                        break
            if not content:
                # 尝试常见的内容字段名变体
                for field in ("content", "text", "message", "comment", "body"):
                    if field in raw:
                        logger.debug(
                            "字段 '%s' 未找到，但发现 '%s' 字段。请检查 --content-field 参数。",
                            self.options.content_field,
                            field,
                        )
                        break
            return None

        created_at = self._safe_int(raw.get(self.options.created_at_field)) if self.options.created_at_field else None
        user_id = raw.get(self.options.user_id_field) if self.options.user_id_field else None

        return CommentRecord(
            comment_id=str(comment_id),
            content=str(content),
            created_at=created_at,
            user_id=str(user_id) if user_id is not None else None,
            platform=self.options.platform,
            source_table=self.options.source_table,
            language=self.options.language,
            raw=raw,
        )

    def _process_batch(self, batch: List[CommentRecord]) -> List[EnrichedComment]:
        inputs = [
            CommentInput(comment_id=record.comment_id, content=record.content, language=record.language)
            for record in batch
        ]

        retries = COMMENT_LLM_MAX_RETRIES
        while retries > 0:
            try:
                semantic_results = self.llm_client.analyze_batch(inputs)
                break
            except Exception as exc:  # noqa: BLE001
                retries -= 1
                logger.error("调用 LLM 失败，还剩 %s 次重试: %s", retries, exc)
                if retries == 0:
                    raise
                time.sleep(2)

        mapping = {result.comment_id: result for result in semantic_results}
        enriched_batch: List[EnrichedComment] = []
        for record in batch:
            semantic = mapping.get(record.comment_id)
            if not semantic:
                logger.warning("评论 %s 未得到语义结果，跳过。", record.comment_id)
                continue
            enriched_batch.append(EnrichedComment(record=record, semantic=semantic))
        return enriched_batch

    def _persist_batch(self, enriched_batch: List[EnrichedComment]) -> None:
        self._persist_to_mysql(enriched_batch)
        self._persist_to_neo4j(enriched_batch)

    def _persist_to_mysql(self, enriched_batch: List[EnrichedComment]) -> None:
        session: OrmSession
        with self.SessionFactory() as session:
            try:
                for item in enriched_batch:
                    self._upsert_comment_semantic(session, item)
                    self._upsert_entities(session, item)
                session.commit()
            except SQLAlchemyError as exc:
                session.rollback()
                logger.error("写入 MySQL 失败: %s", exc)
                raise

    def _upsert_comment_semantic(self, session: OrmSession, item: EnrichedComment) -> None:
        now_ts = int(time.time())
        # 使用 select 语句查询，兼容 SQLAlchemy 2.0
        try:
            stmt = select(CommentSemantic).where(CommentSemantic.comment_unique_id == item.unique_id)
            result = session.execute(stmt)
            existing = result.scalar_one_or_none()
        except Exception as exc:
            # 如果 select 方式失败，回退到 query 方式（兼容旧版本 SQLAlchemy）
            logger.debug("使用 select 查询失败，回退到 query 方式: %s", exc)
            existing = (
                session.query(CommentSemantic)
                .filter(CommentSemantic.comment_unique_id == item.unique_id)
                .first()
            )

        payload = {
            "platform": item.record.platform,
            "source_table": item.record.source_table,
            "comment_id": item.record.comment_id,
            "comment_unique_id": item.unique_id,
            "content": item.record.content,
            "sentiment_label": item.semantic.sentiment_label,
            "sentiment_score": item.semantic.sentiment_score,
            "summary": item.semantic.summary,
            "topics_json": json.dumps(item.semantic.topics, ensure_ascii=False),
            "entities_json": json.dumps(
                [entity.__dict__ for entity in item.semantic.entities], ensure_ascii=False
            ),
            "sentences_json": json.dumps(item.semantic.sentences, ensure_ascii=False),
            "language": item.record.language,
            "model_name": self.llm_client.model,
            "processed_at": now_ts,
            "updated_at": now_ts,
        }

        if existing:
            for key, value in payload.items():
                setattr(existing, key, value)
        else:
            payload["created_at"] = now_ts
            session.add(CommentSemantic(**payload))

    def _upsert_entities(self, session: OrmSession, item: EnrichedComment) -> None:
        now_ts = int(time.time())
        entities_count = len(item.semantic.entities) if item.semantic.entities else 0
        logger.debug("处理评论 %s 的实体，共 %d 个", item.unique_id, entities_count)
        
        if not item.semantic.entities:
            logger.debug("评论 %s 没有实体数据，跳过实体处理", item.unique_id)
            return
        
        for entity in item.semantic.entities:
            if not entity.name or not entity.type:
                logger.debug("跳过无效实体: name=%s, type=%s", entity.name, entity.type)
                continue

            unique_key = f"{entity.type}:{entity.name}"
            # 使用 select 语句查询，兼容 SQLAlchemy 2.0
            try:
                stmt = select(SemanticEntity).where(SemanticEntity.entity_unique_key == unique_key)
                result = session.execute(stmt)
                existing_entity = result.scalar_one_or_none()
            except Exception as exc:
                # 如果 select 方式失败，回退到 query 方式（兼容旧版本 SQLAlchemy）
                logger.debug("使用 select 查询失败，回退到 query 方式: %s", exc)
                existing_entity = (
                    session.query(SemanticEntity)
                    .filter(SemanticEntity.entity_unique_key == unique_key)
                    .first()
                )

            metadata = {
                "mention": entity.mention,
                "sentiment": entity.sentiment,
            }
            metadata_json = json.dumps(metadata, ensure_ascii=False)

            if existing_entity:
                existing_entity.last_seen_at = now_ts
                existing_entity.metadata_json = metadata_json
            else:
                session.add(
                    SemanticEntity(
                        entity_unique_key=unique_key,
                        name=entity.name,
                        entity_type=entity.type,
                        metadata_json=metadata_json,
                        first_seen_at=now_ts,
                        last_seen_at=now_ts,
                    )
                )

            # 使用 select 语句查询，兼容 SQLAlchemy 2.0
            try:
                stmt = select(CommentEntityRelation).where(
                    CommentEntityRelation.comment_unique_id == item.unique_id,
                    CommentEntityRelation.entity_unique_key == unique_key,
                )
                result = session.execute(stmt)
                relation_exists = result.scalar_one_or_none()
            except Exception as exc:
                # 如果 select 方式失败，回退到 query 方式（兼容旧版本 SQLAlchemy）
                logger.debug("使用 select 查询失败，回退到 query 方式: %s", exc)
                relation_exists = (
                    session.query(CommentEntityRelation)
                    .filter(
                        CommentEntityRelation.comment_unique_id == item.unique_id,
                        CommentEntityRelation.entity_unique_key == unique_key,
                    )
                    .first()
                )

            if relation_exists:
                relation_exists.weight = 1.0
                relation_exists.created_at = now_ts
                logger.debug("更新关系: comment=%s, entity=%s", item.unique_id, unique_key)
            else:
                new_relation = CommentEntityRelation(
                    comment_unique_id=item.unique_id,
                    entity_unique_key=unique_key,
                    relation_type="mentions",
                    weight=1.0,
                    created_at=now_ts,
                )
                session.add(new_relation)
                logger.debug("创建关系: comment=%s, entity=%s", item.unique_id, unique_key)

    def _persist_to_neo4j(self, enriched_batch: List[EnrichedComment]) -> None:
        if not self.neo4j_driver:
            return

        payload = []
        for item in enriched_batch:
            payload.append(
                {
                    "comment_unique_id": item.unique_id,
                    "comment_id": item.record.comment_id,
                    "platform": item.record.platform,
                    "content": item.record.content,
                    "summary": item.semantic.summary,
                    "sentiment_label": item.semantic.sentiment_label,
                    "sentiment_score": item.semantic.sentiment_score,
                    "topics": item.semantic.topics,
                    "entities": [
                        {
                            "name": entity.name,
                            "type": entity.type,
                            "mention": entity.mention,
                            "sentiment": entity.sentiment,
                        }
                        for entity in item.semantic.entities
                        if entity.name and entity.type
                    ],
                    "created_at": item.record.created_at,
                    "processed_at": int(time.time()),
                }
            )

        if not payload:
            return

        try:
            with self.neo4j_driver.session(database=NEO4J_DATABASE) as session:
                session.execute_write(self._neo4j_upsert_batch, payload)
        except Exception as exc:  # noqa: BLE001
            logger.error("写入 Neo4j 失败: %s", exc)
            raise

    @staticmethod
    def _neo4j_upsert_batch(tx, payload: List[Dict[str, object]]) -> None:
        query = """
        UNWIND $batch AS row
        MERGE (c:Comment {comment_unique_id: row.comment_unique_id})
          ON CREATE SET
            c.comment_id = row.comment_id,
            c.platform = row.platform,
            c.created_at = row.created_at,
            c.first_processed_at = row.processed_at
          ON MATCH SET
            c.last_processed_at = row.processed_at
        SET c.summary = row.summary,
            c.sentiment_label = row.sentiment_label,
            c.sentiment_score = row.sentiment_score,
            c.content = row.content,
            c.topics = row.topics
        FOREACH (topic IN row.topics |
            MERGE (t:Topic {name: topic})
            MERGE (c)-[:ABOUT_TOPIC]->(t)
        )
        FOREACH (entity IN row.entities |
            MERGE (e:Entity {name: entity.name, type: entity.type})
            ON CREATE SET e.first_seen_at = row.processed_at
            SET e.last_seen_at = row.processed_at,
                e.last_sentiment = entity.sentiment
            MERGE (c)-[rel:MENTIONS]->(e)
            SET rel.mention = entity.mention,
                rel.sentiment = entity.sentiment,
                rel.updated_at = row.processed_at
        )
        """
        tx.run(query, batch=payload)

    @staticmethod
    def _batched(items: List[CommentRecord], size: int) -> Iterable[List[CommentRecord]]:
        for idx in range(0, len(items), max(size, 1)):
            yield items[idx : idx + size]

    @staticmethod
    def _safe_int(value: object) -> Optional[int]:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

