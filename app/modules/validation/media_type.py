import filetype

def is_valid_video(file_path: str) -> bool:
    kind = filetype.guess(file_path)
    if kind is None:
        return False
    return kind.mime.startswith('video/')