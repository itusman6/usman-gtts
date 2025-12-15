# Install and run
pip install edge-tts fastapi uvicorn
# Create api.py with Edge TTS code above
uvicorn api:app --host 0.0.0.0 --port 8000
