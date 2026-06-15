#!/usr/bin/env python3
"""Check draft software copyright materials for completeness and consistency."""

from __future__ import annotations

import argparse
import html
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
BAD_PUNCT_PATTERNS = (
    "。；",
    "；。",
    "。。",
    "，，",
    "、、",
    "，。",
    "、。",
    "；；",
    "：。",
    "；，",
    "，；",
)


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "gbk", "cp936"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def read_json(path: Path) -> Any:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def app_field(text: str, name: str) -> str:
    pattern = re.compile(rf"^➤{re.escape(name)}[:：]\s*(.+)$", re.M)
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def has_confirmation(workdir: Path, rel: str, key: str) -> bool:
    data = read_json(workdir / rel)
    return isinstance(data, dict) and bool(data.get(key))


def screenshot_manifest_records(path: Path) -> list[dict[str, Any]]:
    data = read_json(path)
    if isinstance(data, dict):
        records = data.get("screenshots") or data.get("items") or []
    elif isinstance(data, list):
        records = data
    else:
        records = []
    return [item for item in records if isinstance(item, dict)]


def accepted_word_screenshots(workdir: Path) -> list[dict[str, Any]]:
    manifest_path = workdir / "截图" / "screenshot_manifest.json"
    records = screenshot_manifest_records(manifest_path)
    return [
        item
        for item in records
        if item.get("accepted") is not False and item.get("used_in_word") is not False
    ]


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


def docx_image_count(path: Path) -> int:
    try:
        with zipfile.ZipFile(path) as zf:
            return len([name for name in zf.namelist() if name.startswith("word/media/") and not name.endswith("/")])
    except (zipfile.BadZipFile, FileNotFoundError):
        return 0


def text_quality_failures(label: str, text: str, *, min_cjk: int = 0) -> list[str]:
    failures: list[str] = []
    plain_text = html.unescape(re.sub(r"<[^>]+>", "", text))
    replacement_count = text.count("\ufffd")
    qmark_count = text.count("?")
    if replacement_count:
        failures.append(f"{label} 含替换字符，疑似解码损坏，数量 {replacement_count}")
    if re.search(r"\?{3,}", text) and qmark_count > 20:
        failures.append(f"{label} 含大量连续问号，疑似中文被不可逆替换，数量 {qmark_count}")
    if min_cjk:
        cjk = len(re.findall(r"[\u4e00-\u9fff]", text))
        if len(text) > 1000 and cjk < min_cjk:
            failures.append(f"{label} 中文字符数量异常偏低，疑似写入 DOCX 时编码丢失，中文数 {cjk}")
    punct_hits = [pattern for pattern in BAD_PUNCT_PATTERNS if pattern in plain_text]
    if punct_hits:
        failures.append(f"{label} 含异常中文标点组合：" + "、".join(punct_hits))
    inline_bullet_lines = [
        line.strip()
        for line in plain_text.splitlines()
        if sum(line.count(mark) for mark in ("・", "•", "·")) >= 2
    ]
    if inline_bullet_lines:
        failures.append(f"{label} 含同一行伪项目符号列表，应改为真实 Word 列表")
    return failures


