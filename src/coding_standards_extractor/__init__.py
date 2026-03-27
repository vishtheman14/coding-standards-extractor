"""
Coding Standards Extractor

A tool for watching documents and extracting coding policies and standards.
"""

__version__ = "1.0.0"

from .document_watcher import DocumentWatcher
from .policy_extractor import PolicyExtractor
from .standards_parser import StandardsParser

__all__ = ["DocumentWatcher", "PolicyExtractor", "StandardsParser"]
