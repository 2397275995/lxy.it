import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import seaborn as sns
import matplotlib.pyplot as plt
from database.db import get_db_engine

class AdvancedAnalytics:
    def __init__(self):
        self.engine = get_db_engine()
    
    def get_sentiment_analysis(self, platform='bilibili'):
        """Perform sentiment analysis on comments"""
        try:
            if platform == 'bilibili':
                query = """
                SELECT content, create_time, like_count
                FROM bilibili_video_comment 
                WHERE content IS NOT NULL 
                AND content != ''
                ORDER BY create_time DESC
                LIMIT 1000
                """
            elif platform == 'douyin':
                query = """
                SELECT content, create_time, like_count
                FROM douyin_aweme_comment 
                WHERE content IS NOT NULL 
                AND content != ''
                ORDER BY create_time DESC
                LIMIT 1000
                """
            
            df = pd.read_sql(query, self.engine)
            
            # 转换数值字段为数值类型
            if 'like_count' in df.columns:
                df['like_count'] = pd.to_numeric(df['like_count'], errors='coerce').fillna(0)
            
            # 转换时间戳
            if 'create_time' in df.columns:
                df['create_time'] = pd.to_datetime(df['create_time'], unit='s', errors='coerce')
            
            # Simple sentiment analysis using keyword matching
            positive_words = ['好', '棒', '赞', '喜欢', '爱', '优秀', '厉害', '不错', '完美', '精彩']
            negative_words = ['差', '坏', '烂', '垃圾', '无聊', '难看', '失望', '讨厌', '恶心', '糟糕']
            
            def analyze_sentiment(text):
                if pd.isna(text):
                    return 'neutral'
                
                text = str(text).lower()
                pos_count = sum(1 for word in positive_words if word in text)
                neg_count = sum(1 for word in negative_words if word in text)
                
                if pos_count > neg_count:
                    return 'positive'
                elif neg_count > pos_count:
                    return 'negative'
                else:
                    return 'neutral'
            
            df['sentiment'] = df['content'].apply(analyze_sentiment)
            
            return df
            
        except Exception as e:
            st.error(f"Error in sentiment analysis: {e}")
            return pd.DataFrame()
    
    def get_trending_topics(self, platform='bilibili', limit=20):
        """Extract trending topics from titles and descriptions"""
        try:
            if platform == 'bilibili':
                query = """
                SELECT title, desc, create_time, liked_count, video_play_count
                FROM bilibili_video 
                WHERE (title IS NOT NULL OR desc IS NOT NULL)
                AND create_time > UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 7 DAY))
                ORDER BY liked_count DESC
                LIMIT 1000
                """
            elif platform == 'douyin':
                query = """
                SELECT title, desc, create_time, liked_count, comment_count
                FROM douyin_aweme 
                WHERE (title IS NOT NULL OR desc IS NOT NULL)
                AND create_time > UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 7 DAY))
                ORDER BY liked_count DESC
                LIMIT 1000
                """
            
            df = pd.read_sql(query, self.engine)
            
            # 转换数值字段为数值类型
            numeric_columns = ['liked_count', 'video_play_count', 'comment_count']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # 转换时间戳
            if 'create_time' in df.columns:
                df['create_time'] = pd.to_datetime(df['create_time'], unit='s', errors='coerce')
            
            # Extract keywords (simplified)
            import jieba
            import re
            
            def extract_keywords(text):
                if pd.isna(text):
                    return []
                
                # Clean text
                text = re.sub(r'[^\u4e00-\u9fff\w]', ' ', str(text))
                # Use jieba for Chinese text segmentation
                words = jieba.cut(text)
                # Filter out stop words and short words
                stop_words = set(['的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'])
                keywords = [word for word in words if len(word) > 1 and word not in stop_words]
                return keywords
            
            # Combine title and description
            df['combined_text'] = df['title'].fillna('') + ' ' + df['desc'].fillna('')
            df['keywords'] = df['combined_text'].apply(extract_keywords)
            
            # Count keyword frequency
            all_keywords = []
            for keywords in df['keywords']:
                all_keywords.extend(keywords)
            
            keyword_counts = pd.Series(all_keywords).value_counts().head(limit)
            
            return df, keyword_counts
            
        except Exception as e:
            st.error(f"Error extracting trending topics: {e}")
            return pd.DataFrame(), pd.Series()
    
    def get_user_behavior_analysis(self, platform='bilibili'):
        """Analyze user behavior patterns"""
        try:
            if platform == 'bilibili':
                query = """
                SELECT 
                    v.nickname as creator,
                    v.user_id,
                    COUNT(v.video_id) as video_count,
                    AVG(v.liked_count) as avg_likes,
                    AVG(v.video_play_count) as avg_plays,
                    MAX(v.create_time) as last_activity,
                    MIN(v.create_time) as first_activity
                FROM bilibili_video v
                GROUP BY v.user_id, v.nickname
                HAVING video_count >= 5
                ORDER BY avg_likes DESC
                LIMIT 100
                """
            elif platform == 'douyin':
                query = """
                SELECT 
                    v.nickname as creator,
                    v.user_id,
                    COUNT(v.aweme_id) as video_count,
                    AVG(CAST(v.liked_count AS DECIMAL)) as avg_likes,
                    AVG(CAST(v.comment_count AS DECIMAL)) as avg_comments,
                    MAX(v.create_time) as last_activity,
                    MIN(v.create_time) as first_activity
                FROM douyin_aweme v
                WHERE v.liked_count IS NOT NULL AND v.comment_count IS NOT NULL
                GROUP BY v.user_id, v.nickname
                HAVING video_count >= 5
                ORDER BY avg_likes DESC
                LIMIT 100
                """
            
            df = pd.read_sql(query, self.engine)
            df['last_activity'] = pd.to_datetime(df['last_activity'], unit='s')
            df['first_activity'] = pd.to_datetime(df['first_activity'], unit='s')
            df['activity_span_days'] = (df['last_activity'] - df['first_activity']).dt.days
            
            return df
            
        except Exception as e:
            st.error(f"Error in user behavior analysis: {e}")
            return pd.DataFrame()
    
    def get_content_performance_prediction(self, platform='bilibili'):
        """Simple content performance prediction based on historical data"""
        try:
            if platform == 'bilibili':
                query = """
                SELECT 
                    title,
                    desc,
                    liked_count,
                    video_play_count,
                    video_favorite_count,
                    video_share_count,
                    video_coin_count,
                    create_time,
                    source_keyword
                FROM bilibili_video 
                WHERE liked_count IS NOT NULL 
                AND video_play_count IS NOT NULL
                ORDER BY create_time DESC
                LIMIT 1000
                """
            
            df = pd.read_sql(query, self.engine)
            
            # 转换数值字段为数值类型
            numeric_columns = ['liked_count', 'video_play_count', 'video_favorite_count', 
                              'video_share_count', 'video_coin_count']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # 转换时间戳
            if 'create_time' in df.columns:
                df['create_time'] = pd.to_datetime(df['create_time'], unit='s', errors='coerce')
            
            # Calculate performance score
            df['performance_score'] = (
                df['liked_count'] * 0.4 +
                df['video_play_count'] * 0.3 +
                df['video_favorite_count'] * 0.2 +
                df['video_share_count'] * 0.1
            )
            
            # Categorize performance
            score_percentiles = df['performance_score'].quantile([0.25, 0.5, 0.75])
            
            def categorize_performance(score):
                if score >= score_percentiles[0.75]:
                    return 'High Performance'
                elif score >= score_percentiles[0.5]:
                    return 'Medium Performance'
                elif score >= score_percentiles[0.25]:
                    return 'Low-Medium Performance'
                else:
                    return 'Low Performance'
            
            df['performance_category'] = df['performance_score'].apply(categorize_performance)
            
            return df
            
        except Exception as e:
            st.error(f"Error in performance prediction: {e}")
            return pd.DataFrame()

