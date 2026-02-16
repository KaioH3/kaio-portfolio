"""
Document Processing Service - PDF/TXT parsing + chunking
Uses pypdf (not PyPDF2) for lighter footprint
"""
import hashlib
from pathlib import Path
from typing import List, Tuple
from datetime import datetime
import logging

from ..config import rag_config
from ..models import DocumentMetadata

logger = logging.getLogger(__name__)


class DocumentProcessor:
    def __init__(self):
        self.chunk_size = rag_config.CHUNK_SIZE
        self.chunk_overlap = rag_config.CHUNK_OVERLAP

    def process_file(self, filepath: Path, filename: str) -> Tuple[List[str], List[DocumentMetadata]]:
        """Process file into chunks with metadata"""
        try:
            ext = Path(filename).suffix.lower()
            if ext == ".pdf":
                pages = self._extract_pdf_pages(filepath)
                text = "\n\n".join(pages)
            elif ext in {".txt", ".md"}:
                text = filepath.read_text(encoding="utf-8")
                pages = [text]
            else:
                raise ValueError(f"Unsupported file type: {ext}")

            if not text.strip():
                raise ValueError("Empty document")

            doc_id = self._generate_document_id(filename, text)
            chunks, page_numbers = self._chunk_text_with_pages(pages)

            metadatas = []
            for i, chunk in enumerate(chunks):
                metadatas.append(DocumentMetadata(
                    document_id=doc_id,
                    filename=filename,
                    chunk_index=i,
                    total_chunks=len(chunks),
                    page_number=page_numbers[i],
                ))

            logger.info(f"Processed {filename}: {len(chunks)} chunks")
            return chunks, metadatas

        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")
            raise

    def _extract_pdf_pages(self, filepath: Path) -> List[str]:
        """Extract text from PDF per page"""
        from pypdf import PdfReader
        reader = PdfReader(str(filepath))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            pages.append(text.strip() if text else "")
        return pages

    def _chunk_text_with_pages(self, pages: List[str]) -> Tuple[List[str], List[int]]:
        """Chunk text while tracking which page each chunk came from"""
        # Build word list with page tracking
        words = []
        word_pages = []
        for page_num, page_text in enumerate(pages, 1):
            page_words = page_text.split()
            words.extend(page_words)
            word_pages.extend([page_num] * len(page_words))

        chunks = []
        page_numbers = []
        start = 0
        while start < len(words):
            end = min(start + self.chunk_size, len(words))
            chunk = " ".join(words[start:end])
            if chunk.strip():
                chunks.append(chunk.strip())
                page_numbers.append(word_pages[start])
            start += self.chunk_size - self.chunk_overlap

        if not chunks and words:
            chunks = [" ".join(words[:2000])]
            page_numbers = [word_pages[0]]

        return chunks, page_numbers

    def _generate_document_id(self, filename: str, content: str) -> str:
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return f"{Path(filename).stem}_{ts}_{content_hash}"
