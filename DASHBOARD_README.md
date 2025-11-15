# MediaCrawler Analytics Dashboard

A comprehensive interactive analytics dashboard for MediaCrawler data, providing real-time monitoring, advanced analytics, and cross-platform insights for social media content analysis.

## Features

### 📊 Core Analytics
- **Multi-platform Support**: Analyze data from Bilibili, Douyin, Kuaishou, Weibo, Xiaohongshu, and Zhihu
- **Interactive Visualizations**: Rich charts and graphs using Plotly and Altair
- **Real-time Monitoring**: Live data updates and alerts
- **Cross-platform Analysis**: Compare performance across different social media platforms

### 🔍 Advanced Analytics
- **Sentiment Analysis**: Analyze user sentiment in comments and content
- **Trending Topics**: Identify trending topics and hashtags
- **User Behavior Analysis**: Understand user engagement patterns
- **Content Performance Prediction**: Predict content success metrics

### 📈 Dashboard Features
- **Overview Dashboard**: High-level metrics and KPIs
- **Platform-specific Analytics**: Detailed analysis for each supported platform
- **Customizable Date Ranges**: Flexible time-based filtering
- **Data Export**: Export analytics reports in multiple formats
- **Auto-refresh**: Configurable automatic data refresh

## Installation

### Prerequisites
- Python 3.7+
- MySQL/PostgreSQL database (for MediaCrawler data)

### Quick Start

1. **Install Dependencies**
   ```bash
   pip install streamlit plotly seaborn altair pandas numpy
   ```

2. **Start the Dashboard**
   ```bash
   python start_dashboard.py
   ```

3. **Access the Dashboard**
   - Open your browser to `http://localhost:8501`
   - The dashboard will automatically open in your default browser

## Usage

### Command Line Options

```bash
# Start with default settings
python start_dashboard.py

# Use custom port
python start_dashboard.py --port 8080

# Listen on all interfaces (accessible from network)
python start_dashboard.py --host 0.0.0.0

# Enable debug mode
python start_dashboard.py --debug

# Don't open browser automatically
python start_dashboard.py --no-open

# Check dependencies only
python start_dashboard.py --check-deps
```

### Dashboard Navigation

1. **Overview**: Main dashboard with high-level metrics
2. **Bilibili Analytics**: Detailed Bilibili platform analysis
3. **Douyin Analytics**: Detailed Douyin platform analysis
4. **Cross-Platform Analysis**: Compare platforms side-by-side
5. **Advanced Analytics**: Sentiment analysis, trending topics, predictions
6. **Real-Time Monitor**: Live data monitoring and alerts
7. **Data Export**: Export reports and data

### Configuration

The dashboard uses `dashboard_config.py` for configuration:

- **Database Settings**: Configure database connections
- **Visualization Preferences**: Customize colors and themes
- **Real-time Monitoring**: Set update intervals and alert thresholds
- **Analytics Parameters**: Configure sentiment analysis and prediction models

## Semantic Enrichment & Knowledge Graph

The dashboard includes a **Semantic Insights** page backed by the comment enrichment pipeline:

> 📖 **详细配置说明**: 请参考 [SEMANTIC_CONFIG_README.md](./SEMANTIC_CONFIG_README.md)

1. **Set environment variables**
   
   **Windows PowerShell:**
   ```powershell
   $env:COMMENT_LLM_API_KEY="your-openai-compatible-key"
   $env:COMMENT_LLM_MODEL="gpt-4o-mini"
   $env:NEO4J_URI="bolt://localhost:7687"
   $env:NEO4J_USER="neo4j"
   $env:NEO4J_PASSWORD="password"
   ```
   
   **Windows CMD:**
   ```cmd
   set COMMENT_LLM_API_KEY=your-openai-compatible-key
   set COMMENT_LLM_MODEL=gpt-4o-mini
   set NEO4J_URI=bolt://localhost:7687
   set NEO4J_USER=neo4j
   set NEO4J_PASSWORD=password
   ```
   
   **Linux/macOS:**
   ```bash
   export COMMENT_LLM_API_KEY="your-openai-compatible-key"
   export COMMENT_LLM_MODEL="gpt-4o-mini"
   export NEO4J_URI="bolt://localhost:7687"
   export NEO4J_USER="neo4j"
   export NEO4J_PASSWORD="password"
   ```
   
   Optional: `COMMENT_LLM_BASE_URL`, `COMMENT_LLM_BATCH_SIZE`, `COMMENT_LLM_PROVIDER`.
   
   **Note**: If `COMMENT_LLM_API_KEY` is not set, the system will try to use `OPENAI_API_KEY` as a fallback.

