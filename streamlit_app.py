"""Streamlit frontend for the Python Q&A Assistant.

Self-contained: it imports the RAG pipeline directly (no HTTP) and loads the
embedding model + FAISS index in-process. The FastAPI service in app/main.py
remains available separately as the REST API.

    streamlit run streamlit_app.py
"""
import os

import streamlit as st

# On Streamlit Community Cloud, secrets set in the dashboard are not always
# exposed as environment variables. Bridge them into os.environ BEFORE importing
# app.config (which reads os.getenv at import time).
try:
    for _key, _val in st.secrets.items():
        if isinstance(_val, str):
            os.environ.setdefault(_key, _val)
except Exception:
    pass

from app import config, rag
from app.indexer import build_index

st.set_page_config(page_title="Python Q&A Assistant", page_icon="🐍")


@st.cache_resource(show_spinner="Loading model and index...")
def init_pipeline():
    """Load the embedding model, FAISS index, and Groq client once (cached)."""
    rag.load_pipeline()
    return True


st.title("🐍 Python Q&A Assistant")
st.caption("Answers grounded in Stack Overflow Python Q&A, with citations.")

try:
    init_pipeline()
    ready = rag.is_ready()
except Exception as exc:
    ready = False
    st.error(f"Failed to load pipeline: {exc}")

with st.sidebar:
    st.markdown("[GitHub Repo](https://github.com/vaibhav-y/Python-QnA-Assistant)")
    st.subheader("Status")
    if ready:
        st.success("pipeline ready")
    else:
        st.warning("pipeline not loaded")

    st.subheader("Rebuild index")
    st.caption("Re-embed the FAISS index from the downloaded dataset.")
    max_docs = st.number_input("Max docs", 100, 200000, 20000, step=1000)
    col1, col2 = st.columns(2)
    min_q = col1.number_input("Min Q score", value=config.MIN_QUESTION_SCORE)
    min_a = col2.number_input("Min A score", value=config.MIN_ANSWER_SCORE)
    if st.button("Rebuild from dataset", use_container_width=True):
        try:
            with st.spinner("Building index — this can take a few minutes..."):
                n = build_index(
                    config.DATA_DIR, config.INDEX_DIR,
                    int(min_q), int(min_a), int(max_docs),
                )
                rag.reload_index()
            st.success(f"Rebuilt index with {n} vectors.")
        except Exception as exc:
            st.error(f"Rebuild failed: {exc}")

    st.divider()
    st.caption("Maintained by [Vaibhav Yadav](https://github.com/vaibhav-y/)")

# --- chat ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if question := st.chat_input("Ask a Python question..."):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        if not ready:
            st.error("Pipeline not loaded.")
        else:
            try:
                with st.spinner("Thinking..."):
                    result = rag.answer(question)
                st.markdown(result["answer"])
                sources = result.get("sources", [])
                if sources:
                    st.markdown("**Sources**")
                    for s in sources:
                        label = s.get("title") or s["url"]
                        st.markdown(f"- [{label}]({s['url']})")
                st.session_state.messages.append(
                    {"role": "assistant", "content": result["answer"]}
                )
            except Exception as exc:
                st.error(f"Error: {exc}")
