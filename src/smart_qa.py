from cypher_chain import CypherGenerationChain


class SmartMedicineQA:
    """
    基于LLM的医药问答系统
    使用自定义Cypher生成链替代langchain-neo4j
    """
    
    def __init__(self):
        self.cypher_chain = CypherGenerationChain()
    
    def answer(self, question):
        """
        回答医药相关问题
        
        Args:
            question: 用户问题
            
        Returns:
            str: 回答内容
        """
        question = question.strip()
        
        # 直接使用Cypher生成链回答问题
        answer = self.cypher_chain.answer_question(question)
        
        return answer


# 测试
if __name__ == "__main__":
    qa = SmartMedicineQA()
    
    print("\n" + "=" * 80)
    print("医药知识图谱智能问答系统（基于LLM的Cypher生成）")
    print("=" * 80 + "\n")
    
    test_questions = [
        "布洛芬的副作用是什么？",
        "阿司匹林有什么用途？",
        "布洛芬可以治疗什么疾病？",
        "感冒怎么办？",
        "头痛怎么治？"
    ]
    
    for question in test_questions:
        print(f"❓ 问题: {question}")
        answer = qa.answer(question)
        print(f"💡 回答: {answer}\n")
        print("-" * 80 + "\n")
