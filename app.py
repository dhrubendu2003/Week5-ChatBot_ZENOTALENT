import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import io

# --- Page configuration ---
st.set_page_config(
    page_title="Gemini Voice Bot",
    page_icon="🎙️",
    layout="centered"
)

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash-latest")

# --- Sidebar ---
st.sidebar.title("TTS ChatBot by Dhrubendu")
st.sidebar.markdown("---")
st.sidebar.markdown("🎙️ Powered by Gemini & gTTS")

# --- Check chat history ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- convert text to speech ---
def speak_text(text, lang="en"):
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        mp3_buffer = io.BytesIO()
        tts.write_to_fp(mp3_buffer)
        mp3_buffer.seek(0)
        return mp3_buffer.read()
    except Exception as e:
        st.error(f"Speech generation failed: {str(e)}")
        return None

# Get user input
prompt = st.chat_input("💬 Ask me anything...")

if prompt:
    # user message
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("🤖 Thinking..."):
        try:
            response = model.generate_content(prompt)
            ai_response = response.text.strip()
        except Exception as e:
            ai_response = "I'm sorry, I couldn't process that right now. Please try again later."
            st.error(f"AI Error: {str(e)}")

    # AI response
    with st.chat_message("assistant"):
        st.markdown(ai_response)
    st.session_state.messages.append({"role": "assistant", "content": ai_response})

    # Audio
    with st.spinner("🔊 Converting to speech..."):
        audio_data = speak_text(ai_response)
        if audio_data:
            st.audio(audio_data, format="audio/mp3")