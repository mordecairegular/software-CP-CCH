#!/usr/bin/env python3
"""Check draft software copyright materials for completeness and consistency."""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path
from typing import Any


AI_PHRASES = [
    "赋能",
    "一站式",
    "智能化",
    "高效便捷",
    "显著提升",
    "全方位",
    "强大能力",
    "丰富功能",
    "旨在",
]


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="replace")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def app_field(text: str, name: str) -> str:
    pattern = re.compile(rf"^➤{re.escape(name)}[:：]\s*(.+)$", re.M)
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def has_confirmation(workdir: Path, rel: str, key: str) -> bool:
    return bool(read_json(workdir / rel).get(key))


def docx_text(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as zf:
            parts = [
                name
                for name in zf.namelist()
                if name.startswith("word/") and name.endswith(".xml")
            ]
            return "\n".join(zf.read(name).decode("utf-8", errors="replace") for name in parts)
    except (zipfile.BadZipFile, FileNotFoundError):
        return ""


def check(workdir: Path) -> dict[str, Any]:
    draft = workdir / "草稿"
    issues: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    required = [
        draft / "业务理解.md",
        draft / "权属与AI辅助审计.md",
        draft / "申请表信息.md",
        draft / "操作手册.md",
        draft / "代码提取清单.json",
    ]
    for path in required:
        if not path.exists():
            issues.append({"type": "missing", "message": f"缺少 {path}"})

    confirmations = [
        ("草稿/业务理解确认.json", "business_confirmed", "业务理解未确认"),
        ("草稿/代码选择确认.json", "code_selection_confirmed", "代码选择未确认"),
        ("草稿/申请表字段确认.json", "application_fields_confirmed", "申请表字段未确认"),
        ("截图方式确认.json", "screenshot_method_confirmed", "截图方式未确认"),
    ]
    for rel, key, msg in confirmations:
        if not has_confirmation(workdir, rel, key):
            warnings.append({"type": "confirmation", "message": msg})

    app_text = read_text(draft / "申请表信息.md")
    software_name = app_field(app_text, "软件全称")
    version = app_field(app_text, "版本号")
    if "待用户确认" in app_text:
        warnings.append({"type": "pending-field", "message": "申请表信息仍包含待用户确认字段"})
    if not software_name:
        issues.append({"type": "field", "message": "缺少软件全称"})
    if not version:
        issues.append({"type": "field", "message": "缺少版本号"})

    manual = read_text(draft / "操作手册.md")
    if manual:
        if software_name and software_name not in manual:
            warnings.append({"type": "consistency", "message": "操作手册未出现已确认软件全称"})
        phrase_hits = [p for p in AI_PHRASES if p in manual]
        if len(phrase_hits) >= 3:
            warnings.append({"type": "ai-style", "message": "操作手册存在较多制式/营销化短语：" + "、".join(phrase_hits[:8])})
        if "【截图预留" not in manual and not any((workdir / "截图").glob("*")):
            warnings.append({"type": "screenshot", "message": "未发现截图，也未发现可见截图预留文字"})

    manifest = read_json(draft / "代码提取清单.json")
    if manifest:
        if software_name and manifest.get("software_name") != software_name:
            warnings.append({"type": "consistency", "message": "代码提取清单的软件名与申请表不一致"})
        if version and manifest.get("version") != version:
            warnings.append({"type": "consistency", "message": "代码提取清单版本号与申请表不一致"})
        if not manifest.get("files"):
            issues.append({"type": "source", "message": "代码提取清单没有文件行段"})

    word_dir = workdir / "正式资料" / "word"
    if not word_dir.exists():
        issues.append({"type": "word", "message": "缺少正式 Word 输出目录：正式资料/word"})
    else:
        docxs = sorted(word_dir.glob("*.docx"))
        expected = {
            "01": "申请表 Word 文件",
            "02": "源代码 Word 文件",
            "03": "操作说明书 Word 文件",
        }
        for prefix, label in expected.items():
            matches = [p for p in docxs if p.name.startswith(prefix)]
            if not matches:
                issues.append({"type": "word", "message": f"缺少 {label}"})
                continue
            text = docx_text(matches[0])
            if not text:
                issues.append({"type": "word", "message": f"{label} 不是可读取的 DOCX：{matches[0]}"})
                continue
            if software_name and software_name not in text:
                warnings.append({"type": "word-consistency", "message": f"{label} 未检测到软件全称"})
            if version and version not in text:
                warnings.append({"type": "word-consistency", "message": f"{label} 未检测到版本号"})
            if prefix == "03":
                artifact_hits = [item for item in ["```", "mermaid", "草稿摘要", "原始操作手册草稿摘要"] if item in text]
                if artifact_hits:
                    issues.append({"type": "manual-artifact", "message": "操作说明书 Word 含草稿/代码痕迹：" + "、".join(artifact_hits)})
        report = read_text(word_dir / "word_generation_report.md")
        if not report:
            warnings.append({"type": "word", "message": "缺少 Word 生成报告 word_generation_report.md"})
        elif "待确认" in report:
            warnings.append({"type": "word-pending", "message": "Word 生成报告仍包含待确认字段"})

    status = "PASS"
    if warnings:
        status = "WARN"
    if issues:
        status = "FAIL"

    return {
        "status": status,
        "software_name": software_name,
        "version": version,
        "issues": issues,
        "warnings": warnings,
    }


def write_md(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# 交付自检记录",
        "",
        f"- 结论：{result['status']}",
        f"- 软件全称：{result.get('software_name') or '未识别'}",
        f"- 版本号：{result.get('version') or '未识别'}",
        "",
        "## 失败项",
        "",
    ]
    if result["issues"]:
        for item in result["issues"]:
            lines.append(f"- [{item['type']}] {item['message']}")
    else:
        lines.append("- 无")
    lines.extend(["", "## 警告项", ""])
    if result["warnings"]:
        for item in result["warnings"]:
            lines.append(f"- [{item['type']}] {item['message']}")
    else:
        lines.append("- 无")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", default="软件著作权申请资料")
    args = parser.parse_args()

    workdir = Path(args.workdir)
    result = check(workdir)
    (workdir / "交付自检记录.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    write_md(workdir / "交付自检记录.md", result)
    print(f"{result['status']} material check: {workdir}")


if __name__ == "__main__":
    main()
