from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from gtts import gTTS
import io
import os
import tempfile
import logging

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
logging.basicConfig(level=logging.INFO)

# Supported languages and their corresponding voice IDs
SUPPORTED_VOICES = {
    # English Voices
    "en-US": ["en-US-Standard-A", "en-US-Standard-B", "en-US-Standard-C", "en-US-Standard-D",
              "en-US-Standard-E", "en-US-Standard-F", "en-US-Standard-G", "en-US-Standard-H",
              "en-US-Standard-I", "en-US-Standard-J", "en-US-Wavenet-A", "en-US-Wavenet-B",
              "en-US-Wavenet-C", "en-US-Wavenet-D", "en-US-Wavenet-E", "en-US-Wavenet-F",
              "en-US-Wavenet-G", "en-US-Wavenet-H", "en-US-Wavenet-I", "en-US-Wavenet-J"],
    
    # British English
    "en-GB": ["en-GB-Standard-A", "en-GB-Standard-B", "en-GB-Standard-C", "en-GB-Standard-D",
              "en-GB-Wavenet-A", "en-GB-Wavenet-B", "en-GB-Wavenet-C", "en-GB-Wavenet-D"],
    
    # Australian English
    "en-AU": ["en-AU-Standard-A", "en-AU-Standard-B", "en-AU-Standard-C", "en-AU-Standard-D",
              "en-AU-Wavenet-A", "en-AU-Wavenet-B", "en-AU-Wavenet-C", "en-AU-Wavenet-D"],
    
    # Indian English
    "en-IN": ["en-IN-Standard-A", "en-IN-Standard-B", "en-IN-Standard-C", "en-IN-Standard-D",
              "en-IN-Wavenet-A", "en-IN-Wavenet-B", "en-IN-Wavenet-C", "en-IN-Wavenet-D"],
    
    # Spanish
    "es-ES": ["es-ES-Standard-A", "es-ES-Standard-B", "es-ES-Standard-C", "es-ES-Standard-D",
              "es-ES-Wavenet-A", "es-ES-Wavenet-B", "es-ES-Wavenet-C", "es-ES-Wavenet-D"],
    
    # French
    "fr-FR": ["fr-FR-Standard-A", "fr-FR-Standard-B", "fr-FR-Standard-C", "fr-FR-Standard-D",
              "fr-FR-Standard-E", "fr-FR-Wavenet-A", "fr-FR-Wavenet-B", "fr-FR-Wavenet-C",
              "fr-FR-Wavenet-D", "fr-FR-Wavenet-E"],
    
    # German
    "de-DE": ["de-DE-Standard-A", "de-DE-Standard-B", "de-DE-Standard-C", "de-DE-Standard-D",
              "de-DE-Standard-E", "de-DE-Standard-F", "de-DE-Wavenet-A", "de-DE-Wavenet-B",
              "de-DE-Wavenet-C", "de-DE-Wavenet-D", "de-DE-Wavenet-E", "de-DE-Wavenet-F"],
    
    # Italian
    "it-IT": ["it-IT-Standard-A", "it-IT-Standard-B", "it-IT-Standard-C", "it-IT-Standard-D",
              "it-IT-Wavenet-A", "it-IT-Wavenet-B", "it-IT-Wavenet-C", "it-IT-Wavenet-D"],
    
    # Portuguese
    "pt-BR": ["pt-BR-Standard-A", "pt-BR-Standard-B", "pt-BR-Standard-C", "pt-BR-Wavenet-A",
              "pt-BR-Wavenet-B", "pt-BR-Wavenet-C"],
    
    # Russian
    "ru-RU": ["ru-RU-Standard-A", "ru-RU-Standard-B", "ru-RU-Standard-C", "ru-RU-Standard-D",
              "ru-RU-Standard-E", "ru-RU-Wavenet-A", "ru-RU-Wavenet-B", "ru-RU-Wavenet-C",
              "ru-RU-Wavenet-D", "ru-RU-Wavenet-E"],
    
    # Japanese
    "ja-JP": ["ja-JP-Standard-A", "ja-JP-Standard-B", "ja-JP-Standard-C", "ja-JP-Standard-D",
              "ja-JP-Wavenet-A", "ja-JP-Wavenet-B", "ja-JP-Wavenet-C", "ja-JP-Wavenet-D"],
    
    # Korean
    "ko-KR": ["ko-KR-Standard-A", "ko-KR-Standard-B", "ko-KR-Standard-C", "ko-KR-Standard-D",
              "ko-KR-Wavenet-A", "ko-KR-Wavenet-B", "ko-KR-Wavenet-C", "ko-KR-Wavenet-D"],
    
    # Chinese
    "zh-CN": ["zh-CN-Standard-A", "zh-CN-Standard-B", "zh-CN-Standard-C", "zh-CN-Standard-D",
              "zh-CN-Wavenet-A", "zh-CN-Wavenet-B", "zh-CN-Wavenet-C", "zh-CN-Wavenet-D"],
    
    # Arabic
    "ar-XA": ["ar-XA-Standard-A", "ar-XA-Standard-B", "ar-XA-Standard-C", "ar-XA-Standard-D",
              "ar-XA-Wavenet-A", "ar-XA-Wavenet-B", "ar-XA-Wavenet-C", "ar-XA-Wavenet-D"],
    
    # Hindi
    "hi-IN": ["hi-IN-Standard-A", "hi-IN-Standard-B", "hi-IN-Standard-C", "hi-IN-Standard-D",
              "hi-IN-Wavenet-A", "hi-IN-Wavenet-B", "hi-IN-Wavenet-C", "hi-IN-Wavenet-D"],
}

