import streamlit as st
import requests
import json
import time

import os
API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")

st.set_page_config(
    page_title="HDFC Mutual Fund Advisor",
    page_icon="📈",
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
        background-color: rgba(88, 166, 255, 0.1) !important;
        border: 1px solid rgba(88, 166, 255, 0.3) !important;
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
    }
    div[data-testid="stButton"] button p {
        font-size: 0.82rem !important;
    }
    div[data-testid="stButton"] button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
    }
</style>
""", unsafe_allow_html=True)



st.title("📈 HDFC Fund Advisor AI")
st.caption("Powered by Groq Llama3, ChromaDB, and BGE Cross-Encoder Reranking")


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
prompt = st.chat_input("Ask about HDFC mutual funds...")

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
            # We make a POST request with stream=True
            response = requests.post(
                f"{API_URL}/chat",
                json={"query": prompt, "history": []},
                stream=True,
                timeout=30
            )
            
            if response.status_code == 200:
                for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                    if chunk:
                        full_response += chunk
                        # Update placeholder
                        message_placeholder.markdown(full_response + "▌")
                # Final update without cursor
                message_placeholder.markdown(full_response)
            else:
                st.error(f"API Error {response.status_code}: {response.text}")
                full_response = "Sorry, I encountered an error communicating with the backend."
                
        except requests.exceptions.RequestException as e:
            st.error(f"Could not connect to API: {e}")
            full_response = "Sorry, the backend server is unreachable."
            
        st.session_state.messages.append({"role": "assistant", "content": full_response})
