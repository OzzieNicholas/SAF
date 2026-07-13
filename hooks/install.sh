#!/bin/sh
# 安装本地 git hooks（可选，快失败）。CI（conventions.yml）才是权威门；hook 只为本地早失败。
set -e
root="$(git rev-parse --show-toplevel)"
for h in commit-msg pre-push; do
    chmod +x "$root/hooks/$h"
    ln -sf "../../hooks/$h" "$root/.git/hooks/$h"
    echo "installed .git/hooks/$h -> hooks/$h"
done
