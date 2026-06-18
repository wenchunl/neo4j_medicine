# 旧版风格 Cypher 生成链使用说明

## 📋 概述

本项目实现了一个**不依赖 langchain-neo4j** 的自定义 Cypher 生成链，采用旧版风格的设计思路：

- ✅ 直接使用 OpenAI API（支持 DeepSeek）
- ✅ 自定义 Prompt 模板控制 Cypher 生成
- ✅ 轻量级实现，无重型框架依赖
- ✅ 完全掌控生成逻辑和错误处理

## 🏗️ 架构设计

```
用户问题 
    ↓
CypherGenerationChain (cypher_chain.py)
    ↓
[LLM 生成 Cypher] → [执行查询] → [格式化答案]
    ↓
自然语言回答
```

## 📁 核心文件说明

### 1. `cypher_chain.py` - 核心 Cypher 生成链

**主要类：** `CypherGenerationChain`

**关键方法：**
- `generate_cypher(question)` - 根据问题生成并执行 Cypher 查询
- `answer_question(question)` - 直接回答问题（返回自然语言）

**使用示例：**
```python
from cypher_chain import CypherGenerationChain

chain = CypherGenerationChain()

# 方式1: 获取原始 Cypher 和结果
result = chain.generate_cypher("布洛芬的副作用是什么？")
print(result['cypher'])   # 生成的 Cypher 语句
print(result['result'])   # 查询结果

# 方式2: 直接获取自然语言回答
answer = chain.answer_question("布洛芬的副作用是什么？")
print(answer)
```

### 2. `smart_qa.py` - 智能问答系统

**主要类：** `SmartMedicineQA`

这是对 `CypherGenerationChain` 的封装，提供更简洁的问答接口。

**使用示例：**
```python
from smart_qa import SmartMedicineQA

qa = SmartMedicineQA()
answer = qa.answer("阿司匹林可以治疗什么？")
print(answer)
```

### 3. `compare_qa.py` - 对比测试脚本

用于对比旧版规则匹配系统和新版 LLM 生成系统的差异。

**运行方式：**
```bash
cd src
python compare_qa.py
```

## 🔧 配置说明

### 环境变量配置（`.env` 文件）

确保 `src/.env` 文件中包含以下配置：

```env
DEEPSEEK_API_KEY=sk-your-api-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

也可以使用其他 OpenAI 兼容的 API 服务。

### Neo4j 配置（`config/neo4j_config.py`）

```python
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "your-password"
```

## 🎯 Schema 定义

当前实现的图谱 Schema（可在 `cypher_chain.py` 中修改）：

### 节点类型
- **Medicine** (药物)
  - name: 药物名称
  - description: 描述
  - usage: 用途/作用
  - side_effects: 副作用

- **Disease** (疾病)
  - name: 疾病名称

### 关系类型
- **TREATS**: `(Medicine)-[:TREATS]->(Disease)`
  - 表示药物治疗某疾病

## 💡 Prompt 模板设计

核心的 Cypher 生成 Prompt 模板位于 `CypherGenerationChain.__init__()` 中：

```python
self.cypher_prompt_template = """你是一个Neo4j Cypher查询专家...

### 图谱Schema
{node_info}
{relationship_info}

### 重要规则
1. 只能使用上述Schema中定义的节点标签、关系类型和属性
2. 使用参数化查询（例如 $name, $disease）避免注入攻击
3. 添加 LIMIT 限制返回结果数量
...

### 用户问题
{question}

请生成Cypher查询："""
```

**关键点：**
- 明确定义 Schema，防止 LLM 编造不存在的节点/关系
- 强调参数化查询，防止 Cypher 注入
- 要求只输出 Cypher，便于解析
- 设置低 temperature (0.1) 保证稳定性

## 🚀 快速开始

### 1. 安装依赖

项目已包含所需依赖，无需额外安装（使用现有的 `requirements.txt`）。

### 2. 构建知识图谱（如果尚未构建）

```bash
cd src
python build_kg.py
```

### 3. 测试新版 Cypher 生成链

```bash
cd src
python cypher_chain.py
```

### 4. 测试智能问答系统

```bash
cd src
python smart_qa.py
```

### 5. 对比新旧系统

```bash
cd src
python compare_qa.py
```

## 📊 新旧系统对比

| 特性 | 旧版 (MedicineQA) | 新版 (SmartMedicineQA) |
|------|-------------------|------------------------|
| 实现方式 | 硬编码规则匹配 | LLM 动态生成 Cypher |
| 灵活性 | ❌ 仅支持预定义模式 | ✅ 支持多种问法 |
| 扩展性 | ❌ 需手动添加规则 | ✅ 自动适应新查询 |
| 响应速度 | ✅ 快（本地执行） | ⚠️ 较慢（需调用 API） |
| 成本 | ✅ 免费 | ⚠️ API 调用成本 |
| 准确性 | ✅ 确定性高 | ⚠️ 依赖 LLM 质量 |
| 维护成本 | ❌ 高（需维护规则） | ✅ 低（只需调整 Prompt） |

## 🛠️ 自定义与扩展

### 修改 Schema

在 `cypher_chain.py` 中修改 `self.schema_info`：

```python
self.schema_info = {
    "nodes": [
        {
            "label": "YourNode",
            "properties": ["prop1", "prop2"]
        }
    ],
    "relationships": [
        {
            "type": "YOUR_REL",
            "start_node": "NodeA",
            "end_node": "NodeB"
        }
    ]
}
```

### 调整 Prompt 模板

修改 `self.cypher_prompt_template` 以适配你的场景：

- 添加更多约束规则
- 提供示例查询（few-shot learning）
- 调整输出格式要求

### 集成到现有系统

可以直接替换 `main.py` 中的问答逻辑：

```python
# 原来
from qa import MedicineQA
qa = MedicineQA()

# 改为
from smart_qa import SmartMedicineQA
qa = SmartMedicineQA()
```

## ⚠️ 注意事项

1. **API 密钥安全**：不要将 `.env` 文件提交到版本控制系统
2. **错误处理**：LLM 可能生成错误的 Cypher，建议添加重试机制
3. **性能优化**：可以考虑缓存常见问题的 Cypher 结果
4. **成本控制**：监控 API 调用次数，设置预算上限
5. **Schema 同步**：确保 Prompt 中的 Schema 与实际数据库一致

## 🔍 调试技巧

### 查看生成的 Cypher

在 `cypher_chain.py` 中已添加 DEBUG 输出：

```python
print(f"[DEBUG] 生成的Cypher查询:\n{cypher_query}\n")
```

### 验证 Cypher 语法

可以使用 Neo4j Browser 手动测试生成的查询。

### 调整 Temperature

如果生成的 Cypher 不稳定，可以降低 temperature：

```python
response = self.client.chat.completions.create(
    ...
    temperature=0.0,  # 更 deterministic
    ...
)
```

## 📝 示例输出

```
问题: 布洛芬的副作用是什么？
------------------------------------------------------------
[DEBUG] 生成的Cypher查询:
MATCH (m:Medicine {name: $name})
RETURN m.side_effects AS side_effects
LIMIT 10

回答: 副作用包括：可能引起胃肠道不适、头痛、过敏反应等
```

## 🎓 学习资源

- [Neo4j Cypher 官方文档](https://neo4j.com/docs/cypher-manual/)
- [OpenAI API 文档](https://platform.openai.com/docs/)
- [DeepSeek API 文档](https://platform.deepseek.com/)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个实现！

---

**作者**: AI Assistant  
**日期**: 2026-06-17  
**版本**: 1.0.0
