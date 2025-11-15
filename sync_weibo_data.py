# -*- coding: utf-8 -*-
# @Author  : MediaCrawler Team
# @Time    : 2025/01/XX
# @Desc    : 将微博 JSON文件数据同步到数据库，用于Dashboard显示

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, List
from datetime import datetime

# 添加项目根目录到sys.path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from sqlalchemy import select
from database.db_session import get_session, get_async_engine
from database.models import (
    WeiboNote,
    WeiboNoteComment,
    WeiboCreator,
)
from tools import utils
import config
from config.db_config import mysql_db_config, sqlite_db_config


async def load_json_file(file_path: str) -> List[Dict]:
    """加载JSON文件"""
    if not os.path.exists(file_path):
        utils.logger.warning(f"文件不存在: {file_path}")
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return [data]
            else:
                return []
    except json.JSONDecodeError as e:
        utils.logger.error(f"JSON解析错误 {file_path}: {e}")
        return []
    except Exception as e:
        utils.logger.error(f"读取文件错误 {file_path}: {e}")
        return []


async def sync_notes(note_data: List[Dict], db_type: str = None):
    """同步微博数据到数据库"""
    if not note_data:
        return
    
    utils.logger.info(f"开始同步 {len(note_data)} 条微博数据...")
    
    # 设置数据库类型
    original_option = None
    if db_type:
        original_option = config.SAVE_DATA_OPTION
        config.SAVE_DATA_OPTION = db_type
    
    try:
        from database.db_session import get_async_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.ext.asyncio import AsyncSession
        
        engine = get_async_engine(db_type)
        if not engine:
            utils.logger.error("无法获取数据库引擎，请检查数据库配置")
            return
        
        AsyncSessionFactory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with AsyncSessionFactory() as session:
            success_count = 0
            skip_count = 0
            error_count = 0
            
            for item in note_data:
                try:
                    note_id = item.get("note_id")
                    if not note_id:
                        continue
                    
                    # 检查是否已存在
                    result = await session.execute(
                        select(WeiboNote).where(WeiboNote.note_id == int(note_id))
                    )
                    note_detail = result.scalar_one_or_none()
                    
                    # 准备数据，确保字段匹配
                    note_data_dict = {
                        "note_id": int(note_id) if note_id else None,
                        "user_id": str(item.get("user_id", "")),
                        "nickname": item.get("nickname", ""),
                        "avatar": item.get("avatar", ""),
                        "gender": item.get("gender", ""),
                        "profile_url": item.get("profile_url", ""),
                        "ip_location": item.get("ip_location", ""),
                        "content": item.get("content", ""),
                        "create_time": item.get("create_time"),
                        "create_date_time": item.get("create_date_time", ""),
                        "liked_count": str(item.get("liked_count", "0")),
                        "comments_count": str(item.get("comments_count", "0")),
                        "shared_count": str(item.get("shared_count", "0")),
                        "note_url": item.get("note_url", ""),
                        "source_keyword": item.get("source_keyword", ""),
                        "add_ts": item.get("add_ts") or utils.get_current_timestamp(),
                        "last_modify_ts": item.get("last_modify_ts") or utils.get_current_timestamp(),
                    }
                    
                    if not note_detail:
                        # 新增
                        new_note = WeiboNote(**note_data_dict)
                        session.add(new_note)
                        success_count += 1
                    else:
                        # 更新
                        for key, value in note_data_dict.items():
                            if key != "add_ts":  # 保留原始的add_ts
                                setattr(note_detail, key, value)
                        skip_count += 1
                    
                except Exception as e:
                    utils.logger.error(f"同步微博数据错误 (note_id: {item.get('note_id')}): {e}")
                    error_count += 1
                    continue
            
            await session.commit()
            utils.logger.info(f"微博数据同步完成: 新增 {success_count} 条, 跳过 {skip_count} 条, 错误 {error_count} 条")
    
    finally:
        if db_type:
            config.SAVE_DATA_OPTION = original_option


