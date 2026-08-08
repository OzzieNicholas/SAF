#!/usr/bin/env python3
"""Prune disposable SAF cache files without touching retained evidence.

Dry-run is the default.  Use ``--apply`` to delete cache entries older than
the selected TTL.  Evidence under ``artifacts/runs`` is never a target.
"""

from __future__ import annotations

import argparse
import os
import time
from pathlib import Path

from artifacts import CACHE_ROOT, ROOT, _cache_scope


def candidates(ttl_days: float, kind: str | None = None) -> list[Path]:
    root = _cache_scope(kind)
    if not root.exists():
        return []
    cutoff = time.time() - ttl_days * 86400.0
    return sorted(
        path for path in root.rglob("*")
        if path.is_file()
        and path.resolve() != CACHE_ROOT.resolve()
        and CACHE_ROOT.resolve() in path.resolve().parents
        and path.stat().st_mtime < cutoff
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Prune disposable SAF artifact cache")
    parser.add_argument("--kind", help="only prune one cache kind")
    parser.add_argument("--ttl-days", type=float, default=7.0)
    parser.add_argument("--apply", action="store_true", help="actually delete candidates")
    parser.add_argument("--dry-run", action="store_true", help="list candidates without deleting (default)")
    parser.add_argument("--keep-cache", action="store_true", help="do not delete anything")
    args = parser.parse_args()
    if args.ttl_days < 0:
        parser.error("--ttl-days must be non-negative")
    try:
        _cache_scope(args.kind)
    except ValueError as exc:
        parser.error(str(exc))
    if args.keep_cache:
        print("cache pruning disabled (--keep-cache)")
        return 0
    paths = candidates(args.ttl_days, args.kind)
    for path in paths:
        print(f"{'DELETE' if args.apply else 'WOULD_DELETE'} {path.relative_to(ROOT)}")
        if args.apply:
            path.unlink()
    if args.apply:
        for directory in sorted((p for p in CACHE_ROOT.rglob("*") if p.is_dir()), reverse=True):
            try:
                directory.rmdir()
            except OSError:
                pass
    print(f"{'deleted' if args.apply else 'candidates'}={len(paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
