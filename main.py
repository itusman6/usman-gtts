import io
import asyncio
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import edge_tts

app = FastAPI(
    title="Edge Neural TTS API",
    version="1.0.0",
    description="Vercel-safe TTS with REAL voice changes"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------
# 25+ REAL NEURAL VOICES
# ------------------------------------
VOICES = {
    # English
    "en_male_1": "en-US-GuyNeural",
    "en_female_1": "en-US-JennyNeural",
    "en_female_2": "en-US-AriaNeural",
    "en_male_2": "en-US-DavisNeural",
    "en_uk_male": "en-GB-RyanNeural",
    "en_uk_female": "en-GB-SoniaNeural",
    "en_india_male": "en-IN-PrabhatNeural",
    "en_india_female": "en-IN-NeerjaNeural",

    # Spanish
    "es_male": "es-ES-AlvaroNeural",
    "es_female": "es-ES-ElviraNeural",
    "es_mexico": "es-MX-JorgeNeural",

    # French
    "fr_male": "fr-FR-HenriNeural",
    "fr_female": "fr-FR-DeniseNeural",

    # German
    "de_male": "de-DE-ConradNeural",
    "de_female": "de-DE-KatjaNeural",

    # Italian / Portuguese
    "it_male": "it-IT-DiegoNeural",
    "it_female": "it-IT-ElsaNeural",
    "pt_br_male": "pt-BR-AntonioNeural",
    "pt_br_female": "pt-BR-FranciscaNeural",

    # Asian
    "ja_female": "ja-JP-NanamiNeural",
    "ko_female": "ko-KR-SunHiNeural",
    "zh_male": "zh-CN-YunxiNeural",
    "zh_female": "zh-CN-XiaoxiaoNeural",

    # Arabic / Russian / Hindi
    "ar_male": "ar-SA-HamedNeural",
    "ru_female": "ru-RU-SvetlanaNeural",
    "hi_female": "hi-IN-SwaraNeural",
}

# ------------------------------------
# Helpers
# ------------------------------------
async def synthesize(text: str, voice: str) -> bytes:
    if voice not in VOICES:
        raise HTTPException(status_code=400, detail="Invalid voice")

    communicate = edge_tts.Communicate(
        text=text,
        voice=VOICES[voice],
        rate="+0%",
        volume="+0%"
    )

    audio_bytes = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_bytes += chunk["data"]

    return audio_bytes

# ------------------------------------
# Routes
# ------------------------------------
@app.get("/")
def root():
    return {
        "status": "running",
        "voices": len(VOICES),
        "engine": "edge-tts"
    }

@app.get("/voices")
def list_voices():
    return VOICES

@app.get("/tts")
async def tts(
    text: str = Query(..., max_length=1000),
    voice: str = Query("en_female_1"),
    download: bool = False
):
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text is empty")

    audio = await synthesize(text, voice)

    headers = {}
    if download:
        headers["Content-Disposition"] = 'attachment; filename="speech.mp3"'

    return StreamingResponse(
        io.BytesIO(audio),
        media_type="audio/mpeg",
        headers=headers
    )

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)




