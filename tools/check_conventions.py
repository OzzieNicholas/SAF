#!/usr/bin/env python3
"""动作规范校验器（git 历史 / 分支）—— 规范的唯一可执行权威（spec 之家）。纯 stdlib。

由 .github/workflows/conventions.yml（CI）与 tools/hooks/（本地可选）共用。校验：
  - commit 主题匹配 <type>(<scope>): <主题>，type ∈ TYPES；
  - 当前分支名匹配 <type>/<slug>，或属豁免（main / master / claude/* harness 分支）。
只强制**本分支新增**（相对 base=main，且非 merge 提交）且**自规范引入**
（governance/conventions.md 首次加入的提交）起的提交；base 上的历史与合并提交祖父豁免、不改写历史。
理据 / 生命周期散文见 governance/conventions.md，冻结见 decisions D-013。

用法：
  python tools/check_conventions.py [--branch <name>] [--base <ref>]  # 分支名 + 历史提交（CI / pre-push）
  python tools/check_conventions.py --message-file <path>             # 单条待写消息（commit-msg hook）
CI（pull_request）须传 --branch ${{ github.head_ref }}（真源分支，非 1/merge）与 --base origin/main。
"""
import re
import subprocess
import sys

TYPES = ("feat", "fix", "refactor", "test", "docs", "ci", "gov", "data", "exp", "chore", "revert")
SUBJECT_RE = re.compile(r"^(" + "|".join(TYPES) + r")(\([a-z0-9._-]+\))?: .+")
BRANCH_RE = re.compile(r"^(" + "|".join(TYPES) + r")/[a-z0-9._-]+$")
BRANCH_EXEMPT = re.compile(r"^(main|master|HEAD|claude/.+)$")   # 默认分支 + harness agent 分支


def _git(*args):
    # encoding=utf-8 显式：git 输出 UTF-8，Windows 默认 locale（GBK 等）会解码中文提交崩（NoneType.stdout）
    return subprocess.run(["git", *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace").stdout.strip()


def _has(ref):
    return bool(_git("rev-parse", "--verify", "-q", ref))


def _commits_to_check(base=None):
    """要强制的提交：自规范引入起（祖父豁免更早）∩ 本分支新增（相对 base、非 merge）。"""
    # --follow keeps the bootstrap point discoverable after the governance-root rename.
    intro = _git("log", "--follow", "--reverse", "--format=%H", "--", "governance/conventions.md")
    start = intro.splitlines()[0] if intro else None
    if not start:
        return []                                                  # 规范未引入：不强制
    has_parent = len(_git("rev-list", "--parents", "-n", "1", start).split()) > 1
    adopt = set(_git("rev-list", "--no-merges", f"{start}^..HEAD" if has_parent else "HEAD").splitlines())
    if base is None and _has("origin/main"):
        base = "origin/main"
    if base and _has(base):
        new = set(_git("rev-list", "--no-merges", f"{base}..HEAD").splitlines())
        return [s for s in adopt if s in new]                      # 仅本分支引入 + 采纳后
    return [s for s in adopt if s]                                 # 无 base（本地单分支）：采纳后全查


def check(base=None, branch=None):
    errs = []
    branch = branch or _git("rev-parse", "--abbrev-ref", "HEAD")
    if branch and not (BRANCH_RE.match(branch) or BRANCH_EXEMPT.match(branch)):
        errs.append(f"分支名 '{branch}' 不合规：应为 <type>/<slug>（type∈{{{','.join(TYPES)}}}；main/claude-* 豁免）")
    for sha in _commits_to_check(base):
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


def _arg(a, name):
    return a[a.index(name) + 1] if name in a and a.index(name) + 1 < len(a) else None


def main():
    for _s in (sys.stdout, sys.stderr):            # Windows 控制台默认非 UTF-8（仿 tests/gate.py）
        try:
            _s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    a = sys.argv[1:]
    if "--message-file" in a:
        errs = check_message(_arg(a, "--message-file"))
    else:
        errs = check(_arg(a, "--base"), _arg(a, "--branch"))
    if errs:
        sys.stderr.write("动作规范校验未过（见 governance/conventions.md）：\n")
        for e in errs:
            sys.stderr.write("  ✗ " + e + "\n")
        sys.exit(1)
    print("动作规范校验通过 ✓")


if __name__ == "__main__":
    main()
