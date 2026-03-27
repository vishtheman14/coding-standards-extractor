# Coding Standards Extractor

A Python tool for watching documents and automatically extracting coding policies and standards from various document formats.

## Features

- **Document Watcher**: Monitors directories for document changes in real-time
- **Policy Extractor**: Automatically extracts coding standards from documents
- **Multi-format Support**: Parses Markdown, YAML, JSON, and plain text files
- **Severity Detection**: Categorizes policies by severity (required, recommended, optional)
- **Category Classification**: Automatically categorizes policies (naming, formatting, security, etc.)
- **CLI Interface**: Easy-to-use command-line interface

## Installation

```bash
# Clone the repository
git clone https://github.com/vishtheman14/coding-standards-extractor.git
cd coding-standards-extractor

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

## Usage

### Extract Policies from Documents

```bash
# Extract from a single file
coding-standards-extractor extract path/to/standards.md

# Extract from a directory
coding-standards-extractor extract path/to/docs/ -o output/

# Verbose output
coding-standards-extractor extract path/to/standards.md -v
```

### Watch for Document Changes

```bash
# Watch a directory for changes
coding-standards-extractor watch path/to/docs/

# Watch and process existing files on startup
coding-standards-extractor watch path/to/docs/ --scan-existing

# Specify output directory
coding-standards-extractor watch path/to/docs/ -o output/
```

### Programmatic Usage

```python
from coding_standards_extractor import DocumentWatcher, PolicyExtractor

# Extract policies from a file
extractor = PolicyExtractor(output_dir="output/")
result = extractor.extract_from_file("standards.md")

for policy in result.policies:
    print(f"[{policy.severity}] {policy.title}")
    print(f"  Category: {policy.category}")
    print(f"  Description: {policy.description}")

# Watch a directory for changes
def on_change(file_path):
    result = extractor.extract_from_file(file_path)
    print(f"Extracted {result.policy_count} policies")

with DocumentWatcher("docs/", on_change=on_change) as watcher:
    watcher.scan_existing()  # Process existing files
    # Watcher runs until interrupted
```

## Supported Document Formats

| Format | Extensions | Notes |
|--------|------------|-------|
| Markdown | `.md`, `.markdown` | Supports YAML frontmatter |
| YAML | `.yaml`, `.yml` | Structured policy definitions |
| JSON | `.json` | Structured policy definitions |
| Plain Text | `.txt`, `.rst` | Basic text extraction |

## Policy Detection Patterns

The extractor identifies policies using various patterns:

- **Markdown headers**: `## Policy: Use consistent naming`
- **Numbered rules**: `1. Must validate all input`
- **Bullet points**: `- Should use descriptive names`
- **DO/DON'T patterns**: `- Do: Use snake_case for variables`

### Severity Levels

| Level | Keywords |
|-------|----------|
| Required | must, shall, required, always, never, mandatory |
| Recommended | should, recommend, prefer, consider |
| Optional | may, optional, can, could |

### Categories

- `naming`: Variable, function, and class naming conventions
- `formatting`: Code formatting and style rules
- `documentation`: Comments and documentation standards
- `testing`: Testing requirements and practices
- `security`: Security-related policies
- `performance`: Performance optimization guidelines
- `error_handling`: Exception handling standards
- `architecture`: Architectural patterns and structure

## Configuration

Create a `config/config.yaml` file to customize behavior:

```yaml
watch:
  extensions:
    - .md
    - .yaml
    - .json
  recursive: true
  debounce_delay: 1.0

extraction:
  output_format: json
  include_examples: true

logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

## Development

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run tests with coverage
pytest --cov=src/coding_standards_extractor

# Format code
black src/ tests/

# Lint code
ruff src/ tests/
```

## Project Structure

```
coding-standards-extractor/
├── src/
│   └── coding_standards_extractor/
│       ├── __init__.py
│       ├── cli.py              # Command-line interface
│       ├── document_watcher.py # File system watcher
│       ├── policy_extractor.py # Policy extraction logic
│       └── standards_parser.py # Document format parsers
├── tests/
│   ├── test_document_watcher.py
│   ├── test_policy_extractor.py
│   └── test_standards_parser.py
├── config/
│   └── config.yaml
├── examples/
│   └── sample_standards.md
├── pyproject.toml
├── requirements.txt
└── README.md
```

## License

MIT License
