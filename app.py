import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import speech_recognition as sr
import io
import tempfile

# --- Page config ---
st.set_page_config(page_title="ChatBot by Dhrubendu", page_icon="🎙️", layout="centered")

# --- Load API Key ---
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash-latest")
except Exception as e:
    st.error("API Key not found. Check your secrets.")
    st.stop()

# --- Initialize session state ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Function: Convert text to speech ---
def speak_text(text, lang="en"):
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        mp3_buffer = io.BytesIO()
        tts.write_to_fp(mp3_buffer)
        mp3_buffer.seek(0)
        return mp3_buffer.read()
    except Exception as e:
        st.error(f"Failed: {str(e)}")
        return None

# --- Display chat history ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and "audio" in message:
            st.audio(message["audio"], format="audio/mp3")

# --- Input Section: Text + Mic ---
text_col, mic_col = st.columns([10, 1])

with text_col:
    user_text = st.text_input("Message", key="input_text", label_visibility="collapsed", placeholder="Type a message...")

with mic_col:
    st.write(" ")
    voice_clicked = st.button("🎤", key="btn_mic", help="Speak")

# --- Handle Voice Input ---
if voice_clicked:
    st.session_state.recording = True

if st.session_state.get("recording"):
    with st.sidebar:
        st.info("🎙️ Speak now...")
        audio_bytes = st.audio_input("Recording...", key="audio_input")
        if audio_bytes:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(audio_bytes.getvalue())
                tmp_path = tmp_file.name
            r = sr.Recognizer()
            try:
                with sr.AudioFile(tmp_path) as source:
                    audio = r.record(source)
                text = r.recognize_google(audio)
                if text:
                    if not any(m.get("content") == text and m["role"] == "user" for m in st.session_state.messages):
                        st.session_state.messages.append({"role": "user", "content": text})
                        st.rerun()
            except Exception as e:
                st.sidebar.error(f"STT Error: {e}")
            finally:
                st.session_state.recording = False

# --- Handle Text Input ---
if user_text.strip():
    # Prevent duplicate user messages
    if not any(m["content"] == user_text and m["role"] == "user" for m in st.session_state.messages):
        st.session_state.messages.append({"role": "user", "content": user_text})
        st.rerun()

# --- Generate AI Response ---
for idx, msg in enumerate(st.session_state.messages):
    if msg["role"] == "user":
        ai_reply_key = f"ai_reply_done_{idx}"
        if ai_reply_key not in st.session_state:
            with st.chat_message("assistant"):
                with st.spinner("🧠 Thinking..."):
                    try:
                        response = model.generate_content(msg["content"])
                        ai_text = response.text.strip()
                    except Exception as e:
                        ai_text = "I'm sorry, I couldn't respond."

                st.markdown(ai_text)
                audio_data = speak_text(ai_text)
                if audio_data:
                    st.audio(audio_data, format="audio/mp3")

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": ai_text,
                    "audio": audio_data
                })

            st.session_state[ai_reply_key] = True
            st.rerun()
            break