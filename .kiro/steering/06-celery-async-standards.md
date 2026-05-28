# Celery & Async Processing Standards

## Celery Configuration
```python
# celery_app.py
from celery import Celery

celery_app = Celery(
    "rag_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.processing.worker"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,          # enables STARTED state
    task_acks_late=True,              # ack only after task completes (safer)
    worker_prefetch_multiplier=1,     # one task at a time per worker (memory-safe for ML)
    task_reject_on_worker_lost=True,  # re-queue if worker dies mid-task
    result_expires=3600,              # clean up results after 1h
)
```

## Task Design Rules
- Tasks accept only **serializable primitives** as arguments: `str`, `int`, `UUID as str`
- Never pass ORM objects, Pydantic models, or file handles to tasks
- Always convert UUIDs to strings before passing: `str(doc_id)`
- Tasks must be **idempotent** — safe to run twice on same input

```python
@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,        # 1 min between retries
    name="process_document"
)
def process_document(self, document_id: str) -> dict:
    ...
```

## Processing Task State Machine
Every task must update both `processing_jobs` table AND log at each step:

```
QUEUED (on task creation)
  ↓
RUNNING + progress=0 (task starts)
  ↓
progress=25 (parsing complete)
  ↓
progress=50 (chunking complete)
  ↓
progress=75 (embeddings generated)
  ↓
progress=90 (ChromaDB upsert complete)
  ↓
DONE + progress=100 (all done, document.status=READY)
  ↓ (on any exception)
FAILED + error_detail=str(e) + document.status=FAILED
```
Update `processing_jobs.progress_pct` after each step — the frontend polls this.

## Error Handling in Tasks
```python
try:
    # ... step
except Exception as exc:
    # Update DB first — even if retry fails, user sees the error
    with SyncSessionLocal() as db:
        job = db.get(ProcessingJob, job_id)
        job.status = JobStatus.FAILED
        job.error_detail = str(exc)
        doc = db.get(Document, document_id)
        doc.status = DocumentStatus.FAILED
        doc.error_message = str(exc)
        db.commit()
    
    logger.error("task.process_document.failed", doc_id=document_id, error=str(exc))
    raise self.retry(exc=exc)     # Celery handles retry countdown
```

## DB Access in Celery (Sync)
```python
# ALWAYS use the sync session in Celery tasks — NOT the async one
from app.database import SyncSessionLocal

def process_document(self, document_id: str):
    with SyncSessionLocal() as db:
        document = db.get(Document, UUID(document_id))
        # ... work
        db.commit()
```

## Memory Management
- The embedding model loads once per worker process — NOT per task
- Use the `EmbeddingService` singleton — `EmbeddingService.get_instance()`
- After processing large files, explicitly `del` large variables and call `gc.collect()`
- Batch embedding size: 32 — never encode all chunks at once for large docs
- If a document has > 500 chunks, split into batches of 100 for ChromaDB upsert

## Task Monitoring
- Flower is included in Docker Compose for task monitoring at `:5555`
- Task names must be explicit strings (not auto-generated) for Flower readability
- Always set `name="process_document"` in the task decorator

## Triggering Tasks
```python
# In document service — after saving file and DB record:
from app.processing.worker import process_document

task = process_document.apply_async(
    args=[str(document.id)],
    countdown=1                   # 1s delay — ensures DB record is committed first
)

# Save celery task ID to processing_job record
job.celery_task_id = task.id
```
The `countdown=1` is important — without it, the worker may pick up the task before the DB transaction commits.
