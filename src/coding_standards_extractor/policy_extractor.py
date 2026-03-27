"""
Policy Extractor Module

Extracts coding policies and standards from various document formats.
"""

import re
import json
import logging
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class CodingPolicy:
    """Represents a single coding policy or standard."""

    id: str
    title: str
    description: str
    category: str
    severity: str  # "required", "recommended", "optional"
    source_file: str
    source_line: Optional[int] = None
    examples: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    extracted_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """Convert policy to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert policy to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class ExtractionResult:
    """Result of policy extraction from a document."""

    source_file: str
    policies: list[CodingPolicy]
    metadata: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    extracted_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def policy_count(self) -> int:
        return len(self.policies)

    def to_dict(self) -> dict:
        return {
            "source_file": self.source_file,
            "policies": [p.to_dict() for p in self.policies],
            "metadata": self.metadata,
            "errors": self.errors,
            "extracted_at": self.extracted_at,
            "policy_count": self.policy_count,
        }


class PolicyExtractor:
    """
    Extracts coding policies from documents.

    Supports various document formats and uses pattern matching
    to identify coding standards, rules, and policies.
    """

    # Patterns to identify policy sections
    POLICY_PATTERNS = [
        # Markdown headers with policy keywords
        r"^#{1,6}\s*(policy|rule|standard|requirement|guideline|convention)[\s:]*(.+)$",
        # Numbered rules
        r"^\d+\.\s*(must|should|shall|required|always|never)\s+(.+)$",
        # Bullet points with policy keywords
        r"^[-*]\s*(must|should|shall|required|always|never)\s+(.+)$",
        # DO/DON'T patterns
        r"^[-*]?\s*(do|don't|do not|avoid|prefer)\s*:?\s*(.+)$",
    ]

    SEVERITY_KEYWORDS = {
        "required": ["must", "shall", "required", "always", "never", "mandatory"],
        "recommended": ["should", "recommend", "prefer", "consider"],
        "optional": ["may", "optional", "can", "could"],
    }

    CATEGORY_KEYWORDS = {
        "naming": ["naming", "name", "identifier", "variable", "function", "class"],
        "formatting": ["format", "indent", "spacing", "whitespace", "style"],
        "documentation": ["document", "comment", "docstring", "readme"],
        "testing": ["test", "coverage", "assertion", "mock"],
        "security": ["security", "auth", "credential", "password", "secret"],
        "performance": ["performance", "optimize", "cache", "memory"],
        "error_handling": ["error", "exception", "try", "catch", "handle"],
        "architecture": ["architecture", "pattern", "structure", "module", "import"],
    }

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = Path(output_dir) if output_dir else None
        self._compiled_patterns = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in self.POLICY_PATTERNS]

    def extract_from_file(self, file_path: Path) -> ExtractionResult:
        """Extract policies from a single file."""
        logger.info(f"Extracting policies from: {file_path}")

        try:
            content = self._read_file(file_path)
            policies = self._extract_policies(content, file_path)

            result = ExtractionResult(
                source_file=str(file_path),
                policies=policies,
                metadata={"file_size": file_path.stat().st_size},
            )

            if self.output_dir:
                self._save_result(result)

            return result

        except Exception as e:
            logger.error(f"Failed to extract from {file_path}: {e}")
            return ExtractionResult(
                source_file=str(file_path),
                policies=[],
                errors=[str(e)],
            )

    def _read_file(self, file_path: Path) -> str:
        """Read content from a file."""
        suffix = file_path.suffix.lower()

        if suffix in {".md", ".txt", ".rst"}:
            return file_path.read_text(encoding="utf-8")
        elif suffix in {".yaml", ".yml"}:
            return file_path.read_text(encoding="utf-8")
        elif suffix == ".json":
            return file_path.read_text(encoding="utf-8")
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

    def _extract_policies(self, content: str, source_file: Path) -> list[CodingPolicy]:
        """Extract policies from document content."""
        policies = []
        lines = content.split("\n")

        for line_num, line in enumerate(lines, start=1):
            for pattern in self._compiled_patterns:
                match = pattern.search(line)
                if match:
                    policy = self._create_policy(match, line, line_num, source_file)
                    if policy:
                        policies.append(policy)

        # Also extract structured policies from sections
        section_policies = self._extract_from_sections(content, source_file)
        policies.extend(section_policies)

        # Deduplicate by title
        seen_titles = set()
        unique_policies = []
        for policy in policies:
            if policy.title.lower() not in seen_titles:
                seen_titles.add(policy.title.lower())
                unique_policies.append(policy)

        logger.info(f"Extracted {len(unique_policies)} policies from {source_file}")
        return unique_policies

    def _create_policy(
        self, match: re.Match, line: str, line_num: int, source_file: Path
    ) -> Optional[CodingPolicy]:
        """Create a CodingPolicy from a regex match."""
        groups = match.groups()
        if len(groups) < 2:
            return None

        keyword, description = groups[0], groups[1]
        description = description.strip().rstrip(".")

        if len(description) < 10:
            return None

        policy_id = f"{source_file.stem}_{line_num}"
        title = self._generate_title(description)
        severity = self._determine_severity(line)
        category = self._determine_category(line)

        return CodingPolicy(
            id=policy_id,
            title=title,
            description=description,
            category=category,
            severity=severity,
            source_file=str(source_file),
            source_line=line_num,
            tags=self._extract_tags(line),
        )

    def _extract_from_sections(self, content: str, source_file: Path) -> list[CodingPolicy]:
        """Extract policies from document sections."""
        policies = []

        # Find markdown sections
        section_pattern = r"^(#{1,3})\s+(.+)$"
        sections = re.finditer(section_pattern, content, re.MULTILINE)

        for section in sections:
            header_level = len(section.group(1))
            header_text = section.group(2).strip()

            # Check if this is a policy-related section
            policy_keywords = ["standard", "policy", "rule", "guideline", "requirement"]
            if any(kw in header_text.lower() for kw in policy_keywords):
                # Extract the section content
                start = section.end()
                next_section = re.search(
                    rf"^#{{{1},{header_level}}}\s+", content[start:], re.MULTILINE
                )
                end = start + next_section.start() if next_section else len(content)
                section_content = content[start:end].strip()

                if section_content:
                    policy = CodingPolicy(
                        id=f"{source_file.stem}_section_{section.start()}",
                        title=header_text,
                        description=section_content[:500],
                        category=self._determine_category(header_text + " " + section_content),
                        severity="recommended",
                        source_file=str(source_file),
                    )
                    policies.append(policy)

        return policies

    def _generate_title(self, description: str) -> str:
        """Generate a title from description."""
        words = description.split()[:8]
        title = " ".join(words)
        if len(description.split()) > 8:
            title += "..."
        return title.title()

    def _determine_severity(self, text: str) -> str:
        """Determine the severity level from text."""
        text_lower = text.lower()
        for severity, keywords in self.SEVERITY_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                return severity
        return "recommended"

    def _determine_category(self, text: str) -> str:
        """Determine the category from text."""
        text_lower = text.lower()
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                return category
        return "general"

    def _extract_tags(self, text: str) -> list[str]:
        """Extract tags from text."""
        tags = []
        text_lower = text.lower()

        # Language tags
        languages = ["python", "javascript", "typescript", "java", "go", "rust", "c++"]
        for lang in languages:
            if lang in text_lower:
                tags.append(lang)

        # Topic tags
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                tags.append(category)

        return tags

    def _save_result(self, result: ExtractionResult) -> None:
        """Save extraction result to output directory."""
        if not self.output_dir:
            return

        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_file = self.output_dir / f"{Path(result.source_file).stem}_policies.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2)

        logger.info(f"Saved extraction result to: {output_file}")
