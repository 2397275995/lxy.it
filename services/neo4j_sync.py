# -*- coding: utf-8 -*-
"""
跨平台数据同步到Neo4j服务
将所有平台的内容、评论、创作者数据同步到Neo4j图数据库
"""

import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from neo4j import GraphDatabase
import pandas as pd
from sqlalchemy import create_engine, text

from config.semantic_config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE
from database.db import get_db_engine
from tools import utils

logger = logging.getLogger(__name__)


class Neo4jSyncService:
    """Neo4j数据同步服务"""
    
    def __init__(self, neo4j_driver=None):
        """
        初始化同步服务
        Args:
            neo4j_driver: Neo4j驱动实例，如果为None则自动创建
        """
        self.neo4j_driver = neo4j_driver or self._init_neo4j_driver()
        self.db_engine = get_db_engine()
        
    def _init_neo4j_driver(self):
        """初始化Neo4j驱动"""
        if not NEO4J_URI or not NEO4J_USER or not NEO4J_PASSWORD:
            logger.warning("Neo4j配置不完整，跳过Neo4j同步")
            return None
        
        try:
            driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            with driver.session(database=NEO4J_DATABASE) as session:
                session.run("RETURN 1 AS ok")
            logger.info("Neo4j连接成功")
            return driver
        except Exception as e:
            logger.error(f"Neo4j连接失败: {e}")
            return None
    
    def sync_all_platforms(self, batch_size: int = 100):
        """
        同步所有平台的数据到Neo4j
        Args:
            batch_size: 批处理大小
        """
        if not self.neo4j_driver:
            logger.warning("Neo4j未连接，跳过同步")
            return
        
        logger.info("开始同步所有平台数据到Neo4j...")
        
        # 同步各平台数据
        platforms = ['bilibili', 'douyin', 'kuaishou', 'weibo', 'xhs', 'zhihu']
        
        for platform in platforms:
            try:
                logger.info(f"同步 {platform} 平台数据...")
                self.sync_platform(platform, batch_size)
            except Exception as e:
                logger.error(f"同步 {platform} 平台数据失败: {e}")
        
        logger.info("所有平台数据同步完成")
    
    def sync_platform(self, platform: str, batch_size: int = 100):
        """
        同步指定平台的数据
        Args:
            platform: 平台名称 (bilibili, douyin, kuaishou, weibo, xhs, zhihu)
            batch_size: 批处理大小
        """
        if not self.neo4j_driver:
            return
        
        # 同步内容数据
        self.sync_content(platform, batch_size)
        
        # 同步评论数据
        self.sync_comments(platform, batch_size)
        
        # 同步创作者数据
        self.sync_creators(platform, batch_size)
    
    def sync_content(self, platform: str, batch_size: int = 100):
        """同步内容数据（视频/笔记）"""
        platform_config = {
            'bilibili': {
                'table': 'bilibili_video',
                'id_field': 'video_id',
                'title_field': 'title',
                'user_id_field': 'user_id',
                'nickname_field': 'nickname',
                'time_field': 'create_time',
                'node_type': 'Video',
                'platform_label': 'Bilibili'
            },
            'douyin': {
                'table': 'douyin_aweme',
                'id_field': 'aweme_id',
                'title_field': 'title',
                'user_id_field': 'user_id',
                'nickname_field': 'nickname',
                'time_field': 'create_time',
                'node_type': 'Video',
                'platform_label': 'Douyin'
            },
            'kuaishou': {
                'table': 'kuaishou_video',
                'id_field': 'video_id',
                'title_field': 'title',
                'user_id_field': 'user_id',
                'nickname_field': 'nickname',
                'time_field': 'create_time',
                'node_type': 'Video',
                'platform_label': 'Kuaishou'
            },
            'weibo': {
                'table': 'weibo_note',
                'id_field': 'note_id',
                'title_field': 'content',
                'user_id_field': 'user_id',
                'nickname_field': 'nickname',
                'time_field': 'create_time',
                'node_type': 'Note',
                'platform_label': 'Weibo'
            },
            'xhs': {
                'table': 'xhs_note',
                'id_field': 'note_id',
                'title_field': 'title',
                'user_id_field': 'user_id',
                'nickname_field': 'nickname',
                'time_field': 'time',
                'node_type': 'Note',
                'platform_label': 'Xiaohongshu'
            },
            'zhihu': {
                'table': 'zhihu_content',
                'id_field': 'content_id',
                'title_field': 'title',
                'user_id_field': 'user_id',
                'nickname_field': 'user_nickname',
                'time_field': 'created_time',
                'node_type': 'Content',
                'platform_label': 'Zhihu'
            }
        }
        
        config = platform_config.get(platform)
        if not config:
            logger.warning(f"不支持的平台: {platform}")
            return
        
        try:
            query = f"""
            SELECT 
                {config['id_field']},
                {config['title_field']},
                {config['user_id_field']},
                {config['nickname_field']},
                {config['time_field']},
                source_keyword
            FROM {config['table']}
            WHERE {config['id_field']} IS NOT NULL
            LIMIT 10000
            """
            
            df = pd.read_sql(query, self.db_engine)
            
            if df.empty:
                logger.info(f"{platform} 平台无内容数据")
                return
            
            logger.info(f"同步 {platform} 平台 {len(df)} 条内容数据...")
            
            # 批量写入Neo4j
            with self.neo4j_driver.session(database=NEO4J_DATABASE) as session:
                for i in range(0, len(df), batch_size):
                    batch = df.iloc[i:i+batch_size]
                    payload = []
                    
                    for _, row in batch.iterrows():
                        content_id = str(row[config['id_field']])
                        title = str(row[config['title_field']])[:500] if pd.notna(row[config['title_field']]) else ""
                        user_id = str(row[config['user_id_field']]) if pd.notna(row[config['user_id_field']]) else ""
                        nickname = str(row[config['nickname_field']])[:200] if pd.notna(row[config['nickname_field']]) else ""
                        create_time = int(row[config['time_field']]) if pd.notna(row[config['time_field']]) else int(time.time())
                        source_keyword = str(row['source_keyword']) if pd.notna(row.get('source_keyword')) else ""
                        
                        payload.append({
                            'content_id': f"{platform}:{content_id}",
                            'original_id': content_id,
                            'platform': platform,
                            'platform_label': config['platform_label'],
                            'node_type': config['node_type'],
                            'title': title,
                            'user_id': user_id,
                            'nickname': nickname,
                            'create_time': create_time,
                            'source_keyword': source_keyword
                        })
                    
                    session.execute_write(self._upsert_content_batch, payload)
                    
            logger.info(f"{platform} 平台内容数据同步完成")
            
        except Exception as e:
            logger.error(f"同步 {platform} 平台内容数据失败: {e}")
    
    def sync_comments(self, platform: str, batch_size: int = 100):
        """同步评论数据"""
        platform_config = {
            'bilibili': {
                'table': 'bilibili_video_comment',
                'id_field': 'comment_id',
                'content_id_field': 'video_id',
                'user_id_field': 'user_id',
                'nickname_field': 'nickname',
                'time_field': 'create_time'
            },
            'douyin': {
                'table': 'douyin_aweme_comment',
                'id_field': 'comment_id',
                'content_id_field': 'aweme_id',
                'user_id_field': 'user_id',
                'nickname_field': 'nickname',
                'time_field': 'create_time'
            },
            'kuaishou': {
                'table': 'kuaishou_video_comment',
                'id_field': 'comment_id',
                'content_id_field': 'video_id',
                'user_id_field': 'user_id',
                'nickname_field': 'nickname',
                'time_field': 'create_time'
            },
            'weibo': {
                'table': 'weibo_note_comment',
                'id_field': 'comment_id',
                'content_id_field': 'note_id',
                'user_id_field': 'user_id',
                'nickname_field': 'nickname',
                'time_field': 'create_time'
            },
            'xhs': {
                'table': 'xhs_note_comment',
                'id_field': 'comment_id',
                'content_id_field': 'note_id',
                'user_id_field': 'user_id',
                'nickname_field': 'nickname',
                'time_field': 'create_time'
            },
            'zhihu': {
                'table': 'zhihu_comment',
                'id_field': 'comment_id',
                'content_id_field': 'content_id',
                'user_id_field': 'user_id',
                'nickname_field': 'user_nickname',
                'time_field': 'publish_time'
            }
        }
        
        config = platform_config.get(platform)
        if not config:
            logger.warning(f"不支持的平台: {platform}")
            return
        
        try:
            query = f"""
            SELECT 
                {config['id_field']},
                {config['content_id_field']},
                content,
                {config['user_id_field']},
                {config['nickname_field']},
                {config['time_field']}
            FROM {config['table']}
            WHERE {config['id_field']} IS NOT NULL
            LIMIT 10000
            """
            
            df = pd.read_sql(query, self.db_engine)
            
            if df.empty:
                logger.info(f"{platform} 平台无评论数据")
                return
            
            logger.info(f"同步 {platform} 平台 {len(df)} 条评论数据...")
            
            # 批量写入Neo4j
            with self.neo4j_driver.session(database=NEO4J_DATABASE) as session:
                for i in range(0, len(df), batch_size):
                    batch = df.iloc[i:i+batch_size]
                    payload = []
                    
                    for _, row in batch.iterrows():
                        comment_id = str(row[config['id_field']])
                        content_id = str(row[config['content_id_field']])
                        content = str(row['content'])[:1000] if pd.notna(row['content']) else ""
                        user_id = str(row[config['user_id_field']]) if pd.notna(row[config['user_id_field']]) else ""
                        nickname = str(row[config['nickname_field']])[:200] if pd.notna(row[config['nickname_field']]) else ""
                        create_time = int(row[config['time_field']]) if pd.notna(row[config['time_field']]) else int(time.time())
                        
                        payload.append({
                            'comment_id': f"{platform}:{comment_id}",
                            'original_comment_id': comment_id,
                            'content_id': f"{platform}:{content_id}",
                            'original_content_id': content_id,
                            'platform': platform,
                            'content': content,
                            'user_id': user_id,
                            'nickname': nickname,
                            'create_time': create_time
                        })
                    
                    session.execute_write(self._upsert_comment_batch, payload)
                    
            logger.info(f"{platform} 平台评论数据同步完成")
            
        except Exception as e:
            logger.error(f"同步 {platform} 平台评论数据失败: {e}")
    
    def sync_creators(self, platform: str, batch_size: int = 100):
        """同步创作者数据"""
        platform_config = {
            'bilibili': {
                'table': 'bilibili_up_info',
                'id_field': 'user_id',
                'nickname_field': 'nickname'
            },
            'douyin': {
                'table': 'dy_creator',
                'id_field': 'user_id',
                'nickname_field': 'nickname'
            },
            'weibo': {
                'table': 'weibo_creator',
                'id_field': 'user_id',
                'nickname_field': 'nickname'
            },
            'xhs': {
                'table': 'xhs_creator',
                'id_field': 'user_id',
                'nickname_field': 'nickname'
            },
            'zhihu': {
                'table': 'zhihu_creator',
                'id_field': 'user_id',
                'nickname_field': 'user_nickname'
            }
        }
        
        config = platform_config.get(platform)
        if not config:
            logger.info(f"{platform} 平台无创作者表，跳过")
            return
        
        try:
            query = f"""
            SELECT 
                {config['id_field']},
                {config['nickname_field']},
                fans,
                follows
            FROM {config['table']}
            WHERE {config['id_field']} IS NOT NULL
            LIMIT 5000
            """
            
            df = pd.read_sql(query, self.db_engine)
            
            if df.empty:
                logger.info(f"{platform} 平台无创作者数据")
                return
            
            logger.info(f"同步 {platform} 平台 {len(df)} 条创作者数据...")
            
            # 批量写入Neo4j
            with self.neo4j_driver.session(database=NEO4J_DATABASE) as session:
                for i in range(0, len(df), batch_size):
                    batch = df.iloc[i:i+batch_size]
                    payload = []
                    
                    for _, row in batch.iterrows():
                        user_id = str(row[config['id_field']])
                        nickname = str(row[config['nickname_field']])[:200] if pd.notna(row[config['nickname_field']]) else ""
                        fans = str(row.get('fans', '')) if pd.notna(row.get('fans')) else "0"
                        follows = str(row.get('follows', '')) if pd.notna(row.get('follows')) else "0"
                        
                        payload.append({
                            'user_id': f"{platform}:{user_id}",
                            'original_user_id': user_id,
                            'platform': platform,
                            'nickname': nickname,
                            'fans': fans,
                            'follows': follows
                        })
                    
                    session.execute_write(self._upsert_creator_batch, payload)
                    
            logger.info(f"{platform} 平台创作者数据同步完成")
            
        except Exception as e:
            logger.error(f"同步 {platform} 平台创作者数据失败: {e}")
    
    @staticmethod
    def _upsert_content_batch(tx, payload: List[Dict]):
        """批量写入内容节点"""
        query = """
        UNWIND $batch AS row
        MERGE (c:Content {content_id: row.content_id})
        ON CREATE SET
            c.original_id = row.original_id,
            c.platform = row.platform,
            c.platform_label = row.platform_label,
            c.node_type = row.node_type,
            c.title = row.title,
            c.user_id = row.user_id,
            c.nickname = row.nickname,
            c.create_time = row.create_time,
            c.source_keyword = row.source_keyword,
            c.first_synced_at = timestamp()
        ON MATCH SET
            c.last_synced_at = timestamp(),
            c.title = row.title,
            c.nickname = row.nickname
        
        // 创建或关联创作者节点
        MERGE (u:Creator {user_id: row.user_id, platform: row.platform})
        ON CREATE SET
            u.nickname = row.nickname,
            u.platform = row.platform,
            u.first_seen_at = timestamp()
        ON MATCH SET
            u.nickname = row.nickname,
            u.last_seen_at = timestamp()
        
        // 创建关系
        MERGE (u)-[:CREATED]->(c)
        
        // 如果有关键词，创建关键词节点
        FOREACH (keyword IN CASE WHEN row.source_keyword <> '' THEN [row.source_keyword] ELSE [] END |
            MERGE (k:Keyword {name: keyword})
            MERGE (c)-[:HAS_KEYWORD]->(k)
        )
        """
        tx.run(query, batch=payload)
    
    @staticmethod
    def _upsert_comment_batch(tx, payload: List[Dict]):
        """批量写入评论节点和关系"""
        query = """
        UNWIND $batch AS row
        MERGE (cmt:Comment {comment_id: row.comment_id})
        ON CREATE SET
            cmt.original_comment_id = row.original_comment_id,
            cmt.platform = row.platform,
            cmt.content = row.content,
            cmt.user_id = row.user_id,
            cmt.nickname = row.nickname,
            cmt.create_time = row.create_time,
            cmt.first_synced_at = timestamp()
        ON MATCH SET
            cmt.last_synced_at = timestamp(),
            cmt.content = row.content
        
        // 关联到内容节点
        MERGE (c:Content {content_id: row.content_id})
        MERGE (cmt)-[:COMMENTS_ON]->(c)
        
        // 创建或关联评论者节点
        MERGE (u:User {user_id: row.user_id, platform: row.platform})
        ON CREATE SET
            u.nickname = row.nickname,
            u.platform = row.platform,
            u.first_seen_at = timestamp()
        ON MATCH SET
            u.nickname = row.nickname,
            u.last_seen_at = timestamp()
        
        MERGE (u)-[:WROTE]->(cmt)
        """
        tx.run(query, batch=payload)
    
    @staticmethod
    def _upsert_creator_batch(tx, payload: List[Dict]):
        """批量写入创作者节点"""
        query = """
        UNWIND $batch AS row
        MERGE (c:Creator {user_id: row.user_id})
        ON CREATE SET
            c.original_user_id = row.original_user_id,
            c.platform = row.platform,
            c.nickname = row.nickname,
            c.fans = row.fans,
            c.follows = row.follows,
            c.first_synced_at = timestamp()
        ON MATCH SET
            c.last_synced_at = timestamp(),
            c.nickname = row.nickname,
            c.fans = row.fans,
            c.follows = row.follows
        """
        tx.run(query, batch=payload)
    
    def close(self):
        """关闭Neo4j连接"""
        if self.neo4j_driver:
            self.neo4j_driver.close()


def sync_all_to_neo4j(batch_size: int = 100):
    """
    同步所有平台数据到Neo4j的主函数
    Args:
        batch_size: 批处理大小
    """
    service = Neo4jSyncService()
    try:
        service.sync_all_platforms(batch_size)
    finally:
        service.close()


if __name__ == "__main__":
    # 直接运行此脚本可以同步所有数据
    sync_all_to_neo4j()