def show_advanced_analytics():
    """Display advanced analytics in Streamlit"""
    st.markdown('<div class="main-header">🔬 Advanced Analytics</div>', unsafe_allow_html=True)
    
    analytics = AdvancedAnalytics()
    
    # Platform selection
    platform = st.selectbox("Select Platform", ["Bilibili", "Douyin"], key="adv_platform")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Sentiment Analysis", "Trending Topics", "User Behavior", "Performance Prediction"])
    
    with tab1:
        st.subheader("😊 Sentiment Analysis")
        
        sentiment_df = analytics.get_sentiment_analysis(platform.lower())
        
        if not sentiment_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Sentiment distribution
                sentiment_counts = sentiment_df['sentiment'].value_counts()
                fig = px.pie(values=sentiment_counts.values, names=sentiment_counts.index,
                           title=f'{platform} Comment Sentiment Distribution')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Sentiment over time
                sentiment_time = sentiment_df.groupby([sentiment_df['create_time'].dt.date, 'sentiment']).size().reset_index(name='count')
                sentiment_time.columns = ['Date', 'Sentiment', 'Count']
                
                fig = px.line(sentiment_time, x='Date', y='Count', color='Sentiment',
                             title='Sentiment Trends Over Time')
                st.plotly_chart(fig, use_container_width=True)
            
            # Top comments by likes
            st.subheader("💬 Top Liked Comments")
            if 'like_count' in sentiment_df.columns:
                # 确保 like_count 是数值类型
                sentiment_df['like_count'] = pd.to_numeric(sentiment_df['like_count'], errors='coerce').fillna(0)
            top_comments = sentiment_df.nlargest(10, 'like_count')[['content', 'like_count', 'sentiment']]
            st.dataframe(top_comments, use_container_width=True)
            else:
                st.warning("like_count 列不存在")
        else:
            st.warning(f"No comment data available for {platform}")
    
    with tab2:
        st.subheader("🔥 Trending Topics Analysis")
        
        topics_df, keyword_counts = analytics.get_trending_topics(platform.lower())
        
        if not topics_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Top keywords
                fig = px.bar(x=keyword_counts.values, y=keyword_counts.index, orientation='h',
                           title=f'Top {len(keyword_counts)} Trending Keywords')
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Keyword performance
                keyword_performance = topics_df.groupby('source_keyword').agg({
                    'liked_count': 'mean',
                    'video_play_count' if platform == 'Bilibili' else 'comment_count': 'mean'
                }).reset_index()
                keyword_performance = keyword_performance.sort_values('liked_count', ascending=False).head(10)
                
                fig = px.scatter(keyword_performance, x='liked_count', y='video_play_count' if platform == 'Bilibili' else 'comment_count',
                               size='liked_count', color='source_keyword',
                               title='Keyword Performance (Likes vs Engagement)')
                st.plotly_chart(fig, use_container_width=True)
            
            # Recent trending content
            st.subheader("📈 Recent High-Performing Content")
            if 'liked_count' in topics_df.columns:
                # 确保 liked_count 是数值类型
                topics_df['liked_count'] = pd.to_numeric(topics_df['liked_count'], errors='coerce').fillna(0)
            trending_content = topics_df.nlargest(10, 'liked_count')[['title', 'liked_count', 'create_time']]
            st.dataframe(trending_content, use_container_width=True)
            else:
                st.warning("liked_count 列不存在")
        else:
            st.warning(f"No topic data available for {platform}")
    
    with tab3:
        st.subheader("👥 User Behavior Analysis")
        
        behavior_df = analytics.get_user_behavior_analysis(platform.lower())
        
        if not behavior_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Video count vs average likes
                fig = px.scatter(behavior_df, x='video_count', y='avg_likes', 
                               size='avg_likes', color='creator',
                               title='Content Volume vs Quality (Avg Likes)')
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Activity span analysis
                fig = px.histogram(behavior_df, x='activity_span_days', nbins=20,
                                   title='Creator Activity Span Distribution')
                st.plotly_chart(fig, use_container_width=True)
            
            # Top creators analysis
            st.subheader("⭐ Top Creator Insights")
            # 确保 avg_likes 是数值类型
            if 'avg_likes' in behavior_df.columns:
                behavior_df['avg_likes'] = pd.to_numeric(behavior_df['avg_likes'], errors='coerce').fillna(0)
            top_creators = behavior_df.nlargest(15, 'avg_likes')[['creator', 'video_count', 'avg_likes', 'activity_span_days']]
            
            fig = make_subplots(rows=1, cols=2, 
                              subplot_titles=('Video Count vs Avg Likes', 'Activity Span vs Avg Likes'))
            
            fig.add_trace(go.Scatter(x=top_creators['video_count'], y=top_creators['avg_likes'],
                                   mode='markers+text', text=top_creators['creator'],
                                   textposition='top center', name='Video Count'),
                         row=1, col=1)
            
            fig.add_trace(go.Scatter(x=top_creators['activity_span_days'], y=top_creators['avg_likes'],
                                   mode='markers+text', text=top_creators['creator'],
                                   textposition='top center', name='Activity Span'),
                         row=1, col=2)
            
            fig.update_layout(height=500, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            
            # Detailed creator table
            st.dataframe(top_creators, use_container_width=True)
        else:
            st.warning(f"No user behavior data available for {platform}")
    
    with tab4:
        st.subheader("🎯 Content Performance Prediction")
        
        prediction_df = analytics.get_content_performance_prediction(platform.lower())
        
        if not prediction_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Performance category distribution
                perf_counts = prediction_df['performance_category'].value_counts()
                fig = px.pie(values=perf_counts.values, names=perf_counts.index,
                           title='Content Performance Distribution')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Performance score distribution
                fig = px.histogram(prediction_df, x='performance_score', nbins=30,
                                   title='Performance Score Distribution')
                st.plotly_chart(fig, use_container_width=True)
            
            # High performance content characteristics
            st.subheader("🏆 High Performance Content Analysis")
            high_perf = prediction_df[prediction_df['performance_category'] == 'High Performance']
            
            if not high_perf.empty:
                st.write(f"Found {len(high_perf)} high-performing videos")
                
                # Show top performers
                # 确保 performance_score 是数值类型
                if 'performance_score' in high_perf.columns:
                    high_perf['performance_score'] = pd.to_numeric(high_perf['performance_score'], errors='coerce').fillna(0)
                top_performers = high_perf.nlargest(10, 'performance_score')[['title', 'performance_score', 'liked_count', 'video_play_count']]
                st.dataframe(top_performers, use_container_width=True)
                
                # Keyword analysis for high performers
                if 'source_keyword' in high_perf.columns:
                    high_perf_keywords = high_perf['source_keyword'].value_counts().head(10)
                    fig = px.bar(x=high_perf_keywords.values, y=high_perf_keywords.index, orientation='h',
                               title='Top Keywords in High-Performing Content')
                    st.plotly_chart(fig, use_container_width=True)
            
            # Performance prediction insights
            st.subheader("💡 Performance Insights")
            
            insights = []
            
            # Average metrics by category
            category_stats = prediction_df.groupby('performance_category').agg({
                'liked_count': 'mean',
                'video_play_count': 'mean',
                'video_favorite_count': 'mean',
                'video_share_count': 'mean'
            }).round(2)
            
            st.write("Average metrics by performance category:")
            st.dataframe(category_stats, use_container_width=True)
            
            # Success factors
            high_perf_avg = prediction_df[prediction_df['performance_category'] == 'High Performance'].agg({
                'liked_count': 'mean',
                'video_play_count': 'mean',
                'video_favorite_count': 'mean',
                'video_share_count': 'mean'
            })
            
            overall_avg = prediction_df.agg({
                'liked_count': 'mean',
                'video_play_count': 'mean',
                'video_favorite_count': 'mean',
                'video_share_count': 'mean'
            })
            
            st.write("Success factors (High Performance vs Overall Average):")
            comparison_df = pd.DataFrame({
                'High Performance': high_perf_avg,
                'Overall Average': overall_avg,
                'Performance Ratio': high_perf_avg / overall_avg
            }).round(2)
            
            st.dataframe(comparison_df, use_container_width=True)
            
        else:
            st.warning(f"No prediction data available for {platform}")

if __name__ == "__main__":
    show_advanced_analytics()