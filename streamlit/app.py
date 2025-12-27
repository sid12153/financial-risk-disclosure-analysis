import requests
import streamlit as st

API_BASE = st.secrets.get("API_BASE", "http://127.0.0.1:8000")

st.set_page_config(page_title="Finance RAG (Strict)", layout="wide")
st.title("Finance RAG (Strict, Evidence-Based)")
st.caption(
    "Answers use only indexed SEC filings and must include citations. "
    "If evidence is missing or weak, the system should refuse."
)

# ----------------------------
# API helpers
# ----------------------------
@st.cache_data(ttl=60)
def fetch_sources():
    r = requests.get(f"{API_BASE}/sources", timeout=30)
    r.raise_for_status()
    return r.json()


def safe_get_sources():
    try:
        return fetch_sources()
    except Exception:
        st.error(f"Could not reach API at {API_BASE}. Start FastAPI first (uvicorn api.main:app --reload).")
        st.stop()


# ----------------------------
# Load sources
# ----------------------------
sources = safe_get_sources()
docs = sources.get("available_docs", [])
if not docs:
    st.warning("No indexed sources found. Make sure you built chunks + FAISS index, and the API can read them.")
    st.stop()

# Build display labels
# Example label: "MorganStanley — 2023 10-K (MorganStanley_2023_10K)"
def label_for(d):
    company = d.get("Company", d.get("doc_id", "Unknown"))
    year = d.get("Filing_year", "")
    ftype = d.get("Filing_type", "")
    doc_id = d.get("doc_id", "")
    return f"{company} — {year} {ftype} ({doc_id})"

doc_id_list = [d["doc_id"] for d in docs]
label_map = {d["doc_id"]: label_for(d) for d in docs}
meta_map = {d["doc_id"]: d for d in docs}

# ----------------------------
# Controls
# ----------------------------
left, right = st.columns([2, 1])

with left:
    selected_doc = st.selectbox(
        "Select filing",
        options=doc_id_list,
        format_func=lambda x: label_map.get(x, x),
        index=0,
    )

with right:
    d = meta_map.get(selected_doc, {})
    st.write("**Selected filing metadata**")
    st.write(f"- **doc_id:** `{d.get('doc_id', '')}`")
    st.write(f"- **Filename:** `{d.get('filename', '')}`")
    st.write(f"- **Company:** {d.get('company', '')}")
    st.write(f"- **Year:** {d.get('filing_year', '')}")
    st.write(f"- **Type:** {d.get('filing_type', '')}")

st.divider()

default_q = "What regulatory or compliance risks are highlighted related to capital requirements and resolution planning?"
question = st.text_input("Ask a question", value=default_q)

top_k = st.slider("Top-K evidence chunks", min_value=3, max_value=12, value=5, step=1)

with st.expander("Advanced"):
    search_all_docs = st.checkbox("Search across all filings (ignore selected filing)", value=False)
    timeout_seconds = st.number_input("API timeout (seconds)", min_value=30, max_value=600, value=180, step=30)

# ----------------------------
# Ask button
# ----------------------------
if st.button("Ask", type="primary"):
    payload = {
        "question": question.strip(),
        "doc_id": None if search_all_docs else selected_doc,
        "top_k": int(top_k),
    }

    if not payload["question"]:
        st.warning("Please enter a question.")
        st.stop()

    with st.spinner("Retrieving evidence..."):
        try:
            resp = requests.post(f"{API_BASE}/ask", json=payload, timeout=int(timeout_seconds))
            if resp.status_code != 200:
                st.error(f"API error: {resp.status_code}")
                st.code(resp.text)
                st.stop()
            data = resp.json()
        except Exception as e:
            st.error("Ask request failed.")
            st.write(str(e))
            st.stop()

    if data.get("refused"):
        st.error(data.get("answer") or "Refused.")
        reason = data.get("refusal_reason", "")
        if reason:
            st.caption(reason)
        st.stop()

    # ----------------------------
    # Render Answer
    # ----------------------------
    st.subheader("Answer")
    st.write(data.get("answer", ""))

    # ----------------------------
    # Render Citations
    # ----------------------------
    st.subheader("Citations")
    citations = data.get("citations", [])
    if citations:
        for c in citations:
            chunk_id = c.get("chunk_id", "")
            score = c.get("score", 0.0)
            # st.write(f"- `{chunk_id}` (score={score:.3f})")
            st.write(f"- `{c['chunk_id']}` (score={float(c['score']):.3f})")
    else:
        st.write("No citations returned.")

    # ----------------------------
    # Render Evidence
    # ----------------------------
    st.subheader("Evidence Excerpts")
    evidence = data.get("evidence", [])

    if not evidence:
        st.write("No evidence returned.")
    else:
        for ev in evidence:
            chunk_id = ev.get("chunk_id", "")
            score = float(ev.get("score", 0.0))

            # Prefer cleaned text if available (from your updated API)
            text_clean = ev.get("text_clean", "")
            text_raw = ev.get("text", "")
            text_to_show = text_clean if text_clean else text_raw

            with st.expander(f"{chunk_id} (score={score:.3f})"):
                st.write(text_to_show)

                # Optional: show raw text toggle for debugging
                show_raw = st.checkbox(f"Show raw text for {chunk_id}", value=False, key=f"raw_{chunk_id}")
                if show_raw and text_clean:
                    st.text(text_raw)

