"""
诊断为什么实体提取仍然为空
"""
import sys
import json
from pathlib import Path

# 添加项目根目录到sys.path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from database.db import get_db_engine
from datetime import datetime

def diagnose_entity_extraction():
    """诊断实体提取问题"""
    
    engine = get_db_engine()
    if not engine:
        print("[错误] 无法连接数据库")
        return
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("=" * 70)
        print("诊断实体提取问题")
        print("=" * 70)
        
        # 1. 检查最新的处理时间
        print("\n1. 检查最新处理时间...")
        result = session.execute(text("""
            SELECT 
                MAX(processed_at) as latest_time,
                COUNT(*) as total
            FROM comment_semantic
        """))
        row = result.fetchone()
        latest_time = row[0]
        total = row[1]
        
        if latest_time:
            latest_date = datetime.fromtimestamp(int(latest_time)).strftime('%Y-%m-%d %H:%M:%S')
            print(f"   - 最新处理时间: {latest_date}")
            print(f"   - 总记录数: {total}")
            
            # 检查是否在改进 Prompt 之后处理
            # 改进 Prompt 的时间大约是 2025-01-13
            improved_prompt_time = datetime(2025, 1, 13).timestamp()
            if latest_time < improved_prompt_time:
                print(f"\n   [警告] 最新数据在改进 Prompt 之前处理！")
                print(f"   [建议] 需要重新运行语义处理流水线")
            else:
                print(f"\n   [提示] 数据在改进 Prompt 之后处理")
                print(f"   [问题] 但实体数据仍然为空，需要进一步诊断")
        
        # 2. 检查一些最新的记录
        print("\n2. 检查最新的5条记录...")
        result = session.execute(text("""
            SELECT 
                comment_unique_id,
                content,
                entities_json,
                topics_json,
                processed_at
            FROM comment_semantic
            ORDER BY processed_at DESC
            LIMIT 5
        """))
        samples = result.fetchall()
        
        for i, (comment_id, content, entities_json, topics_json, processed_at) in enumerate(samples, 1):
            print(f"\n   记录 {i}:")
            print(f"   - comment_id: {comment_id}")
            print(f"   - 处理时间: {datetime.fromtimestamp(int(processed_at)).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   - content: {content[:50] if content else 'None'}...")
            
            # 检查 topics
            if topics_json:
                try:
                    topics = json.loads(topics_json)
                    if isinstance(topics, list) and len(topics) > 0:
                        print(f"   - topics: {topics[:3]}... (共{len(topics)}个)")
                    else:
                        print(f"   - topics: 空列表")
                except:
                    print(f"   - topics: 解析失败")
            else:
                print(f"   - topics: None")
            
            # 检查 entities
            if entities_json:
                try:
                    entities = json.loads(entities_json)
                    if isinstance(entities, list):
                        if len(entities) > 0:
                            print(f"   - entities: {len(entities)} 个实体")
                            for j, entity in enumerate(entities[:3], 1):
                                print(f"      {j}. {entity.get('name', 'N/A')} ({entity.get('type', 'N/A')})")
                        else:
                            print(f"   - entities: 空列表 []")
                    else:
                        print(f"   - entities: 非列表类型: {type(entities)}")
                except Exception as e:
                    print(f"   - entities_json 解析失败: {e}")
                    print(f"   - 原始数据: {entities_json[:200]}...")
            else:
                print(f"   - entities_json: None")
        
        # 3. 检查 Prompt 是否已更新
        print("\n3. 检查 Prompt 是否已更新...")
        try:
            from services.llm_client import SemanticLLMClient
            import inspect
            
            # 获取 _build_user_prompt 方法的源代码
            source = inspect.getsource(SemanticLLMClient._build_user_prompt)
            
            # 检查是否包含改进后的内容
            if "必须提取评论中提到的所有实体" in source:
                print("   [成功] Prompt 已更新（包含改进后的实体提取指令）")
            else:
                print("   [警告] Prompt 可能未更新")
            
            if "PERSON人物、ORG组织" in source or "PERSON" in source and "ORG" in source:
                print("   [成功] Prompt 包含标准化的实体类型")
            else:
                print("   [警告] Prompt 可能不包含标准化的实体类型")
                
        except Exception as e:
            print(f"   [错误] 无法检查 Prompt: {e}")
        
        # 4. 给出建议
        print("\n" + "=" * 70)
        print("诊断建议")
        print("=" * 70)
        
        if latest_time and latest_time < improved_prompt_time:
            print("\n[主要问题] 数据在改进 Prompt 之前处理")
            print("[解决方案] 重新运行语义处理流水线：")
            print("   1. python export_comments_for_semantic.py --limit 100")
            print("   2. python run_semantic_pipeline.py <json文件> --platform bilibili --limit 10")
        else:
            print("\n[可能原因]")
            print("   1. LLM 没有返回实体数据（即使使用了改进后的 Prompt）")
            print("   2. 评论内容本身不包含可识别的实体")
            print("   3. LLM API 配置问题")
            print("\n[建议]")
            print("   1. 检查 LLM API 密钥是否正确配置")
            print("   2. 查看语义处理流水线的日志输出")
            print("   3. 尝试处理一些包含明显实体的评论（如包含产品名、品牌名等）")
            print("   4. 检查 LLM 返回的原始 JSON 数据")
        
    except Exception as e:
        print(f"\n[错误] {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()
        engine.dispose()

if __name__ == "__main__":
    diagnose_entity_extraction()

