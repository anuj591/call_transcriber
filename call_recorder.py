import os
import requests
import json
from datetime import datetime, timedelta
import time
from pathlib import Path
from dotenv import load_dotenv
import asyncio
from deepgram import Deepgram

load_dotenv()


class ExotelCallRecorder:
    def __init__(self):
        # Load credentials from environment variables
        self.api_key = os.getenv('EXOTEL_API_KEY')
        self.api_token = os.getenv('EXOTEL_API_TOKEN')
        self.sid = os.getenv('EXOTEL_SID')
        self.subdomain = os.getenv('EXOTEL_SUBDOMAIN', 'api.exotel.com')
        
        # Deepgram API key
        self.deepgram_api_key = os.getenv('DEEPGRAM_API_KEY', '507bdfd052088ccd9f3422aa295066621b29209a')
        
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
    
    def get_call_details(self, call_sid):
        """Get detailed information about a specific call"""
        url = f"{self.base_url}/Calls/{call_sid}.json"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            return data.get('Call', {})
        except Exception as e:
            print(f"Error fetching call details for {call_sid}: {e}")
            return {}
    
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
    
    async def transcribe_audio_deepgram(self, audio_filepath, call_sid):
        """Transcribe audio using Deepgram API"""
        try:
            # Get file name
            file_name = os.path.splitext(os.path.basename(audio_filepath))[0]
            
            # Generate timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create output filename
            output_filename = f"{file_name}_{timestamp}.txt"
            output_path = os.path.join(self.transcriptions_dir, output_filename)
            
            # Initialize client
            deepgram = Deepgram(self.deepgram_api_key)
            
            # Read audio file
            with open(audio_filepath, 'rb') as audio:
                source = {'buffer': audio, 'mimetype': 'audio/mp3'}
                
                # Configure options
                options = {
                    'punctuate': True,
                    'diarize': True,
                    'language': 'hi'
                }
                
                # Transcribe
                print(f"🎙️  Transcribing: {audio_filepath}")
                response = await deepgram.transcription.prerecorded(source, options)
                
                # Print results
                transcript = response['results']['channels'][0]['alternatives'][0]['transcript']
                print("\nFull Transcription:")
                print(transcript)
                print("\n" + "="*60)
                
                # Open file for writing
                with open(output_path, 'w', encoding='utf-8') as output_file:
                    # Write header
                    output_file.write(f"FILE: {audio_filepath}\n")
                    output_file.write(f"CALL SID: {call_sid}\n")
                    output_file.write(f"DATE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    output_file.write("="*60 + "\n\n")
                    
                    # Write full transcript
                    output_file.write("FULL TRANSCRIPTION:\n")
                    output_file.write("-"*60 + "\n")
                    output_file.write(transcript + "\n\n")
                    
                    # Speaker diarization
                    words = response['results']['channels'][0]['alternatives'][0]['words']
                    if words:
                        output_file.write("SPEAKER DIARIZATION:\n")
                        output_file.write("-"*60 + "\n\n")
                        
                        print("Speaker Diarization:\n")
                        current_speaker = None
                        current_text = []
                        
                        for word in words:
                            speaker = word.get('speaker', 'Unknown')
                            word_text = word.get('punctuated_word', word.get('word', ''))
                            
                            if speaker != current_speaker:
                                if current_speaker is not None:
                                    line = f"Speaker {current_speaker}: {' '.join(current_text)}"
                                    print(line)
                                    output_file.write(line + "\n\n")
                                current_speaker = speaker
                                current_text = [word_text]
                            else:
                                current_text.append(word_text)
                        
                        # Print and write last speaker
                        if current_speaker is not None:
                            line = f"Speaker {current_speaker}: {' '.join(current_text)}"
                            print(line)
                            output_file.write(line + "\n")
                
                print("\n" + "="*60)
                print(f"✅ Transcription saved to: {output_path}")
                return output_path
                
        except Exception as e:
            print(f"Error transcribing with Deepgram: {e}")
            return None
    
    def save_call_metadata(self, call_sid, from_number, to_number, 
                          direction, duration, timestamp):
        """Save call metadata to a JSON file"""
        filename = f"{call_sid}_metadata.json"
        filepath = self.recordings_dir / filename
        
        metadata = {
            'call_sid': call_sid,
            'from': from_number,
            'to': to_number,
            'direction': direction,
            'duration': duration,
            'timestamp': timestamp,
            'downloaded_at': datetime.now().isoformat()
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"✓ Saved metadata: {filename}")
            return filepath
        except Exception as e:
            print(f"Error saving metadata: {e}")
            return None
    
    async def process_call_async(self, call):
        """Process a single call: download recording, transcribe, and save metadata"""
        call_sid = call.get('Sid')
        
        # Handle both string and dict formats
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
        
        # Transcribe using Deepgram
        transcription_file = await self.transcribe_audio_deepgram(audio_file, call_sid)
        if not transcription_file:
            print("⊘ Transcription failed")
            return False
        
        # Save metadata
        self.save_call_metadata(
            call_sid, from_number, to_number,
            direction, duration, date_created
        )
        
        print(f"✓ Successfully processed call {call_sid}")
        print(f"Recording saved at: {audio_file}")
        print(f"Transcription saved at: {transcription_file}\n")
        return True
    
    def process_call(self, call):
        """Synchronous wrapper for async process_call_async"""
        return asyncio.run(self.process_call_async(call))
    
    def run(self, hours=24, continuous=False, interval=300):
        """
        Main function to process calls
        
        Args:
            hours: Look back N hours for calls
            continuous: If True, run continuously
            interval: Seconds between checks (if continuous)
        """
        print("="*80)
        print("EXOTEL CALL RECORDER & TRANSCRIBER (DEEPGRAM)")
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
    
    # Run once to fetch and transcribe recordings from last 24 hours
    # Set continuous=True to run in loop mode
    recorder.run(hours=24, continuous=False, interval=300)


if __name__ == "__main__":
    main()