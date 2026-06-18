import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from db import db


class CypherGenerationChain:
    """
    旧版风格的Cypher生成链
    不使用langchain-neo4j，直接调用LLM生成Cypher查询
    """
    
    def __init__(self):
        # 加载环境变量
        env_path = Path(__file__).parent / '.env'
        load_dotenv(dotenv_path=env_path)
        
        # 初始化OpenAI客户端（使用DeepSeek）
        self.client = OpenAI(
            api_key=os.getenv('DEEPSEEK_API_KEY', 'sk-****'),
            base_url=os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
        )
        self.model = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
        
        # 定义Schema信息
        self.schema_info = {
            "nodes": [
                {
                    "label": "Medicine",
                    "properties": ["name", "description", "usage", "side_effects"]
                },
                {
                    "label": "Disease",
                    "properties": ["name"]
                }
            ],
            "relationships": [
                {
                    "type": "TREATS",
                    "start_node": "Medicine",
                    "end_node": "Disease"
                }
            ]
        }
        
        # Cypher生成Prompt模板
        self.cypher_prompt_template = """你是一个Neo4j Cypher查询专家。根据以下图谱Schema和用户问题，生成准确的Cypher查询语句。

### 图谱Schema

节点类型：
{node_info}

关系类型：
{relationship_info}

### 重要规则
1. 只能使用上述Schema中定义的节点标签、关系类型和属性
2. 【关键】无论什么情况，都直接使用字符串字面量（用单引号包裹），绝对不要使用参数化查询（$符号）
   - 正确示例：MATCH (m:Medicine {{name: '布洛芬'}})
   - 正确示例：WHERE d.name CONTAINS '过敏'
   - 错误示例：MATCH (m:Medicine {{name: $name}}) ← 禁止使用$符号
3. 添加 LIMIT 限制返回结果数量（默认LIMIT 10）
4. 注意关系方向：(Medicine)-[:TREATS]->(Disease) 表示药物治疗疾病
5. 查询药物副作用/用途时，直接返回Medicine节点的属性
6. 查询治疗某疾病的药物时，需要遍历TREATS关系
7. 如果查询涉及聚合，使用 WITH 子句
8. 对于模糊查询（如"抗过敏"、"感冒类"），使用 CONTAINS 或 STARTS WITH
9. 只输出Cypher查询语句，不要包含任何解释、代码格式或其他文字

### 示例

用户问题：布洛芬的副作用是什么？
Cypher查询：
MATCH (m:Medicine {{name: '布洛芬'}})
RETURN m.side_effects AS side_effects
LIMIT 10

用户问题：感冒怎么办？
Cypher查询：
MATCH (m:Medicine)-[:TREATS]->(d:Disease {{name: '感冒'}})
RETURN m.name AS medicine
LIMIT 10

用户问题：找出所有能治疗哮喘的药物
Cypher查询：
MATCH (m:Medicine)-[:TREATS]->(d:Disease {{name: '哮喘'}})
RETURN m.name AS medicine
LIMIT 10

用户问题：找出所有的抗过敏药物
Cypher查询：
MATCH (m:Medicine)-[:TREATS]->(d:Disease)
WHERE d.name CONTAINS '过敏'
RETURN m.name AS medicine
LIMIT 10

用户问题：找出副作用有可能导致口干的药物
Cypher查询：
MATCH (m:Medicine)
WHERE m.side_effects CONTAINS '口干'
RETURN m.name AS medicine, m.side_effects
LIMIT 10

### 用户问题
{question}

请生成Cypher查询："""

    def _format_schema(self):
        """格式化Schema信息为文本"""
        node_info = ""
        for node in self.schema_info["nodes"]:
            props = ", ".join(node["properties"])
            node_info += f"- {node['label']} (属性: {props})\n"
        
        relationship_info = ""
        for rel in self.schema_info["relationships"]:
            relationship_info += f"- ({rel['start_node']})-[:{rel['type']}]->({rel['end_node']})\n"
        
        return node_info, relationship_info

    def generate_cypher(self, question):
        """
        根据用户问题生成Cypher查询
        
        Args:
            question: 用户的自然语言问题
            
        Returns:
            dict: 包含生成的Cypher查询和执行结果
        """
        try:
            # 格式化Schema
            node_info, relationship_info = self._format_schema()
            
            # 构建Prompt
            prompt = self.cypher_prompt_template.format(
                node_info=node_info,
                relationship_info=relationship_info,
                question=question
            )
            
            # 调用LLM生成Cypher
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是Neo4j Cypher查询专家，只输出Cypher语句"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # 低温度以保证稳定性
                max_tokens=500
            )
            
            # 提取生成的Cypher
            cypher_query = response.choices[0].message.content.strip()
            
            # 清理可能的代码块标记
            cypher_query = cypher_query.replace("```cypher", "").replace("```", "").strip()
            
            print(f"[DEBUG] 生成的Cypher查询:\n{cypher_query}\n")
            
            # 执行查询
            result = db.query(cypher_query)
            
            return {
                "success": True,
                "cypher": cypher_query,
                "result": result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "cypher": None,
                "result": None
            }

    def answer_question(self, question):
        """
        回答用户问题（生成Cypher并执行）
        
        Args:
            question: 用户的自然语言问题
            
        Returns:
            str: 自然语言回答
        """
        result = self.generate_cypher(question)
        
        if not result["success"]:
            return f"查询失败: {result['error']}"
        
        if not result["result"]:
            return "未找到相关信息"
        
        # 简单格式化结果
        return self._format_answer(result["result"], question)
    
    def _format_answer(self, query_result, question):
        """将查询结果格式化为自然语言回答"""
        if not query_result:
            return "未找到相关信息"
        
        # 根据问题类型格式化答案
        if "副作用" in question or "不良反应" in question:
            if query_result and len(query_result) > 0:
                side_effects = query_result[0].get('side_effects', '暂无数据')
                return f"副作用包括：{side_effects}"
        
        elif "用途" in question or "作用" in question:
            if query_result and len(query_result) > 0:
                usage = query_result[0].get('usage', '暂无数据')
                return f"用途/作用：{usage}"
        
        elif "治疗" in question or "治什么" in question:
            diseases = [r.get('disease') for r in query_result if r.get('disease')]
            if diseases:
                return f"可用于治疗：{', '.join(diseases)}"
        
        elif "怎么办" in question or "怎么治" in question:
            medicines = [r.get('medicine') for r in query_result if r.get('medicine')]
            if medicines:
                return f"可以使用：{', '.join(medicines)}"
        
        # 通用格式化
        return f"查询结果：{query_result}"


# 使用示例
if __name__ == "__main__":
    chain = CypherGenerationChain()
    
    # 测试问题
    # test_questions = [
    #     "布洛芬的副作用是什么？",
    #     "阿司匹林有什么用途？",
    #     "布洛芬可以治疗什么疾病？",
    #     "感冒怎么办？"
    # ]
    # test_questions = [
    #     "找出所有能治疗哮喘的药物",
    #     "找出所有的抗过敏药物",
    #     "找出副作用有可能导致口干的药物"
    # ]
    test_questions = [
        "找出所有能治疗哮喘的药物"
    ]
    
    print("=" * 60)
    for question in test_questions:
        print(f"\n问题: {question}")
        print("-" * 60)
        answer = chain.answer_question(question)
        print(f"回答: {answer}")
        print("=" * 60)
