from fastapi import FastAPI
from fastapi.responses import FileResponse
from TTS.api import TTS
import uuid
import os
import uvicorn

app = FastAPI()

# Load model once (CPU-friendly model)
tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False)

OUTPUT_DIR = "audio"
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.get("/tts")
def text_to_speech(text: str):
    filename = f"{uuid.uuid4()}.wav"
    path = os.path.join(OUTPUT_DIR, filename)

    tts.tts_to_file(text=text, file_path=path)

    return FileResponse(
        path,
        media_type="audio/wav",
        filename=filename
    )

# Only run if executed directly (not imported)
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
