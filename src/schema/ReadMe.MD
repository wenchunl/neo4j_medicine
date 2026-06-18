The file under this directory is the source code to demonstrate
the different ways to extract the schema from a database.

-- Solution 1: using the neo4j native method

-- Solution 2: using langchain (not really working)
This way need APOC plugin in Neo4j installed and enabled
The APOC plugin is available at https://github.com/neo4j-contrib/neo4j-apoc-procedures
alternative way is to disable schema refresh use the following command:
    CALL db.schema.visualization()
and set the schema manually, see the below code:
```python
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
```

-- solution 3: Includes statistics and examples. Suitable when detailed schema information needed.

-- solution 4: using cached schema. see \schema\s4.py