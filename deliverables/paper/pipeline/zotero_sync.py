"""Read-only Zotero collection sync for the SAF paper package."""

from __future__ import annotations

import json
from pathlib import Path
import re
from urllib.error import URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[3]
COLLECTION_FILE = ROOT / "deliverables" / "paper" / "zotero" / "collection.json"
KEYS_FILE = ROOT / "deliverables" / "paper" / "zotero" / "citation_keys.json"
KEY_RE = re.compile(r"@\w+\s*\{\s*([^,\s]+)")
_ATTACHMENT_FIELD_RE = re.compile(r"(?is)(?:^|,|\n)\s*file\s*=\s*\{.*?\}\s*,?")


class ZoteroSyncError(RuntimeError):
    """Raised when the required local collection cannot be verified."""


def _json(url: str) -> dict | list:
    try:
        with urlopen(Request(url, headers={"Accept": "application/json"}), timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, ValueError) as error:
        raise ZoteroSyncError(f"Zotero API unavailable: {url}: {error}") from error


def _text(url: str) -> str:
    try:
        with urlopen(Request(url, headers={"Accept": "application/x-bibtex"}), timeout=10) as response:
            return response.read().decode("utf-8")
    except (OSError, URLError, UnicodeError) as error:
        raise ZoteroSyncError(f"Zotero BibTeX export unavailable: {url}: {error}") from error


def _portable_bibtex(text: str, allowed: set[str]) -> str:
    """Keep only manuscript keys and remove Zotero-local attachment paths."""
    entries = re.split(r"(?m)(?=^@)", text.strip())
    kept = []
    for entry in entries:
        if not entry.strip():
            continue
        match = KEY_RE.search(entry)
        if match and match.group(1) in allowed:
            kept.append(_ATTACHMENT_FIELD_RE.sub("", entry).strip())
    return "\n\n".join(kept) + ("\n" if kept else "")


def load_contract() -> tuple[dict, dict]:
    try:
        collection = json.loads(COLLECTION_FILE.read_text(encoding="utf-8"))
        keys = json.loads(KEYS_FILE.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ZoteroSyncError(f"Zotero contract is unreadable: {error}") from error
    if collection.get("collection_key") != keys.get("collection_key"):
        raise ZoteroSyncError("Zotero collection/key contracts disagree")
    return collection, keys


def sync_collection(output: str | Path, *, strict: bool = True) -> dict[str, object]:
    """Verify the collection and write a temporary BibTeX export."""
    collection, key_contract = load_contract()
    base = str(collection.get("api_base", "http://127.0.0.1:23119")).rstrip("/")
    key = collection["collection_key"]
    metadata = _json(f"{base}/api/users/0/collections/{key}")
    if not isinstance(metadata, dict):
        raise ZoteroSyncError("Zotero collection metadata is not an object")
    actual_name = metadata.get("data", {}).get("name")
    if actual_name != collection["collection_name"]:
        raise ZoteroSyncError(
            f"Zotero collection name mismatch: expected {collection['collection_name']!r}, got {actual_name!r}"
        )
    bib = _text(f"{base}/api/users/0/collections/{key}/items?format=bibtex&limit=100")
    required = set(key_contract.get("citation_keys", ()))
    source_keys = key_contract.get("zotero_keys", {})
    found_source = set(KEY_RE.findall(bib))
    missing_source = sorted(set(source_keys.values()) - found_source)
    if missing_source and strict:
        raise ZoteroSyncError(f"Zotero collection export is missing source keys: {', '.join(missing_source)}")
    for desired, source in source_keys.items():
        bib = re.sub(
            rf"(@\w+\s*\{{)\s*{re.escape(source)}(\s*,)",
            rf"\g<1>{desired}\g<2>",
            bib,
            count=1,
        )
    found = set(KEY_RE.findall(bib))
    missing = sorted(required - found)
    if missing and strict:
        raise ZoteroSyncError(f"Zotero collection export is missing citation keys: {', '.join(missing)}")
    bib = _portable_bibtex(bib, required)
    found = set(KEY_RE.findall(bib))
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(bib, encoding="utf-8")
    return {
        "collection_key": key,
        "collection_name": actual_name,
        "collection_version": metadata.get("version"),
        "entry_count": len(found),
        "required_count": len(required),
        "missing": missing,
        "output": str(target),
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Verify and export the SAF Zotero collection")
    parser.add_argument("--out", default=str(ROOT / "deliverables" / "paper" / "build" / "references.bib"))
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(sync_collection(args.out, strict=args.strict), ensure_ascii=False, indent=2))
    except ZoteroSyncError as error:
        print(f"ZOTERO_ERROR: {error}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
