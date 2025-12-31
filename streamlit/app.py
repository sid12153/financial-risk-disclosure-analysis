import os
import requests
import streamlit as st

# API_BASE = st.secrets.get("API_BASE", os.getenv("API_BASE", "http://api:8000"))
API_BASE = os.getenv("API_BASE") or st.secrets.get("API_BASE") or "http://api:8000"

st.set_page_config(page_title="Disclosure Intelligence", layout="wide")

st.markdown(
    """
    <style>
      .policy-pill {
        display:inline-block;
        padding:6px 10px;
        border-radius:999px;
        border:1px solid #e5e7eb;
        font-size:12px;
        background:#f9fafb;
        color:#111827;
      }

      .muted {
        color:#6b7280;
        font-size:13px;
      }

      .card{
        background: #121826;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 14px 14px;
        margin: 10px 0;
      }
      .card h4{ margin: 0 0 6px 0; }
      .muted{ opacity: 0.7; font-size: 0.9rem; }

      code {
        color:#1f2937;
        background:#f3f4f6;
        padding:2px 4px;
        border-radius:4px;
        font-size:12px;
      }

      .kpi {
        font-size:20px;
        font-weight:700;
        color:#111827;
      }

      .kpi-label {
        color:#6b7280;
        font-size:12px;
        margin-top:-2px;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Financial Disclosure Intelligence")
st.caption("Evidence-first answers from indexed SEC filings with strict refusal and citations.")
st.markdown(
    '<span class="policy-pill">✅ Zero-Hallucination Policy: Enforced (Planner + Verifier + Evidence)</span>',
    unsafe_allow_html=True
)

@st.cache_data(ttl=30)
def fetch_sources():
    r = requests.get(f"{API_BASE}/sources", timeout=30)
    r.raise_for_status()
    return r.json()

# ---- Load sources ----
try:
    sources = fetch_sources()
except Exception:
    st.error(f"Could not reach API at {API_BASE}. Start the FastAPI server first.")
    st.stop()

docs = sources.get("available_docs", [])
if not docs:
    st.warning("No indexed docs found. Add filings, build chunks + FAISS index, then retry.")
    st.stop()

# Debug (temporary): shows what keys the API returns
# Uncomment for 10 seconds if Year/Type are blank
# st.write("DEBUG /sources sample:", docs[0])

doc_options = [d.get("doc_id", "") for d in docs if d.get("doc_id")]
meta_map = {d["doc_id"]: d for d in docs if d.get("doc_id")}

# ---- Two-panel layout ----
left, right = st.columns([1, 2], gap="large")

with left:
    st.subheader("Query")
    selected_doc = st.selectbox("Filing", doc_options, index=0)

    meta = meta_map.get(selected_doc, {})
    company = meta.get("company") or "—"
    year = meta.get("filing_year") or "—"
    ftype = meta.get("filing_type") or "—"
    fname = meta.get("filename") or ""

    st.markdown(
        f"**Company:** {company}  \n"
        f"**Year:** {year}  \n"
        f"**Type:** {ftype}"
    )
    if fname:
        st.caption(fname)

    question = st.text_area(
        "Question",
        value="What regulatory or compliance risks are highlighted related to capital requirements and resolution planning?",
        height=110
    )
    top_k = st.slider("Top-K evidence chunks", 3, 10, 5, 1)
    ask_clicked = st.button("Run", use_container_width=True)


with right:
    st.subheader("Results")
    st.markdown('<div class="muted">Answers are produced only from retrieved excerpts. If evidence is weak or out of scope, the system refuses.</div>', unsafe_allow_html=True)

    if ask_clicked:
        payload = {"question": question, "doc_id": selected_doc, "top_k": int(top_k), "max_pages": None}

        with st.spinner("Retrieving evidence and running agents..."):
            try:
                resp = requests.post(f"{API_BASE}/ask", json=payload, timeout=300)
                if resp.status_code != 200:
                    st.error(f"API error: {resp.status_code}")
                    st.code(resp.text)
                    st.stop()
                data = resp.json()
            except Exception as e:
                st.error("Ask request failed.")
                st.write(str(e))
                st.stop()

        refused = bool(data.get("refused"))
        citations = data.get("citations", []) or []
        evidence = data.get("evidence", []) or []

        # --- KPIs (minimal + relevant) ---
        status = "REFUSED" if refused else "ANSWERED"
        status_color = "#ff4b4b" if refused else "#2ecc71"  # red / green

        k1, k2, k3 = st.columns(3)
        k1.markdown(
            f"<div style='font-size:28px;font-weight:800;color:{status_color}'>{status}</div>"
            f"<div class='kpi-label'>Status</div>",
            unsafe_allow_html=True
        )

        top_score = float(citations[0]["score"]) if citations else 0.0
        k2.markdown(
            f"<div style='font-size:28px;font-weight:800'>{top_score:.3f}</div>"
            f"<div class='kpi-label'>Top score</div>",
            unsafe_allow_html=True
        )

        k3.markdown(
            f"<div style='font-size:28px;font-weight:800'>{len(evidence)}</div>"
            f"<div class='kpi-label'>Evidence chunks</div>",
            unsafe_allow_html=True
        )

        st.divider()

        if refused:
            st.error(data.get("answer") or "I can’t answer that reliably from the indexed filings.")
            reason = data.get("refusal_reason", "")
            if reason:
                st.caption(reason)
        else:
            st.markdown("### Answer")
            st.write(data.get("answer", ""))

            st.markdown("### Sources")

            for i, ev in enumerate(evidence[: min(len(evidence), 5)]):
                chunk_id = ev.get("chunk_id", "")
                score = float(ev.get("score", 0.0))
                text_raw = ev.get("text", "") or ""
                text_clean = ev.get("text_clean", "") or ""

                st.markdown(
                    f"""
                    <div class="card">
                      <div style="display:flex;justify-content:space-between;align-items:center;">
                        <h4 style="margin:0;">Evidence excerpt</h4>
                        <div class="muted">score={score:.3f}</div>
                      </div>
                      <div class="muted" style="margin-top:6px;">Chunk: <code>{chunk_id}</code></div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                with st.expander("View excerpt", expanded=False):
                    tab1, tab2 = st.tabs(["Clean", "Raw"])
                    with tab1:
                        st.write(text_clean if text_clean else text_raw)
                    with tab2:
                        st.code(text_raw)

                    st.download_button(
                        "Download raw chunk",
                        data=text_raw.encode("utf-8"),
                        file_name=f"{chunk_id}.txt",
                        mime="text/plain",
                        key=f"dl_{chunk_id}_{i}",
                        use_container_width=True,
                    )
