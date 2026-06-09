#!/usr/bin/env python3
"""Record explicit user confirmations for software copyright workflow gates."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


STAGE_FILES = {
    "business": ("草稿/业务理解确认.json", "business_confirmed"),
    "code-selection": ("草稿/代码选择确认.json", "code_selection_confirmed"),
    "application-fields": ("草稿/申请表字段确认.json", "application_fields_confirmed"),
    "screenshot-method": ("截图方式确认.json", "screenshot_method_confirmed"),
    "markdown": ("草稿/最终生成确认.json", "markdown_confirmed"),
    "rights-ai": ("草稿/权属AI审计确认.json", "rights_ai_confirmed"),
    "mvp": ("草稿/MVP确认.json", "mvp_confirmed"),
}


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", default="软件著作权申请资料")
    parser.add_argument("--stage", required=True, choices=sorted(STAGE_FILES))
    parser.add_argument("--note", default="用户已确认")
    parser.add_argument("--method", default="")
    args = parser.parse_args()

    rel_path, key = STAGE_FILES[args.stage]
    out_path = Path(args.workdir) / rel_path
    data = read_json(out_path)
    data[key] = True
    data["stage"] = args.stage
    data["note"] = args.note
    data["method"] = args.method
    data["confirmed_at"] = datetime.now().isoformat(timespec="seconds")
    write_json(out_path, data)
    print(f"OK confirmed {args.stage}: {out_path}")


if __name__ == "__main__":
    main()