async def sync_comments(comment_data: List[Dict], db_type: str = None):
    """同步评论数据到数据库"""
    if not comment_data:
        return
    
    utils.logger.info(f"开始同步 {len(comment_data)} 条评论数据...")
    
    # 设置数据库类型
    original_option = None
    if db_type:
        original_option = config.SAVE_DATA_OPTION
        config.SAVE_DATA_OPTION = db_type
    
    try:
        from database.db_session import get_async_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.ext.asyncio import AsyncSession
        
        engine = get_async_engine(db_type)
        if not engine:
            utils.logger.error("无法获取数据库引擎，请检查数据库配置")
            return
        
        AsyncSessionFactory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with AsyncSessionFactory() as session:
            success_count = 0
            skip_count = 0
            error_count = 0
            
            for item in comment_data:
                try:
                    comment_id = item.get("comment_id")
                    if not comment_id:
                        continue
                    
                    # 检查是否已存在
                    result = await session.execute(
                        select(WeiboNoteComment).where(WeiboNoteComment.comment_id == int(comment_id))
                    )
                    comment_detail = result.scalar_one_or_none()
                    
                    # 准备数据
                    comment_data_dict = {
                        "comment_id": int(comment_id) if comment_id else None,
                        "note_id": int(item.get("note_id", 0)) if item.get("note_id") else None,
                        "user_id": str(item.get("user_id", "")),
                        "nickname": item.get("nickname", ""),
                        "avatar": item.get("avatar", ""),
                        "gender": item.get("gender", ""),
                        "profile_url": item.get("profile_url", ""),
                        "ip_location": item.get("ip_location", ""),
                        "content": item.get("content", ""),
                        "create_time": item.get("create_time"),
                        "create_date_time": item.get("create_date_time", ""),
                        "comment_like_count": str(item.get("comment_like_count", "0")),
                        "sub_comment_count": str(item.get("sub_comment_count", "0")),
                        "parent_comment_id": str(item.get("parent_comment_id", "")),
                        "add_ts": item.get("add_ts") or utils.get_current_timestamp(),
                        "last_modify_ts": item.get("last_modify_ts") or utils.get_current_timestamp(),
                    }
                    
                    if not comment_detail:
                        # 新增
                        new_comment = WeiboNoteComment(**comment_data_dict)
                        session.add(new_comment)
                        success_count += 1
                    else:
                        # 更新
                        for key, value in comment_data_dict.items():
                            if key != "add_ts":
                                setattr(comment_detail, key, value)
                        skip_count += 1
                    
                except Exception as e:
                    utils.logger.error(f"同步评论数据错误 (comment_id: {item.get('comment_id')}): {e}")
                    error_count += 1
                    continue
            
            await session.commit()
            utils.logger.info(f"评论数据同步完成: 新增 {success_count} 条, 跳过 {skip_count} 条, 错误 {error_count} 条")
    
    finally:
        if db_type:
            config.SAVE_DATA_OPTION = original_option


async def sync_creators(creator_data: List[Dict], db_type: str = None):
    """同步创作者数据到数据库"""
    if not creator_data:
        return
    
    utils.logger.info(f"开始同步 {len(creator_data)} 条创作者数据...")
    
    # 设置数据库类型
    original_option = None
    if db_type:
        original_option = config.SAVE_DATA_OPTION
        config.SAVE_DATA_OPTION = db_type
    
    try:
        from database.db_session import get_async_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.ext.asyncio import AsyncSession
        
        engine = get_async_engine(db_type)
        if not engine:
            utils.logger.error("无法获取数据库引擎，请检查数据库配置")
            return
        
        AsyncSessionFactory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with AsyncSessionFactory() as session:
            success_count = 0
            skip_count = 0
            error_count = 0
            
            for item in creator_data:
                try:
                    user_id = item.get("user_id")
                    if not user_id:
                        continue
                    
                    # 检查是否已存在
                    result = await session.execute(
                        select(WeiboCreator).where(WeiboCreator.user_id == str(user_id))
                    )
                    creator_detail = result.scalar_one_or_none()
                    
                    # 准备数据
                    creator_data_dict = {
                        "user_id": str(user_id) if user_id else None,
                        "nickname": item.get("nickname", ""),
                        "avatar": item.get("avatar", ""),
                        "gender": item.get("gender", ""),
                        "desc": item.get("desc", ""),
                        "ip_location": item.get("ip_location", ""),
                        "follows": str(item.get("follows", "")),
                        "fans": str(item.get("fans", "")),
                        "tag_list": item.get("tag_list", ""),
                        "add_ts": item.get("add_ts") or utils.get_current_timestamp(),
                        "last_modify_ts": item.get("last_modify_ts") or utils.get_current_timestamp(),
                    }
                    
                    if not creator_detail:
                        # 新增
                        new_creator = WeiboCreator(**creator_data_dict)
                        session.add(new_creator)
                        success_count += 1
                    else:
                        # 更新
                        for key, value in creator_data_dict.items():
                            if key != "add_ts":
                                setattr(creator_detail, key, value)
                        skip_count += 1
                    
                except Exception as e:
                    utils.logger.error(f"同步创作者数据错误 (user_id: {item.get('user_id')}): {e}")
                    error_count += 1
                    continue
            
            await session.commit()
            utils.logger.info(f"创作者数据同步完成: 新增 {success_count} 条, 跳过 {skip_count} 条, 错误 {error_count} 条")
    
    finally:
        if db_type:
            config.SAVE_DATA_OPTION = original_option


