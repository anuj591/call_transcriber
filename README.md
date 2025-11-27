# Exotel Call Recorder & Transcriber

An automated system that fetches call recordings from Exotel, downloads them, and transcribes them using AssemblyAI's transcription service with speaker diarization support.

## 📋 Overview

This system automatically:
- Fetches call recordings from your Exotel account
- Downloads the audio files locally
- Transcribes them using AssemblyAI API (supports Hindi + English)
- Identifies different speakers in the conversation
- Saves transcriptions with metadata to text files
- Processes only the most recent call to avoid duplicates

## 🚀 Features

- **Automated Processing**: Continuously monitors for new calls
- **Multi-language Support**: Handles Hindi and English (auto-detection)
- **Speaker Diarization**: Identifies and labels different speakers (Person A, Person B, etc.)
- **Error Handling**: Robust error handling with retry logic
- **Organized Storage**: Saves recordings and transcriptions in separate directories
- **Metadata Tracking**: Includes call details (SID, phone numbers, duration, timestamp)

## 📦 Prerequisites

- Python 3.7 or higher
- Exotel account with API credentials
- AssemblyAI API key (get it from [assemblyai.com](https://www.assemblyai.com))

## 🔧 Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `requests` - For API calls
- `python-dotenv` - For environment variable management

### 2. Get API Credentials

#### Exotel Credentials:
1. Log in to your Exotel dashboard
2. Go to Settings → API Settings
3. Copy your:
   - **API Key** (usually your account SID)
   - **API Token** (secret token)
   - **Account SID** (your Exotel account identifier)

#### AssemblyAI Credentials:
1. Sign up at [assemblyai.com](https://www.assemblyai.com)
2. Go to your dashboard
3. Copy your **API Key**

### 3. Create Environment File

Create a `.env` file in the project root directory:

```env
# Exotel API Credentials
EXOTEL_API_KEY=your_exotel_api_key
EXOTEL_API_TOKEN=your_exotel_api_token
EXOTEL_SID=your_exotel_account_sid
EXOTEL_SUBDOMAIN=api.exotel.com

# AssemblyAI API Key
ASSEMBLYAI_API_KEY=your_assemblyai_api_key
```

**Example:**
```env
EXOTEL_API_KEY=ideafoundation1
EXOTEL_API_TOKEN=abc123xyz789...
EXOTEL_SID=ideafoundation1
EXOTEL_SUBDOMAIN=api.exotel.com
ASSEMBLYAI_API_KEY=a1b2c3d4e5f6...
```

### 4. Directory Structure

The script automatically creates these directories:
```
Transcriber/
├── recordings/          # Downloaded audio files (.mp3)
├── transcriptions/       # Transcription text files (.txt)
├── .env                 # Your credentials (not tracked in git)
├── call_recorder.py     # Main script
└── requirements.txt     # Python dependencies
```

## 🎯 How It Works

### System Flow:

1. **Fetch Calls**: Queries Exotel API for calls from the last 24 hours
2. **Filter & Sort**: 
   - Filters only completed calls with recordings
   - Sorts by date (most recent first)
   - Processes only the last call to avoid duplicates
3. **Download**: Downloads the audio recording to local storage
4. **Transcribe**: 
   - Uploads audio to AssemblyAI
   - Submits transcription request with Hindi language support
   - Polls for completion (checks every 5 seconds)
   - Retrieves transcript with speaker labels
5. **Format**: Formats transcription with speaker labels (Person A, Person B, etc.)
6. **Save**: Saves transcription with metadata to a text file

### Transcription Process:

```
Audio File → Upload to AssemblyAI → Submit Request → Poll Status → Get Transcript
```

- **Language**: Hindi (auto-detects English)
- **Speaker Diarization**: Enabled (identifies different speakers)
- **Polling**: Checks every 5 seconds, timeout after 5 minutes

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
- **Format**: `{call_sid}_{timestamp}.mp3`
- **Example**: `a87d41db671503dc74bedf83580219br_20251127_124004.mp3`

### Transcriptions Directory
- **Format**: `{call_sid}_{timestamp}.txt`
- **Example**: `a87d41db671503dc74bedf83580219br_20251127_124004.txt`

### Transcription File Format:

```
================================================================================
CALL RECORDING TRANSCRIPTION
================================================================================

Call SID: a87d41db671503dc74bedf83580219br
From: 09466584717
To: 09138366566
Direction: inbound
Duration: 45 seconds
Timestamp: 2025-11-27 12:07:45

================================================================================
TRANSCRIPTION:
================================================================================

Person A: Hello, how can I help you?

Person B: I need information about your services.

Person A: Sure, let me provide you with the details.

...
================================================================================
```

## 🔍 Monitoring

The script provides real-time status updates:

```
================================================================================
EXOTEL CALL RECORDER & TRANSCRIBER
================================================================================
Recordings saved to: E:\IDEA FOUNDATION 1\Transcriber\recordings
Transcriptions saved to: E:\IDEA FOUNDATION 1\Transcriber\transcriptions
================================================================================

[2025-11-27 12:45:52] Checking for new calls...
Found 6 calls in the last 24 hours
Processing last call: a87d41db671503dc74bedf83580219br

================================================================================
Processing Call: a87d41db671503dc74bedf83580219br
From: 09466584717 → To: 09138366566
Direction: inbound | Duration: 45s
================================================================================
✓ Downloaded: a87d41db671503dc74bedf83580219br_20251127_124004.mp3
Transcribing audio with AssemblyAI...
  Waiting for transcription... (5s)
  Waiting for transcription... (10s)
✓ Saved transcription: a87d41db671503dc74bedf83580219br_20251127_124004.txt
✓ Successfully processed call a87d41db671503dc74bedf83580219br
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

### Process All Calls (Not Just Last)

Edit the `run()` method to process all calls instead of just the last one.

## 🐛 Troubleshooting

### Error: "Error fetching calls"
- **Cause**: Invalid Exotel credentials or network issue
- **Solution**: 
  - Verify your `.env` file has correct credentials
  - Check your internet connection
  - Verify Exotel API access

### Error: "Failed to upload audio file"
- **Cause**: AssemblyAI API key invalid or network issue
- **Solution**: 
  - Verify `ASSEMBLYAI_API_KEY` in `.env`
  - Check AssemblyAI account status
  - Ensure you have API credits

### Error: "Transcription timeout"
- **Cause**: Audio file too long or API processing delay
- **Solution**: 
  - Wait and retry
  - Check AssemblyAI service status
  - Verify audio file is valid

### Error: "No recording available"
- **Cause**: Call doesn't have a recording
- **Solution**: This is normal - the script skips calls without recordings

### Error: "Last call already processed"
- **Cause**: The most recent call was already transcribed
- **Solution**: This is expected behavior - wait for a new call

## 📝 Notes

- The script processes **only the most recent call** to avoid processing duplicates
- Calls must have status `completed` and a `RecordingUrl` to be processed
- Transcription typically takes 10-30 seconds depending on audio length
- Speaker labels (Person A, Person B) are automatically assigned by AssemblyAI
- The script tracks processed calls in memory (resets on restart)

## 🔒 Security

- **Never commit `.env` file** to version control
- Keep your API keys secure
- Add `.env` to `.gitignore`:
  ```
  .env
  recordings/
  transcriptions/
  ```

## 📞 Support

For issues related to:
- **Exotel API**: Contact Exotel support
- **AssemblyAI**: Check [AssemblyAI Documentation](https://www.assemblyai.com/docs)
- **Script Issues**: Check error messages and verify configuration

## 📄 License

This script is provided as-is for use with Exotel and AssemblyAI services.

---

**Last Updated**: November 2025

