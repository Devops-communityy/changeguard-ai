import hashlib
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from pydantic import SecretStr


class KnowledgeBase:
    def __init__(self, persist_path: Path, api_key: str, embedding_model: str) -> None:
        self._store = Chroma(
            collection_name="changeguard-knowledge",
            persist_directory=str(persist_path),
            embedding_function=OpenAIEmbeddings(
                model=embedding_model, openai_api_key=SecretStr(api_key)
            ),
        )

    def ingest(self, root: Path) -> int:
        documents: list[Document] = []
        for path in sorted(root.rglob("*")):
            if path.suffix.lower() not in {".md", ".txt"} or not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            for index, chunk in enumerate(self._chunks(text)):
                documents.append(
                    Document(
                        page_content=chunk,
                        metadata={"source": str(path), "chunk": index},
                    )
                )
        if documents:
            ids = [
                hashlib.sha256(
                    f"{doc.metadata['source']}:{doc.metadata['chunk']}".encode()
                ).hexdigest()
                for doc in documents
            ]
            self._store.add_documents(documents, ids=ids)
        return len(documents)

    def search(self, query: str, limit: int = 4) -> list[Document]:
        return self._store.similarity_search(query, k=limit)

    @staticmethod
    def _chunks(text: str, size: int = 1400, overlap: int = 200) -> list[str]:
        paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
        chunks: list[str] = []
        current = ""
        for paragraph in paragraphs:
            if current and len(current) + len(paragraph) > size:
                chunks.append(current)
                current = current[-overlap:] + "\n\n" + paragraph
            else:
                current = f"{current}\n\n{paragraph}".strip()
        if current:
            chunks.append(current)
        return chunks
