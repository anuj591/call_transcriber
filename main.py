import base64
import json
import os

from flask import Flask, request, Response
from flask_sock import Sock
import ngrok
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

from twilio_transcriber import TwilioTranscriber

# Flask settings
PORT = 5000
DEBUG = True
INCOMING_CALL_ROUTE = '/'
WEBSOCKET_ROUTE = '/'

# Twilio authentication
account_sid = os.environ['TWILIO_ACCOUNT_SID']
api_key = os.environ['TWILIO_API_KEY_SID']
api_secret = os.environ['TWILIO_API_SECRET']
client = Client(api_key, api_secret, account_sid)

# Twilio phone number to call
TWILIO_NUMBER = os.environ['TWILIO_NUMBER']

# ngrok authentication
ngrok_authtoken = os.getenv("NGROK_AUTHTOKEN")
if not ngrok_authtoken:
    raise ValueError(
        "NGROK_AUTHTOKEN is not set in your .env file. "
        "Please get your authtoken from https://dashboard.ngrok.com/get-started/your-authtoken "
        "and add it to your .env file as: NGROK_AUTHTOKEN=your_authtoken_here"
    )
ngrok.set_auth_token(ngrok_authtoken)
app = Flask(__name__)
sock = Sock(app)

@app.route(INCOMING_CALL_ROUTE, methods=['GET', 'POST'])
def receive_call():
    if request.method == 'POST':
        # Log the incoming request for debugging
        print(f"\n{'='*60}")
        print(f"📞 INCOMING CALL RECEIVED!")
        print(f"{'='*60}")
        print(f"   From: {request.form.get('From', 'Unknown')}")
        print(f"   To: {request.form.get('To', 'Unknown')}")
        print(f"   CallSid: {request.form.get('CallSid', 'Unknown')}")
        print(f"   CallStatus: {request.form.get('CallStatus', 'Unknown')}")
        print(f"   Direction: {request.form.get('Direction', 'Unknown')}")
        
        # Use request.host for WebSocket URL (ngrok will handle the routing)
        # Convert http/https to wss/ws
        websocket_url = f"wss://{request.host}"
        
        print(f"   WebSocket URL: {websocket_url}{WEBSOCKET_ROUTE}")
        print(f"{'='*60}\n")
        
        # Check call direction
        direction = request.form.get('Direction', 'inbound')
        
        # For all call types (inbound, outbound-api, outbound-dial), connect the Media Stream
        # The Stream will capture audio from the call
        print(f"   📞 Call direction: {direction} - connecting Media Stream")
        
        # For test calls, play a message first so there's audio to transcribe
        xml = f"""
        <Response>
            <Say>
                Hello, this is a test call. Please speak now and your words will be transcribed in real time. You can say anything you want, and it will appear in the console. Thank you for testing the transcription system.
            </Say>
            <Pause length="2"/>
            <Connect>
                <Stream url='{websocket_url}{WEBSOCKET_ROUTE}' />
            </Connect>
        </Response>
        """.strip()
        
        return Response(xml, mimetype='text/xml')
    else:
        # GET request - show status page
        status_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Call Transcription Status</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1 {{ color: #333; }}
                .status {{ padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .success {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
                .info {{ background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }}
                .warning {{ background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }}
                code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📞 Real-time Phone Call Transcription</h1>
                <div class="status success">
                    <strong>✅ Server is running!</strong><br>
                    Using Vosk (Free & Offline)
                </div>
                <div class="status info">
                    <strong>ℹ️ Webhook URL:</strong><br>
                    <code>{request.url}</code>
                </div>
                <div class="status info">
                    <strong>ℹ️ WebSocket URL:</strong><br>
                    <code>wss://{request.host}/</code>
                </div>
                <div class="status warning">
                    <strong>⚠️ Next Steps:</strong><br>
                    1. Make sure this URL is set in Twilio Console → Phone Numbers → Your Number → Voice & Fax<br>
                    2. Call your Twilio number: <code>+15394895575</code><br>
                    3. Watch your terminal for transcription output
                </div>
                <div class="status info">
                    <strong>📋 Troubleshooting:</strong><br>
                    • Check <code>CHECK_TWILIO.md</code> for detailed troubleshooting steps<br>
                    • Check Twilio Console → Monitor → Debugger for errors<br>
                    • Verify ngrok tunnel is active (no warning page)
                </div>
            </div>
        </body>
        </html>
        """
        return Response(status_html, mimetype='text/html')

@sock.route(WEBSOCKET_ROUTE)
def transcription_websocket(ws):
    transcriber = None
    media_count = 0
    
    try:
        while True:
            data = json.loads(ws.receive())
            event_type = data.get('event', 'unknown')
            print(f"📨 WebSocket event received: {event_type}")
            match event_type:
                case "connected":
                    print('✅ Twilio connected, starting transcriber...')
                    print(f"   Stream SID: {data.get('streamSid', 'Unknown')}")
                    # Get language from environment variable (optional)
                    # If not set, will auto-detect from available models
                    # Set TRANSCRIPTION_LANGUAGE='hi' for Hindi or 'en' for English
                    language = os.getenv('TRANSCRIPTION_LANGUAGE', None)
                    if language:
                        language = language.lower()
                    # Model will be auto-detected based on language or use default
                    transcriber = TwilioTranscriber(language=language)
                    transcriber.start_transcription()
                case "start":
                    print('🎤 Call started - ready to receive audio')
                    media_count = 0
                case "media": 
                    media_count += 1
                    if media_count % 100 == 0:  # Log every 100 media packets
                        print(f"   📊 Received {media_count} audio packets so far...")
                    if transcriber:
                        # Extract base64 encoded audio payload
                        payload_b64 = data['media']['payload']
                        # Decode from base64 to get μ-law encoded audio
                        payload_mulaw = base64.b64decode(payload_b64)
                        # Process audio with Vosk
                        transcriber.process_audio(payload_mulaw)
                    else:
                        print('⚠️  Warning: Received audio but transcriber not initialized')
                case "stop":
                    print(f'🛑 Call ended (received {media_count} total audio packets)')
                    if transcriber:
                        transcriber.stop_transcription()
                        # Transcript will be saved automatically in stop_transcription()
                    break
    except Exception as e:
        print(f"Error in websocket: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if transcriber:
            try:
                transcriber.stop_transcription()
            except Exception as cleanup_error:
                print(f"Cleanup error: {cleanup_error}")


if __name__ == "__main__":
    # Prevent ngrok from being recreated on Flask reload in debug mode
    # WERKZEUG_RUN_MAIN is set by Flask's reloader - only create tunnel on first run
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        # This is the first run, not a reload
        try:
            # Disconnect any existing ngrok tunnels first
            try:
                ngrok.disconnect()
            except:
                pass
            
            # Open Ngrok tunnel
            listener = ngrok.forward(f"http://localhost:{PORT}")
            ngrok_url = listener.url()
            print(f"Ngrok tunnel opened at {ngrok_url} for port {PORT}")
            print(f"⚠️  NOTE: If using ngrok free tier, the interstitial page may break WebSocket connections.")
            print(f"⚠️  Consider upgrading to ngrok paid plan or using ngrok's bypass header options.\n")

            # Set ngrok URL to be the webhook for the appropriate Twilio number
            twilio_numbers = client.incoming_phone_numbers.list()
            twilio_number_sid = [num.sid for num in twilio_numbers if num.phone_number == TWILIO_NUMBER][0]
            voice_webhook_url = f"{ngrok_url}{INCOMING_CALL_ROUTE}"
            client.incoming_phone_numbers(twilio_number_sid).update(account_sid, voice_url=voice_webhook_url)

            print(f"\n✓ Webhook configured: {voice_webhook_url}")
            print(f"✓ Waiting for calls on {TWILIO_NUMBER}")
            print(f"✓ Call this number to start transcription...\n")
        except Exception as e:
            print(f"⚠️  Warning: Could not set up ngrok tunnel: {e}")
            print("⚠️  Continuing anyway - make sure ngrok is configured manually if needed.\n")
    
    try:
        # run the app
        app.run(port=PORT, debug=DEBUG, use_reloader=True)
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
    finally:
        # Only disconnect on actual exit, not on reload
        if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
            try:
                ngrok.disconnect()
            except:
                pass
