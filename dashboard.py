import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, func, text
from sqlalchemy.orm import sessionmaker
import os
import json
from collections import Counter
from datetime import datetime, timedelta
import altair as alt
from neo4j import GraphDatabase
from database.models import *
from database.db import get_db_engine
import numpy as np
from dashboard_config import DASHBOARD_CONFIG, get_platform_color, format_number, get_time_ago
from advanced_analytics import show_advanced_analytics
from realtime_monitor import show_realtime_dashboard
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE

# Page configuration
st.set_page_config(
    page_title="MediaCrawler Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
        background-color: #f0f2f6;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database connection
@st.cache_resource
def init_connection():
    try:
        engine = get_db_engine()
        return engine
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None


@st.cache_resource
def init_neo4j_driver():
    if not NEO4J_URI or not NEO4J_USER or not NEO4J_PASSWORD:
        return None
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        return driver
    except Exception as e:
        st.warning(f"Neo4j connection failed: {e}")
        return None

# Load data functions
@st.cache_data
def load_platform_overview():
    engine = init_connection()
    if not engine:
        return pd.DataFrame()
    
    platforms = {
        'Bilibili': ['bilibili_video', 'bilibili_video_comment', 'bilibili_up_info'],
        'Douyin': ['douyin_aweme', 'douyin_aweme_comment', 'dy_creator'],
        'Kuaishou': ['kuaishou_video', 'kuaishou_video_comment'],
        'Weibo': ['weibo_note', 'weibo_note_comment', 'weibo_creator'],
        'Xiaohongshu': ['xhs_note'],
        'Zhihu': ['zhihu_answer', 'zhihu_article']
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
            'Platform': platform,
            'Total Records': total_records,
            'Tables': len(tables)
        })
    
    return pd.DataFrame(overview_data)

@st.cache_data
def load_bilibili_data():
    engine = init_connection()
    if not engine:
        return pd.DataFrame()
    
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
        
        # 转换时间戳为datetime
        if not df.empty and 'create_time' in df.columns:
            try:
                df['create_time'] = pd.to_datetime(df['create_time'], unit='s', errors='coerce')
            except:
                # 如果unit='s'失败，尝试直接转换
                df['create_time'] = pd.to_datetime(df['create_time'], errors='coerce')
        
        # 转换数值字段为数值类型
        numeric_columns = ['liked_count', 'video_play_count', 'video_favorite_count', 
                          'video_share_count', 'video_coin_count']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Error loading Bilibili data: {e}")
        import traceback
        st.error(f"Traceback: {traceback.format_exc()}")
        return pd.DataFrame()

@st.cache_data
def load_douyin_data():
    engine = init_connection()
    if not engine:
        return pd.DataFrame()
    
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
        df['create_time'] = pd.to_datetime(df['create_time'], unit='s')
        return df
    except Exception as e:
        st.error(f"Error loading Douyin data: {e}")
        return pd.DataFrame()

@st.cache_data
def load_kuaishou_data():
    engine = init_connection()
    if not engine:
        return pd.DataFrame()
    
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
        
        # 转换时间戳为datetime
        if not df.empty and 'create_time' in df.columns:
            try:
                df['create_time'] = pd.to_datetime(df['create_time'], unit='s', errors='coerce')
            except:
                # 如果unit='s'失败，尝试直接转换
                df['create_time'] = pd.to_datetime(df['create_time'], errors='coerce')
        
        # 转换数值字段为数值类型
        numeric_columns = ['liked_count', 'viewd_count']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Error loading Kuaishou data: {e}")
        import traceback
        st.error(f"Traceback: {traceback.format_exc()}")
        return pd.DataFrame()

