from db import db
import csv


class KnowledgeGraphBuilder:
    def __init__(self):
        pass

    # CATION: this will clear all nodes and relationships
    def clear_graph(self):
        query = """
        MATCH (n) DETACH DELETE n
        """
        db.query(query)

    def load_medicine_data(self, filepath):
        medicines = []
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                medicines.append(row)
        return medicines

    def create_medicine_nodes(self, medicines):
        query = """
        UNWIND $rows AS row
        MERGE (m:Medicine {name: row.name})
        SET m.description = row.description,
            m.usage = row.usage,
            m.side_effects = row.side_effects
        """
        db.query(query, {"rows": medicines})

    def create_relationships(self, medicines):
        for med in medicines:
            if med.get("disease"):
                query = """
                MATCH (m:Medicine {name: $medicine})
                MERGE (d:Disease {name: $disease})
                MERGE (m)-[:TREATS]->(d)
                """
                db.query(query, {"medicine": med["name"], "disease": med["disease"]})

    def build(self, filepath):
        medicines = self.load_medicine_data(filepath)
        self.clear_graph()
        self.create_medicine_nodes(medicines)
        self.create_relationships(medicines)
        print("csv data loaded, and created node&relationships")


if __name__ == "__main__":
    builder = KnowledgeGraphBuilder()
    builder.build("data/medicine.csv")