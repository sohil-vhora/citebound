import streamlit as st
from anthropic import Anthropic
from dotenv import load_dotenv
import os

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

st.title("Citebound — Day 1 Test")
st.caption("Research project on high-stakes RAG. Not legal or immigration advice.")

question = st.text_input("Ask a question:", "How long is a study permit valid in Canada?")

if st.button("Ask"):
    with st.spinner("Thinking..."):
        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=500,
            messages=[{"role": "user", "content": question}]
        )
        st.write(response.content[0].text)