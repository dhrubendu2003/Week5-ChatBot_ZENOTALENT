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

if "input_key" not in st.session_state:
    st.session_state.input_key = 0  # For resetting text input

# --- Convert text to speech ---
def speak_text(text, lang="en"):
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        mp3_buffer = io.BytesIO()
        tts.write_to_fp(mp3_buffer)
        mp3_buffer.seek(0)
        return mp3_buffer.read()
    except Exception as e:
        st.error(f"❌ TTS failed: {str(e)}")
        return None

# --- Display chat history ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and "audio" in message:
            st.audio(message["audio"], format="audio/mp3")

# --- Input Section: Text + Mic ---
text_col, mic_col = st.columns([10, 1])

# Use dynamic key to allow reset
input_key = f"user_input_{st.session_state.input_key}"

with text_col:
    user_text = st.text_input(
        "Message",
        key=input_key,
        placeholder="Type a message...",
        label_visibility="collapsed"
    )

with mic_col:
    st.write(" ")
    voice_clicked = st.button("🎤", key="mic_btn", help="Hold to speak")

# --- Handle Voice Input ---
if voice_clicked:
    st.session_state.recording = True

if st.session_state.get("recording"):
    with st.sidebar:
        st.info("🎙️ Speak now. Click outside to stop.")
        audio_bytes = st.audio_input("Record your voice", key="voice_recorder")

        if audio_bytes:
            try:
                # Save to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                    tmp_file.write(audio_bytes.getvalue())
                    tmp_path = tmp_file.name

                # STT
                r = sr.Recognizer()
                with sr.AudioFile(tmp_path) as source:
                    audio = r.record(source)
                text = r.recognize_google(audio)

                if text and not any(m["content"] == text for m in st.session_state.messages if m["role"] == "user"):
                    st.session_state.messages.append({"role": "user", "content": text})
                    st.session_state.input_key += 1  # Reset input key
                    st.rerun()

            except Exception as e:
                st.sidebar.error(f"🎤 Error: {str(e)}")
            finally:
                st.session_state.recording = False

# --- Handle Text Input ---
if user_text.strip():
    if not any(m["content"] == user_text for m in st.session_state.messages if m["role"] == "user"):
        st.session_state.messages.append({"role": "user", "content": user_text})
    
    # Reset input by incrementing key
    st.session_state.input_key += 1
    st.rerun()

# --- Generate AI Response ---
for idx, msg in enumerate(st.session_state.messages):
    if msg["role"] == "user":
        ai_key = f"ai_replied_{idx}"
        if ai_key not in st.session_state:
            with st.chat_message("assistant"):
                with st.spinner("🧠 Thinking..."):
                    try:
                        response = model.generate_content(msg["content"])
                        ai_text = response.text.strip()
                    except Exception as e:
                        ai_text = "I'm sorry, I couldn't process your request."

                st.markdown(ai_text)
                audio_data = speak_text(ai_text)
                if audio_data:
                    st.audio(audio_data, format="audio/mp3")

                # Append AI response
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": ai_text,
                    "audio": audio_data
                })

            # Mark as processed
            st.session_state[ai_key] = True
            st.rerun()  
            break