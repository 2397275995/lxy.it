"""
快速检查语义数据状态
"""
import sys
from pathlib import Path

# 添加项目根目录到sys.path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from database.db import get_db_engine
from datetime import datetime

def check_semantic_status():
    """检查语义数据状态"""
    
    engine = get_db_engine()
    if not engine:
        print("[错误] 无法连接数据库，请检查数据库配置")
        return
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("=" * 70)
        print("检查语义数据状态")
        print("=" * 70)
        
        # 1. 检查表是否存在
        print("\n1. 检查表结构...")
        check_table = session.execute(text("""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = 'comment_semantic'
        """))
        table_exists = check_table.fetchone()[0] > 0
        
        if not table_exists:
            print("   [错误] comment_semantic 表不存在！")
            print("   [提示] 请先运行语义处理流水线创建表")
            return
        
        print("   [成功] comment_semantic 表存在")
        
        # 2. 检查数据总数
        print("\n2. 检查数据量...")
        result = session.execute(text("SELECT COUNT(*) as count FROM comment_semantic"))
        total_count = result.fetchone()[0]
        print(f"   - comment_semantic 表总记录数: {total_count}")
        
        if total_count == 0:
            print("\n   [警告] 表中没有数据！")
            print("   [解决方案] 请运行以下命令处理数据：")
            print("   1. python export_comments_for_semantic.py --limit 100")
            print("   2. python run_semantic_pipeline.py <json文件> --platform bilibili")
            return
        
        # 3. 检查时间范围
        print("\n3. 检查数据时间范围...")
        time_range_query = """
        SELECT 
            MIN(processed_at) as min_time,
            MAX(processed_at) as max_time,
            COUNT(DISTINCT platform) as platform_count
        FROM comment_semantic
        """
        time_df = session.execute(text(time_range_query)).fetchone()
        
        if time_df and time_df[0]:
            min_time = int(time_df[0])
            max_time = int(time_df[1])
            platform_count = int(time_df[2])
            
            min_date = datetime.fromtimestamp(min_time).strftime('%Y-%m-%d %H:%M:%S')
            max_date = datetime.fromtimestamp(max_time).strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"   - 最早数据时间: {min_date}")
            print(f"   - 最新数据时间: {max_date}")
            print(f"   - 平台数量: {platform_count}")
            
            # 检查当前日期范围
            now = datetime.now()
            days_ago_30 = (now.timestamp() - 30 * 24 * 3600)
            days_ago_365 = (now.timestamp() - 365 * 24 * 3600)
            
            print(f"\n   [提示] Dashboard 默认查询最近365天的数据（已改进）")
            if max_time < days_ago_30:
                print(f"   [警告] 最新数据在30天前，请调整Dashboard的日期范围")
                print(f"   [建议] 将日期范围设置为: {datetime.fromtimestamp(min_time).strftime('%Y-%m-%d')} 至 {datetime.fromtimestamp(max_time).strftime('%Y-%m-%d')}")
        else:
            print("   [警告] 无法获取时间范围")
        
        # 4. 检查平台分布
        print("\n4. 检查平台分布...")
        platform_query = """
        SELECT platform, COUNT(*) as count 
        FROM comment_semantic 
        GROUP BY platform
        ORDER BY count DESC
        """
        platform_result = session.execute(text(platform_query))
        platforms = platform_result.fetchall()
        
        if platforms:
            print("   平台数据分布:")
            for platform, count in platforms:
                print(f"   - {platform}: {count} 条")
        else:
            print("   [警告] 没有平台数据")
        
        # 5. 检查实体数据
        print("\n5. 检查实体数据...")
        entity_query = """
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN entities_json IS NOT NULL 
                     AND entities_json != '' 
                     AND entities_json != '[]' 
                THEN 1 ELSE 0 END) as with_entities
        FROM comment_semantic
        """
        entity_result = session.execute(text(entity_query)).fetchone()
        total = entity_result[0]
        with_entities = entity_result[1] or 0
        
        print(f"   - 总记录数: {total}")
        print(f"   - 有实体数据的记录数: {with_entities}")
        if total > 0:
            print(f"   - 实体数据覆盖率: {with_entities/total*100:.1f}%")
        
        if with_entities == 0:
            print("\n   [警告] 没有实体数据！")
            print("   [原因] 可能是：")
            print("   1. 使用了改进前的 Prompt（已修复）")
            print("   2. LLM 没有返回实体数据")
            print("   [解决方案] 重新运行语义处理流水线（使用改进后的 Prompt）")
        
        print("\n" + "=" * 70)
        print("检查完成")
        print("=" * 70)
        
        # 给出建议
        if total_count > 0:
            print("\n[建议]")
            if with_entities == 0:
                print("1. 重新运行语义处理流水线以使用改进后的 Prompt")
                print("   python export_comments_for_semantic.py --limit 100")
                print("   python run_semantic_pipeline.py <json文件> --platform bilibili")
            else:
                print("1. 如果Dashboard仍显示无数据，请检查日期范围是否包含数据时间范围")
                if time_df and time_df[0]:
                    print(f"2. 建议将日期范围设置为: {datetime.fromtimestamp(min_time).strftime('%Y-%m-%d')} 至 {datetime.fromtimestamp(max_time).strftime('%Y-%m-%d')}")
        
    except Exception as e:
        print(f"\n[错误] {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()
        engine.dispose()

if __name__ == "__main__":
    check_semantic_status()

