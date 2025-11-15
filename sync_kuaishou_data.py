# -*- coding: utf-8 -*-
# @Author  : MediaCrawler Team
# @Time    : 2025/01/XX
# @Desc    : 将快手 JSON文件数据同步到数据库，用于Dashboard显示

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
    KuaishouVideo,
    KuaishouVideoComment,
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


async def sync_videos(video_data: List[Dict], db_type: str = None):
    """同步视频数据到数据库"""
    if not video_data:
        return
    
    utils.logger.info(f"开始同步 {len(video_data)} 条视频数据...")
    
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
            
            for item in video_data:
                try:
                    video_id = item.get("video_id")
                    if not video_id:
                        continue
                    
                    # 检查是否已存在
                    result = await session.execute(
                        select(KuaishouVideo).where(KuaishouVideo.video_id == str(video_id))
                    )
                    video_detail = result.scalar_one_or_none()
                    
                    # 准备数据，确保字段匹配
                    video_data_dict = {
                        "video_id": str(video_id),
                        "video_type": str(item.get("video_type", "")),
                        "title": str(item.get("title", ""))[:500] if item.get("title") else "",
                        "desc": str(item.get("desc", ""))[:500] if item.get("desc") else "",
                        "create_time": int(item.get("create_time", 0)) if item.get("create_time") else None,
                        "user_id": str(item.get("user_id", "")),
                        "nickname": str(item.get("nickname", "")) if item.get("nickname") else "",
                        "avatar": str(item.get("avatar", "")) if item.get("avatar") else "",
                        "liked_count": str(item.get("liked_count", "0")),
                        "viewd_count": str(item.get("viewd_count", "0")),
                        "video_url": str(item.get("video_url", "")),
                        "video_cover_url": str(item.get("video_cover_url", "")),
                        "video_play_url": str(item.get("video_play_url", "")),
                        "source_keyword": str(item.get("source_keyword", "")),
                        "add_ts": int(datetime.now().timestamp()),
                        "last_modify_ts": int(datetime.now().timestamp()),
                    }
                    
                    if video_detail:
                        # 更新现有记录
                        for key, value in video_data_dict.items():
                            if key not in ["video_id"]:  # 不更新主键
                                setattr(video_detail, key, value)
                        skip_count += 1
                    else:
                        # 创建新记录
                        video_detail = KuaishouVideo(**video_data_dict)
                        session.add(video_detail)
                        success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    utils.logger.error(f"同步视频数据失败 {item.get('video_id', 'unknown')}: {e}")
                    continue
            
            await session.commit()
            utils.logger.info(f"✅ 视频数据同步完成: 新增 {success_count} 条, 更新 {skip_count} 条, 错误 {error_count} 条")
            
    except Exception as e:
        utils.logger.error(f"同步视频数据时发生错误: {e}")
        import traceback
        utils.logger.error(traceback.format_exc())
    finally:
        if original_option:
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
                        select(KuaishouVideoComment).where(KuaishouVideoComment.comment_id == int(comment_id))
                    )
                    comment_detail = result.scalar_one_or_none()
                    
                    # 准备数据
                    comment_data_dict = {
                        "comment_id": int(comment_id) if comment_id else None,
                        "video_id": str(item.get("video_id", "")),
                        "content": str(item.get("content", "")) if item.get("content") else "",
                        "create_time": int(item.get("create_time", 0)) if item.get("create_time") else None,
                        "user_id": str(item.get("user_id", "")) if item.get("user_id") else "",
                        "nickname": str(item.get("nickname", "")) if item.get("nickname") else "",
                        "avatar": str(item.get("avatar", "")) if item.get("avatar") else "",
                        "sub_comment_count": str(item.get("sub_comment_count", "0")),
                        "add_ts": int(datetime.now().timestamp()),
                        "last_modify_ts": int(datetime.now().timestamp()),
                    }
                    
                    if comment_detail:
                        # 更新现有记录
                        for key, value in comment_data_dict.items():
                            if key not in ["comment_id"]:  # 不更新主键
                                setattr(comment_detail, key, value)
                        skip_count += 1
                    else:
                        # 创建新记录
                        comment_detail = KuaishouVideoComment(**comment_data_dict)
                        session.add(comment_detail)
                        success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    utils.logger.error(f"同步评论数据失败 {item.get('comment_id', 'unknown')}: {e}")
                    continue
            
            await session.commit()
            utils.logger.info(f"✅ 评论数据同步完成: 新增 {success_count} 条, 更新 {skip_count} 条, 错误 {error_count} 条")
            
    except Exception as e:
        utils.logger.error(f"同步评论数据时发生错误: {e}")
        import traceback
        utils.logger.error(traceback.format_exc())
    finally:
        if original_option:
            config.SAVE_DATA_OPTION = original_option


async def sync_all_kuaishou_data(data_dir: str = None, db_type: str = None):
    """
    同步所有快手 JSON文件数据到数据库
    
    Args:
        data_dir: 数据目录路径，默认为 data/kuaishou/json
        db_type: 数据库类型，默认为配置文件中的SAVE_DATA_OPTION
    """
    if data_dir is None:
        data_dir = os.path.join(project_root, "data", "kuaishou", "json")
    
    if not os.path.exists(data_dir):
        utils.logger.error(f"数据目录不存在: {data_dir}")
        return
    
    utils.logger.info(f"开始同步快手数据，数据目录: {data_dir}")
    
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
    }
    
    for file in os.listdir(data_dir):
        if file.endswith(".json"):
            file_path = os.path.join(data_dir, file)
            if "content" in file.lower() or "video" in file.lower():
                json_files["contents"].append(file_path)
            elif "comment" in file.lower():
                json_files["comments"].append(file_path)
    
    # 同步视频数据
    for file_path in json_files["contents"]:
        utils.logger.info(f"处理视频文件: {file_path}")
        video_data = await load_json_file(file_path)
        if video_data:
            await sync_videos(video_data, db_type)
    
    # 同步评论数据
    for file_path in json_files["comments"]:
        utils.logger.info(f"处理评论文件: {file_path}")
        comment_data = await load_json_file(file_path)
        if comment_data:
            await sync_comments(comment_data, db_type)
    
    utils.logger.info("所有快手数据同步完成！")


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="将快手JSON文件数据同步到数据库")
    parser.add_argument("--data-dir", "-d", help="数据目录路径（默认: data/kuaishou/json）")
    parser.add_argument("--db-type", "-t", choices=["db", "mysql", "sqlite"], 
                        help="数据库类型（db/mysql=MySQL, sqlite=SQLite）")
    
    args = parser.parse_args()
    
    try:
        await sync_all_kuaishou_data(data_dir=args.data_dir, db_type=args.db_type)
        print("\n✅ 同步完成！")
        print("💡 现在可以在Dashboard中查看快手数据了")
    except Exception as e:
        utils.logger.error(f"同步失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

