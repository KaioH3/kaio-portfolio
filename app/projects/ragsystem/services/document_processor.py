"""
Document Processing Service
PDF/TXT parsing, chunking, and text extraction
"""
import PyPDF2
import tiktoken
import hashlib
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime
import logging

from ..config import rag_config
from ..models import DocumentMetadata

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Process documents into chunks for embedding"""
    
    def __init__(self):
        self.tokenizer = tiktoken.get_encoding("cl100k_base")  # GPT-4 tokenizer
        self.chunk_size = rag_config.CHUNK_SIZE
        self.chunk_overlap = rag_config.CHUNK_OVERLAP
    
    def process_file(self, file_path: Path, filename: str) -> Tuple[List[str], List[DocumentMetadata]]:
        """
        Process uploaded file into chunks with metadata
        
        Args:
            file_path: Path to uploaded file
            filename: Original filename
            
        Returns:
            Tuple of (chunks, metadata_list)
        """
        try:
            # Extract text based on file type
            if file_path.suffix.lower() == '.pdf':
                text = self._extract_pdf(file_path)
            elif file_path.suffix.lower() in ['.txt', '.md']:
                text = self._extract_text(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_path.suffix}")
            
            # Generate document ID
            doc_id = self._generate_document_id(filename, text)
            
            # Create chunks
            chunks = self._create_chunks(text)
            
            # Create metadata for each chunk
            metadata_list = [
                DocumentMetadata(
                    document_id=doc_id,
                    filename=filename,
                    chunk_index=i,
                    total_chunks=len(chunks),
                    page_number=None  # TODO: Track page numbers in PDF
                )
                for i in range(len(chunks))
            ]
            
            logger.info(f"Processed {filename}: {len(chunks)} chunks created")
            return chunks, metadata_list
            
        except Exception as e:
            logger.error(f"Error processing {filename}: {str(e)}")
            raise
    
    def _extract_pdf(self, file_path: Path) -> str:
        """Extract text from PDF file"""
        text_parts = []
        
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_parts.append(page_text)
                except Exception as e:
                    logger.warning(f"Error extracting page {page_num}: {e}")
                    continue
        
        return "\n\n".join(text_parts)
    
    def _extract_text(self, file_path: Path) -> str:
        """Extract text from TXT/MD file"""
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    
    def _create_chunks(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks based on token count
        
        Uses sliding window approach for better context preservation
        """
        # Tokenize entire text
        tokens = self.tokenizer.encode(text)
        
        chunks = []
        start_idx = 0
        
        while start_idx < len(tokens):
            # Get chunk tokens
            end_idx = start_idx + self.chunk_size
            chunk_tokens = tokens[start_idx:end_idx]
            
            # Decode back to text
            chunk_text = self.tokenizer.decode(chunk_tokens)
            
            # Clean and add chunk
            chunk_text = chunk_text.strip()
            if chunk_text:
                chunks.append(chunk_text)
            
            # Move window with overlap
            start_idx += (self.chunk_size - self.chunk_overlap)
        
        return chunks
    
    def _generate_document_id(self, filename: str, content: str) -> str:
        """Generate unique document ID from filename + content hash"""
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return f"{Path(filename).stem}_{timestamp}_{content_hash}"
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.tokenizer.encode(text))
