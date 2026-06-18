#
#
# Important notes: using GraphCypherQAChain cannot find a proper solution,
# do not use it or try to modify it.
#
#
import os
from pathlib import Path

# from langchain_neo4j import Neo4jGraph
# from langchain_neo4j.graphs.neo4j_graph import Neo4jGraph
# from langchain_community.chains.graph_qa.cypher import GraphCypherQAChain
from langchain_neo4j import Neo4jGraph,GraphCypherQAChain
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# DeepSeek API Configuration
# These values are loaded from backend/.env file
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', 'sk-****')
DEEPSEEK_BASE_URL = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')


class SmartCypherGenerator:
    def __init__(self, uri, username, password):
        # 初始化Neo4j连接（自动提取Schema）
        self.graph = Neo4jGraph(
            url=uri,
            username=username,
            password=password,
            refresh_schema=False
        )

        # 初始化LLM
        self.llm = ChatOpenAI(
            api_key=SecretStr(DEEPSEEK_API_KEY),
            base_url=DEEPSEEK_BASE_URL,
            model=DEEPSEEK_MODEL
        )

        # 手动设置Schema（避免使用 APOC）
        self.graph.structured_schema = {
            "nodes": [
                {"labels": ["Disease"]},
                {"labels": ["Medicine"]}
            ],
            "relationships": [
                {
                    "start": ["Medicine"],
                    "end": ["Disease"],
                    "type": "TREATS"
                }
            ]
        }

        # 自定义Prompt模板
        self.cypher_generation_template = """
你是Neo4j Cypher查询专家。基于以下Graph Schema生成准确的Cypher查询。

Graph Schema:
{schema}

注意事项:
1. 仅使用Schema中存在的节点标签、关系类型和属性
2. 使用参数化查询 ($param) 避免注入
3. 优先使用有索引的字段进行查询
4. 添加 LIMIT 避免返回过多数据
5. 关系方向要正确
6. 如果查询涉及聚合，使用 WITH 子句

用户问题: {question}

仅输出Cypher查询语句，不包含任何解释:
"""

        self.cypher_prompt = PromptTemplate(
            template=self.cypher_generation_template,
            input_variables=["schema", "question"]
        )

        # 创建查询链
        self.chain = GraphCypherQAChain.from_llm(
            llm=self.llm,
            graph=self.graph,
            verbose=True,
            validate_cypher=True,  # 自动验证Cypher语法
            cypher_prompt=self.cypher_prompt,
            return_intermediate_steps=True,  # 返回中间步骤
            allow_dangerous_requests=True
        )

    def get_schema(self):
        """获取Schema文本"""
        return self.graph.structured_schema

    def generate_cypher(self, question):
        """生成并执行Cypher查询"""
        try:
            result = self.chain.invoke({"query": question})
            return {
                "success": True,
                "cypher": result.get('intermediate_steps', [{}])[0].get('query', ''),
                "result": result['result'],
                "context": result.get('intermediate_steps', [])
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def validate_cypher(self, cypher):
        """验证Cypher语法"""
        try:
            self.graph.query(f"EXPLAIN {cypher}")
            return {"valid": True, "message": "语法正确"}
        except Exception as e:
            return {"valid": False, "error": str(e)}


# 使用示例
if __name__ == "__main__":
    generator = SmartCypherGenerator(
        uri="bolt://localhost:7687",
        username="neo4j",
        password="wcl123456"
    )

    # 查看提取的Schema
    print("=== 自动提取的Schema ===")
    print(generator.get_schema())
    print("\n")

    # 生成查询
    questions = [
        "找出所有能治疗哮喘的药物",
        "找出所有的抗过敏药物",
        "找出副作用有可能导致口干的药物"
    ]

    for q in questions:
        print(f"\n问题: {q}")
        response = generator.generate_cypher(q)
        if response['success']:
            print(f"生成的Cypher: {response['cypher']}")
            print(f"查询结果: {response['result']}")
        else:
            print(f"错误: {response['error']}")
