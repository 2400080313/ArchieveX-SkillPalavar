"""
ArchiveX - Copilot & Explanation Interface View
Natural-language explanation interface with deterministic fallback labeled 'Rule-based Archive Assistant'.
"""
import streamlit as st
import pandas as pd
from core.copilot import ArchiveCopilot

def render_copilot_interface(data: dict):
    copilot = ArchiveCopilot()
    mode_label = copilot.engine_mode

    # Header with deterministic badge
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.subheader("💬 ArchiveX Copilot")
        st.caption("Natural-language explanation engine for S3 lifecycle decisions, cost trade-offs, and compliance rules.")
    with col_h2:
        if copilot.is_llm_active():
            st.markdown('<span class="archivex-badge-live">⚡ LLM Augmented</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="archivex-badge-demo" title="Deterministic Rules Engine Active">🛡️ Rule-based Archive Assistant</span>', unsafe_allow_html=True)

    # Initialize chat history in session_state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {
                "role": "assistant",
                "content": f"Hello! I am the **{mode_label}**. I can explain any archive recommendation, evaluate retrieval fee trade-offs, or clarify S3 storage classes. Try one of the suggested prompts below or ask a question!"
            }
        ]

    # Quick question prompt buttons
    st.markdown("**Suggested Quick Prompts:**")
    q_col1, q_col2, q_col3 = st.columns(3)
    preset_query = None

    with q_col1:
        if st.button("Why should I archive this backup?", use_container_width=True):
            preset_query = "Why should I archive this backup?"
        if st.button("Why not move small files (<128KB) to Glacier?", use_container_width=True):
            preset_query = "Why not move small files (<128KB) to Glacier?"

    with q_col2:
        if st.button("Why was Intelligent-Tiering recommended?", use_container_width=True):
            preset_query = "Why was Intelligent-Tiering recommended?"
        if st.button("What are the retrieval cost risks?", use_container_width=True):
            preset_query = "What are the retrieval cost risks?"

    with q_col3:
        if st.button("Compare Flexible vs Deep Archive", use_container_width=True):
            preset_query = "Compare Glacier Flexible vs Glacier Deep Archive"
        if st.button("Explain the ArchiveX Scoring Algorithm", use_container_width=True):
            preset_query = "How does ArchiveX calculate the score?"

    # Context selection (allows selecting an object to contextualize query)
    df: pd.DataFrame = data["dataframe"]
    selected_context = None
    if not df.empty:
        with st.expander("🎯 Select Context Object (Optional)", expanded=False):
            ctx_key = st.selectbox("Attach Object Context to Chat:", options=df["Key"].head(50).tolist())
            ctx_row = df[df["Key"] == ctx_key].iloc[0]
            selected_context = ctx_row.to_dict()
            st.caption(f"Context active: {ctx_key} ({ctx_row['AgeDays']} days old, {ctx_row['StorageClass']}, score {ctx_row.get('ArchiveScore', 0):.0f})")

    st.markdown("---")

    # Render Chat History
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"""
            <div class="chat-user-bubble">
                <strong>You:</strong><br>{msg['content']}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-bot-bubble">
                <strong>🤖 {mode_label}:</strong><br>{msg['content']}
            </div>
            """, unsafe_allow_html=True)

    # Chat Input
    user_input = st.chat_input("Ask a question about S3 archiving, costs, or lifecycle strategies...")
    active_prompt = preset_query or user_input

    if active_prompt:
        # Add user message
        st.session_state.chat_history.append({"role": "user", "content": active_prompt})
        
        # Generate response
        response = copilot.answer_query(active_prompt, context=selected_context)
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        st.rerun()

    # Clear chat
    if len(st.session_state.chat_history) > 1:
        if st.button("Clear Conversation History", type="secondary"):
            st.session_state.chat_history = [st.session_state.chat_history[0]]
            st.rerun()
