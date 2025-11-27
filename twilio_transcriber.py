import os
import json
import threading
from typing import List, Optional
from datetime import datetime
import audioop
from vosk import Model, KaldiRecognizer
from dotenv import load_dotenv

load_dotenv()

# Terminal control codes for cursor movement
CL = '\x1b[2K'  # Clear line from cursor to end
BS = '\x08'     # Backspace

# Audio configuration
TWILIO_SAMPLE_RATE = 8000  # Hz - Twilio's sample rate
VOSK_SAMPLE_RATE = 16000  # Hz - Vosk's required sample rate

# Supported languages: 'en' for English, 'hi' for Hindi
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'hi': 'Hindi'
}

# Model directory patterns to search for
MODEL_PATTERNS = {
    'en': ['vosk-model-small-en-us-0.15', 'vosk-model-en-us', 'vosk-model-en'],
    'hi': ['vosk-model-small-hi-0.22', 'vosk-model-hi   ', 'vosk-model-hi']
}


class TranscriptDisplay:
    def __init__(self):
        self.final_transcripts: List[str] = []  # Store all final transcripts
        self.lock = threading.Lock()
    
    def add_final(self, text: str):
        """Add final transcript as a new line"""
        with self.lock:
            if text.strip():  # Only add non-empty transcripts
                self.final_transcripts.append(text)
                print(text + ' ', end='', flush=True)  # Print with space for readability
    
    def get_full_transcript(self) -> str:
        """Get the complete transcript as a single string"""
        with self.lock:
            return ' '.join(self.final_transcripts)
    
    def save_to_file(self, filename: str = None):
        """Save the transcript to a file"""
        transcript_text = self.get_full_transcript()
        if not transcript_text.strip():
            print("\nNo transcript to save.")
            return
        
        # Create transcripts directory if it doesn't exist
        transcripts_dir = "transcripts"
        os.makedirs(transcripts_dir, exist_ok=True)
        
        # Generate filename with timestamp if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{transcripts_dir}/transcript_{timestamp}.txt"
        else:
            filename = f"{transcripts_dir}/{filename}"
        
        # Save to file
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Call Transcript - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n\n")
                f.write(transcript_text)
                f.write("\n")
            print(f"\n✓ Transcript saved to: {filename}")
        except Exception as e:
            print(f"\n✗ Error saving transcript: {e}")


def find_model_directory(language: Optional[str] = None, base_path: str = ".") -> Optional[str]:
    """
    Find Vosk model directory automatically
    
    Args:
        language: Language code ('en' or 'hi') to find specific model
        base_path: Base directory to search in (default: current directory)
    
    Returns:
        Path to model directory if found, None otherwise
    """
    if not os.path.exists(base_path):
        return None
    
    # If language is specified, search for that language's model
    if language and language.lower() in MODEL_PATTERNS:
        patterns = MODEL_PATTERNS[language.lower()]
        for item in os.listdir(base_path):
            item_path = os.path.join(base_path, item)
            if os.path.isdir(item_path):
                for pattern in patterns:
                    if pattern in item.lower():
                        # Verify it's a valid Vosk model (has 'am' directory)
                        if os.path.exists(os.path.join(item_path, 'am')):
                            return item_path
    
    # If no language specified or model not found, search for any Vosk model
    for item in os.listdir(base_path):
        item_path = os.path.join(base_path, item)
        if os.path.isdir(item_path) and 'vosk-model' in item.lower():
            # Verify it's a valid Vosk model (has 'am' directory)
            if os.path.exists(os.path.join(item_path, 'am')):
                return item_path
    
    return None


