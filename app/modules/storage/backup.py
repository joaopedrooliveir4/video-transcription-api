import json
from uuid import UUID

def save_as_txt(job_id: UUID, content: str) -> str:
    file_path = f"backup_{job_id}.txt"
    with open(file_path, "w") as file:
        file.write(content)

    return file_path

def save_as_json(job_id: UUID, content: str) -> str:
    file_path = f"backup_{job_id}.json"
    with open(file_path, "w") as file:
        json.dump(content, file, indent=4)

    return file_path