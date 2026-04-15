"""
Script para iniciar o worker de processamento de transcrições.
Execute com: python run_worker.py
"""
from app.worker.processor import run_worker

if __name__ == "__main__":
    run_worker()
