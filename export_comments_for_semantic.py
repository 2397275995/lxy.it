# -*- coding: utf-8 -*-
"""
从MySQL数据库导出评论数据为JSON文件，用于语义处理流水线
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到sys.path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

import pandas as pd
from database.db import get_db_engine
from tools import utils


def export_bilibili_comments(output_file: str = None, limit: int = None):
    """从MySQL数据库导出Bilibili评论数据为JSON文件"""
    
    engine = get_db_engine()
    if not engine:
        utils.logger.error("无法连接数据库，请检查数据库配置")
        return False
    
    try:
        # 构建查询
        query = """
        SELECT 
            comment_id,
            content,
            create_time,
            user_id,
            nickname,
            like_count,
            video_id
        FROM bilibili_video_comment
        WHERE content IS NOT NULL 
        AND content != ''
        ORDER BY create_time DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        utils.logger.info("正在从数据库读取评论数据...")
        df = pd.read_sql(query, engine)
        
        if df.empty:
            utils.logger.warning("数据库中没有找到评论数据")
            return False
        
        utils.logger.info(f"找到 {len(df)} 条评论数据")
        
        # 转换为JSON格式
        comments = []
        for _, row in df.iterrows():
            comment = {
                "comment_id": str(row['comment_id']) if pd.notna(row['comment_id']) else None,
                "content": str(row['content']) if pd.notna(row['content']) else "",
                "create_time": int(row['create_time']) if pd.notna(row['create_time']) else None,
                "user_id": str(row['user_id']) if pd.notna(row['user_id']) else None,
                "nickname": str(row['nickname']) if pd.notna(row['nickname']) else None,
                "like_count": str(row['like_count']) if pd.notna(row['like_count']) else "0",
                "video_id": str(row['video_id']) if pd.notna(row['video_id']) else None,
            }
            comments.append(comment)
        
        # 确定输出文件路径
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path("data/bili/json")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"search_comments_{timestamp}.json"
        else:
            output_file = Path(output_file)
            output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存为JSON文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(comments, f, ensure_ascii=False, indent=2)
        
        utils.logger.info(f"✅ 成功导出 {len(comments)} 条评论到: {output_file}")
        return str(output_file)
        
    except Exception as e:
        utils.logger.error(f"导出评论数据失败: {e}")
        import traceback
        utils.logger.error(traceback.format_exc())
        return False


