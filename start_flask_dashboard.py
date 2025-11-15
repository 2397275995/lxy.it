# -*- coding: utf-8 -*-
"""
启动Flask Dashboard服务器
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到sys.path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# 导入flask_dashboard模块
sys.path.insert(0, str(project_root))
from flask_dashboard.app import app

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='启动Flask Dashboard服务器')
    parser.add_argument('--host', default='127.0.0.1', help='服务器地址 (默认: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=5000, help='服务器端口 (默认: 5000)')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    
    args = parser.parse_args()
    
    print(f"""
    ╔══════════════════════════════════════════════════════╗
    ║   爬取数据分析 Dashboard                              ║
    ║                                                      ║
    ║   服务器地址: http://{args.host}:{args.port}        ║
    ║   调试模式: {'开启' if args.debug else '关闭'}      ║
    ╚══════════════════════════════════════════════════════╝
    """)
    
    app.run(host=args.host, port=args.port, debug=args.debug)

