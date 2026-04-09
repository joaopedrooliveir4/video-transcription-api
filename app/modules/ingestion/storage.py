import tempfile
import os

def save_temp_file(data: bytes) -> str:
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(data)
        tmp.flush()
        tmp.seek(0)

        return tmp.name

def remove_temp_file(file_path: str) -> None:
    os.remove(file_path)