def export_weibo_comments(output_file: str = None, limit: int = None):
    """从MySQL数据库导出微博评论数据为JSON文件"""
    
    engine = get_db_engine()
    if not engine:
        utils.logger.error("无法连接数据库，请检查数据库配置")
        return False
    
    try:
        # 构建查询
        query = """
        SELECT 
            comment_id,
            content,
            create_time,
            user_id,
            nickname,
            comment_like_count,
            note_id
        FROM weibo_note_comment
        WHERE content IS NOT NULL 
        AND content != ''
        ORDER BY create_time DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        utils.logger.info("正在从数据库读取微博评论数据...")
        df = pd.read_sql(query, engine)
        
        if df.empty:
            utils.logger.warning("数据库中没有找到微博评论数据")
            return False
        
        utils.logger.info(f"找到 {len(df)} 条微博评论数据")
        
        # 转换为JSON格式
        comments = []
        for _, row in df.iterrows():
            comment = {
                "comment_id": str(row['comment_id']) if pd.notna(row['comment_id']) else None,
                "content": str(row['content']) if pd.notna(row['content']) else "",
                "create_time": int(row['create_time']) if pd.notna(row['create_time']) else None,
                "user_id": str(row['user_id']) if pd.notna(row['user_id']) else None,
                "nickname": str(row['nickname']) if pd.notna(row['nickname']) else None,
                "comment_like_count": str(row['comment_like_count']) if pd.notna(row['comment_like_count']) else "0",
                "note_id": str(row['note_id']) if pd.notna(row['note_id']) else None,
            }
            comments.append(comment)
        
        # 确定输出文件路径
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path("data/weibo/json")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"search_comments_{timestamp}.json"
        else:
            output_file = Path(output_file)
            output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存为JSON文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(comments, f, ensure_ascii=False, indent=2)
        
        utils.logger.info(f"✅ 成功导出 {len(comments)} 条微博评论到: {output_file}")
        return str(output_file)
        
    except Exception as e:
        utils.logger.error(f"导出微博评论数据失败: {e}")
        import traceback
        utils.logger.error(traceback.format_exc())
        return False


def export_douyin_comments(output_file: str = None, limit: int = None):
    """从MySQL数据库导出抖音评论数据为JSON文件"""
    
    engine = get_db_engine()
    if not engine:
        utils.logger.error("无法连接数据库，请检查数据库配置")
        return False
    
    try:
        # 构建查询
        query = """
        SELECT 
            comment_id,
            content,
            create_time,
            user_id,
            nickname,
            like_count,
            aweme_id
        FROM douyin_aweme_comment
        WHERE content IS NOT NULL 
        AND content != ''
        ORDER BY create_time DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        utils.logger.info("正在从数据库读取抖音评论数据...")
        df = pd.read_sql(query, engine)
        
        if df.empty:
            utils.logger.warning("数据库中没有找到抖音评论数据")
            return False
        
        utils.logger.info(f"找到 {len(df)} 条抖音评论数据")
        
        # 转换为JSON格式
        comments = []
        for _, row in df.iterrows():
            comment = {
                "comment_id": str(row['comment_id']) if pd.notna(row['comment_id']) else None,
                "content": str(row['content']) if pd.notna(row['content']) else "",
                "create_time": int(row['create_time']) if pd.notna(row['create_time']) else None,
                "user_id": str(row['user_id']) if pd.notna(row['user_id']) else None,
                "nickname": str(row['nickname']) if pd.notna(row['nickname']) else None,
                "like_count": str(row['like_count']) if pd.notna(row['like_count']) else "0",
                "aweme_id": str(row['aweme_id']) if pd.notna(row['aweme_id']) else None,
            }
            comments.append(comment)
        
        # 确定输出文件路径
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path("data/douyin/json")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"search_comments_{timestamp}.json"
        else:
            output_file = Path(output_file)
            output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存为JSON文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(comments, f, ensure_ascii=False, indent=2)
        
        utils.logger.info(f"✅ 成功导出 {len(comments)} 条抖音评论到: {output_file}")
        return str(output_file)
        
    except Exception as e:
        utils.logger.error(f"导出抖音评论数据失败: {e}")
        import traceback
        utils.logger.error(traceback.format_exc())
        return False


