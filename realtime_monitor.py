import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
from collections import deque
import threading
import queue
from database.db import get_db_engine
import numpy as np

class RealTimeMonitor:
    def __init__(self, update_interval=30):
        self.engine = get_db_engine()
        self.update_interval = update_interval
        self.data_queue = queue.Queue()
        self.running = False
        self.thread = None
        
        # Data storage for real-time charts
        self.time_series_data = {
            'timestamps': deque(maxlen=100),
            'bilibili_videos': deque(maxlen=100),
            'douyin_videos': deque(maxlen=100),
            'total_engagement': deque(maxlen=100)
        }
    
    def fetch_latest_data(self):
        """Fetch the latest data from database"""
        try:
            # Get latest videos in the last update interval
            current_time = datetime.now()
            time_threshold = int((current_time - timedelta(seconds=self.update_interval)).timestamp())
            
            # Bilibili latest data
            bilibili_query = f"""
            SELECT COUNT(*) as new_videos, 
                   COALESCE(SUM(liked_count), 0) as total_likes,
                   COALESCE(SUM(video_play_count), 0) as total_plays
            FROM bilibili_video 
            WHERE create_time > {time_threshold}
            """
            
            # Douyin latest data
            douyin_query = f"""
            SELECT COUNT(*) as new_videos, 
                   COALESCE(SUM(CAST(liked_count AS INTEGER)), 0) as total_likes,
                   COALESCE(SUM(CAST(comment_count AS INTEGER)), 0) as total_comments
            FROM douyin_aweme 
            WHERE create_time > {time_threshold}
            """
            
            bilibili_stats = pd.read_sql(bilibili_query, self.engine)
            douyin_stats = pd.read_sql(douyin_query, self.engine)
            
            return {
                'timestamp': current_time,
                'bilibili_new_videos': bilibili_stats.iloc[0]['new_videos'],
                'bilibili_likes': bilibili_stats.iloc[0]['total_likes'],
                'bilibili_plays': bilibili_stats.iloc[0]['total_plays'],
                'douyin_new_videos': douyin_stats.iloc[0]['new_videos'],
                'douyin_likes': douyin_stats.iloc[0]['total_likes'],
                'douyin_comments': douyin_stats.iloc[0]['total_comments']
            }
            
        except Exception as e:
            st.error(f"Error fetching latest data: {e}")
            return None
    
    def background_update(self):
        """Background thread for continuous data updates"""
        while self.running:
            try:
                data = self.fetch_latest_data()
                if data:
                    self.data_queue.put(data)
                time.sleep(self.update_interval)
            except Exception as e:
                st.error(f"Background update error: {e}")
                time.sleep(self.update_interval)
    
    def start_monitoring(self):
        """Start real-time monitoring"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.background_update, daemon=True)
            self.thread.start()
            return True
        return False
    
    def stop_monitoring(self):
        """Stop real-time monitoring"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
    
    def get_update(self):
        """Get latest data update from queue"""
        try:
            return self.data_queue.get_nowait()
        except queue.Empty:
            return None
    
    def get_platform_summary(self):
        """Get current platform summary statistics"""
        try:
            # Get total counts and recent activity
            queries = {
                'bilibili_total': "SELECT COUNT(*) as count FROM bilibili_video",
                'bilibili_today': f"SELECT COUNT(*) as count FROM bilibili_video WHERE create_time > {int((datetime.now() - timedelta(days=1)).timestamp())}",
                'douyin_total': "SELECT COUNT(*) as count FROM douyin_aweme",
                'douyin_today': f"SELECT COUNT(*) as count FROM douyin_aweme WHERE create_time > {int((datetime.now() - timedelta(days=1)).timestamp())}",
                'bilibili_top_creator': """
                    SELECT nickname, COUNT(*) as video_count, SUM(liked_count) as total_likes 
                    FROM bilibili_video 
                    GROUP BY nickname 
                    ORDER BY total_likes DESC 
                    LIMIT 1
                """,
                'douyin_top_creator': """
                    SELECT nickname, COUNT(*) as video_count, SUM(CAST(liked_count AS INTEGER)) as total_likes 
                    FROM douyin_aweme 
                    GROUP BY nickname 
                    ORDER BY total_likes DESC 
                    LIMIT 1
                """
            }
            
            results = {}
            for key, query in queries.items():
                try:
                    df = pd.read_sql(query, self.engine)
                    if not df.empty:
                        if 'top_creator' in key:
                            results[key] = df.iloc[0].to_dict()
                        else:
                            results[key] = df.iloc[0]['count']
                    else:
                        results[key] = 0
                except:
                    results[key] = 0
            
            return results
            
        except Exception as e:
            st.error(f"Error getting platform summary: {e}")
            return {}

