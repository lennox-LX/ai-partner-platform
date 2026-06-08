"""
Step 5: 检索 + 拼 Prompt + 调 LLM 生成回答
输入: 用户问题
做了什么: 检索相关 chunk → 拼成 Prompt → 发给 DeepSeek → 得到回答
输出: 带有源资料依据的回答
验证: 打印完整 Prompt + LLM 回答
"""
import os
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from openai import OpenAI

# ====== 配置 ======
# 从环境变量读取 API Key
# Windows: set DEEPSEEK_KEY=sk-你的key
# Mac/Linux: export DEEPSEEK_KEY=sk-你的key
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_KEY")
if not DEEPSEEK_API_KEY:
    raise RuntimeError("请设置环境变量 DEEPSEEK_KEY")

QUESTION = "Which city is famous for pandas?"

# Step 1: 加载向量库 + 检索
embedding_fn = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embedding_fn,
    collection_name="my_docs"
)

results = vectorstore.similarity_search(QUESTION, k=2)
context = "\n\n".join([doc.page_content for doc in results])

# Step 2: 拼 Prompt
prompt = f"""Answer the question based ONLY on the following context.
If you cannot find the answer in the context, say "I cannot find the answer in the provided documents."

--- CONTEXT ---
{context}

--- QUESTION ---
{QUESTION}

Answer:"""

# Step 3: 发给 LLM
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com/v1"
)

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": prompt}]
)

answer = response.choices[0].message.content

# 验证输出
print("=" * 50)
print("📝 完整 Prompt 预览:")
print("=" * 50)
print(prompt)
print("\n" + "=" * 50)
print("🤖 LLM 回答:")
print("=" * 50)
print(answer)
print("\n" + "=" * 50)
print("📎 参考来源 (检索到的 chunk):")
print("=" * 50)
for i, doc in enumerate(results):
    print(f"[{i+1}] {doc.page_content[:100]}...")
