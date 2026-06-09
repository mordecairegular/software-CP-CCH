#!/usr/bin/env python3
"""Extract confirmed source code pages for software copyright materials."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


LINES_PER_PAGE = 50
SPLIT_PAGES = 60
PART_PAGES = 30


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def relpath(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8-sig", errors="replace").splitlines()


def selected_files(selection: dict[str, Any]) -> list[dict[str, Any]]:
    files = selection.get("files") or []
    return [item for item in files if isinstance(item, dict) and item.get("selected")]


def collect_lines(project: Path, selection: dict[str, Any]) -> tuple[list[str], list[dict[str, Any]]]:
    output: list[str] = []
    manifest: list[dict[str, Any]] = []
    for item in selected_files(selection):
        rel = str(item.get("path") or "").strip()
        if not rel:
            continue
        path = (project / rel).resolve()
        if not path.exists() or project.resolve() not in path.parents and path != project.resolve():
            raise SystemExit(f"Selected file is missing or outside project: {rel}")
        lines = read_lines(path)
        start = max(int(item.get("start_line") or 1), 1)
        end_raw = item.get("end_line")
        end = int(end_raw) if end_raw else len(lines)
        end = min(end, len(lines))
        if start > end:
            raise SystemExit(f"Invalid line range: {rel} {start}-{end}")
        chunk = lines[start - 1 : end]
        output.append(f"// FILE: {rel} lines {start}-{end}")
        output.extend(chunk)
        output.append("")
        manifest.append(
            {
                "path": rel,
                "start_line": start,
                "end_line": end,
                "line_count": len(chunk),
                "model_reason": item.get("model_reason", ""),
            }
        )
    return output, manifest


def paginate(lines: list[str]) -> list[list[str]]:
    return [lines[i : i + LINES_PER_PAGE] for i in range(0, len(lines), LINES_PER_PAGE)] or [[]]


def page_md(page_no: int, page_lines: list[str], software_name: str, version: str) -> list[str]:
    return [
        f"## 第 {page_no} 页",
        "",
        f"软件名称：{software_name}    版本号：{version}",
        "",
        "```text",
        *page_lines,
        "```",
        "",
    ]


def write_pages(path: Path, pages: list[tuple[int, list[str]]], software_name: str, version: str) -> None:
    lines = [f"# {software_name}{version} 源程序鉴别材料", ""]
    for page_no, page_lines in pages:
        lines.extend(page_md(page_no, page_lines, software_name, version))
    path.write_text("\n".join(lines), encoding="utf-8")


def write_manifest_md(path: Path, manifest: dict[str, Any]) -> None:
    lines = [
        "# 代码提取清单",
        "",
        f"- 软件名称：{manifest['software_name']}",
        f"- 版本号：{manifest['version']}",
        f"- 项目路径：`{manifest['project_root']}`",
        f"- 抽取总行数：{manifest['total_lines']}",
        f"- 总页数：{manifest['total_pages']}",
        f"- 输出模式：{manifest['mode']}",
        "",
        "## 文件行段",
        "",
    ]
    for item in manifest["files"]:
        lines.append(f"- `{item['path']}`：{item['start_line']}-{item['end_line']}，{item['line_count']} 行；{item.get('model_reason') or '未填写理由'}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--selection", required=True)
    parser.add_argument("--software-name", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--out-dir", default="软件著作权申请资料/草稿")
    args = parser.parse_args()

    project = Path(args.project).resolve()
    selection = read_json(Path(args.selection))
    if not selected_files(selection):
        raise SystemExit("No selected files in selection JSON.")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    lines, files = collect_lines(project, selection)
    pages = paginate(lines)
    numbered = list(enumerate(pages, start=1))
    total_pages = len(numbered)

    if total_pages >= SPLIT_PAGES:
        front = numbered[:PART_PAGES]
        back = numbered[-PART_PAGES:]
        write_pages(out_dir / "代码-前30页.md", front, args.software_name, args.version)
        write_pages(out_dir / "代码-后30页.md", back, args.software_name, args.version)
        mode = "front-back-30-pages"
    else:
        write_pages(out_dir / "代码-全部.md", numbered, args.software_name, args.version)
        mode = "all-source-under-60-pages"

    manifest = {
        "software_name": args.software_name,
        "version": args.version,
        "project_root": str(project),
        "lines_per_page": LINES_PER_PAGE,
        "total_lines": len(lines),
        "total_pages": total_pages,
        "mode": mode,
        "files": files,
    }
    (out_dir / "代码提取清单.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    write_manifest_md(out_dir / "代码提取清单.md", manifest)
    print(f"OK source material: {out_dir} ({mode}, {total_pages} pages)")


if __name__ == "__main__":
    main()
