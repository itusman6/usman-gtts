import io
import base64
from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse
from TTS.api import TTS

app = FastAPI()

# Load model once per cold start (Vercel caches)
tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False, gpu=False)

@app.post("/api/speak")
async def speak(text: str = Form(...), voice: str = Form("all"), format: str = Form("wav")):
    """
    Generate TTS audio for given text.
    Returns: base64 encoded audio
    """
    # Generate in-memory file
    file_buffer = io.BytesIO()
    tts.tts_to_file(text=text, speaker=voice, file_path=file_buffer)
    
    file_buffer.seek(0)
    audio_bytes = file_buffer.read()
    encoded_audio = base64.b64encode(audio_bytes).decode("utf-8")
    
    return JSONResponse({"audio_base64": encoded_audio, "format": format})

@app.get("/api/voices")
async def get_voices():
    return {"voices": tts.speakers}