def show_realtime_dashboard():
    """Display real-time monitoring dashboard"""
    st.markdown('<div class="main-header">📡 Real-Time Monitoring Dashboard</div>', unsafe_allow_html=True)
    
    # Initialize monitor
    if 'monitor' not in st.session_state:
        st.session_state.monitor = RealTimeMonitor(update_interval=30)
    
    monitor = st.session_state.monitor
    
    # Control panel
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("🚀 Start Monitoring"):
            if monitor.start_monitoring():
                st.success("Real-time monitoring started!")
            else:
                st.warning("Monitoring already running!")
    
    with col2:
        if st.button("⏹️ Stop Monitoring"):
            monitor.stop_monitoring()
            st.info("Real-time monitoring stopped!")
    
    with col3:
        st.info(f"Status: {'🟢 Running' if monitor.running else '🔴 Stopped'}")
    
    st.divider()
    
    # Get platform summary
    summary = monitor.get_platform_summary()
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Bilibili Total Videos",
            f"{summary.get('bilibili_total', 0):,}",
            f"+{summary.get('bilibili_today', 0)} today"
        )
    
    with col2:
        st.metric(
            "Douyin Total Videos",
            f"{summary.get('douyin_total', 0):,}",
            f"+{summary.get('douyin_today', 0)} today"
        )
    
    with col3:
        bl_top = summary.get('bilibili_top_creator', {})
        if bl_top and isinstance(bl_top, dict):
            st.metric(
                "Top Bilibili Creator",
                bl_top.get('nickname', 'N/A'),
                f"{bl_top.get('video_count', 0)} videos, {bl_top.get('total_likes', 0):,} likes"
            )
        else:
            st.metric("Top Bilibili Creator", "N/A", "No data")
    
    with col4:
        dy_top = summary.get('douyin_top_creator', {})
        if dy_top and isinstance(dy_top, dict):
            st.metric(
                "Top Douyin Creator",
                dy_top.get('nickname', 'N/A'),
                f"{dy_top.get('video_count', 0)} videos, {dy_top.get('total_likes', 0):,} likes"
            )
        else:
            st.metric("Top Douyin Creator", "N/A", "No data")
    
    st.divider()
    
    # Real-time charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Activity Timeline")
        
        # Create placeholder for real-time chart
        activity_chart = st.empty()
        
        # Initialize time series data
        if 'time_data' not in st.session_state:
            st.session_state.time_data = {
                'timestamps': [],
                'bilibili_activity': [],
                'douyin_activity': []
            }
        
        # Update chart with new data
        latest_data = monitor.get_update()
        if latest_data:
            # Add new data point
            st.session_state.time_data['timestamps'].append(latest_data['timestamp'])
            st.session_state.time_data['bilibili_activity'].append(
                latest_data['bilibili_new_videos'] + latest_data['bilibili_likes'] // 1000
            )
            st.session_state.time_data['douyin_activity'].append(
                latest_data['douyin_new_videos'] + latest_data['douyin_likes'] // 1000
            )
        
        # Create activity chart
        if len(st.session_state.time_data['timestamps']) > 0:
            activity_df = pd.DataFrame({
                'Timestamp': st.session_state.time_data['timestamps'],
                'Bilibili': st.session_state.time_data['bilibili_activity'],
                'Douyin': st.session_state.time_data['douyin_activity']
            })
            
            fig = px.line(activity_df, x='Timestamp', y=['Bilibili', 'Douyin'],
                         title='Platform Activity Over Time')
            fig.update_layout(height=400)
            activity_chart.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No real-time data available yet. Start monitoring to see activity timeline.")
    
    with col2:
        st.subheader("🔔 Recent Activity")
        
        # Create activity log
        if 'activity_log' not in st.session_state:
            st.session_state.activity_log = []
        
        # Add new activity to log
        latest_data = monitor.get_update()
        if latest_data:
            activity_entry = {
                'time': latest_data['timestamp'].strftime('%H:%M:%S'),
                'bilibili_new': latest_data['bilibili_new_videos'],
                'bilibili_likes': latest_data['bilibili_likes'],
                'douyin_new': latest_data['douyin_new_videos'],
                'douyin_likes': latest_data['douyin_likes']
            }
            st.session_state.activity_log.insert(0, activity_entry)
            
            # Keep only last 10 entries
            if len(st.session_state.activity_log) > 10:
                st.session_state.activity_log = st.session_state.activity_log[:10]
        
        # Display activity log
        if st.session_state.activity_log:
            for entry in st.session_state.activity_log:
                col_a, col_b, col_c, col_d, col_e = st.columns(5)
                with col_a:
                    st.write(f"**{entry['time']}**")
                with col_b:
                    st.write(f"📺 Bilibili: +{entry['bilibili_new']} videos")
                with col_c:
                    st.write(f"👍 +{entry['bilibili_likes']:,} likes")
                with col_d:
                    st.write(f"🎵 Douyin: +{entry['douyin_new']} videos")
                with col_e:
                    st.write(f"❤️ +{entry['douyin_likes']:,} likes")
        else:
            st.info("No recent activity to display")
    
    st.divider()
    
    # Platform comparison
    st.subheader("⚡ Platform Performance Comparison")
    
    if latest_data:
        comparison_data = {
            'Platform': ['Bilibili', 'Douyin'],
            'New Videos': [latest_data['bilibili_new_videos'], latest_data['douyin_new_videos']],
            'New Likes': [latest_data['bilibili_likes'], latest_data['douyin_likes']],
            'Engagement Rate': [
                latest_data['bilibili_likes'] / max(latest_data['bilibili_new_videos'], 1),
                latest_data['douyin_likes'] / max(latest_data['douyin_new_videos'], 1)
            ]
        }
        
        comparison_df = pd.DataFrame(comparison_data)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(comparison_df, x='Platform', y='New Videos',
                        title='New Videos Comparison')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.bar(comparison_df, x='Platform', y='New Likes',
                        title='New Likes Comparison')
            st.plotly_chart(fig, use_container_width=True)
    
    # Auto-refresh
    if monitor.running:
        time.sleep(2)  # Short delay for better UX
        st.rerun()

if __name__ == "__main__":
    show_realtime_dashboard()