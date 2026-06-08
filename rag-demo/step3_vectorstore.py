"""
Step 3: 向量化 + 存入 Chroma
输入: Step 2 切好的 chunk 列表
做了什么: 每个 chunk 用本地 embedding 模型转成向量 → 存入 Chroma
输出: 一个存好向量的 Chroma 集合
验证: 打印存了多少条
"""
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# ====== 配置 ======
PDF_PATH = "test.pdf"

# Step 1: 加载
loader = PyPDFLoader(PDF_PATH)
pages = loader.load()

# Step 2: 切分
splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,
    chunk_overlap=30,
    separators=["\n\n", "\n", ".", " ", ""]
)
chunks = splitter.split_documents(pages)
print(f"✅ 加载 {len(pages)} 页，切了 {len(chunks)} 块")

# Step 3: 向量化 + 存入 Chroma
# 使用本地免费的 embedding 模型，不需要 API Key
embedding_fn = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embedding_fn,
    persist_directory="./chroma_db",
    collection_name="my_docs"
)

# 验证
count = vectorstore._collection.count()
print(f"✅ 已存入 Chroma：{count} 条")
print(f"✅ 向量库保存在：./chroma_db/")
