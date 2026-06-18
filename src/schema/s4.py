from neo4j import GraphDatabase
import pickle
import os
from datetime import datetime, timedelta
import hashlib


class CachedSchemaExtractor:
    def __init__(self, uri, username, password, cache_dir='./schema_cache'):
        self.uri = uri
        self.username = username
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.cache_dir = cache_dir
        self.cache_ttl = timedelta(hours=24)  # 缓存24小时

        # 创建缓存目录
        os.makedirs(cache_dir, exist_ok=True)

    def close(self):
        self.driver.close()

    def _get_cache_key(self):
        """生成缓存键"""
        # 使用URI和用户名生成唯一的缓存键
        db_info = f"{self.uri}:{self.username}"
        return hashlib.md5(db_info.encode()).hexdigest()

    def _get_cache_path(self):
        """获取缓存文件路径"""
        cache_key = self._get_cache_key()
        return os.path.join(self.cache_dir, f"schema_{cache_key}.pkl")

    def _is_cache_valid(self):
        """检查缓存是否有效"""
        cache_path = self._get_cache_path()
        if not os.path.exists(cache_path):
            return False

        # 检查缓存时间
        cache_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
        return datetime.now() - cache_time < self.cache_ttl

    def _save_cache(self, schema):
        """保存Schema到缓存"""
        cache_path = self._get_cache_path()
        with open(cache_path, 'wb') as f:
            pickle.dump(schema, f)
        print(f"Schema已缓存到: {cache_path}")

    def _load_cache(self):
        """从缓存加载Schema"""
        cache_path = self._get_cache_path()
        with open(cache_path, 'rb') as f:
            return pickle.load(f)

    def get_schema(self, force_refresh=False):
        """获取Schema（带缓存）"""
        # 如果强制刷新或缓存无效，重新提取
        if force_refresh or not self._is_cache_valid():
            print("提取新Schema...")
            extracted_schema = self._extract_schema()
            self._save_cache(extracted_schema)
            return extracted_schema
        else:
            print("使用缓存的Schema...")
            return self._load_cache()

    def _extract_schema(self):
        """实际提取Schema逻辑"""
        with self.driver.session() as session:
            schema = {}

            # 节点标签
            node_labels = session.run("CALL db.labels()").data()
            schema['node_labels'] = [l['label'] for l in node_labels]

            # 关系类型
            rel_types = session.run("CALL db.relationshipTypes()").data()
            schema['relationship_types'] = [r['relationshipType'] for r in rel_types]

            # 节点属性
            node_props = session.run("""
                CALL db.schema.nodeTypeProperties()
                YIELD nodeType, propertyName, propertyTypes
                RETURN nodeType, collect({name: propertyName, types: propertyTypes}) as properties
            """).data()
            schema['node_properties'] = {
                item['nodeType']: item['properties']
                for item in node_props
            }

            # 关系属性
            rel_props = session.run("""
                CALL db.schema.relTypeProperties()
                YIELD relType, propertyName, propertyTypes
                RETURN relType, collect({name: propertyName, types: propertyTypes}) as properties
            """).data()
            schema['relationship_properties'] = {
                item['relType']: item['properties']
                for item in rel_props
            }

            # 关系模式
            patterns = session.run("""
                CALL db.schema.visualization()
                YIELD nodes, relationships
                RETURN relationships
            """).data()
            schema['patterns'] = patterns

            return schema

    @staticmethod
    def format_for_prompt(schema):
        """格式化为Prompt"""
        prompt = "# Neo4j Graph Schema\n\n"

        prompt += "## Nodes:\n"
        for label in schema['node_labels']:
            prompt += f"- {label}\n"
            if label in schema.get('node_properties', {}):
                for prop in schema['node_properties'][label]:
                    prompt += f"  - {prop['name']}: {prop['types']}\n"

        prompt += "\n## Relationships:\n"
        for rel_type in schema['relationship_types']:
            prompt += f"- {rel_type}\n"
            if rel_type in schema.get('relationship_properties', {}):
                for prop in schema['relationship_properties'][rel_type]:
                    prompt += f"  - {prop['name']}: {prop['types']}\n"

        return prompt


# 使用示例
if __name__ == "__main__":
    extractor = CachedSchemaExtractor(
        uri="bolt://localhost:7687",
        username="neo4j",
        password="wcl123456"
    )

    # 第一次调用：提取Schema
    print("第一次调用")
    unformatted_schema = extractor.get_schema()
    prompt_text = extractor.format_for_prompt(unformatted_schema)
    print(prompt_text)

    # 第二次调用：使用缓存
    print("\n第二次调用")
    unformatted_schema = extractor.get_schema()  # 会使用缓存
    print(extractor.format_for_prompt(unformatted_schema))

    # 强制刷新
    print("\n第三次调用")
    unformatted_schema = extractor.get_schema(force_refresh=True)
    print(extractor.format_for_prompt(unformatted_schema))

    extractor.close()
