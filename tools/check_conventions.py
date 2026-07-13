#!/usr/bin/env python3
"""动作规范校验器（git 历史 / 分支）—— 规范的唯一可执行权威（spec 之家）。纯 stdlib。

由 .github/workflows/conventions.yml（CI）与 hooks/（本地可选）共用。校验：
  - commit 主题匹配 <type>(<scope>): <主题>，type ∈ TYPES；
  - 当前分支名匹配 <type>/<slug>，或属豁免（main / master / claude/* harness 分支）。
规范**自其引入**（charter/conventions.md 首次加入的提交）向后强制；之前的 bootstrap 提交祖父豁免，
不改写历史。理据 / 生命周期散文见 charter/conventions.md，冻结见 decisions D-013。

用法：
  python tools/check_conventions.py [--branch <name>]     # 校验分支名 + 历史提交（CI / pre-push）
  python tools/check_conventions.py --message-file <path> # 校验单条待写消息（commit-msg hook）
"""
import re
import subprocess
import sys

TYPES = ("feat", "fix", "refactor", "test", "docs", "ci", "gov", "data", "exp", "chore", "revert")
SUBJECT_RE = re.compile(r"^(" + "|".join(TYPES) + r")(\([a-z0-9._-]+\))?: .+")
BRANCH_RE = re.compile(r"^(" + "|".join(TYPES) + r")/[a-z0-9._-]+$")
BRANCH_EXEMPT = re.compile(r"^(main|master|HEAD|claude/.+)$")   # 默认分支 + harness agent 分支


def _git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True).stdout.strip()


def _commits_to_check():
    """规范自 charter/conventions.md 引入的提交起强制；祖父豁免更早的 bootstrap 提交。"""
    added = _git("log", "--diff-filter=A", "--reverse", "--format=%H", "--", "charter/conventions.md")
    start = added.splitlines()[0] if added else None
    if not start:
        return []                                          # 规范尚未引入：不强制
    has_parent = len(_git("rev-list", "--parents", "-n", "1", start).split()) > 1
    rng = f"{start}^..HEAD" if has_parent else "HEAD"
    return [s for s in _git("rev-list", rng).splitlines() if s]


def check(branch=None):
    errs = []
    branch = branch or _git("rev-parse", "--abbrev-ref", "HEAD")
    if branch and not (BRANCH_RE.match(branch) or BRANCH_EXEMPT.match(branch)):
        errs.append(f"分支名 '{branch}' 不合规：应为 <type>/<slug>（type∈{{{','.join(TYPES)}}}；main/claude-* 豁免）")
    for sha in _commits_to_check():
        subj = _git("show", "-s", "--format=%s", sha)
        if not SUBJECT_RE.match(subj):
            errs.append(f"提交 {sha[:9]} 主题 '{subj[:56]}' 不合规：应为 <type>(<scope>): …")
    return errs


def check_message(path):
    try:
        with open(path, encoding="utf-8") as f:
            subj = next((ln for ln in f.read().splitlines() if ln.strip() and not ln.startswith("#")), "")
    except OSError as e:
        return [f"读不到消息文件 {path}: {e}"]
    return [] if SUBJECT_RE.match(subj) else [f"消息主题 '{subj[:56]}' 不合规：应为 <type>(<scope>): …"]


def main():
    a = sys.argv[1:]
    if "--message-file" in a:
        errs = check_message(a[a.index("--message-file") + 1])
    else:
        branch = a[a.index("--branch") + 1] if "--branch" in a else None
        errs = check(branch)
    if errs:
        sys.stderr.write("动作规范校验未过（见 charter/conventions.md）：\n")
        for e in errs:
            sys.stderr.write("  ✗ " + e + "\n")
        sys.exit(1)
    print("动作规范校验通过 ✓")


if __name__ == "__main__":
    main()