@st.cache_data
def load_weibo_data():
    engine = init_connection()
    if not engine:
        return pd.DataFrame()
    
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
        
        # 转换时间戳为datetime
        if not df.empty and 'create_time' in df.columns:
            try:
                df['create_time'] = pd.to_datetime(df['create_time'], unit='s', errors='coerce')
            except:
                # 如果unit='s'失败，尝试直接转换
                df['create_time'] = pd.to_datetime(df['create_time'], errors='coerce')
        
        # 转换数值字段为数值类型
        numeric_columns = ['liked_count', 'comments_count', 'shared_count']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Error loading Weibo data: {e}")
        import traceback
        st.error(f"Traceback: {traceback.format_exc()}")
        return pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_semantic_comments(start_date, end_date, platforms):
    engine = init_connection()
    if not engine:
        return pd.DataFrame()

    # 首先检查表中是否有数据
    try:
        check_query = "SELECT COUNT(*) as count FROM comment_semantic"
        count_df = pd.read_sql(check_query, engine)
        total_count = count_df.iloc[0]['count'] if not count_df.empty else 0
        
        if total_count == 0:
            # 表中没有数据，返回空的DataFrame
            return pd.DataFrame()
        
        # 获取数据的时间范围
        time_range_query = """
        SELECT 
            MIN(processed_at) as min_time,
            MAX(processed_at) as max_time
        FROM comment_semantic
        """
        time_range_df = pd.read_sql(time_range_query, engine)
        
        if not time_range_df.empty and pd.notna(time_range_df.iloc[0]['min_time']):
            min_time = int(time_range_df.iloc[0]['min_time'])
            max_time = int(time_range_df.iloc[0]['max_time'])
            min_date_str = datetime.fromtimestamp(min_time).strftime('%Y-%m-%d')
            max_date_str = datetime.fromtimestamp(max_time).strftime('%Y-%m-%d')
            
            # 检查数据时间范围是否在查询范围内
            start_dt = datetime.combine(start_date, datetime.min.time())
            end_dt = datetime.combine(end_date, datetime.max.time())
            start_ts = int(start_dt.timestamp())
            end_ts = int(end_dt.timestamp())
            
            # 如果数据时间范围不在查询范围内，但表中有数据，返回空的DataFrame
            # Dashboard会显示提示信息
            if max_time < start_ts or min_time > end_ts:
                return pd.DataFrame()
    except Exception as e:
        st.warning(f"检查数据状态时出错: {e}")
        return pd.DataFrame()

    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())
    start_ts = int(start_dt.timestamp())
    end_ts = int(end_dt.timestamp())
    
    # 使用位置参数（%s）而不是命名参数，因为pymysql不支持命名参数
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
        if df.empty:
            return df

        df["platform"] = df["platform"].astype(str)
        if platforms:
            platform_set = {p.lower() for p in platforms}
            df = df[df["platform"].str.lower().isin(platform_set)]
        df["platform_display"] = df["platform"].str.title()

        df["processed_at_dt"] = pd.to_datetime(df["processed_at"], unit="s")
        df["topics"] = df["topics_json"].apply(
            lambda x: json.loads(x) if isinstance(x, str) and x else []
        )
        df["entities"] = df["entities_json"].apply(
            lambda x: json.loads(x) if isinstance(x, str) and x else []
        )
        df["topics_str"] = df["topics"].apply(lambda lst: ", ".join(lst))
        df["entities_str"] = df["entities"].apply(
            lambda lst: ", ".join(
                f"{item.get('name')}" + (f"({item.get('type')})" if item.get("type") else "")
                for item in lst
                if isinstance(item, dict) and item.get("name")
            )
        )
        return df
    except Exception as e:
        st.error(f"Error loading semantic comments: {e}")
        return pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_entity_snapshot(limit: int = 50):
    engine = init_connection()
    if not engine:
        return pd.DataFrame()

    # 使用位置参数（%s）而不是命名参数，因为pymysql不支持命名参数
    query = """
    SELECT se.name, se.entity_type, COUNT(cer.id) AS mention_count
    FROM comment_entity_relation cer
    JOIN semantic_entity se ON se.entity_unique_key = cer.entity_unique_key
    GROUP BY se.name, se.entity_type
    ORDER BY mention_count DESC
    LIMIT %s
    """
    try:
        df = pd.read_sql(query, engine, params=(limit,))
        return df
    except Exception as e:
        st.warning(f"Failed to load entity snapshot: {e}")
        return pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_neo4j_mentions(limit: int = 100):
    driver = init_neo4j_driver()
    if not driver:
        return pd.DataFrame()

    query = """
    MATCH (c:Comment)-[r:MENTIONS]->(e:Entity)
    RETURN c.comment_unique_id AS comment_unique_id,
           c.platform AS platform,
           e.name AS entity_name,
           e.type AS entity_type,
           r.sentiment AS sentiment,
           c.summary AS summary
    ORDER BY c.last_processed_at DESC, c.first_processed_at DESC
    LIMIT $limit
    """
    try:
        with driver.session(database=NEO4J_DATABASE) as session:
            records = session.run(query, limit=limit)
            rows = [record.data() for record in records]
        return pd.DataFrame(rows)
    except Exception as e:
        st.warning(f"Failed to load Neo4j mentions: {e}")
        return pd.DataFrame()


