from db import db


class MedicineQA:
    def __init__(self):
        pass

    def answer(self, question):
        question = question.strip()

        if "副作用" in question or "不良反应" in question:
            return self._ask_side_effect(question)

        if "用途" in question or "有什么用" in question or "作用" in question:
            return self._ask_usage(question)

        if "治疗" in question or "治什么" in question:
            return self._ask_disease(question)

        # 疾病 → 药物 查询
        if "怎么办" in question or "怎么治" in question or "如何治疗" in question:
            return self._ask_medicine_for_disease(question)

        return "未能理解您的问题，请尝试询问例如：某药的副作用/用途/可以治疗什么。"

    def _extract_medicine(self, question):
        return question.replace("的副作用", "").replace("的用途", "").replace("的作用", "").replace("治什么", "").strip()

    def _extract_disease(self, question):
        for w in ["怎么办", "怎么治", "如何治疗"]:
            if w in question:
                return question.replace(w, "").replace("？", "").replace("?", "").strip()
        return question.strip()

    def _ask_side_effect(self, question):
        med = self._extract_medicine(question)
        query = """
        MATCH (m:Medicine {name: $name})
        RETURN m.side_effects AS side_effects
        """
        result = db.query(query, {"name": med})
        if result:
            return f"{med} 的副作用包括：{result[0].get('side_effects', '暂无数据')}"
        return f"数据库中未找到药物：{med}"

    def _ask_usage(self, question):
        med = self._extract_medicine(question)
        query = """
        MATCH (m:Medicine {name: $name})
        RETURN m.usage AS usage
        """
        result = db.query(query, {"name": med})
        if result:
            return f"{med} 的用途/作用：{result[0].get('usage', '暂无数据')}"
        return f"数据库中未找到药物：{med}"

    def _ask_medicine_for_disease(self, question):
        disease = self._extract_disease(question)
        query = """
        MATCH (d:Disease {name: $disease})<-[:TREATS]-(m:Medicine)
        RETURN m.name AS medicine
        """
        result = db.query(query, {"disease": disease})
        if result:
            meds = [r["medicine"] for r in result]
            return f"治疗{disease}可以使用：{', '.join(meds)}"
        return f"数据库中未找到治疗 {disease} 的药物"

    def _ask_disease(self, question):
        med = self._extract_medicine(question)
        query = """
        MATCH (m:Medicine {name: $name})-[:TREATS]->(d:Disease)
        RETURN d.name AS disease
        """
        result = db.query(query, {"name": med})
        if result:
            diseases = [r["disease"] for r in result]
            return f"{med} 可用于治疗：{', '.join(diseases)}"
        return f"数据库中未找到相关疾病信息：{med}"


if __name__ == "__main__":
    qa = MedicineQA()
    print(qa.answer("布洛芬的副作用"))
    print(qa.answer("阿司匹林治什么"))