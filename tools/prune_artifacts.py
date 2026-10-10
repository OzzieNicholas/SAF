#!/usr/bin/env python3
"""清理可丢弃的缓存文件（artifacts/cache），绝不触碰证据目录 artifacts/runs。

默认只列出（dry-run）；加 ``--apply`` 才删除超过 TTL 的缓存文件。
"""

from __future__ import annotations

import argparse

from support_accessibility.runtime.run_records import CACHE_ROOT, ROOT, cache_scope, stale_cache_files


def main() -> int:
    parser = argparse.ArgumentParser(description="Prune disposable SAF artifact cache")
    parser.add_argument("--kind", help="only prune one cache kind")
    parser.add_argument("--ttl-days", type=float, default=7.0)
    parser.add_argument("--apply", action="store_true", help="actually delete candidates")
    args = parser.parse_args()
    if args.ttl_days < 0:
        parser.error("--ttl-days must be non-negative")
    try:
        cache_scope(args.kind)
    except ValueError as exc:
        parser.error(str(exc))
    paths = stale_cache_files(args.ttl_days, args.kind)
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
