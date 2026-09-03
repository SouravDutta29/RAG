import streamlit as st
import sys
from pathlib import Path

# Add root directory to sys.path so modules can be imported
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

from retriever.reranker import Reranker
from generator.guardrail import PromptGuard
from generator.prompt_builder import PromptBuilder
from generator.llm_engine import LLMEngine
from generator.verifier import FactVerifier
from generator.citation_injector import CitationInjector
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Groww FAQ Assistant",
    page_icon="https://assets-netstorage.groww.in/web-assets/nbg_mobile/prod/_next/static/media/section-intro.95ecaf7c.svg",
    layout="centered"
)

# Premium CSS Styling
st.markdown("""
<style>
    /* Headers */
    h1, h2, h3 {
        font-family: 'Inter', 'Roboto', sans-serif;
        font-weight: 600;
        letter-spacing: -0.02em;
    }
    
    /* Global text readability */
    p, li {
        font-family: 'Inter', 'Segoe UI', sans-serif;
        line-height: 1.6;
        font-size: 1.05rem;
    }

    /* Chat bubbles styling */
    [data-testid="stChatMessage"] {
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    /* User chat bubble */
    [data-testid="stChatMessage-user"] {
        background-color: rgba(0, 208, 156, 0.1) !important;
        border: 1px solid rgba(0, 208, 156, 0.3) !important;
    }
    
    /* Assistant chat bubble */
    [data-testid="stChatMessage-assistant"] {
        background-color: rgba(128, 128, 128, 0.05) !important;
        border: 1px solid rgba(128, 128, 128, 0.15) !important;
    }
    
    /* Pills */
    div[data-testid="stButton"] button {
        border-radius: 24px !important;
        padding: 8px 12px !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        min-height: 60px !important;
        white-space: nowrap !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
        border: 1px solid #00d09c !important;
        color: #00d09c !important;
    }
    div[data-testid="stButton"] button p {
        font-size: 0.82rem !important;
        color: inherit !important;
    }
    div[data-testid="stButton"] button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
        background-color: #00d09c !important;
        color: white !important;
        border-color: #00d09c !important;
    }
</style>
""", unsafe_allow_html=True)



import base64

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

logo_path = Path(__file__).resolve().parent / "groww_logo.png"
img_b64 = get_base64_image(logo_path)
st.markdown(
    f"""
    <div style='display: flex; align-items: center; margin-bottom: 20px;'>
        <img src='data:image/png;base64,{img_b64}' style='width: 75px; height: 75px; margin-right: 18px; border-radius: 50%; object-fit: contain;'>
        <div style='display: flex; flex-direction: column; justify-content: center;'>
            <h1 style='margin: 0; padding: 0; line-height: 1.2;'>Groww FAQ Assistant</h1>
            <p style='margin: 0; padding: 0; font-size: 0.95rem; opacity: 0.7;'>Get your mutual fund related queries</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


@st.cache_resource(show_spinner="Loading AI Models into Memory (this might take a moment)...")
def load_rag_components():
    return {
        "reranker": Reranker(),
        "guard": PromptGuard(),
        "prompt_builder": PromptBuilder(),
        "llm": LLMEngine(),
        "verifier": FactVerifier(),
        "citation": CitationInjector()
    }


# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display quick pills if chat is empty
if not st.session_state.messages:
    st.write("### Try asking:")
    # Row 1
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Compare HDFC Mid Cap vs Small Cap expense ratio", key="pill1", use_container_width=True):
            st.session_state.pill_query = "Compare HDFC Mid Cap vs Small Cap expense ratio"
    with col2:
        if st.button("Which HDFC fund has the highest 3-year returns?", key="pill3", use_container_width=True):
            st.session_state.pill_query = "Which HDFC fund has the highest 3-year returns?"
            
    # Row 2
    col3, col4 = st.columns(2)
    with col3:
        if st.button("What is the NAV of HDFC Gold ETF FoF today?", key="pill2", use_container_width=True):
            st.session_state.pill_query = "What is the NAV of HDFC Gold ETF FoF today?"
    with col4:
        if st.button("Explain exit load rules for HDFC Large Cap Fund", key="pill4", use_container_width=True):
            st.session_state.pill_query = "Explain exit load rules for HDFC Large Cap Fund"

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
prompt = st.chat_input("Ask about Groww mutual funds...")

# Handle pill click
if "pill_query" in st.session_state and st.session_state.pill_query:
    prompt = st.session_state.pill_query
    st.session_state.pill_query = None

if prompt:
    # Add user message to state
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call API and stream response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            components = load_rag_components()
            
            # 1. Guardrail Check
            if not components["guard"].check_safety(prompt):
                full_response = "I cannot fulfill this request as it violates safety guidelines."
                message_placeholder.markdown(full_response)
            else:
                # 2. Retrieve & Rerank
                top_chunks = components["reranker"].retrieve_and_rerank(prompt)
                
                # 3. Build Prompt
                llm_prompt = components["prompt_builder"].build_prompt(prompt, top_chunks)
                
                # 4. Stream response
                for token in components["llm"].generate_response_stream(llm_prompt):
                    full_response += token
                    message_placeholder.markdown(full_response + "▌")
                    
                # 5. Output Verification
                verified_text = components["verifier"].verify(full_response, top_chunks)
                if verified_text != full_response:
                    full_response = verified_text + "\n\n[Correction: Verified data not available in the knowledge base for this figure.]"
                    
                # 6. Citations
                citations = components["citation"].inject_citations("", top_chunks)
                full_response += citations
                
                # Final update
                message_placeholder.markdown(full_response)
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            full_response = "I encountered an error processing your request."
            
        st.session_state.messages.append({"role": "assistant", "content": full_response})