def render_semantic_insights(start_date, end_date, platforms):
    st.markdown('<div class="main-header">🧠 Semantic Insights</div>', unsafe_allow_html=True)

    # 首先检查表中是否有数据
    engine = init_connection()
    has_data = False
    data_time_range = None
    
    if engine:
        try:
            check_query = "SELECT COUNT(*) as count FROM comment_semantic"
            count_df = pd.read_sql(check_query, engine)
            total_count = count_df.iloc[0]['count'] if not count_df.empty else 0
            has_data = total_count > 0
            
            if has_data:
                # 获取数据的时间范围
                time_range_query = """
                SELECT 
                    MIN(processed_at) as min_time,
                    MAX(processed_at) as max_time
                FROM comment_semantic
                """
                time_range_df = pd.read_sql(time_range_query, engine)
                if not time_range_df.empty and pd.notna(time_range_df.iloc[0]['min_time']):
                    min_time = int(time_range_df.iloc[0]['min_time'])
                    max_time = int(time_range_df.iloc[0]['max_time'])
                    data_time_range = {
                        'min': datetime.fromtimestamp(min_time),
                        'max': datetime.fromtimestamp(max_time)
                    }
        except Exception as e:
            st.warning(f"检查数据状态时出错: {e}")

    semantic_df = load_semantic_comments(start_date, end_date, platforms)
    
    if semantic_df.empty:
        if not has_data:
            st.info("📝 暂无语义增强数据，请先运行语义处理流水线。")
            st.markdown("""
            ### 💡 运行步骤：
            
            1. **准备评论数据**：
               ```bash
               # 从数据库导出评论数据
               python export_comments_for_semantic.py --limit 100
               ```
            
            2. **运行语义处理流水线**：
               ```bash
               # 测试运行（处理10条评论）
               python run_semantic_pipeline.py ./data/bili/json/search_comments_XXXXXX.json --platform bilibili --limit 10
               
               # 如果测试成功，处理所有数据
               python run_semantic_pipeline.py ./data/bili/json/search_comments_XXXXXX.json --platform bilibili
               ```
            
            3. **验证数据**：
               ```bash
               # 检查数据是否写入
               python check_semantic_status.py
               ```
            
            📚 详细说明请参考：`运行语义处理流水线指南.md`
            """)
        else:
            # 表中有数据，但日期范围不匹配
            if data_time_range:
                st.warning(f"⚠️ 指定日期范围内暂无语义增强数据。")
                st.info(f"💡 数据时间范围：{data_time_range['min'].strftime('%Y-%m-%d')} 至 {data_time_range['max'].strftime('%Y-%m-%d')}")
                st.info("💡 请在侧边栏调整日期范围以包含数据时间范围。")
            else:
                st.info("📝 指定日期范围内暂无语义增强数据，请调整日期范围。")
        return

    col1, col2 = st.columns(2)
    with col1:
        sentiment_counts = semantic_df["sentiment_label"].value_counts()
        fig = px.pie(
            values=sentiment_counts.values,
            names=sentiment_counts.index,
            title="情绪分布",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        sentiment_time = (
            semantic_df.groupby([semantic_df["processed_at_dt"].dt.date, "sentiment_label"])
            .size()
            .reset_index(name="count")
        )
        sentiment_time.columns = ["Date", "Sentiment", "Count"]
        fig = px.line(
            sentiment_time,
            x="Date",
            y="Count",
            color="Sentiment",
            title="情绪趋势",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.subheader("🔥 热门主题")
    topic_counter = Counter()
    for topics in semantic_df["topics"]:
        topic_counter.update(topics)
    if topic_counter:
        topics_df = pd.DataFrame(topic_counter.most_common(20), columns=["Topic", "Count"])
        fig = px.bar(
            topics_df,
            x="Count",
            y="Topic",
            orientation="h",
            title="主题热度 TOP 20",
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("暂无主题数据。")

    st.subheader("🧭 实体洞察")
    entity_df = load_entity_snapshot(limit=30)
    if not entity_df.empty:
        fig = px.bar(
            entity_df.sort_values("mention_count"),
            x="mention_count",
            y="name",
            color="entity_type",
            orientation="h",
            title="实体提及次数 TOP 30",
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(entity_df, use_container_width=True)
    else:
        st.info("尚未有实体统计数据。")

    neo4j_df = load_neo4j_mentions(limit=100)
    st.subheader("🕸 知识图谱最新关联")
    if not neo4j_df.empty:
        st.dataframe(neo4j_df, use_container_width=True)
    else:
        st.info("Neo4j 未连接或暂无关联数据。")

    st.subheader("💬 最新语义增强评论")
    display_columns = [
        "platform_display",
        "comment_id",
        "sentiment_label",
        "sentiment_score",
        "summary",
        "topics_str",
        "entities_str",
        "processed_at_dt",
    ]
    st.dataframe(
        semantic_df[display_columns].rename(
            columns={
                "platform_display": "Platform",
                "comment_id": "Comment ID",
                "sentiment_label": "Sentiment",
                "sentiment_score": "Score",
                "summary": "Summary",
                "topics_str": "Topics",
                "entities_str": "Entities",
                "processed_at_dt": "Processed At",
            }
        ),
        use_container_width=True,
    )

    csv_data = semantic_df.to_csv(index=False)
    st.download_button(
        label="下载语义增强数据（CSV）",
        data=csv_data,
        file_name=f"semantic_comments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )

# Sidebar
with st.sidebar:
    st.title("🎯 Navigation")
    page = st.radio("Select Page", ["Overview", "Bilibili Analytics", "Douyin Analytics", "Kuaishou Analytics", "Weibo Analytics", "Cross-Platform Analysis", "Semantic Insights", "Advanced Analytics", "Real-Time Monitor", "Data Export"])
    
    st.divider()
    
    # Date range filter
    st.subheader("📅 Date Range")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", datetime.now())
    
    st.divider()
    
    # Platform filter
    st.subheader("🔧 Platform Filter")
    platforms = st.multiselect(
        "Select Platforms",
        ["Bilibili", "Douyin", "Kuaishou", "Weibo", "Xiaohongshu", "Zhihu"],
        ["Bilibili", "Douyin"]
    )
    
    st.divider()
    
    # Settings
    st.subheader("⚙️ Settings")
    auto_refresh = st.checkbox("Auto-refresh data", value=False)
    if auto_refresh:
        refresh_interval = st.slider("Refresh interval (minutes)", 1, 60, 5)
        st.session_state.auto_refresh = True
        st.session_state.refresh_interval = refresh_interval
    else:
        st.session_state.auto_refresh = False

# Main content
if page == "Overview":
    st.markdown('<div class="main-header">📊 MediaCrawler Analytics Dashboard</div>', unsafe_allow_html=True)
    
    # Load overview data
    overview_df = load_platform_overview()
    
    if not overview_df.empty:
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_records = overview_df['Total Records'].sum()
            st.metric("Total Records", f"{total_records:,}")
        
        with col2:
            active_platforms = len(overview_df[overview_df['Total Records'] > 0])
            st.metric("Active Platforms", active_platforms)
        
        with col3:
            avg_records = overview_df['Total Records'].mean()
            st.metric("Avg Records/Platform", f"{avg_records:,.0f}")
        
        with col4:
            total_tables = overview_df['Tables'].sum()
            st.metric("Total Tables", total_tables)
        
        st.divider()
        
        # Platform overview chart
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📈 Platform Distribution")
            fig = px.bar(overview_df, x='Platform', y='Total Records', 
                        title='Records by Platform',
                        color='Platform',
                        color_discrete_map={
                            'Bilibili': '#fb7299',
                            'Douyin': '#000000',
                            'Kuaishou': '#ff6100',
                            'Weibo': '#e6162d',
                            'Xiaohongshu': '#ff2442',
                            'Zhihu': '#0084ff'
                        })
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("📋 Platform Summary")
            st.dataframe(overview_df, use_container_width=True, hide_index=True)
    
    else:
        st.warning("No data available. Please check database connection.")

elif page == "Bilibili Analytics":
    st.markdown('<div class="main-header">📺 Bilibili Analytics</div>', unsafe_allow_html=True)
    
    bilibili_df = load_bilibili_data()
    
    if not bilibili_df.empty:
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Videos", len(bilibili_df))
        
        with col2:
            avg_likes = bilibili_df['liked_count'].mean()
            st.metric("Avg Likes", f"{avg_likes:,.0f}")
        
        with col3:
            avg_plays = bilibili_df['video_play_count'].mean()
            st.metric("Avg Plays", f"{avg_plays:,.0f}")
        
        with col4:
            total_creators = bilibili_df['nickname'].nunique()
            st.metric("Unique Creators", total_creators)
        
        st.divider()
        
        # Top creators by likes
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏆 Top Creators by Total Likes")
            top_creators = bilibili_df.groupby('nickname')['liked_count'].sum().sort_values(ascending=False).head(10)
            fig = px.bar(x=top_creators.values, y=top_creators.index, orientation='h',
                        title='Top 10 Creators by Total Likes')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("📊 Likes vs Plays Correlation")
            fig = px.scatter(bilibili_df, x='video_play_count', y='liked_count',
                             color='nickname', title='Likes vs Plays',
                             hover_data=['title'])
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Video timeline
        st.subheader("📅 Video Publishing Timeline")
        if 'create_time' in bilibili_df.columns and not bilibili_df['create_time'].isna().all():
            try:
                daily_videos = bilibili_df.groupby(bilibili_df['create_time'].dt.date).size().reset_index()
                daily_videos.columns = ['Date', 'Video Count']
                
                fig = px.line(daily_videos, x='Date', y='Video Count',
                             title='Daily Video Uploads')
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning(f"无法生成时间线图表: {e}")
        else:
            st.info("没有可用的时间数据来生成时间线图表")
        
        # Detailed table
        st.subheader("📋 Detailed Video Data")
        st.dataframe(bilibili_df, use_container_width=True)
    
    else:
        st.warning("No Bilibili data available.")

elif page == "Douyin Analytics":
    st.markdown('<div class="main-header">🎵 Douyin Analytics</div>', unsafe_allow_html=True)
    
    douyin_df = load_douyin_data()
    
    if not douyin_df.empty:
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Videos", len(douyin_df))
        
        with col2:
            avg_likes = pd.to_numeric(douyin_df['liked_count'], errors='coerce').mean()
            st.metric("Avg Likes", f"{avg_likes:,.0f}")
        
        with col3:
            avg_comments = pd.to_numeric(douyin_df['comment_count'], errors='coerce').mean()
            st.metric("Avg Comments", f"{avg_comments:,.0f}")
        
        with col4:
            total_creators = douyin_df['nickname'].nunique()
            st.metric("Unique Creators", total_creators)
        
        st.divider()
        
        # Engagement analysis
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💝 Engagement Rate Distribution")
            douyin_df['liked_count'] = pd.to_numeric(douyin_df['liked_count'], errors='coerce')
            douyin_df['comment_count'] = pd.to_numeric(douyin_df['comment_count'], errors='coerce')
            douyin_df['engagement_rate'] = (douyin_df['liked_count'] + douyin_df['comment_count']) / 2
            
            fig = px.histogram(douyin_df, x='engagement_rate', nbins=20,
                             title='Engagement Rate Distribution')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🔥 Top Trending Keywords")
            keyword_counts = douyin_df['source_keyword'].value_counts().head(10)
            fig = px.pie(values=keyword_counts.values, names=keyword_counts.index,
                        title='Top 10 Keywords')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Creator performance
        st.subheader("⭐ Creator Performance Analysis")
        creator_stats = douyin_df.groupby('nickname').agg({
            'liked_count': 'sum',
            'comment_count': 'sum',
            'aweme_id': 'count'
        }).reset_index()
        creator_stats.columns = ['Creator', 'Total Likes', 'Total Comments', 'Video Count']
        creator_stats = creator_stats.sort_values('Total Likes', ascending=False).head(15)
        
        fig = px.bar(creator_stats, x='Creator', y='Total Likes',
                    title='Top 15 Creators by Total Likes')
        fig.update_layout(xaxis_tickangle=-45, height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed table
        st.subheader("📋 Detailed Video Data")
        st.dataframe(douyin_df, use_container_width=True)
    
    else:
        st.warning("No Douyin data available.")

elif page == "Weibo Analytics":
    st.markdown('<div class="main-header">📱 Weibo Analytics</div>', unsafe_allow_html=True)
    
    weibo_df = load_weibo_data()
    
    if not weibo_df.empty:
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Notes", len(weibo_df))
        
        with col2:
            avg_likes = weibo_df['liked_count'].mean()
            st.metric("Avg Likes", f"{avg_likes:,.0f}")
        
        with col3:
            avg_comments = weibo_df['comments_count'].mean()
            st.metric("Avg Comments", f"{avg_comments:,.0f}")
        
        with col4:
            total_creators = weibo_df['nickname'].nunique()
            st.metric("Unique Creators", total_creators)
        
        st.divider()
        
        # Engagement analysis
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💝 Engagement Distribution")
            weibo_df['engagement'] = weibo_df['liked_count'] + weibo_df['comments_count'] + weibo_df['shared_count']
            
            fig = px.histogram(weibo_df, x='engagement', nbins=20,
                             title='Engagement Distribution')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🔥 Top Trending Keywords")
            keyword_counts = weibo_df['source_keyword'].value_counts().head(10)
            if len(keyword_counts) > 0:
                fig = px.pie(values=keyword_counts.values, names=keyword_counts.index,
                            title='Top 10 Keywords')
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("暂无关键词数据")
        
        # Creator performance
        st.subheader("⭐ Creator Performance Analysis")
        creator_stats = weibo_df.groupby('nickname').agg({
            'liked_count': 'sum',
            'comments_count': 'sum',
            'shared_count': 'sum',
            'note_id': 'count'
        }).reset_index()
        creator_stats.columns = ['Creator', 'Total Likes', 'Total Comments', 'Total Shares', 'Note Count']
        creator_stats = creator_stats.sort_values('Total Likes', ascending=False).head(15)
        
        fig = px.bar(creator_stats, x='Creator', y='Total Likes',
                    title='Top 15 Creators by Total Likes')
        fig.update_layout(xaxis_tickangle=-45, height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Notes timeline
        st.subheader("📅 Notes Publishing Timeline")
        if 'create_time' in weibo_df.columns and not weibo_df['create_time'].isna().all():
            try:
                daily_notes = weibo_df.groupby(weibo_df['create_time'].dt.date).size().reset_index()
                daily_notes.columns = ['Date', 'Note Count']
                
                fig = px.line(daily_notes, x='Date', y='Note Count',
                             title='Daily Note Posts')
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning(f"无法生成时间线图表: {e}")
        else:
            st.info("没有可用的时间数据来生成时间线图表")
        
        # Detailed table
        st.subheader("📋 Detailed Note Data")
        st.dataframe(weibo_df, use_container_width=True)
    
    else:
        st.warning("No Weibo data available.")

elif page == "Kuaishou Analytics":
    st.markdown('<div class="main-header">⚡ Kuaishou Analytics</div>', unsafe_allow_html=True)
    
    kuaishou_df = load_kuaishou_data()
    
    if not kuaishou_df.empty:
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Videos", len(kuaishou_df))
        
        with col2:
            avg_likes = kuaishou_df['liked_count'].mean()
            st.metric("Avg Likes", f"{avg_likes:,.0f}")
        
        with col3:
            avg_views = kuaishou_df['viewd_count'].mean()
            st.metric("Avg Views", f"{avg_views:,.0f}")
        
        with col4:
            total_creators = kuaishou_df['nickname'].nunique()
            st.metric("Unique Creators", total_creators)
        
        st.divider()
        
        # Top creators by likes
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏆 Top Creators by Total Likes")
            top_creators = kuaishou_df.groupby('nickname')['liked_count'].sum().sort_values(ascending=False).head(10)
            fig = px.bar(x=top_creators.values, y=top_creators.index, orientation='h',
                        title='Top 10 Creators by Total Likes',
                        color=top_creators.values,
                        color_continuous_scale='Oranges')
            fig.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("📊 Likes vs Views Correlation")
            fig = px.scatter(kuaishou_df, x='viewd_count', y='liked_count',
                             color='nickname', title='Likes vs Views',
                             hover_data=['title'],
                             color_discrete_sequence=px.colors.qualitative.Set3)
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Engagement analysis
        st.subheader("💝 Engagement Analysis")
        col1, col2 = st.columns(2)
        
        with col1:
            # 计算互动率（点赞数/观看数）
            kuaishou_df['engagement_rate'] = (kuaishou_df['liked_count'] / kuaishou_df['viewd_count'].replace(0, 1) * 100).fillna(0)
            fig = px.histogram(kuaishou_df, x='engagement_rate', nbins=20,
                             title='Engagement Rate Distribution (%)',
                             color_discrete_sequence=['#ff6100'])
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🔥 Top Trending Keywords")
            keyword_counts = kuaishou_df['source_keyword'].value_counts().head(10)
            if len(keyword_counts) > 0 and keyword_counts.iloc[0] > 0:
                fig = px.pie(values=keyword_counts.values, names=keyword_counts.index,
                            title='Top 10 Keywords',
                            color_discrete_sequence=px.colors.sequential.Oranges)
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("暂无关键词数据")
        
        # Video timeline
        st.subheader("📅 Video Publishing Timeline")
        if 'create_time' in kuaishou_df.columns and not kuaishou_df['create_time'].isna().all():
            try:
                daily_videos = kuaishou_df.groupby(kuaishou_df['create_time'].dt.date).size().reset_index()
                daily_videos.columns = ['Date', 'Video Count']
                
                fig = px.line(daily_videos, x='Date', y='Video Count',
                             title='Daily Video Posts',
                             color_discrete_sequence=['#ff6100'])
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning(f"无法生成时间线图表: {e}")
        else:
            st.info("没有可用的时间数据来生成时间线图表")
        
        # Creator performance
        st.subheader("⭐ Creator Performance Analysis")
        creator_stats = kuaishou_df.groupby('nickname').agg({
            'liked_count': 'sum',
            'viewd_count': 'sum',
            'video_id': 'count'
        }).reset_index()
        creator_stats.columns = ['Creator', 'Total Likes', 'Total Views', 'Video Count']
        creator_stats = creator_stats.sort_values('Total Likes', ascending=False).head(15)
        
        fig = px.bar(creator_stats, x='Creator', y='Total Likes',
                    title='Top 15 Creators by Total Likes',
                    color='Total Likes',
                    color_continuous_scale='Oranges')
        fig.update_layout(xaxis_tickangle=-45, height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed table
        st.subheader("📋 Detailed Video Data")
        st.dataframe(kuaishou_df, use_container_width=True)
    
    else:
        st.warning("No Kuaishou data available.")

elif page == "Cross-Platform Analysis":
    st.markdown('<div class="main-header">🔗 Cross-Platform Analysis</div>', unsafe_allow_html=True)
    
    bilibili_df = load_bilibili_data()
    douyin_df = load_douyin_data()
    kuaishou_df = load_kuaishou_data()
    weibo_df = load_weibo_data()
    
    # 检查是否有至少一个平台的数据
    has_data = not bilibili_df.empty or not douyin_df.empty or not kuaishou_df.empty or not weibo_df.empty
    
    if has_data:
        # Platform comparison
        st.subheader("📊 Platform Comparison")
        
        comparison_data = []
        
        # Bilibili stats
        if not bilibili_df.empty:
            bl_stats = {
                'Platform': 'Bilibili',
                'Total Content': len(bilibili_df),
                'Avg Likes': bilibili_df['liked_count'].mean(),
                'Avg Engagement': bilibili_df['liked_count'].mean(),  # Simplified
                'Unique Creators': bilibili_df['nickname'].nunique()
            }
            comparison_data.append(bl_stats)
        
        # Douyin stats
        if not douyin_df.empty:
            dy_likes = pd.to_numeric(douyin_df['liked_count'], errors='coerce').mean()
            dy_comments = pd.to_numeric(douyin_df['comment_count'], errors='coerce').mean()
            dy_stats = {
                'Platform': 'Douyin',
                'Total Content': len(douyin_df),
                'Avg Likes': dy_likes,
                'Avg Engagement': (dy_likes + dy_comments) / 2,
                'Unique Creators': douyin_df['nickname'].nunique()
            }
            comparison_data.append(dy_stats)
        
        # Kuaishou stats
        if not kuaishou_df.empty:
            ks_likes = pd.to_numeric(kuaishou_df['liked_count'], errors='coerce').mean()
            ks_views = pd.to_numeric(kuaishou_df['viewd_count'], errors='coerce').mean()
            ks_stats = {
                'Platform': 'Kuaishou',
                'Total Content': len(kuaishou_df),
                'Avg Likes': ks_likes,
                'Avg Engagement': (ks_likes + ks_views) / 2,
                'Unique Creators': kuaishou_df['nickname'].nunique()
            }
            comparison_data.append(ks_stats)
        
        # Weibo stats
        if not weibo_df.empty:
            wb_likes = pd.to_numeric(weibo_df['liked_count'], errors='coerce').mean()
            wb_comments = pd.to_numeric(weibo_df['comments_count'], errors='coerce').mean()
            wb_shares = pd.to_numeric(weibo_df['shared_count'], errors='coerce').mean()
            wb_stats = {
                'Platform': 'Weibo',
                'Total Content': len(weibo_df),
                'Avg Likes': wb_likes,
                'Avg Engagement': (wb_likes + wb_comments + wb_shares) / 3,
                'Unique Creators': weibo_df['nickname'].nunique()
            }
            comparison_data.append(wb_stats)
        
        if comparison_data:
            comparison_df = pd.DataFrame(comparison_data)
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.bar(comparison_df, x='Platform', y='Total Content',
                            title='Content Volume Comparison',
                            color='Platform',
                            color_discrete_map={
                                'Bilibili': '#fb7299',
                                'Douyin': '#000000',
                                'Kuaishou': '#ff6100',
                                'Weibo': '#e6162d'
                            })
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.bar(comparison_df, x='Platform', y='Avg Engagement',
                            title='Average Engagement Comparison',
                            color='Platform',
                            color_discrete_map={
                                'Bilibili': '#fb7299',
                                'Douyin': '#000000',
                                'Kuaishou': '#ff6100',
                                'Weibo': '#e6162d'
                            })
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            # Additional comparison charts
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.bar(comparison_df, x='Platform', y='Avg Likes',
                            title='Average Likes Comparison',
                            color='Platform',
                            color_discrete_map={
                                'Bilibili': '#fb7299',
                                'Douyin': '#000000',
                                'Kuaishou': '#ff6100',
                                'Weibo': '#e6162d'
                            })
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.bar(comparison_df, x='Platform', y='Unique Creators',
                            title='Unique Creators Comparison',
                            color='Platform',
                            color_discrete_map={
                                'Bilibili': '#fb7299',
                                'Douyin': '#000000',
                                'Kuaishou': '#ff6100',
                                'Weibo': '#e6162d'
                            })
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            # Detailed comparison table
            st.subheader("📋 Platform Statistics")
            st.dataframe(comparison_df, use_container_width=True, hide_index=True)
        else:
            st.warning("No data available for comparison.")
    
    else:
        st.warning("Insufficient data for cross-platform analysis.")

elif page == "Semantic Insights":
    render_semantic_insights(start_date, end_date, platforms)

elif page == "Advanced Analytics":
    show_advanced_analytics()

elif page == "Real-Time Monitor":
    show_realtime_dashboard()
    st.markdown('<div class="main-header">📤 Data Export</div>', unsafe_allow_html=True)
    
    st.subheader("Export Analytics Data")
    
    export_format = st.selectbox("Select Export Format", ["CSV", "Excel", "JSON"])
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Export Bilibili Data"):
            bilibili_df = load_bilibili_data()
            if not bilibili_df.empty:
                if export_format == "CSV":
                    csv = bilibili_df.to_csv(index=False)
                    st.download_button(
                        label="Download Bilibili CSV",
                        data=csv,
                        file_name=f"bilibili_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                elif export_format == "Excel":
                    # Create Excel file
                    import io
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        bilibili_df.to_excel(writer, sheet_name='Bilibili Data', index=False)
                    excel_data = output.getvalue()
                    st.download_button(
                        label="Download Bilibili Excel",
                        data=excel_data,
                        file_name=f"bilibili_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:  # JSON
                    json_str = bilibili_df.to_json(orient='records', force_ascii=False)
                    st.download_button(
                        label="Download Bilibili JSON",
                        data=json_str,
                        file_name=f"bilibili_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
    
    with col2:
        if st.button("Export Douyin Data"):
            douyin_df = load_douyin_data()
            if not douyin_df.empty:
                if export_format == "CSV":
                    csv = douyin_df.to_csv(index=False)
                    st.download_button(
                        label="Download Douyin CSV",
                        data=csv,
                        file_name=f"douyin_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                elif export_format == "Excel":
                    import io
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        douyin_df.to_excel(writer, sheet_name='Douyin Data', index=False)
                    excel_data = output.getvalue()
                    st.download_button(
                        label="Download Douyin Excel",
                        data=excel_data,
                        file_name=f"douyin_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:  # JSON
                    json_str = douyin_df.to_json(orient='records', force_ascii=False)
                    st.download_button(
                        label="Download Douyin JSON",
                        data=json_str,
                        file_name=f"douyin_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
    
    st.divider()
    
    # Export analytics report
    st.subheader("📊 Export Analytics Report")
    
    if st.button("Generate Full Report"):
        overview_df = load_platform_overview()
        bilibili_df = load_bilibili_data()
        douyin_df = load_douyin_data()
        
        if not overview_df.empty:
            import io
            output = io.BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Overview sheet
                overview_df.to_excel(writer, sheet_name='Platform Overview', index=False)
                
                # Bilibili data
                if not bilibili_df.empty:
                    bilibili_df.to_excel(writer, sheet_name='Bilibili Data', index=False)
                
                # Douyin data
                if not douyin_df.empty:
                    douyin_df.to_excel(writer, sheet_name='Douyin Data', index=False)
                
                # Summary statistics
                summary_data = []
                if not bilibili_df.empty:
                    summary_data.append({
                        'Platform': 'Bilibili',
                        'Total Videos': len(bilibili_df),
                        'Avg Likes': bilibili_df['liked_count'].mean(),
                        'Avg Plays': bilibili_df['video_play_count'].mean(),
                        'Unique Creators': bilibili_df['nickname'].nunique()
                    })
                
                if not douyin_df.empty:
                    summary_data.append({
                        'Platform': 'Douyin',
                        'Total Videos': len(douyin_df),
                        'Avg Likes': pd.to_numeric(douyin_df['liked_count'], errors='coerce').mean(),
                        'Avg Comments': pd.to_numeric(douyin_df['comment_count'], errors='coerce').mean(),
                        'Unique Creators': douyin_df['nickname'].nunique()
                    })
                
                if summary_data:
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name='Summary Statistics', index=False)
            
            excel_data = output.getvalue()
            st.download_button(
                label="Download Full Analytics Report",
                data=excel_data,
                file_name=f"mediacrawler_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p>MediaCrawler Analytics Dashboard | Built with Streamlit</p>
    <p style='font-size: 0.9rem;'>Last updated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
</div>
""", unsafe_allow_html=True)