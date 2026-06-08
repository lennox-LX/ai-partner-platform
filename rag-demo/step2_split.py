"""
Step 2: 切分文本
输入: Step 1 加载的页面列表
做了什么: RecursiveCharacterTextSplitter 切成小块
输出: 一堆 chunk，每个约 200 字
验证: 打印总共多少块 + 前 2 块的内容
"""
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ====== 改这里：换成你的 PDF 文件路径 ======
PDF_PATH = "test.pdf"

# Step 1: 加载（和 step1 一样）
loader = PyPDFLoader(PDF_PATH)
pages = loader.load()
print(f"✅ 加载 {len(pages)} 页")

# Step 2: 切分
splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,      # 每块最多 200 字（测试用小一点，看得清）
    chunk_overlap=30,    # 块之间重叠 30 字，防止切断上下文
    separators=["\n\n", "\n", ".", " ", ""]
)

chunks = splitter.split_documents(pages)

# 验证输出
print(f"✅ 切成了 {len(chunks)} 块")
print(f"\n--- 前 2 块内容 ---")
for i, chunk in enumerate(chunks[:2]):
    print(f"\n[Chunk {i+1}] ({len(chunk.page_content)} 字):")
    print(chunk.page_content)
