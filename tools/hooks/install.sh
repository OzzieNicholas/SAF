#!/bin/sh
# 安装本地 git hooks（可选，快失败）。CI（conventions.yml）才是权威门；hook 只为本地早失败。
set -e
root="$(git rev-parse --show-toplevel)"
mkdir -p "$root/.git/hooks"
for h in commit-msg pre-push; do
    chmod +x "$root/tools/hooks/$h"
    ln -sf "../../tools/hooks/$h" "$root/.git/hooks/$h"
    echo "installed .git/hooks/$h -> tools/hooks/$h"
done
