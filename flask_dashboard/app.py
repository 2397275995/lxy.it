# -*- coding: utf-8 -*-
"""
Flask Dashboard Backend API
提供Dashboard所需的所有数据API接口
"""

from flask import Flask, jsonify, request, send_from_directory, render_template
from flask_cors import CORS
import pandas as pd
import json
from datetime import datetime, timedelta
from collections import Counter
import sys
from pathlib import Path
from sqlalchemy import text

# 添加项目根目录到sys.path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from database.db import get_db_engine
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE
from neo4j import GraphDatabase

# Flask应用配置
flask_dir = Path(__file__).parent
app = Flask(__name__, 
            static_folder=str(flask_dir / 'static'),
            template_folder=str(flask_dir / 'templates'))
CORS(app)  # 允许跨域请求

# 数据库连接缓存
_engine = None
_neo4j_driver = None


def get_engine():
    """获取数据库引擎（单例模式）"""
    global _engine
    if _engine is None:
        try:
            _engine = get_db_engine()
        except Exception as e:
            print(f"Database connection failed: {e}")
            return None
    return _engine


def get_neo4j_driver():
    """获取Neo4j驱动（单例模式）"""
    global _neo4j_driver
    if not NEO4J_URI or not NEO4J_USER or not NEO4J_PASSWORD:
        return None
    if _neo4j_driver is None:
        try:
            _neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            with _neo4j_driver.session(database=NEO4J_DATABASE) as session:
                session.run("RETURN 1 AS ok")
        except Exception as e:
            print(f"Neo4j connection failed: {e}")
            return None
    return _neo4j_driver


@app.route('/')
def index():
    """返回主页面"""
    return render_template('index.html')


@app.route('/api/overview', methods=['GET'])
def get_overview():
    """获取平台概览数据"""
    engine = get_engine()
    if not engine:
        return jsonify({'error': 'Database connection failed'}), 500
    
    platforms = {
        'Bilibili': ['bilibili_video', 'bilibili_video_comment', 'bilibili_up_info'],
        'Douyin': ['douyin_aweme', 'douyin_aweme_comment', 'dy_creator'],
        'Kuaishou': ['kuaishou_video', 'kuaishou_video_comment'],
        'Weibo': ['weibo_note', 'weibo_note_comment', 'weibo_creator'],
        'Xiaohongshu': ['xhs_note'],
        'Zhihu': ['zhihu_content', 'zhihu_comment'],
        'Tieba': ['tieba_note', 'tieba_comment', 'tieba_creator']
    }
    
    overview_data = []
    for platform, tables in platforms.items():
        total_records = 0
        for table in tables:
            try:
                query = f"SELECT COUNT(*) as count FROM {table}"
                result = pd.read_sql(query, engine)
                total_records += result.iloc[0]['count']
            except:
                continue
        
        overview_data.append({
            'platform': platform,
            'total_records': int(total_records),
            'tables': len(tables)
        })
    
    # 计算总指标
    total_records = sum(item['total_records'] for item in overview_data)
    active_platforms = len([item for item in overview_data if item['total_records'] > 0])
    avg_records = total_records / len(overview_data) if overview_data else 0
    total_tables = sum(item['tables'] for item in overview_data)
    
    return jsonify({
        'success': True,
        'data': overview_data,
        'metrics': {
            'total_records': total_records,
            'active_platforms': active_platforms,
            'avg_records': round(avg_records, 0),
            'total_tables': total_tables
        }
    })


