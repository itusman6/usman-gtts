import edge_tts
import os
from fastapi import FastAPI, Response, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware if needed
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Your voices dictionary
VOICES = {
    "jenny": "en-US-JennyNeural",
    "guy": "en-US-GuyNeural",
    "emma": "en-GB-EmmaNeural",
    "female": "en-US-AriaNeural"
}

@app.get("/")
async def root():
    return {
        "message": "Edge TTS API is running",
        "endpoints": {
            "/tts": "GET ?text=YourText&voice=voiceName",
            "/voices": "GET - List available voices",
            "/health": "GET - Health check"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "edge-tts-api"}

@app.get("/voices")
async def get_voices():
    """List all available voices"""
    return {"voices": VOICES}

@app.get("/tts")
async def text_to_speech(text: str, voice: str = "jenny"):
    """Generate speech using Edge TTS"""
    try:
        # Input validation
        if not text or len(text.strip()) == 0:
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Limit text length to prevent abuse
        if len(text) > 5000:
            raise HTTPException(status_code=400, detail="Text too long. Maximum 5000 characters.")
        
        # Get voice or default to jenny
        selected_voice = VOICES.get(voice, VOICES["jenny"])
        logger.info(f"Generating speech: '{text[:50]}...' with voice: {selected_voice}")
        
        # Generate audio
        communicate = edge_tts.Communicate(text, selected_voice)
        
        # Collect audio chunks
        audio_data = bytearray()
        
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data.extend(chunk["data"])
        
        # Return as streaming response
        async def audio_generator():
            yield bytes(audio_data)
        
        headers = {
            "Content-Disposition": "attachment; filename=speech.mp3",
            "Content-Type": "audio/mpeg",
            "X-Voice-Used": selected_voice
        }
        
        return StreamingResponse(
            audio_generator(),
            media_type="audio/mpeg",
            headers=headers
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating speech: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate speech: {str(e)}")

# Alternative endpoint for POST requests (for longer texts)
@app.post("/tts")
async def text_to_speech_post(text: str = None, voice: str = "jenny"):
    """Generate speech using POST method"""
    if text is None:
        raise HTTPException(status_code=400, detail="Text is required")
    return await text_to_speech(text, voice)

# Handle 404 errors
@app.exception_handler(404)
async def not_found_exception_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Endpoint not found. Use /tts?text=YourText"}
    )

# For Vercel deployment
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
