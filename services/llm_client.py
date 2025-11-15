from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from tenacity import retry, stop_after_attempt, wait_exponential

from config import (
    COMMENT_LLM_API_KEY,
    COMMENT_LLM_BASE_URL,
    COMMENT_LLM_MODEL,
    COMMENT_LLM_PROVIDER,
)


@dataclass(slots=True)
class CommentInput:
    """原始评论输入。"""

    comment_id: str
    content: str
    language: str = "zh"


@dataclass(slots=True)
class EntityExtraction:
    """LLM 返回的实体信息。"""

    name: str
    type: str
    mention: Optional[str] = None
    sentiment: Optional[str] = None


@dataclass(slots=True)
class CommentSemanticLLMResult:
    """LLM 输出的结构化结果。"""

    comment_id: str
    summary: str
    sentiment_label: str
    sentiment_score: Optional[float]
    topics: List[str]
    sentences: List[str]
    entities: List[EntityExtraction]


class SemanticLLMClient:
    """封装大模型调用，负责语义分析。"""

    def __init__(
        self,
        provider: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.provider = (provider or COMMENT_LLM_PROVIDER).lower()
        self.model = model or COMMENT_LLM_MODEL
        self.api_key = api_key or COMMENT_LLM_API_KEY
        self.base_url = base_url or COMMENT_LLM_BASE_URL

        if not self.api_key:
            raise ValueError(
                "未找到 LLM API 密钥！\n"
                "请设置以下环境变量之一：\n"
                "  1. COMMENT_LLM_API_KEY (推荐)\n"
                "  2. OPENAI_API_KEY (备选)\n"
                "\n"
                "设置方法：\n"
                "  Windows PowerShell: $env:COMMENT_LLM_API_KEY='your-api-key'\n"
                "  Windows CMD: set COMMENT_LLM_API_KEY=your-api-key\n"
                "  Linux/macOS: export COMMENT_LLM_API_KEY='your-api-key'\n"
                "\n"
                "或者创建 .env 文件（需要 python-dotenv 支持）：\n"
                "  COMMENT_LLM_API_KEY=your-api-key\n"
                "\n"
                "详细配置说明请参考：MediaCrawler/config/semantic_config.py"
            )

        if self.provider == "openai":
            from openai import OpenAI

            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        else:
            raise NotImplementedError(f"暂不支持的 LLM 提供商: {self.provider}")

    def analyze_batch(self, comments: List[CommentInput]) -> List[CommentSemanticLLMResult]:
        """对一批评论做语义分析。"""

        if not comments:
            return []

        response = self._call_llm(comments)
        parsed = self._parse_response(response, comments)
        return parsed

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def _call_llm(self, comments: List[CommentInput]) -> Dict[str, Any]:
        """向 LLM 发送请求。"""

        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个专业的中文文本分析助手，擅长对社交媒体评论进行深度结构化分析。"
                    "你的任务包括：情感分析、主题提取、实体识别和内容摘要。"
                    "请特别注意实体识别：必须仔细提取评论中提到的所有实体（人物、组织、地点、产品、品牌、事件等），"
                    "即使实体名称不完整或模糊，也要尽可能识别。"
                    "请确保输出严格遵守 JSON 格式，字段包含 comment_id, summary, sentiment_label, sentiment_score, topics, sentences, entities。"
                ),
            },
            {
                "role": "user",
                "content": self._build_user_prompt(comments),
            },
        ]

        completion = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        return completion.model_dump()

    @staticmethod
    def _build_user_prompt(comments: List[CommentInput]) -> str:
        payload = [
            {
                "comment_id": item.comment_id,
                "language": item.language,
                "content": item.content,
            }
            for item in comments
        ]

        instructions = (
            "请对以下评论逐条进行分析，输出 JSON 对象，字段如下：\n"
            "results: 数组，数组元素包含以下字段：\n"
            "- comment_id: 输入中的 comment_id\n"
            "- summary: 对评论的简短归纳（20字以内）\n"
            "- sentiment_label: positive/neutral/negative 之一\n"
            "- sentiment_score: 介于 -1 和 1 的数字，可为空\n"
            "- topics: 数组，列出与评论相关的主题关键词（每个不超过4个汉字）\n"
            "- sentences: 数组，对原评论的分句或重点摘录\n"
            "- entities: 数组，必须提取评论中提到的所有实体。每个实体是一个对象，包含：\n"
            "  * name: 实体名称（必填，字符串）\n"
            "  * type: 实体类型（必填，从以下类型中选择：PERSON人物、ORG组织/机构、LOCATION地点、PRODUCT产品、BRAND品牌、EVENT事件、CONCEPT概念/话题、OTHER其他）\n"
            "  * mention: 实体在评论中的提及方式（可选，字符串，如\"@用户名\"、\"#话题#\"等）\n"
            "  * sentiment: 对该实体的情感倾向（可选，positive/neutral/negative）\n"
            "  注意：即使评论中没有明显的实体，也要尝试提取（如提到的产品名、品牌名、人物名、地点等）。如果确实没有任何实体，返回空数组 []。\n"
            "请确保 results 数组的顺序与输入顺序一致。"
        )

        return f"{instructions}\n\n输入评论：\n{json.dumps(payload, ensure_ascii=False, indent=2)}"

    def _parse_response(
        self, response: Dict[str, Any], comments: List[CommentInput]
    ) -> List[CommentSemanticLLMResult]:
        content = self._extract_content(response)
        if not content:
            raise ValueError("LLM 返回为空，无法解析。")

        data = self._safe_json_loads(content)

        results: Optional[List[Any]] = None
        if isinstance(data, dict):
            dict_results = data.get("results")
            if isinstance(dict_results, list):
                results = dict_results
            else:
                # 兼容直接返回单条对象的情况
                if self._looks_like_result(data):
                    results = [data]
        elif isinstance(data, list):
            results = data

        if not isinstance(results, list):
            raise ValueError(f"LLM 返回格式不正确: {content}")

        parsed_results: List[CommentSemanticLLMResult] = []
        comments_map = {item.comment_id: item for item in comments}

        for item in results:
            comment_id = str(item.get("comment_id"))
            if comment_id not in comments_map:
                # 忽略多余记录
                continue

            entities_data = item.get("entities") or []
            entities: List[EntityExtraction] = []
            for entity in entities_data:
                if not isinstance(entity, dict) or "name" not in entity or "type" not in entity:
                    continue
                entities.append(
                    EntityExtraction(
                        name=str(entity["name"]).strip(),
                        type=str(entity["type"]).strip(),
                        mention=str(entity.get("mention")).strip() if entity.get("mention") else None,
                        sentiment=str(entity.get("sentiment")).strip()
                        if entity.get("sentiment")
                        else None,
                    )
                )

            parsed_results.append(
                CommentSemanticLLMResult(
                    comment_id=comment_id,
                    summary=str(item.get("summary") or "").strip(),
                    sentiment_label=str(item.get("sentiment_label") or "").strip()
                    or "neutral",
                    sentiment_score=self._safe_float(item.get("sentiment_score")),
                    topics=[str(topic).strip() for topic in (item.get("topics") or []) if topic],
                    sentences=[
                        str(sentence).strip() for sentence in (item.get("sentences") or []) if sentence
                    ],
                    entities=entities,
                )
            )

        # 如果个别评论没有返回结果，追加空壳，避免后续处理中断
        missing_ids = set(comments_map.keys()) - {item.comment_id for item in parsed_results}
        for comment_id in missing_ids:
            parsed_results.append(
                CommentSemanticLLMResult(
                    comment_id=comment_id,
                    summary="",
                    sentiment_label="neutral",
                    sentiment_score=None,
                    topics=[],
                    sentences=[],
                    entities=[],
                )
            )

        # 按原顺序排序
        parsed_results.sort(key=lambda item: list(comments_map.keys()).index(item.comment_id))
        return parsed_results

    @staticmethod
    def _looks_like_result(data: Dict[str, Any]) -> bool:
        """粗略判断对象是否像单条结果，兼容部分模型未套 results 数组的场景。"""
        required_keys = {"comment_id", "summary", "sentiment_label"}
        return required_keys.issubset(set(data.keys()))

    @staticmethod
    def _extract_content(response: Dict[str, Any]) -> Optional[str]:
        try:
            choices = response["choices"]
            if not choices:
                return None
            message = choices[0]["message"]
            return message.get("content")
        except (KeyError, TypeError):
            return None

    @staticmethod
    def _safe_json_loads(text: str) -> Any:
        text = text.strip()
        if not text:
            return {}

        # 尝试截取大括号中的 JSON
        if text[0] not in "[{":
            first = text.find("{")
            if first >= 0:
                text = text[first:]
        if text and text[-1] not in "}]":
            last_curly = text.rfind("}")
            last_bracket = text.rfind("]")
            last_index = max(last_curly, last_bracket)
            if last_index > 0:
                text = text[: last_index + 1]
        return json.loads(text)

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