@app.route('/api/bilibili', methods=['GET'])
def get_bilibili_data():
    """获取Bilibili数据"""
    engine = get_engine()
    if not engine:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        query = """
        SELECT 
            video_id,
            title,
            nickname,
            liked_count,
            video_play_count,
            video_favorite_count,
            video_share_count,
            video_coin_count,
            create_time,
            source_keyword
        FROM bilibili_video 
        WHERE create_time IS NOT NULL
        ORDER BY create_time DESC
        LIMIT 1000
        """
        df = pd.read_sql(query, engine)
        
        if df.empty:
            return jsonify({'success': True, 'data': [], 'metrics': {}})
        
        # 转换时间戳
        if 'create_time' in df.columns:
            df['create_time'] = pd.to_datetime(df['create_time'], unit='s', errors='coerce')
        
        # 转换数值字段
        numeric_columns = ['liked_count', 'video_play_count', 'video_favorite_count', 
                          'video_share_count', 'video_coin_count']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # 计算指标
        metrics = {
            'total_videos': len(df),
            'avg_likes': float(df['liked_count'].mean()) if 'liked_count' in df.columns else 0,
            'avg_plays': float(df['video_play_count'].mean()) if 'video_play_count' in df.columns else 0,
            'unique_creators': int(df['nickname'].nunique()) if 'nickname' in df.columns else 0
        }
        
        # Top creators
        if 'nickname' in df.columns and 'liked_count' in df.columns:
            top_creators = df.groupby('nickname')['liked_count'].sum().sort_values(ascending=False).head(10)
            top_creators_data = [{'name': name, 'likes': int(likes)} for name, likes in top_creators.items()]
        else:
            top_creators_data = []
        
        # 时间线数据
        if 'create_time' in df.columns and not df['create_time'].isna().all():
            daily_videos = df.groupby(df['create_time'].dt.date).size().reset_index()
            daily_videos.columns = ['date', 'count']
            timeline_data = [{'date': str(row['date']), 'count': int(row['count'])} 
                            for _, row in daily_videos.iterrows()]
        else:
            timeline_data = []
        
        # 转换为JSON格式
        data = df.to_dict('records')
        for record in data:
            # 转换datetime为字符串
            if 'create_time' in record and pd.notna(record['create_time']):
                record['create_time'] = record['create_time'].isoformat() if hasattr(record['create_time'], 'isoformat') else str(record['create_time'])
            # 转换numpy类型为Python原生类型
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None
                elif isinstance(value, (pd.Timestamp, pd.Timedelta)):
                    record[key] = str(value)
                elif hasattr(value, 'item'):  # numpy类型
                    record[key] = value.item()
        
        return jsonify({
            'success': True,
            'data': data,
            'metrics': metrics,
            'top_creators': top_creators_data,
            'timeline': timeline_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/douyin', methods=['GET'])
def get_douyin_data():
    """获取Douyin数据"""
    engine = get_engine()
    if not engine:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        query = """
        SELECT 
            aweme_id,
            title,
            nickname,
            liked_count,
            comment_count,
            share_count,
            collected_count,
            create_time,
            source_keyword
        FROM douyin_aweme 
        WHERE create_time IS NOT NULL
        ORDER BY create_time DESC
        LIMIT 1000
        """
        df = pd.read_sql(query, engine)
        
        if df.empty:
            return jsonify({'success': True, 'data': [], 'metrics': {}})
        
        # 转换时间戳
        if 'create_time' in df.columns:
            df['create_time'] = pd.to_datetime(df['create_time'], unit='s', errors='coerce')
        
        # 转换数值字段
        numeric_columns = ['liked_count', 'comment_count', 'share_count', 'collected_count']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # 计算指标
        metrics = {
            'total_videos': len(df),
            'avg_likes': float(df['liked_count'].mean()) if 'liked_count' in df.columns else 0,
            'avg_comments': float(df['comment_count'].mean()) if 'comment_count' in df.columns else 0,
            'unique_creators': int(df['nickname'].nunique()) if 'nickname' in df.columns else 0
        }

        # Top creators
        if 'nickname' in df.columns and 'liked_count' in df.columns:
            top_creators = df.groupby('nickname')['liked_count'] \
                             .sum().sort_values(ascending=False).head(10)
            top_creators_data = [{'name': name, 'likes': int(likes)} for name, likes in top_creators.items()]
        else:
            top_creators_data = []

        # 时间线数据
        if 'create_time' in df.columns and not df['create_time'].isna().all():
            daily_videos = df.groupby(df['create_time'].dt.date).size().reset_index()
            daily_videos.columns = ['date', 'count']
            timeline_data = [{'date': str(row['date']), 'count': int(row['count'])}
                             for _, row in daily_videos.iterrows()]
        else:
            timeline_data = []
        
        # 转换为JSON格式
        data = df.to_dict('records')
        for record in data:
            if 'create_time' in record and pd.notna(record['create_time']):
                record['create_time'] = record['create_time'].isoformat() if hasattr(record['create_time'], 'isoformat') else str(record['create_time'])
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None
                elif isinstance(value, (pd.Timestamp, pd.Timedelta)):
                    record[key] = str(value)
                elif hasattr(value, 'item'):
                    record[key] = value.item()
        
        return jsonify({
            'success': True,
            'data': data,
            'metrics': metrics,
            'top_creators': top_creators_data,
            'timeline': timeline_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/kuaishou', methods=['GET'])
def get_kuaishou_data():
    """获取快手数据"""
    engine = get_engine()
    if not engine:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        query = """
        SELECT 
            video_id,
            title,
            `desc`,
            nickname,
            liked_count,
            viewd_count,
            create_time,
            video_url,
            video_cover_url,
            source_keyword
        FROM kuaishou_video 
        WHERE create_time IS NOT NULL
        ORDER BY create_time DESC
        LIMIT 1000
        """
        df = pd.read_sql(query, engine)
        
        if df.empty:
            return jsonify({
                'success': True, 
                'data': [], 
                'metrics': {
                    'total_videos': 0,
                    'avg_likes': 0,
                    'avg_views': 0,
                    'unique_creators': 0
                },
                'top_creators': [],
                'timeline': [],
                'message': '数据库中没有快手视频数据，请先同步数据'
            })
        
        # 转换时间戳
        if 'create_time' in df.columns:
            # 保存原始时间戳用于重试
            original_time = df['create_time'].copy()
            try:
                # 先尝试作为秒级时间戳
                df['create_time'] = pd.to_datetime(df['create_time'], unit='s', errors='coerce')
                # 如果转换后全是NaN，尝试毫秒级时间戳
                if df['create_time'].isna().all() and not original_time.isna().all():
                    df['create_time'] = pd.to_datetime(original_time, unit='ms', errors='coerce')
                # 如果还是NaN，尝试直接转换
                if df['create_time'].isna().all() and not original_time.isna().all():
                    df['create_time'] = pd.to_datetime(original_time, errors='coerce')
            except Exception as e:
                print(f"[WARN] 时间戳转换失败: {e}")
                df['create_time'] = pd.to_datetime(original_time, errors='coerce')
        
        # 转换数值字段
        numeric_columns = ['liked_count', 'viewd_count']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # 计算指标
        metrics = {
            'total_videos': len(df),
            'avg_likes': float(df['liked_count'].mean()) if 'liked_count' in df.columns else 0,
            'avg_views': float(df['viewd_count'].mean()) if 'viewd_count' in df.columns else 0,
            'unique_creators': int(df['nickname'].nunique()) if 'nickname' in df.columns else 0
        }
        
        # Top creators
        if 'nickname' in df.columns and 'liked_count' in df.columns:
            top_creators = df.groupby('nickname')['liked_count'].sum().sort_values(ascending=False).head(10)
            top_creators_data = [{'name': name, 'likes': int(likes)} for name, likes in top_creators.items()]
        else:
            top_creators_data = []
        
        # 时间线数据
        timeline_data = []
        if 'create_time' in df.columns:
            # 过滤掉NaN值
            valid_time_df = df[df['create_time'].notna()].copy()
            if not valid_time_df.empty:
                try:
                    # 确保create_time是datetime类型
                    if not pd.api.types.is_datetime64_any_dtype(valid_time_df['create_time']):
                        valid_time_df['create_time'] = pd.to_datetime(valid_time_df['create_time'], errors='coerce')
                        valid_time_df = valid_time_df[valid_time_df['create_time'].notna()]
                    
                    if not valid_time_df.empty:
                        # 按日期分组
                        valid_time_df['date'] = valid_time_df['create_time'].dt.date
                        daily_videos = valid_time_df.groupby('date').size().reset_index(name='count')
                        timeline_data = [{'date': str(row['date']), 'count': int(row['count'])} 
                                        for _, row in daily_videos.iterrows()]
                except Exception as e:
                    print(f"[WARN] 生成时间线数据失败: {e}")
                    import traceback
                    traceback.print_exc()
                    timeline_data = []
        
        # 转换为JSON格式
        data = df.to_dict('records')
        for record in data:
            if 'create_time' in record and pd.notna(record['create_time']):
                record['create_time'] = record['create_time'].isoformat() if hasattr(record['create_time'], 'isoformat') else str(record['create_time'])
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None
                elif isinstance(value, (pd.Timestamp, pd.Timedelta)):
                    record[key] = str(value)
                elif hasattr(value, 'item'):
                    record[key] = value.item()
        
        return jsonify({
            'success': True,
            'data': data,
            'metrics': metrics,
            'top_creators': top_creators_data,
            'timeline': timeline_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/zhihu', methods=['GET'])
def get_zhihu_data():
    """获取知乎数据"""
    engine = get_engine()
    if not engine:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        query = """
        SELECT
            content_id,
            content_type,
            title,
            content_text,
            user_nickname,
            voteup_count,
            comment_count,
            created_time,
            source_keyword
        FROM zhihu_content
        WHERE created_time IS NOT NULL
        ORDER BY created_time DESC
        LIMIT 1000
        """
        df = pd.read_sql(query, engine)

        if df.empty:
            return jsonify({'success': True, 'data': [], 'metrics': {}, 'top_creators': [], 'timeline': []})

        if 'created_time' in df.columns:
            original_time = df['created_time'].copy()
            parsed_time = pd.to_datetime(original_time, errors='coerce')

            # 对无法直接解析的记录，再尝试按时间戳（秒/毫秒）解析
            if parsed_time.isna().any():
                numeric_time = pd.to_numeric(original_time, errors='coerce')
                numeric_mask = parsed_time.isna() & numeric_time.notna()
                if numeric_mask.any():
                    candidate = numeric_time[numeric_mask].abs().median()
                    if pd.notna(candidate) and candidate > 0:
                        unit = 'ms' if candidate > 1e11 else 's'
                    else:
                        unit = 's'
                    parsed_time.loc[numeric_mask] = pd.to_datetime(
                        numeric_time[numeric_mask], unit=unit, errors='coerce'
                    )

            df['created_time'] = parsed_time

        numeric_columns = ['voteup_count', 'comment_count']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        metrics = {
            'total_contents': len(df),
            'avg_votes': float(df['voteup_count'].mean()) if 'voteup_count' in df.columns else 0,
            'avg_comments': float(df['comment_count'].mean()) if 'comment_count' in df.columns else 0,
            'unique_creators': int(df['user_nickname'].nunique()) if 'user_nickname' in df.columns else 0
        }

        if 'user_nickname' in df.columns and 'voteup_count' in df.columns:
            top_creators = df.groupby('user_nickname')['voteup_count'] \
                             .sum().sort_values(ascending=False).head(10)
            top_creators_data = [{'name': name, 'votes': int(votes)} for name, votes in top_creators.items()]
        else:
            top_creators_data = []

        if 'created_time' in df.columns and not df['created_time'].isna().all():
            daily_contents = df.groupby(df['created_time'].dt.date).size().reset_index()
            daily_contents.columns = ['date', 'count']
            timeline_data = [{'date': str(row['date']), 'count': int(row['count'])}
                             for _, row in daily_contents.iterrows()]
        else:
            timeline_data = []

        data = df.to_dict('records')
        for record in data:
            if 'created_time' in record and pd.notna(record['created_time']):
                record['created_time'] = record['created_time'].isoformat() if hasattr(record['created_time'], 'isoformat') else str(record['created_time'])
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None
                elif isinstance(value, (pd.Timestamp, pd.Timedelta)):
                    record[key] = str(value)
                elif hasattr(value, 'item'):
                    record[key] = value.item()

        return jsonify({
            'success': True,
            'data': data,
            'metrics': metrics,
            'top_creators': top_creators_data,
            'timeline': timeline_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/tieba', methods=['GET'])
def get_tieba_data():
    """获取贴吧数据"""
    engine = get_engine()
    if not engine:
        return jsonify({
            'success': False,
            'error': 'Database connection failed',
            'metrics': {
                'total_notes': 0,
                'avg_replies': 0,
                'unique_creators': 0,
                'unique_tiebas': 0
            }
        }), 500
    
    try:
        # 首先检查表是否存在
        try:
            check_query = "SELECT COUNT(*) as count FROM tieba_note"
            pd.read_sql(check_query, engine)
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Table tieba_note does not exist or is not accessible: {str(e)}',
                'metrics': {
                    'total_notes': 0,
                    'avg_replies': 0,
                    'unique_creators': 0,
                    'unique_tiebas': 0
                }
            }), 500
        
        # 查询所有数据，优先使用 add_ts 排序，如果没有则使用 publish_time
        # 使用更兼容的 SQL 语法，注意：desc 是 MySQL 保留关键字，需要用反引号括起来
        query = """
        SELECT 
            note_id,
            title,
            `desc`,
            user_nickname,
            total_replay_num,
            tieba_name,
            publish_time,
            ip_location,
            note_url,
            source_keyword,
            add_ts
        FROM tieba_note 
        ORDER BY 
            CASE WHEN add_ts IS NOT NULL THEN add_ts ELSE 0 END DESC,
            publish_time DESC
        LIMIT 1000
        """
        df = pd.read_sql(query, engine)
        
        if df.empty:
            # 检查是否有任何数据（包括 add_ts 为 NULL 的）
            count_query = "SELECT COUNT(*) as count FROM tieba_note"
            total_count = pd.read_sql(count_query, engine)
            total_records = total_count.iloc[0]['count'] if not total_count.empty else 0
            
            message = '数据库中没有贴吧数据，请先同步数据'
            if total_records > 0:
                message = f'数据库中有 {total_records} 条记录，但查询条件可能过于严格'
            
            return jsonify({
                'success': True, 
                'data': [], 
                'metrics': {
                    'total_notes': 0,
                    'avg_replies': 0,
                    'unique_creators': 0,
                    'unique_tiebas': 0
                },
                'top_creators': [],
                'top_tiebas': [],
                'timeline': [],
                'message': message
            })
        
        # 转换时间戳 - 优先使用 add_ts，如果为空则使用 publish_time
        df['create_time'] = None
        if 'add_ts' in df.columns:
            # 先尝试使用 add_ts（时间戳，单位：秒）
            df['create_time'] = pd.to_datetime(df['add_ts'], unit='s', errors='coerce')
        
        # 如果 add_ts 转换失败或为空，尝试使用 publish_time
        if 'publish_time' in df.columns:
            # 对于 create_time 为空的记录，尝试使用 publish_time
            mask = df['create_time'].isna()
            if mask.any():
                publish_times = pd.to_datetime(df.loc[mask, 'publish_time'], errors='coerce')
                df.loc[mask, 'create_time'] = publish_times
        
        # 如果仍然没有时间，尝试从 publish_time 解析（即使 add_ts 存在但为空）
        if df['create_time'].isna().any() and 'publish_time' in df.columns:
            mask = df['create_time'].isna()
            publish_times = pd.to_datetime(df.loc[mask, 'publish_time'], errors='coerce')
            df.loc[mask, 'create_time'] = publish_times
        
        # 转换数值字段
        numeric_columns = ['total_replay_num']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # 计算指标
        metrics = {
            'total_notes': len(df),
            'avg_replies': float(df['total_replay_num'].mean()) if 'total_replay_num' in df.columns else 0,
            'unique_creators': int(df['user_nickname'].nunique()) if 'user_nickname' in df.columns else 0,
            'unique_tiebas': int(df['tieba_name'].nunique()) if 'tieba_name' in df.columns else 0
        }
        
        # Top creators
        if 'user_nickname' in df.columns and 'total_replay_num' in df.columns:
            top_creators = df.groupby('user_nickname')['total_replay_num'].sum().sort_values(ascending=False).head(10)
            top_creators_data = [{'name': name, 'replies': int(replies)} for name, replies in top_creators.items()]
        else:
            top_creators_data = []
        
        # Top tiebas
        if 'tieba_name' in df.columns:
            top_tiebas = df.groupby('tieba_name').size().sort_values(ascending=False).head(10)
            top_tiebas_data = [{'name': name, 'count': int(count)} for name, count in top_tiebas.items()]
        else:
            top_tiebas_data = []
        
        # 时间线数据
        timeline_data = []
        if 'create_time' in df.columns:
            valid_time_df = df[df['create_time'].notna()].copy()
            if not valid_time_df.empty:
                try:
                    if not pd.api.types.is_datetime64_any_dtype(valid_time_df['create_time']):
                        valid_time_df['create_time'] = pd.to_datetime(valid_time_df['create_time'], errors='coerce')
                        valid_time_df = valid_time_df[valid_time_df['create_time'].notna()]
                    
                    if not valid_time_df.empty:
                        valid_time_df['date'] = valid_time_df['create_time'].dt.date
                        daily_notes = valid_time_df.groupby('date').size().reset_index(name='count')
                        timeline_data = [{'date': str(row['date']), 'count': int(row['count'])} 
                                        for _, row in daily_notes.iterrows()]
                except Exception as e:
                    print(f"[WARN] 生成时间线数据失败: {e}")
                    timeline_data = []
        
        # 转换为JSON格式
        data = df.to_dict('records')
        for record in data:
            # 处理 create_time
            if 'create_time' in record:
                if pd.notna(record['create_time']):
                    # 如果是 pandas Timestamp，转换为 ISO 格式字符串
                    if isinstance(record['create_time'], pd.Timestamp):
                        record['create_time'] = record['create_time'].isoformat()
                    elif hasattr(record['create_time'], 'isoformat'):
                        record['create_time'] = record['create_time'].isoformat()
                    else:
                        record['create_time'] = str(record['create_time'])
                else:
                    # 如果 create_time 为空，尝试使用 publish_time 作为显示值
                    if 'publish_time' in record and pd.notna(record['publish_time']):
                        record['create_time'] = str(record['publish_time'])
                    else:
                        record['create_time'] = None
            
            # 处理其他字段
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None
                elif isinstance(value, (pd.Timestamp, pd.Timedelta)):
                    record[key] = str(value)
                elif hasattr(value, 'item'):
                    record[key] = value.item()
        
        return jsonify({
            'success': True,
            'data': data,
            'metrics': metrics,
            'top_creators': top_creators_data,
            'top_tiebas': top_tiebas_data,
            'timeline': timeline_data
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'metrics': {
                'total_notes': 0,
                'avg_replies': 0,
                'unique_creators': 0,
                'unique_tiebas': 0
            }
        }), 500


@app.route('/api/weibo', methods=['GET'])
def get_weibo_data():
    """获取微博数据"""
    engine = get_engine()
    if not engine:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        query = """
        SELECT 
            note_id,
            content,
            nickname,
            liked_count,
            comments_count,
            shared_count,
            create_time,
            create_date_time,
            ip_location,
            source_keyword,
            note_url
        FROM weibo_note 
        WHERE create_time IS NOT NULL
        ORDER BY create_time DESC
        LIMIT 1000
        """
        df = pd.read_sql(query, engine)
        
        if df.empty:
            return jsonify({'success': True, 'data': [], 'metrics': {}})
        
        # 转换时间戳
        if 'create_time' in df.columns:
            df['create_time'] = pd.to_datetime(df['create_time'], unit='s', errors='coerce')
        
        # 转换数值字段
        numeric_columns = ['liked_count', 'comments_count', 'shared_count']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # 计算指标
        metrics = {
            'total_notes': len(df),
            'avg_likes': float(df['liked_count'].mean()) if 'liked_count' in df.columns else 0,
            'avg_comments': float(df['comments_count'].mean()) if 'comments_count' in df.columns else 0,
            'avg_shares': float(df['shared_count'].mean()) if 'shared_count' in df.columns else 0,
            'unique_creators': int(df['nickname'].nunique()) if 'nickname' in df.columns else 0
        }
        
        # Top creators
        if 'nickname' in df.columns and 'liked_count' in df.columns:
            top_creators = df.groupby('nickname')['liked_count'].sum().sort_values(ascending=False).head(10)
            top_creators_data = [{'name': name, 'likes': int(likes)} for name, likes in top_creators.items()]
        else:
            top_creators_data = []
        
        # 时间线数据
        if 'create_time' in df.columns and not df['create_time'].isna().all():
            daily_notes = df.groupby(df['create_time'].dt.date).size().reset_index()
            daily_notes.columns = ['date', 'count']
            timeline_data = [{'date': str(row['date']), 'count': int(row['count'])} 
                            for _, row in daily_notes.iterrows()]
        else:
            timeline_data = []
        
        # 转换为JSON格式
        data = df.to_dict('records')
        for record in data:
            # 转换datetime为字符串
            if 'create_time' in record and pd.notna(record['create_time']):
                record['create_time'] = record['create_time'].isoformat() if hasattr(record['create_time'], 'isoformat') else str(record['create_time'])
            # 转换numpy类型为Python原生类型
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None
                elif isinstance(value, (pd.Timestamp, pd.Timedelta)):
                    record[key] = str(value)
                elif hasattr(value, 'item'):  # numpy类型
                    record[key] = value.item()
        
        return jsonify({
            'success': True,
            'data': data,
            'metrics': metrics,
            'top_creators': top_creators_data,
            'timeline': timeline_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/semantic', methods=['GET'])
def get_semantic_data():
    """获取语义增强数据"""
    engine = get_engine()
    if not engine:
        return jsonify({'error': 'Database connection failed'}), 500
    
    # 获取查询参数
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    platforms = request.args.getlist('platforms')
    
    try:
        # 首先检查表中是否有数据，并获取实际的时间范围
        check_query = """
        SELECT 
            COUNT(*) as count,
            MIN(processed_at) as min_time,
            MAX(processed_at) as max_time
        FROM comment_semantic
        """
        check_df = pd.read_sql(check_query, engine)
        total_count = check_df.iloc[0]['count'] if not check_df.empty else 0
        
        print(f"[DEBUG] Total count in comment_semantic: {total_count}")
        
        if total_count == 0:
            return jsonify({
                'success': True, 
                'data': [], 
                'message': '暂无语义增强数据，请先运行语义处理流水线。',
                'total_count': 0
            })
        
        # 获取实际数据的时间范围
        min_time = check_df.iloc[0]['min_time']
        max_time = check_df.iloc[0]['max_time']
        
        print(f"[DEBUG] Data time range: min={min_time}, max={max_time}")
        print(f"[DEBUG] Request params: start_date={start_date}, end_date={end_date}, platforms={platforms}")
        
        # 如果没有指定日期范围，使用数据的实际时间范围
        if not start_date or not end_date:
            if pd.notna(min_time) and pd.notna(max_time):
                min_date = datetime.fromtimestamp(int(min_time)).strftime('%Y-%m-%d')
                max_date = datetime.fromtimestamp(int(max_time)).strftime('%Y-%m-%d')
                start_date = min_date
                end_date = max_date
                print(f"[DEBUG] Auto-set date range: {start_date} to {end_date}")
            else:
                # 如果时间戳异常，使用默认范围
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
                end_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
                print(f"[DEBUG] Using default date range: {start_date} to {end_date}")
        
        # 获取时间范围
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        # 将结束时间设置为当天的23:59:59
        end_dt = end_dt.replace(hour=23, minute=59, second=59)
        start_ts = int(start_dt.timestamp())
        end_ts = int(end_dt.timestamp())
        
        print(f"[DEBUG] Query time range: {start_ts} to {end_ts}")
        
        # 使用与dashboard.py相同的方式：直接使用%s占位符和位置参数
        # 这对于pymysql和pandas read_sql是最兼容的方式
        query = """
        SELECT comment_id, platform, sentiment_label, sentiment_score,
               topics_json, entities_json, summary, content, processed_at
        FROM comment_semantic
        WHERE processed_at BETWEEN %s AND %s
        ORDER BY processed_at DESC
        LIMIT 2000
        """
        
        try:
            df = pd.read_sql(query, engine, params=(start_ts, end_ts))
        except Exception as e:
            print(f"[ERROR] Query failed: {e}")
            import traceback
            traceback.print_exc()
            # 如果查询失败，尝试查询所有数据
            query_all = """
            SELECT comment_id, platform, sentiment_label, sentiment_score,
                   topics_json, entities_json, summary, content, processed_at
            FROM comment_semantic
            ORDER BY processed_at DESC
            LIMIT 2000
            """
            df = pd.read_sql(query_all, engine)
        
        print(f"[DEBUG] Query returned {len(df)} rows")
        
        # 如果指定日期范围内没有数据，但数据库中有数据，则查询所有数据
        if df.empty and total_count > 0:
            print(f"[DEBUG] Date range query returned empty, querying all data")
            # 查询所有数据（不限制时间范围）
            query_all = """
            SELECT comment_id, platform, sentiment_label, sentiment_score,
                   topics_json, entities_json, summary, content, processed_at
            FROM comment_semantic
            ORDER BY processed_at DESC
            LIMIT 2000
            """
            df = pd.read_sql(query_all, engine)
            print(f"[DEBUG] All data query returned {len(df)} rows")
        
        # 如果仍然为空，返回空结果
        if df.empty:
            return jsonify({
                'success': True, 
                'data': [], 
                'message': '指定日期范围内暂无语义增强数据，请调整日期范围。',
                'total_count': total_count,
                'sentiment_distribution': {},
                'top_topics': []
            })
        
        # 标准化平台字段，避免NaN导致的.str访问错误
        df['platform'] = df['platform'].fillna('').astype(str)
        df['platform'] = df['platform'].str.strip()
        df['platform_lower'] = df['platform'].str.lower()

        # 过滤平台
        if platforms:
            platform_set = {p.lower() for p in platforms}
            df = df[df['platform_lower'].isin(platform_set)]
        
        # 如果过滤后为空，返回空结果
        if df.empty:
            return jsonify({
                'success': True, 
                'data': [], 
                'message': '指定平台和日期范围内暂无语义增强数据，请调整筛选条件。',
                'total_count': total_count,
                'sentiment_distribution': {},
                'top_topics': []
            })
        
        # 处理JSON字段
        def safe_load_list(value, default=None):
            if default is None:
                default = []
            if isinstance(value, str) and value:
                try:
                    loaded = json.loads(value)
                    if isinstance(loaded, list):
                        return loaded
                    # 如果不是列表，包装成列表以保持兼容
                    return [loaded]
                except json.JSONDecodeError as exc:
                    print(f"[WARN] Failed to parse JSON list: {exc}. Raw value: {value[:200] if isinstance(value, str) else value}")
                    return default
            return default

        def safe_load_entities(value):
            items = safe_load_list(value)
            # 确保每个实体都是dict
            cleaned = []
            for item in items:
                if isinstance(item, dict):
                    cleaned.append(item)
                else:
                    cleaned.append({'name': str(item)})
            return cleaned

        df['topics'] = df['topics_json'].apply(safe_load_list)
        df['entities'] = df['entities_json'].apply(safe_load_entities)
        
        # 情绪分布
        sentiment_counts = df['sentiment_label'].value_counts().to_dict()
        
        # 热门主题
        topic_counter = Counter()
        for topics in df['topics']:
            if isinstance(topics, list):
                topic_counter.update(topics)
        top_topics = [{'topic': topic, 'count': count} for topic, count in topic_counter.most_common(20)]
        
        if 'platform_lower' in df.columns:
            df = df.drop(columns=['platform_lower'])

        # 转换为JSON格式
        data = df.to_dict('records')

        def is_scalar_nan(value):
            if isinstance(value, (list, dict)):
                return False
            try:
                return pd.isna(value)
            except TypeError:
                return False

        for record in data:
            if 'processed_at' in record and not is_scalar_nan(record['processed_at']):
                try:
                    ts = float(record['processed_at'])
                    record['processed_at'] = datetime.fromtimestamp(ts).isoformat()
                except (ValueError, TypeError, OSError):
                    record['processed_at'] = str(record['processed_at'])
            for key, value in record.items():
                if is_scalar_nan(value):
                    record[key] = None
                elif isinstance(value, (pd.Timestamp, pd.Timedelta)):
                    record[key] = str(value)
                elif hasattr(value, 'item'):
                    record[key] = value.item()
        
        print(f"[DEBUG] Returning {len(data)} records, sentiment_distribution: {sentiment_counts}, top_topics: {len(top_topics)}")
        
        return jsonify({
            'success': True,
            'data': data,
            'sentiment_distribution': sentiment_counts,
            'top_topics': top_topics,
            'total_count': len(data)
        })
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback.print_exc()
        print(f"[ERROR] get_semantic_data failed: {error_msg}")
        return jsonify({
            'success': False,
            'error': error_msg,
            'data': [],
            'sentiment_distribution': {},
            'top_topics': []
        }), 500


@app.route('/api/cross-platform', methods=['GET'])
def get_cross_platform_data():
    """获取跨平台对比数据"""
    engine = get_engine()
    if not engine:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        comparison_data = []
        
        # 获取Bilibili数据
        try:
            bilibili_query = """
            SELECT COUNT(*) as total, AVG(liked_count) as avg_likes, COUNT(DISTINCT nickname) as creators
            FROM bilibili_video
            """
            bilibili_df = pd.read_sql(bilibili_query, engine)
            
            if not bilibili_df.empty:
                bl_row = bilibili_df.iloc[0]
                comparison_data.append({
                    'platform': 'Bilibili',
                    'total_content': int(bl_row['total']),
                    'avg_likes': float(bl_row['avg_likes']) if pd.notna(bl_row['avg_likes']) else 0,
                    'unique_creators': int(bl_row['creators'])
                })
        except Exception as e:
            print(f"Error loading Bilibili data: {e}")
        
        # 获取Douyin数据
        try:
            douyin_query = """
            SELECT COUNT(*) as total, AVG(CAST(liked_count AS DECIMAL)) as avg_likes, COUNT(DISTINCT nickname) as creators
            FROM douyin_aweme
            WHERE liked_count IS NOT NULL
            """
            douyin_df = pd.read_sql(douyin_query, engine)
            
            if not douyin_df.empty:
                dy_row = douyin_df.iloc[0]
                comparison_data.append({
                    'platform': 'Douyin',
                    'total_content': int(dy_row['total']),
                    'avg_likes': float(dy_row['avg_likes']) if pd.notna(dy_row['avg_likes']) else 0,
                    'unique_creators': int(dy_row['creators'])
                })
        except Exception as e:
            print(f"Error loading Douyin data: {e}")
        
        # 获取Kuaishou数据
        try:
            kuaishou_query = """
            SELECT COUNT(*) as total, 
                   AVG(CAST(liked_count AS DECIMAL)) as avg_likes,
                   AVG(CAST(viewd_count AS DECIMAL)) as avg_views,
                   COUNT(DISTINCT nickname) as creators
            FROM kuaishou_video
            WHERE liked_count IS NOT NULL
            """
            kuaishou_df = pd.read_sql(kuaishou_query, engine)
            
            if not kuaishou_df.empty:
                ks_row = kuaishou_df.iloc[0]
                comparison_data.append({
                    'platform': 'Kuaishou',
                    'total_content': int(ks_row['total']),
                    'avg_likes': float(ks_row['avg_likes']) if pd.notna(ks_row['avg_likes']) else 0,
                    'avg_views': float(ks_row['avg_views']) if pd.notna(ks_row['avg_views']) else 0,
                    'unique_creators': int(ks_row['creators'])
                })
        except Exception as e:
            print(f"Error loading Kuaishou data: {e}")
        
        # 获取Weibo数据
        try:
            # 微博的 liked_count, comments_count, shared_count 是 Text 类型，需要特殊处理
            weibo_query = """
            SELECT COUNT(*) as total, 
                   AVG(CASE 
                       WHEN liked_count IS NOT NULL AND liked_count != '' 
                       THEN CAST(liked_count AS DECIMAL) 
                       ELSE 0 
                   END) as avg_likes,
                   AVG(CASE 
                       WHEN comments_count IS NOT NULL AND comments_count != '' 
                       THEN CAST(comments_count AS DECIMAL) 
                       ELSE 0 
                   END) as avg_comments,
                   AVG(CASE 
                       WHEN shared_count IS NOT NULL AND shared_count != '' 
                       THEN CAST(shared_count AS DECIMAL) 
                       ELSE 0 
                   END) as avg_shares,
                   COUNT(DISTINCT nickname) as creators
            FROM weibo_note
            """
            weibo_df = pd.read_sql(weibo_query, engine)
            
            if not weibo_df.empty:
                wb_row = weibo_df.iloc[0]
                total = int(wb_row['total']) if pd.notna(wb_row['total']) else 0
                
                # 确保即使值为 0 也显示
                avg_likes = float(wb_row['avg_likes']) if pd.notna(wb_row['avg_likes']) else 0
                avg_comments = float(wb_row['avg_comments']) if pd.notna(wb_row['avg_comments']) else 0
                avg_shares = float(wb_row['avg_shares']) if pd.notna(wb_row['avg_shares']) else 0
                
                # 计算平均互动量，如果所有值都是 0，则返回 0
                if avg_likes == 0 and avg_comments == 0 and avg_shares == 0:
                    avg_engagement = 0
                else:
                    avg_engagement = (avg_likes + avg_comments + avg_shares) / 3
                
                # 即使数据为 0 也添加到对比数据中
                comparison_data.append({
                    'platform': 'Weibo',
                    'total_content': total,
                    'avg_likes': avg_likes,
                    'avg_comments': avg_comments,
                    'avg_shares': avg_shares,
                    'avg_engagement': avg_engagement,
                    'unique_creators': int(wb_row['creators']) if pd.notna(wb_row['creators']) else 0
                })
        except Exception as e:
            print(f"Error loading Weibo data: {e}")
            import traceback
            traceback.print_exc()
        
        # 获取Zhihu数据
        try:
            zhihu_query = """
            SELECT COUNT(*) as total,
                   AVG(CAST(voteup_count AS DECIMAL)) as avg_votes,
                   AVG(CAST(comment_count AS DECIMAL)) as avg_comments,
                   COUNT(DISTINCT user_nickname) as creators
            FROM zhihu_content
            WHERE voteup_count IS NOT NULL
            """
            zhihu_df = pd.read_sql(zhihu_query, engine)

            if not zhihu_df.empty:
                zh_row = zhihu_df.iloc[0]
                avg_votes = float(zh_row['avg_votes']) if pd.notna(zh_row['avg_votes']) else 0
                avg_comments = float(zh_row['avg_comments']) if pd.notna(zh_row['avg_comments']) else 0
                avg_engagement = (avg_votes + avg_comments) / 2 if (avg_votes or avg_comments) else 0
                comparison_data.append({
                    'platform': 'Zhihu',
                    'total_content': int(zh_row['total']),
                    'avg_likes': avg_votes,
                    'avg_comments': avg_comments,
                    'avg_engagement': avg_engagement,
                    'unique_creators': int(zh_row['creators'])
                })
        except Exception as e:
            print(f"Error loading Zhihu data: {e}")
        
        # 获取Tieba数据
        try:
            tieba_query = """
            SELECT COUNT(*) as total,
                   AVG(CAST(total_replay_num AS DECIMAL)) as avg_replies,
                   COUNT(DISTINCT user_nickname) as creators,
                   COUNT(DISTINCT tieba_name) as tiebas
            FROM tieba_note
            WHERE total_replay_num IS NOT NULL
            """
            tieba_df = pd.read_sql(tieba_query, engine)
            
            if not tieba_df.empty:
                tb_row = tieba_df.iloc[0]
                avg_replies = float(tb_row['avg_replies']) if pd.notna(tb_row['avg_replies']) else 0
                comparison_data.append({
                    'platform': 'Tieba',
                    'total_content': int(tb_row['total']),
                    'avg_likes': avg_replies,
                    'avg_comments': avg_replies,
                    'avg_engagement': avg_replies,
                    'unique_creators': int(tb_row['creators']),
                    'unique_tiebas': int(tb_row['tiebas']) if 'tiebas' in tb_row else 0
                })
        except Exception as e:
            print(f"Error loading Tieba data: {e}")
        
        return jsonify({
            'success': True,
            'data': comparison_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    engine = get_engine()
    if engine:
        try:
            pd.read_sql("SELECT 1", engine)
            db_status = 'connected'
        except:
            db_status = 'disconnected'
    else:
        db_status = 'disconnected'
    
    return jsonify({
        'status': 'ok',
        'database': db_status,
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

