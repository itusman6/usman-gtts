import os
import io
import json
import tempfile
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any
from http.client import HTTPException
import torch

# FastAPI imports
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Check if we're in production (Vercel has this env var)
IS_VERCEL = os.getenv("VERCEL") == "1"

# Initialize FastAPI app
app = FastAPI(
    title="Coqui TTS API",
    description="Text-to-Speech API using Coqui TTS",
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

# Global TTS model instance
_tts_model = None
_speaker_manager = None

class TTSRequest(BaseModel):
    text: str = Field(..., description="Text to convert to speech")
    speaker_id: Optional[str] = Field(None, description="Speaker ID (if using XTTS)")
    language: Optional[str] = Field("en", description="Language code (e.g., 'en', 'es', 'fr')")
    emotion: Optional[str] = Field(None, description="Emotion (if supported by model)")
    speed: Optional[float] = Field(1.0, ge=0.5, le=2.0, description="Speech speed multiplier")

class TTSResponse(BaseModel):
    success: bool
    message: str
    audio_url: Optional[str] = None
    audio_base64: Optional[str] = None
    duration: Optional[float] = None

def get_model_path(model_name: str = "tts_models/en/ljspeech/tacotron2-DDC"):
    """Get model path, considering Vercel's filesystem limitations"""
    if IS_VERCEL:
        # On Vercel, use /tmp for storage
        model_dir = Path("/tmp/coqui_models")
    else:
        model_dir = Path.home() / ".coqui" / "models"
    
    model_dir.mkdir(parents=True, exist_ok=True)
    return model_dir / model_name.replace("/", "_")

def initialize_model(
    model_name: str = "tts_models/en/ljspeech/tacotron2-DDC",
    use_cuda: bool = False
):
    """Initialize TTS model"""
    global _tts_model, _speaker_manager
    
    if _tts_model is not None:
        return _tts_model, _speaker_manager
    
    try:
        # Import TTS here to handle errors gracefully
        from TTS.api import TTS
        from TTS.utils.manage import ModelManager
        
        print(f"Initializing TTS model: {model_name}")
        
        # Check if CUDA is available
        if use_cuda and torch.cuda.is_available():
            device = "cuda"
            print("Using CUDA for TTS")
        else:
            device = "cpu"
            print("Using CPU for TTS")
        
        # Initialize TTS
        _tts_model = TTS(model_name, progress_bar=False).to(device)
        
        # Check if model has speaker manager (for XTTS models)
        try:
            if hasattr(_tts_model, 'speaker_manager') and _tts_model.speaker_manager:
                _speaker_manager = _tts_model.speaker_manager
                print(f"Speaker manager loaded. Available speakers: {len(_speaker_manager.speaker_ids)}")
        except:
            _speaker_manager = None
        
        print(f"TTS model '{model_name}' initialized successfully")
        return _tts_model, _speaker_manager
        
    except ImportError as e:
        raise ImportError("Coqui TTS is not installed. Please install it with: pip install TTS")
    except Exception as e:
        raise RuntimeError(f"Failed to initialize TTS model: {str(e)}")

def cleanup_temp_files():
    """Clean up temporary audio files"""
    try:
        temp_dir = Path("/tmp") if IS_VERCEL else Path(tempfile.gettempdir())
        for file in temp_dir.glob("tts_audio_*.wav"):
            try:
                file.unlink()
            except:
                pass
    except:
        pass

def text_to_speech(
    text: str,
    speaker_id: Optional[str] = None,
    language: Optional[str] = "en",
    emotion: Optional[str] = None,
    speed: float = 1.0,
    model_name: str = "tts_models/en/ljspeech/tacotron2-DDC"
):
    """Convert text to speech using Coqui TTS"""
    try:
        # Initialize model if not already done
        tts_model, speaker_manager = initialize_model(model_name)
        
        # Prepare parameters
        params = {}
        
        # Add speaker ID for XTTS models
        if speaker_id and speaker_manager:
            if speaker_id in speaker_manager.speaker_ids:
                params['speaker'] = speaker_id
            else:
                print(f"Speaker ID '{speaker_id}' not found. Using default.")
        
        # Add language for multilingual models
        if language and hasattr(tts_model, 'language'):
            params['language'] = language
        
        # Add emotion if supported
        if emotion and hasattr(tts_model, 'set_emotion'):
            try:
                tts_model.set_emotion(emotion)
            except:
                pass
        
        # Generate speech
        print(f"Generating speech for text: {text[:50]}...")
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(
            suffix=".wav", 
            delete=False,
            dir="/tmp" if IS_VERCEL else None
        ) as temp_file:
            temp_path = temp_file.name
            
            # Generate audio
            if speaker_id and 'speaker' in params:
                # For XTTS models with speaker
                tts_model.tts_to_file(
                    text=text,
                    speaker=params['speaker'],
                    language=language,
                    file_path=temp_path
                )
            else:
                # For regular models
                tts_model.tts_to_file(text=text, file_path=temp_path)
            
            # Read the generated audio
            with open(temp_path, 'rb') as audio_file:
                audio_data = audio_file.read()
            
            # Clean up temp file
            Path(temp_path).unlink()
            
            return audio_data
            
    except Exception as e:
        raise RuntimeError(f"Failed to generate speech: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    print("Starting up TTS API...")
    
    # Clean up any old temp files
    cleanup_temp_files()
    
    # Try to initialize model (but don't fail startup)
    try:
        initialize_model()
        print("TTS model initialized successfully")
    except Exception as e:
        print(f"Warning: Could not initialize TTS model on startup: {e}")
        print("Model will be initialized on first request")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("Shutting down TTS API...")
    cleanup_temp_files()

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Coqui TTS API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "/": "This info page",
            "/tts": "Generate speech from text (GET)",
            "/tts-post": "Generate speech from text (POST)",
            "/speakers": "Get available speakers",
            "/health": "Health check",
            "/models": "Get available models"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        tts_model, _ = initialize_model()
        return {
            "status": "healthy",
            "model_loaded": tts_model is not None,
            "device": "cuda" if torch.cuda.is_available() else "cpu",
            "environment": "vercel" if IS_VERCEL else "local"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.get("/speakers")
async def get_speakers():
    """Get available speakers"""
    try:
        _, speaker_manager = initialize_model()
        if speaker_manager:
            return {
                "speakers": list(speaker_manager.speaker_ids),
                "count": len(speaker_manager.speaker_ids)
            }
        else:
            return {"speakers": [], "count": 0, "message": "No speaker manager available for this model"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get speakers: {str(e)}")

@app.get("/models")
async def get_models():
    """Get available TTS models"""
    try:
        from TTS.api import TTS
        models = TTS().list_models()
        return {
            "models": models,
            "count": len(models)
        }
    except Exception as e:
        # Return some default models if TTS is not fully initialized
        return {
            "models": [
                "tts_models/en/ljspeech/tacotron2-DDC",
                "tts_models/en/ljspeech/glow-tts",
                "tts_models/en/ljspeech/speedy-speech",
                "tts_models/en/vctk/vits",
                "tts_models/multilingual/multi-dataset/xtts_v2"
            ],
            "message": "Using default model list"
        }

@app.get("/tts")
async def tts_get(
    text: str = Query(..., description="Text to convert to speech"),
    speaker: Optional[str] = Query(None, description="Speaker ID"),
    language: Optional[str] = Query("en", description="Language code"),
    emotion: Optional[str] = Query(None, description="Emotion"),
    speed: Optional[float] = Query(1.0, ge=0.5, le=2.0, description="Speech speed"),
    download: Optional[bool] = Query(False, description="Force download instead of streaming")
):
    """Generate speech from text (GET endpoint)"""
    try:
        # Generate audio
        audio_data = text_to_speech(
            text=text,
            speaker_id=speaker,
            language=language,
            emotion=emotion,
            speed=speed
        )
        
        # Create response
        headers = {}
        if download:
            headers["Content-Disposition"] = 'attachment; filename="speech.wav"'
        
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/wav",
            headers=headers
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")

@app.post("/tts", response_model=TTSResponse)
async def tts_post(request: TTSRequest):
    """Generate speech from text (POST endpoint with JSON response)"""
    try:
        # Generate audio
        audio_data = text_to_speech(
            text=request.text,
            speaker_id=request.speaker_id,
            language=request.language,
            emotion=request.emotion,
            speed=request.speed
        )
        
        # Encode audio as base64 for JSON response
        import base64
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        return TTSResponse(
            success=True,
            message="Speech generated successfully",
            audio_base64=audio_base64,
            duration=len(audio_data) / 16000 / 2  # Rough estimate
        )
        
    except Exception as e:
        return TTSResponse(
            success=False,
            message=f"TTS generation failed: {str(e)}",
            audio_base64=None,
            duration=None
        )

@app.post("/tts-post-audio")
async def tts_post_audio(request: TTSRequest):
    """Generate speech from text (POST endpoint returning audio directly)"""
    try:
        # Generate audio
        audio_data = text_to_speech(
            text=request.text,
            speaker_id=request.speaker_id,
            language=request.language,
            emotion=request.emotion,
            speed=request.speed
        )
        
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/wav"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")

# For Vercel deployment
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