def export_kuaishou_comments(output_file: str = None, limit: int = None):
    """从MySQL数据库导出快手评论数据为JSON文件"""
    
    engine = get_db_engine()
    if not engine:
        utils.logger.error("无法连接数据库，请检查数据库配置")
        return False
    
    try:
        # 构建查询
        query = """
        SELECT 
            comment_id,
            content,
            create_time,
            user_id,
            nickname,
            video_id,
            sub_comment_count
        FROM kuaishou_video_comment
        WHERE content IS NOT NULL 
        AND content != ''
        ORDER BY create_time DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        utils.logger.info("正在从数据库读取快手评论数据...")
        df = pd.read_sql(query, engine)
        
        if df.empty:
            utils.logger.warning("数据库中没有找到快手评论数据")
            return False
        
        utils.logger.info(f"找到 {len(df)} 条快手评论数据")
        
        # 转换为JSON格式
        comments = []
        for _, row in df.iterrows():
            comment = {
                "comment_id": str(row['comment_id']) if pd.notna(row['comment_id']) else None,
                "content": str(row['content']) if pd.notna(row['content']) else "",
                "create_time": int(row['create_time']) if pd.notna(row['create_time']) else None,
                "user_id": str(row['user_id']) if pd.notna(row['user_id']) else None,
                "nickname": str(row['nickname']) if pd.notna(row['nickname']) else None,
                "video_id": str(row['video_id']) if pd.notna(row['video_id']) else None,
                "sub_comment_count": str(row['sub_comment_count']) if pd.notna(row['sub_comment_count']) else "0",
            }
            comments.append(comment)
        
        # 确定输出文件路径
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path("data/kuaishou/json")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"search_comments_{timestamp}.json"
        else:
            output_file = Path(output_file)
            output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存为JSON文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(comments, f, ensure_ascii=False, indent=2)
        
        utils.logger.info(f"✅ 成功导出 {len(comments)} 条快手评论到: {output_file}")
        return str(output_file)
        
    except Exception as e:
        utils.logger.error(f"导出快手评论数据失败: {e}")
        import traceback
        utils.logger.error(traceback.format_exc())
        return False


def export_tieba_comments(output_file: str = None, limit: int = None):
    """从MySQL数据库导出贴吧评论数据为JSON文件"""
    engine = get_db_engine()
    if not engine:
        utils.logger.error("无法连接数据库，请检查数据库配置")
        return False

    try:
        query = """
        SELECT
            comment_id,
            content,
            add_ts,
            user_nickname,
            note_id,
            tieba_name,
            sub_comment_count,
            publish_time
        FROM tieba_comment
        WHERE content IS NOT NULL
        AND content != ''
        ORDER BY add_ts DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        utils.logger.info("正在从数据库读取贴吧评论数据...")
        df = pd.read_sql(query, engine)

        if df.empty:
            utils.logger.warning("数据库中没有找到贴吧评论数据")
            return False

        utils.logger.info(f"找到 {len(df)} 条贴吧评论数据")

        comments = []
        for _, row in df.iterrows():
            # 处理时间戳，优先使用 add_ts，如果没有则使用 publish_time
            create_time_value = None
            if pd.notna(row.get('add_ts')):
                try:
                    create_time_value = int(row['add_ts'])
                except (ValueError, TypeError):
                    create_time_value = None
            elif pd.notna(row.get('publish_time')):
                try:
                    # 尝试解析发布时间字符串
                    create_time_value = int(pd.to_datetime(row['publish_time']).timestamp())
                except Exception:
                    create_time_value = None

            comment = {
                "comment_id": str(row['comment_id']) if pd.notna(row['comment_id']) else None,
                "content": str(row['content']) if pd.notna(row['content']) else "",
                "create_time": create_time_value,
                "user_id": None,  # 贴吧评论表没有 user_id 字段
                "nickname": str(row['user_nickname']) if pd.notna(row['user_nickname']) else None,
                "note_id": str(row['note_id']) if pd.notna(row['note_id']) else None,
                "tieba_name": str(row['tieba_name']) if pd.notna(row['tieba_name']) else None,
                "sub_comment_count": str(row['sub_comment_count']) if pd.notna(row['sub_comment_count']) else "0",
            }
            comments.append(comment)

        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path("data/tieba/json")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"search_comments_{timestamp}.json"
        else:
            output_file = Path(output_file)
            output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(comments, f, ensure_ascii=False, indent=2)

        utils.logger.info(f"✅ 成功导出 {len(comments)} 条贴吧评论到: {output_file}")
        return str(output_file)

    except Exception as e:
        utils.logger.error(f"导出贴吧评论数据失败: {e}")
        import traceback
        utils.logger.error(traceback.format_exc())
        return False


