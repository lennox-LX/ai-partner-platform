"""
Step 4: 用户提问 → 检索相似 chunk
输入: 用户的问题
做了什么: 问题转向量 → 在 Chroma 中找最相似的 chunk
输出: 最相关的几个 chunk 原文
验证: 看检索到的内容跟问题相关吗？
"""
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# 加载之前存好的向量库
embedding_fn = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embedding_fn,
    collection_name="my_docs"
)

# ====== 改这里：试不同的问题看检索效果 ======
QUESTION = "Which city is famous for pandas?"

# 检索最相关的 2 个 chunk
results = vectorstore.similarity_search_with_score(QUESTION, k=2)

print(f"🔍 问题: {QUESTION}\n")
for i, (doc, score) in enumerate(results):
    # score 越小越相关（距离）
    print(f"--- 结果 {i+1} (距离: {score:.4f}) ---")
    print(doc.page_content)
    print()
