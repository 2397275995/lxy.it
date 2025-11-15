"""
测试 LLM 实体提取功能
"""
import sys
import json
from pathlib import Path

# 添加项目根目录到sys.path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from services.llm_client import SemanticLLMClient, CommentInput

def test_entity_extraction():
    """测试实体提取"""
    
    print("=" * 70)
    print("测试 LLM 实体提取功能")
    print("=" * 70)
    
    # 创建测试评论（包含明显的实体）
    test_comments = [
        CommentInput(
            comment_id="test_001",
            content="我在北京看了ChatGPT的发布会，OpenAI真的很厉害！",
            language="zh"
        ),
        CommentInput(
            comment_id="test_002",
            content="王者荣耀这个游戏太好玩了，我在上海玩了一整天。",
            language="zh"
        ),
    ]
    
    print("\n测试评论：")
    for comment in test_comments:
        print(f"  - {comment.content}")
    
    try:
        # 创建客户端
        print("\n正在调用 LLM...")
        client = SemanticLLMClient()
        
        # 调用 LLM
        results = client.analyze_batch(test_comments)
        
        print(f"\n收到 {len(results)} 条结果")
        
        # 检查结果
        for result in results:
            print(f"\n评论 ID: {result.comment_id}")
            print(f"  摘要: {result.summary}")
            print(f"  情绪: {result.sentiment_label}")
            print(f"  主题: {result.topics}")
            print(f"  实体数量: {len(result.entities)}")
            
            if result.entities:
                print("  实体列表:")
                for entity in result.entities:
                    print(f"    - {entity.name} ({entity.type})")
            else:
                print("  [警告] 没有提取到实体！")
        
        # 检查 Prompt
        print("\n" + "=" * 70)
        print("检查 Prompt 内容")
        print("=" * 70)
        
        import inspect
        prompt_source = inspect.getsource(client._build_user_prompt)
        
        # 显示 Prompt 的关键部分
        if "必须提取评论中提到的所有实体" in prompt_source:
            print("[成功] Prompt 包含实体提取要求")
        else:
            print("[失败] Prompt 不包含实体提取要求")
        
        if "PERSON人物" in prompt_source:
            print("[成功] Prompt 包含标准化实体类型")
        else:
            print("[失败] Prompt 不包含标准化实体类型")
        
        # 显示实际的 Prompt
        actual_prompt = client._build_user_prompt(test_comments)
        print("\n实际使用的 Prompt（前500字符）：")
        print(actual_prompt[:500] + "...")
        
    except Exception as e:
        print(f"\n[错误] {e}")
        import traceback
        traceback.print_exc()
        print("\n可能的原因：")
        print("1. LLM API 密钥未配置")
        print("2. LLM API 调用失败")
        print("3. 网络连接问题")

if __name__ == "__main__":
    test_entity_extraction()

