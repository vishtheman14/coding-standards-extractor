"""Tests for the DocumentWatcher module."""

import time
from pathlib import Path
from unittest.mock import Mock

import pytest

from coding_standards_extractor.document_watcher import DocumentWatcher, DocumentEventHandler


class TestDocumentEventHandler:
    """Tests for DocumentEventHandler."""

    def test_should_process_supported_extensions(self):
        """Test that supported extensions are processed."""
        callback = Mock()
        handler = DocumentEventHandler(on_change_callback=callback)

        assert handler._should_process("test.md")
        assert handler._should_process("test.yaml")
        assert handler._should_process("test.json")
        assert not handler._should_process("test.py")
        assert not handler._should_process("test.exe")

    def test_custom_extensions(self):
        """Test using custom extensions."""
        callback = Mock()
        handler = DocumentEventHandler(
            on_change_callback=callback,
            extensions={".custom", ".ext"},
        )

        assert handler._should_process("test.custom")
        assert handler._should_process("test.ext")
        assert not handler._should_process("test.md")


class TestDocumentWatcher:
    """Tests for DocumentWatcher class."""

    @pytest.fixture
    def watch_dir(self, tmp_path):
        """Create a temporary directory for watching."""
        watch_path = tmp_path / "watched"
        watch_path.mkdir()
        return watch_path

    def test_init_with_valid_path(self, watch_dir):
        """Test initializing watcher with valid path."""
        callback = Mock()
        watcher = DocumentWatcher(watch_dir, on_change=callback)

        assert watcher.watch_path == watch_dir
        assert watcher.recursive is True

    def test_init_with_invalid_path(self, tmp_path):
        """Test initializing watcher with invalid path."""
        callback = Mock()
        invalid_path = tmp_path / "nonexistent"

        with pytest.raises(ValueError, match="does not exist"):
            DocumentWatcher(invalid_path, on_change=callback)

    def test_scan_existing_documents(self, watch_dir):
        """Test scanning existing documents."""
        # Create some test files
        (watch_dir / "test1.md").write_text("# Test 1")
        (watch_dir / "test2.yaml").write_text("title: Test 2")
        (watch_dir / "ignored.py").write_text("# Python file")

        callback = Mock()
        watcher = DocumentWatcher(watch_dir, on_change=callback)
        documents = watcher.scan_existing()

        # Should find .md and .yaml, not .py
        assert len(documents) == 2
        extensions = {doc.suffix for doc in documents}
        assert ".md" in extensions
        assert ".yaml" in extensions

    def test_scan_recursive(self, watch_dir):
        """Test recursive scanning."""
        subdir = watch_dir / "subdir"
        subdir.mkdir()
        (watch_dir / "root.md").write_text("# Root")
        (subdir / "nested.md").write_text("# Nested")

        callback = Mock()
        watcher = DocumentWatcher(watch_dir, on_change=callback, recursive=True)
        documents = watcher.scan_existing()

        assert len(documents) == 2

    def test_scan_non_recursive(self, watch_dir):
        """Test non-recursive scanning."""
        subdir = watch_dir / "subdir"
        subdir.mkdir()
        (watch_dir / "root.md").write_text("# Root")
        (subdir / "nested.md").write_text("# Nested")

        callback = Mock()
        watcher = DocumentWatcher(watch_dir, on_change=callback, recursive=False)
        documents = watcher.scan_existing()

        assert len(documents) == 1

    def test_context_manager(self, watch_dir):
        """Test using watcher as context manager."""
        callback = Mock()

        with DocumentWatcher(watch_dir, on_change=callback) as watcher:
            assert watcher._running is True

        assert watcher._running is False

    def test_start_stop(self, watch_dir):
        """Test starting and stopping the watcher."""
        callback = Mock()
        watcher = DocumentWatcher(watch_dir, on_change=callback)

        watcher.start()
        assert watcher._running is True

        watcher.stop()
        assert watcher._running is False

    def test_double_start(self, watch_dir):
        """Test that starting twice doesn't cause issues."""
        callback = Mock()
        watcher = DocumentWatcher(watch_dir, on_change=callback)

        watcher.start()
        watcher.start()  # Should not raise

        assert watcher._running is True
        watcher.stop()

    def test_custom_extensions(self, watch_dir):
        """Test watcher with custom extensions."""
        (watch_dir / "test.custom").write_text("Custom content")
        (watch_dir / "test.md").write_text("# Markdown")

        callback = Mock()
        watcher = DocumentWatcher(
            watch_dir,
            on_change=callback,
            extensions={".custom"},
        )
        documents = watcher.scan_existing()

        assert len(documents) == 1
        assert documents[0].suffix == ".custom"