def export_zhihu_comments(output_file: str = None, limit: int = None):
    """从MySQL数据库导出知乎评论数据为JSON文件"""
    engine = get_db_engine()
    if not engine:
        utils.logger.error("无法连接数据库，请检查数据库配置")
        return False

    try:
        query = """
        SELECT
            comment_id,
            content,
            publish_time,
            user_id,
            user_nickname,
            like_count,
            content_id
        FROM zhihu_comment
        WHERE content IS NOT NULL
        AND content != ''
        ORDER BY publish_time DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        utils.logger.info("正在从数据库读取知乎评论数据...")
        df = pd.read_sql(query, engine)

        if df.empty:
            utils.logger.warning("数据库中没有找到知乎评论数据")
            return False

        utils.logger.info(f"找到 {len(df)} 条知乎评论数据")

        comments = []
        for _, row in df.iterrows():
            publish_time_value = None
            if pd.notna(row['publish_time']):
                try:
                    publish_time_value = int(row['publish_time'])
                except (ValueError, TypeError):
                    try:
                        publish_time_value = int(pd.to_datetime(row['publish_time']).timestamp())
                    except Exception:
                        publish_time_value = str(row['publish_time'])

            comment = {
                "comment_id": str(row['comment_id']) if pd.notna(row['comment_id']) else None,
                "content": str(row['content']) if pd.notna(row['content']) else "",
                "publish_time": publish_time_value,
                "user_id": str(row['user_id']) if pd.notna(row['user_id']) else None,
                "nickname": str(row['user_nickname']) if pd.notna(row['user_nickname']) else None,
                "like_count": str(row['like_count']) if pd.notna(row['like_count']) else "0",
                "content_id": str(row['content_id']) if pd.notna(row['content_id']) else None,
            }
            comments.append(comment)

        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path("data/zhihu/json")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"search_comments_{timestamp}.json"
        else:
            output_file = Path(output_file)
            output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(comments, f, ensure_ascii=False, indent=2)

        utils.logger.info(f"✅ 成功导出 {len(comments)} 条知乎评论到: {output_file}")
        return str(output_file)

    except Exception as e:
        utils.logger.error(f"导出知乎评论数据失败: {e}")
        import traceback
        utils.logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="从数据库导出评论数据为JSON文件")
    parser.add_argument("--platform", "-p", choices=["bilibili", "weibo", "douyin", "kuaishou", "zhihu", "tieba"], 
                        default="bilibili", help="平台类型（默认：bilibili）")
    parser.add_argument("--output", "-o", help="输出文件路径（可选，自动生成）")
    parser.add_argument("--limit", "-l", type=int, help="限制导出的评论数量（可选）")
    
    args = parser.parse_args()
    
    # 根据平台选择导出函数
    if args.platform == "bilibili":
        result = export_bilibili_comments(args.output, args.limit)
        platform_name = "bilibili"
    elif args.platform == "weibo":
        result = export_weibo_comments(args.output, args.limit)
        platform_name = "weibo"
    elif args.platform == "douyin":
        result = export_douyin_comments(args.output, args.limit)
        platform_name = "douyin"
    elif args.platform == "kuaishou":
        result = export_kuaishou_comments(args.output, args.limit)
        platform_name = "kuaishou"
    elif args.platform == "zhihu":
        result = export_zhihu_comments(args.output, args.limit)
        platform_name = "zhihu"
    elif args.platform == "tieba":
        result = export_tieba_comments(args.output, args.limit)
        platform_name = "tieba"
    else:
        print(f"❌ 不支持的平台: {args.platform}")
        sys.exit(1)
    
    if result:
        print(f"\n✅ 导出成功！")
        print(f"📁 文件位置: {result}")
        print(f"\n💡 下一步：运行语义处理流水线")
        print(f"   python run_semantic_pipeline.py {result} --platform {platform_name} --limit 10")
    else:
        print("\n❌ 导出失败，请检查错误信息")
        print(f"💡 可能的原因：")
        print(f"   1. 数据库中没有 {args.platform} 评论数据")
        print(f"   2. 数据库表不存在")
        print(f"   3. 数据库连接失败")
        sys.exit(1)

