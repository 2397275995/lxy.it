"""
修复 comment_entity_relation 表：从 comment_semantic 表的 entities_json 字段重新生成关系数据
"""
import json
import time
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from database.db import get_db_engine
from database.models import CommentEntityRelation, SemanticEntity
from sqlalchemy import select

def fix_entity_relation_table():
    """从 comment_semantic 表的 entities_json 重新生成 comment_entity_relation 数据"""
    
    # 连接数据库
    engine = get_db_engine()
    if not engine:
        print("[错误] 无法连接数据库，请检查数据库配置")
        return
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("=" * 60)
        print("修复 comment_entity_relation 表")
        print("=" * 60)
        
        # 1. 检查 comment_semantic 表中是否有 entities_json 数据
        print("\n1. 检查数据源...")
        result = session.execute(text("""
            SELECT 
                comment_unique_id,
                entities_json
            FROM comment_semantic
            WHERE entities_json IS NOT NULL 
              AND entities_json != '' 
              AND entities_json != '[]'
        """))
        rows = result.fetchall()
        print(f"   - 找到 {len(rows)} 条有实体数据的记录")
        
        if len(rows) == 0:
            print("   [警告] 没有找到包含实体数据的记录！")
            print("   [提示] 请先运行语义处理流水线，确保 LLM 返回了实体数据")
            
            # 检查一些示例数据
            print("\n   检查示例数据...")
            result = session.execute(text("""
                SELECT comment_unique_id, entities_json 
                FROM comment_semantic 
                LIMIT 5
            """))
            samples = result.fetchall()
            for comment_id, entities_json in samples:
                print(f"      - comment_id: {comment_id}")
                if entities_json:
                    try:
                        entities = json.loads(entities_json)
                        print(f"        entities_json 类型: {type(entities)}, 长度: {len(entities) if isinstance(entities, list) else 'N/A'}")
                        if isinstance(entities, list) and len(entities) > 0:
                            print(f"        示例实体: {entities[0]}")
                    except:
                        print(f"        entities_json 解析失败: {entities_json[:100] if entities_json else 'None'}...")
                else:
                    print(f"        entities_json: 空")
            return
        
        # 2. 处理每条记录
        print("\n2. 开始处理数据...")
        now_ts = int(time.time())
        processed_count = 0
        relation_count = 0
        entity_count = 0
        
        for comment_unique_id, entities_json in rows:
            try:
                # 解析 entities_json
                entities = json.loads(entities_json)
                if not isinstance(entities, list) or len(entities) == 0:
                    continue
                
                # 处理每个实体
                for entity_data in entities:
                    if not isinstance(entity_data, dict):
                        continue
                    
                    entity_name = entity_data.get("name", "").strip()
                    entity_type = entity_data.get("type", "").strip()
                    
                    if not entity_name or not entity_type:
                        continue
                    
                    # 生成 unique_key
                    unique_key = f"{entity_type}:{entity_name}"
                    
                    # 1. 确保 semantic_entity 表中存在该实体
                    try:
                        stmt = select(SemanticEntity).where(SemanticEntity.entity_unique_key == unique_key)
                        result = session.execute(stmt)
                        existing_entity = result.scalar_one_or_none()
                    except Exception:
                        existing_entity = (
                            session.query(SemanticEntity)
                            .filter(SemanticEntity.entity_unique_key == unique_key)
                            .first()
                        )
                    
                    if not existing_entity:
                        # 创建新实体
                        metadata = {
                            "mention": entity_data.get("mention"),
                            "sentiment": entity_data.get("sentiment"),
                        }
                        metadata_json = json.dumps(metadata, ensure_ascii=False)
                        
                        new_entity = SemanticEntity(
                            entity_unique_key=unique_key,
                            name=entity_name,
                            entity_type=entity_type,
                            metadata_json=metadata_json,
                            first_seen_at=now_ts,
                            last_seen_at=now_ts,
                        )
                        session.add(new_entity)
                        entity_count += 1
                    else:
                        # 更新现有实体
                        existing_entity.last_seen_at = now_ts
                        metadata = {
                            "mention": entity_data.get("mention"),
                            "sentiment": entity_data.get("sentiment"),
                        }
                        existing_entity.metadata_json = json.dumps(metadata, ensure_ascii=False)
                    
                    # 2. 确保 comment_entity_relation 表中存在该关系
                    try:
                        stmt = select(CommentEntityRelation).where(
                            CommentEntityRelation.comment_unique_id == comment_unique_id,
                            CommentEntityRelation.entity_unique_key == unique_key,
                        )
                        result = session.execute(stmt)
                        existing_relation = result.scalar_one_or_none()
                    except Exception:
                        existing_relation = (
                            session.query(CommentEntityRelation)
                            .filter(
                                CommentEntityRelation.comment_unique_id == comment_unique_id,
                                CommentEntityRelation.entity_unique_key == unique_key,
                            )
                            .first()
                        )
                    
                    if not existing_relation:
                        # 创建新关系
                        new_relation = CommentEntityRelation(
                            comment_unique_id=comment_unique_id,
                            entity_unique_key=unique_key,
                            relation_type="mentions",
                            weight=1.0,
                            created_at=now_ts,
                        )
                        session.add(new_relation)
                        relation_count += 1
                    else:
                        # 更新现有关系
                        existing_relation.weight = 1.0
                        existing_relation.created_at = now_ts
                
                processed_count += 1
                
                if processed_count % 100 == 0:
                    print(f"   - 已处理 {processed_count} 条记录...")
                    session.commit()  # 每100条提交一次
                    
            except json.JSONDecodeError as e:
                print(f"   [警告] 解析 JSON 失败 (comment_id={comment_unique_id}): {e}")
                continue
            except Exception as e:
                print(f"   [警告] 处理记录失败 (comment_id={comment_unique_id}): {e}")
                continue
        
        # 3. 提交所有更改
        print("\n3. 提交更改...")
        session.commit()
        print(f"   ✓ 成功提交")
        
        # 4. 统计结果
        print("\n4. 处理结果:")
        print(f"   - 处理的评论记录数: {processed_count}")
        print(f"   - 创建/更新的实体数: {entity_count}")
        print(f"   - 创建/更新的关系数: {relation_count}")
        
        # 5. 验证结果
        print("\n5. 验证结果...")
        result = session.execute(text("SELECT COUNT(*) FROM comment_entity_relation"))
        total_relations = result.scalar()
        print(f"   - comment_entity_relation 表总记录数: {total_relations}")
        
        result = session.execute(text("SELECT COUNT(*) FROM semantic_entity"))
        total_entities = result.scalar()
        print(f"   - semantic_entity 表总记录数: {total_entities}")
        
        if total_relations > 0:
            print("\n[成功] 修复成功！comment_entity_relation 表现在有数据了。")
        else:
            print("\n[警告] comment_entity_relation 表仍然为空。")
            print("   可能原因:")
            print("   1. entities_json 数据格式不正确")
            print("   2. entity.name 或 entity.type 为空")
            print("   3. 数据解析失败")
        
    except Exception as e:
        print(f"\n[错误] {e}")
        session.rollback()
        import traceback
        traceback.print_exc()
    finally:
        session.close()
        engine.dispose()

if __name__ == "__main__":
    fix_entity_relation_table()