# Default voice mapping for your existing voice IDs
VOICE_MAPPING = {
    # Map your existing voice IDs to Google TTS languages
    "Brian": "en-GB-Standard-B",
    "Amy": "en-GB-Standard-A",
    "Emma": "en-GB-Standard-C",
    "Joanna": "en-US-Standard-C",
    "Salli": "en-US-Standard-J",
    "Matthew": "en-US-Standard-D",
    "Kimberly": "en-US-Standard-F",
    "Kendra": "en-US-Standard-G",
    "Justin": "en-US-Standard-E",
    "Joey": "en-US-Standard-H",
    "Ivy": "en-US-Standard-I",
    "Nicole": "en-AU-Standard-A",
    "Russell": "en-AU-Standard-B",
    "Aditi": "en-IN-Standard-A",
    "Raveena": "en-IN-Standard-B",
    "Mizuki": "ja-JP-Standard-A",
    "Takumi": "ja-JP-Standard-D",
    "Seoyeon": "ko-KR-Standard-A",
    "Celine": "fr-FR-Standard-A",
    "Lea": "fr-FR-Standard-C",
    "Mathieu": "fr-FR-Standard-D",
    "Hans": "de-DE-Standard-B",
    "Marlene": "de-DE-Standard-A",
    "Vicki": "de-DE-Standard-C",
    "Giorgio": "it-IT-Standard-B",
    "Bianca": "it-IT-Standard-A",
    "Carla": "it-IT-Standard-C",
    "Ricardo": "pt-BR-Standard-B",
    "Vitoria": "pt-BR-Standard-A",
    "Camila": "pt-BR-Standard-C",
    "Enrique": "es-ES-Standard-B",
    "Conchita": "es-ES-Standard-C",
    "Lucia": "es-ES-Standard-A",
    "Penelope": "es-US-Standard-A",
    "Lupe": "es-US-Standard-B",
    "Miguel": "es-US-Standard-C",
    "Mia": "es-US-Standard-D",
    "Maxim": "ru-RU-Standard-B",
    "Tatyana": "ru-RU-Standard-A",
    "Filiz": "tr-TR-Standard-A",
    "Zeina": "ar-XA-Standard-A",
    "Zhiyu": "zh-CN-Standard-A",
}

def get_language_from_voice(voice_id):
    """Extract language from voice ID"""
    # Check if it's a Google voice ID
    if "-Standard-" in voice_id or "-Wavenet-" in voice_id:
        # Extract language code (e.g., "en-US" from "en-US-Standard-A")
        parts = voice_id.split("-")
        if len(parts) >= 2:
            return f"{parts[0]}-{parts[1]}"
    
    # Check voice mapping
    if voice_id in VOICE_MAPPING:
        google_voice = VOICE_MAPPING[voice_id]
        parts = google_voice.split("-")
        if len(parts) >= 2:
            return f"{parts[0]}-{parts[1]}"
    
    # Default to English US
    return "en-US"

