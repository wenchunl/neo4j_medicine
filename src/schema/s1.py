from neo4j import GraphDatabase


class Neo4jSchemaExtractor:
    def __init__(self, uri, username, password):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self):
        self.driver.close()

    def extract_schema(self):
        """提取完整Schema信息"""
        with self.driver.session() as session:
            # 1. 获取所有节点标签
            node_labels = session.run("CALL db.labels()").data()

            # 2. 获取所有关系类型
            rel_types = session.run("CALL db.relationshipTypes()").data()

            # 3. 获取节点属性
            node_properties = session.run("""
                CALL db.schema.nodeTypeProperties()
                YIELD nodeType, propertyName, propertyTypes, mandatory
                RETURN nodeType, propertyName, propertyTypes, mandatory
            """).data()

            # 4. 获取关系属性
            rel_properties = session.run("""
                CALL db.schema.relTypeProperties()
                YIELD relType, propertyName, propertyTypes, mandatory
                RETURN relType, propertyName, propertyTypes, mandatory
            """).data()

            # 5. 获取索引信息
            indexes = session.run("SHOW INDEXES").data()

            # 6. 获取约束信息
            constraints = session.run("SHOW CONSTRAINTS").data()

            return {
                'node_labels': node_labels,
                'relationship_types': rel_types,
                'node_properties': node_properties,
                'relationship_properties': rel_properties,
                'indexes': indexes,
                'constraints': constraints
            }

    def format_schema_for_llm(self):
        """格式化成适合LLM理解的文本"""
        schema_data = self.extract_schema()

        # 整理节点属性
        node_props_dict = {}
        for item in schema_data['node_properties']:
            label = item['nodeType']
            if label not in node_props_dict:
                node_props_dict[label] = []
            node_props_dict[label].append({
                'name': item['propertyName'],
                'types': item['propertyTypes'],
                'mandatory': item['mandatory']
            })

        # 整理关系属性
        rel_props_dict = {}
        for item in schema_data['relationship_properties']:
            rel_type = item['relType']
            if rel_type not in rel_props_dict:
                rel_props_dict[rel_type] = []
            rel_props_dict[rel_type].append({
                'name': item['propertyName'],
                'types': item['propertyTypes']
            })

        # 生成格式化文本
        schema_text = "=== Neo4j Graph Database Schema ===\n\n"

        # 节点信息
        schema_text += "## 节点类型 (Node Labels):\n"
        for label_info in schema_data['node_labels']:
            label = label_info['label']
            schema_text += f"\n### {label}\n"
            if label in node_props_dict:
                schema_text += "属性:\n"
                for prop in node_props_dict[label]:
                    mandatory = " (必填)" if prop['mandatory'] else ""
                    schema_text += f"  - {prop['name']}: {prop['types']}{mandatory}\n"

        # 关系信息
        schema_text += "\n## 关系类型 (Relationship Types):\n"
        for rel_info in schema_data['relationship_types']:
            rel_type = rel_info['relationshipType']
            schema_text += f"\n### {rel_type}\n"
            if rel_type in rel_props_dict:
                schema_text += "属性:\n"
                for prop in rel_props_dict[rel_type]:
                    schema_text += f"  - {prop['name']}: {prop['types']}\n"

        # 索引信息
        schema_text += "\n## 索引 (Indexes):\n"
        for idx in schema_data['indexes']:
            schema_text += f"  - {idx.get('labelsOrTypes', [])} on {idx.get('properties', [])}\n"

        # 约束信息
        schema_text += "\n## 约束 (Constraints):\n"
        for cons in schema_data['constraints']:
            schema_text += f"  - {cons.get('name', 'N/A')}: {cons.get('type', 'N/A')}\n"

        return schema_text


# 使用示例
if __name__ == "__main__":
    extractor = Neo4jSchemaExtractor(
        uri="bolt://localhost:7687",
        username="neo4j",
        password="wcl123456"
    )

    extracted_schema_text = extractor.format_schema_for_llm()
    print(extracted_schema_text)

    extractor.close()
