// Dashboard JavaScript 主文件

// 全局变量
let charts = {};
let autoRefreshInterval = null;
let refreshIntervalMinutes = 5;

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    setupEventListeners();
    loadInitialData();
});

// 初始化Dashboard
function initializeDashboard() {
    // 设置默认日期
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 30);
    
    document.getElementById('start-date').value = formatDate(startDate);
    document.getElementById('end-date').value = formatDate(endDate);
}

// 设置事件监听器
function setupEventListeners() {
    // 导航切换
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const page = this.dataset.page;
            switchPage(page);
        });
    });

    // 日期变化
    document.getElementById('start-date').addEventListener('change', handleFilterChange);
    document.getElementById('end-date').addEventListener('change', handleFilterChange);

    // 平台选择变化
    document.querySelectorAll('.platform-checkboxes input').forEach(checkbox => {
        checkbox.addEventListener('change', handleFilterChange);
    });

    // 自动刷新
    document.getElementById('auto-refresh').addEventListener('change', function() {
        const enabled = this.checked;
        const intervalInput = document.getElementById('refresh-interval');
        intervalInput.disabled = !enabled;
        
        if (enabled) {
            refreshIntervalMinutes = parseInt(intervalInput.value);
            startAutoRefresh();
        } else {
            stopAutoRefresh();
        }
    });

    // 刷新间隔调整
    document.getElementById('refresh-interval').addEventListener('input', function() {
        refreshIntervalMinutes = parseInt(this.value);
        document.getElementById('refresh-interval-value').textContent = `${refreshIntervalMinutes} 分钟`;
        if (document.getElementById('auto-refresh').checked) {
            stopAutoRefresh();
            startAutoRefresh();
        }
    });
}

