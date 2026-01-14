import assemblyai as aai
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")

# Audio file path
audio_file = "recordings/6dc81675f63121c6f666575fd89a19cb_20251211_144714.mp3"

# Extract call ID from filename (part before first underscore)
call_id = os.path.splitext(os.path.basename(audio_file))[0].split('_')[0]

# Create transcriptions folder if it doesn't exist
transcriptions_dir = Path('transcriptions')
transcriptions_dir.mkdir(exist_ok=True)

# Generate timestamp for output file
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Create output filename with call ID
output_filename = f"{call_id}_{timestamp}.txt"
output_path = transcriptions_dir / output_filename

# Configure transcription with speaker labels and language detection
# Specify expected languages (Hindi and English) for better detection
language_detection_options = aai.LanguageDetectionOptions(
    expected_languages=["hi", "en"],  # Only consider Hindi and English
    fallback_language="auto"  # Fallback to auto if detection is uncertain
)

config = aai.TranscriptionConfig(
    speaker_labels=True,
    language_detection=True,  # Enable automatic language detection
    language_detection_options=language_detection_options
)

# Upload your audio file and transcribe
print(f"🎙️  Transcribing: {audio_file}")
transcriber = aai.Transcriber()
transcript = transcriber.transcribe(audio_file, config)

# Print full transcript
print("\nFull Transcription:")
print(transcript.text)
print("\n" + "="*60)

# Save transcription to file
with open(output_path, 'w', encoding='utf-8') as output_file:
    # Write header
    output_file.write(f"FILE: {audio_file}\n")
    output_file.write(f"CALL ID: {call_id}\n")
    output_file.write(f"DATE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    output_file.write("="*60 + "\n\n")
    
    # Write full transcript
    output_file.write("FULL TRANSCRIPTION:\n")
    output_file.write("-"*60 + "\n")
    output_file.write(transcript.text + "\n\n")
    
    # Write speaker diarization
    if transcript.utterances:
        output_file.write("SPEAKER DIARIZATION:\n")
        output_file.write("-"*60 + "\n\n")
        
        print("Speaker Diarization:\n")
        for utterance in transcript.utterances:
            line = f"Speaker {utterance.speaker}: {utterance.text}"
            print(line)
            output_file.write(line + "\n\n")

print("\n" + "="*60)
print(f"✅ Transcription saved to: {output_path}")