#!/usr/bin/env python3
"""Append trial revision records for the software-CP-CCH skill itself."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", default="docs/trial-revision-log.md")
    parser.add_argument("--summary", required=True)
    parser.add_argument("--decision", required=True)
    parser.add_argument("--files", default="")
    parser.add_argument("--verify", default="")
    parser.add_argument("--stage", default="试用反馈")
    parser.add_argument("--scope", default="未归类")
    parser.add_argument("--regression", default="")
    parser.add_argument("--open-questions", default="")
    args = parser.parse_args()

    path = Path(args.log)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("# software-CP-CCH 试用修订记录\n\n", encoding="utf-8")

    entry = [
        f"## {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {args.stage}",
        "",
        f"- 用户反馈摘要：{args.summary}",
        f"- 影响范围：{args.scope}",
        f"- 修订决策：{args.decision}",
        f"- 改动文件：{args.files or '待补充'}",
        f"- 验证方式和结果：{args.verify or '待补充'}",
        f"- 回归场景：{args.regression or '待补充'}",
        f"- 未决问题：{args.open_questions or '无'}",
        "",
    ]
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(entry))
    print(f"OK revision log appended: {path}")


if __name__ == "__main__":
    main()

