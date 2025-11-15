# -*- coding: utf-8 -*-
"""
跨平台数据同步到Neo4j的启动脚本
使用方法: python sync_to_neo4j.py
"""

import sys
from pathlib import Path

# 添加项目根目录到sys.path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from services.neo4j_sync import sync_all_to_neo4j
from tools import utils

if __name__ == "__main__":
    utils.logger.info("开始同步所有平台数据到Neo4j...")
    try:
        sync_all_to_neo4j(batch_size=100)
        utils.logger.info("数据同步完成！")
    except Exception as e:
        utils.logger.error(f"同步失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

