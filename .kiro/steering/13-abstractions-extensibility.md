# Abstractions & Extensibility Standards

## The Core Rule
Every external dependency (LLM, file storage, email) is hidden behind an interface.
Swapping providers = changing one config value, not rewriting code.

## LLM Provider Abstraction
```python
# llm/base.py — NEVER instantiate providers directly outside factory
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

class LLMProvider(ABC):
    @abstractmethod
    async def stream_chat(
        self,
        system_prompt: str,
        messages: list[dict],
        max_tokens: int = 1024,
        temperature: float = 0.1
    ) -> AsyncGenerator[str, None]:
        """Yields token strings. Raises LLMUnavailableError on failure."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Returns True if provider is reachable."""
        ...

# llm/factory.py — the ONLY place providers are instantiated
def get_llm_provider() -> LLMProvider:
    match settings.LLM_PROVIDER:
        case "groq":        return GroqProvider()
        case "huggingface": return HuggingFaceProvider()
        case "ollama":      return OllamaProvider()      # easy to add new
        case _: raise ValueError(f"Unknown provider: {settings.LLM_PROVIDER}")
```
Adding a new LLM = create a new class in `llm/` + add a case to factory. Zero other changes.

## Storage Backend Abstraction
```python
# documents/storage.py
from abc import ABC, abstractmethod

class StorageBackend(ABC):
    @abstractmethod
    async def save(self, file_data: bytes, path: str) -> str:
        """Save file, return the storage path/key."""
        ...

    @abstractmethod
    async def read(self, path: str) -> bytes:
        """Read file by path."""
        ...

    @abstractmethod
    async def delete(self, path: str) -> None:
        ...

    @abstractmethod
    def get_storage_path(self, user_id: str, doc_id: str, filename: str) -> str:
        """Generate the path for a new file."""
        ...

class LocalFileStorage(StorageBackend):
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)

    def get_storage_path(self, user_id, doc_id, filename):
        return str(self.base_dir / user_id / doc_id / secure_filename(filename))

    async def save(self, file_data, path):
        full_path = Path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(full_path, "wb") as f:
            await f.write(file_data)
        return path

# S3Storage would implement the same interface
# Switching: change settings.STORAGE_BACKEND = "s3"

def get_storage_backend() -> StorageBackend:
    match settings.STORAGE_BACKEND:
        case "local": return LocalFileStorage(settings.UPLOAD_DIR)
        case "s3":    return S3Storage(settings.S3_BUCKET)
        case _: raise ValueError(f"Unknown storage: {settings.STORAGE_BACKEND}")
```

## Document Parser Abstraction
```python
# processing/parser.py
from abc import ABC, abstractmethod

class DocumentParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> str:
        """Extract plain text from file. Raises DocumentProcessingError on failure."""
        ...

class PdfParser(DocumentParser):
    def parse(self, file_path):
        import fitz   # PyMuPDF
        doc = fitz.open(file_path)
        return "\n\n".join([page.get_text() for page in doc])

class DocxParser(DocumentParser):
    def parse(self, file_path):
        from docx import Document
        doc = Document(file_path)
        return "\n\n".join([para.text for para in doc.paragraphs if para.text.strip()])

class TxtParser(DocumentParser):
    def parse(self, file_path):
        with open(file_path, encoding="utf-8", errors="replace") as f:
            return f.read()

# Registry pattern — adding a new format = one line here
PARSERS: dict[str, type[DocumentParser]] = {
    "application/pdf": PdfParser,
    "text/plain": TxtParser,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DocxParser,
}

def get_parser(mime_type: str) -> DocumentParser:
    cls = PARSERS.get(mime_type)
    if not cls:
        raise UnsupportedFileTypeError(f"No parser for {mime_type}")
    return cls()
```

## Feature Flag Pattern (for Future Features)
```python
# app/config.py
class Settings(BaseSettings):
    # Feature flags — set to False to disable in-progress features
    FEATURE_MULTI_DOCUMENT: bool = False    # allow >1 doc per user
    FEATURE_DOC_SHARING: bool = False       # public share links
    FEATURE_WEBHOOK_NOTIFY: bool = False    # webhook on doc ready

# Usage in service layer
if not settings.FEATURE_MULTI_DOCUMENT:
    existing = await document_service.count_documents(db, user_id)
    if existing >= 1:
        raise HTTPException(400, "Multi-document support coming soon")
```
Gate new features with flags — enables safe incremental rollout.

## Extensibility Checklist (Run This Before Finalizing Any Module)
Before writing a module, ask:
- [ ] If we add a second LLM provider, does this code change? (it shouldn't)
- [ ] If we move from local storage to S3, does this code change? (it shouldn't)
- [ ] If we add a new file type (e.g. .csv), is it one file + one registry entry? (it should be)
- [ ] If a user uploads 10 documents, does the collection/query logic still work? (it should)
- [ ] If we add a `deleted_at` soft-delete, how many files change? (should be 1-2)
