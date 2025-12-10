"""
Data Sources Package
Multi-source ingestion: OEM manuals, iFixit API, YouTube transcripts
"""

from .ifixit_api import IFixitAPI
from .oem_manual_parser import OEMManualParser
from .youtube_transcript import YouTubeTranscriptFetcher
from .ingestion_pipeline import DataIngestionPipeline

__all__ = [
    "IFixitAPI",
    "OEMManualParser",
    "YouTubeTranscriptFetcher",
    "DataIngestionPipeline"
]
