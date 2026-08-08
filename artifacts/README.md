# Artifact lifecycle

`artifacts/runs/` is the retained machine-evidence area. Result JSON, audit
samples, and figure QA reports may be referenced by `governance/`, the gate, or
the paper and are never removed by cache cleanup.

`artifacts/cache/` is disposable working state: checkpoints, candidate images,
logs, and temporary arrays. It is ignored by Git and may be cleaned with:

```text
python tools/prune_artifacts.py --dry-run
python tools/prune_artifacts.py --apply
```

Cleanup is TTL-based (seven days by default), dry-run by default, and refuses
to target anything outside `artifacts/cache/`. Failed runs can keep their cache
for diagnosis with `--keep-cache`; promote any evidence needed for a result
before cleanup. Successful figure QA runs use `--ttl-days 0` for their own
cache scope, while strict QA failures leave the cache for the diagnostic TTL.
