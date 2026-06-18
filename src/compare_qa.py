"""
对比测试：旧版规则匹配 vs 新版LLM Cypher生成
"""
from qa import MedicineQA
from smart_qa import SmartMedicineQA


def compare_qa_systems():
    """对比两种问答系统"""
    
    print("\n" + "=" * 80)
    print("医药问答系统对比测试")
    print("=" * 80 + "\n")
    
    # 初始化两个系统
    old_qa = MedicineQA()
    new_qa = SmartMedicineQA()
    
    test_questions = [
        "布洛芬的副作用",
        "阿司匹林治什么",
        "感冒怎么办",
        "头痛怎么治",
        "布洛芬的用途是什么？",
        "哪些药物可以治疗哮喘？"
    ]
    
    for question in test_questions:
        print(f"\n{'='*80}")
        print(f"问题: {question}")
        print(f"{'='*80}\n")
        
        # 旧版系统（基于规则匹配）
        print("【旧版】基于规则匹配的问答系统")
        print("-" * 80)
        try:
            old_answer = old_qa.answer(question)
            print(f"回答: {old_answer}")
        except Exception as e:
            print(f"错误: {e}")
        
        print()
        
        # 新版系统（基于LLM生成Cypher）
        print("【新版】基于LLM的Cypher生成链")
        print("-" * 80)
        try:
            new_answer = new_qa.answer(question)
            print(f"回答: {new_answer}")
        except Exception as e:
            print(f"错误: {e}")
        
        print()
    
    print("\n" + "=" * 80)
    print("对比测试完成")
    print("=" * 80 + "\n")
    
    # 总结
    print("📊 系统对比总结:\n")
    print("旧版系统 (MedicineQA):")
    print("  ✅ 优点: 速度快、确定性高、无需调用LLM")
    print("  ❌ 缺点: 只能处理预定义的问题模式、灵活性差")
    print("  📌 适用场景: 固定模式的查询、对响应速度要求高的场景\n")
    
    print("新版系统 (SmartMedicineQA):")
    print("  ✅ 优点: 灵活性强、可理解多种问法、易于扩展")
    print("  ❌ 缺点: 需要调用LLM API、响应较慢、可能有成本")
    print("  📌 适用场景: 复杂查询、自然语言理解、多样化问法\n")


if __name__ == "__main__":
    compare_qa_systems()
