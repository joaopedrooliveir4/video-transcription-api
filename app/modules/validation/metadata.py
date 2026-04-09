import ffmpeg

def get_video_metadata(file_path: str) -> dict:
    probe = ffmpeg.probe(file_path)

    duration = float(probe['format']['duration'])
    has_audio = any(s['codec_type'] == 'audio' for s in probe['streams'])

    return {
        'duration': duration,
        'has_audio': has_audio
    }