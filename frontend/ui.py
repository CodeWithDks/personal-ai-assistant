import streamlit as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))
from backend.app.ai.agent import assistant

st.set_page_config(page_title="AI Agent", page_icon="🤖")

st.title("🤖 AI Agent")
st.write("Ask anything and let the agent respond.")

# User Input
user_input = st.text_input(
    "Ask the agent anything:",
    placeholder="Type your prompt here..."
)

if st.button("Run Agent"):
    if not user_input.strip():
        st.warning("Please enter a valid prompt.")
    else:
        with st.spinner("Agent is thinking..."):
            try:
                response = assistant.invoke(
                    {
                        "messages": [
                            {
                                "role": "user",
                                "content": user_input,
                            }
                        ]
                    }
                )

                # Get last AI message
                output = response["messages"][-1].content

                st.subheader("Agent Response")
                st.write(output)

            except Exception as e:
                st.error(f"Error: {e}")