class TwilioTranscriber:
    def __init__(self, model_path: str = None, language: str = None):
        """
        Initialize Vosk transcriber (completely free, no API keys needed)
        Automatically finds and loads the appropriate model based on language.
        
        Args:
            model_path: Path to Vosk language model directory (optional, auto-detected if not provided)
            language: Language code ('en' for English, 'hi' for Hindi)
        """
        # Determine which model to use
        if model_path is None:
            # Try to find model automatically
            base_path = os.getenv('VOSK_MODELS_DIR', '.')  # Directory containing model folders
            model_path = find_model_directory(language, base_path)
            
            if model_path is None:
                # Fallback: check if single 'model' directory exists
                if os.path.exists('model') and os.path.exists(os.path.join('model', 'am')):
                    model_path = 'model'
                else:
                    raise FileNotFoundError(
                        f"\n❌ Vosk model not found!\n"
                        f"📥 Please download models from: https://alphacephei.com/vosk/models\n"
                        f"📁 Extract them to your project directory\n"
                        f"💡 Detected models should be in folders like:\n"
                        f"   - vosk-model-small-en-us-0.15/ (for English)\n"
                        f"   - vosk-model-small-hi-0.22/ (for Hindi)\n"
                        f"💡 Or set VOSK_MODEL_PATH environment variable to your model path.\n"
                        f"💡 Or set VOSK_MODELS_DIR to directory containing model folders."
                    )
        
        # Check if model exists and is valid
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"\n❌ Vosk model not found at: {model_path}\n"
                f"📥 Please download a model from: https://alphacephei.com/vosk/models"
            )
        
        if not os.path.exists(os.path.join(model_path, 'am')):
            raise FileNotFoundError(
                f"\n❌ Invalid Vosk model at: {model_path}\n"
                f"📥 The model directory should contain an 'am' folder.\n"
                f"💡 Make sure you extracted the model ZIP file correctly."
            )
        
        # Detect language from model path if not specified
        detected_lang = None
        model_name = os.path.basename(model_path).lower()
        if 'en' in model_name and 'hi' not in model_name:
            detected_lang = 'en'
        elif 'hi' in model_name:
            detected_lang = 'hi'
        
        # Use specified language or detected language
        if language:
            language = language.lower()
            if language not in SUPPORTED_LANGUAGES:
                print(f"⚠️  Warning: Language '{language}' not supported. Using detected language from model.")
                language = detected_lang
        else:
            language = detected_lang
        
        print(f"📦 Loading Vosk model from: {model_path}")
        self.model = Model(model_path)
        self.rec = KaldiRecognizer(self.model, VOSK_SAMPLE_RATE)
        self.rec.SetWords(True)  # Enable word-level timestamps (optional)
        
        self.transcript_display = TranscriptDisplay()
        self.is_active = False
        
        # Language info
        if language:
            lang_name = SUPPORTED_LANGUAGES.get(language, 'Auto')
            print(f"🌐 Language: {lang_name} ({language})")
        else:
            print(f"🌐 Language: Auto-detected from model")
        
        print("✅ Vosk model loaded successfully. Ready for transcription.")
        print("💡 Vosk is completely free - no API keys or credit cards needed!\n")
    
    def process_audio(self, audio_data: bytes):
        """
        Process audio data from Twilio and transcribe using Vosk
        
        Args:
            audio_data: Raw μ-law encoded audio bytes from Twilio
        """
        if not self.is_active:
            return
        
        try:
            # Convert from base64 decoded μ-law to linear PCM
            # Twilio sends μ-law encoded audio at 8kHz
            audio = audioop.ulaw2lin(audio_data, 2)  # 2 bytes per sample (16-bit)
            
            # Convert sample rate from 8kHz to 16kHz (required by Vosk)
            audio, _ = audioop.ratecv(audio, 2, 1, TWILIO_SAMPLE_RATE, VOSK_SAMPLE_RATE, None)
            
            # Process audio with Vosk
            if self.rec.AcceptWaveform(bytes(audio)):
                # Final result - complete sentence/phrase
                result = json.loads(self.rec.Result())
                if 'text' in result and result['text']:
                    self.transcript_display.add_final(result['text'])
            else:
                # Partial result - still processing
                partial = json.loads(self.rec.PartialResult())
                if 'partial' in partial and partial['partial']:
                    # Clear line and print partial result (will be overwritten)
                    print(CL + partial['partial'] + BS * len(partial['partial']), end='', flush=True)
        
        except Exception as e:
            print(f"\n❌ Error processing audio: {e}")
            import traceback
            traceback.print_exc()
    
    def start_transcription(self):
        """Start the transcription session"""
        self.is_active = True
        print("🎤 Transcription started. Speak into your phone...\n")
    
    def stop_transcription(self):
        """Stop the transcription and clean up"""
        self.is_active = False
        
        # Get any remaining final result
        try:
            final_result = json.loads(self.rec.FinalResult())
            if 'text' in final_result and final_result['text']:
                self.transcript_display.add_final(final_result['text'])
        except:
            pass
        
        print("\n🛑 Transcription stopped.")
        
        # Save transcript when stopping
        if self.transcript_display:
            self.transcript_display.save_to_file()
