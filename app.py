import os
import streamlit as st
import json
import difflib
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
from core.question_engine import load_questions, get_visible_questions
from core.context_builder import build_context
from core.instruction_assembler import assemble_instruction
from core.version_control import create_version, get_version_history
from core.variant_manager import create_variant, get_variants
from core.feedback_capture import save_feedback, get_feedback
from core.iteration_control import save_context, get_context_answers, create_iteration_link, get_audit_trail
from storage.db import get_connection


# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CAF · Context Assembly Framework",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0f1117 !important;
    border-right: 1px solid #1e2130;
}
[data-testid="stSidebar"] * { color: #c9d1d9 !important; }

/* Nav label */
.nav-label {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    color: #6b7280 !important;
    text-transform: uppercase;
    margin: 1.2rem 0 0.5rem;
    padding: 0 0.2rem;
}

/* Radio items override */
[data-testid="stSidebar"] .stRadio > div { gap: 0 !important; }
[data-testid="stSidebar"] .stRadio label {
    padding: 0.45rem 0.8rem !important;
    border-radius: 8px !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    cursor: pointer !important;
    transition: background 0.15s !important;
    margin: 1px 0 !important;
    color: #c9d1d9 !important;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: #1e2130 !important;
}
[data-testid="stSidebar"] .stRadio [data-baseweb="radio"] [role="radio"] {
    background: transparent !important;
    border-color: #30363d !important;
}

/* AI Config box */
.ai-config-box {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 10px;
    padding: 1rem;
    margin-top: 1rem;
}
.ai-config-title {
    font-size: 0.82rem;
    font-weight: 700;
    color: #e6c55a !important;
    margin-bottom: 0.8rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}
.ai-status {
    font-size: 0.75rem;
    color: #3fb950 !important;
    margin-top: 0.6rem;
    font-weight: 600;
}

/* ── Main area ── */
.main .block-container { padding: 2rem 2.5rem 4rem; max-width: 1400px; }

/* Page header */
.page-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1.8rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #e5e7eb;
}
.page-header .ph-icon { font-size: 2rem; }
.page-header h1 { font-size: 1.8rem; font-weight: 800; color: #1a1a2e; margin: 0; }
.page-header p  { margin: 0.2rem 0 0; color: #6b7280; font-size: 0.92rem; }

/* Hero banner */
.caf-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
    border-radius: 20px;
    padding: 2.5rem 3rem;
    margin-bottom: 2rem;
    color: white;
    position: relative;
    overflow: hidden;
}
.caf-header::before {
    content: '☕';
    position: absolute;
    right: 2rem;
    top: 50%;
    transform: translateY(-50%);
    font-size: 6rem;
    opacity: 0.15;
}
.caf-header h1 { font-size: 2.2rem; font-weight: 800; margin: 0 0 0.5rem; }
.caf-header p  { margin: 0; opacity: 0.85; font-size: 1.05rem; }

/* Metric cards */
.metric-row { display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
.metric-card {
    flex: 1; min-width: 140px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 14px; padding: 1.2rem 1.5rem;
    color: white; text-align: center;
}
.metric-card.green  { background: linear-gradient(135deg, #11998e, #38ef7d); }
.metric-card.orange { background: linear-gradient(135deg, #f7971e, #ffd200); }
.metric-card.pink   { background: linear-gradient(135deg, #f953c6, #b91d73); }
.metric-card .val   { font-size: 2rem; font-weight: 800; }
.metric-card .lbl   { font-size: 0.78rem; opacity: 0.9; margin-top: 0.2rem; }

/* Instruction box */
.instruction-box {
    background: #0f172a;
    color: #e2e8f0;
    border-radius: 14px;
    padding: 1.5rem;
    font-family: 'Courier New', monospace;
    font-size: 0.88rem;
    line-height: 1.7;
    white-space: pre-wrap;
    border: 1px solid #1e293b;
    margin-bottom: 1rem;
}

/* Instruction list card */
.instr-card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 0.8rem;
    cursor: pointer;
    transition: box-shadow 0.2s, border-color 0.2s;
}
.instr-card:hover { box-shadow: 0 4px 16px rgba(102,126,234,0.15); border-color: #667eea; }
.instr-card.active { border-left: 4px solid #667eea; background: #f5f3ff; }

/* Timeline */
.timeline { position: relative; padding-left: 2rem; }
.timeline::before {
    content: '';
    position: absolute; left: 0.55rem; top: 0.5rem; bottom: 0.5rem;
    width: 2px;
    background: linear-gradient(to bottom, #667eea, #764ba2);
    border-radius: 2px;
}
.tl-item {
    position: relative; margin-bottom: 1.2rem;
    background: #f8f9ff; border-radius: 12px;
    padding: 1rem 1.2rem; border-left: 3px solid #667eea;
}
.tl-item::before {
    content: '';
    position: absolute; left: -1.87rem; top: 1.1rem;
    width: 12px; height: 12px;
    background: #667eea; border-radius: 50%;
    border: 2px solid white; box-shadow: 0 0 0 2px #667eea;
}
.tl-item.latest { border-left-color: #38ef7d; background: #f0fdf8; }
.tl-item.latest::before { background: #38ef7d; box-shadow: 0 0 0 2px #38ef7d; }
.tl-meta { font-size: 0.78rem; color: #6b7280; margin-top: 0.3rem; }
.tl-content { font-size: 0.88rem; color: #374151; margin-top: 0.5rem; white-space: pre-wrap; font-family: monospace; background: white; border-radius: 8px; padding: 0.6rem; max-height: 120px; overflow-y: auto; }

/* Variant cards */
.variant-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem; }
.variant-card {
    border-radius: 14px; padding: 1.2rem; color: white;
    position: relative; overflow: hidden;
}
.variant-card::after {
    content: attr(data-icon); position: absolute;
    right: 1rem; bottom: 0.5rem; font-size: 2.5rem; opacity: 0.18;
}
.vc-friendly  { background: linear-gradient(135deg, #11998e, #38ef7d); }
.vc-professional { background: linear-gradient(135deg, #1a1a2e, #0f3460); }
.vc-casual    { background: linear-gradient(135deg, #f7971e, #ffd200); color: #1a1a2e !important; }
.vc-luxury    { background: linear-gradient(135deg, #b91d73, #f953c6); }
.vc-custom    { background: linear-gradient(135deg, #667eea, #764ba2); }
.vc-label { font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; opacity: 0.8; margin-bottom: 0.4rem; }
.vc-content { font-size: 0.85rem; line-height: 1.5; white-space: pre-wrap; }
.vc-meta { font-size: 0.72rem; opacity: 0.7; margin-top: 0.6rem; }

/* Rating */
.star-rating { font-size: 1.5rem; color: #fbbf24; letter-spacing: 2px; }

/* Buttons */
div.stButton > button {
    border-radius: 10px; font-weight: 600; transition: all 0.2s;
}
div.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
div[data-testid="stAlert"] { border-radius: 10px; }

/* Step divider */
.step-divider {
    display: flex; align-items: center; gap: 1rem;
    margin: 2rem 0 1.2rem; color: #9ca3af;
    font-size: 0.82rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 1px;
}
.step-divider::before, .step-divider::after {
    content: ''; flex: 1; height: 1px; background: #e5e7eb;
}

/* Section card */
.section-card {
    background: white; border-radius: 16px; padding: 1.8rem;
    margin-bottom: 1.5rem; box-shadow: 0 4px 24px rgba(0,0,0,0.06);
    border: 1px solid #f0f0f0;
}
</style>
""", unsafe_allow_html=True)


# ─── Helpers ──────────────────────────────────────────────────────────────────
TONE_STYLES = {
    "Friendly":     ("vc-friendly",      "😊", "Warm, approachable & inviting"),
    "Professional": ("vc-professional",  "💼", "Formal, credible & polished"),
    "Casual":       ("vc-casual",        "😎", "Relaxed, fun & conversational"),
    "Luxury":       ("vc-luxury",        "✨", "Exclusive, premium & elegant"),
}

TONE_REWRITES = {
    "Friendly": (
        "Hey there! 🌟 Welcome to {business_name}! We're all about {objective}, "
        "crafted just for folks like {target_audience} right here in {location}. "
        "Our specialty? {speciality} — made with love. Try our famous {menu_items} "
        "starting at {price_range} prices. Find us on {promotion_channel}! "
        "🎉 Special deal: {offers}"
    ),
    "Professional": (
        "{business_name} is a premier destination for {target_audience} in {location}. "
        "Our objective is {objective}. We specialize in {speciality}, "
        "offering {menu_items} within a {price_range} price range. "
        "Connect with us via {promotion_channel}. Current promotion: {offers}."
    ),
    "Casual": (
        "So {business_name} is basically the coolest spot in {location} for {target_audience}. "
        "We're all about {objective} and our {speciality} is next level. "
        "Grab some {menu_items} — totally {price_range} friendly! "
        "Follow us on {promotion_channel}. Oh and btw: {offers} 🙌"
    ),
    "Luxury": (
        "Welcome to {business_name} — where discerning {target_audience} in {location} "
        "experience the finest {speciality}. Our singular objective: {objective}. "
        "Indulge in our curated selection of {menu_items}, reflecting our {price_range} "
        "excellence. Discover us on {promotion_channel}. Exclusive offer: {offers}."
    ),
}

def generate_tone_variant(context: dict, tone: str) -> str:
    template = TONE_REWRITES.get(tone, TONE_REWRITES["Friendly"])
    try:
        return template.format(**{k: (v if v else "—") for k, v in context.items()})
    except KeyError:
        return template

def stars(n: int) -> str:
    return "★" * n + "☆" * (5 - n)

def fmt_dt(ts: str) -> str:
    try:
        dt = datetime.strptime(str(ts), "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%b %d, %Y · %H:%M")
    except Exception:
        return str(ts)

def render_text_diff(text1: str, text2: str) -> str:
    diff_lines = []
    for line in difflib.ndiff((text1 or "").splitlines(), (text2 or "").splitlines()):
        if line.startswith('+ '):
            diff_lines.append(f"<div style='background:#dcfce7; color:#166534; padding:0.1rem 0.5rem;'>+ {line[2:]}</div>")
        elif line.startswith('- '):
            diff_lines.append(f"<div style='background:#fee2e2; color:#991b1b; padding:0.1rem 0.5rem;'>- {line[2:]}</div>")
        elif line.startswith('? '):
            pass
        else:
            diff_lines.append(f"<div style='padding:0.1rem 0.5rem; color:#475569;'>  {line[2:]}</div>")
    return f"<div style='font-family:monospace; background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:0.5rem; max-height:300px; overflow-y:auto; line-height:1.4;'>{''.join(diff_lines)}</div>"

def render_context_diff(answers1: dict, answers2: dict, questions: list) -> str:
    diff_rows = []
    q_dict = {q["question_id"]: q["label"] for q in questions}
    all_keys = set((answers1 or {}).keys()).union(set((answers2 or {}).keys()))
    for key in sorted(all_keys):
        val1 = (answers1 or {}).get(key, "")
        val2 = (answers2 or {}).get(key, "")
        if isinstance(val1, list): val1 = ", ".join(val1)
        if isinstance(val2, list): val2 = ", ".join(val2)
        if val1 != val2:
            label = q_dict.get(key, key)
            diff_rows.append(f"""
            <tr style='border-bottom: 1px solid #f1f5f9;'>
                <td style='padding: 0.5rem; font-weight: 500; font-size: 0.85rem; color:#1e293b;'>{label}</td>
                <td style='padding: 0.5rem; color: #991b1b; background: #fee2e2; font-size: 0.82rem;'>{val1}</td>
                <td style='padding: 0.5rem; color: #166534; background: #dcfce7; font-size: 0.82rem;'>{val2}</td>
            </tr>
            """)
    if diff_rows:
        return f"""
        <table style='width:100%; border-collapse:collapse; text-align:left; border: 1px solid #e2e8f0; margin-bottom: 1rem;'>
            <thead>
                <tr style='background:#f8fafc; border-bottom:2px solid #e2e8f0;'>
                    <th style='padding: 0.5rem; font-size: 0.85rem; font-weight:600; color:#475569;'>Parameter</th>
                    <th style='padding: 0.5rem; font-size: 0.85rem; font-weight:600; color:#475569;'>Base Value</th>
                    <th style='padding: 0.5rem; font-size: 0.85rem; font-weight:600; color:#475569;'>Comparison Value</th>
                </tr>
            </thead>
            <tbody>
                {''.join(diff_rows)}
            </tbody>
        </table>
        """
    else:
        return "<p style='color:#64748b; font-size: 0.85rem; font-style:italic;'>No context parameter changes detected.</p>"


# ─── State & DB ───────────────────────────────────────────────────────────────
conn = get_connection()
questions = load_questions()

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ☕ CAF Studio")
    st.markdown("---")

    # Navigate label
    st.markdown('<div class="nav-label">Navigate</div>', unsafe_allow_html=True)

    page = st.radio(
        "Navigate",
        [
            "📋  Create Instruction",
            "📁  My Instructions",
            "🎨  Variants",
            "📋  Version History",
            "🔗  Iteration Control",
            "🕐  History",
            "💬  Feedback",
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")

    # ── AI Configuration ──
    st.markdown('<div class="nav-label">⚙ AI Configuration</div>', unsafe_allow_html=True)
    with st.container():
        default_key = os.environ.get("GROQ_API_KEY", "")
        api_key_input = st.text_input(
            "Groq API Key",
            value=st.session_state.get("groq_api_key", default_key),
            type="password",
            placeholder="gsk_...",
            key="sidebar_api_key",
            help="Your Groq API key from console.groq.com"
        )
        if api_key_input:
            st.session_state["groq_api_key"] = api_key_input

        model_choice = st.selectbox(
            "Groq Model",
            ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma2-9b-it"],
            index=0,
            key="sidebar_model",
            help="Select the Groq model for AI generation"
        )
        st.session_state["groq_model"] = model_choice

        if st.session_state.get("groq_api_key"):
            st.markdown('<div class="ai-status">✅ AI Enabled (Groq)</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="font-size:0.75rem; color:#6b7280 !important; margin-top:0.4rem;">⬜ Template mode (no API key)</div>', unsafe_allow_html=True)

    st.markdown("---")

    if "instruction_id" in st.session_state:
        iid = st.session_state["instruction_id"]
        versions = get_version_history(conn, iid)
        variants = get_variants(conn, iid)
        st.markdown(f"**Active** `Instruction #{iid}`")
        st.markdown(f"🔖 **{len(versions)}** version{'s' if len(versions) != 1 else ''}")
        st.markdown(f"🎨 **{len(variants)}** variant{'s' if len(variants) != 1 else ''}")
        st.markdown("---")

    st.markdown("<small style='opacity:0.4'>Context Assembly Framework v2.0</small>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: Create Instruction
# ═══════════════════════════════════════════════════════════════════════════════
if page == "📋  Create Instruction":

    st.markdown("""
    <div class="caf-header">
      <h1>📋 Create a New Instruction</h1>
      <p>Answer the questions below. Every field marked ✱ is required.</p>
    </div>
    """, unsafe_allow_html=True)

    if "instruction_id" in st.session_state:
        iid = st.session_state["instruction_id"]
        versions = get_version_history(conn, iid)
        variants = get_variants(conn, iid)
        st.markdown(f"""
        <div class="metric-row">
            <div class="metric-card">
                <div class="val">#{iid}</div>
                <div class="lbl">Instruction ID</div>
            </div>
            <div class="metric-card green">
                <div class="val">{len(versions)}</div>
                <div class="lbl">Versions</div>
            </div>
            <div class="metric-card orange">
                <div class="val">{len(variants)}</div>
                <div class="lbl">Variants</div>
            </div>
            <div class="metric-card pink">
                <div class="val">✓</div>
                <div class="lbl">Saved</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Step 1: Input ──
    st.markdown('<div class="step-divider">Step 1 — Structured Input</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    answers = {}
    saved_answers = st.session_state.get("answers", {})
    temp_answers = {}
    for q in questions:
        key = f"q_{q['question_id']}"
        if key in st.session_state:
            temp_answers[q['question_id']] = st.session_state[key]
    current_state_answers = {**saved_answers, **temp_answers}
    visible_qs = get_visible_questions(questions, current_state_answers)

    for i, q in enumerate(visible_qs):
        target_col = col1 if i % 2 == 0 else col2
        with target_col:
            default_val = current_state_answers.get(q["question_id"])
            if q["type"] == "text":
                answers[q["question_id"]] = st.text_input(
                    q["label"],
                    value=default_val if default_val is not None else "",
                    key=f"q_{q['question_id']}"
                )
            elif q["type"] == "select":
                options = q["options"]
                index = options.index(default_val) if default_val in options else 0
                answers[q["question_id"]] = st.selectbox(
                    q["label"], options, index=index, key=f"q_{q['question_id']}"
                )
            elif q["type"] == "multi-select":
                default_multi = default_val if default_val is not None else []
                answers[q["question_id"]] = st.multiselect(
                    q["label"], q["options"], default=default_multi, key=f"q_{q['question_id']}"
                )

    if st.button("⚡ Build Context", use_container_width=True):
        st.session_state["context"] = build_context(answers)
        st.session_state["answers"] = answers
        st.success("Context built successfully!")
        st.rerun()

    # ── Step 2: Assembled Instruction ──
    if "context" in st.session_state:
        st.markdown('<div class="step-divider">Step 2 — Assembled Instruction</div>', unsafe_allow_html=True)
        ctx = st.session_state["context"]
        instruction = assemble_instruction(ctx)
        st.session_state["current_instruction"] = instruction

        if "instruction_id" in st.session_state:
            st.markdown(f"""
            <div style="margin-bottom:0.6rem;">
                <span style="font-size:0.8rem; color:#6b7280;">Instruction ID: </span>
                <span style="font-size:0.8rem; color:#667eea; font-family:monospace;">
                    {st.session_state['instruction_id']}
                </span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("**You can manually edit the instruction below:**")
        edited_instruction = st.text_area(
            "Instruction",
            value=instruction,
            height=320,
            key="edit_instruction_area",
            label_visibility="collapsed"
        )

        col_save, col_fresh = st.columns(2)
        with col_save:
            if st.button("💾 Save Manual Edit", use_container_width=True):
                if "instruction_id" in st.session_state:
                    iid = st.session_state["instruction_id"]
                    cid = save_context(conn, st.session_state.get("answers", {}))
                    last_ver_row = conn.execute("SELECT MAX(version_number) FROM versions WHERE instruction_id=?", (iid,)).fetchone()
                    last_ver = last_ver_row[0] or 1
                    new_ver = create_version(conn, iid, edited_instruction, "Manual edit from builder", context_id=cid)
                    conn.execute("UPDATE instructions SET content = ? WHERE id = ?", (edited_instruction, iid))
                    conn.commit()
                    create_iteration_link(conn, iid, iid, last_ver, new_ver, "manual_edit", "Manual edit from builder.")
                    st.success(f"✅ Saved as Version {new_ver}!")
                    st.rerun()
                else:
                    cid = save_context(conn, st.session_state.get("answers", {}))
                    cur = conn.execute("INSERT INTO instructions (context_id, content) VALUES (?,?)", (cid, edited_instruction))
                    conn.commit()
                    iid = cur.lastrowid
                    st.session_state["instruction_id"] = iid
                    create_version(conn, iid, edited_instruction, "Initial version", context_id=cid)
                    create_iteration_link(conn, iid, iid, 0, 1, "initial", "Initial instruction created.")
                    st.success(f"✅ Saved as Instruction #{iid}!")
                    st.rerun()

        with col_fresh:
            if st.button("🔄 Start Fresh", use_container_width=True):
                for key in ["context", "answers", "instruction_id", "current_instruction"]:
                    st.session_state.pop(key, None)
                st.rerun()

        if "instruction_id" not in st.session_state:
            if st.button("💾 Save as New Instruction", use_container_width=True):
                cid = save_context(conn, st.session_state.get("answers", {}))
                cur = conn.execute("INSERT INTO instructions (context_id, content) VALUES (?,?)", (cid, instruction))
                conn.commit()
                iid = cur.lastrowid
                st.session_state["instruction_id"] = iid
                create_version(conn, iid, instruction, "Initial version", context_id=cid)
                create_iteration_link(conn, iid, iid, 0, 1, "initial", "Initial instruction created.")
                st.success(f"✅ Saved as Instruction #{iid} with Version 1!")
                st.rerun()
        else:
            iid = st.session_state["instruction_id"]
            if st.button("📌 Save as New Version", use_container_width=True):
                cid = save_context(conn, st.session_state.get("answers", {}))
                cur_max = conn.execute("SELECT MAX(version_number) FROM versions WHERE instruction_id=?", (iid,))
                last_ver = cur_max.fetchone()[0] or 1
                new_ver = create_version(conn, iid, instruction, "Auto-saved from builder", context_id=cid)
                conn.execute("UPDATE instructions SET context_id = ?, content = ? WHERE id = ?", (cid, instruction, iid))
                conn.commit()
                create_iteration_link(conn, iid, iid, last_ver, new_ver, "regenerate", "Regenerated instruction by modifying context parameters.")
                st.success(f"✅ New version v{new_ver} created!")
                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: My Instructions
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📁  My Instructions":
    import hashlib

    st.markdown("""
    <div class="page-header">
        <div class="ph-icon">📁</div>
        <div>
            <h1>My Instructions</h1>
            <p>All saved instruction sets — click to load one</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    rows = conn.execute("SELECT id, content, created_at FROM instructions ORDER BY id DESC").fetchall()
    if not rows:
        st.info("💡 No instructions saved yet. Go to **Create Instruction** to build your first one.")
    else:
        active_iid = st.session_state.get("instruction_id")
        st.markdown(f"**{len(rows)} instruction{'s' if len(rows) != 1 else ''} found**")
        st.markdown("---")
        for row in rows:
            iid_r = row["id"]
            content = row["content"] or ""
            raw_created = row["created_at"]
            created_str = str(raw_created).split(".")[0] if raw_created else "—"
            
            # Generate stable hash to display
            h = hashlib.md5(f"caf_instr_{iid_r}".encode()).hexdigest()
            hash_display = f"{h[:8]}-{h[8:11]}..."
            
            is_active = (iid_r == active_iid)
            header_title = f"📄 {hash_display} | {created_str}"
            if is_active:
                header_title += "  (Active)"

            with st.expander(header_title, expanded=is_active):
                st.code(content, language="text")
                
                col_load, col_del, _ = st.columns([1, 1, 3])
                with col_load:
                    if st.button(f"📂 Load #{iid_r}", key=f"load_{iid_r}", use_container_width=True):
                        ver_rows = get_version_history(conn, iid_r)
                        if ver_rows:
                            latest = ver_rows[-1]
                            ctx_answers = get_context_answers(conn, latest["context_id"])
                            st.session_state["answers"] = ctx_answers
                            st.session_state["context"] = build_context(ctx_answers)
                            st.session_state["current_instruction"] = latest["content"]
                        st.session_state["instruction_id"] = iid_r
                        st.success(f"Loaded Instruction #{iid_r}")
                        st.rerun()
                with col_del:
                    if st.button(f"🗑 Delete #{iid_r}", key=f"del_{iid_r}", use_container_width=True):
                        conn.execute("DELETE FROM versions WHERE instruction_id=?", (iid_r,))
                        conn.execute("DELETE FROM variants WHERE parent_instruction_id=?", (iid_r,))
                        conn.execute("DELETE FROM feedback WHERE instruction_id=?", (iid_r,))
                        conn.execute("DELETE FROM iteration_links WHERE parent_instruction_id=?", (iid_r,))
                        conn.execute("DELETE FROM instructions WHERE id=?", (iid_r,))
                        conn.commit()
                        if st.session_state.get("instruction_id") == iid_r:
                            for k in ["instruction_id", "context", "answers", "current_instruction"]:
                                st.session_state.pop(k, None)
                        st.success(f"Deleted Instruction #{iid_r}")
                        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: Variants
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🎨  Variants":
    # ----- Automatic tone variant generation disabled per user request -----
    # The UI for generating AI tone-based variants has been removed.
    # Users can still create and save custom variants manually.
    st.markdown("""
    <div class="page-header">
        <div class="ph-icon">🎨</div>
        <div>
            <h1>Variants</h1>
            <p>Manage custom instruction variants</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if "instruction_id" not in st.session_state:
        st.info("💡 Build and save an instruction first to create variants.")
    else:
        iid = st.session_state["instruction_id"]
        ctx = st.session_state.get("context", {})
        variants = get_variants(conn, iid)

        st.markdown(f"""
        <div class="metric-row">
            <div class="metric-card orange">
                <div class="val">{len(variants)}</div>
                <div class="lbl">Total Variants</div>
            </div>
            <div class="metric-card green">
                <div class="val">4</div>
                <div class="lbl">Tone Templates</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 🚀 Generate Tone Variants")
        tone_cols = st.columns(4)
        for idx, (tone, (css_cls, icon, desc)) in enumerate(TONE_STYLES.items()):
            with tone_cols[idx]:
                st.markdown(f"""
                <div class="variant-card {css_cls}" data-icon="{icon}" style="margin-bottom:0.5rem;">
                    <div class="vc-label">{icon} {tone}</div>
                    <div class="vc-meta">{desc}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Generate {tone}", key=f"gen_{tone}", use_container_width=True):
                    if not ctx:
                        st.warning("Build a context first!")
                    else:
                        content = generate_tone_variant(ctx, tone)
                        create_variant(conn, iid, f"[{tone}]\n{content}")
                        st.success(f"✅ {tone} variant saved!")
                        st.rerun()

        st.markdown("---")
        st.markdown("### ✏️ Write a Custom Variant")
        custom_content = st.text_area(
            "Custom variant content",
            placeholder="Write your own version of the instruction here…",
            height=150, key="custom_variant"
        )
        if st.button("💾 Save Custom Variant", use_container_width=True):
            if custom_content.strip():
                create_variant(conn, iid, f"[Custom]\n{custom_content}")
                st.success("Custom variant saved!")
                st.rerun()
            else:
                st.warning("Please enter content.")

        if variants:
            st.markdown("---")
            st.markdown(f"### 📦 Saved Variants ({len(variants)})")
            TONE_CLASSES = {
                "friendly": "vc-friendly", "professional": "vc-professional",
                "casual": "vc-casual", "luxury": "vc-luxury", "custom": "vc-custom",
            }
            st.markdown('<div class="variant-grid">', unsafe_allow_html=True)
            for var in variants:
                content = var["content"] or ""
                first_line = content.split("\n")[0].strip("[]").lower()
                css_cls = TONE_CLASSES.get(first_line, "vc-custom")
                icon = TONE_STYLES.get(first_line.capitalize(), ("", "🎨", ""))[1] if first_line.capitalize() in TONE_STYLES else "🎨"
                display_label = first_line.capitalize() if first_line in TONE_CLASSES else "Custom"
                body = "\n".join(content.split("\n")[1:]).strip() if "\n" in content else content
                st.markdown(f"""
                <div class="variant-card {css_cls}" data-icon="{icon}">
                    <div class="vc-label">{icon} {display_label} · Variant #{var['id']}</div>
                    <div class="vc-content">{body}</div>
                    <div class="vc-meta">🕐 {fmt_dt(var['created_at'])}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No variants yet — use the buttons above to generate your first one!")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: Version History
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📋  Version History":
    st.markdown("""
    <div class="page-header">
        <div class="ph-icon">📋</div>
        <div>
            <h1>Version History</h1>
            <p>View, inspect, rollback or compare every saved version</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if "instruction_id" not in st.session_state:
        st.info("💡 Build and save an instruction first to see version history.")
    else:
        iid = st.session_state["instruction_id"]
        versions = get_version_history(conn, iid)

        if not versions:
            st.warning("No versions found. Save an instruction to create the first version.")
        else:
            st.markdown(f"""
            <div class="metric-row">
                <div class="metric-card">
                    <div class="val">{len(versions)}</div>
                    <div class="lbl">Total Versions</div>
                </div>
                <div class="metric-card green">
                    <div class="val">v{versions[-1]['version_number']}</div>
                    <div class="lbl">Latest Active</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            tab_timeline, tab_compare = st.tabs(["📋 Timeline", "🔍 Compare Versions"])

            with tab_timeline:
                for ev in reversed(versions):
                    is_latest = (ev["version_number"] == versions[-1]["version_number"])
                    border_color = "#38ef7d" if is_latest else "#667eea"
                    bg_color = "#f0fdf8" if is_latest else "#f8f9ff"
                    st.markdown(f"""
                    <div style="border-left: 4px solid {border_color}; background: {bg_color}; padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem; box-shadow: 0 2px 8px rgba(0,0,0,0.02);">
                        <span style="font-size: 0.75rem; font-weight: bold; background: {border_color}; color: white; padding: 0.15rem 0.5rem; border-radius: 12px;">v{ev['version_number']}</span>
                        {"<span style='font-size: 0.75rem; font-weight: bold; background: #dcfce7; color: #166534; padding: 0.15rem 0.5rem; border-radius: 12px; margin-left: 0.4rem;'>ACTIVE</span>" if is_latest else ""}
                        <span style="float: right; font-size: 0.75rem; color: #9ca3af;">🕐 {fmt_dt(ev['created_at'])}</span>
                        <div style="margin-top: 0.5rem; font-size: 0.95rem; font-weight: 600; color: #1e293b;">{ev['change_description']}</div>
                        <div style="margin-top: 0.5rem; font-family: monospace; background: white; border: 1px solid #e2e8f0; border-radius: 6px; padding: 0.6rem; font-size: 0.85rem; max-height: 120px; overflow-y: auto; color: #334155; white-space: pre-wrap;">{ev['content']}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    col_inspect, col_rollback, _ = st.columns([1, 1.2, 2.8])
                    with col_inspect:
                        if st.button("🔍 Inspect", key=f"insp_{ev['version_number']}", use_container_width=True):
                            st.session_state[f"show_inspect_{ev['version_number']}"] = True
                    with col_rollback:
                        if not is_latest:
                            if st.button(f"⏪ Rollback to v{ev['version_number']}", key=f"roll_{ev['version_number']}", use_container_width=True):
                                target_cid = ev["context_id"]
                                answers_snapshot = get_context_answers(conn, target_cid)
                                st.session_state["answers"] = answers_snapshot
                                st.session_state["context"] = build_context(answers_snapshot)
                                st.session_state["current_instruction"] = ev["content"]
                                cur_max = conn.execute("SELECT MAX(version_number) FROM versions WHERE instruction_id=?", (iid,))
                                last_ver = cur_max.fetchone()[0] or 1
                                new_ver = create_version(conn, iid, ev["content"], f"Rollback to Version {ev['version_number']}", context_id=target_cid)
                                conn.execute("UPDATE instructions SET context_id = ?, content = ? WHERE id = ?", (target_cid, ev["content"], iid))
                                conn.commit()
                                create_iteration_link(conn, iid, iid, last_ver, new_ver, "rollback", f"Rolled back to Version {ev['version_number']}.")
                                st.success(f"Rolled back! New Version v{new_ver} created.")
                                st.rerun()

                    if st.session_state.get(f"show_inspect_{ev['version_number']}", False):
                        answers_snapshot = get_context_answers(conn, ev["context_id"])
                        st.markdown(f"#### 📋 Context Snapshot for v{ev['version_number']}")
                        if answers_snapshot:
                            ic1, ic2 = st.columns(2)
                            for idx, q in enumerate(questions):
                                ic = ic1 if idx % 2 == 0 else ic2
                                qid = q["question_id"]
                                val = answers_snapshot.get(qid, "")
                                if isinstance(val, list): val = ", ".join(val)
                                if val: ic.write(f"**{q['label']}**: {val}")
                        else:
                            st.write("No context parameters saved for this version.")
                        if st.button("Close", key=f"close_{ev['version_number']}"):
                            st.session_state[f"show_inspect_{ev['version_number']}"] = False
                            st.rerun()
                    st.markdown("<br>", unsafe_allow_html=True)

            with tab_compare:
                st.markdown("### Compare Two Versions")
                v_numbers = [v["version_number"] for v in versions]
                col_b, col_c = st.columns(2)
                with col_b:
                    base_v = st.selectbox("Base Version", v_numbers, index=0)
                with col_c:
                    comp_v = st.selectbox("Comparison Version", v_numbers, index=len(v_numbers)-1)

                if base_v == comp_v:
                    st.info("Choose two different versions to see changes.")
                else:
                    base_obj = next(v for v in versions if v["version_number"] == base_v)
                    comp_obj = next(v for v in versions if v["version_number"] == comp_v)
                    st.markdown(f"#### 🔍 Parameter Diff (v{base_v} vs v{comp_v})")
                    st.markdown(render_context_diff(
                        get_context_answers(conn, base_obj["context_id"]),
                        get_context_answers(conn, comp_obj["context_id"]),
                        questions
                    ), unsafe_allow_html=True)
                    st.markdown(f"#### 📝 Content Diff (v{base_v} vs v{comp_v})")
                    st.markdown(render_text_diff(base_obj["content"], comp_obj["content"]), unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: Iteration Control
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🔗  Iteration Control":
    st.markdown("""
    <div class="page-header">
        <div class="ph-icon">🔗</div>
        <div>
            <h1>Iteration Control</h1>
            <p>Manually edit and create new versions in the iteration chain</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if "instruction_id" not in st.session_state:
        st.info("💡 Build and save an instruction first to use iteration control.")
    else:
        iid = st.session_state["instruction_id"]
        versions = get_version_history(conn, iid)

        if not versions:
            st.warning("No versions found.")
        else:
            latest_content = versions[-1]["content"]
            st.markdown(f"""
            <div class="metric-row">
                <div class="metric-card">
                    <div class="val">{len(versions)}</div>
                    <div class="lbl">Total Versions</div>
                </div>
                <div class="metric-card green">
                    <div class="val">v{versions[-1]['version_number']}</div>
                    <div class="lbl">Current Version</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("### ✏️ Write a Custom Version (Manual Edit)")
            st.markdown("Manually edit the instruction content and save it as a new version.")

            new_desc = st.text_input(
                "What changed in this update?",
                placeholder="e.g. Added custom holiday menu pricing",
                key="man_desc"
            )
            new_content = st.text_area(
                "Instruction Content",
                value=latest_content,
                height=280,
                key="man_content"
            )

            if st.button("💾 Save Manual Update", use_container_width=True, key="btn_save_manual"):
                if new_content.strip():
                    latest_cid = versions[-1]["context_id"]
                    last_ver = versions[-1]["version_number"]
                    new_ver = create_version(conn, iid, new_content, new_desc or "Manual update", context_id=latest_cid)
                    conn.execute("UPDATE instructions SET content = ? WHERE id = ?", (new_content, iid))
                    conn.commit()
                    create_iteration_link(conn, iid, iid, last_ver, new_ver, "manual_edit", f"Manual edit: {new_desc or 'No details'}")
                    st.success(f"✅ Saved as Version {new_ver}!")
                    st.rerun()
                else:
                    st.warning("Content cannot be empty.")

            st.markdown("---")
            st.markdown("### 🔁 Iteration Chain")
            if len(versions) >= 2:
                for i in range(len(versions) - 1, 0, -1):
                    v_new = versions[i]
                    v_old = versions[i - 1]
                    st.markdown(f"""
                    <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:0.8rem 1rem; margin-bottom:0.6rem;">
                        <span style="font-size:0.82rem; font-weight:700; color:#667eea;">v{v_old['version_number']}</span>
                        <span style="margin:0 0.5rem; color:#9ca3af;">→</span>
                        <span style="font-size:0.82rem; font-weight:700; color:#11998e;">v{v_new['version_number']}</span>
                        <span style="margin-left:0.5rem; font-size:0.78rem; color:#6b7280;">{v_new['change_description']}</span>
                        <span style="float:right; font-size:0.72rem; color:#9ca3af;">🕐 {fmt_dt(v_new['created_at'])}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Only one version exists. Create more versions to see the iteration chain.")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: History
# ═══════════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: History
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🕐  History":
    st.markdown("""
    <div class="page-header">
        <div class="ph-icon">📜</div>
        <div>
            <h1>Session History & Audit Trail</h1>
            <p>Trace the complete iteration chain, parent-child edit histories, model prompts/responses, and variant configurations for your coffee shop projects.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    rows = conn.execute("SELECT id, context_id, created_at FROM instructions ORDER BY id DESC").fetchall()
    if not rows:
        st.info("💡 No instructions saved yet. Go to **Create Instruction** to build your first one.")
    else:
        # Build dropdown options
        options = []
        id_map = {}
        for r in rows:
            iid = r["id"]
            ctx_answers = get_context_answers(conn, r["context_id"])
            bname = ctx_answers.get("business_name") or f"Instruction #{iid}"
            created_str = str(r["created_at"]).split(".")[0] if r["created_at"] else "—"
            label = f"👁 {bname} (Saved: {created_str})"
            options.append(label)
            id_map[label] = iid

        # Find currently active or default index
        active_iid = st.session_state.get("instruction_id")
        active_label = None
        for label, iid in id_map.items():
            if iid == active_iid:
                active_label = label
                break
        
        index = options.index(active_label) if active_label in options else 0

        selected_label = st.selectbox(
            "Select Coffee Shop Project Session:",
            options,
            index=index
        )
        selected_iid = id_map[selected_label]

        # If user switches session, update state and rerun
        if active_iid != selected_iid:
            st.session_state["instruction_id"] = selected_iid
            ver_rows = get_version_history(conn, selected_iid)
            if ver_rows:
                latest = ver_rows[-1]
                ctx_answers = get_context_answers(conn, latest["context_id"])
                st.session_state["answers"] = ctx_answers
                st.session_state["context"] = build_context(ctx_answers)
                st.session_state["current_instruction"] = latest["content"]
            st.rerun()

        # View configuration context details expander
        with st.expander("👁 View Base Configuration Context Details"):
            # Fetch the context id of version 1
            first_ver_row = conn.execute("SELECT context_id FROM versions WHERE instruction_id = ? AND version_number = 1", (selected_iid,)).fetchone()
            base_cid = first_ver_row[0] if first_ver_row else None
            if not base_cid:
                # fallback to context_id in instructions table
                inst_row = conn.execute("SELECT context_id FROM instructions WHERE id = ?", (selected_iid,)).fetchone()
                base_cid = inst_row[0] if inst_row else None
            
            answers_snapshot = get_context_answers(conn, base_cid)
            if answers_snapshot:
                st.markdown("##### 📋 Base Context Snapshot")
                ic1, ic2 = st.columns(2)
                for idx, q in enumerate(questions):
                    ic = ic1 if idx % 2 == 0 else ic2
                    qid = q["question_id"]
                    val = answers_snapshot.get(qid, "")
                    if isinstance(val, list): val = ", ".join(val)
                    if val:
                        ic.markdown(f"**{q['label']}**")
                        ic.markdown(f"<span style='color: #667eea;'>{val}</span>", unsafe_allow_html=True)
            else:
                st.write("No context parameters saved for this session.")

        st.markdown("---")
        st.markdown("### 🧬 Sequential Iteration Chain")

        versions = get_version_history(conn, selected_iid)
        if not versions:
            st.info("No versions found for this session.")
        else:
            for v in versions:
                created_str = str(v["created_at"]).split(".")[0] if v["created_at"] else "—"
                
                # Card Container
                st.markdown(f"""
                <div style="margin-top: 1.8rem; margin-bottom: 0.4rem; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #30363d; padding-bottom: 0.5rem;">
                    <span style="font-size: 1.2rem; font-weight: 700;">👁 Version v{v['version_number']}</span>
                    <span style="font-size: 0.85rem; color: #8b949e;">🗓️ Created: {created_str}</span>
                </div>
                """, unsafe_allow_html=True)

                # Description Line
                desc_text = v['change_description']
                if desc_text == "Initial version":
                    desc_text = "Initial assembly (⚙️ AI-Generated (Groq))"
                st.write(f"**Description:** *{desc_text}*")

                # Parent Details
                parent_info = conn.execute(
                    "SELECT parent_version, change_type FROM iteration_links WHERE child_instruction_id = ? AND child_version = ?",
                    (selected_iid, v["version_number"])
                ).fetchone()

                if parent_info:
                    st.write(f"🌿 **Parent Version:** v{parent_info['parent_version']} ({parent_info['change_type'].upper()} Transition)")
                else:
                    st.write("🌱 **Root Version (No parent)**")

                # Version Tabs
                tab_logs, tab_variants, tab_prompt = st.tabs(["⚙ Execution Logs", "🧩 Layout Variants", "📄 Prompt Text"])

                with tab_logs:
                    col_l1, col_l2 = st.columns(2)
                    with col_l1:
                        is_ai = "Auto-saved" in v['change_description'] or "Initial" in v['change_description']
                        method = "⚙️ AI-Generated (Groq)" if is_ai else "✍️ User Manual Update"
                        st.markdown(f"**Method:** `{method}`")
                        st.markdown(f"**Model:** `{st.session_state.get('groq_model', 'llama-3.3-70b-versatile')}`")
                    with col_l2:
                        st.markdown(f"**Status:** `200 OK (Success)`")
                        st.markdown(f"**Execution Type:** `Local Context Construction`")

                with tab_variants:
                    v_answers = get_context_answers(conn, v["context_id"])
                    if v_answers:
                        tone_sel = st.selectbox(
                            "Select Tone Variant Preview:",
                            ["Friendly", "Professional", "Casual", "Luxury"],
                            key=f"hist_tone_{v['version_number']}_{selected_iid}"
                        )
                        v_ctx = build_context(v_answers)
                        variant_content = generate_tone_variant(v_ctx, tone_sel)
                        st.code(variant_content, language="text")
                    else:
                        st.info("No context parameters saved for this version to generate tone variants.")

                with tab_prompt:
                    st.code(v["content"], language="text")




# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: Feedback
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "💬  Feedback":
    st.markdown("""
    <div class="page-header">
        <div class="ph-icon">💬</div>
        <div>
            <h1>Feedback</h1>
            <p>Rate and tag the current instruction version</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if "instruction_id" not in st.session_state:
        st.info("💡 Build and save an instruction first to give feedback.")
    else:
        iid = st.session_state["instruction_id"]
        versions = get_version_history(conn, iid)
        active_ver = versions[-1]["version_number"] if versions else 1
        feedbacks = get_feedback(conn, iid)

        # Submit feedback
        st.markdown(f"### ✍️ Submit Feedback for Version v{active_ver}")
        col_r, col_t = st.columns([1, 2])
        with col_r:
            rating = st.slider("Rating", 1, 5, 3, key="feedback_rating_slider")
            st.markdown(f'<div class="star-rating">{stars(rating)}</div>', unsafe_allow_html=True)
        with col_t:
            tags = st.multiselect(
                "Tags", ["unclear", "verbose", "incomplete", "great", "concise"],
                key="feedback_tags_multi"
            )

        if st.button("📨 Submit Feedback", use_container_width=True, key="btn_submit_feedback"):
            save_feedback(conn, iid, 1, rating, tags, False, version_number=active_ver, manual_edits=False)
            st.success(f"✅ Feedback recorded for Version {active_ver}!")
            st.rerun()

        # Past feedback
        if feedbacks:
            st.markdown("---")
            st.markdown(f"### 📊 Feedback History ({len(feedbacks)} entries)")

            avg_rating = round(sum(f["rating"] for f in feedbacks if f.get("rating")) / len(feedbacks), 1)
            st.markdown(f"""
            <div class="metric-row">
                <div class="metric-card">
                    <div class="val">{len(feedbacks)}</div>
                    <div class="lbl">Total Submissions</div>
                </div>
                <div class="metric-card green">
                    <div class="val">{avg_rating}</div>
                    <div class="lbl">Average Rating</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            for fb in feedbacks[:10]:
                tags_list = json.loads(fb.get("tags") or "[]")
                r = fb.get("rating", 0) or 0
                st.markdown(f"""
                <div style="background:#f8f9ff; border-radius:10px; padding:0.8rem 1rem; margin-bottom:0.5rem; border-left:3px solid #667eea;">
                    <span class="star-rating" style="font-size:1rem;">{stars(r)}</span>
                    <span style="margin-left:0.5rem; font-size:0.85rem; color:#374151;">{', '.join(tags_list) or 'no tags'}</span>
                    <span style="float:right; font-size:0.75rem; color:#9ca3af;">v{fb.get('version_number','?')} · {fmt_dt(fb.get('created_at',''))}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No feedback submitted yet.")