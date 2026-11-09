"""Generate README.md from projects.toml.

Usage: python scripts/generate.py [--config PATH] [--output PATH]
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path

BASE_URL = "https://github.com/cet-t/"
CATEGORIES = (("projects", "Projects"), ("archive", "Archive"))
ALLOWED_FIELDS = {"name", "description"}
NAME_RE = re.compile(r"^[A-Za-z0-9._-]{1,100}$")

ROOT = Path(__file__).resolve().parent.parent


class ConfigError(Exception):
    """Raised when projects.toml is invalid."""


def load_config(path: Path) -> dict:
    try:
        with path.open("rb") as f:
            return tomllib.load(f)
    except FileNotFoundError:
        raise ConfigError(f"{path}: file not found") from None
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"{path}: invalid TOML: {e}") from None


def validate(config: dict) -> dict[str, list[dict[str, str]]]:
    """Validate raw config and return {category: [{"name", "description"?}, ...]}."""
    known = {key for key, _ in CATEGORIES}
    unknown = sorted(set(config) - known)
    if unknown:
        raise ConfigError(f"unknown top-level key(s): {', '.join(unknown)}")

    result: dict[str, list[dict[str, str]]] = {}
    seen: dict[str, str] = {}
    for key, _ in CATEGORIES:
        entries = config.get(key, [])
        if not isinstance(entries, list):
            raise ConfigError(f"'{key}' must be an array of tables ([[{key}]])")
        repos = []
        for i, entry in enumerate(entries):
            where = f"{key}[{i}]"
            if not isinstance(entry, dict):
                raise ConfigError(f"{where}: must be a table")
            extra = sorted(set(entry) - ALLOWED_FIELDS)
            if extra:
                raise ConfigError(f"{where}: unknown field(s): {', '.join(extra)}")

            name = entry.get("name")
            if not isinstance(name, str):
                raise ConfigError(f"{where}: 'name' is required and must be a string")
            if not NAME_RE.fullmatch(name) or name in {".", ".."}:
                raise ConfigError(f"{where}: invalid repository name: {name!r}")
            folded = name.lower()  # GitHub repository names are case-insensitive
            if folded in seen:
                raise ConfigError(f"{where}: duplicate repository {name!r} (also in {seen[folded]})")
            seen[folded] = where

            repo = {"name": name}
            if "description" in entry:
                desc = entry["description"]
                if not isinstance(desc, str):
                    raise ConfigError(f"{where}: 'description' must be a string")
                if desc.strip():
                    repo["description"] = desc
            repos.append(repo)
        result[key] = repos
    return result


def escape_cell(text: str) -> str:
    """Escape text so it stays inside a single Markdown table cell."""
    text = " ".join(text.split())  # collapse newlines/tabs that would break the row
    return text.replace("\\", "\\\\").replace("|", "\\|")


def render_table(repos: list[dict[str, str]]) -> str:
    with_desc = any("description" in r for r in repos)
    header = ["Repository", "Description"] if with_desc else ["Repository"]
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    for r in repos:
        cells = [f"[{r['name']}]({BASE_URL}{r['name']})"]
        if with_desc:
            cells.append(escape_cell(r.get("description", "")))
        lines.append("|" + "|".join(f" {c} " if c else " " for c in cells) + "|")
    return "\n".join(lines)


def render(data: dict[str, list[dict[str, str]]]) -> str:
    sections = [f"# {title}\n\n{render_table(data[key])}" for key, title in CATEGORIES]
    return "\n\n".join(sections) + "\n"


def write_if_changed(path: Path, content: str) -> bool:
    """Write content to path only if it differs. Returns True if written."""
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8", newline="\n")
    tmp.replace(path)
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, default=ROOT / "projects.toml")
    parser.add_argument("--output", type=Path, default=ROOT / "README.md")
    args = parser.parse_args(argv)

    try:
        content = render(validate(load_config(args.config)))
    except ConfigError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if write_if_changed(args.output, content):
        print(f"updated {args.output}")
    else:
        print(f"{args.output} is up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
