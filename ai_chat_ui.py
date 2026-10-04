"""
ai_chat_ui.py  -  Reusable Real-AI Chat widget for every panel
Uses Groq LLaMA-3.1 (already configured in .env)
"""
import streamlit as st
from ai import get_ai_response, full_ai_analysis
from utils import map_symptom_to_specialization
from emergency import check_emergency, get_emergency_level

CHAT_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');
.ai-header {
    background: linear-gradient(120deg, #0f62fe, #0043ce);
    color: white; border-radius: 16px; padding: 20px 24px;
    display: flex; align-items: center; gap: 14px; margin-bottom: 18px;
}
.ai-header .icon { font-size: 36px; }
.ai-header h2 { margin: 0; font-size: 22px; font-weight: 900; }
.ai-header p  { margin: 3px 0 0; font-size: 13px; opacity: 0.88; }
.msg-user {
    background: #0f62fe; color: white;
    border-radius: 18px 18px 4px 18px;
    padding: 10px 16px; margin: 6px 0 6px 20%;
    font-size: 14px; line-height: 1.5;
}
.msg-ai {
    background: #f0f4ff; color: #071a44;
    border-radius: 18px 18px 18px 4px;
    padding: 10px 16px; margin: 6px 20% 6px 0;
    font-size: 14px; line-height: 1.6;
    border-left: 3px solid #0f62fe;
}
.msg-emergency {
    background: #fff0f0; color: #b91c1c;
    border-radius: 12px; padding: 10px 16px;
    border-left: 4px solid #ef4444;
    margin: 6px 0; font-size: 14px;
}
.diag-card {
    background: white; border-radius: 16px;
    padding: 18px 22px; margin: 12px 0;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    border-top: 4px solid #0f62fe;
}
.diag-title { font-size: 18px; font-weight: 900; color: #071a44; }
.diag-row { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px; }
.diag-pill {
    background: #eef5ff; color: #0f62fe;
    border-radius: 20px; padding: 4px 12px;
    font-size: 12px; font-weight: 700;
}
.diag-pill.red   { background: #fff0f0; color: #b91c1c; }
.diag-pill.green { background: #f0fdf4; color: #15803d; }
.diag-pill.amber { background: #fffbeb; color: #92400e; }
.med-card {
    background: #f8fbff; border: 1px solid #bfdbfe;
    border-radius: 10px; padding: 10px 14px; margin: 6px 0;
    font-size: 13px;
}
</style>
"""

PANEL_CFG = {
    "admin": {
        "title": "Admin AI Assistant",
        "sub":   "Hospital analytics, patient statistics, system insights & clinical queries.",
        "icon":  "🤖",
        "chips": [
            "How many emergency cases today?",
            "Which specialization has most patients?",
            "Summarize patient trends this week",
            "What are common diseases this month?",
            "How to optimize hospital bed allocation?",
        ],
        "system": (
            "You are Aura, an advanced AI assistant for hospital administration. "
            "Help admin staff with hospital analytics, patient statistics, clinical insights, "
            "operational decisions, staff management, and healthcare policy. "
            "Answer clearly, concisely, and professionally."
        ),
    },
    "doctor": {
        "title": "Doctor AI Clinical Assistant",
        "sub":   "Clinical decision support, drug interaction checks, and diagnosis assistance.",
        "icon":  "👨‍⚕️",
        "chips": [
            "Analyze: chest pain + sweating + nausea",
            "Drug interaction: Metformin + Aspirin",
            "Differential diagnosis: high fever + rash",
            "Post-op care for appendectomy patient",
            "Dosage: Amoxicillin for 65yr diabetic",
        ],
        "system": (
            "You are Aura, an advanced AI clinical assistant for doctors at Prasad Hospitals. "
            "Provide clinical decision support: differential diagnoses, drug interaction checks, "
            "treatment protocols, dosage recommendations, and patient management advice. "
            "Always flag serious conditions. Remind that AI suggestions must be validated clinically."
        ),
    },
    "staff": {
        "title": "Staff AI Triage Assistant",
        "sub":   "Symptom triage, department routing, and patient assessment support.",
        "icon":  "🏥",
        "chips": [
            "Patient has severe chest pain — which dept?",
            "Triage: breathlessness + swollen legs",
            "Patient BP 180/110 — what to do?",
            "Child 5yr with high fever and rash",
            "Which doctor handles knee replacement?",
        ],
        "system": (
            "You are Aura, an AI triage assistant for hospital staff at Prasad Hospitals. "
            "Help staff route patients to the correct department, assess symptom severity, "
            "provide immediate first-aid guidance, and support clinical documentation."
        ),
    },
}


def _safe_int(val, default=0):
    try:
        return int(str(val).replace("%","").strip())
    except Exception:
        return default


def _render_diagnosis_card(res):
    cond   = res.get("condition", "Unknown")
    conf   = res.get("confidence_score", "-")
    risk   = res.get("risk_score",      "-")
    spec   = res.get("specialization",  "General Physician")
    fa     = res.get("first_aid",       "-")
    meds   = res.get("medications",     [])
    fu     = res.get("follow_up",       "-")
    expl   = res.get("explanation",     "")

    risk_v = _safe_int(risk)
    risk_cls = "red" if risk_v >= 60 else "amber" if risk_v >= 35 else "green"

    st.markdown(f"""
    <div class='diag-card'>
      <div class='diag-title'>🩺 {cond}</div>
      <div class='diag-row'>
        <span class='diag-pill green'>Confidence: {conf}</span>
        <span class='diag-pill {risk_cls}'>Risk: {risk}</span>
        <span class='diag-pill'>👨‍⚕️ {spec}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("🩹 First Aid Instructions", expanded=True):
        st.markdown(fa)

    if meds:
        with st.expander(f"💊 Suggested Medications ({len(meds)})", expanded=True):
            for m in meds:
                name  = m.get("name",        "-")
                dose  = m.get("dosage",      "-")
                freq  = m.get("frequency",   "-")
                dur   = m.get("duration",    "-")
                prec  = m.get("precautions", "-")
                st.markdown(f"""
                <div class='med-card'>
                  <b>{name}</b> &nbsp;<span style='color:#0369a1;'>{dose}</span><br>
                  <small>🕐 {freq} | 📅 {dur} | ⚠️ {prec}</small>
                </div>
                """, unsafe_allow_html=True)

    with st.expander("📅 Follow-up Recommendations"):
        st.markdown(fu)

    if expl:
        with st.expander("🔬 Clinical Explanation"):
            st.markdown(expl)


def render_ai_chat(panel, user=None, patient_username=None, session_key="ai_chat_history"):
    """
    panel: "admin" | "doctor" | "staff"
    """
    cfg = PANEL_CFG.get(panel, PANEL_CFG["admin"])

    st.markdown(CHAT_CSS, unsafe_allow_html=True)
    st.markdown(f"""
    <div class='ai-header'>
      <div class='icon'>{cfg["icon"]}</div>
      <div>
        <h2>{cfg["title"]}</h2>
        <p>{cfg["sub"]}</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if session_key not in st.session_state:
        st.session_state[session_key] = []
    history = st.session_state[session_key]

    # Quick-ask chip buttons
    chips = cfg["chips"]
    chip_clicked = None
    chip_cols = st.columns(len(chips))
    for i, (col, chip) in enumerate(zip(chip_cols, chips)):
        with col:
            lbl = chip[:28] + "…" if len(chip) > 28 else chip
            if st.button(lbl, key=f"{session_key}_chip_{i}", use_container_width=True):
                chip_clicked = chip

    st.markdown("---")

    # Chat history display
    for msg in history:
        if msg["role"] == "user":
            st.markdown(
                f"<div class='msg-user'>👤 {msg['content']}</div>",
                unsafe_allow_html=True
            )
        else:
            if isinstance(msg.get("data"), dict):
                st.markdown(
                    f"<div style='color:#0043ce;font-weight:700;margin-top:8px;'>"
                    f"🤖 Aura — Clinical Analysis</div>",
                    unsafe_allow_html=True
                )
                _render_diagnosis_card(msg["data"])
            else:
                st.markdown(
                    f"<div class='msg-ai'>🤖 <b>Aura:</b> {msg['content']}</div>",
                    unsafe_allow_html=True
                )

    # Input + Send + Clear
    col_in, col_btn, col_clr = st.columns([7, 1, 1])
    with col_in:
        user_msg = st.text_input(
            "Message",
            label_visibility="collapsed",
            placeholder="Type your question here…",
            key=f"{session_key}_input",
            value=chip_clicked or "",
        )
    with col_btn:
        send = st.button("Send ▶", type="primary",
                         use_container_width=True,
                         key=f"{session_key}_send")
    with col_clr:
        if st.button("🗑️", use_container_width=True,
                     key=f"{session_key}_clr",
                     help="Clear chat"):
            st.session_state[session_key] = []
            st.rerun()

    # Mode selector
    ai_mode = st.radio(
        "AI Mode",
        ["💬 Chat Answer", "🩺 Full Diagnosis Card"],
        horizontal=True,
        key=f"{session_key}_mode",
        help="Chat Answer = conversational reply  |  Full Diagnosis Card = structured medical report"
    )

    # Send logic
    query = (chip_clicked or user_msg or "").strip()
    if (send or chip_clicked) and query:
        history.append({"role": "user", "content": query})

        groq_hist = [
            {"role": m["role"], "content": m["content"]}
            for m in history[-10:]
            if isinstance(m.get("content"), str)
        ]

        with st.spinner("🤖 Aura is thinking…"):
            try:
                is_emerg = check_emergency(query)
                emerg_level = get_emergency_level(query) if is_emerg else None

                if is_emerg:
                    st.markdown(
                        f"<div class='msg-emergency'>"
                        f"🚨 <b>EMERGENCY DETECTED</b> — Severity: <b>{(emerg_level or 'HIGH').upper()}</b>"
                        f" — Escalate to medical team immediately!</div>",
                        unsafe_allow_html=True
                    )

                if ai_mode == "🩺 Full Diagnosis Card":
                    result = full_ai_analysis(query, user=patient_username or user)
                    history.append({
                        "role": "assistant",
                        "content": f"Diagnosis for: {query}",
                        "data": result
                    })
                else:
                    sys_msgs = [{"role": "system", "content": cfg["system"]}] + groq_hist[:-1]
                    reply = get_ai_response(query, user=patient_username or user, chat_history=sys_msgs)
                    history.append({"role": "assistant", "content": reply})

            except Exception as e:
                history.append({"role": "assistant", "content": f"⚠️ AI error: {e}"})

        st.session_state[session_key] = history
        st.rerun()

    # Footer
    if history:
        turns = sum(1 for m in history if m["role"] == "user")
        st.caption(f"💬 {turns} message(s) · Powered by Groq LLaMA-3.1-8B")
