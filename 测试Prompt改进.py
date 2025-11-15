"""
测试 Prompt 改进是否生效
"""
import sys
from pathlib import Path

# 添加项目根目录到sys.path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from services.llm_client import SemanticLLMClient

def test_prompt():
    """测试 Prompt 是否包含改进内容"""
    
    print("=" * 70)
    print("测试 Prompt 改进")
    print("=" * 70)
    
    try:
        # 创建客户端实例（不需要实际调用 API）
        client = SemanticLLMClient()
        
        # 获取 System Message
        import inspect
        source = inspect.getsource(client._call_llm)
        
        # 检查 System Message
        if "必须仔细提取评论中提到的所有实体" in source:
            print("\n[成功] System Message 已更新")
        else:
            print("\n[失败] System Message 未更新")
        
        # 检查 User Prompt
        prompt_source = inspect.getsource(client._build_user_prompt)
        
        checks = [
            ("必须提取评论中提到的所有实体", "实体提取要求"),
            ("PERSON人物", "标准化实体类型"),
            ("ORG组织", "标准化实体类型"),
            ("LOCATION地点", "标准化实体类型"),
            ("PRODUCT产品", "标准化实体类型"),
            ("即使评论中没有明显的实体，也要尝试提取", "引导性提示"),
        ]
        
        print("\n检查 User Prompt:")
        all_passed = True
        for check_text, description in checks:
            if check_text in prompt_source:
                print(f"  [通过] {description}: {check_text[:30]}...")
            else:
                print(f"  [失败] {description}: 未找到")
                all_passed = False
        
        print("\n" + "=" * 70)
        if all_passed:
            print("[结论] Prompt 改进已生效！")
            print("[建议] 重新运行语义处理流水线以使用改进后的 Prompt")
        else:
            print("[结论] Prompt 改进未完全生效")
            print("[建议] 检查 services/llm_client.py 文件")
        
    except Exception as e:
        print(f"\n[错误] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_prompt()

