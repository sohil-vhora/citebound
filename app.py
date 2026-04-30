"""
Citebound — Streamlit chat UI
Citation-grounded Q&A for international students in Canada.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st

# Allow importing from scripts/
sys.path.insert(0, str(Path(__file__).parent / "scripts"))
from answer import answer_question  # noqa: E402

# ─────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Citebound",
    page_icon="📌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Tighter top padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 5rem;
        max-width: 900px;
    }

    /* Disclaimer banner */
    .disclaimer-banner {
        background: linear-gradient(90deg, #fff4e5 0%, #fffaf2 100%);
        border-left: 4px solid #ff9800;
        padding: 12px 16px;
        border-radius: 6px;
        margin-bottom: 24px;
        font-size: 14px;
        color: #5a3d00;
    }

    /* Source cards */
    .source-card {
        background: #f5f7fa;
        border: 1px solid #e1e5ea;
        border-left: 3px solid #1d4e89;
        padding: 12px 14px;
        border-radius: 6px;
        margin-bottom: 10px;
        font-size: 14px;
    }
    .source-card a {
        color: #1d4e89;
        text-decoration: none;
        font-weight: 500;
    }
    .source-card a:hover {
        text-decoration: underline;
    }
    .source-meta {
        font-size: 12px;
        color: #6b7785;
        margin-top: 4px;
    }

    /* Freshness badges */
    .badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 11px;
        font-weight: 600;
        margin-right: 6px;
    }
    .badge-fresh { background: #d4edda; color: #155724; }
    .badge-stale { background: #fff3cd; color: #856404; }
    .badge-unknown { background: #f8d7da; color: #721c24; }

    /* Hero */
    .hero-title {
        font-size: 32px;
        font-weight: 700;
        color: #1d4e89;
        margin-bottom: 4px;
    }
    .hero-sub {
        color: #6b7785;
        font-size: 15px;
        margin-bottom: 24px;
    }

    /* Sample question pills */
    .stButton > button {
        font-size: 13px;
        text-align: left;
        background: #f5f7fa;
        border: 1px solid #d8dde3;
        color: #1a1a1a;
        font-weight: 400;
    }
    .stButton > button:hover {
        background: #e8edf3;
        border-color: #1d4e89;
        color: #1d4e89;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────
def freshness_badge(date_str: str) -> str:
    """Return colored badge HTML based on age of source."""
    if not date_str or date_str == "unknown":
        return '<span class="badge badge-unknown">date unknown</span>'
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
        age = datetime.now() - date
        if age < timedelta(days=180):
            return f'<span class="badge badge-fresh">updated {date_str}</span>'
        else:
            return f'<span class="badge badge-stale">updated {date_str}</span>'
    except (ValueError, TypeError):
        return f'<span class="badge badge-unknown">{date_str}</span>'


# ─────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📌 Citebound")
    st.caption("A research project on high-stakes RAG.")

    st.markdown("---")

    st.markdown("**What I cover**")
    st.markdown(
        "- Study permits, PGWP, off-campus work\n"
        "- Express Entry, OINP, provincial PNPs\n"
        "- CRA tax basics for students\n"
        "- Provincial health coverage"
    )

    st.markdown("**What I don't do**")
    st.markdown(
        "- Tell you whether *you specifically* qualify\n"
        "- Predict application outcomes\n"
        "- Recommend a strategy for your case\n"
        "- Give legal, immigration, or tax advice"
    )

    st.markdown("---")

    st.markdown("**Stack**")
    st.caption(
        "Claude Opus 4.7 · voyage-3 embeddings · "
        "ChromaDB · Streamlit · 45 government sources"
    )

    st.markdown(
        "[GitHub →](https://github.com/sohil-vhora/citebound)"
    )

    if st.button("Clear chat", use_container_width=True):
        st.session_state["messages"] = []
        st.rerun()

# ─────────────────────────────────────────────────────────────
# Header + disclaimer
# ─────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">Citebound</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-sub">'
    "Citation-grounded answers for international students in Canada. "
    "Every answer cites a canada.ca or provincial government source — or refuses."
    '</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="disclaimer-banner">
        <strong>⚠️ Research project — not legal, immigration, or tax advice.</strong><br>
        For your specific situation, consult a Regulated Canadian Immigration Consultant
        via <a href="https://college-ic.ca" target="_blank">college-ic.ca</a> or a Canadian
        immigration lawyer. All decisions on immigration applications are made solely by IRCC.
    </div>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────
# Initialize chat state
# ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# ─────────────────────────────────────────────────────────────
# Sample questions (only shown when chat is empty)
# ─────────────────────────────────────────────────────────────
if not st.session_state["messages"]:
    st.markdown("**Try a question:**")
    sample_questions = [
        "How many hours can I work off-campus per week?",
        "Do Master's students need a PAL in 2026?",
        "How does the GST/HST credit work for newcomers?",
        "Can international students get OHIP in Ontario?",
        "Are co-op work permits still required after April 2026?",
        "How does Quebec's CAQ differ from a PAL?",
    ]
    cols = st.columns(2)
    for i, q in enumerate(sample_questions):
        if cols[i % 2].button(q, key=f"sample_{i}", use_container_width=True):
            st.session_state["pending_question"] = q
            st.rerun()

# ─────────────────────────────────────────────────────────────
# Render existing chat history
# ─────────────────────────────────────────────────────────────
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("sources"):
            with st.expander(f"Sources ({len(msg['sources'])})"):
                for src in msg["sources"]:
                    badge = freshness_badge(src["date_modified"])
                    st.markdown(
                        f"""
                        <div class="source-card">
                            <a href="{src['url']}" target="_blank">[{src['id']}] {src['title']}</a><br>
                            <div class="source-meta">
                                {badge}
                                <span style="margin-left:8px;">retrieval distance: {src['distance']:.3f}</span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

# ─────────────────────────────────────────────────────────────
# Handle new question — either from sample button or chat input
# ─────────────────────────────────────────────────────────────
# Always render the chat input — it must exist on every run for the user
# to ask follow-up questions
user_input = st.chat_input("Ask about study permits, work rules, taxes, or health coverage...")

new_question = None
if "pending_question" in st.session_state:
    new_question = st.session_state.pop("pending_question")
elif user_input:
    new_question = user_input

    # Show user message immediately
    st.session_state["messages"].append({"role": "user", "content": new_question})
    with st.chat_message("user"):
        st.markdown(new_question)

    # Run retrieval + answer
    with st.chat_message("assistant"):
        with st.spinner("Retrieving sources and drafting answer..."):
            try:
                result = answer_question(new_question, history=prior_history)
            except Exception as e:
                st.error(f"Something went wrong: {e}")
                st.stop()

        st.markdown(result["answer"])

        if result["sources"]:
            with st.expander(f"Sources ({len(result['sources'])})"):
                for src in result["sources"]:
                    badge = freshness_badge(src["date_modified"])
                    st.markdown(
                        f"""
                        <div class="source-card">
                            <a href="{src['url']}" target="_blank">[{src['id']}] {src['title']}</a><br>
                            <div class="source-meta">
                                {badge}
                                <span style="margin-left:8px;">retrieval distance: {src['distance']:.3f}</span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    # Store the assistant message in history
    st.session_state["messages"].append({
        "role": "assistant",
        "content": result["answer"],
        "sources": result["sources"],
    })