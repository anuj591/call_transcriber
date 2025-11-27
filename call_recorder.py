import os
import requests
import json
from datetime import datetime, timedelta
import time
from pathlib import Path
import base64
from dotenv import load_dotenv
load_dotenv()
class ExotelCallRecorder:
    def __init__(self):
        # Load credentials from environment variables
        self.api_key = os.getenv('EXOTEL_API_KEY')
        self.api_token = os.getenv('EXOTEL_API_TOKEN')
        self.sid = os.getenv('EXOTEL_SID')
        self.subdomain = os.getenv('EXOTEL_SUBDOMAIN', 'api.exotel.com')
        
        # AssemblyAI API for transcription
        self.assemblyai_api_key = os.getenv('ASSEMBLYAI_API_KEY')
        
        # Create directories for storage
        self.recordings_dir = Path('recordings')
        self.transcriptions_dir = Path('transcriptions')
        self.recordings_dir.mkdir(exist_ok=True)
        self.transcriptions_dir.mkdir(exist_ok=True)
        
        # Base URL for API
        self.base_url = f"https://{self.api_key}:{self.api_token}@{self.subdomain}/v1/Accounts/{self.sid}"
        
    def get_recent_calls(self, hours=24):
        """Fetch calls from the last N hours"""
        url = f"{self.base_url}/Calls.json"
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=hours)
        
        params = {
            'StartTime': start_date.strftime('%Y-%m-%d'),
            'EndTime': end_date.strftime('%Y-%m-%d'),
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('Calls', [])
        except Exception as e:
            print(f"Error fetching calls: {e}")
            return []
    
    def download_recording(self, call_sid, recording_url):
        """Download call recording audio file"""
        try:
            # Create filename with call SID and timestamp
            filename = f"{call_sid}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
            filepath = self.recordings_dir / filename
            
            # Download the recording
            auth = (self.api_key, self.api_token)
            response = requests.get(recording_url, auth=auth, stream=True)
            response.raise_for_status()
            
            # Save to file
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✓ Downloaded: {filename}")
            return filepath
        except Exception as e:
            print(f"Error downloading recording {call_sid}: {e}")
            return None
    
    def transcribe_audio_whisper(self, audio_filepath):
        """Transcribe audio using AssemblyAI API (supports Hindi + English)"""
        try:
            # Step 1: Upload audio file to AssemblyAI
            upload_url = "https://api.assemblyai.com/v2/upload"
            headers = {
                "authorization": self.assemblyai_api_key
            }
            
            with open(audio_filepath, 'rb') as audio_file:
                response = requests.post(upload_url, headers=headers, files={'file': audio_file})
                response.raise_for_status()
                upload_result = response.json()
                audio_url = upload_result.get('upload_url')
            
            if not audio_url:
                print("Error: Failed to upload audio file")
                return None
            
            # Step 2: Submit transcription request
            transcript_url = "https://api.assemblyai.com/v2/transcript"
            transcript_headers = {
                "authorization": self.assemblyai_api_key,
                "content-type": "application/json"
            }
            
            transcript_data = {
                "audio_url": audio_url,
                "language_code": "hi",  # Hindi, but auto-detects English too
                "speaker_labels": True  # Enable speaker diarization
            }
            
            response = requests.post(transcript_url, json=transcript_data, headers=transcript_headers)
            response.raise_for_status()
            transcript_result = response.json()
            transcript_id = transcript_result.get('id')
            
            if not transcript_id:
                print("Error: Failed to submit transcription request")
                return None
            
            # Step 3: Poll for transcription completion
            polling_url = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
            max_attempts = 60  # 5 minutes max (5 seconds * 60)
            attempt = 0
            
            while attempt < max_attempts:
                response = requests.get(polling_url, headers=headers)
                response.raise_for_status()
                status_result = response.json()
                
                status = status_result.get('status')
                
                if status == 'completed':
                    # Get the transcript text
                    transcript_text = status_result.get('text', '')
                    
                    # If speaker labels are available, format with speakers
                    if status_result.get('utterances'):
                        formatted_text = ""
                        for utterance in status_result.get('utterances', []):
                            speaker_value = utterance.get('speaker', 0)
                            
                            # Handle both string ('A', 'B') and numeric (0, 1) speaker labels
                            if isinstance(speaker_value, str):
                                # Already a letter like 'A', 'B', 'C'
                                speaker = f"Person {speaker_value}"
                            else:
                                # Numeric value, convert to letter
                                speaker_num = int(speaker_value)
                                speaker = f"Person {chr(65 + speaker_num)}"  # A, B, C...
                            
                            text = utterance.get('text', '')
                            formatted_text += f"{speaker}: {text}\n\n"
                        return formatted_text.strip()
                    
                    return transcript_text
                    
                elif status == 'error':
                    error_msg = status_result.get('error', 'Unknown error')
                    print(f"Transcription error: {error_msg}")
                    return None
                
                # Wait before next poll
                time.sleep(5)
                attempt += 1
                print(f"  Waiting for transcription... ({attempt * 5}s)")
            
            print("Error: Transcription timeout")
            return None
            
        except Exception as e:
            print(f"Error transcribing with AssemblyAI: {e}")
            return None
    
    def transcribe_audio_google(self, audio_filepath):
        """Alternative: Transcribe using Google Speech-to-Text API"""
        try:
            from google.cloud import speech
            
            client = speech.SpeechClient()
            
            with open(audio_filepath, 'rb') as audio_file:
                content = audio_file.read()
            
            audio = speech.RecognitionAudio(content=content)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.MP3,
                language_code='hi-IN',  # Hindi
                alternative_language_codes=['en-IN'],  # English fallback
                enable_automatic_punctuation=True,
            )
            
            response = client.recognize(config=config, audio=audio)
            
            transcript = ""
            for result in response.results:
                transcript += result.alternatives[0].transcript + " "
            
            return transcript.strip()
        except Exception as e:
            print(f"Error transcribing with Google: {e}")
            return None
    
    def save_transcription(self, call_sid, from_number, to_number, 
                          direction, duration, timestamp, transcription):
        """Save transcription to a text file with metadata"""
        filename = f"{call_sid}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = self.transcriptions_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("="*80 + "\n")
                f.write("CALL RECORDING TRANSCRIPTION\n")
                f.write("="*80 + "\n\n")
                f.write(f"Call SID: {call_sid}\n")
                f.write(f"From: {from_number}\n")
                f.write(f"To: {to_number}\n")
                f.write(f"Direction: {direction}\n")
                f.write(f"Duration: {duration} seconds\n")
                f.write(f"Timestamp: {timestamp}\n")
                f.write("\n" + "="*80 + "\n")
                f.write("TRANSCRIPTION:\n")
                f.write("="*80 + "\n\n")
                f.write(transcription)
                f.write("\n\n" + "="*80 + "\n")
            
            print(f"✓ Saved transcription: {filename}")
            return filepath
        except Exception as e:
            print(f"Error saving transcription: {e}")
            return None
    
    def format_conversation(self, transcription, from_number, to_number):
        """
        Format transcription with Person A and Person B labels
        This is a simple version - for better speaker diarization,
        use advanced APIs like AWS Transcribe or Google Speech Diarization
        """
        lines = transcription.split('.')
        formatted = ""
        
        for i, line in enumerate(lines):
            line = line.strip()
            if line:
                # Simple alternating pattern (not accurate without diarization)
                speaker = "Person A" if i % 2 == 0 else "Person B"
                formatted += f"{speaker}: {line}.\n\n"
        
        return formatted
    
    def process_call(self, call):
        
        """Process a single call: download, transcribe, and save"""
        call_sid = call.get('Sid')
        
        # Fix: Handle both string and dict formats
        from_field = call.get('From', 'Unknown')
        to_field = call.get('To', 'Unknown')
        
        from_number = from_field.get('PhoneNumber') if isinstance(from_field, dict) else from_field
        to_number = to_field.get('PhoneNumber') if isinstance(to_field, dict) else to_field
        
        direction = call.get('Direction', 'Unknown')
        duration = call.get('Duration', 0)
        status = call.get('Status', 'Unknown')
        date_created = call.get('DateCreated', '')
        
        # Get recording URL
        recording_url = call.get('RecordingUrl')
        
        if not recording_url:
            print(f"⊘ No recording available for call {call_sid}")
            return False
        
        if status != 'completed':
            print(f"⊘ Skipping incomplete call {call_sid}")
            return False
        
        print(f"\n{'='*80}")
        print(f"Processing Call: {call_sid}")
        print(f"From: {from_number} → To: {to_number}")
        print(f"Direction: {direction} | Duration: {duration}s")
        print(f"{'='*80}")
        
        # Download recording
        audio_file = self.download_recording(call_sid, recording_url)
        if not audio_file:
            return False
        
        # Transcribe
        print("Transcribing audio with AssemblyAI...")
        transcription = self.transcribe_audio_whisper(audio_file)
        
        if not transcription:
            print("⊘ Transcription failed")
            return False
        
        # Format with speaker labels (only if not already formatted by AssemblyAI)
        if "Person A:" in transcription or "Person B:" in transcription:
            # Already formatted with speaker labels
            formatted_transcription = transcription
        else:
            # Format with simple alternating pattern
            formatted_transcription = self.format_conversation(
                transcription, from_number, to_number
            )
        
        # Save transcription
        self.save_transcription(
            call_sid, from_number, to_number,
            direction, duration, date_created,
            formatted_transcription
        )
        
        print(f"✓ Successfully processed call {call_sid}\n")
        return True
    
    def run(self, hours=24, continuous=False, interval=300):
        """
        Main function to process calls
        
        Args:
            hours: Look back N hours for calls
            continuous: If True, run continuously
            interval: Seconds between checks (if continuous)
        """
        print("="*80)
        print("EXOTEL CALL RECORDER & TRANSCRIBER")
        print("="*80)
        print(f"Recordings saved to: {self.recordings_dir.absolute()}")
        print(f"Transcriptions saved to: {self.transcriptions_dir.absolute()}")
        print("="*80 + "\n")
        
        processed_calls = set()
        
        while True:
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking for new calls...")
            
            # Get recent calls
            calls = self.get_recent_calls(hours=hours)
            print(f"Found {len(calls)} calls in the last {hours} hours")
            
            if not calls:
                print("No calls found")
            else:
                # Sort calls by date (most recent first) and process only the last call
                # Assuming calls are returned with DateCreated field
                calls_sorted = sorted(calls, key=lambda x: x.get('DateCreated', ''), reverse=True)
                last_call = calls_sorted[0]
                call_sid = last_call.get('Sid')
                
                # Skip if already processed
                if call_sid in processed_calls:
                    print(f"⊘ Last call {call_sid} already processed")
                else:
                    print(f"Processing last call: {call_sid}")
                    success = self.process_call(last_call)
                    if success:
                        processed_calls.add(call_sid)
                        print(f"\n✓ Successfully processed last call")
                    else:
                        print(f"\n⊘ Failed to process last call")
            
            if not continuous:
                break
            
            print(f"\nWaiting {interval} seconds before next check...")
            time.sleep(interval)


def main():
    # Initialize recorder
    recorder = ExotelCallRecorder()
    
    # Run in continuous mode (checks every 5 minutes)
    # Set continuous=False to run once
    recorder.run(hours=24, continuous=True, interval=300)


if __name__ == "__main__":
    main()