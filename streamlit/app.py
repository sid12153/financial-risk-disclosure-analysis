import requests
import streamlit as st

API_BASE = st.secrets.get("API_BASE", "http://127.0.0.1:8000")


st.set_page_config(page_title="Finance RAG (Strict)", layout="wide")
st.title("Finance RAG (Strict, Evidence-Based)")
st.caption("Answers are generated only from indexed SEC filings and must include citations. If evidence is missing, the system refuses.")


@st.cache_data(ttl=30)
def fetch_sources():
    r = requests.get(f"{API_BASE}/sources", timeout=30)
    r.raise_for_status()
    return r.json()


sources = None
try:
    sources = fetch_sources()
except Exception as e:
    st.error(f"Could not reach API at {API_BASE}. Start the FastAPI server first.")
    st.stop()

docs = sources.get("available_docs", [])
if not docs:
    st.warning("No PDFs found in data/raw. Add filings and refresh.")
    st.stop()

doc_options = [d["doc_id"] for d in docs]
doc_map = {d["doc_id"]: d["filename"] for d in docs}

col1, col2 = st.columns([2, 1])
with col1:
    selected_doc = st.selectbox("Select filing (doc_id)", doc_options, index=0)
with col2:
    st.write("**Filename:**")
    st.write(doc_map.get(selected_doc, ""))

question = st.text_input("Ask a question about the filing", value="What are the primary risk factors described in this filing?")
top_k = st.slider("Top-K evidence chunks", min_value=3, max_value=10, value=5, step=1)
max_pages = st.number_input("Max pages to parse (dev speed, optional)", min_value=0, max_value=500, value=0, step=10)

if st.button("Ask"):
    payload = {
        "question": question,
        "doc_id": selected_doc,
        "top_k": int(top_k),
        "max_pages": None if max_pages == 0 else int(max_pages),
    }

    with st.spinner("Retrieving evidence..."):
        resp = requests.post(f"{API_BASE}/ask", json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()

    if data.get("refused"):
        st.error(data.get("answer") or "Refused.")
        st.caption(data.get("refusal_reason", ""))
    else:
        st.subheader("Answer")
        st.write(data.get("answer", ""))

        st.subheader("Citations")
        citations = data.get("citations", [])
        if citations:
            for c in citations:
                st.write(f"- `{c['chunk_id']}` (score={c['score']})")
        else:
            st.write("No citations returned.")

        st.subheader("Evidence Excerpts")
        evidence = data.get("evidence", [])
        for ev in evidence:
            with st.expander(f"{ev['chunk_id']} (score={ev['score']})"):
                st.write(ev["text"])
