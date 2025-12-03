# Exotel Call Recorder & Transcriber

An automated system that fetches call recordings from Exotel, downloads them, and transcribes them using Deepgram's transcription service with speaker diarization support.

## 📋 Overview

This system automatically:
- Fetches call recordings from your Exotel account
- Downloads the audio files locally
- Transcribes them using Deepgram API (supports Hindi + English)
- Identifies different speakers in the conversation
- Saves transcriptions with metadata to text files
- Processes only the most recent call to avoid duplicates

## 🚀 Features

- **Automated Processing**: Continuously monitors for new calls
- **Multi-language Support**: Handles Hindi and English (auto-detection)
- **Speaker Diarization**: Identifies and labels different speakers (Speaker 0, Speaker 1, etc.)
- **Error Handling**: Robust error handling with retry logic
- **Organized Storage**: Saves recordings and transcriptions in separate directories
- **Metadata Tracking**: Includes call details (SID, phone numbers, duration, timestamp)
- **Continuous Mode**: Can run continuously or process once

## 📦 Prerequisites

- Python 3.7 or higher
- Exotel account with API credentials
- Deepgram API key (get it from [deepgram.com](https://www.deepgram.com))

## 🔧 Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `requests` - For API calls
- `python-dotenv` - For environment variable management
- `deepgram` - Deepgram Python SDK
- `asyncio` - For async operations (built-in)

### 2. Get API Credentials

#### Exotel Credentials:
1. Log in to your Exotel dashboard
2. Go to Settings → API Settings
3. Copy your:
   - **API Key** (usually your account SID)
   - **API Token** (secret token)
   - **Account SID** (your Exotel account identifier)

#### Deepgram Credentials:
1. Sign up at [deepgram.com](https://www.deepgram.com)
2. Go to your dashboard
3. Navigate to API Keys section
4. Create a new API key or copy your existing one

### 3. Create Environment File

Create a `.env` file in the project root directory:

```env
# Exotel API Credentials
EXOTEL_API_KEY=your_exotel_api_key
EXOTEL_API_TOKEN=your_exotel_api_token
EXOTEL_SID=your_exotel_account_sid
EXOTEL_SUBDOMAIN=api.exotel.com

# Deepgram API Key
DEEPGRAM_API_KEY=your_deepgram_api_key
```

**Example:**
```env
EXOTEL_API_KEY=ideafoundation1
EXOTEL_API_TOKEN=abc123xyz789...
EXOTEL_SID=ideafoundation1
EXOTEL_SUBDOMAIN=api.exotel.com
DEEPGRAM_API_KEY=507bdfd052088ccd9f3422aa295066621b29209a
```

### 4. Directory Structure

The script automatically creates these directories:
```
call_transcriber/
├── recordings/          # Downloaded audio files (.mp3) and metadata (.json)
├── transcriptions/       # Transcription text files (.txt)
├── .env                 # Your credentials (not tracked in git)
├── call_recorder.py     # Main script
└── requirements.txt     # Python dependencies
```

## 🎯 How It Works

### System Flow:

1. **Fetch Calls**: Queries Exotel API for calls from the last 24 hours (configurable)
2. **Filter & Sort**: 
   - Filters only completed calls with recordings
   - Sorts by date (most recent first)
   - Processes only the last call to avoid duplicates
3. **Download**: Downloads the audio recording to local storage
4. **Transcribe**: 
   - Uploads audio to Deepgram
   - Submits transcription request with Hindi language support
   - Retrieves transcript with speaker labels
5. **Format**: Formats transcription with speaker labels (Speaker 0, Speaker 1, etc.)
6. **Save**: Saves transcription with metadata to a text file
7. **Metadata**: Saves call metadata (SID, numbers, duration, timestamp) to JSON

### Transcription Process:

```
Exotel API → Download Recording → Deepgram API → Transcription → Save Files
```

- **Language**: Hindi (configurable in code)
- **Speaker Diarization**: Enabled (identifies different speakers)
- **Processing Time**: Typically 5-15 seconds depending on audio length

## 💻 Usage

### Basic Usage

Run the script:

```bash
python call_recorder.py
```

### Configuration Options

Edit the `main()` function in `call_recorder.py`:

```python
def main():
    recorder = ExotelCallRecorder()
    
    # Run continuously (checks every 5 minutes)
    recorder.run(hours=24, continuous=True, interval=300)
    
    # OR run once for last 24 hours
    # recorder.run(hours=24, continuous=False)
```

### Parameters:

- **`hours`**: Look back N hours for calls (default: 24)
- **`continuous`**: 
  - `True` - Runs continuously, checking for new calls periodically
  - `False` - Runs once and exits
- **`interval`**: Seconds between checks when `continuous=True` (default: 300 = 5 minutes)

## 📁 Output Files

### Recordings Directory
- **Audio Format**: `{call_sid}_{timestamp}.mp3`
- **Example**: `53b09f838a420b1ebeed15f3452c19c3_20251203_190626.mp3`
- **Metadata Format**: `{call_sid}_metadata.json`
- **Example**: `53b09f838a420b1ebeed15f3452c19c3_metadata.json`

### Transcriptions Directory
- **Format**: `{call_sid}_{timestamp}_{transcription_timestamp}.txt`
- **Example**: `53b09f838a420b1ebeed15f3452c19c3_20251203_190626_20251203_190627.txt`

### Transcription File Format:

```
FILE: recordings/53b09f838a420b1ebeed15f3452c19c3_20251203_190626.mp3
CALL SID: 53b09f838a420b1ebeed15f3452c19c3
DATE: 2025-12-03 19:06:27
============================================================

FULL TRANSCRIPTION:
------------------------------------------------------------
नमस्ते, मैं आपकी कैसे मदद कर सकता हूं? हां, मुझे आपकी सेवाओं के बारे में जानकारी चाहिए।

SPEAKER DIARIZATION:
------------------------------------------------------------

Speaker 0: नमस्ते, मैं आपकी कैसे मदद कर सकता हूं?

Speaker 1: हां, मुझे आपकी सेवाओं के बारे में जानकारी चाहिए।
```

### Metadata File Format:

```json
{
  "call_sid": "53b09f838a420b1ebeed15f3452c19c3",
  "from": "09466584717",
  "to": "09138366566",
  "direction": "inbound",
  "duration": 45,
  "timestamp": "2025-12-03T19:06:27",
  "downloaded_at": "2025-12-03T19:06:30.123456"
}
```

## 🔍 Monitoring

The script provides real-time status updates:

```
================================================================================
EXOTEL CALL RECORDER & TRANSCRIBER (DEEPGRAM)
================================================================================
Recordings saved to: E:\IDEA FOUNDATION 1\Transcriber\call_transcriber\recordings
Transcriptions saved to: E:\IDEA FOUNDATION 1\Transcriber\call_transcriber\transcriptions
================================================================================

[2025-12-03 19:06:27] Checking for new calls...
Found 6 calls in the last 24 hours
Processing last call: 53b09f838a420b1ebeed15f3452c19c3

================================================================================
Processing Call: 53b09f838a420b1ebeed15f3452c19c3
From: 09466584717 → To: 09138366566
Direction: inbound | Duration: 45s
================================================================================
✓ Downloaded: 53b09f838a420b1ebeed15f3452c19c3_20251203_190626.mp3
🎙️  Transcribing: recordings/53b09f838a420b1ebeed15f3452c19c3_20251203_190626.mp3

Full Transcription:
नमस्ते, मैं आपकी कैसे मदद कर सकता हूं? हां, मुझे आपकी सेवाओं के बारे में जानकारी चाहिए।

============================================================

Speaker Diarization:

Speaker 0: नमस्ते, मैं आपकी कैसे मदद कर सकता हूं?

Speaker 1: हां, मुझे आपकी सेवाओं के बारे में जानकारी चाहिए।

============================================================
✅ Transcription saved to: transcriptions/53b09f838a420b1ebeed15f3452c19c3_20251203_190626_20251203_190627.txt
✓ Saved metadata: 53b09f838a420b1ebeed15f3452c19c3_metadata.json
✓ Successfully processed call 53b09f838a420b1ebeed15f3452c19c3
```

## ⚙️ Configuration

### Change Lookback Period

```python
# Check last 48 hours instead of 24
recorder.run(hours=48, continuous=True, interval=300)
```

### Change Check Interval

```python
# Check every 10 minutes instead of 5
recorder.run(hours=24, continuous=True, interval=600)
```

### Change Language

Edit the `transcribe_audio_deepgram` method in `call_recorder.py`:

```python
options = {
    'punctuate': True,
    'diarize': True,
    'language': 'en'  # Change to 'en' for English, 'hi' for Hindi
}
```

Supported languages: `en`, `hi`, `es`, `fr`, `de`, `it`, `pt`, `ru`, `ja`, `ko`, `zh`, and more.

### Disable Speaker Diarization

```python
options = {
    'punctuate': True,
    'diarize': False,  # Disable speaker diarization
    'language': 'hi'
}
```

### Process All Calls (Not Just Last)

Edit the `run()` method to process all calls instead of just the last one.

## 🐛 Troubleshooting

### Error: "Error fetching calls"
- **Cause**: Invalid Exotel credentials or network issue
- **Solution**: 
  - Verify your `.env` file has correct Exotel credentials
  - Check your internet connection
  - Verify Exotel API access

### Error: "Error transcribing with Deepgram"
- **Cause**: Deepgram API key invalid or network issue
- **Solution**: 
  - Verify `DEEPGRAM_API_KEY` in `.env`
  - Check Deepgram account status
  - Ensure you have API credits

### Error: "No recording available"
- **Cause**: Call doesn't have a recording
- **Solution**: This is normal - the script skips calls without recordings

### Error: "Last call already processed"
- **Cause**: The most recent call was already transcribed
- **Solution**: This is expected behavior - wait for a new call

### Error: "Skipping incomplete call"
- **Cause**: Call status is not 'completed'
- **Solution**: This is normal - the script only processes completed calls

## 📝 Notes

- The script processes **only the most recent call** to avoid processing duplicates
- Calls must have status `completed` and a `RecordingUrl` to be processed
- Transcription typically takes 5-15 seconds depending on audio length
- Speaker labels (Speaker 0, Speaker 1) are automatically assigned by Deepgram
- The script tracks processed calls in memory (resets on restart)
- Uses async/await for efficient Deepgram API calls

## 🔒 Security

- **Never commit `.env` file** to version control
- Keep your API keys secure
- Add `.env` to `.gitignore`:
  ```
  .env
  recordings/
  transcriptions/
  *.mp3
  *.wav
  ```

## 📞 Support

For issues related to:
- **Exotel API**: Contact Exotel support
- **Deepgram API**: Check [Deepgram Documentation](https://developers.deepgram.com)
- **Script Issues**: Check error messages and verify configuration

## 📄 License

This script is provided as-is for use with Exotel and Deepgram services.

---

**Last Updated**: December 2025
