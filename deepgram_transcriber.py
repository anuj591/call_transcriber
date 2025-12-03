from deepgram import Deepgram
import asyncio
import json
import os
from datetime import datetime

api_key = '507bdfd052088ccd9f3422aa295066621b29209a'

async def main():
    # Create transcriptions folder if it doesn't exist
    output_folder = 'transcriptions'
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"✅ Created folder: {output_folder}")
    
    # Get audio file name
    audio_file = '53b09f838a420b1ebeed15f3452c19c3_20251203_190626.mp3'
    file_name = os.path.splitext(os.path.basename(audio_file))[0]
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create output filename
    output_filename = f"{file_name}_{timestamp}.txt"
    output_path = os.path.join(output_folder, output_filename)
    
    # Initialize client
    deepgram = Deepgram(api_key)
    
    # Read audio file
    with open(audio_file, 'rb') as audio:
        source = {'buffer': audio, 'mimetype': 'audio/wav'}
        
        # Configure options
        options = {
            'punctuate': True,
            'diarize': True,
            'language': 'hi'
        }
        
        # Transcribe
        print(f"🎙️  Transcribing: {audio_file}")
        response = await deepgram.transcription.prerecorded(source, options)
        
        # Print results
        transcript = response['results']['channels'][0]['alternatives'][0]['transcript']
        print("\nFull Transcription:")
        print(transcript)
        print("\n" + "="*60)
        
        # Open file for writing
        with open(output_path, 'w', encoding='utf-8') as output_file:
            # Write header
            output_file.write(f"FILE: {audio_file}\n")
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

# Run
asyncio.run(main())
