from openai import OpenAI
from app.core.config import settings

client = OpenAI(api_key=settings.openai_api_key)

def transcribe_video(file_path: str) -> str:
    with open(file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )

    return transcript.text