// 页面切换
function switchPage(pageName) {
    // 更新导航状态
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-page="${pageName}"]`).classList.add('active');

    // 更新页面显示
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    document.getElementById(`page-${pageName}`).classList.add('active');

    // 加载对应页面数据
    loadPageData(pageName);
}

// 加载初始数据
function loadInitialData() {
    loadPageData('overview');
}

// 加载页面数据
function loadPageData(pageName) {
    switch(pageName) {
        case 'overview':
            loadOverviewData();
            break;
        case 'bilibili':
            loadBilibiliData();
            break;
        case 'douyin':
            loadDouyinData();
            break;
        case 'kuaishou':
            loadKuaishouData();
            break;
        case 'weibo':
            loadWeiboData();
            break;
        case 'zhihu':
            loadZhihuData();
            break;
        case 'tieba':
            loadTiebaData();
            break;
        case 'cross-platform':
            loadCrossPlatformData();
            break;
        case 'semantic':
            loadSemanticData();
            break;
    }
}

// 加载概览数据
async function loadOverviewData() {
    try {
        const response = await fetch('/api/overview');
        const result = await response.json();
        
        if (result.success) {
            // 更新指标
            document.getElementById('metric-total-records').textContent = formatNumber(result.metrics.total_records);
            document.getElementById('metric-active-platforms').textContent = result.metrics.active_platforms;
            document.getElementById('metric-avg-records').textContent = formatNumber(result.metrics.avg_records);
            document.getElementById('metric-total-tables').textContent = result.metrics.total_tables;

            // 绘制图表
            drawOverviewChart(result.data);
            renderOverviewTable(result.data);
        }
    } catch (error) {
        console.error('Error loading overview data:', error);
    }
}

// 绘制概览图表
function drawOverviewChart(data) {
    const ctx = document.getElementById('overview-chart');
    if (charts.overview) {
        charts.overview.destroy();
    }

    charts.overview = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(item => item.platform),
            datasets: [{
                label: '总记录数',
                data: data.map(item => item.total_records),
                backgroundColor: [
                    '#fb7299', '#000000', '#ff6100', 
                    '#e6162d', '#ff2442', '#0084ff'
                ],
                borderColor: '#1e40af',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// 渲染概览表格
function renderOverviewTable(data) {
    const tableContainer = document.getElementById('overview-table');
    let html = '<table><thead><tr><th>平台</th><th>总记录数</th><th>表数量</th></tr></thead><tbody>';
    
    data.forEach(item => {
        html += `<tr>
            <td>${item.platform}</td>
            <td>${formatNumber(item.total_records)}</td>
            <td>${item.tables}</td>
        </tr>`;
    });
    
    html += '</tbody></table>';
    tableContainer.innerHTML = html;
}

// 加载Bilibili数据
async function loadBilibiliData() {
    try {
        const response = await fetch('/api/bilibili');
        const result = await response.json();
        
        if (result.success) {
            // 更新指标
            document.getElementById('bilibili-total-videos').textContent = formatNumber(result.metrics.total_videos);
            document.getElementById('bilibili-avg-likes').textContent = formatNumber(result.metrics.avg_likes);
            document.getElementById('bilibili-avg-plays').textContent = formatNumber(result.metrics.avg_plays);
            document.getElementById('bilibili-creators').textContent = formatNumber(result.metrics.unique_creators);

            // 绘制图表
            drawBilibiliTopCreatorsChart(result.top_creators);
            drawBilibiliTimelineChart(result.timeline);
            renderBilibiliTable(result.data);
        }
    } catch (error) {
        console.error('Error loading Bilibili data:', error);
    }
}

// 绘制Bilibili Top Creators图表
function drawBilibiliTopCreatorsChart(data) {
    const ctx = document.getElementById('bilibili-top-creators-chart');
    if (charts.bilibiliTopCreators) {
        charts.bilibiliTopCreators.destroy();
    }

    charts.bilibiliTopCreators = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(item => item.name),
            datasets: [{
                label: '总点赞数',
                data: data.map(item => item.likes),
                backgroundColor: '#fb7299',
                borderColor: '#1e40af',
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    beginAtZero: true
                }
            }
        }
    });
}

// 绘制Bilibili时间线图表
function drawBilibiliTimelineChart(data) {
    const container = document.getElementById('bilibili-timeline-chart');
    
    const trace = {
        x: data.map(item => item.date),
        y: data.map(item => item.count),
        type: 'scatter',
        mode: 'lines+markers',
        name: '视频数量',
        line: { color: '#fb7299' }
    };

    const layout = {
        title: '每日视频上传量',
        xaxis: { title: '日期' },
        yaxis: { title: '视频数量' },
        height: 300
    };

    Plotly.newPlot(container, [trace], layout);
}

// 渲染Bilibili表格
function renderBilibiliTable(data) {
    const tableContainer = document.getElementById('bilibili-table');
    if (data.length === 0) {
        tableContainer.innerHTML = '<p>暂无数据</p>';
        return;
    }

    const columns = [
        {key: 'video_id', label: '视频ID'},
        {key: 'title', label: '标题'},
        {key: 'nickname', label: '创作者'},
        {key: 'liked_count', label: '点赞数'},
        {key: 'video_play_count', label: '播放数'},
        {key: 'create_time', label: '创建时间'}
    ];
    let html = '<table><thead><tr>';
    columns.forEach(col => {
        html += `<th>${col.label}</th>`;
    });
    html += '</tr></thead><tbody>';

    data.slice(0, 100).forEach(item => {
        html += '<tr>';
        columns.forEach(col => {
            let value = item[col.key] || '-';
            if (col.key === 'create_time' && value !== '-') {
                value = new Date(value).toLocaleDateString('zh-CN');
            } else if (typeof value === 'number') {
                value = formatNumber(value);
            }
            html += `<td>${value}</td>`;
        });
        html += '</tr>';
    });

    html += '</tbody></table>';
    tableContainer.innerHTML = html;
}

// 加载Douyin数据
async function loadDouyinData() {
    try {
        const response = await fetch('/api/douyin');
        const result = await response.json();
        
        if (result.success) {
            // 更新指标
            document.getElementById('douyin-total-videos').textContent = formatNumber(result.metrics.total_videos);
            document.getElementById('douyin-avg-likes').textContent = formatNumber(result.metrics.avg_likes);
            document.getElementById('douyin-avg-comments').textContent = formatNumber(result.metrics.avg_comments);
            document.getElementById('douyin-creators').textContent = formatNumber(result.metrics.unique_creators);

            if (result.top_creators && result.top_creators.length > 0) {
                drawDouyinTopCreatorsChart(result.top_creators);
            } else {
                const chartCard = document.getElementById('douyin-top-creators-chart')?.parentElement;
                if (chartCard) {
                    chartCard.innerHTML = '<p style="text-align: center; color: #666; padding: 20px;">暂无创作者数据</p>';
                }
            }

            if (result.timeline && result.timeline.length > 0) {
                drawDouyinTimelineChart(result.timeline);
            } else {
                const timelineCard = document.getElementById('douyin-timeline-chart')?.parentElement;
                if (timelineCard) {
                    timelineCard.innerHTML = '<p style="text-align: center; color: #666; padding: 20px;">暂无时间线数据</p>';
                }
            }

            // 渲染表格
            renderDouyinTable(result.data);
        }
    } catch (error) {
        console.error('Error loading Douyin data:', error);
    }
}

// 渲染Douyin表格
function renderDouyinTable(data) {
    const tableContainer = document.getElementById('douyin-table');
    if (data.length === 0) {
        tableContainer.innerHTML = '<p>暂无数据</p>';
        return;
    }

    const columns = [
        {key: 'aweme_id', label: '视频ID'},
        {key: 'title', label: '标题'},
        {key: 'nickname', label: '创作者'},
        {key: 'liked_count', label: '点赞数'},
        {key: 'comment_count', label: '评论数'},
        {key: 'create_time', label: '创建时间'}
    ];
    let html = '<table><thead><tr>';
    columns.forEach(col => {
        html += `<th>${col.label}</th>`;
    });
    html += '</tr></thead><tbody>';

    data.slice(0, 100).forEach(item => {
        html += '<tr>';
        columns.forEach(col => {
            let value = item[col.key] || '-';
            if (col.key === 'create_time' && value !== '-') {
                value = new Date(value).toLocaleDateString('zh-CN');
            } else if (typeof value === 'number') {
                value = formatNumber(value);
            }
            html += `<td>${value}</td>`;
        });
        html += '</tr>';
    });

    html += '</tbody></table>';
    tableContainer.innerHTML = html;
}

// 绘制Douyin Top Creators图表
function drawDouyinTopCreatorsChart(data) {
    const ctx = document.getElementById('douyin-top-creators-chart');
    if (!ctx) return;
    if (charts.douyinTopCreators) {
        charts.douyinTopCreators.destroy();
    }

    charts.douyinTopCreators = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(item => item.name),
            datasets: [{
                label: '总点赞数',
                data: data.map(item => item.likes),
                backgroundColor: '#111827',
                borderColor: '#1f2937',
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    beginAtZero: true
                }
            }
        }
    });
}

// 绘制Douyin时间线图表
function drawDouyinTimelineChart(data) {
    const container = document.getElementById('douyin-timeline-chart');
    if (!container) return;

    const trace = {
        x: data.map(item => item.date),
        y: data.map(item => item.count),
        type: 'scatter',
        mode: 'lines+markers',
        name: '视频数量',
        line: { color: '#111827' }
    };

    const layout = {
        title: '每日视频上传量',
        xaxis: { title: '日期' },
        yaxis: { title: '视频数量' },
        height: 300
    };

    Plotly.newPlot(container, [trace], layout);
}

// 加载快手数据
async function loadKuaishouData() {
    try {
        const response = await fetch('/api/kuaishou');
        const result = await response.json();
        
        if (result.success) {
            // 检查是否有数据
            if (!result.data || result.data.length === 0) {
                // 显示无数据提示
                showKuaishouEmptyMessage();
                return;
            }
            
            // 更新指标
            document.getElementById('kuaishou-total-videos').textContent = formatNumber(result.metrics.total_videos);
            document.getElementById('kuaishou-avg-likes').textContent = formatNumber(result.metrics.avg_likes);
            document.getElementById('kuaishou-avg-views').textContent = formatNumber(result.metrics.avg_views);
            document.getElementById('kuaishou-creators').textContent = formatNumber(result.metrics.unique_creators);

            // 绘制图表
            if (result.top_creators && result.top_creators.length > 0) {
                drawKuaishouTopCreatorsChart(result.top_creators);
            } else {
                document.getElementById('kuaishou-top-creators-chart').parentElement.innerHTML = 
                    '<p style="text-align: center; color: #666; padding: 20px;">暂无创作者数据</p>';
            }
            
            if (result.timeline && result.timeline.length > 0) {
                drawKuaishouTimelineChart(result.timeline);
            } else {
                document.getElementById('kuaishou-timeline-chart').parentElement.innerHTML = 
                    '<p style="text-align: center; color: #666; padding: 20px;">暂无时间线数据</p>';
            }
            
            renderKuaishouTable(result.data);
        } else {
            showKuaishouEmptyMessage(result.error || '加载数据失败');
        }
    } catch (error) {
        console.error('Error loading Kuaishou data:', error);
        showKuaishouEmptyMessage('网络错误，请检查连接');
    }
}

// 显示快手无数据提示
function showKuaishouEmptyMessage(message) {
    const messageText = message || '暂无快手数据';
    const container = document.querySelector('#page-kuaishou .charts-container');
    if (container) {
        container.innerHTML = `
            <div style="text-align: center; padding: 40px; background: #f8f9fa; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #666; margin-bottom: 20px;">📭 ${messageText}</h3>
                <div style="color: #888; line-height: 1.8;">
                    <p>💡 请按照以下步骤同步数据：</p>
                    <ol style="text-align: left; display: inline-block; margin-top: 10px;">
                        <li>确保已爬取快手数据（JSON文件在 <code>data/kuaishou/json/</code> 目录）</li>
                        <li>运行同步脚本：<code>python sync_kuaishou_data.py --db-type db</code></li>
                        <li>验证数据：<code>python check_mysql_data.py</code></li>
                        <li>刷新页面查看数据</li>
                    </ol>
                    <p style="margin-top: 20px;">
                        📚 详细说明请参考：<code>KUAISHOU_SYNC_README.md</code>
                    </p>
                </div>
            </div>
        `;
    }
    
    // 清空表格
    const tableContainer = document.getElementById('kuaishou-table');
    if (tableContainer) {
        tableContainer.innerHTML = '<p style="text-align: center; color: #666; padding: 20px;">暂无数据</p>';
    }
}

// 绘制快手 Top Creators图表
function drawKuaishouTopCreatorsChart(data) {
    const ctx = document.getElementById('kuaishou-top-creators-chart');
    if (charts.kuaishouTopCreators) {
        charts.kuaishouTopCreators.destroy();
    }

    charts.kuaishouTopCreators = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(item => item.name),
            datasets: [{
                label: '总点赞数',
                data: data.map(item => item.likes),
                backgroundColor: '#ff6100',
                borderColor: '#1e40af',
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    beginAtZero: true
                }
            }
        }
    });
}

// 绘制快手时间线图表
function drawKuaishouTimelineChart(data) {
    const container = document.getElementById('kuaishou-timeline-chart');
    
    const trace = {
        x: data.map(item => item.date),
        y: data.map(item => item.count),
        type: 'scatter',
        mode: 'lines+markers',
        name: '视频数量',
        line: { color: '#ff6100' }
    };

    const layout = {
        title: '每日视频上传量',
        xaxis: { title: '日期' },
        yaxis: { title: '视频数量' },
        height: 300
    };

    Plotly.newPlot(container, [trace], layout);
}

// 渲染快手表格
function renderKuaishouTable(data) {
    const tableContainer = document.getElementById('kuaishou-table');
    if (data.length === 0) {
        tableContainer.innerHTML = '<p>暂无数据</p>';
        return;
    }

    const columns = [
        {key: 'video_id', label: '视频ID'},
        {key: 'title', label: '标题'},
        {key: 'nickname', label: '创作者'},
        {key: 'liked_count', label: '点赞数'},
        {key: 'viewd_count', label: '观看数'},
        {key: 'create_time', label: '创建时间'}
    ];
    let html = '<table><thead><tr>';
    columns.forEach(col => {
        html += `<th>${col.label}</th>`;
    });
    html += '</tr></thead><tbody>';

    data.slice(0, 100).forEach(item => {
        html += '<tr>';
        columns.forEach(col => {
            let value = item[col.key] || '-';
            if (col.key === 'title' && value && value.length > 50) {
                value = value.substring(0, 50) + '...';
            } else if (col.key === 'create_time' && value !== '-') {
                value = new Date(value).toLocaleDateString('zh-CN');
            } else if (typeof value === 'number') {
                value = formatNumber(value);
            }
            html += `<td>${value}</td>`;
        });
        html += '</tr>';
    });

    html += '</tbody></table>';
    tableContainer.innerHTML = html;
}

// 加载微博数据
async function loadWeiboData() {
    try {
        const response = await fetch('/api/weibo');
        const result = await response.json();
        
        if (result.success) {
            // 更新指标
            document.getElementById('weibo-total-notes').textContent = formatNumber(result.metrics.total_notes);
            document.getElementById('weibo-avg-likes').textContent = formatNumber(result.metrics.avg_likes);
            document.getElementById('weibo-avg-comments').textContent = formatNumber(result.metrics.avg_comments);
            document.getElementById('weibo-creators').textContent = formatNumber(result.metrics.unique_creators);

            // 绘制图表
            drawWeiboTopCreatorsChart(result.top_creators);
            drawWeiboTimelineChart(result.timeline);
            renderWeiboTable(result.data);
        }
    } catch (error) {
        console.error('Error loading Weibo data:', error);
    }
}

// 绘制微博 Top Creators图表
function drawWeiboTopCreatorsChart(data) {
    const ctx = document.getElementById('weibo-top-creators-chart');
    if (charts.weiboTopCreators) {
        charts.weiboTopCreators.destroy();
    }

    charts.weiboTopCreators = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(item => item.name),
            datasets: [{
                label: '总点赞数',
                data: data.map(item => item.likes),
                backgroundColor: '#e6162d',
                borderColor: '#1e40af',
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    beginAtZero: true
                }
            }
        }
    });
}

// 绘制微博时间线图表
function drawWeiboTimelineChart(data) {
    const container = document.getElementById('weibo-timeline-chart');
    
    const trace = {
        x: data.map(item => item.date),
        y: data.map(item => item.count),
        type: 'scatter',
        mode: 'lines+markers',
        name: '微博数量',
        line: { color: '#e6162d' }
    };

    const layout = {
        title: '每日微博发布量',
        xaxis: { title: '日期' },
        yaxis: { title: '微博数量' },
        height: 300
    };

    Plotly.newPlot(container, [trace], layout);
}

// 渲染微博表格
function renderWeiboTable(data) {
    const tableContainer = document.getElementById('weibo-table');
    if (data.length === 0) {
        tableContainer.innerHTML = '<p>暂无数据</p>';
        return;
    }

    const columns = [
        {key: 'note_id', label: '微博ID'},
        {key: 'content', label: '内容'},
        {key: 'nickname', label: '创作者'},
        {key: 'liked_count', label: '点赞数'},
        {key: 'comments_count', label: '评论数'},
        {key: 'shared_count', label: '转发数'},
        {key: 'create_time', label: '创建时间'}
    ];
    let html = '<table><thead><tr>';
    columns.forEach(col => {
        html += `<th>${col.label}</th>`;
    });
    html += '</tr></thead><tbody>';

    data.slice(0, 100).forEach(item => {
        html += '<tr>';
        columns.forEach(col => {
            let value = item[col.key] || '-';
            if (col.key === 'content' && value && value.length > 50) {
                value = value.substring(0, 50) + '...';
            } else if (col.key === 'create_time' && value !== '-') {
                value = new Date(value).toLocaleDateString('zh-CN');
            } else if (typeof value === 'number') {
                value = formatNumber(value);
            }
            html += `<td>${value}</td>`;
        });
        html += '</tr>';
    });

    html += '</tbody></table>';
    tableContainer.innerHTML = html;
}

// 加载知乎数据
async function loadZhihuData() {
    try {
        const response = await fetch('/api/zhihu');
        const result = await response.json();

        if (result.success) {
            const metrics = result.metrics || {};
            document.getElementById('zhihu-total-contents').textContent = formatNumber(metrics.total_contents || 0);
            document.getElementById('zhihu-avg-votes').textContent = formatNumber(metrics.avg_votes || 0);
            document.getElementById('zhihu-avg-comments').textContent = formatNumber(metrics.avg_comments || 0);
            document.getElementById('zhihu-creators').textContent = formatNumber(metrics.unique_creators || 0);

            if (result.top_creators && result.top_creators.length > 0) {
                drawZhihuTopCreatorsChart(result.top_creators);
            } else {
                const chartCard = document.getElementById('zhihu-top-creators-chart')?.parentElement;
                if (chartCard) {
                    chartCard.innerHTML = '<p style="text-align: center; color: #666; padding: 20px;">暂无创作者数据</p>';
                }
            }

            if (result.timeline && result.timeline.length > 0) {
                drawZhihuTimelineChart(result.timeline);
            } else {
                const timelineCard = document.getElementById('zhihu-timeline-chart')?.parentElement;
                if (timelineCard) {
                    timelineCard.innerHTML = '<p style="text-align: center; color: #666; padding: 20px;">暂无时间线数据</p>';
                }
            }

            renderZhihuTable(result.data);
        }
    } catch (error) {
        console.error('Error loading Zhihu data:', error);
    }
}

// 绘制知乎 Top Creators 图表
function drawZhihuTopCreatorsChart(data) {
    const ctx = document.getElementById('zhihu-top-creators-chart');
    if (!ctx) return;
    if (charts.zhihuTopCreators) {
        charts.zhihuTopCreators.destroy();
    }

    charts.zhihuTopCreators = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(item => item.name),
            datasets: [{
                label: '总赞同数',
                data: data.map(item => item.votes),
                backgroundColor: '#0084ff',
                borderColor: '#1e40af',
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    beginAtZero: true
                }
            }
        }
    });
}

// 绘制知乎时间线图
function drawZhihuTimelineChart(data) {
    const container = document.getElementById('zhihu-timeline-chart');
    if (!container) return;

    const trace = {
        x: data.map(item => item.date),
        y: data.map(item => item.count),
        type: 'scatter',
        mode: 'lines+markers',
        name: '内容数量',
        line: { color: '#0084ff' }
    };

    const layout = {
        title: '每日内容发布量',
        xaxis: { title: '日期' },
        yaxis: { title: '内容数量' },
        height: 300
    };

    Plotly.newPlot(container, [trace], layout);
}

// 渲染知乎表格
function renderZhihuTable(data) {
    const tableContainer = document.getElementById('zhihu-table');
    if (!tableContainer) return;
    if (!data || data.length === 0) {
        tableContainer.innerHTML = '<p>暂无数据</p>';
        return;
    }

    const columns = [
        {key: 'content_id', label: '内容ID'},
        {key: 'title', label: '标题'},
        {key: 'user_nickname', label: '创作者'},
        {key: 'content_type', label: '类型'},
        {key: 'voteup_count', label: '赞同数'},
        {key: 'comment_count', label: '评论数'},
        {key: 'created_time', label: '发布时间'}
    ];

    let html = '<table><thead><tr>';
    columns.forEach(col => {
        html += `<th>${col.label}</th>`;
    });
    html += '</tr></thead><tbody>';

    data.slice(0, 100).forEach(item => {
        html += '<tr>';
        columns.forEach(col => {
            let value = item[col.key] || '-';
            if (col.key === 'title' && value && value.length > 50) {
                value = value.substring(0, 50) + '...';
            } else if (col.key === 'created_time' && value !== '-') {
                value = new Date(value).toLocaleDateString('zh-CN');
            } else if (typeof value === 'number') {
                value = formatNumber(value);
            }
            html += `<td>${value}</td>`;
        });
        html += '</tr>';
    });

    html += '</tbody></table>';
    tableContainer.innerHTML = html;
}

// 加载贴吧数据
async function loadTiebaData() {
    try {
        const response = await fetch('/api/tieba');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();

        if (result.success) {
            const metrics = result.metrics || {};
            document.getElementById('tieba-total-notes').textContent = formatNumber(metrics.total_notes || 0);
            document.getElementById('tieba-avg-replies').textContent = formatNumber(metrics.avg_replies || 0);
            document.getElementById('tieba-creators').textContent = formatNumber(metrics.unique_creators || 0);
            document.getElementById('tieba-tiebas').textContent = formatNumber(metrics.unique_tiebas || 0);

            if (result.top_creators && result.top_creators.length > 0) {
                drawTiebaTopCreatorsChart(result.top_creators);
            } else {
                const chartCard = document.getElementById('tieba-top-creators-chart')?.parentElement;
                if (chartCard) {
                    chartCard.innerHTML = '<p style="text-align: center; color: #666; padding: 20px;">暂无创作者数据</p>';
                }
            }

            if (result.top_tiebas && result.top_tiebas.length > 0) {
                drawTiebaTopTiebasChart(result.top_tiebas);
            } else {
                const chartCard = document.getElementById('tieba-top-tiebas-chart')?.parentElement;
                if (chartCard) {
                    chartCard.innerHTML = '<p style="text-align: center; color: #666; padding: 20px;">暂无贴吧数据</p>';
                }
            }

            if (result.timeline && result.timeline.length > 0) {
                drawTiebaTimelineChart(result.timeline);
            } else {
                const timelineCard = document.getElementById('tieba-timeline-chart')?.parentElement;
                if (timelineCard) {
                    timelineCard.innerHTML = '<p style="text-align: center; color: #666; padding: 20px;">暂无时间线数据</p>';
                }
            }

            renderTiebaTable(result.data || []);
            
            // 如果有消息（比如提示没有数据），显示它
            if (result.message) {
                console.log('Tieba API message:', result.message);
            }
        } else {
            // API 返回了错误
            console.error('Tieba API error:', result.error || result.message);
            // 即使失败，也尝试更新指标为0（如果 metrics 存在）
            if (result.metrics) {
                const metrics = result.metrics;
                document.getElementById('tieba-total-notes').textContent = formatNumber(metrics.total_notes || 0);
                document.getElementById('tieba-avg-replies').textContent = formatNumber(metrics.avg_replies || 0);
                document.getElementById('tieba-creators').textContent = formatNumber(metrics.unique_creators || 0);
                document.getElementById('tieba-tiebas').textContent = formatNumber(metrics.unique_tiebas || 0);
            } else {
                // 如果没有 metrics，设置为 0
                document.getElementById('tieba-total-notes').textContent = '0';
                document.getElementById('tieba-avg-replies').textContent = '0';
                document.getElementById('tieba-creators').textContent = '0';
                document.getElementById('tieba-tiebas').textContent = '0';
            }
            
            // 显示错误信息
            const errorMsg = result.error || result.message || '加载贴吧数据失败';
            const chartCard = document.getElementById('tieba-top-creators-chart')?.parentElement;
            if (chartCard) {
                chartCard.innerHTML = `<p style="text-align: center; color: #f44336; padding: 20px;">${errorMsg}</p>`;
            }
        }
    } catch (error) {
        console.error('Error loading Tieba data:', error);
        // 发生网络错误或其他异常时，显示错误信息
        document.getElementById('tieba-total-notes').textContent = '0';
        document.getElementById('tieba-avg-replies').textContent = '0';
        document.getElementById('tieba-creators').textContent = '0';
        document.getElementById('tieba-tiebas').textContent = '0';
        
        const chartCard = document.getElementById('tieba-top-creators-chart')?.parentElement;
        if (chartCard) {
            chartCard.innerHTML = `<p style="text-align: center; color: #f44336; padding: 20px;">加载数据失败: ${error.message}</p>`;
        }
    }
}

// 绘制贴吧 Top Creators 图表
function drawTiebaTopCreatorsChart(data) {
    const ctx = document.getElementById('tieba-top-creators-chart');
    if (!ctx) return;
    if (charts.tiebaTopCreators) {
        charts.tiebaTopCreators.destroy();
    }

    charts.tiebaTopCreators = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(item => item.name),
            datasets: [{
                label: '总回复数',
                data: data.map(item => item.replies),
                backgroundColor: '#3b82f6',
                borderColor: '#1e40af',
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    beginAtZero: true
                }
            }
        }
    });
}

// 绘制贴吧 Top Tiebas 图表
function drawTiebaTopTiebasChart(data) {
    const ctx = document.getElementById('tieba-top-tiebas-chart');
    if (!ctx) return;
    if (charts.tiebaTopTiebas) {
        charts.tiebaTopTiebas.destroy();
    }

    charts.tiebaTopTiebas = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(item => item.name),
            datasets: [{
                label: '帖子数量',
                data: data.map(item => item.count),
                backgroundColor: '#10b981',
                borderColor: '#059669',
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    beginAtZero: true
                }
            }
        }
    });
}

// 绘制贴吧时间线图
function drawTiebaTimelineChart(data) {
    const container = document.getElementById('tieba-timeline-chart');
    if (!container) return;

    const trace = {
        x: data.map(item => item.date),
        y: data.map(item => item.count),
        type: 'scatter',
        mode: 'lines+markers',
        name: '帖子数量',
        line: { color: '#3b82f6' }
    };

    const layout = {
        title: '每日帖子发布量',
        xaxis: { title: '日期' },
        yaxis: { title: '帖子数量' },
        height: 300
    };

    Plotly.newPlot(container, [trace], layout);
}

// 渲染贴吧表格
function renderTiebaTable(data) {
    const tableContainer = document.getElementById('tieba-table');
    if (!tableContainer) return;
    if (!data || data.length === 0) {
        tableContainer.innerHTML = '<p>暂无数据</p>';
        return;
    }

    const columns = [
        {key: 'note_id', label: '帖子ID'},
        {key: 'title', label: '标题'},
        {key: 'user_nickname', label: '发帖人'},
        {key: 'tieba_name', label: '贴吧'},
        {key: 'total_replay_num', label: '回复数'},
        {key: 'create_time', label: '发布时间'}
    ];

    let html = '<table><thead><tr>';
    columns.forEach(col => {
        html += `<th>${col.label}</th>`;
    });
    html += '</tr></thead><tbody>';

    data.slice(0, 100).forEach(item => {
        html += '<tr>';
        columns.forEach(col => {
            let value = item[col.key];
            
            // 处理时间字段
            if (col.key === 'create_time') {
                if (value && value !== null && value !== undefined && value !== '-') {
                    try {
                        // 尝试解析时间字符串
                        const date = new Date(value);
                        if (!isNaN(date.getTime())) {
                            value = date.toLocaleDateString('zh-CN', {
                                year: 'numeric',
                                month: '2-digit',
                                day: '2-digit',
                                hour: '2-digit',
                                minute: '2-digit'
                            });
                        } else {
                            // 如果无法解析，直接显示原始值
                            value = String(value);
                        }
                    } catch (e) {
                        // 解析失败，显示原始值
                        value = String(value);
                    }
                } else {
                    // 如果没有 create_time，尝试使用 publish_time
                    if (item['publish_time'] && item['publish_time'] !== null && item['publish_time'] !== undefined) {
                        value = String(item['publish_time']);
                    } else {
                        value = '-';
                    }
                }
            } else if (col.key === 'title' && value && value.length > 50) {
                value = value.substring(0, 50) + '...';
            } else if (typeof value === 'number') {
                value = formatNumber(value);
            } else if (value === null || value === undefined) {
                value = '-';
            }
            
            html += `<td>${value}</td>`;
        });
        html += '</tr>';
    });

    html += '</tbody></table>';
    tableContainer.innerHTML = html;
}

// 加载跨平台数据
async function loadCrossPlatformData() {
    try {
        const response = await fetch('/api/cross-platform');
        const result = await response.json();
        
        if (result.success) {
            console.log('Cross-platform data received:', result.data);
            // 验证数据
            if (!result.data || result.data.length === 0) {
                console.warn('No cross-platform data available');
                return;
            }
            drawCrossPlatformCharts(result.data);
            renderCrossPlatformTable(result.data);
        } else {
            console.error('Cross-platform API error:', result.error);
        }
    } catch (error) {
        console.error('Error loading cross-platform data:', error);
    }
}

// 绘制跨平台图表
function drawCrossPlatformCharts(data) {
    const platforms = data.map(item => item.platform);
    
    // 平台颜色映射
    const platformColors = {
        'Bilibili': '#fb7299',
        'Douyin': '#000000',
        'Kuaishou': '#ff6100',
        'Weibo': '#e6162d',
        'Zhihu': '#0084ff'
    };
    
    const colors = platforms.map(p => platformColors[p] || '#6b7280');
    
    // Content Volume Chart
    const volumeCtx = document.getElementById('cross-platform-volume-chart');
    if (charts.crossPlatformVolume) {
        charts.crossPlatformVolume.destroy();
    }
    charts.crossPlatformVolume = new Chart(volumeCtx, {
        type: 'bar',
        data: {
            labels: platforms,
            datasets: [{
                label: '内容总数',
                data: data.map(item => item.total_content),
                backgroundColor: colors,
                borderColor: colors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    // Engagement Chart
    const engagementCtx = document.getElementById('cross-platform-engagement-chart');
    if (charts.crossPlatformEngagement) {
        charts.crossPlatformEngagement.destroy();
    }
    
    // 使用avg_engagement如果存在，否则使用avg_likes
    // 注意：需要明确检查 undefined/null，因为 0 是有效值
    const engagementData = data.map(item => {
        let value = 0;
        if (item.avg_engagement !== undefined && item.avg_engagement !== null) {
            value = item.avg_engagement;
        } else if (item.avg_likes !== undefined && item.avg_likes !== null) {
            value = item.avg_likes;
        }
        // 确保值是数字类型
        value = Number(value) || 0;
        // 调试日志
        console.log(`Platform: ${item.platform}, avg_engagement: ${item.avg_engagement}, avg_likes: ${item.avg_likes}, final value: ${value}`);
        return value;
    });
    
    // 调试：打印所有数据
    console.log('Engagement data:', engagementData);
    console.log('Platforms:', platforms);
    
    // 检查数据中是否有微博
    const weiboIndex = platforms.indexOf('Weibo');
    if (weiboIndex !== -1) {
        console.log(`Weibo found at index ${weiboIndex}, value: ${engagementData[weiboIndex]}`);
    } else {
        console.warn('Weibo not found in platforms array:', platforms);
    }
    
    // 计算最大值，用于确保小值也能显示
    const maxValue = Math.max(...engagementData.filter(v => !isNaN(v) && isFinite(v)));
    const minVisibleValue = maxValue * 0.01; // 至少显示最大值的1%，确保小值可见
    
    // 如果值太小（小于最大值的1%），至少显示最小可见值
    const adjustedData = engagementData.map((value, index) => {
        if (value > 0 && value < minVisibleValue && maxValue > 0) {
            console.log(`Adjusting ${platforms[index]} value from ${value} to ${minVisibleValue} for visibility`);
            return minVisibleValue;
        }
        return value;
    });
    
    charts.crossPlatformEngagement = new Chart(engagementCtx, {
        type: 'bar',
        data: {
            labels: platforms,
            datasets: [{
                label: '平均互动量',
                data: adjustedData,
                backgroundColor: colors,
                borderColor: colors,
                borderWidth: 1,
                // 设置柱状图宽度
                barThickness: 'flex',
                maxBarThickness: 50
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const index = context.dataIndex;
                            const originalValue = engagementData[index];
                            const displayedValue = context.parsed.y;
                            // 如果显示的值被调整过，在提示中说明
                            if (originalValue > 0 && originalValue < displayedValue) {
                                return `平均互动量: ${formatNumber(originalValue)} (已放大显示)`;
                            }
                            return '平均互动量: ' + formatNumber(displayedValue);
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return formatNumber(value);
                        },
                        // 确保显示所有刻度，包括小值
                        stepSize: null
                    },
                    // 如果数据差异很大，可以考虑使用对数刻度（可选）
                    // type: 'logarithmic'  // 取消注释以使用对数刻度
                },
                x: {
                    ticks: {
                        // 确保所有平台标签都显示
                        autoSkip: false
                    }
                }
            },
            // 确保即使值很小也能看到柱状图
            animation: {
                duration: 1000
            }
        }
    });
}

// 渲染跨平台表格
function renderCrossPlatformTable(data) {
    const tableContainer = document.getElementById('cross-platform-table');
    let html = '<table><thead><tr><th>平台</th><th>内容总数</th><th>平均点赞数</th><th>平均评论数</th><th>平均转发数</th><th>平均互动量</th><th>创作者数量</th></tr></thead><tbody>';
    
    data.forEach(item => {
        const avgComments = item.avg_comments ? formatNumber(item.avg_comments) : '-';
        const avgShares = item.avg_shares ? formatNumber(item.avg_shares) : '-';
        const avgEngagement = item.avg_engagement ? formatNumber(item.avg_engagement) : formatNumber(item.avg_likes || 0);
        
        html += `<tr>
            <td>${item.platform}</td>
            <td>${formatNumber(item.total_content)}</td>
            <td>${formatNumber(item.avg_likes)}</td>
            <td>${avgComments}</td>
            <td>${avgShares}</td>
            <td>${avgEngagement}</td>
            <td>${formatNumber(item.unique_creators)}</td>
        </tr>`;
    });
    
    html += '</tbody></table>';
    tableContainer.innerHTML = html;
}

// 加载语义数据
async function loadSemanticData() {
    const loadingEl = document.getElementById('semantic-loading');
    const emptyEl = document.getElementById('semantic-empty');
    const contentEl = document.getElementById('semantic-content');
    
    loadingEl.style.display = 'block';
    emptyEl.style.display = 'none';
    contentEl.style.display = 'none';

    try {
        const startDate = document.getElementById('start-date').value;
        const endDate = document.getElementById('end-date').value;
        const platforms = Array.from(document.querySelectorAll('.platform-checkboxes input:checked'))
            .map(cb => cb.value);

        const params = new URLSearchParams();
        // 只有在日期不为空时才添加日期参数
        if (startDate) {
            params.append('start_date', startDate);
        }
        if (endDate) {
            params.append('end_date', endDate);
        }
        // 添加平台参数
        platforms.forEach(p => {
            params.append('platforms', p);
        });

        const response = await fetch(`/api/semantic?${params}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        console.log('[DEBUG] Semantic API response:', {
            success: result.success,
            dataLength: result.data ? result.data.length : 0,
            hasSentiment: !!result.sentiment_distribution,
            hasTopics: !!result.top_topics,
            message: result.message
        });
        
        loadingEl.style.display = 'none';

        if (!result.success) {
            emptyEl.style.display = 'block';
            emptyEl.textContent = result.error || result.message || '加载语义数据时发生错误。';
            console.error('[ERROR] Semantic API error:', result.error);
            return;
        }

        if (!result.data || result.data.length === 0) {
            emptyEl.style.display = 'block';
            // 更新错误消息，显示更详细的信息
            const message = result.message || '暂无语义增强数据，请先运行语义处理流水线。';
            emptyEl.textContent = message;
            
            // 如果有数据时间范围，显示提示
            if (result.data_range) {
                const tipEl = document.createElement('p');
                tipEl.className = 'tip';
                tipEl.style.marginTop = '10px';
                tipEl.style.color = '#666';
                tipEl.style.fontSize = '14px';
                tipEl.textContent = `💡 提示：请将日期范围调整为 ${result.data_range.min} 至 ${result.data_range.max}`;
                emptyEl.appendChild(tipEl);
            }
            return;
        }

        contentEl.style.display = 'block';
        
        // 绘制情绪分布图表
        if (result.sentiment_distribution && Object.keys(result.sentiment_distribution).length > 0) {
            drawSemanticSentimentChart(result.sentiment_distribution);
        } else {
            console.warn('[WARN] No sentiment distribution data');
        }
        
        // 绘制热门主题图表
        if (result.top_topics && result.top_topics.length > 0) {
            drawSemanticTopicsChart(result.top_topics);
        } else {
            console.warn('[WARN] No topics data');
        }
        
        // 渲染表格
        renderSemanticTable(result.data);
    } catch (error) {
        console.error('Error loading semantic data:', error);
        loadingEl.style.display = 'none';
        emptyEl.style.display = 'block';
    }
}

