# -*- coding: utf-8 -*-
"""
检查快手数据是否已同步到数据库
"""

import sys
from pathlib import Path

# 添加项目根目录到sys.path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from database.db import get_db_engine
import pandas as pd
from tools import utils


def check_kuaishou_data():
    """检查快手数据状态"""
    print("=" * 60)
    print("快手数据检查")
    print("=" * 60)
    
    # 1. 检查数据库连接
    print("\n1. 检查数据库连接...")
    try:
        engine = get_db_engine()
        if not engine:
            print("   ❌ 无法连接数据库，请检查数据库配置")
            print("   💡 请确认 config/base_config.py 中 SAVE_DATA_OPTION = 'db' 或 'sqlite'")
            return
        print("   ✅ 数据库连接成功")
    except Exception as e:
        print(f"   ❌ 数据库连接失败: {e}")
        return
    
    # 2. 检查表是否存在
    print("\n2. 检查数据库表...")
    try:
        # 检查视频表
        video_check = pd.read_sql("SHOW TABLES LIKE 'kuaishou_video'", engine)
        if video_check.empty:
            print("   ❌ kuaishou_video 表不存在")
            print("   💡 请先初始化数据库：python main.py --init-db db")
            return
        print("   ✅ kuaishou_video 表存在")
        
        # 检查评论表
        comment_check = pd.read_sql("SHOW TABLES LIKE 'kuaishou_video_comment'", engine)
        if comment_check.empty:
            print("   ⚠️  kuaishou_video_comment 表不存在（可选）")
        else:
            print("   ✅ kuaishou_video_comment 表存在")
    except Exception as e:
        # SQLite 使用不同的查询
        try:
            video_count = pd.read_sql("SELECT COUNT(*) as count FROM kuaishou_video", engine)
            print("   ✅ kuaishou_video 表存在")
            try:
                comment_count = pd.read_sql("SELECT COUNT(*) as count FROM kuaishou_video_comment", engine)
                print("   ✅ kuaishou_video_comment 表存在")
            except:
                print("   ⚠️  kuaishou_video_comment 表不存在（可选）")
        except Exception as e2:
            print(f"   ❌ 检查表失败: {e2}")
            return
    
    # 3. 检查数据数量
    print("\n3. 检查数据数量...")
    try:
        video_query = "SELECT COUNT(*) as count FROM kuaishou_video"
        video_df = pd.read_sql(video_query, engine)
        video_count = video_df.iloc[0]['count'] if not video_df.empty else 0
        
        print(f"   - kuaishou_video 表记录数: {video_count}")
        
        if video_count == 0:
            print("\n   ⚠️  表中没有视频数据！")
            print("   💡 请运行以下命令同步数据：")
            print("      python sync_kuaishou_data.py --db-type db")
            print("\n   📝 数据文件应位于：data/kuaishou/json/")
            return
        
        # 检查评论数据
        try:
            comment_query = "SELECT COUNT(*) as count FROM kuaishou_video_comment"
            comment_df = pd.read_sql(comment_query, engine)
            comment_count = comment_df.iloc[0]['count'] if not comment_df.empty else 0
            print(f"   - kuaishou_video_comment 表记录数: {comment_count}")
        except:
            comment_count = 0
            print("   - kuaishou_video_comment 表记录数: 0（表不存在或无数据）")
        
    except Exception as e:
        print(f"   ❌ 查询数据失败: {e}")
        return
    
    # 4. 检查数据示例
    print("\n4. 数据示例...")
    try:
        sample_query = """
        SELECT video_id, title, nickname, liked_count, viewd_count, create_time
        FROM kuaishou_video
        ORDER BY create_time DESC
        LIMIT 5
        """
        sample_df = pd.read_sql(sample_query, engine)
        
        if not sample_df.empty:
            print("   前5条视频数据：")
            for idx, row in sample_df.iterrows():
                title = str(row.get('title', ''))[:30] + '...' if len(str(row.get('title', ''))) > 30 else str(row.get('title', ''))
                print(f"   {idx + 1}. {title} (ID: {row.get('video_id')}, 点赞: {row.get('liked_count')}, 观看: {row.get('viewd_count')})")
        else:
            print("   ⚠️  无法获取数据示例")
    except Exception as e:
        print(f"   ⚠️  获取数据示例失败: {e}")
    
    # 5. 总结
    print("\n" + "=" * 60)
    if video_count > 0:
        print("✅ 快手数据检查完成！")
        print(f"   - 视频数据: {video_count} 条")
        print(f"   - 评论数据: {comment_count} 条")
        print("\n💡 现在可以在Dashboard中查看快手数据了！")
        print("   启动Dashboard: python start_dashboard.py 或 python start_flask_dashboard.py")
    else:
        print("⚠️  数据库中没有快手数据")
        print("\n📝 下一步操作：")
        print("   1. 确认有JSON数据文件在 data/kuaishou/json/ 目录")
        print("   2. 运行同步脚本: python sync_kuaishou_data.py --db-type db")
        print("   3. 再次运行此脚本验证: python check_kuaishou_data.py")
    print("=" * 60)


if __name__ == "__main__":
    try:
        check_kuaishou_data()
    except Exception as e:
        print(f"\n❌ 检查过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

