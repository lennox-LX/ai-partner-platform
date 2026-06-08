"""
RAG 文档问答应用 — 完整版
上传 PDF → 提问 → AI 基于文档内容回答
"""
import os
import tempfile
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from openai import OpenAI

# ====== 页面配置 ======
st.set_page_config(page_title="RAG 文档问答", page_icon="📄")
st.title("📄 RAG 文档问答系统")
st.caption("上传 PDF，提问，AI 基于文档内容回答")

# ====== 侧边栏：API Key 配置 ======
with st.sidebar:
    st.header("⚙️ 配置")
    api_key = st.text_input(
        "DeepSeek API Key",
        type="password",
        value=os.getenv("DEEPSEEK_KEY", ""),
        help="从 platform.deepseek.com 获取"
    )
    st.markdown("---")
    st.markdown("### 🔧 参数")
    chunk_size = st.slider("Chunk 大小", 100, 1000, 500, step=50)
    chunk_overlap = st.slider("Chunk 重叠", 0, 200, 50, step=10)
    top_k = st.slider("检索数量", 1, 5, 3)

# ====== 初始化状态 ======
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# 加载 embedding 模型（只加载一次）
@st.cache_resource
def get_embedding_model():
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

embedding_fn = get_embedding_model()

# ====== 上传 PDF ======
uploaded_file = st.file_uploader("📤 上传 PDF 文档", type="pdf")

if uploaded_file is not None:
    # 保存临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    # 处理 PDF
    with st.spinner("处理文档中..."):
        # Step 1: 加载
        loader = PyPDFLoader(tmp_path)
        pages = loader.load()

        # Step 2: 切分
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        chunks = splitter.split_documents(pages)

        # Step 3: 存入向量库（内存模式）
        st.session_state.vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embedding_fn,
            collection_name=f"doc_{uploaded_file.name}"
        )

        # 清理临时文件
        os.unlink(tmp_path)

    st.success(f"✅ 文档已处理：{len(pages)} 页 → {len(chunks)} 个文本块")
    st.info("💡 现在可以在下方提问了")

# ====== 对话区域 ======
st.divider()
st.subheader("💬 提问")

# 显示历史对话
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if "sources" in msg:
            with st.expander("📎 参考来源"):
                for s in msg["sources"]:
                    st.text(s[:300])

# 输入问题
question = st.chat_input("基于文档提问...")

if question:
    if not api_key:
        st.error("请在侧边栏输入 DeepSeek API Key")
    elif st.session_state.vectorstore is None:
        st.error("请先上传 PDF 文档")
    else:
        # 显示用户问题
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.write(question)

        # Step 4: 检索
        results = st.session_state.vectorstore.similarity_search(question, k=top_k)
        context = "\n\n".join([doc.page_content for doc in results])

        # Step 5: 调 LLM
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")

        prompt = f"""Answer the question based ONLY on the following context.
If you cannot find the answer in the context, say "文档中未找到相关信息"。

Context:
{context}

Question: {question}

Answer:"""

        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": prompt}]
                )
                answer = response.choices[0].message.content
                st.write(answer)

            # 显示来源
            with st.expander("📎 参考来源"):
                for i, doc in enumerate(results):
                    st.text(f"[{i+1}] {doc.page_content[:300]}")

        # 保存对话历史
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "sources": [doc.page_content for doc in results]
        })

# ====== 页脚 ======
st.divider()
st.caption("🔧 技术栈: LangChain + Chroma + DeepSeek + Streamlit")
