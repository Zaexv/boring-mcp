"""Seed utility — bootstrap behaviors from a YAML file.

Usage:
    python -m boring_mcp.seed data/behaviors.yaml

YAML format:
    tone:
      - "Always respond with empathy"
      - "Use bullet points for lists longer than 3 items"
    boundaries:
      - "Never share personal data"
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

from boring_mcp.logging import get_logger
from boring_mcp.repositories.chroma import ChromaRepository
from boring_mcp.services.behavior_service import BehaviorService

_log = get_logger("seed")


def _load_yaml(yaml_path: str) -> dict[str, list[str]] | None:
    """Load and validate a YAML behaviors file.

    Returns:
        Parsed dict if valid, None if the file is missing or malformed.
    """
    path = Path(yaml_path)
    result: dict[str, list[str]] | None = None
    if not path.exists():
        _log.error("File not found: %s", yaml_path)
    else:
        with path.open() as f:
            data = yaml.safe_load(f)
        if isinstance(data, dict):
            result = data
        else:
            _log.error("YAML root must be a mapping of collection → sentences")
    return result


def seed_from_yaml(yaml_path: str, chroma_path: str = "./data/chroma") -> int:
    """Load behaviors from a YAML file into ChromaDB.

    Args:
        yaml_path: Path to the YAML file.
        chroma_path: Path to the ChromaDB storage directory.

    Returns:
        Number of behaviors stored.
    """
    data = _load_yaml(yaml_path)
    count = 0

    if data is not None:
        repository = ChromaRepository(persist_path=chroma_path)
        service = BehaviorService(repository=repository)

        for collection, sentences in data.items():
            if not isinstance(sentences, list):
                _log.warning("Skipping '%s' — value must be a list", collection)
                continue
            for sentence in sentences:
                if isinstance(sentence, str) and sentence.strip():
                    service.store(sentence=sentence.strip(), collection=str(collection))
                    count += 1
                    _log.info("Stored in '%s': %s", collection, sentence.strip()[:60])

        _log.info("Seeded %d behaviors across %d collections", count, len(data))
    return count


def main() -> None:
    """CLI entry point for the seed utility."""
    if len(sys.argv) < 2:
        print("Usage: python -m boring_mcp.seed <path-to-yaml>")  # noqa: T201
        sys.exit(1)
    yaml_path = sys.argv[1]
    chroma_path = sys.argv[2] if len(sys.argv) > 2 else "./data/chroma"
    count = seed_from_yaml(yaml_path, chroma_path)
    print(f"✅ Seeded {count} behaviors")  # noqa: T201


if __name__ == "__main__":
    main()
