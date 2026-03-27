"""Tests for the StandardsParser module."""

import json
from pathlib import Path

import pytest

from coding_standards_extractor.standards_parser import (
    StandardsParser,
    MarkdownParser,
    YAMLParser,
    JSONParser,
    PlainTextParser,
    ParsedDocument,
)


class TestMarkdownParser:
    """Tests for MarkdownParser."""

    @pytest.fixture
    def parser(self):
        return MarkdownParser()

    def test_can_parse_markdown(self, parser):
        """Test that parser recognizes markdown files."""
        assert parser.can_parse(Path("test.md"))
        assert parser.can_parse(Path("test.markdown"))
        assert not parser.can_parse(Path("test.txt"))

    def test_parse_markdown(self, parser, tmp_path):
        """Test parsing a markdown file."""
        content = """# Main Title

## Section 1

Content of section 1.

## Section 2

Content of section 2.
"""
        file_path = tmp_path / "test.md"
        file_path.write_text(content)

        result = parser.parse(file_path)

        assert isinstance(result, ParsedDocument)
        assert result.title == "Main Title"
        assert result.content_type == "markdown"
        assert len(result.sections) >= 2

    def test_parse_frontmatter(self, parser, tmp_path):
        """Test parsing YAML frontmatter."""
        content = """---
title: My Standards
version: 1.0
---

# Main Content
"""
        file_path = tmp_path / "test.md"
        file_path.write_text(content)

        result = parser.parse(file_path)

        assert result.metadata.get("title") == "My Standards"
        assert result.metadata.get("version") == 1.0


class TestYAMLParser:
    """Tests for YAMLParser."""

    @pytest.fixture
    def parser(self):
        return YAMLParser()

    def test_can_parse_yaml(self, parser):
        """Test that parser recognizes YAML files."""
        assert parser.can_parse(Path("test.yaml"))
        assert parser.can_parse(Path("test.yml"))
        assert not parser.can_parse(Path("test.json"))

    def test_parse_yaml(self, parser, tmp_path):
        """Test parsing a YAML file."""
        content = """title: Coding Standards
rules:
  - Use consistent naming
  - Write tests
  - Document code
"""
        file_path = tmp_path / "test.yaml"
        file_path.write_text(content)

        result = parser.parse(file_path)

        assert isinstance(result, ParsedDocument)
        assert result.title == "Coding Standards"
        assert result.content_type == "yaml"


class TestJSONParser:
    """Tests for JSONParser."""

    @pytest.fixture
    def parser(self):
        return JSONParser()

    def test_can_parse_json(self, parser):
        """Test that parser recognizes JSON files."""
        assert parser.can_parse(Path("test.json"))
        assert not parser.can_parse(Path("test.yaml"))

    def test_parse_json(self, parser, tmp_path):
        """Test parsing a JSON file."""
        content = {
            "title": "API Standards",
            "rules": [
                {"name": "Use REST conventions"},
                {"name": "Version APIs"},
            ],
        }
        file_path = tmp_path / "test.json"
        file_path.write_text(json.dumps(content))

        result = parser.parse(file_path)

        assert isinstance(result, ParsedDocument)
        assert result.title == "API Standards"
        assert result.content_type == "json"


class TestPlainTextParser:
    """Tests for PlainTextParser."""

    @pytest.fixture
    def parser(self):
        return PlainTextParser()

    def test_can_parse_text(self, parser):
        """Test that parser recognizes text files."""
        assert parser.can_parse(Path("test.txt"))
        assert parser.can_parse(Path("test.rst"))
        assert not parser.can_parse(Path("test.md"))

    def test_parse_text(self, parser, tmp_path):
        """Test parsing a text file."""
        content = """Coding Standards Document

These are the rules to follow.
"""
        file_path = tmp_path / "test.txt"
        file_path.write_text(content)

        result = parser.parse(file_path)

        assert isinstance(result, ParsedDocument)
        assert result.content_type == "text"


class TestStandardsParser:
    """Tests for StandardsParser."""

    @pytest.fixture
    def parser(self):
        return StandardsParser()

    def test_supported_extensions(self, parser):
        """Test that parser reports supported extensions."""
        extensions = parser.supported_extensions()

        assert ".md" in extensions
        assert ".yaml" in extensions
        assert ".json" in extensions
        assert ".txt" in extensions

    def test_parse_delegates_to_correct_parser(self, parser, tmp_path):
        """Test that parser delegates to the correct format parser."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test")

        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("title: Test")

        md_result = parser.parse(md_file)
        yaml_result = parser.parse(yaml_file)

        assert md_result.content_type == "markdown"
        assert yaml_result.content_type == "yaml"

    def test_unsupported_format(self, parser, tmp_path):
        """Test handling of unsupported file formats."""
        file_path = tmp_path / "test.xyz"
        file_path.write_text("content")

        with pytest.raises(ValueError, match="No parser available"):
            parser.parse(file_path)
