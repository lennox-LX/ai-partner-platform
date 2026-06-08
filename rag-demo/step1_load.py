"""
Step 1: 加载 PDF 文档
输入: PDF 文件路径
做了什么: PyPDFLoader 读取每一页
输出: 一个列表，每个元素是一页文本
验证: 打印总页数和第一页前 200 字
"""
from langchain_community.document_loaders import PyPDFLoader

# ====== 改这里：换成你的 PDF 文件路径 ======
PDF_PATH = "test.pdf"

# 加载 PDF
loader = PyPDFLoader(PDF_PATH)
pages = loader.load()

# 验证输出
print(f"✅ 共加载 {len(pages)} 页")
print(f"--- 第 1 页前 200 字 ---")
print(pages[0].page_content[:200])
