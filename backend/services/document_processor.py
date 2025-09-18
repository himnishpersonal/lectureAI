"""Document processing service for parsing PDF and DOCX files."""

import os
import json
from typing import List, Dict, Any
from pathlib import Path

try:
    import PyPDF2
    from docx import Document as DocxDocument
except ImportError:
    PyPDF2 = None
    DocxDocument = None

from ..utils.config import get_settings

class DocumentProcessor:
    """Service for processing documents and extracting text."""
    
    def __init__(self):
        self.settings = get_settings()
        self.chunk_size = self.settings.CHUNK_SIZE
        self.chunk_overlap = self.settings.CHUNK_OVERLAP
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        if not PyPDF2:
            raise ImportError("PyPDF2 not installed. Run: pip install PyPDF2")
        
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        if not DocxDocument:
            raise ImportError("python-docx not installed. Run: pip install python-docx")
        
        try:
            doc = DocxDocument(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"Error extracting text from DOCX: {str(e)}")
    
    def extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from TXT file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
        except Exception as e:
            raise Exception(f"Error reading TXT file: {str(e)}")
    
    def extract_text(self, file_path: str) -> str:
        """Extract text from file based on extension."""
        file_extension = Path(file_path).suffix.lower()
        
        if file_extension == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif file_extension == '.docx':
            return self.extract_text_from_docx(file_path)
        elif file_extension == '.txt':
            return self.extract_text_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
    
    def create_chunks(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Split text into chunks with overlap using token-based chunking."""
        if not text:
            return []
        
        chunks = []
        
        # Simple token-based splitting (approximate 4 chars per token)
        tokens_per_chunk = 500
        overlap_tokens = 100
        chars_per_token = 4
        
        chunk_size_chars = tokens_per_chunk * chars_per_token
        overlap_chars = overlap_tokens * chars_per_token
        
        # Split text into sentences for better chunk boundaries
        sentences = self._split_into_sentences(text)
        
        current_chunk = ""
        current_chunk_sentences = []
        
        for sentence in sentences:
            # Check if adding this sentence would exceed chunk size
            if len(current_chunk + sentence) > chunk_size_chars and current_chunk:
                # Create chunk from current sentences
                chunk_metadata = {
                    "chunk_index": len(chunks),
                    "sentence_count": len(current_chunk_sentences),
                    "char_count": len(current_chunk),
                    "estimated_tokens": len(current_chunk) // chars_per_token
                }
                
                if metadata:
                    chunk_metadata.update(metadata)
                
                chunks.append({
                    "text": current_chunk.strip(),
                    "metadata": chunk_metadata
                })
                
                # Start new chunk with overlap
                if len(chunks) > 0:
                    # Take last few sentences for overlap
                    overlap_sentences = current_chunk_sentences[-2:] if len(current_chunk_sentences) > 2 else current_chunk_sentences
                    current_chunk = " ".join(overlap_sentences) + " " + sentence
                    current_chunk_sentences = overlap_sentences + [sentence]
                else:
                    current_chunk = sentence
                    current_chunk_sentences = [sentence]
            else:
                current_chunk += " " + sentence if current_chunk else sentence
                current_chunk_sentences.append(sentence)
        
        # Add final chunk if there's remaining text
        if current_chunk:
            chunk_metadata = {
                "chunk_index": len(chunks),
                "sentence_count": len(current_chunk_sentences),
                "char_count": len(current_chunk),
                "estimated_tokens": len(current_chunk) // chars_per_token
            }
            
            if metadata:
                chunk_metadata.update(metadata)
            
            chunks.append({
                "text": current_chunk.strip(),
                "metadata": chunk_metadata
            })
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences for better chunk boundaries."""
        import re
        
        # Simple sentence splitting on periods, exclamation marks, and question marks
        # followed by whitespace and capital letter
        sentence_pattern = r'(?<=[.!?])\s+(?=[A-Z])'
        sentences = re.split(sentence_pattern, text)
        
        # Clean up sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def process_document(self, file_path: str, document_id: int) -> Dict[str, Any]:
        """Process a document: extract text and create chunks."""
        try:
            # Extract text
            text = self.extract_text(file_path)
            
            if not text:
                raise ValueError("No text extracted from document")
            
            # Create metadata
            file_metadata = {
                "document_id": document_id,
                "filename": Path(file_path).name,
                "file_type": Path(file_path).suffix.lower(),
                "file_size": os.path.getsize(file_path),
                "total_chars": len(text),
                "total_words": len(text.split())
            }
            
            # Create chunks
            chunks = self.create_chunks(text, file_metadata)
            
            # Save chunks to disk (optional)
            chunks_dir = Path(self.settings.CHUNKS_DIR)
            chunks_dir.mkdir(parents=True, exist_ok=True)
            
            chunks_file = chunks_dir / f"document_{document_id}_chunks.json"
            with open(chunks_file, 'w', encoding='utf-8') as f:
                json.dump(chunks, f, ensure_ascii=False, indent=2)
            
            return {
                "success": True,
                "text": text,
                "chunks": chunks,
                "metadata": file_metadata,
                "chunks_file": str(chunks_file)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "chunks": [],
                "metadata": {}
            }
    
    def get_document_stats(self, file_path: str) -> Dict[str, Any]:
        """Get basic statistics about a document."""
        try:
            text = self.extract_text(file_path)
            
            return {
                "char_count": len(text),
                "word_count": len(text.split()),
                "line_count": len(text.split('\n')),
                "estimated_chunks": len(self.create_chunks(text))
            }
        except Exception as e:
            return {"error": str(e)}
    
    def process_text(self, text: str, document_id: int, filename: str = "transcript") -> Dict[str, Any]:
        """Process raw text (e.g., from transcription) into chunks."""
        try:
            if not text or not text.strip():
                return {
                    "success": False,
                    "error": "Empty text provided",
                    "chunks": [],
                    "metadata": {}
                }
            
            # Create chunks from the text
            chunks = self.create_chunks(text.strip())
            
            # The chunks already come with text and metadata from create_chunks
            processed_chunks = []
            for chunk in chunks:
                chunk_text = chunk["text"]
                chunk_metadata = chunk["metadata"].copy()
                
                # Add additional metadata
                chunk_metadata.update({
                    "document_id": document_id,
                    "filename": filename,
                })
                
                chunk_data = {
                    "text": chunk_text,
                    "metadata": chunk_metadata
                }
                processed_chunks.append(chunk_data)
            
            # Save chunks to file
            chunks_file = os.path.join(
                self.settings.CHUNKS_DIR, 
                f"document_{document_id}_chunks.json"
            )
            
            # Ensure chunks directory exists
            os.makedirs(self.settings.CHUNKS_DIR, exist_ok=True)
            
            with open(chunks_file, 'w', encoding='utf-8') as f:
                json.dump(processed_chunks, f, indent=2, ensure_ascii=False)
            
            return {
                "success": True,
                "chunks": processed_chunks,
                "metadata": {
                    "total_chunks": len(processed_chunks),
                    "total_chars": len(text),
                    "total_words": len(text.split()),
                    "chunks_file": chunks_file,
                    "source_type": "text_input"
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "chunks": [],
                "metadata": {}
            }