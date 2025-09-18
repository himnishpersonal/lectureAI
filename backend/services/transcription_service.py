"""Transcription service using Faster Whisper for audio processing."""

import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import tempfile
import subprocess

try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    WhisperModel = None

from ..utils.config import get_settings

logger = logging.getLogger(__name__)

class TranscriptionService:
    """Service for transcribing audio files using Faster Whisper."""
    
    def __init__(self):
        self.settings = get_settings()
        self.model = None
        self.model_size = "base"  # Can be: tiny, base, small, medium, large
        self.supported_formats = {'.mp3', '.wav', '.m4a', '.mp4', '.avi', '.mkv', '.webm'}
        
        # Initialize model if available
        if FASTER_WHISPER_AVAILABLE:
            try:
                self._load_model()
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {str(e)}")
                self.model = None
        else:
            logger.warning("faster-whisper not available. Install with: pip install faster-whisper")
    
    def _load_model(self):
        """Load the Whisper model."""
        try:
            logger.info(f"Loading Whisper model: {self.model_size}")
            self.model = WhisperModel(
                self.model_size,
                device="cpu",  # Use "cuda" if you have GPU
                compute_type="int8"  # Optimize for CPU performance
            )
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading Whisper model: {str(e)}")
            raise
    
    def is_available(self) -> bool:
        """Check if transcription service is available."""
        return FASTER_WHISPER_AVAILABLE and self.model is not None
    
    def is_audio_file(self, filename: str) -> bool:
        """Check if file is a supported audio format."""
        file_ext = os.path.splitext(filename.lower())[1]
        return file_ext in self.supported_formats
    
    def get_audio_duration(self, file_path: str) -> Optional[float]:
        """Get audio file duration using ffprobe."""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'csv=p=0', file_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return float(result.stdout.strip())
        except Exception as e:
            logger.warning(f"Could not get audio duration: {str(e)}")
        return None
    
    def convert_to_wav(self, input_path: str) -> str:
        """Convert audio file to WAV format for better Whisper compatibility."""
        try:
            # Create temporary WAV file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_wav_path = temp_file.name
            
            # Convert using ffmpeg
            cmd = [
                'ffmpeg', '-i', input_path, '-acodec', 'pcm_s16le',
                '-ar', '16000', '-ac', '1', '-y', temp_wav_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info(f"Successfully converted {input_path} to WAV")
                return temp_wav_path
            else:
                logger.error(f"FFmpeg conversion failed: {result.stderr}")
                # Clean up temp file
                if os.path.exists(temp_wav_path):
                    os.unlink(temp_wav_path)
                return input_path  # Return original if conversion fails
                
        except Exception as e:
            logger.error(f"Error converting audio: {str(e)}")
            return input_path  # Return original if conversion fails
    
    def transcribe_audio(self, file_path: str, language: str = None) -> Dict[str, Any]:
        """Transcribe audio file and return transcript with metadata."""
        if not self.is_available():
            return {
                "success": False,
                "error": "Transcription service not available. Please install faster-whisper."
            }
        
        try:
            logger.info(f"Starting transcription of: {file_path}")
            
            # Get audio duration
            duration = self.get_audio_duration(file_path)
            
            # Convert to WAV if needed (for better compatibility)
            working_file = file_path
            converted = False
            
            file_ext = os.path.splitext(file_path.lower())[1]
            if file_ext not in ['.wav']:
                working_file = self.convert_to_wav(file_path)
                converted = True
            
            # Transcribe with timestamps
            segments, info = self.model.transcribe(
                working_file,
                language=language,
                word_timestamps=True,
                vad_filter=True,  # Voice activity detection
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            # Process segments
            transcript_parts = []
            timestamped_segments = []
            
            for segment in segments:
                transcript_parts.append(segment.text.strip())
                
                # Create timestamped segment
                timestamped_segments.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip(),
                    "words": [
                        {
                            "word": word.word,
                            "start": word.start,
                            "end": word.end,
                            "probability": word.probability
                        }
                        for word in segment.words
                    ] if hasattr(segment, 'words') and segment.words else []
                })
            
            # Combine transcript
            full_transcript = " ".join(transcript_parts)
            
            # Clean up converted file
            if converted and os.path.exists(working_file):
                try:
                    os.unlink(working_file)
                except:
                    pass
            
            # Create metadata
            metadata = {
                "language": info.language,
                "language_probability": info.language_probability,
                "duration": duration or info.duration,
                "segments_count": len(timestamped_segments),
                "transcribed_at": datetime.utcnow().isoformat(),
                "model_size": self.model_size,
                "segments": timestamped_segments
            }
            
            logger.info(f"Transcription completed. Language: {info.language}, Duration: {duration}s")
            
            return {
                "success": True,
                "transcript": full_transcript,
                "duration": duration or info.duration,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error during transcription: {str(e)}")
            return {
                "success": False,
                "error": f"Transcription failed: {str(e)}"
            }
    
    async def transcribe_audio_async(self, file_path: str, language: str = None) -> Dict[str, Any]:
        """Async wrapper for transcription."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.transcribe_audio, file_path, language)
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported audio formats."""
        return list(self.supported_formats)
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for transcription service."""
        return {
            "status": "available" if self.is_available() else "unavailable",
            "faster_whisper_installed": FASTER_WHISPER_AVAILABLE,
            "model_loaded": self.model is not None,
            "model_size": self.model_size,
            "supported_formats": list(self.supported_formats)
        }
