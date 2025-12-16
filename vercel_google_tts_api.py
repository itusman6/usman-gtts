import os
import io
import base64
import tempfile
import json
from pathlib import Path
from typing import Optional, Dict, List
from enum import Enum
import subprocess
import sys

# FastAPI imports
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check if we're in production
IS_VERCEL = os.getenv("VERCEL") == "1"

# Initialize FastAPI app
app = FastAPI(
    title="eSpeak NG TTS API",
    description="Text-to-Speech API using eSpeak NG-like functionality",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Language definitions
class Language(str, Enum):
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    RUSSIAN = "ru"
    CHINESE = "zh"
    JAPANESE = "ja"
    KOREAN = "ko"
    HINDI = "hi"
    ARABIC = "ar"
    DUTCH = "nl"
    SWEDISH = "sv"
    POLISH = "pl"

class VoiceGender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"

class TTSRequest(BaseModel):
    text: str = Field(..., description="Text to convert to speech", max_length=1000)
    language: Language = Field(Language.ENGLISH, description="Language code")
    voice: Optional[str] = Field(None, description="Voice name")
    speed: int = Field(160, ge=80, le=300, description="Speech speed (80-300)")
    pitch: int = Field(50, ge=0, le=99, description="Pitch (0-99)")
    volume: int = Field(100, ge=0, le=200, description="Volume (0-200)")
    gender: Optional[VoiceGender] = Field(None, description="Voice gender")
    ssml: Optional[bool] = Field(False, description="Whether text is SSML")

class TTSResponse(BaseModel):
    success: bool
    message: str
    audio_url: Optional[str] = None
    audio_base64: Optional[str] = None
    duration: Optional[float] = None
    sample_rate: Optional[int] = None
    format: Optional[str] = None

class VoiceInfo(BaseModel):
    name: str
    language: str
    gender: Optional[str]
    age: Optional[int]

# Language to voice mapping
LANGUAGE_VOICES = {
    "en": ["en-us", "en-gb", "en-scotland", "en-north", "en-rp", "en-wmids"],
    "es": ["es", "es-la"],
    "fr": ["fr", "fr-be", "fr-ch"],
    "de": ["de", "de-at", "de-ch"],
    "it": ["it"],
    "pt": ["pt", "pt-br"],
    "ru": ["ru"],
    "zh": ["zh", "zh-yue"],
    "ja": ["ja"],
    "ko": ["ko"],
    "hi": ["hi"],
    "ar": ["ar"],
    "nl": ["nl"],
    "sv": ["sv"],
    "pl": ["pl"]
}

# Available voices (simulated)
AVAILABLE_VOICES = [
    {"name": "en-us", "language": "en", "gender": "male", "age": 30},
    {"name": "en-gb", "language": "en", "gender": "female", "age": 25},
    {"name": "es", "language": "es", "gender": "male", "age": 35},
    {"name": "fr", "language": "fr", "gender": "female", "age": 28},
    {"name": "de", "language": "de", "gender": "male", "age": 40},
    {"name": "it", "language": "it", "gender": "female", "age": 32},
    {"name": "ja", "language": "ja", "gender": "female", "age": 26},
    {"name": "zh", "language": "zh", "gender": "male", "age": 45},
]

# Try to import espeak-phonemizer if available
try:
    from phonemizer import phonemize
    from phonemizer.backend import EspeakBackend
    PHONEMIZER_AVAILABLE = True
except ImportError:
    PHONEMIZER_AVAILABLE = False
    logger.warning("phonemizer not available. Phonetic conversion disabled.")

# Try to import gTTS for fallback
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    logger.warning("gTTS not available. Using fallback methods.")

def text_to_phonemes(text: str, language: str = "en-us") -> str:
    """Convert text to phonemes using phonemizer"""
    if not PHONEMIZER_AVAILABLE:
        return text
    
    try:
        backend = EspeakBackend(language=language, preserve_punctuation=True)
        phonemes = phonemize(
            text,
            language=language,
            backend=backend,
            strip=True,
            preserve_punctuation=True,
            with_stress=True
        )
        return phonemes
    except Exception as e:
        logger.error(f"Phonemization failed: {e}")
        return text

def generate_audio_gtts(text: str, language: str = "en", slow: bool = False) -> bytes:
    """Generate audio using gTTS (Google Text-to-Speech) as fallback"""
    if not GTTS_AVAILABLE:
        raise RuntimeError("gTTS is not available")
    
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
            temp_path = tmp_file.name
        
        # Generate speech
        tts = gTTS(text=text, lang=language, slow=slow)
        tts.save(temp_path)
        
        # Read file
        with open(temp_path, 'rb') as f:
            audio_data = f.read()
        
        # Cleanup
        os.unlink(temp_path)
        
        return audio_data, "mp3"
    except Exception as e:
        raise RuntimeError(f"gTTS failed: {e}")

def generate_audio_pyttsx3(text: str, language: str = "en") -> bytes:
    """Generate audio using pyttsx3 (offline TTS)"""
    try:
        import pyttsx3
        import wave
        import pyaudio
        
        # Initialize engine
        engine = pyttsx3.init()
        
        # Set properties
        engine.setProperty('rate', 150)
        
        # Set voice based on language
        voices = engine.getProperty('voices')
        for voice in voices:
            if language in voice.id.lower():
                engine.setProperty('voice', voice.id)
                break
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            temp_path = tmp_file.name
        
        engine.save_to_file(text, temp_path)
        engine.runAndWait()
        
        # Read file
        with open(temp_path, 'rb') as f:
            audio_data = f.read()
        
        # Cleanup
        os.unlink(temp_path)
        
        return audio_data, "wav"
    except ImportError:
        raise RuntimeError("pyttsx3 not available")
    except Exception as e:
        raise RuntimeError(f"pyttsx3 failed: {e}")

def generate_sine_wave(text: str, sample_rate: int = 22050) -> bytes:
    """Generate a simple sine wave audio for demonstration"""
    import numpy as np
    from scipy.io import wavfile
    
    # Convert text to a simple tone sequence
    duration_per_char = 0.1  # seconds per character
    frequency_base = 220  # Hz
    
    # Generate tones for each character
    audio_chunks = []
    for i, char in enumerate(text):
        if char.isalpha():
            # Map character to frequency
            freq = frequency_base + (ord(char.lower()) - ord('a')) * 10
            
            # Generate sine wave for this character
            t = np.linspace(0, duration_per_char, int(sample_rate * duration_per_char), False)
            tone = 0.5 * np.sin(2 * np.pi * freq * t)
            
            # Add fade in/out
            fade_samples = int(0.01 * sample_rate)
            if len(tone) > fade_samples * 2:
                tone[:fade_samples] *= np.linspace(0, 1, fade_samples)
                tone[-fade_samples:] *= np.linspace(1, 0, fade_samples)
            
            audio_chunks.append(tone)
        
        # Add short pause for spaces
        if char == ' ':
            silence = np.zeros(int(sample_rate * duration_per_char * 0.3))
            audio_chunks.append(silence)
    
    if not audio_chunks:
        # Generate default tone
        t = np.linspace(0, 1.0, sample_rate, False)
        audio_chunks = [0.5 * np.sin(2 * np.pi * 440 * t)]
    
    # Combine all chunks
    audio = np.concatenate(audio_chunks)
    
    # Normalize
    audio = audio / np.max(np.abs(audio)) * 0.8
    
    # Convert to 16-bit PCM
    audio_int16 = (audio * 32767).astype(np.int16)
    
    # Write to bytes buffer
    buffer = io.BytesIO()
    wavfile.write(buffer, sample_rate, audio_int16)
    
    return buffer.getvalue()

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "eSpeak NG TTS API",
        "version": "1.0.0",
        "status": "running",
        "environment": "vercel" if IS_VERCEL else "local",
        "features": {
            "phonemizer": PHONEMIZER_AVAILABLE,
            "gtts": GTTS_AVAILABLE,
            "max_text_length": 1000
        },
        "endpoints": {
            "/": "This info page",
            "/tts": "Generate speech from text (GET)",
            "/tts-post": "Generate speech from text (POST)",
            "/voices": "Get available voices",
            "/languages": "Get supported languages",
            "/phonemes": "Convert text to phonemes",
            "/health": "Health check"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "phonemizer": PHONEMIZER_AVAILABLE,
        "gtts": GTTS_AVAILABLE,
        "environment": "vercel" if IS_VERCEL else "local"
    }

@app.get("/voices")
async def get_voices(language: Optional[str] = None):
    """Get available voices"""
    if language:
        filtered_voices = [v for v in AVAILABLE_VOICES if v["language"] == language]
    else:
        filtered_voices = AVAILABLE_VOICES
    
    return {
        "voices": filtered_voices,
        "count": len(filtered_voices)
    }

@app.get("/languages")
async def get_languages():
    """Get supported languages"""
    languages = list(LANGUAGE_VOICES.keys())
    return {
        "languages": languages,
        "count": len(languages)
    }

@app.get("/phonemes")
async def get_phonemes(
    text: str = Query(..., description="Text to convert to phonemes"),
    language: str = Query("en-us", description="Language/variant for phonemization")
):
    """Convert text to phonemes"""
    if not PHONEMIZER_AVAILABLE:
        raise HTTPException(status_code=501, detail="Phonemizer not available")
    
    try:
        phonemes = text_to_phonemes(text, language)
        return {
            "text": text,
            "phonemes": phonemes,
            "language": language,
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Phonemization failed: {str(e)}")

@app.get("/tts")
async def tts_get(
    text: str = Query(..., description="Text to convert to speech"),
    language: str = Query("en", description="Language code"),
    voice: Optional[str] = Query(None, description="Voice name"),
    speed: int = Query(160, ge=80, le=300, description="Speech speed (80-300)"),
    pitch: int = Query(50, ge=0, le=99, description="Pitch (0-99)"),
    volume: int = Query(100, ge=0, le=200, description="Volume (0-200)"),
    download: bool = Query(False, description="Force download instead of streaming"),
    engine: str = Query("gtts", description="TTS engine to use (gtts, demo, phonemes)")
):
    """Generate speech from text (GET endpoint)"""
    try:
        # Limit text length
        if len(text) > 1000:
            text = text[:1000]
        
        audio_data = None
        content_type = "audio/wav"
        
        if engine == "gtts" and GTTS_AVAILABLE:
            # Use gTTS
            audio_data, format = generate_audio_gtts(text, language)
            content_type = f"audio/{format}"
            
        elif engine == "phonemes" and PHONEMIZER_AVAILABLE:
            # Convert to phonemes first
            phonemes = text_to_phonemes(text, voice or f"{language}-us")
            
            # For demo, generate audio from phonemes
            # In a real implementation, you would use a phoneme-to-speech synthesizer
            audio_data = generate_sine_wave(phonemes)
            
        elif engine == "demo":
            # Generate demo sine wave audio
            audio_data = generate_sine_wave(text)
            
        else:
            # Try pyttsx3 as fallback
            try:
                audio_data, format = generate_audio_pyttsx3(text, language)
                content_type = f"audio/{format}"
            except:
                # Final fallback to sine wave
                audio_data = generate_sine_wave(text)
        
        if not audio_data:
            raise HTTPException(status_code=500, detail="Failed to generate audio")
        
        # Create response
        headers = {}
        if download:
            headers["Content-Disposition"] = 'attachment; filename="speech.wav"'
        
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type=content_type,
            headers=headers
        )
        
    except Exception as e:
        logger.error(f"TTS generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")

@app.post("/tts", response_model=TTSResponse)
async def tts_post(request: TTSRequest):
    """Generate speech from text (POST endpoint with JSON response)"""
    try:
        # Limit text length
        text = request.text[:1000] if len(request.text) > 1000 else request.text
        
        # Determine voice
        voice = request.voice or f"{request.language}-us"
        
        # Generate audio
        audio_data = None
        format = "wav"
        
        if GTTS_AVAILABLE:
            try:
                audio_data, format = generate_audio_gtts(text, request.language)
            except:
                pass
        
        if not audio_data:
            # Fallback to demo audio
            audio_data = generate_sine_wave(text)
        
        # Encode audio as base64
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        return TTSResponse(
            success=True,
            message="Speech generated successfully",
            audio_base64=audio_base64,
            duration=len(audio_data) / 44100 / 2,  # Rough estimate
            sample_rate=22050,
            format=format
        )
        
    except Exception as e:
        logger.error(f"TTS generation failed: {e}")
        return TTSResponse(
            success=False,
            message=f"TTS generation failed: {str(e)}",
            audio_base64=None,
            duration=None,
            sample_rate=None,
            format=None
        )

@app.post("/tts-audio")
async def tts_audio(request: TTSRequest):
    """Generate speech from text (POST endpoint returning audio directly)"""
    try:
        # Limit text length
        text = request.text[:1000] if len(request.text) > 1000 else request.text
        
        # Determine voice
        voice = request.voice or f"{request.language}-us"
        
        # Generate audio
        audio_data = None
        
        if GTTS_AVAILABLE:
            try:
                audio_data, format = generate_audio_gtts(text, request.language)
                content_type = f"audio/{format}"
            except:
                audio_data = generate_sine_wave(text)
                content_type = "audio/wav"
        else:
            audio_data = generate_sine_wave(text)
            content_type = "audio/wav"
        
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type=content_type
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")

# Static files for demo page
if not IS_VERCEL:
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/demo")
async def demo_page():
    """Demo HTML page for testing TTS"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>eSpeak NG TTS Demo</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .container { background: #f5f5f5; padding: 20px; border-radius: 10px; }
            textarea { width: 100%; height: 100px; margin: 10px 0; padding: 10px; }
            select, input { margin: 5px; padding: 5px; }
            button { background: #0070f3; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
            button:hover { background: #0051cc; }
            .controls { margin: 20px 0; }
            .audio-player { margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>eSpeak NG TTS Demo</h1>
            
            <div class="controls">
                <textarea id="text" placeholder="Enter text to convert to speech...">Hello, this is a test of the eSpeak NG TTS system.</textarea>
                
                <div>
                    <label>Language:</label>
                    <select id="language">
                        <option value="en">English</option>
                        <option value="es">Spanish</option>
                        <option value="fr">French</option>
                        <option value="de">German</option>
                        <option value="it">Italian</option>
                        <option value="ja">Japanese</option>
                        <option value="zh">Chinese</option>
                    </select>
                    
                    <label>Speed:</label>
                    <input type="range" id="speed" min="80" max="300" value="160">
                    <span id="speed-value">160</span>
                    
                    <label>Engine:</label>
                    <select id="engine">
                        <option value="gtts">Google TTS (Online)</option>
                        <option value="demo">Demo Tone</option>
                        <option value="phonemes">Phonemes (Experimental)</option>
                    </select>
                </div>
                
                <button onclick="generateSpeech()">Generate Speech</button>
                <button onclick="downloadSpeech()">Download</button>
            </div>
            
            <div class="audio-player">
                <audio id="audio-player" controls style="width: 100%;"></audio>
            </div>
            
            <div id="status"></div>
        </div>
        
        <script>
            function updateSpeed() {
                document.getElementById('speed-value').textContent = document.getElementById('speed').value;
            }
            
            function generateSpeech() {
                const text = document.getElementById('text').value;
                const language = document.getElementById('language').value;
                const speed = document.getElementById('speed').value;
                const engine = document.getElementById('engine').value;
                
                const status = document.getElementById('status');
                status.innerHTML = 'Generating speech...';
                
                // Build URL
                const url = `/tts?text=${encodeURIComponent(text)}&language=${language}&speed=${speed}&engine=${engine}`;
                
                // Update audio player
                const audioPlayer = document.getElementById('audio-player');
                audioPlayer.src = url;
                
                status.innerHTML = 'Speech generated! Click play to listen.';
            }
            
            function downloadSpeech() {
                const text = document.getElementById('text').value;
                const language = document.getElementById('language').value;
                const speed = document.getElementById('speed').value;
                const engine = document.getElementById('engine').value;
                
                // Build URL for download
                const url = `/tts?text=${encodeURIComponent(text)}&language=${language}&speed=${speed}&engine=${engine}&download=true`;
                
                // Trigger download
                window.open(url, '_blank');
            }
            
            // Initialize
            document.getElementById('speed').addEventListener('input', updateSpeed);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html_content)

from fastapi.responses import HTMLResponse

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
