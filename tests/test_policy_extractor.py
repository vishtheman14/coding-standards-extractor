"""Tests for the PolicyExtractor module."""

import tempfile
from pathlib import Path

import pytest

from coding_standards_extractor.policy_extractor import PolicyExtractor, CodingPolicy


class TestCodingPolicy:
    """Tests for CodingPolicy dataclass."""

    def test_policy_creation(self):
        """Test creating a policy instance."""
        policy = CodingPolicy(
            id="test_1",
            title="Test Policy",
            description="This is a test policy",
            category="testing",
            severity="required",
            source_file="test.md",
        )

        assert policy.id == "test_1"
        assert policy.title == "Test Policy"
        assert policy.severity == "required"

    def test_policy_to_dict(self):
        """Test converting policy to dictionary."""
        policy = CodingPolicy(
            id="test_1",
            title="Test Policy",
            description="This is a test policy",
            category="testing",
            severity="required",
            source_file="test.md",
        )

        result = policy.to_dict()
        assert isinstance(result, dict)
        assert result["id"] == "test_1"
        assert result["title"] == "Test Policy"

    def test_policy_to_json(self):
        """Test converting policy to JSON."""
        policy = CodingPolicy(
            id="test_1",
            title="Test Policy",
            description="This is a test policy",
            category="testing",
            severity="required",
            source_file="test.md",
        )

        json_str = policy.to_json()
        assert isinstance(json_str, str)
        assert '"id": "test_1"' in json_str


class TestPolicyExtractor:
    """Tests for PolicyExtractor class."""

    @pytest.fixture
    def extractor(self):
        """Create a PolicyExtractor instance."""
        return PolicyExtractor()

    @pytest.fixture
    def sample_markdown(self, tmp_path):
        """Create a sample markdown file."""
        content = """# Coding Standards

## Naming Conventions

- You must use snake_case for Python variables
- You should use descriptive names for functions
- Never use single letter variable names except in loops

## Error Handling

1. Must handle all exceptions properly
2. Should log errors with appropriate context
"""
        file_path = tmp_path / "standards.md"
        file_path.write_text(content)
        return file_path

    def test_extract_from_markdown(self, extractor, sample_markdown):
        """Test extracting policies from markdown file."""
        result = extractor.extract_from_file(sample_markdown)

        assert result.source_file == str(sample_markdown)
        assert len(result.policies) > 0
        assert result.policy_count > 0
        assert not result.errors

    def test_severity_detection(self, extractor, tmp_path):
        """Test that severity is correctly detected."""
        content = """
- Must always validate input
- Should consider edge cases
- May use caching for performance
"""
        file_path = tmp_path / "severity.md"
        file_path.write_text(content)

        result = extractor.extract_from_file(file_path)

        severities = {p.severity for p in result.policies}
        assert "required" in severities or "recommended" in severities

    def test_category_detection(self, extractor, tmp_path):
        """Test that category is correctly detected."""
        content = """
- Must use proper naming conventions for variables
- Should format code consistently
- Must handle security vulnerabilities
"""
        file_path = tmp_path / "categories.md"
        file_path.write_text(content)

        result = extractor.extract_from_file(file_path)

        categories = {p.category for p in result.policies}
        assert len(categories) > 0

    def test_output_directory(self, tmp_path):
        """Test saving results to output directory."""
        output_dir = tmp_path / "output"
        extractor = PolicyExtractor(output_dir=output_dir)

        content = "- Must follow coding standards"
        file_path = tmp_path / "test.md"
        file_path.write_text(content)

        extractor.extract_from_file(file_path)

        assert output_dir.exists()
        output_files = list(output_dir.glob("*.json"))
        assert len(output_files) == 1

    def test_unsupported_file_type(self, extractor, tmp_path):
        """Test handling of unsupported file types."""
        file_path = tmp_path / "test.xyz"
        file_path.write_text("Some content")

        result = extractor.extract_from_file(file_path)

        assert len(result.errors) > 0
        assert result.policy_count == 0

    def test_empty_file(self, extractor, tmp_path):
        """Test handling of empty files."""
        file_path = tmp_path / "empty.md"
        file_path.write_text("")

        result = extractor.extract_from_file(file_path)

        assert result.policy_count == 0
        assert not result.errors
