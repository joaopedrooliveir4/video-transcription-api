# API de Transcrição de Vídeos

API assíncrona para transcrição de vídeos via URL ou upload, com validação, histórico e deduplicação automática.

---

## Pipeline da arquitetura

Fluxograma:
<img width="989" height="660" alt="image" src="https://github.com/user-attachments/assets/23cf3758-7132-4d3e-b92b-defa42c092bc" />

<img width="988" height="808" alt="image" src="https://github.com/user-attachments/assets/67d9d788-921e-4399-b7c8-16bc4af582e6" />

Worker e Status Peding:
<img width="863" height="350" alt="image" src="https://github.com/user-attachments/assets/f4501551-3306-4784-b217-ac573b6310c7" />

---

## Stack

| Camada | Tecnologia |
|---|---|
| Framework | FastAPI |
| Validação | Pydantic |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Banco | PostgreSQL |
| Magic bytes | filetype |
| Metadados de vídeo | ffmpeg-python |
| HTTP async | httpx |
| Testes | pytest + pytest-asyncio |

---

## Estrutura de Pastas

```
app/
├── main.py
├── api/v1/
│   ├── routes/
│   │   ├── transcription.py
│   │   └── status.py
│   └── dependencies.py
├── core/
│   ├── config.py          # MAX_RETRIES, TIMEOUT, MAX_CONCURRENT_JOBS
│   └── exceptions.py
├── modules/
│   ├── ingestion/         # Recebe e armazena o vídeo temporariamente
│   ├── validation/        # filetype, ffprobe, range request
│   ├── transcription/     # Lógica de transcrição
│   └── storage/           # Persistência e backup
├── worker/
│   ├── queue.py
│   └── processor.py
├── models/                # Entidades do banco
├── schemas/               # DTOs de entrada e saída
├── repositories/
└── tests/
    ├── unit/
    ├── integration/
    ├── e2e/
    └── load/
```

---

## Banco de Dados

### Transcription
| Campo | Tipo | Descrição |
|---|---|---|
| id | UUID | Identificador único |
| hash | string | Hash do conteúdo — deduplicação |
| content | text | Texto transcrito |
| created_at | timestamp | Data de criação |

### Job
| Campo | Tipo | Descrição |
|---|---|---|
| id | UUID | Identificador único |
| transcription_id | UUID FK | Nullable — preenchido ao concluir |
| status | enum | pending → processing → completed / error |
| source_url | string | Preenchido se entrada via URL |
| file_path | string | Preenchido se entrada via upload |
| retry_count | int | Contador de tentativas |
| created_at | timestamp | Criação do job |
| updated_at | timestamp | Última atualização |
| started_at | timestamp | Início do processamento |
| finished_at | timestamp | Fim do processamento |

### JobLog
| Campo | Tipo | Descrição |
|---|---|---|
| id | UUID | Identificador único |
| job_id | UUID FK | Referência ao Job |
| message | string | Ex: "Validando duração do vídeo" |
| status | enum | ok / error |
| created_at | timestamp | Timestamp do log |

---

## Endpoints

### POST /transcriptions
Envia um vídeo para transcrição. Apenas `source_url` ou `file_path` — nunca os dois.

```json
// Request
{ "source_url": "https://..." }

// Response 201
{ "id": "abc-123", "status": "pending" }
```

### GET /transcriptions/{id}
Acompanha o status de um job via polling.

```json
// Response 200
{
  "id": "abc-123",
  "status": "processing",
  "logs": [
    { "message": "Validando integridade do vídeo", "status": "ok", "created_at": "..." },
    { "message": "Validando duração do vídeo", "status": "error", "created_at": "..." }
  ]
}
```

### GET /transcriptions
Histórico paginado de transcrições.

```json
// Response 200
{
  "page": 1,
  "total": 50,
  "items": [
    { "id": "abc-123", "status": "completed", "created_at": "..." }
  ]
}
```

---

## Worker

Processo separado da API. Faz polling no banco buscando jobs `pending`.

**Fluxo:**
1. `SELECT FOR UPDATE SKIP LOCKED` — pega e trava o job
2. Status → `processing`, registra `started_at`
3. Processa com timeout configurável
4. **Sucesso** → status `completed`, salva transcrição, registra `finished_at`
5. **Falha/Timeout** → incrementa `retry_count`, volta para `pending`
6. **Falha definitiva** → `retry_count` atingiu o limite, status `error`

---

## Testes

| Nível | O que testa |
|---|---|
| Unitário | Regras de negócio isoladas — validação de entrada, magic bytes, duração, áudio |
| Integração | Persistência no banco, processamento pelo worker, geração de logs |
| E2E | Fluxo completo — upload, polling, transcrição, histórico |
| Carga | Capacidade máxima de requisições simultâneas e tempo de resposta sob sobrecarga |