@app.route('/api/tts', methods=['POST', 'GET'])
def text_to_speech():
    try:
        if request.method == 'GET':
            text = request.args.get('text', '')
            voice = request.args.get('voice', 'en-US-Standard-A')
        else:
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided"}), 400
            text = data.get('text', '')
            voice = data.get('voice', 'en-US-Standard-A')
        
        if not text:
            return jsonify({"error": "No text provided"}), 400
        
        # Validate text length (Google TTS has limits)
        if len(text) > 5000:  # Increased limit
            return jsonify({"error": "Text too long. Maximum 5000 characters."}), 400
        
        # Get language from voice
        lang = get_language_from_voice(voice)
        
        # If voice is in our mapping, use the mapped Google voice
        if voice in VOICE_MAPPING:
            google_voice = VOICE_MAPPING[voice]
        elif "-Standard-" in voice or "-Wavenet-" in voice:
            google_voice = voice
        else:
            # Default to a standard voice for the language
            google_voice = f"{lang}-Standard-A"
        
        logging.info(f"Converting text to speech: {len(text)} chars, voice: {google_voice}, lang: {lang}")
        
        # Generate speech using gTTS
        tts = gTTS(text=text, lang=lang, tld='com')
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        tts.save(temp_file.name)
        temp_file.close()
        
        # Read file content
        with open(temp_file.name, 'rb') as f:
            audio_data = f.read()
        
        # Clean up temp file
        os.unlink(temp_file.name)
        
        # Return as base64 encoded or direct binary
        return jsonify({
            "success": True,
            "audio_data": audio_data.hex(),  # Convert to hex for JSON transmission
            "size": len(audio_data),
            "voice": google_voice,
            "language": lang
        })
        
    except Exception as e:
        logging.error(f"Error in TTS conversion: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/voices', methods=['GET'])
def get_voices():
    """Return all available voices"""
    try:
        all_voices = []
        
        # Add Google TTS voices
        for lang_code, voice_list in SUPPORTED_VOICES.items():
            for voice_id in voice_list:
                # Extract gender from voice ID (last letter: A, C, E, G are typically female)
                last_char = voice_id[-1]
                gender = "female" if last_char in ['A', 'C', 'E', 'G', 'I'] else "male"
                
                # Extract voice type
                voice_type = "Standard" if "Standard" in voice_id else "Wavenet"
                
                # Create avatar based on gender and language
                if gender == "male":
                    avatar = "👨" + get_language_flag(lang_code)
                else:
                    avatar = "👩" + get_language_flag(lang_code)
                
                all_voices.append({
                    "id": voice_id,
                    "name": voice_id.replace("-", " "),
                    "gender": gender,
                    "avatar": avatar,
                    "language": get_language_name(lang_code),
                    "lang_code": lang_code,
                    "type": voice_type,
                    "provider": "google"
                })
        
        # Add mapped voices from your existing system
        for voice_id, google_voice in VOICE_MAPPING.items():
            lang_code = get_language_from_voice(voice_id)
            gender = "female" if voice_id in ["Amy", "Emma", "Joanna", "Salli", "Kimberly", 
                                            "Kendra", "Ivy", "Nicole", "Aditi", "Raveena",
                                            "Mizuki", "Seoyeon", "Celine", "Lea", "Marlene",
                                            "Vicki", "Bianca", "Carla", "Vitoria", "Camila",
                                            "Conchita", "Lucia", "Penelope", "Lupe", "Mia",
                                            "Tatyana", "Filiz", "Zeina", "Zhiyu"] else "male"
            
            all_voices.append({
                "id": voice_id,
                "name": voice_id,
                "gender": gender,
                "avatar": "👩" if gender == "female" else "👨",
                "language": get_language_name(lang_code),
                "lang_code": lang_code,
                "type": "Standard",
                "provider": "google_mapped"
            })
        
        return jsonify({
            "success": True,
            "count": len(all_voices),
            "voices": all_voices
        })
        
    except Exception as e:
        logging.error(f"Error getting voices: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/test', methods=['GET'])
def test_api():
    """Test endpoint to verify API is working"""
    return jsonify({
        "status": "active",
        "service": "Google Text-to-Speech API",
        "version": "1.0.0",
        "endpoints": [
            "/api/tts - POST/GET - Convert text to speech",
            "/api/voices - GET - Get available voices",
            "/api/test - GET - Test endpoint"
        ]
    })

def get_language_flag(lang_code):
    """Get flag emoji for language code"""
    flag_map = {
        "en-US": "🇺🇸", "en-GB": "🇬🇧", "en-AU": "🇦🇺", "en-IN": "🇮🇳",
        "es-ES": "🇪🇸", "es-US": "🇺🇸", "fr-FR": "🇫🇷", "de-DE": "🇩🇪",
        "it-IT": "🇮🇹", "pt-BR": "🇧🇷", "ru-RU": "🇷🇺", "ja-JP": "🇯🇵",
        "ko-KR": "🇰🇷", "zh-CN": "🇨🇳", "ar-XA": "🇸🇦", "hi-IN": "🇮🇳",
        "tr-TR": "🇹🇷"
    }
    return flag_map.get(lang_code, "🌐")

def get_language_name(lang_code):
    """Get full language name from code"""
    lang_names = {
        "en-US": "US English", "en-GB": "British English", 
        "en-AU": "Australian English", "en-IN": "Indian English",
        "es-ES": "Spanish (Spain)", "es-US": "Spanish (US)",
        "fr-FR": "French", "de-DE": "German", "it-IT": "Italian",
        "pt-BR": "Portuguese (Brazil)", "ru-RU": "Russian",
        "ja-JP": "Japanese", "ko-KR": "Korean", "zh-CN": "Chinese",
        "ar-XA": "Arabic", "hi-IN": "Hindi", "tr-TR": "Turkish"
    }
    return lang_names.get(lang_code, lang_code)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)