import filetype
import httpx

def is_valid_video_url(url: str) -> bool:
    headers = {"Range": "bytes=0-1023"}

    with httpx.Client() as client:
        response = client.get(url, headers=headers)

    if response.status_code == 206:
        kind = filetype.guess(response.content)
        if kind is None:
            return False
        return kind.mime.startswith("video/")

    return False