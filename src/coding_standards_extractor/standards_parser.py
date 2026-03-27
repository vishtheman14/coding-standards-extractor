"""
Standards Parser Module

Parses various document formats to extract coding standards.
"""

import re
import json
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Any
from abc import ABC, abstractmethod

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class ParsedDocument:
    """Represents a parsed document."""

    file_path: str
    content_type: str
    title: Optional[str] = None
    sections: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    raw_content: str = ""


class BaseParser(ABC):
    """Base class for document parsers."""

    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the file."""
        pass

    @abstractmethod
    def parse(self, file_path: Path) -> ParsedDocument:
        """Parse the document and return structured content."""
        pass


class MarkdownParser(BaseParser):
    """Parser for Markdown documents."""

    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in {".md", ".markdown"}

    def parse(self, file_path: Path) -> ParsedDocument:
        content = file_path.read_text(encoding="utf-8")

        # Extract title from first H1
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else None

        # Extract sections
        sections = self._extract_sections(content)

        # Extract metadata from YAML frontmatter
        metadata = self._extract_frontmatter(content)

        return ParsedDocument(
            file_path=str(file_path),
            content_type="markdown",
            title=title,
            sections=sections,
            metadata=metadata,
            raw_content=content,
        )

    def _extract_sections(self, content: str) -> list[dict]:
        """Extract sections from markdown content."""
        sections = []
        current_section = None

        lines = content.split("\n")
        for i, line in enumerate(lines):
            header_match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if header_match:
                if current_section:
                    sections.append(current_section)

                level = len(header_match.group(1))
                title = header_match.group(2).strip()
                current_section = {
                    "level": level,
                    "title": title,
                    "line_number": i + 1,
                    "content": [],
                }
            elif current_section:
                current_section["content"].append(line)

        if current_section:
            current_section["content"] = "\n".join(current_section["content"]).strip()
            sections.append(current_section)

        return sections

    def _extract_frontmatter(self, content: str) -> dict:
        """Extract YAML frontmatter from markdown."""
        if not content.startswith("---"):
            return {}

        end_match = re.search(r"\n---\n", content[3:])
        if not end_match:
            return {}

        frontmatter = content[3 : 3 + end_match.start()]

        if YAML_AVAILABLE:
            try:
                return yaml.safe_load(frontmatter) or {}
            except yaml.YAMLError:
                return {}
        return {}


class YAMLParser(BaseParser):
    """Parser for YAML documents."""

    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in {".yaml", ".yml"}

    def parse(self, file_path: Path) -> ParsedDocument:
        content = file_path.read_text(encoding="utf-8")

        data = {}
        if YAML_AVAILABLE:
            try:
                data = yaml.safe_load(content) or {}
            except yaml.YAMLError as e:
                logger.warning(f"Failed to parse YAML: {e}")

        # Convert YAML structure to sections
        sections = self._yaml_to_sections(data)

        return ParsedDocument(
            file_path=str(file_path),
            content_type="yaml",
            title=data.get("title"),
            sections=sections,
            metadata=data.get("metadata", {}),
            raw_content=content,
        )

    def _yaml_to_sections(self, data: dict, level: int = 1) -> list[dict]:
        """Convert YAML data to sections."""
        sections = []

        if isinstance(data, dict):
            for key, value in data.items():
                if key in {"title", "metadata"}:
                    continue

                section = {
                    "level": level,
                    "title": str(key),
                    "content": "",
                }

                if isinstance(value, str):
                    section["content"] = value
                elif isinstance(value, list):
                    section["content"] = "\n".join(f"- {item}" for item in value if isinstance(item, str))
                    # Recursively process list items that are dicts
                    for item in value:
                        if isinstance(item, dict):
                            sections.extend(self._yaml_to_sections(item, level + 1))
                elif isinstance(value, dict):
                    sections.extend(self._yaml_to_sections(value, level + 1))

                sections.append(section)

        return sections


class JSONParser(BaseParser):
    """Parser for JSON documents."""

    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".json"

    def parse(self, file_path: Path) -> ParsedDocument:
        content = file_path.read_text(encoding="utf-8")

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON: {e}")
            data = {}

        sections = self._json_to_sections(data)

        return ParsedDocument(
            file_path=str(file_path),
            content_type="json",
            title=data.get("title") if isinstance(data, dict) else None,
            sections=sections,
            metadata=data.get("metadata", {}) if isinstance(data, dict) else {},
            raw_content=content,
        )

    def _json_to_sections(self, data: Any, level: int = 1) -> list[dict]:
        """Convert JSON data to sections."""
        sections = []

        if isinstance(data, dict):
            for key, value in data.items():
                if key in {"title", "metadata"}:
                    continue

                section = {
                    "level": level,
                    "title": str(key),
                    "content": "",
                }

                if isinstance(value, str):
                    section["content"] = value
                elif isinstance(value, list):
                    section["content"] = json.dumps(value, indent=2)
                elif isinstance(value, dict):
                    section["content"] = json.dumps(value, indent=2)
                    sections.extend(self._json_to_sections(value, level + 1))

                sections.append(section)

        return sections


class PlainTextParser(BaseParser):
    """Parser for plain text documents."""

    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in {".txt", ".rst"}

    def parse(self, file_path: Path) -> ParsedDocument:
        content = file_path.read_text(encoding="utf-8")

        # Try to extract title from first line
        lines = content.split("\n")
        title = lines[0].strip() if lines else None

        # Create a single section with all content
        sections = [
            {
                "level": 1,
                "title": "Content",
                "content": content,
            }
        ]

        return ParsedDocument(
            file_path=str(file_path),
            content_type="text",
            title=title,
            sections=sections,
            raw_content=content,
        )


class StandardsParser:
    """
    Main parser that delegates to appropriate format-specific parsers.

    Example:
        parser = StandardsParser()
        doc = parser.parse(Path("coding-standards.md"))
        print(doc.title)
        for section in doc.sections:
            print(f"  - {section['title']}")
    """

    def __init__(self):
        self.parsers: list[BaseParser] = [
            MarkdownParser(),
            YAMLParser(),
            JSONParser(),
            PlainTextParser(),
        ]

    def parse(self, file_path: Path) -> ParsedDocument:
        """Parse a document using the appropriate parser."""
        for parser in self.parsers:
            if parser.can_parse(file_path):
                logger.info(f"Parsing {file_path} with {parser.__class__.__name__}")
                return parser.parse(file_path)

        raise ValueError(f"No parser available for: {file_path}")

    def supported_extensions(self) -> set[str]:
        """Return all supported file extensions."""
        return {".md", ".markdown", ".yaml", ".yml", ".json", ".txt", ".rst"}