async def sync_all_weibo_data(data_dir: str = None, db_type: str = None):
    """
    同步所有微博 JSON文件数据到数据库
    
    Args:
        data_dir: 数据目录路径，默认为 data/weibo/json
        db_type: 数据库类型，默认为配置文件中的SAVE_DATA_OPTION
    """
    if data_dir is None:
        data_dir = os.path.join(project_root, "data", "weibo", "json")
    
    if not os.path.exists(data_dir):
        utils.logger.error(f"数据目录不存在: {data_dir}")
        return
    
    utils.logger.info(f"开始同步微博数据，数据目录: {data_dir}")
    
    # 如果没有指定数据库类型，使用配置文件中的
    if db_type is None:
        db_type = config.SAVE_DATA_OPTION
    
    # 确保数据库类型不是json或csv
    if db_type in ["json", "csv"]:
        utils.logger.warning("当前配置的存储类型为json或csv，无法同步到数据库。请使用 --db-type 参数指定数据库类型（sqlite或db）")
        return
    
    # 初始化数据库表
    from database.db import init_db
    await init_db(db_type)
    utils.logger.info(f"数据库 {db_type} 初始化完成")
    
    # 查找所有JSON文件
    json_files = {
        "contents": [],
        "comments": [],
        "creators": [],
    }
    
    for file in os.listdir(data_dir):
        if file.endswith(".json"):
            file_path = os.path.join(data_dir, file)
            if "content" in file.lower() or "note" in file.lower():
                json_files["contents"].append(file_path)
            elif "comment" in file.lower():
                json_files["comments"].append(file_path)
            elif "creator" in file.lower():
                json_files["creators"].append(file_path)
    
    # 同步微博数据
    for file_path in json_files["contents"]:
        utils.logger.info(f"处理微博文件: {file_path}")
        note_data = await load_json_file(file_path)
        await sync_notes(note_data, db_type)
    
    # 同步评论数据
    for file_path in json_files["comments"]:
        utils.logger.info(f"处理评论文件: {file_path}")
        comment_data = await load_json_file(file_path)
        await sync_comments(comment_data, db_type)
    
    # 同步创作者数据
    for file_path in json_files["creators"]:
        utils.logger.info(f"处理创作者文件: {file_path}")
        creator_data = await load_json_file(file_path)
        await sync_creators(creator_data, db_type)
    
    utils.logger.info("所有微博数据同步完成！")


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="将微博 JSON文件数据同步到数据库")
    parser.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help="数据目录路径，默认为 data/weibo/json"
    )
    parser.add_argument(
        "--db-type",
        type=str,
        choices=["sqlite", "db", "mysql"],
        default=None,
        help="数据库类型：sqlite 或 db/mysql，默认使用配置文件中的SAVE_DATA_OPTION"
    )
    
    args = parser.parse_args()
    
    try:
        await sync_all_weibo_data(data_dir=args.data_dir, db_type=args.db_type)
        print("✅ 数据同步完成！")
    except Exception as e:
        utils.logger.error(f"同步过程出错: {e}")
        import traceback
        traceback.print_exc()
        print("❌ 数据同步失败！")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

