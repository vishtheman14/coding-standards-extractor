"""
Document Watcher Module

Monitors directories for document changes and triggers policy extraction.
"""

import os
import time
import logging
from pathlib import Path
from typing import Callable, Optional, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

logger = logging.getLogger(__name__)


class DocumentEventHandler(FileSystemEventHandler):
    """Handles file system events for document changes."""

    SUPPORTED_EXTENSIONS = {".md", ".txt", ".rst", ".yaml", ".yml", ".json", ".pdf", ".docx"}

    def __init__(
        self,
        on_change_callback: Callable[[Path], None],
        extensions: Optional[Set[str]] = None,
    ):
        super().__init__()
        self.on_change_callback = on_change_callback
        self.extensions = extensions or self.SUPPORTED_EXTENSIONS
        self._debounce_times: dict[str, float] = {}
        self._debounce_delay = 1.0  # seconds

    def _should_process(self, path: str) -> bool:
        """Check if the file should be processed based on extension."""
        return Path(path).suffix.lower() in self.extensions

    def _is_debounced(self, path: str) -> bool:
        """Check if the event should be debounced."""
        current_time = time.time()
        last_time = self._debounce_times.get(path, 0)
        if current_time - last_time < self._debounce_delay:
            return True
        self._debounce_times[path] = current_time
        return False

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events."""
        if not event.is_directory and self._should_process(event.src_path):
            if not self._is_debounced(event.src_path):
                logger.info(f"New document detected: {event.src_path}")
                self.on_change_callback(Path(event.src_path))

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events."""
        if not event.is_directory and self._should_process(event.src_path):
            if not self._is_debounced(event.src_path):
                logger.info(f"Document modified: {event.src_path}")
                self.on_change_callback(Path(event.src_path))


class DocumentWatcher:
    """
    Watches directories for document changes and triggers callbacks.

    Example:
        def handle_document(path):
            print(f"Processing: {path}")

        watcher = DocumentWatcher("/path/to/docs", on_change=handle_document)
        watcher.start()
    """

    def __init__(
        self,
        watch_path: str | Path,
        on_change: Callable[[Path], None],
        recursive: bool = True,
        extensions: Optional[Set[str]] = None,
    ):
        self.watch_path = Path(watch_path)
        self.on_change = on_change
        self.recursive = recursive
        self.extensions = extensions

        if not self.watch_path.exists():
            raise ValueError(f"Watch path does not exist: {self.watch_path}")

        self._observer: Optional[Observer] = None
        self._running = False

    def start(self) -> None:
        """Start watching for document changes."""
        if self._running:
            logger.warning("Watcher is already running")
            return

        handler = DocumentEventHandler(
            on_change_callback=self.on_change,
            extensions=self.extensions,
        )

        self._observer = Observer()
        self._observer.schedule(handler, str(self.watch_path), recursive=self.recursive)
        self._observer.start()
        self._running = True

        logger.info(f"Started watching: {self.watch_path} (recursive={self.recursive})")

    def stop(self) -> None:
        """Stop watching for document changes."""
        if self._observer and self._running:
            self._observer.stop()
            self._observer.join()
            self._running = False
            logger.info("Document watcher stopped")

    def scan_existing(self) -> list[Path]:
        """Scan and return all existing documents in the watch path."""
        documents = []
        extensions = self.extensions or DocumentEventHandler.SUPPORTED_EXTENSIONS

        if self.recursive:
            for ext in extensions:
                documents.extend(self.watch_path.rglob(f"*{ext}"))
        else:
            for ext in extensions:
                documents.extend(self.watch_path.glob(f"*{ext}"))

        logger.info(f"Found {len(documents)} existing documents")
        return sorted(documents)

    def __enter__(self) -> "DocumentWatcher":
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()
