# Dashboard Configuration

DASHBOARD_CONFIG = {
    'title': 'MediaCrawler Analytics Dashboard',
    'description': 'Interactive analytics dashboard for social media crawling data',
    'version': '1.0.0',
    'author': 'MediaCrawler Team',
    
    # Database settings
    'database': {
        'connection_timeout': 30,
        'query_timeout': 60,
        'max_retries': 3,
        'cache_ttl': 300  # 5 minutes
    },
    
    # Dashboard settings
    'dashboard': {
        'theme': 'light',
        'page_title': 'MediaCrawler Analytics',
        'favicon': '📊',
        'layout': 'wide',
        'sidebar_state': 'expanded'
    },
    
    # Visualization settings
    'visualization': {
        'default_chart_height': 400,
        'color_palette': {
            'bilibili': '#fb7299',
            'douyin': '#000000',
            'kuaishou': '#ff6100',
            'weibo': '#e6162d',
            'xiaohongshu': '#ff2442',
            'zhihu': '#0084ff'
        },
        'chart_themes': {
            'light': 'plotly_white',
            'dark': 'plotly_dark'
        }
    },
    
    # Real-time monitoring
    'monitoring': {
        'update_interval': 30,  # seconds
        'max_data_points': 100,
        'alert_thresholds': {
            'video_upload_rate': 100,  # videos per hour
            'engagement_rate_drop': 0.5,  # 50% drop
            'error_rate': 0.1  # 10% error rate
        }
    },
    
    # Analytics settings
    'analytics': {
        'sentiment_analysis': {
            'positive_words': ['好', '棒', '赞', '喜欢', '爱', '优秀', '厉害', '不错', '完美', '精彩', 'awesome', 'good', 'great', 'love', 'perfect'],
            'negative_words': ['差', '坏', '烂', '垃圾', '无聊', '难看', '失望', '讨厌', '恶心', '糟糕', 'bad', 'terrible', 'hate', 'awful', 'disappointing']
        },
        'trending_analysis': {
            'min_keyword_length': 2,
            'max_keywords': 50,
            'time_window_days': 7
        },
        'performance_prediction': {
            'weights': {
                'likes': 0.4,
                'plays': 0.3,
                'favorites': 0.2,
                'shares': 0.1
            }
        }
    },
    
    # Export settings
    'export': {
        'formats': ['CSV', 'Excel', 'JSON'],
        'max_rows': 10000,
        'include_metadata': True,
        'compression': False
    },
    
    # Platform-specific settings
    'platforms': {
        'bilibili': {
            'enabled': True,
            'tables': ['bilibili_video', 'bilibili_video_comment', 'bilibili_up_info'],
            'metrics': ['video_count', 'likes', 'plays', 'coins', 'favorites', 'shares'],
            'update_frequency': 'hourly'
        },
        'douyin': {
            'enabled': True,
            'tables': ['douyin_aweme', 'douyin_aweme_comment', 'dy_creator'],
            'metrics': ['video_count', 'likes', 'comments', 'shares', 'collections'],
            'update_frequency': 'hourly'
        },
        'kuaishou': {
            'enabled': True,
            'tables': ['kuaishou_video', 'kuaishou_video_comment'],
            'metrics': ['video_count', 'likes', 'views', 'comments'],
            'update_frequency': 'daily'
        },
        'weibo': {
            'enabled': True,
            'tables': ['weibo_note'],
            'metrics': ['post_count', 'likes', 'comments', 'shares'],
            'update_frequency': 'hourly'
        },
        'xiaohongshu': {
            'enabled': True,
            'tables': ['xhs_note'],
            'metrics': ['note_count', 'likes', 'collections', 'comments'],
            'update_frequency': 'daily'
        },
        'zhihu': {
            'enabled': True,
            'tables': ['zhihu_answer', 'zhihu_article'],
            'metrics': ['content_count', 'likes', 'comments'],
            'update_frequency': 'daily'
        }
    }
}

# Helper functions
def get_platform_color(platform):
    """Get platform-specific color"""
    return DASHBOARD_CONFIG['visualization']['color_palette'].get(platform.lower(), '#1f77b4')

def get_chart_theme():
    """Get current chart theme"""
    theme = DASHBOARD_CONFIG['dashboard']['theme']
    return DASHBOARD_CONFIG['visualization']['chart_themes'].get(theme, 'plotly_white')

def validate_date_range(start_date, end_date):
    """Validate date range"""
    if start_date > end_date:
        return False, "Start date must be before end date"
    
    if (end_date - start_date).days > 365:
        return False, "Date range cannot exceed 1 year"
    
    return True, "Valid date range"

def format_number(number):
    """Format large numbers"""
    if number >= 1e9:
        return f"{number/1e9:.1f}B"
    elif number >= 1e6:
        return f"{number/1e6:.1f}M"
    elif number >= 1e3:
        return f"{number/1e3:.1f}K"
    else:
        return str(number)

def get_time_ago(timestamp):
    """Convert timestamp to human-readable time ago"""
    now = datetime.now()
    diff = now - datetime.fromtimestamp(timestamp)
    
    if diff.days > 0:
        return f"{diff.days} days ago"
    elif diff.seconds > 3600:
        return f"{diff.seconds // 3600} hours ago"
    elif diff.seconds > 60:
        return f"{diff.seconds // 60} minutes ago"
    else:
        return "Just now"

# Alert system
class AlertManager:
    def __init__(self):
        self.alerts = []
        self.thresholds = DASHBOARD_CONFIG['monitoring']['alert_thresholds']
    
    def check_alerts(self, data):
        """Check for alert conditions"""
        alerts = []
        
        # Check video upload rate
        if 'video_upload_rate' in data:
            if data['video_upload_rate'] > self.thresholds['video_upload_rate']:
                alerts.append({
                    'type': 'warning',
                    'message': f"High video upload rate: {data['video_upload_rate']} videos/hour",
                    'timestamp': datetime.now()
                })
        
        # Check engagement rate drop
        if 'engagement_rate_drop' in data:
            if data['engagement_rate_drop'] < self.thresholds['engagement_rate_drop']:
                alerts.append({
                    'type': 'danger',
                    'message': f"Engagement rate dropped by {data['engagement_rate_drop']:.1%}",
                    'timestamp': datetime.now()
                })
        
        # Check error rate
        if 'error_rate' in data:
            if data['error_rate'] > self.thresholds['error_rate']:
                alerts.append({
                    'type': 'danger',
                    'message': f"High error rate: {data['error_rate']:.1%}",
                    'timestamp': datetime.now()
                })
        
        self.alerts.extend(alerts)
        return alerts
    
    def get_recent_alerts(self, limit=10):
        """Get recent alerts"""
        return sorted(self.alerts, key=lambda x: x['timestamp'], reverse=True)[:limit]
    
    def clear_alerts(self):
        """Clear all alerts"""
        self.alerts = []

# Initialize alert manager
alert_manager = AlertManager()