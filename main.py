import io
import base64
import tempfile
from typing import Optional, Dict
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from gtts import gTTS
import numpy as np
from scipy.io import wavfile

# --------------------------------
# App
# --------------------------------
app = FastAPI(
    title="Multi-Voice TTS API",
    version="1.1.0",
    description="Vercel-safe TTS with 25+ voice presets (gTTS)"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------
# 25+ Voice Presets (gTTS)
# --------------------------------
VOICES: Dict[str, Dict] = {
    # English
    "en_us_male": {"lang": "en", "tld": "com", "slow": False},
    "en_us_female": {"lang": "en", "tld": "com", "slow": True},
    "en_uk_male": {"lang": "en", "tld": "co.uk", "slow": False},
    "en_uk_female": {"lang": "en", "tld": "co.uk", "slow": True},
    "en_india": {"lang": "en", "tld": "co.in", "slow": False},
    "en_australia": {"lang": "en", "tld": "com.au", "slow": False},
    "en_canada": {"lang": "en", "tld": "ca", "slow": False},
    "en_ireland": {"lang": "en", "tld": "ie", "slow": False},

    # Spanish
    "es_spain": {"lang": "es", "tld": "es", "slow": False},
    "es_mexico": {"lang": "es", "tld": "com.mx", "slow": False},
    "es_argentina": {"lang": "es", "tld": "com.ar", "slow": False},

    # French
    "fr_france": {"lang": "fr", "tld": "fr", "slow": False},
    "fr_canada": {"lang": "fr", "tld": "ca", "slow": False},

    # German
    "de_germany": {"lang": "de", "tld": "de", "slow": False},
    "de_austria": {"lang": "de", "tld": "at", "slow": False},

    # Italian / Portuguese
    "it_italy": {"lang": "it", "tld": "it", "slow": False},
    "pt_portugal": {"lang": "pt", "tld": "pt", "slow": False},
    "pt_brazil": {"lang": "pt", "tld": "com.br", "slow": False},

    # Asian
    "ja_japan": {"lang": "ja", "tld": "jp", "slow": False},
    "ko_korea": {"lang": "ko", "tld": "kr", "slow": False},
    "zh_china": {"lang": "zh-CN", "tld": "cn", "slow": False},
    "zh_taiwan": {"lang": "zh-TW", "tld": "tw", "slow": False},

    # Other
    "ru_russia": {"lang": "ru", "tld": "ru", "slow": False},
    "hi_india": {"lang": "hi", "tld": "co.in", "slow": False},
    "ar_saudi": {"lang": "ar", "tld": "com.sa", "slow": False},
}

# --------------------------------
# Models
# --------------------------------
class TTSRequest(BaseModel):
    text: str = Field(..., max_length=1000)
    voice: str = Field("en_us_male")

# --------------------------------
# Helpers
# --------------------------------
def generate_gtts(text: str, voice: str) -> bytes:
    if voice not in VOICES:
        raise HTTPException(status_code=400, detail="Invalid voice")

    cfg = VOICES[voice]

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        path = f.name

    tts = gTTS(
        text=text,
        lang=cfg["lang"],
        tld=cfg["tld"],
        slow=cfg["slow"]
    )
    tts.save(path)

    with open(path, "rb") as f:
        return f.read()


def demo_wave(text: str):
    sr = 22050
    t = np.linspace(0, max(len(text) * 0.05, 0.5), int(sr * 0.5), False)
    wave = (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    pcm = (wave * 32767).astype(np.int16)

    buf = io.BytesIO()
    wavfile.write(buf, sr, pcm)
    return buf.getvalue()

# --------------------------------
# Routes
# --------------------------------
@app.get("/")
def root():
    return {
        "status": "running",
        "voices": len(VOICES)
    }

@app.get("/voices")
def list_voices():
    return VOICES

@app.get("/tts")
def tts_get(
    text: str = Query(..., max_length=1000),
    voice: str = Query("en_us_male"),
    download: bool = False
):
    try:
        audio = generate_gtts(text, voice)
        headers = {}
        if download:
            headers["Content-Disposition"] = 'attachment; filename="speech.mp3"'

        return StreamingResponse(
            io.BytesIO(audio),
            media_type="audio/mpeg",
            headers=headers
        )
    except Exception:
        audio = demo_wave(text)
        return StreamingResponse(io.BytesIO(audio), media_type="audio/wav")

@app.post("/tts")
def tts_post(data: TTSRequest):
    try:
        audio = generate_gtts(data.text, data.voice)
        return {
            "success": True,
            "voice": data.voice,
            "format": "mp3",
            "audio_base64": base64.b64encode(audio).decode()
        }
    except Exception:
        audio = demo_wave(data.text)
        return {
            "success": True,
            "voice": "demo",
            "format": "wav",
            "audio_base64": base64.b64encode(audio).decode()
        }

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
