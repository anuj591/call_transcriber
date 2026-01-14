# Transcription Solution - Implementation Approach

## Overview

This document outlines the implementation approach for an automated call transcription solution that integrates Exotel, AWS S3, AWS Lambda, and AssemblyAI API. The system automatically fetches call recordings from Exotel, stores them in S3, and transcribes them using AssemblyAI via serverless Lambda functions.

---

## Architecture Overview

```
Exotel → Lambda (Downloader) → S3 (Recordings) → Lambda (Transcriber) → AssemblyAI → S3 (Transcriptions)
```

**Flow:**
1. Scheduled Lambda polls Exotel API for new recordings
2. Downloads recordings and uploads to S3
3. S3 event triggers transcription Lambda
4. Transcription Lambda processes via AssemblyAI API
5. Results stored back in S3

---

## 1. Accessing Saved Recordings from Exotel

### Authentication

Exotel REST API uses HTTP Basic Authentication requiring:
- **API Key**: Exotel account API key
- **API Token**: Secret token from Exotel dashboard
- **Account SID**: Exotel account identifier
- **Subdomain**: API endpoint (typically `api.exotel.com`)

**Base URL Pattern:**
```
https://{API_KEY}:{API_TOKEN}@{SUBDOMAIN}/v1/Accounts/{ACCOUNT_SID}
```

### Fetching Recordings

**Step 1: Get Call List**
- Endpoint: `GET /v1/Accounts/{ACCOUNT_SID}/Calls.json`
- Query Parameters: `StartTime` and `EndTime` (format: YYYY-MM-DD)
- Response: JSON array of call objects with `RecordingUrl` field

**Step 2: Download Recording**
- Extract `RecordingUrl` from call object
- Make authenticated GET request to recording URL
- Stream audio file (typically MP3 format)

**Step 3: Filtering**
- Only process calls with status `completed`
- Only process calls with `RecordingUrl` available
- Track processed call SIDs to prevent duplicates

---

## 2. Data Transfer: Exotel to S3

### Process

A scheduled Lambda function (triggered by EventBridge) handles the transfer:

1. **Poll Exotel API**: Query for recent calls within specified time range
2. **Download Recording**: Stream download from Exotel to Lambda `/tmp` directory
3. **Upload to S3**: Upload MP3 file to `recordings/{YEAR}/{MONTH}/{CALL_SID}_{TIMESTAMP}.mp3`
4. **Store Metadata**: Save call metadata as JSON to `recordings/{YEAR}/{MONTH}/{CALL_SID}_metadata.json`
5. **Track Processed**: Store processed call SIDs to prevent duplicate downloads


### Network Flow

```
Exotel Servers → Internet → Lambda → AWS Internal Network → S3
```

Data streams from Exotel to Lambda's temporary storage, then uploads to S3 via AWS SDK.

---

## 3. S3 Storage Architecture

### Bucket Structure

```
s3://{BUCKET_NAME}/
├── recordings/
│   ├── {YEAR}/{MONTH}/
│   │   ├── {CALL_SID}_{TIMESTAMP}.mp3
│   │   └── {CALL_SID}_metadata.json
└── transcriptions/
    ├── {YEAR}/{MONTH}/
    │   ├── {CALL_SID}_{TIMESTAMP}.txt
    │   └── {CALL_SID}_transcription.json
```

### Storage Details

- **Recordings**: MP3 audio files with metadata JSON
- **Transcriptions**: Plain text files and structured JSON with speaker diarization
- **Organization**: Year/Month folder structure for efficient querying

---

## 4. Lambda Transcription Function

### Trigger

- **Event**: S3 `ObjectCreated:Put` event
- **Filter**: Objects in `recordings/` prefix with `.mp3` suffix
- **Automatic**: Triggers when new recording is uploaded

### Process Flow

1. **Event Processing**: Extract S3 bucket and object key from event
2. **Download from S3**: Retrieve audio file to Lambda `/tmp`
3. **Upload to AssemblyAI**: Upload audio and receive upload URL
4. **Submit Transcription**: Create transcription job with speaker diarization and language detection
5. **Poll for Completion**: Check status until transcription completes
6. **Retrieve Results**: Fetch transcript with speaker labels
7. **Store in S3**: Upload plain text and JSON transcriptions to `transcriptions/` prefix


## 5. AssemblyAI Integration

### Authentication

- API key stored in AWS Secrets Manager or environment variables
- Retrieved by Lambda at runtime

### Transcription Settings

- **Speaker Diarization**: Enabled (identifies different speakers)
- **Language Detection**: Enabled for Hindi and English
- **Punctuation**: Automatically added
- **Output**: Full transcript + speaker-labeled utterances with timestamps

### API Workflow

1. Upload audio file to AssemblyAI
2. Submit transcription request with configuration
3. Poll status endpoint until completion
4. Retrieve transcript with speaker labels and metadata



