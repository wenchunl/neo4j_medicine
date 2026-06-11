from neo4j import GraphDatabase
from config.neo4j_config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD


class Neo4jConnection:
    def __init__(self, uri=NEO4J_URI, user=NEO4J_USER, password=NEO4J_PASSWORD):
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        if self._driver:
            self._driver.close()

    def query(self, cypher_query, parameters=None):
        parameters = parameters or {}
        with self._driver.session() as session:
            result = session.run(cypher_query, parameters)
            return [record.data() for record in result]


# Singleton instance
db = Neo4jConnection()