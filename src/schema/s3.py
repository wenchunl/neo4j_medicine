import json

from neo4j import GraphDatabase, Result


class AdvancedSchemaExtractor:
    def __init__(self, uri, username, password):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self):
        self.driver.close()

    @staticmethod
    def _run_query(session, query_text, parameters=None) -> Result:
        """
        执行Cypher查询的辅助方法
        :param session: Neo4j session 对象
        :param query_text: Cypher 查询字符串
        :param parameters: 查询参数字典
        :return: 查询结果对象
        """
        return session.run(query_text, parameters) if parameters else session.run(query_text)

    def extract_enhanced_schema(self, sample_size=1000):
        """提取增强Schema，包含统计信息"""
        with self.driver.session() as session:
            schema = {
                'nodes': {},
                'relationships': {},
                'statistics': {}
            }

            # 1. 获取节点信息（带采样统计）
            node_labels = self._run_query(session, "CALL db.labels()").data()

            for label_info in node_labels:
                label = label_info['label']

                # 统计节点数量
                count_query = f"MATCH (n:`{label}`) RETURN count(n) as count"
                count_result = self._run_query(session, count_query).single()
                node_count = count_result['count']

                # 采样节点获取属性名称和示例值
                sample_query = f"""
                MATCH (n:`{label}`)
                WITH n LIMIT {sample_size}
                UNWIND keys(n) as key
                WITH key, n[key] as value
                RETURN key, 
                       toString(value) as sample_value
                LIMIT 50
                """
                properties = self._run_query(session, sample_query).data()

                # 整理属性信息
                prop_dict = {}
                for prop in properties:
                    key = prop['key']
                    if key not in prop_dict:
                        prop_dict[key] = []
                    if len(prop_dict[key]) < 3 and prop['sample_value']:
                        prop_dict[key].append(prop['sample_value'])

                schema['nodes'][label] = {
                    'count': node_count,
                    'properties': {
                        key: {
                            'examples': examples
                        }
                        for key, examples in prop_dict.items()
                    }
                }

            # 2. 获取关系信息（带模式统计）
            rel_types = self._run_query(session, "CALL db.relationshipTypes()").data()

            for rel_info in rel_types:
                rel_type = rel_info['relationshipType']

                # 统计关系数量
                count_query = f"MATCH ()-[r:`{rel_type}`]->() RETURN count(r) as count"
                count_result = self._run_query(session, count_query).single()
                rel_count = count_result['count']

                # 获取关系模式 (起点标签 -> 关系 -> 终点标签)
                pattern_query = f"""
                MATCH (a)-[r:`{rel_type}`]->(b)
                WITH labels(a) as start_labels, labels(b) as end_labels
                RETURN DISTINCT start_labels, end_labels
                LIMIT 10
                """
                patterns = self._run_query(session, pattern_query).data()

                # 获取关系属性
                rel_prop_query = f"""
                MATCH ()-[r:`{rel_type}`]->()
                WITH r LIMIT {sample_size}
                UNWIND keys(r) as key
                RETURN DISTINCT key
                """
                rel_properties = [p['key'] for p in self._run_query(session, rel_prop_query).data()]

                schema['relationships'][rel_type] = {
                    'count': rel_count,
                    'patterns': [
                        {
                            'start': p['start_labels'],
                            'end': p['end_labels']
                        }
                        for p in patterns
                    ],
                    'properties': rel_properties
                }

            # 3. 获取索引和约束（返回列表，这是正确的）
            schema['indexes'] = self._run_query(session, "SHOW INDEXES").data()  # type: ignore[assignment]
            schema['constraints'] = self._run_query(session, "SHOW CONSTRAINTS").data()  # type: ignore[assignment]

            # 4. 总体统计
            total_nodes = self._run_query(session, "MATCH (n) RETURN count(n) as count").single()['count']
            total_rels = self._run_query(session, "MATCH ()-[r]->() RETURN count(r) as count").single()['count']

            schema['statistics'] = {
                'total_nodes': total_nodes,
                'total_relationships': total_rels,
                'node_label_count': len(node_labels),
                'relationship_type_count': len(rel_types)
            }

            return schema

    @staticmethod
    def format_for_llm(schema):
        """格式化成LLM友好的文本"""
        text = "=== Neo4j Graph Database Schema ===\n\n"

        # 统计概览
        stats = schema['statistics']
        text += f"## 数据库概览\n"
        text += f"- 总节点数: {stats['total_nodes']:,}\n"
        text += f"- 总关系数: {stats['total_relationships']:,}\n"
        text += f"- 节点类型数: {stats['node_label_count']}\n"
        text += f"- 关系类型数: {stats['relationship_type_count']}\n\n"

        # 节点详情
        text += "## 节点类型 (Nodes)\n\n"
        for label, info in schema['nodes'].items():
            text += f"### {label} (共 {info['count']:,} 个)\n"
            if info['properties']:
                text += "属性:\n"
                for prop_name, prop_info in info['properties'].items():
                    examples = ', '.join([str(e) for e in prop_info.get('examples', [])[:3]])
                    text += f"  - {prop_name}"
                    if examples:
                        text += f"\n    示例: {examples}"
                    text += "\n"
            else:
                text += "属性: 无\n"
            text += "\n"

        # 关系详情
        text += "## 关系类型 (Relationships)\n\n"
        for rel_type, info in schema['relationships'].items():
            text += f"### {rel_type} (共 {info['count']:,} 条)\n"
            text += "连接模式:\n"
            for pattern in info['patterns']:
                start = ', '.join(pattern['start']) if pattern['start'] else 'Any'
                end = ', '.join(pattern['end']) if pattern['end'] else 'Any'
                text += f"  - ({start})-[:{rel_type}]->({end})\n"
            if info['properties']:
                text += f"属性: {', '.join(info['properties'])}\n"
            text += "\n"

        # 索引信息
        text += "## 索引 (Indexes)\n"
        for idx in schema['indexes']:
            labels_or_types = idx.get('labelsOrTypes')
            properties = idx.get('properties')
            
            # 确保是可迭代的列表
            if isinstance(labels_or_types, list):
                labels = ', '.join(str(l) for l in labels_or_types)
            else:
                labels = str(labels_or_types) if labels_or_types else 'N/A'
            
            if isinstance(properties, list):
                props = ', '.join(str(p) for p in properties)
            else:
                props = str(properties) if properties else 'N/A'
            
            text += f"  - {labels} ({props})\n"
        text += "\n"

        # 约束信息
        text += "## 约束 (Constraints)\n"
        for cons in schema['constraints']:
            name = cons.get('name', 'N/A')
            cons_type = cons.get('type', 'N/A')
            text += f"  - {name}: {cons_type}\n"

        return text

    @staticmethod
    def export_to_json(schema, filename='schema.json'):
        """导出为JSON文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(schema, f, ensure_ascii=False, indent=2)
        print(f"Schema已导出到 {filename}")


# 使用示例
if __name__ == "__main__":
    extractor = AdvancedSchemaExtractor(
        uri="bolt://localhost:7687",
        username="neo4j",
        password="wcl123456"
    )

    # 提取增强Schema
    print("正在提取Schema...")
    extracted_schema = extractor.extract_enhanced_schema(sample_size=1000)

    # 格式化输出
    schema_text = extractor.format_for_llm(extracted_schema)
    print(schema_text)

    # 导出JSON
    extractor.export_to_json(schema_text)

    extractor.close()
