import hashlib

def generate_hash(filepath: str) -> str:
    with open(filepath, 'rb') as f:
        digest = hashlib.file_digest(f, "sha256")
        return digest.hexdigest()