def check(workdir: Path, word_dir_override: Path | None = None) -> dict[str, Any]:
    draft = workdir / "草稿"
    issues: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    required = [
        draft / "软著候选挖掘.md",
        draft / "业务理解.md",
        draft / "权属与AI辅助审计.md",
        draft / "申请表信息.md",
        draft / "操作手册.md",
        draft / "代码提取清单.json",
    ]
    for path in required:
        if not path.exists():
            issues.append({"type": "missing", "message": f"缺少 {path}"})

    candidate_json = workdir / "analysis" / "候选软件挖掘.json"
    if not candidate_json.exists():
        issues.append({"type": "candidate", "message": "缺少 analysis/候选软件挖掘.json，无法确认申报对象边界"})
    else:
        candidate_data = read_json(candidate_json)
        if not isinstance(candidate_data, dict):
            issues.append({"type": "candidate", "message": "analysis/候选软件挖掘.json 不是对象结构"})
        else:
            candidates = candidate_data.get("candidates") or []
            if not candidates:
                issues.append({"type": "candidate", "message": "候选软件挖掘记录没有 candidates"})
            if not any(item.get("recommended") for item in candidates if isinstance(item, dict)):
                warnings.append({"type": "candidate", "message": "候选软件挖掘记录没有 recommended 候选"})

    confirmations = [
        ("草稿/申报对象确认.json", "candidate_confirmed", "申报对象未确认"),
        ("草稿/业务理解确认.json", "business_confirmed", "业务理解未确认"),
        ("草稿/代码选择确认.json", "code_selection_confirmed", "代码选择未确认"),
        ("草稿/申请表字段确认.json", "application_fields_confirmed", "申请表字段未确认"),
        ("截图方式确认.json", "screenshot_method_confirmed", "截图方式未确认"),
    ]
    for rel, key, msg in confirmations:
        if not has_confirmation(workdir, rel, key):
            severity = issues if key == "candidate_confirmed" else warnings
            severity.append({"type": "confirmation", "message": msg})

    mvp_record = draft / "MVP开发记录.md"
    if mvp_record.exists():
        ui_design = draft / "UI设计方案.md"
        if not ui_design.exists():
            issues.append({"type": "ui-design", "message": "本轮新开发/改造软件缺少 草稿/UI设计方案.md"})
        if not has_confirmation(workdir, "草稿/UI设计确认.json", "ui_design_confirmed"):
            issues.append({"type": "ui-design", "message": "本轮新开发/改造软件缺少 UI 设计确认记录"})
        screenshot_manifest = workdir / "截图" / "screenshot_manifest.json"
        if not screenshot_manifest.exists():
            issues.append({"type": "ui-screenshot", "message": "本轮新开发/改造软件缺少 截图/screenshot_manifest.json"})
        else:
            accepted = accepted_word_screenshots(workdir)
            if len(accepted) < 5:
                issues.append({"type": "ui-screenshot", "message": f"验收且用于 Word 的截图少于 5 张：{len(accepted)}"})

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
        if not any((workdir / "截图").glob("*")):
            warnings.append({"type": "screenshot", "message": "未发现截图；截图缺口只能留在草稿中，正式 Word 不得使用占位截图"})

    manifest = read_json(draft / "代码提取清单.json")
    if manifest and not isinstance(manifest, dict):
        issues.append({"type": "source", "message": "代码提取清单 JSON 不是对象结构"})
    elif manifest:
        if software_name and manifest.get("software_name") != software_name:
            warnings.append({"type": "consistency", "message": "代码提取清单的软件名与申请表不一致"})
        if version and manifest.get("version") != version:
            warnings.append({"type": "consistency", "message": "代码提取清单版本号与申请表不一致"})
        if not manifest.get("files"):
            issues.append({"type": "source", "message": "代码提取清单没有文件行段"})

    word_dir = word_dir_override or workdir / "正式资料" / "word"
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
            if prefix == "01":
                for failure in text_quality_failures(label, text, min_cjk=80):
                    issues.append({"type": "word-encoding", "message": failure})
            if prefix == "03":
                for failure in text_quality_failures(label, text, min_cjk=120):
                    issues.append({"type": "word-encoding", "message": failure})
                artifact_hits = [item for item in ["```", "mermaid", "草稿摘要", "原始操作手册草稿摘要"] if item in text]
                if artifact_hits:
                    issues.append({"type": "manual-artifact", "message": "操作说明书 Word 含草稿/代码痕迹：" + "、".join(artifact_hits)})
                image_count = docx_image_count(matches[0])
                if image_count == 0:
                    issues.append({"type": "manual-image", "message": "操作说明书 Word 未嵌入真实截图"})
                elif image_count < 3:
                    warnings.append({"type": "manual-image", "message": f"操作说明书 Word 截图数量偏少：{image_count}"})
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
        "word_dir": str(word_dir),
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
        f"- Word 目录：{result.get('word_dir') or '未记录'}",
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
    parser.add_argument("--word-dir", help="可选：指定待检查的 Word 输出目录，默认 <workdir>/正式资料/word")
    args = parser.parse_args()

    workdir = Path(args.workdir)
    word_dir = Path(args.word_dir) if args.word_dir else None
    result = check(workdir, word_dir)
    (workdir / "交付自检记录.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    write_md(workdir / "交付自检记录.md", result)
    print(f"{result['status']} material check: {workdir}")


if __name__ == "__main__":
    main()
