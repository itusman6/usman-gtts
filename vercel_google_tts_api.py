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

# Complete voice list with metadata
GOOGLE_VOICES = [
    # US English Voices
    {'id': 'en-US-Standard-A', 'name': 'US English Standard A', 'gender': 'female', 'avatar': '👩🇺🇸', 'language': 'US English', 'type': 'standard'},
    {'id': 'en-US-Standard-B', 'name': 'US English Standard B', 'gender': 'male', 'avatar': '👨🇺🇸', 'language': 'US English', 'type': 'standard'},
    {'id': 'en-US-Standard-C', 'name': 'US English Standard C', 'gender': 'female', 'avatar': '👩🇺🇸', 'language': 'US English', 'type': 'standard'},
    {'id': 'en-US-Standard-D', 'name': 'US English Standard D', 'gender': 'male', 'avatar': '👨🇺🇸', 'language': 'US English', 'type': 'standard'},
    {'id': 'en-US-Standard-E', 'name': 'US English Standard E', 'gender': 'female', 'avatar': '👩🇺🇸', 'language': 'US English', 'type': 'standard'},
    {'id': 'en-US-Standard-F', 'name': 'US English Standard F', 'gender': 'female', 'avatar': '👩🇺🇸', 'language': 'US English', 'type': 'standard'},
    {'id': 'en-US-Standard-G', 'name': 'US English Standard G', 'gender': 'female', 'avatar': '👩🇺🇸', 'language': 'US English', 'type': 'standard'},
    {'id': 'en-US-Standard-H', 'name': 'US English Standard H', 'gender': 'female', 'avatar': '👩🇺🇸', 'language': 'US English', 'type': 'standard'},
    {'id': 'en-US-Standard-I', 'name': 'US English Standard I', 'gender': 'male', 'avatar': '👨🇺🇸', 'language': 'US English', 'type': 'standard'},
    {'id': 'en-US-Standard-J', 'name': 'US English Standard J', 'gender': 'male', 'avatar': '👨🇺🇸', 'language': 'US English', 'type': 'standard'},
    
    # US English Wavenet (Premium)
    {'id': 'en-US-Wavenet-A', 'name': 'US English Wavenet A', 'gender': 'female', 'avatar': '👩🌟🇺🇸', 'language': 'US English', 'type': 'wavenet'},
    {'id': 'en-US-Wavenet-B', 'name': 'US English Wavenet B', 'gender': 'male', 'avatar': '👨🌟🇺🇸', 'language': 'US English', 'type': 'wavenet'},
    {'id': 'en-US-Wavenet-C', 'name': 'US English Wavenet C', 'gender': 'female', 'avatar': '👩🌟🇺🇸', 'language': 'US English', 'type': 'wavenet'},
    {'id': 'en-US-Wavenet-D', 'name': 'US English Wavenet D', 'gender': 'male', 'avatar': '👨🌟🇺🇸', 'language': 'US English', 'type': 'wavenet'},
    {'id': 'en-US-Wavenet-E', 'name': 'US English Wavenet E', 'gender': 'female', 'avatar': '👩🌟🇺🇸', 'language': 'US English', 'type': 'wavenet'},
    {'id': 'en-US-Wavenet-F', 'name': 'US English Wavenet F', 'gender': 'female', 'avatar': '👩🌟🇺🇸', 'language': 'US English', 'type': 'wavenet'},
    {'id': 'en-US-Wavenet-G', 'name': 'US English Wavenet G', 'gender': 'female', 'avatar': '👩🌟🇺🇸', 'language': 'US English', 'type': 'wavenet'},
    {'id': 'en-US-Wavenet-H', 'name': 'US English Wavenet H', 'gender': 'female', 'avatar': '👩🌟🇺🇸', 'language': 'US English', 'type': 'wavenet'},
    {'id': 'en-US-Wavenet-I', 'name': 'US English Wavenet I', 'gender': 'male', 'avatar': '👨🌟🇺🇸', 'language': 'US English', 'type': 'wavenet'},
    {'id': 'en-US-Wavenet-J', 'name': 'US English Wavenet J', 'gender': 'male', 'avatar': '👨🌟🇺🇸', 'language': 'US English', 'type': 'wavenet'},
    
    # British English
    {'id': 'en-GB-Standard-A', 'name': 'UK English Standard A', 'gender': 'female', 'avatar': '👩🇬🇧', 'language': 'British English', 'type': 'standard'},
    {'id': 'en-GB-Standard-B', 'name': 'UK English Standard B', 'gender': 'male', 'avatar': '👨🇬🇧', 'language': 'British English', 'type': 'standard'},
    {'id': 'en-GB-Standard-C', 'name': 'UK English Standard C', 'gender': 'female', 'avatar': '👩🇬🇧', 'language': 'British English', 'type': 'standard'},
    {'id': 'en-GB-Standard-D', 'name': 'UK English Standard D', 'gender': 'male', 'avatar': '👨🇬🇧', 'language': 'British English', 'type': 'standard'},
    {'id': 'en-GB-Wavenet-A', 'name': 'UK English Wavenet A', 'gender': 'female', 'avatar': '👩🌟🇬🇧', 'language': 'British English', 'type': 'wavenet'},
    {'id': 'en-GB-Wavenet-B', 'name': 'UK English Wavenet B', 'gender': 'male', 'avatar': '👨🌟🇬🇧', 'language': 'British English', 'type': 'wavenet'},
    {'id': 'en-GB-Wavenet-C', 'name': 'UK English Wavenet C', 'gender': 'female', 'avatar': '👩🌟🇬🇧', 'language': 'British English', 'type': 'wavenet'},
    {'id': 'en-GB-Wavenet-D', 'name': 'UK English Wavenet D', 'gender': 'male', 'avatar': '👨🌟🇬🇧', 'language': 'British English', 'type': 'wavenet'},
    
    # Australian English
    {'id': 'en-AU-Standard-A', 'name': 'Australian English Standard A', 'gender': 'female', 'avatar': '👩🇦🇺', 'language': 'Australian English', 'type': 'standard'},
    {'id': 'en-AU-Standard-B', 'name': 'Australian English Standard B', 'gender': 'male', 'avatar': '👨🇦🇺', 'language': 'Australian English', 'type': 'standard'},
    {'id': 'en-AU-Standard-C', 'name': 'Australian English Standard C', 'gender': 'female', 'avatar': '👩🇦🇺', 'language': 'Australian English', 'type': 'standard'},
    {'id': 'en-AU-Standard-D', 'name': 'Australian English Standard D', 'gender': 'male', 'avatar': '👨🇦🇺', 'language': 'Australian English', 'type': 'standard'},
    {'id': 'en-AU-Wavenet-A', 'name': 'Australian English Wavenet A', 'gender': 'female', 'avatar': '👩🌟🇦🇺', 'language': 'Australian English', 'type': 'wavenet'},
    {'id': 'en-AU-Wavenet-B', 'name': 'Australian English Wavenet B', 'gender': 'male', 'avatar': '👨🌟🇦🇺', 'language': 'Australian English', 'type': 'wavenet'},
    {'id': 'en-AU-Wavenet-C', 'name': 'Australian English Wavenet C', 'gender': 'female', 'avatar': '👩🌟🇦🇺', 'language': 'Australian English', 'type': 'wavenet'},
    {'id': 'en-AU-Wavenet-D', 'name': 'Australian English Wavenet D', 'gender': 'male', 'avatar': '👨🌟🇦🇺', 'language': 'Australian English', 'type': 'wavenet'},
    
    # Indian English
    {'id': 'en-IN-Standard-A', 'name': 'Indian English Standard A', 'gender': 'female', 'avatar': '👩🇮🇳', 'language': 'Indian English', 'type': 'standard'},
    {'id': 'en-IN-Standard-B', 'name': 'Indian English Standard B', 'gender': 'male', 'avatar': '👨🇮🇳', 'language': 'Indian English', 'type': 'standard'},
    {'id': 'en-IN-Standard-C', 'name': 'Indian English Standard C', 'gender': 'male', 'avatar': '👨🇮🇳', 'language': 'Indian English', 'type': 'standard'},
    {'id': 'en-IN-Standard-D', 'name': 'Indian English Standard D', 'gender': 'female', 'avatar': '👩🇮🇳', 'language': 'Indian English', 'type': 'standard'},
    {'id': 'en-IN-Wavenet-A', 'name': 'Indian English Wavenet A', 'gender': 'female', 'avatar': '👩🌟🇮🇳', 'language': 'Indian English', 'type': 'wavenet'},
    {'id': 'en-IN-Wavenet-B', 'name': 'Indian English Wavenet B', 'gender': 'male', 'avatar': '👨🌟🇮🇳', 'language': 'Indian English', 'type': 'wavenet'},
    {'id': 'en-IN-Wavenet-C', 'name': 'Indian English Wavenet C', 'gender': 'male', 'avatar': '👨🌟🇮🇳', 'language': 'Indian English', 'type': 'wavenet'},
    {'id': 'en-IN-Wavenet-D', 'name': 'Indian English Wavenet D', 'gender': 'female', 'avatar': '👩🌟🇮🇳', 'language': 'Indian English', 'type': 'wavenet'},
    
    # Spanish
    {'id': 'es-ES-Standard-A', 'name': 'Spanish Standard A', 'gender': 'female', 'avatar': '👩🇪🇸', 'language': 'Spanish (Spain)', 'type': 'standard'},
    {'id': 'es-ES-Standard-B', 'name': 'Spanish Standard B', 'gender': 'male', 'avatar': '👨🇪🇸', 'language': 'Spanish (Spain)', 'type': 'standard'},
    {'id': 'es-ES-Standard-C', 'name': 'Spanish Standard C', 'gender': 'female', 'avatar': '👩🇪🇸', 'language': 'Spanish (Spain)', 'type': 'standard'},
    {'id': 'es-ES-Standard-D', 'name': 'Spanish Standard D', 'gender': 'male', 'avatar': '👨🇪🇸', 'language': 'Spanish (Spain)', 'type': 'standard'},
    {'id': 'es-US-Standard-A', 'name': 'US Spanish Standard A', 'gender': 'female', 'avatar': '👩🇺🇸', 'language': 'Spanish (US)', 'type': 'standard'},
    {'id': 'es-US-Standard-B', 'name': 'US Spanish Standard B', 'gender': 'male', 'avatar': '👨🇺🇸', 'language': 'Spanish (US)', 'type': 'standard'},
    {'id': 'es-US-Standard-C', 'name': 'US Spanish Standard C', 'gender': 'male', 'avatar': '👨🇺🇸', 'language': 'Spanish (US)', 'type': 'standard'},
    
    # French
    {'id': 'fr-FR-Standard-A', 'name': 'French Standard A', 'gender': 'female', 'avatar': '👩🇫🇷', 'language': 'French', 'type': 'standard'},
    {'id': 'fr-FR-Standard-B', 'name': 'French Standard B', 'gender': 'male', 'avatar': '👨🇫🇷', 'language': 'French', 'type': 'standard'},
    {'id': 'fr-FR-Standard-C', 'name': 'French Standard C', 'gender': 'female', 'avatar': '👩🇫🇷', 'language': 'French', 'type': 'standard'},
    {'id': 'fr-FR-Standard-D', 'name': 'French Standard D', 'gender': 'male', 'avatar': '👨🇫🇷', 'language': 'French', 'type': 'standard'},
    {'id': 'fr-FR-Standard-E', 'name': 'French Standard E', 'gender': 'female', 'avatar': '👩🇫🇷', 'language': 'French', 'type': 'standard'},
    
    # German
    {'id': 'de-DE-Standard-A', 'name': 'German Standard A', 'gender': 'female', 'avatar': '👩🇩🇪', 'language': 'German', 'type': 'standard'},
    {'id': 'de-DE-Standard-B', 'name': 'German Standard B', 'gender': 'male', 'avatar': '👨🇩🇪', 'language': 'German', 'type': 'standard'},
    {'id': 'de-DE-Standard-C', 'name': 'German Standard C', 'gender': 'female', 'avatar': '👩🇩🇪', 'language': 'German', 'type': 'standard'},
    {'id': 'de-DE-Standard-D', 'name': 'German Standard D', 'gender': 'male', 'avatar': '👨🇩🇪', 'language': 'German', 'type': 'standard'},
    {'id': 'de-DE-Standard-E', 'name': 'German Standard E', 'gender': 'male', 'avatar': '👨🇩🇪', 'language': 'German', 'type': 'standard'},
    {'id': 'de-DE-Standard-F', 'name': 'German Standard F', 'gender': 'female', 'avatar': '👩🇩🇪', 'language': 'German', 'type': 'standard'},
    
    # Italian
    {'id': 'it-IT-Standard-A', 'name': 'Italian Standard A', 'gender': 'female', 'avatar': '👩🇮🇹', 'language': 'Italian', 'type': 'standard'},
    {'id': 'it-IT-Standard-B', 'name': 'Italian Standard B', 'gender': 'female', 'avatar': '👩🇮🇹', 'language': 'Italian', 'type': 'standard'},
    {'id': 'it-IT-Standard-C', 'name': 'Italian Standard C', 'gender': 'male', 'avatar': '👨🇮🇹', 'language': 'Italian', 'type': 'standard'},
    {'id': 'it-IT-Standard-D', 'name': 'Italian Standard D', 'gender': 'male', 'avatar': '👨🇮🇹', 'language': 'Italian', 'type': 'standard'},
    
    # Portuguese
    {'id': 'pt-BR-Standard-A', 'name': 'Portuguese Standard A', 'gender': 'female', 'avatar': '👩🇧🇷', 'language': 'Portuguese (Brazil)', 'type': 'standard'},
    {'id': 'pt-BR-Standard-B', 'name': 'Portuguese Standard B', 'gender': 'male', 'avatar': '👨🇧🇷', 'language': 'Portuguese (Brazil)', 'type': 'standard'},
    {'id': 'pt-BR-Standard-C', 'name': 'Portuguese Standard C', 'gender': 'female', 'avatar': '👩🇧🇷', 'language': 'Portuguese (Brazil)', 'type': 'standard'},
    {'id': 'pt-PT-Standard-A', 'name': 'Portuguese Standard A', 'gender': 'female', 'avatar': '👩🇵🇹', 'language': 'Portuguese (Portugal)', 'type': 'standard'},
    {'id': 'pt-PT-Standard-B', 'name': 'Portuguese Standard B', 'gender': 'male', 'avatar': '👨🇵🇹', 'language': 'Portuguese (Portugal)', 'type': 'standard'},
    {'id': 'pt-PT-Standard-C', 'name': 'Portuguese Standard C', 'gender': 'male', 'avatar': '👨🇵🇹', 'language': 'Portuguese (Portugal)', 'type': 'standard'},
    {'id': 'pt-PT-Standard-D', 'name': 'Portuguese Standard D', 'gender': 'female', 'avatar': '👩🇵🇹', 'language': 'Portuguese (Portugal)', 'type': 'standard'},
    
    # Russian
    {'id': 'ru-RU-Standard-A', 'name': 'Russian Standard A', 'gender': 'female', 'avatar': '👩🇷🇺', 'language': 'Russian', 'type': 'standard'},
    {'id': 'ru-RU-Standard-B', 'name': 'Russian Standard B', 'gender': 'male', 'avatar': '👨🇷🇺', 'language': 'Russian', 'type': 'standard'},
    {'id': 'ru-RU-Standard-C', 'name': 'Russian Standard C', 'gender': 'female', 'avatar': '👩🇷🇺', 'language': 'Russian', 'type': 'standard'},
    {'id': 'ru-RU-Standard-D', 'name': 'Russian Standard D', 'gender': 'male', 'avatar': '👨🇷🇺', 'language': 'Russian', 'type': 'standard'},
    {'id': 'ru-RU-Standard-E', 'name': 'Russian Standard E', 'gender': 'female', 'avatar': '👩🇷🇺', 'language': 'Russian', 'type': 'standard'},
    
    # Japanese
    {'id': 'ja-JP-Standard-A', 'name': 'Japanese Standard A', 'gender': 'female', 'avatar': '👩🇯🇵', 'language': 'Japanese', 'type': 'standard'},
    {'id': 'ja-JP-Standard-B', 'name': 'Japanese Standard B', 'gender': 'female', 'avatar': '👩🇯🇵', 'language': 'Japanese', 'type': 'standard'},
    {'id': 'ja-JP-Standard-C', 'name': 'Japanese Standard C', 'gender': 'male', 'avatar': '👨🇯🇵', 'language': 'Japanese', 'type': 'standard'},
    {'id': 'ja-JP-Standard-D', 'name': 'Japanese Standard D', 'gender': 'male', 'avatar': '👨🇯🇵', 'language': 'Japanese', 'type': 'standard'},
    
    # Korean
    {'id': 'ko-KR-Standard-A', 'name': 'Korean Standard A', 'gender': 'female', 'avatar': '👩🇰🇷', 'language': 'Korean', 'type': 'standard'},
    {'id': 'ko-KR-Standard-B', 'name': 'Korean Standard B', 'gender': 'female', 'avatar': '👩🇰🇷', 'language': 'Korean', 'type': 'standard'},
    {'id': 'ko-KR-Standard-C', 'name': 'Korean Standard C', 'gender': 'male', 'avatar': '👨🇰🇷', 'language': 'Korean', 'type': 'standard'},
    {'id': 'ko-KR-Standard-D', 'name': 'Korean Standard D', 'gender': 'male', 'avatar': '👨🇰🇷', 'language': 'Korean', 'type': 'standard'},
    
    # Chinese
    {'id': 'zh-CN-Standard-A', 'name': 'Chinese Standard A', 'gender': 'female', 'avatar': '👩🇨🇳', 'language': 'Chinese (Mandarin)', 'type': 'standard'},
    {'id': 'zh-CN-Standard-B', 'name': 'Chinese Standard B', 'gender': 'male', 'avatar': '👨🇨🇳', 'language': 'Chinese (Mandarin)', 'type': 'standard'},
    {'id': 'zh-CN-Standard-C', 'name': 'Chinese Standard C', 'gender': 'male', 'avatar': '👨🇨🇳', 'language': 'Chinese (Mandarin)', 'type': 'standard'},
    {'id': 'zh-CN-Standard-D', 'name': 'Chinese Standard D', 'gender': 'female', 'avatar': '👩🇨🇳', 'language': 'Chinese (Mandarin)', 'type': 'standard'},
    
    # Arabic
    {'id': 'ar-XA-Standard-A', 'name': 'Arabic Standard A', 'gender': 'female', 'avatar': '👩🇸🇦', 'language': 'Arabic', 'type': 'standard'},
    {'id': 'ar-XA-Standard-B', 'name': 'Arabic Standard B', 'gender': 'male', 'avatar': '👨🇸🇦', 'language': 'Arabic', 'type': 'standard'},
    {'id': 'ar-XA-Standard-C', 'name': 'Arabic Standard C', 'gender': 'male', 'avatar': '👨🇸🇦', 'language': 'Arabic', 'type': 'standard'},
    {'id': 'ar-XA-Standard-D', 'name': 'Arabic Standard D', 'gender': 'female', 'avatar': '👩🇸🇦', 'language': 'Arabic', 'type': 'standard'},
    
    # Hindi
    {'id': 'hi-IN-Standard-A', 'name': 'Hindi Standard A', 'gender': 'female', 'avatar': '👩🇮🇳', 'language': 'Hindi', 'type': 'standard'},
    {'id': 'hi-IN-Standard-B', 'name': 'Hindi Standard B', 'gender': 'male', 'avatar': '👨🇮🇳', 'language': 'Hindi', 'type': 'standard'},
    {'id': 'hi-IN-Standard-C', 'name': 'Hindi Standard C', 'gender': 'male', 'avatar': '👨🇮🇳', 'language': 'Hindi', 'type': 'standard'},
    {'id': 'hi-IN-Standard-D', 'name': 'Hindi Standard D', 'gender': 'female', 'avatar': '👩🇮🇳', 'language': 'Hindi', 'type': 'standard'},
    
    # Turkish
    {'id': 'tr-TR-Standard-A', 'name': 'Turkish Standard A', 'gender': 'female', 'avatar': '👩🇹🇷', 'language': 'Turkish', 'type': 'standard'},
    {'id': 'tr-TR-Standard-B', 'name': 'Turkish Standard B', 'gender': 'male', 'avatar': '👨🇹🇷', 'language': 'Turkish', 'type': 'standard'},
    {'id': 'tr-TR-Standard-C', 'name': 'Turkish Standard C', 'gender': 'female', 'avatar': '👩🇹🇷', 'language': 'Turkish', 'type': 'standard'},
    {'id': 'tr-TR-Standard-D', 'name': 'Turkish Standard D', 'gender': 'female', 'avatar': '👩🇹🇷', 'language': 'Turkish', 'type': 'standard'},
    {'id': 'tr-TR-Standard-E', 'name': 'Turkish Standard E', 'gender': 'male', 'avatar': '👨🇹🇷', 'language': 'Turkish', 'type': 'standard'},
    
    # Dutch
    {'id': 'nl-NL-Standard-A', 'name': 'Dutch Standard A', 'gender': 'female', 'avatar': '👩🇳🇱', 'language': 'Dutch', 'type': 'standard'},
    {'id': 'nl-NL-Standard-B', 'name': 'Dutch Standard B', 'gender': 'male', 'avatar': '👨🇳🇱', 'language': 'Dutch', 'type': 'standard'},
    {'id': 'nl-NL-Standard-C', 'name': 'Dutch Standard C', 'gender': 'male', 'avatar': '👨🇳🇱', 'language': 'Dutch', 'type': 'standard'},
    {'id': 'nl-NL-Standard-D', 'name': 'Dutch Standard D', 'gender': 'female', 'avatar': '👩🇳🇱', 'language': 'Dutch', 'type': 'standard'},
    {'id': 'nl-NL-Standard-E', 'name': 'Dutch Standard E', 'gender': 'female', 'avatar': '👩🇳🇱', 'language': 'Dutch', 'type': 'standard'},
    
    # Polish
    {'id': 'pl-PL-Standard-A', 'name': 'Polish Standard A', 'gender': 'female', 'avatar': '👩🇵🇱', 'language': 'Polish', 'type': 'standard'},
    {'id': 'pl-PL-Standard-B', 'name': 'Polish Standard B', 'gender': 'male', 'avatar': '👨🇵🇱', 'language': 'Polish', 'type': 'standard'},
    {'id': 'pl-PL-Standard-C', 'name': 'Polish Standard C', 'gender': 'male', 'avatar': '👨🇵🇱', 'language': 'Polish', 'type': 'standard'},
    {'id': 'pl-PL-Standard-D', 'name': 'Polish Standard D', 'gender': 'female', 'avatar': '👩🇵🇱', 'language': 'Polish', 'type': 'standard'},
    {'id': 'pl-PL-Standard-E', 'name': 'Polish Standard E', 'gender': 'female', 'avatar': '👩🇵🇱', 'language': 'Polish', 'type': 'standard'},
    
    # Swedish
    {'id': 'sv-SE-Standard-A', 'name': 'Swedish Standard A', 'gender': 'female', 'avatar': '👩🇸🇪', 'language': 'Swedish', 'type': 'standard'},
    {'id': 'sv-SE-Standard-B', 'name': 'Swedish Standard B', 'gender': 'female', 'avatar': '👩🇸🇪', 'language': 'Swedish', 'type': 'standard'},
    {'id': 'sv-SE-Standard-C', 'name': 'Swedish Standard C', 'gender': 'male', 'avatar': '👨🇸🇪', 'language': 'Swedish', 'type': 'standard'},
    {'id': 'sv-SE-Standard-D', 'name': 'Swedish Standard D', 'gender': 'male', 'avatar': '👨🇸🇪', 'language': 'Swedish', 'type': 'standard'},
    {'id': 'sv-SE-Standard-E', 'name': 'Swedish Standard E', 'gender': 'female', 'avatar': '👩🇸🇪', 'language': 'Swedish', 'type': 'standard'},
    
    # Norwegian
    {'id': 'nb-NO-Standard-A', 'name': 'Norwegian Standard A', 'gender': 'female', 'avatar': '👩🇳🇴', 'language': 'Norwegian', 'type': 'standard'},
    {'id': 'nb-NO-Standard-B', 'name': 'Norwegian Standard B', 'gender': 'male', 'avatar': '👨🇳🇴', 'language': 'Norwegian', 'type': 'standard'},
    {'id': 'nb-NO-Standard-C', 'name': 'Norwegian Standard C', 'gender': 'female', 'avatar': '👩🇳🇴', 'language': 'Norwegian', 'type': 'standard'},
    {'id': 'nb-NO-Standard-D', 'name': 'Norwegian Standard D', 'gender': 'male', 'avatar': '👨🇳🇴', 'language': 'Norwegian', 'type': 'standard'},
    {'id': 'nb-NO-Standard-E', 'name': 'Norwegian Standard E', 'gender': 'female', 'avatar': '👩🇳🇴', 'language': 'Norwegian', 'type': 'standard'},
    
    # Danish
    {'id': 'da-DK-Standard-A', 'name': 'Danish Standard A', 'gender': 'female', 'avatar': '👩🇩🇰', 'language': 'Danish', 'type': 'standard'},
    {'id': 'da-DK-Standard-C', 'name': 'Danish Standard C', 'gender': 'male', 'avatar': '👨🇩🇰', 'language': 'Danish', 'type': 'standard'},
    {'id': 'da-DK-Standard-D', 'name': 'Danish Standard D', 'gender': 'female', 'avatar': '👩🇩🇰', 'language': 'Danish', 'type': 'standard'},
    {'id': 'da-DK-Standard-E', 'name': 'Danish Standard E', 'gender': 'female', 'avatar': '👩🇩🇰', 'language': 'Danish', 'type': 'standard'},
]

