"""
Voice transcription API using Cloud.ru Whisper.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
import httpx
import tempfile
import os
import subprocess

from ..core.config import settings

router = APIRouter()


def convert_webm_to_mp3(webm_content: bytes) -> bytes:
    """Convert webm audio to mp3 using ffmpeg."""
    with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as webm_file:
        webm_file.write(webm_content)
        webm_path = webm_file.name
    
    mp3_path = webm_path.replace('.webm', '.mp3')
    
    try:
        # Convert using ffmpeg
        result = subprocess.run([
            'ffmpeg', '-i', webm_path,
            '-vn',  # No video
            '-acodec', 'libmp3lame',
            '-q:a', '2',  # Good quality
            '-y',  # Overwrite
            mp3_path
        ], capture_output=True, timeout=30)
        
        if result.returncode != 0:
            print(f"FFmpeg error: {result.stderr.decode()}")
            raise Exception("FFmpeg conversion failed")
        
        with open(mp3_path, 'rb') as f:
            mp3_content = f.read()
        
        return mp3_content
    finally:
        # Cleanup temp files
        if os.path.exists(webm_path):
            os.unlink(webm_path)
        if os.path.exists(mp3_path):
            os.unlink(mp3_path)


@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Transcribe audio file to text using Cloud.ru Whisper API.
    Supports: mp3, wav, webm, ogg, m4a
    """
    content_type = file.content_type or ""
    
    if not any(t in content_type for t in ["audio", "webm", "ogg"]):
        raise HTTPException(status_code=400, detail=f"Invalid file type: {content_type}. Use audio files.")
    
    # Read file content
    content = await file.read()
    
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty audio file")
    
    if len(content) > 25 * 1024 * 1024:  # 25MB limit
        raise HTTPException(status_code=400, detail="File too large. Max 25MB.")
    
    # Determine file extension
    filename = file.filename or "audio.webm"
    ext = filename.split(".")[-1] if "." in filename else "webm"
    
    try:
        # Convert webm to mp3 (Cloud.ru doesn't support webm)
        if ext == "webm" or "webm" in content_type:
            print(f"🎤 Converting webm to mp3...")
            content = convert_webm_to_mp3(content)
            ext = "mp3"
            mime_type = "audio/mp3"
        else:
            mime_type = file.content_type or "audio/mpeg"
        
        # Call Cloud.ru Whisper API
        url = "https://foundation-models.api.cloud.ru/v1/audio/transcriptions"
        
        print(f"🎤 Transcribing audio: {len(content)} bytes, ext={ext}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            files = {
                "file": (f"audio.{ext}", content, mime_type)
            }
            data = {
                "model": "openai/whisper-large-v3",
                "response_format": "text",
                "temperature": "0.5",
                "language": "ru"
            }
            headers = {
                "Authorization": f"Bearer {settings.SCIBOX_API_KEY}"
            }
            
            print(f"🎤 Sending to Whisper API...")
            response = await client.post(url, headers=headers, data=data, files=files)
            print(f"🎤 Whisper response: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Whisper API error: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "text": "",
                    "message": f"Ошибка распознавания. Код: {response.status_code}"
                }
            
            # Parse response - may be JSON or plain text
            raw_text = response.text.strip()
            try:
                # Try parsing as JSON first
                import json
                data = json.loads(raw_text)
                text = data.get("text", "").strip()
            except:
                # Plain text response
                text = raw_text
            
            print(f"🎤 Transcribed text: {text}")
            
            if not text or len(text) < 2:
                return {
                    "success": False,
                    "text": "",
                    "message": "Не удалось распознать речь. Попробуйте ещё раз."
                }
            
            return {
                "success": True,
                "text": text,
                "message": "OK"
            }
            
    except httpx.TimeoutException:
        return {"success": False, "text": "", "message": "Таймаут. Попробуйте короче."}
    except Exception as e:
        print(f"Transcription error: {e}")
        return {"success": False, "text": "", "message": f"Ошибка: {str(e)}"}
