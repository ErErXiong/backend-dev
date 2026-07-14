#!/usr/bin/env python3
"""只读收集 Git 上下文，供 backend-retro 生成经验候选。"""

import json
import subprocess
import sys
from pathlib import Path


def run(command, cwd):
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return result.stdout.strip() if result.returncode == 0 else ""


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    if run(["git", "rev-parse", "--is-inside-work-tree"], root) != "true":
        print(json.dumps({"repository": str(root), "is_git_repository": False}, ensure_ascii=False))
        return

    print(json.dumps({
        "repository": str(root),
        "is_git_repository": True,
        "status": run(["git", "status", "--short"], root).splitlines(),
        "changed_files": run(["git", "diff", "--name-only"], root).splitlines(),
        "staged_files": run(["git", "diff", "--cached", "--name-only"], root).splitlines(),
        "recent_commit": run(["git", "log", "-1", "--oneline"], root),
        "diff_stat": run(["git", "diff", "--stat"], root),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