2. **Install extra dependencies**
   ```bash
   pip install neo4j openai
   ```

3. **Run the enrichment pipeline**
   ```bash
   python run_semantic_pipeline.py ./data/bili/json --platform bilibili --comment-id-field id --content-field content
   ```
   Additional options:
   - `--source-table`: Reference table name for MySQL storage.
   - `--language`: Comment language tag (default `zh`).
   - `--limit`: Process the first N comments only (quick smoke test).

4. **Refresh Streamlit**
   Launch or refresh the dashboard, then open **Semantic Insights** to review:
   - Sentiment distribution and trend charts
   - Topic frequency and leaderboards
   - Entity mention statistics from MySQL
   - Latest comment–entity relations from Neo4j

> 提示：若当前无法连接 Neo4j，页面会提示“Neo4j 未连接或暂无关联数据”，不会影响其它图表。

## Architecture

### File Structure
```
MediaCrawler/
├── dashboard.py              # Main dashboard application
├── start_dashboard.py        # Startup script
├── dashboard_config.py       # Configuration settings
├── advanced_analytics.py     # Advanced analytics modules
├── realtime_monitor.py       # Real-time monitoring
├── database/
│   ├── models.py            # SQLAlchemy models
│   └── db.py                # Database connection utilities
└── requirements.txt         # Python dependencies
```

### Key Components

#### Dashboard Application (`dashboard.py`)
- Streamlit-based web interface
- Multi-page navigation
- Interactive data visualizations
- Responsive design with custom CSS

#### Advanced Analytics (`advanced_analytics.py`)
- Sentiment analysis using keyword matching
- Trending topic identification
- User behavior pattern analysis
- Content performance prediction algorithms

#### Real-time Monitor (`realtime_monitor.py`)
- Live data fetching and updates
- Alert system for anomalies
- Activity timeline visualization
- Platform comparison metrics

#### Configuration (`dashboard_config.py`)
- Centralized settings management
- Platform-specific configurations
- Visualization preferences
- Alert and monitoring settings

## Data Sources

The dashboard connects to MediaCrawler's database and provides analytics for:

### Bilibili Data
- Video metadata and statistics
- User profiles and interactions
- Comments and engagement metrics
- Content categories and tags

### Douyin Data
- Video information and metrics
- User data and engagement
- Comments and reactions
- Trending content analysis

### Cross-Platform Data
- Comparative performance metrics
- User behavior across platforms
- Content success patterns
- Platform-specific trends

## Customization

### Adding New Platforms

1. Update `dashboard_config.py` with platform settings
2. Add platform-specific data loading functions in `dashboard.py`
3. Create platform-specific analytics modules
4. Update navigation and UI components

### Custom Visualizations

1. Modify visualization functions in `dashboard.py`
2. Update color schemes in `dashboard_config.py`
3. Add new chart types using Plotly or Altair
4. Configure display preferences

### Advanced Analytics

1. Extend sentiment analysis keywords in `dashboard_config.py`
2. Add new prediction models in `advanced_analytics.py`
3. Configure trending topic algorithms
4. Customize user behavior analysis

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check database configuration in `dashboard_config.py`
   - Verify database is running and accessible
   - Check network connectivity

2. **Missing Dependencies**
   - Run `python start_dashboard.py --check-deps`
   - Install missing packages manually
   - Check Python version compatibility

3. **Port Already in Use**
   - Use a different port with `--port` option
   - Check for other applications using the port
   - Restart the application

4. **Data Loading Issues**
   - Verify database has MediaCrawler data
   - Check date range filters
   - Review platform-specific data availability

### Performance Optimization

1. **Large Dataset Handling**
   - Use date range filters to limit data
   - Enable pagination for large tables
   - Optimize database queries

2. **Memory Usage**
   - Reduce refresh frequency
   - Limit concurrent data loading
   - Use data sampling for large datasets

3. **Response Time**
   - Enable caching for frequently accessed data
   - Optimize visualization rendering
   - Use efficient data aggregation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is part of the MediaCrawler project and follows the same licensing terms.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the configuration options
3. Check application logs
4. Submit an issue with detailed information

---

**Note**: This dashboard is designed to work with MediaCrawler data. Ensure your MediaCrawler database is properly configured and contains data before using the dashboard.