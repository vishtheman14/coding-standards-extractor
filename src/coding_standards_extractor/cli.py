"""
Command Line Interface for Coding Standards Extractor.
"""

import argparse
import logging
import sys
import time
from pathlib import Path

from .document_watcher import DocumentWatcher
from .policy_extractor import PolicyExtractor


def setup_logging(verbose: bool = False) -> None:
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )


def extract_command(args: argparse.Namespace) -> int:
    """Run the extract command."""
    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else None

    if not input_path.exists():
        print(f"Error: Input path does not exist: {input_path}", file=sys.stderr)
        return 1

    extractor = PolicyExtractor(output_dir=output_path)

    if input_path.is_file():
        result = extractor.extract_from_file(input_path)
        print(f"Extracted {result.policy_count} policies from {input_path}")
        if args.verbose:
            for policy in result.policies:
                print(f"  - [{policy.severity}] {policy.title}")
    else:
        # Process all files in directory
        extensions = {".md", ".txt", ".yaml", ".yml", ".json"}
        total_policies = 0
        for ext in extensions:
            for file_path in input_path.rglob(f"*{ext}"):
                result = extractor.extract_from_file(file_path)
                total_policies += result.policy_count
                if args.verbose:
                    print(f"  {file_path}: {result.policy_count} policies")
        print(f"Extracted {total_policies} policies from {input_path}")

    return 0


def watch_command(args: argparse.Namespace) -> int:
    """Run the watch command."""
    watch_path = Path(args.path)
    output_path = Path(args.output) if args.output else Path("output")

    if not watch_path.exists():
        print(f"Error: Watch path does not exist: {watch_path}", file=sys.stderr)
        return 1

    extractor = PolicyExtractor(output_dir=output_path)

    def on_document_change(file_path: Path) -> None:
        """Handle document changes."""
        print(f"Processing: {file_path}")
        result = extractor.extract_from_file(file_path)
        print(f"  Extracted {result.policy_count} policies")

    print(f"Watching for changes in: {watch_path}")
    print("Press Ctrl+C to stop...")

    try:
        with DocumentWatcher(watch_path, on_change=on_document_change) as watcher:
            # Process existing files if requested
            if args.scan_existing:
                print("Scanning existing documents...")
                for doc_path in watcher.scan_existing():
                    on_document_change(doc_path)

            # Keep running until interrupted
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping watcher...")

    return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="coding-standards-extractor",
        description="Extract coding policies and standards from documents",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Extract command
    extract_parser = subparsers.add_parser("extract", help="Extract policies from documents")
    extract_parser.add_argument("input", help="Input file or directory")
    extract_parser.add_argument("-o", "--output", help="Output directory for extracted policies")

    # Watch command
    watch_parser = subparsers.add_parser("watch", help="Watch directory for document changes")
    watch_parser.add_argument("path", help="Directory to watch")
    watch_parser.add_argument("-o", "--output", help="Output directory for extracted policies")
    watch_parser.add_argument(
        "--scan-existing", action="store_true", help="Process existing documents on startup"
    )

    args = parser.parse_args()

    setup_logging(args.verbose)

    if args.command == "extract":
        return extract_command(args)
    elif args.command == "watch":
        return watch_command(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