// 绘制语义情绪图表
function drawSemanticSentimentChart(data) {
    const ctx = document.getElementById('semantic-sentiment-chart');
    if (charts.semanticSentiment) {
        charts.semanticSentiment.destroy();
    }

    charts.semanticSentiment = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: Object.keys(data),
            datasets: [{
                data: Object.values(data),
                backgroundColor: ['#10b981', '#ef4444', '#6b7280']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true
        }
    });
}

// 绘制语义主题图表
function drawSemanticTopicsChart(data) {
    const ctx = document.getElementById('semantic-topics-chart');
    if (charts.semanticTopics) {
        charts.semanticTopics.destroy();
    }

    charts.semanticTopics = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(item => item.topic),
            datasets: [{
                label: 'Count',
                data: data.map(item => item.count),
                backgroundColor: '#1e40af'
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

// 渲染语义表格
function renderSemanticTable(data) {
    const tableContainer = document.getElementById('semantic-table');
    if (data.length === 0) {
        tableContainer.innerHTML = '<p>暂无数据</p>';
        return;
    }

    const columns = [
        {key: 'platform', label: '平台'},
        {key: 'sentiment_label', label: '情绪标签'},
        {key: 'summary', label: '摘要'},
        {key: 'content', label: '内容'}
    ];
    let html = '<table><thead><tr>';
    columns.forEach(col => {
        html += `<th>${col.label}</th>`;
    });
    html += '</tr></thead><tbody>';

    data.slice(0, 100).forEach(item => {
        html += '<tr>';
        columns.forEach(col => {
            let value = item[col.key] || '-';
            if (col.key === 'content' && value && value.length > 100) {
                value = value.substring(0, 100) + '...';
            }
            html += `<td>${value}</td>`;
        });
        html += '</tr>';
    });

    html += '</tbody></table>';
    tableContainer.innerHTML = html;
}

// 处理过滤器变化
function handleFilterChange() {
    const activePage = document.querySelector('.page.active').id.replace('page-', '');
    if (activePage === 'semantic') {
        loadSemanticData();
    }
}

// 自动刷新
function startAutoRefresh() {
    stopAutoRefresh();
    autoRefreshInterval = setInterval(() => {
        const activePage = document.querySelector('.page.active').id.replace('page-', '');
        loadPageData(activePage);
    }, refreshIntervalMinutes * 60 * 1000);
}

function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
}

// 工具函数
function formatNumber(num) {
    if (num === null || num === undefined) return '-';
    return new Intl.NumberFormat('en-US').format(Math.round(num));
}

function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

