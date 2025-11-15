"""
诊断 comment_entity_relation 表为什么没有数据
"""
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config.base_config import DB_CONFIG

def check_entity_relation_data():
    """检查实体关系表的数据情况"""
    
    # 连接数据库
    db_url = (
        f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    )
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("=" * 60)
        print("诊断 comment_entity_relation 表数据问题")
        print("=" * 60)
        
        # 1. 检查 comment_semantic 表中是否有数据
        print("\n1. 检查 comment_semantic 表:")
        result = session.execute(text("SELECT COUNT(*) as count FROM comment_semantic"))
        semantic_count = result.scalar()
        print(f"   - comment_semantic 表总记录数: {semantic_count}")
        
        if semantic_count == 0:
            print("   ⚠️  警告: comment_semantic 表为空，请先运行语义处理流水线！")
            return
        
        # 2. 检查 comment_semantic 表中是否有 entities_json 数据
        print("\n2. 检查 entities_json 字段:")
        result = session.execute(text("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN entities_json IS NOT NULL AND entities_json != '' AND entities_json != '[]' THEN 1 ELSE 0 END) as has_entities
            FROM comment_semantic
        """))
        row = result.fetchone()
        total = row[0]
        has_entities = row[1]
        print(f"   - 总记录数: {total}")
        print(f"   - 有实体数据的记录数: {has_entities}")
        print(f"   - 无实体数据的记录数: {total - has_entities}")
        
        if has_entities == 0:
            print("   ⚠️  警告: 所有记录的 entities_json 都为空！")
            print("   💡 可能原因: LLM 没有返回实体数据，或者实体数据格式不正确")
            
            # 查看一个示例记录
            result = session.execute(text("""
                SELECT comment_id, content, entities_json 
                FROM comment_semantic 
                LIMIT 1
            """))
            sample = result.fetchone()
            if sample:
                print(f"\n   示例记录:")
                print(f"   - comment_id: {sample[0]}")
                print(f"   - content: {sample[1][:100]}...")
                print(f"   - entities_json: {sample[2]}")
            return
        
        # 3. 检查 entities_json 的内容格式
        print("\n3. 检查 entities_json 数据格式:")
        result = session.execute(text("""
            SELECT entities_json 
            FROM comment_semantic 
            WHERE entities_json IS NOT NULL 
              AND entities_json != '' 
              AND entities_json != '[]'
            LIMIT 5
        """))
        samples = result.fetchall()
        print(f"   - 查看前5条有实体数据的记录:")
        for i, (entities_json,) in enumerate(samples, 1):
            try:
                entities = json.loads(entities_json)
                print(f"\n   示例 {i}:")
                print(f"   - entities_json: {entities_json[:200]}...")
                print(f"   - 解析后实体数量: {len(entities) if isinstance(entities, list) else '格式错误'}")
                if isinstance(entities, list) and len(entities) > 0:
                    print(f"   - 第一个实体: {entities[0]}")
            except json.JSONDecodeError as e:
                print(f"   ⚠️  示例 {i} JSON 解析失败: {e}")
                print(f"   - 原始数据: {entities_json[:200]}...")
        
        # 4. 检查 semantic_entity 表
        print("\n4. 检查 semantic_entity 表:")
        result = session.execute(text("SELECT COUNT(*) as count FROM semantic_entity"))
        entity_count = result.scalar()
        print(f"   - semantic_entity 表总记录数: {entity_count}")
        
        if entity_count == 0:
            print("   ⚠️  警告: semantic_entity 表为空！")
            print("   💡 可能原因: _upsert_entities 方法没有正确执行，或者实体数据格式不符合要求")
        
        # 5. 检查 comment_entity_relation 表
        print("\n5. 检查 comment_entity_relation 表:")
        result = session.execute(text("SELECT COUNT(*) as count FROM comment_entity_relation"))
        relation_count = result.scalar()
        print(f"   - comment_entity_relation 表总记录数: {relation_count}")
        
        if relation_count == 0:
            print("   ⚠️  警告: comment_entity_relation 表为空！")
            
            # 如果 semantic_entity 有数据但 relation 没有，说明问题在关系插入逻辑
            if entity_count > 0:
                print("   💡 问题分析:")
                print("      - semantic_entity 表有数据，说明实体插入成功")
                print("      - comment_entity_relation 表无数据，说明关系插入失败")
                print("      - 可能原因:")
                print("        1. item.unique_id 格式不正确")
                print("        2. unique_key 生成逻辑有问题")
                print("        3. 事务提交失败")
                print("        4. 代码逻辑有bug")
                
                # 检查 unique_id 格式
                print("\n   检查 unique_id 格式:")
                result = session.execute(text("""
                    SELECT DISTINCT comment_unique_id 
                    FROM comment_semantic 
                    LIMIT 5
                """))
                unique_ids = [row[0] for row in result.fetchall()]
                print(f"   - comment_semantic 表中的 unique_id 示例:")
                for uid in unique_ids:
                    print(f"     * {uid}")
                
                result = session.execute(text("""
                    SELECT DISTINCT entity_unique_key 
                    FROM semantic_entity 
                    LIMIT 5
                """))
                entity_keys = [row[0] for row in result.fetchall()]
                print(f"   - semantic_entity 表中的 entity_unique_key 示例:")
                for ekey in entity_keys:
                    print(f"     * {ekey}")
        
        # 6. 尝试手动创建一条关系数据（用于测试）
        print("\n6. 数据关联检查:")
        if semantic_count > 0 and entity_count > 0 and relation_count == 0:
            print("   - 尝试查找可以关联的数据:")
            result = session.execute(text("""
                SELECT 
                    cs.comment_unique_id,
                    se.entity_unique_key
                FROM comment_semantic cs
                CROSS JOIN semantic_entity se
                LIMIT 1
            """))
            sample = result.fetchone()
            if sample:
                print(f"   - 找到可关联的数据:")
                print(f"     * comment_unique_id: {sample[0]}")
                print(f"     * entity_unique_key: {sample[1]}")
                print("   💡 建议: 检查 _upsert_entities 方法中的逻辑")
        
        # 7. 检查是否有错误日志
        print("\n7. 建议检查项:")
        print("   - 查看运行语义处理流水线时的日志输出")
        print("   - 检查是否有 '写入 MySQL 失败' 的错误信息")
        print("   - 确认 item.unique_id 的格式是否正确（应该是 '平台:comment_id'）")
        print("   - 确认 entity.name 和 entity.type 都不为空")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()
        engine.dispose()

if __name__ == "__main__":
    check_entity_relation_data()