# Create SUPPORTED_VOICES from GOOGLE_VOICES
def create_supported_voices():
    supported_voices = {}
    for voice in GOOGLE_VOICES:
        voice_id = voice['id']
        # Extract language code (e.g., "en-US" from "en-US-Standard-A")
        parts = voice_id.split("-")
        if len(parts) >= 2:
            lang_code = f"{parts[0]}-{parts[1]}"
            if lang_code not in supported_voices:
                supported_voices[lang_code] = []
            supported_voices[lang_code].append(voice_id)
    return supported_voices

SUPPORTED_VOICES = create_supported_voices()

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
        for voice in GOOGLE_VOICES:
            all_voices.append({
                "id": voice['id'],
                "name": voice['name'],
                "gender": voice['gender'],
                "avatar": voice['avatar'],
                "language": voice['language'],
                "lang_code": get_language_from_voice(voice['id']),
                "type": voice['type'],
                "provider": "google"
            })
        
        # Add mapped voices from your existing system
        legacy_voices = [
            {'id': 'Brian', 'name': 'Brian', 'gender': 'male', 'avatar': '👨🇬🇧', 'language': 'British English', 'mapped_to': 'en-GB-Standard-B'},
            {'id': 'Amy', 'name': 'Amy', 'gender': 'female', 'avatar': '👩🇬🇧', 'language': 'British English', 'mapped_to': 'en-GB-Standard-A'},
            {'id': 'Emma', 'name': 'Emma', 'gender': 'female', 'avatar': '👩🇬🇧', 'language': 'British English', 'mapped_to': 'en-GB-Standard-C'},
            {'id': 'Joanna', 'name': 'Joanna', 'gender': 'female', 'avatar': '👩🇺🇸', 'language': 'US English', 'mapped_to': 'en-US-Standard-C'},
            {'id': 'Salli', 'name': 'Salli', 'gender': 'female', 'avatar': '👩🇺🇸', 'language': 'US English', 'mapped_to': 'en-US-Standard-J'},
            {'id': 'Matthew', 'name': 'Matthew', 'gender': 'male', 'avatar': '👨🇺🇸', 'language': 'US English', 'mapped_to': 'en-US-Standard-D'},
            {'id': 'Kimberly', 'name': 'Kimberly', 'gender': 'female', 'avatar': '👩🇺🇸', 'language': 'US English', 'mapped_to': 'en-US-Standard-F'},
            {'id': 'Kendra', 'name': 'Kendra', 'gender': 'female', 'avatar': '👩🇺🇸', 'language': 'US English', 'mapped_to': 'en-US-Standard-G'},
            {'id': 'Justin', 'name': 'Justin', 'gender': 'male', 'avatar': '👨🇺🇸', 'language': 'US English', 'mapped_to': 'en-US-Standard-E'},
            {'id': 'Joey', 'name': 'Joey', 'gender': 'male', 'avatar': '👨🇺🇸', 'language': 'US English', 'mapped_to': 'en-US-Standard-H'},
            {'id': 'Ivy', 'name': 'Ivy', 'gender': 'female', 'avatar': '👩🇺🇸', 'language': 'US English', 'mapped_to': 'en-US-Standard-I'},
            {'id': 'Nicole', 'name': 'Nicole', 'gender': 'female', 'avatar': '👩🇦🇺', 'language': 'Australian English', 'mapped_to': 'en-AU-Standard-A'},
            {'id': 'Russell', 'name': 'Russell', 'gender': 'male', 'avatar': '👨🇦🇺', 'language': 'Australian English', 'mapped_to': 'en-AU-Standard-B'},
            {'id': 'Aditi', 'name': 'Aditi', 'gender': 'female', 'avatar': '👩🇮🇳', 'language': 'Indian English', 'mapped_to': 'en-IN-Standard-A'},
            {'id': 'Raveena', 'name': 'Raveena', 'gender': 'female', 'avatar': '👩🇮🇳', 'language': 'Indian English', 'mapped_to': 'en-IN-Standard-B'},
            {'id': 'Mizuki', 'name': 'Mizuki', 'gender': 'female', 'avatar': '👩🇯🇵', 'language': 'Japanese', 'mapped_to': 'ja-JP-Standard-A'},
            {'id': 'Takumi', 'name': 'Takumi', 'gender': 'male', 'avatar': '👨🇯🇵', 'language': 'Japanese', 'mapped_to': 'ja-JP-Standard-D'},
            {'id': 'Seoyeon', 'name': 'Seoyeon', 'gender': 'female', 'avatar': '👩🇰🇷', 'language': 'Korean', 'mapped_to': 'ko-KR-Standard-A'},
            {'id': 'Celine', 'name': 'Celine', 'gender': 'female', 'avatar': '👩🇫🇷', 'language': 'French', 'mapped_to': 'fr-FR-Standard-A'},
            {'id': 'Lea', 'name': 'Lea', 'gender': 'female', 'avatar': '👩🇫🇷', 'language': 'French', 'mapped_to': 'fr-FR-Standard-C'},
            {'id': 'Mathieu', 'name': 'Mathieu', 'gender': 'male', 'avatar': '👨🇫🇷', 'language': 'French', 'mapped_to': 'fr-FR-Standard-D'},
            {'id': 'Hans', 'name': 'Hans', 'gender': 'male', 'avatar': '👨🇩🇪', 'language': 'German', 'mapped_to': 'de-DE-Standard-B'},
            {'id': 'Marlene', 'name': 'Marlene', 'gender': 'female', 'avatar': '👩🇩🇪', 'language': 'German', 'mapped_to': 'de-DE-Standard-A'},
            {'id': 'Vicki', 'name': 'Vicki', 'gender': 'female', 'avatar': '👩🇩🇪', 'language': 'German', 'mapped_to': 'de-DE-Standard-C'},
            {'id': 'Giorgio', 'name': 'Giorgio', 'gender': 'male', 'avatar': '👨🇮🇹', 'language': 'Italian', 'mapped_to': 'it-IT-Standard-B'},
            {'id': 'Bianca', 'name': 'Bianca', 'gender': 'female', 'avatar': '👩🇮🇹', 'language': 'Italian', 'mapped_to': 'it-IT-Standard-A'},
            {'id': 'Carla', 'name': 'Carla', 'gender': 'female', 'avatar': '👩🇮🇹', 'language': 'Italian', 'mapped_to': 'it-IT-Standard-C'},
            {'id': 'Ricardo', 'name': 'Ricardo', 'gender': 'male', 'avatar': '👨🇧🇷', 'language': 'Portuguese', 'mapped_to': 'pt-BR-Standard-B'},
            {'id': 'Vitoria', 'name': 'Vitoria', 'gender': 'female', 'avatar': '👩🇧🇷', 'language': 'Portuguese', 'mapped_to': 'pt-BR-Standard-A'},
            {'id': 'Camila', 'name': 'Camila', 'gender': 'female', 'avatar': '👩🇧🇷', 'language': 'Portuguese', 'mapped_to': 'pt-BR-Standard-C'},
            {'id': 'Enrique', 'name': 'Enrique', 'gender': 'male', 'avatar': '👨🇪🇸', 'language': 'Spanish', 'mapped_to': 'es-ES-Standard-B'},
            {'id': 'Conchita', 'name': 'Conchita', 'gender': 'female', 'avatar': '👩🇪🇸', 'language': 'Spanish', 'mapped_to': 'es-ES-Standard-C'},
            {'id': 'Lucia', 'name': 'Lucia', 'gender': 'female', 'avatar': '👩🇪🇸', 'language': 'Spanish', 'mapped_to': 'es-ES-Standard-A'},
            {'id': 'Penelope', 'name': 'Penelope', 'gender': 'female', 'avatar': '👩🇺🇸', 'language': 'Spanish (US)', 'mapped_to': 'es-US-Standard-A'},
            {'id': 'Lupe', 'name': 'Lupe', 'gender': 'female', 'avatar': '👩🇺🇸', 'language': 'Spanish (US)', 'mapped_to': 'es-US-Standard-B'},
            {'id': 'Miguel', 'name': 'Miguel', 'gender': 'male', 'avatar': '👨🇺🇸', 'language': 'Spanish (US)', 'mapped_to': 'es-US-Standard-C'},
            {'id': 'Mia', 'name': 'Mia', 'gender': 'female', 'avatar': '👩🇺🇸', 'language': 'Spanish (US)', 'mapped_to': 'es-US-Standard-D'},
            {'id': 'Maxim', 'name': 'Maxim', 'gender': 'male', 'avatar': '👨🇷🇺', 'language': 'Russian', 'mapped_to': 'ru-RU-Standard-B'},
            {'id': 'Tatyana', 'name': 'Tatyana', 'gender': 'female', 'avatar': '👩🇷🇺', 'language': 'Russian', 'mapped_to': 'ru-RU-Standard-A'},
            {'id': 'Filiz', 'name': 'Filiz', 'gender': 'female', 'avatar': '👩🇹🇷', 'language': 'Turkish', 'mapped_to': 'tr-TR-Standard-A'},
            {'id': 'Zeina', 'name': 'Zeina', 'gender': 'female', 'avatar': '👩🇸🇦', 'language': 'Arabic', 'mapped_to': 'ar-XA-Standard-A'},
            {'id': 'Zhiyu', 'name': 'Zhiyu', 'gender': 'female', 'avatar': '👩🇨🇳', 'language': 'Chinese', 'mapped_to': 'zh-CN-Standard-A'},
        ]
        
        for legacy_voice in legacy_voices:
            all_voices.append({
                "id": legacy_voice['id'],
                "name": legacy_voice['name'],
                "gender": legacy_voice['gender'],
                "avatar": legacy_voice['avatar'],
                "language": legacy_voice['language'],
                "lang_code": get_language_from_voice(legacy_voice['id']),
                "type": "legacy",
                "provider": "legacy_mapped",
                "mapped_to": legacy_voice['mapped_to']
            })
        
        return jsonify({
            "success": True,
            "count": len(all_voices),
            "voices": all_voices
        })
        
    except Exception as e:
        logging.error(f"Error getting voices: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/voices/<voice_id>', methods=['GET'])
def get_voice_details(voice_id):
    """Get details for a specific voice"""
    try:
        # Check Google voices
        for voice in GOOGLE_VOICES:
            if voice['id'] == voice_id:
                return jsonify({
                    "success": True,
                    "voice": {
                        "id": voice['id'],
                        "name": voice['name'],
                        "gender": voice['gender'],
                        "avatar": voice['avatar'],
                        "language": voice['language'],
                        "lang_code": get_language_from_voice(voice['id']),
                        "type": voice['type'],
                        "provider": "google"
                    }
                })
        
        # Check legacy voices
        legacy_voices = [
            {'id': 'Brian', 'name': 'Brian', 'gender': 'male', 'avatar': '👨🇬🇧', 'language': 'British English', 'mapped_to': 'en-GB-Standard-B'},
            {'id': 'Amy', 'name': 'Amy', 'gender': 'female', 'avatar': '👩🇬🇧', 'language': 'British English', 'mapped_to': 'en-GB-Standard-A'},
            {'id': 'Emma', 'name': 'Emma', 'gender': 'female', 'avatar': '👩🇬🇧', 'language': 'British English', 'mapped_to': 'en-GB-Standard-C'},
            {'id': 'Joanna', 'name': 'Joanna', 'gender': 'female', 'avatar': '👩🇺🇸', 'language': 'US English', 'mapped_to': 'en-US-Standard-C'},
            {'id': 'Salli', 'name': 'Salli', 'gender': 'female', 'avatar': '👩🇺🇸', 'language': 'US English', 'mapped_to': 'en-US-Standard-J'},
            {'id': 'Matthew', 'name': 'Matthew', 'gender': 'male', 'avatar': '👨🇺🇸', 'language': 'US English', 'mapped_to': 'en-US-Standard-D'},
            {'id': 'Kimberly', 'name': 'Kimberly', 'gender': 'female', 'avatar': '👩🇺🇸', 'language': 'US English', 'mapped_to': 'en-US-Standard-F'},
            {'id': 'Kendra', 'name': 'Kendra', 'gender': 'female', 'avatar': '👩🇺🇸', 'language': 'US English', 'mapped_to': 'en-US-Standard-G'},
            {'id': 'Justin', 'name': 'Justin', 'gender': 'male', 'avatar': '👨🇺🇸', 'language': 'US English', 'mapped_to': 'en-US-Standard-E'},
            {'id': 'Joey', 'name': 'Joey', 'gender': 'male', 'avatar': '👨🇺🇸', 'language': 'US English', 'mapped_to': 'en-US-Standard-H'},
            {'id': 'Ivy', 'name': 'Ivy', 'gender': 'female', 'avatar': '👩🇺🇸', 'language': 'US English', 'mapped_to': 'en-US-Standard-I'},
            {'id': 'Nicole', 'name': 'Nicole', 'gender': 'female', 'avatar': '👩🇦🇺', 'language': 'Australian English', 'mapped_to': 'en-AU-Standard-A'},
            {'id': 'Russell', 'name': 'Russell', 'gender': 'male', 'avatar': '👨🇦🇺', 'language': 'Australian English', 'mapped_to': 'en-AU-Standard-B'},
            {'id': 'Aditi', 'name': 'Aditi', 'gender': 'female', 'avatar': '👩🇮🇳', 'language': 'Indian English', 'mapped_to': 'en-IN-Standard-A'},
            {'id': 'Raveena', 'name': 'Raveena', 'gender': 'female', 'avatar': '👩🇮🇳', 'language': 'Indian English', 'mapped_to': 'en-IN-Standard-B'},
            {'id': 'Mizuki', 'name': 'Mizuki', 'gender': 'female', 'avatar': '👩🇯🇵', 'language': 'Japanese', 'mapped_to': 'ja-JP-Standard-A'},
            {'id': 'Takumi', 'name': 'Takumi', 'gender': 'male', 'avatar': '👨🇯🇵', 'language': 'Japanese', 'mapped_to': 'ja-JP-Standard-D'},
            {'id': 'Seoyeon', 'name': 'Seoyeon', 'gender': 'female', 'avatar': '👩🇰🇷', 'language': 'Korean', 'mapped_to': 'ko-KR-Standard-A'},
            {'id': 'Celine', 'name': 'Celine', 'gender': 'female', 'avatar': '👩🇫🇷', 'language': 'French', 'mapped_to': 'fr-FR-Standard-A'},
            {'id': 'Lea', 'name': 'Lea', 'gender': 'female', 'avatar': '👩🇫🇷', 'language': 'French', 'mapped_to': 'fr-FR-Standard-C'},
            {'id': 'Mathieu', 'name': 'Mathieu', 'gender': 'male', 'avatar': '👨🇫🇷', 'language': 'French', 'mapped_to': 'fr-FR-Standard-D'},
            {'id': 'Hans', 'name': 'Hans', 'gender': 'male', 'avatar': '👨🇩🇪', 'language': 'German', 'mapped_to': 'de-DE-Standard-B'},
            {'id': 'Marlene', 'name': 'Marlene', 'gender': 'female', 'avatar': '👩🇩🇪', 'language': 'German', 'mapped_to': 'de-DE-Standard-A'},
            {'id': 'Vicki', 'name': 'Vicki', 'gender': 'female', 'avatar': '👩🇩🇪', 'language': 'German', 'mapped_to': 'de-DE-Standard-C'},
            {'id': 'Giorgio', 'name': 'Giorgio', 'gender': 'male', 'avatar': '👨🇮🇹', 'language': 'Italian', 'mapped_to': 'it-IT-Standard-B'},
            {'id': 'Bianca', 'name': 'Bianca', 'gender': 'female', 'avatar': '👩🇮🇹', 'language': 'Italian', 'mapped_to': 'it-IT-Standard-A'},
            {'id': 'Carla', 'name': 'Carla', 'gender': 'female', 'avatar': '👩🇮🇹', 'language': 'Italian', 'mapped_to': 'it-IT-Standard-C'},
            {'id': 'Ricardo', 'name': 'Ricardo', 'gender': 'male', 'avatar': '👨🇧🇷', 'language': 'Portuguese', 'mapped_to': 'pt-BR-Standard-B'},
            {'id': 'Vitoria', 'name': 'Vitoria', 'gender': 'female', 'avatar': '👩🇧🇷', 'language': 'Portuguese', 'mapped_to': 'pt-BR-Standard-A'},
            {'id': 'Camila', 'name': 'Camila', 'gender': 'female', 'avatar': '👩🇧🇷', 'language': 'Portuguese', 'mapped_to': 'pt-BR-Standard-C'},
            {'id': 'Enrique', 'name': 'Enrique', 'gender': 'male', 'avatar': '👨🇪🇸', 'language': 'Spanish', 'mapped_to': 'es-ES-Standard-B'},
            {'id': 'Conchita', 'name': 'Conchita', 'gender': 'female', 'avatar': '👩🇪🇸', 'language': 'Spanish', 'mapped_to': 'es-ES-Standard-C'},
            {'id': 'Lucia', 'name': 'Lucia', 'gender': 'female', 'avatar': '👩🇪🇸', 'language': 'Spanish', 'mapped_to': 'es-ES-Standard-A'},
            {'id': 'Penelope', 'name': 'Penelope', 'gender': 'female', 'avatar': '👩🇺🇸', 'language': 'Spanish (US)', 'mapped_to': 'es-US-Standard-A'},
            {'id': 'Lupe', 'name': 'Lupe', 'gender': 'female', 'avatar': '👩🇺🇸', 'language': 'Spanish (US)', 'mapped_to': 'es-US-Standard-B'},
            {'id': 'Miguel', 'name': 'Miguel', 'gender': 'male', 'avatar': '👨🇺🇸', 'language': 'Spanish (US)', 'mapped_to': 'es-US-Standard-C'},
            {'id': 'Mia', 'name': 'Mia', 'gender': 'female', 'avatar': '👩🇺🇸', 'language': 'Spanish (US)', 'mapped_to': 'es-US-Standard-D'},
            {'id': 'Maxim', 'name': 'Maxim', 'gender': 'male', 'avatar': '👨🇷🇺', 'language': 'Russian', 'mapped_to': 'ru-RU-Standard-B'},
            {'id': 'Tatyana', 'name': 'Tatyana', 'gender': 'female', 'avatar': '👩🇷🇺', 'language': 'Russian', 'mapped_to': 'ru-RU-Standard-A'},
            {'id': 'Filiz', 'name': 'Filiz', 'gender': 'female', 'avatar': '👩🇹🇷', 'language': 'Turkish', 'mapped_to': 'tr-TR-Standard-A'},
            {'id': 'Zeina', 'name': 'Zeina', 'gender': 'female', 'avatar': '👩🇸🇦', 'language': 'Arabic', 'mapped_to': 'ar-XA-Standard-A'},
            {'id': 'Zhiyu', 'name': 'Zhiyu', 'gender': 'female', 'avatar': '👩🇨🇳', 'language': 'Chinese', 'mapped_to': 'zh-CN-Standard-A'},
        ]
        
        for legacy_voice in legacy_voices:
            if legacy_voice['id'] == voice_id:
                return jsonify({
                    "success": True,
                    "voice": {
                        "id": legacy_voice['id'],
                        "name": legacy_voice['name'],
                        "gender": legacy_voice['gender'],
                        "avatar": legacy_voice['avatar'],
                        "language": legacy_voice['language'],
                        "lang_code": get_language_from_voice(legacy_voice['id']),
                        "type": "legacy",
                        "provider": "legacy_mapped",
                        "mapped_to": legacy_voice['mapped_to']
                    }
                })
        
        return jsonify({"error": "Voice not found"}), 404
        
    except Exception as e:
        logging.error(f"Error getting voice details: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/languages', methods=['GET'])
def get_languages():
    """Get all supported languages"""
    try:
        languages = {}
        for voice in GOOGLE_VOICES:
            lang_code = get_language_from_voice(voice['id'])
            if lang_code not in languages:
                languages[lang_code] = {
                    "code": lang_code,
                    "name": voice['language'].split('(')[0].strip(),
                    "flag": get_language_flag(lang_code),
                    "voice_count": 0
                }
            languages[lang_code]["voice_count"] += 1
        
        return jsonify({
            "success": True,
            "languages": list(languages.values())
        })
        
    except Exception as e:
        logging.error(f"Error getting languages: {str(e)}")
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
            "/api/voices/<voice_id> - GET - Get voice details",
            "/api/languages - GET - Get supported languages",
            "/api/test - GET - Test endpoint"
        ]
    })

def get_language_flag(lang_code):
    """Get flag emoji for language code"""
    flag_map = {
        "en-US": "🇺🇸", "en-GB": "🇬🇧", "en-AU": "🇦🇺", "en-IN": "🇮🇳",
        "es-ES": "🇪🇸", "es-US": "🇺🇸", "fr-FR": "🇫🇷", "de-DE": "🇩🇪",
        "it-IT": "🇮🇹", "pt-BR": "🇧🇷", "pt-PT": "🇵🇹", "ru-RU": "🇷🇺",
        "ja-JP": "🇯🇵", "ko-KR": "🇰🇷", "zh-CN": "🇨🇳", "ar-XA": "🇸🇦",
        "hi-IN": "🇮🇳", "tr-TR": "🇹🇷", "nl-NL": "🇳🇱", "pl-PL": "🇵🇱",
        "sv-SE": "🇸🇪", "nb-NO": "🇳🇴", "da-DK": "🇩🇰"
    }
    return flag_map.get(lang_code, "🌐")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)


