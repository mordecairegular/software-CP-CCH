#!/usr/bin/env python3
"""Build final DOCX materials for a Chinese software copyright case.

The tool deliberately separates verified case facts from placeholders. If a
field is still pending, it writes a visible confirmation marker instead of
leaking values from a sample template.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

try:
    from PIL import Image
except Exception:  # pragma: no cover - optional for structural generation
    Image = None


LINES_PER_PAGE = 50
FRONT_LINES = 1650
BACK_LINES = 1650


@dataclass
class GeneratedFile:
    label: str
    path: Path


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def safe_filename(text: str) -> str:
    text = re.sub(r'[<>:"/\\|?*\n\r\t]+', "_", text)
    return re.sub(r"\s+", " ", text).strip()[:110]


def clean_value(value: str) -> str:
    value = value.strip()
    value = re.sub(r"\s+", " ", value)
    return value.strip("：: ")


def parse_application_fields(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    text = read_text(path)
    for line in text.splitlines():
        if not line.strip().startswith("➤"):
            continue
        line = line.strip().lstrip("➤").strip()
        if "：" in line:
            key, value = line.split("：", 1)
        elif ":" in line:
            key, value = line.split(":", 1)
        else:
            continue
        key = clean_value(key).replace(" / ", "/")
        data[key] = clean_value(value)
    return data


def pick_field(fields: dict[str, str], names: Iterable[str], default: str) -> str:
    for name in names:
        if name in fields and fields[name].strip():
            return fields[name].strip()
    return default


def pending_marker(label: str) -> str:
    return f"【待确认：{label}】"


def is_pending(value: str) -> bool:
    return (not value.strip()) or ("待" in value) or ("确认" in value)


def load_metadata(workdir: Path, args: argparse.Namespace) -> dict[str, str]:
    fields = parse_application_fields(workdir / "草稿" / "申请表信息.md")
    code_manifest = workdir / "草稿" / "代码提取清单.json"
    source_lines = ""
    if code_manifest.exists():
        try:
            manifest_data = json.loads(read_text(code_manifest))
            source_lines = str(sum(int(item.get("line_count") or 0) for item in manifest_data.get("files", [])))
            if source_lines == "0":
                source_lines = str(manifest_data.get("total_lines", ""))
        except json.JSONDecodeError:
            source_lines = ""

    software_name = args.software_name or pick_field(fields, ["软件全称"], pending_marker("软件全称"))
    short_name = args.short_name or pick_field(fields, ["软件简称"], "")
    version = args.version or pick_field(fields, ["版本号"], "V1.0")

    meta = {
        "software_name": software_name,
        "short_name": short_name or software_name,
        "version": version,
        "owner": args.owner or pick_field(fields, ["著作权人/申请人", "著作权人 / 申请人", "著作权人"], pending_marker("著作权人")),
        "developer": args.developer or pick_field(fields, ["开发者"], pending_marker("开发者")),
        "completion_date": args.completion_date or pick_field(fields, ["开发完成日期"], pending_marker("开发完成日期")),
        "first_publish": args.first_publish or pick_field(fields, ["首次发表日期"], "未发表（待确认）"),
        "rights_acquire": args.rights_acquire or pick_field(fields, ["权利取得方式"], "原始取得（待确认）"),
        "development_mode": args.development_mode or pick_field(fields, ["开发方式"], "独立开发/职务开发待确认"),
        "dev_hardware": pick_field(fields, ["开发硬件环境"], "普通个人计算机，八吉字节以上内存"),
        "runtime_hardware": pick_field(fields, ["运行硬件环境"], "普通个人计算机，支持本地浏览器访问"),
        "dev_os": pick_field(fields, ["开发操作系统"], "Windows"),
        "runtime_os": pick_field(fields, ["运行平台/操作系统"], "Windows"),
        "dev_tools": pick_field(fields, ["开发工具", "软件开发环境/开发工具"], "Python、文本编辑器、浏览器调试工具"),
        "support_env": pick_field(fields, ["运行支撑环境", "软件运行支撑环境/支持软件"], "Python 3.10 以上，本地浏览器"),
        "language": pick_field(fields, ["编程语言"], "Python、HTML、CSS、JavaScript"),
        "source_lines": args.source_lines or source_lines or pick_field(fields, ["源程序量"], pending_marker("源程序量")),
        "software_class": pick_field(fields, ["软件分类"], "应用软件"),
        "industry": pick_field(fields, ["行业领域", "面向领域/行业"], "待确认"),
        "classification_code": args.classification_code or "30200/6510（待确认）",
        "owner_category": args.owner_category or "待确认",
        "certificate_type": args.certificate_type or "待确认",
        "certificate_no": args.certificate_no or "【待确认：证件号码】",
        "nationality": args.nationality or "中国",
        "province_city": args.province_city or "【待确认：省份/城市】",
        "contact_name": args.contact_name or pending_marker("联系人"),
        "contact_phone": args.contact_phone or pending_marker("电话"),
        "contact_mobile": args.contact_mobile or pending_marker("手机"),
        "contact_email": args.contact_email or pending_marker("Email"),
        "contact_address": args.contact_address or pending_marker("详细地址"),
        "contact_postcode": args.contact_postcode or pending_marker("邮编"),
    }
    return meta


def extract_business_paragraphs(workdir: Path) -> dict[str, str]:
    text = read_text(workdir / "草稿" / "业务理解.md")
    manual = read_text(workdir / "草稿" / "操作手册.md")
    joined = "\n".join([text, manual])

    def section(title: str) -> str:
        pattern = re.compile(rf"^#+\s*{re.escape(title)}\s*$([\s\S]*?)(?=^#+\s|\Z)", re.MULTILINE)
        match = pattern.search(joined)
        return clean_markdown(match.group(1)) if match else ""

    return {
        "positioning": section("软件定位") or section("软件概述"),
        "core_problem": section("核心问题和使用场景"),
        "functions": section("主要功能模块") or section("主要功能"),
        "flow": section("典型操作流程"),
        "technical": section("技术特点的申请表口径") or section("技术特点"),
        "environment": section("运行环境"),
        "notes": section("使用注意事项"),
    }


def clean_markdown(text: str) -> str:
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"^\s*[-*]\s+", "・", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def compose_main_function_text(meta: dict[str, str], business: dict[str, str]) -> str:
    base = business.get("positioning") or ""
    functions = business.get("functions") or ""
    flow = business.get("flow") or ""
    problem = business.get("core_problem") or ""
    industry = strip_terminal_punct(meta["industry"])
    text = (
        f"{meta['software_name']}是一款面向{industry}的工程计算与风险筛查软件。"
        f"{base}\n\n"
        f"软件围绕业务对象、输入数据、处理流程和输出结果组织功能，"
        f"用于把用户在实际业务中的经验判断或重复操作转化为可输入、可处理、可复核、可留痕的软件流程。"
        f"{problem}\n\n"
        f"主要功能包括：{functions}\n\n"
        f"典型使用流程为：{flow}\n\n"
        "软件输出风险等级、安全裕度、击穿电压、气压、临界气隙上界、批量评估结果、历史记录和报告文件。"
        "这些结果可用于项目复核、业务办理、数据整理、过程留痕、结果归档和成果转化材料整理。"
        "软件结果用于工程筛查和研究分析参考，不替代现场检测、实验认证或适用标准。"
    )
    return re.sub(r"\s+", " ", text).strip()


def compose_technical_text(meta: dict[str, str], business: dict[str, str]) -> str:
    technical = business.get("technical") or ""
    text = (
        f"{technical} 软件采用本地化运行方式，前端界面、后端服务、计算模型、数据记录和报告生成模块相互配合。"
        "核心模型包括标准大气压力估算、空气帕邢击穿电压计算、安全裕度计算、危险间隙上界求解和风险等级判定。"
        "软件支持单点工况评估、批量数据处理、曲线和热力图显示、SQLite 本地记录、CSV 导出以及 HTML 报告生成。"
        "界面层使用原生页面与脚本实现交互和图表绘制，服务层使用本地 HTTP 接口组织评估请求，数据层使用结构化记录保存案例结果。"
    )
    return re.sub(r"\s+", " ", text).strip()


def strip_terminal_punct(text: str) -> str:
    return re.sub(r"[。；;，,\s]+$", "", text.strip())


def iter_unique_cells(row):
    seen = set()
    for cell in row.cells:
        key = cell._tc
        if key in seen:
            continue
        seen.add(key)
        yield cell


def unique_cells(row):
    return list(iter_unique_cells(row))


def set_cell_text(cell, text: str, *, size: int = 9, bold: bool = False) -> None:
    cell.text = ""
    para = cell.paragraphs[0]
    para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = para.add_run(str(text))
    run.font.name = "宋体"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    run.font.size = Pt(size)
    run.bold = bold
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER


def set_row_cell(table, row_idx: int, unique_idx: int, value: str, expected: str, report: list[str]) -> None:
    cells = unique_cells(table.rows[row_idx])
    row_text = " ".join(c.text for c in cells)
    if expected not in row_text:
        report.append(f"WARN: row {row_idx} expected label {expected!r}, actual={row_text[:80]!r}")
    if unique_idx >= len(cells):
        report.append(f"FAIL: row {row_idx} has no unique cell {unique_idx} for {expected}")
        return
    set_cell_text(cells[unique_idx], value)


def find_application_template(template_dir: Path | None) -> Path | None:
    if template_dir is None or not template_dir.exists():
        return None
    candidates = list(template_dir.glob("*.docx"))
    preferred = [
        p
        for p in candidates
        if ("申请表" in p.name or "登记申请" in p.name) and not p.name.startswith("~$")
    ]
    if preferred:
        return sorted(preferred)[0]
    return None


def build_application_docx(workdir: Path, out_dir: Path, meta: dict[str, str], business: dict[str, str], template_dir: Path) -> tuple[GeneratedFile, list[str]]:
    qa: list[str] = []
    template = find_application_template(template_dir)
    out_path = out_dir / f"01 计算机软件著作权登记申请表 — {safe_filename(meta['software_name'] + meta['version'])}.docx"
    if template:
        shutil.copyfile(template, out_path)
        doc = Document(str(out_path))
        if not doc.tables:
            qa.append("FAIL: application template has no table; fallback form required")
        else:
            table = doc.tables[0]
            fill_application_table(table, meta, business, qa)
    else:
        qa.append("WARN: no application template found; generated simple structured form")
        doc = create_simple_application_doc(meta, business)
    doc.save(str(out_path))
    qa.extend(verify_application_docx(out_path, meta))
    return GeneratedFile("申请表", out_path), qa


def fill_application_table(table, meta: dict[str, str], business: dict[str, str], qa: list[str]) -> None:
    main_functions = compose_main_function_text(meta, business)
    technical = compose_technical_text(meta, business)
    rows_needed = 30
    if len(table.rows) < rows_needed:
        qa.append(f"WARN: application table row count {len(table.rows)} < {rows_needed}; template may differ")

    set_row_cell(table, 0, 2, meta["software_name"], "软件名称", qa)
    set_row_cell(table, 0, 4, meta["version"], "版本号", qa)
    set_row_cell(table, 1, 2, meta["short_name"], "软件简称", qa)
    set_row_cell(table, 1, 4, meta["classification_code"], "分类号", qa)
    set_row_cell(table, 2, 2, "●原创 ○修改（含翻译软件、合成软件）", "软件作品说明", qa)
    set_row_cell(table, 3, 1, meta["completion_date"], "开发完成日期", qa)
    published = "○已发表 首次发表日期：______ 首次发表地点及其所在国：______  ●未发表（☑允许公众查询）"
    if "已发表" in meta["first_publish"] and "未发表" not in meta["first_publish"]:
        published = f"●已发表 首次发表日期：{meta['first_publish']} 首次发表地点及其所在国：【待确认】  ○未发表"
    set_row_cell(table, 4, 1, published, "发表状态", qa)
    dev_mode = "●独立开发 ○合作开发 ○委托开发 ○下达任务完成"
    if "职务" in meta["development_mode"]:
        dev_mode = "●独立开发（职务开发事实待确认） ○合作开发 ○委托开发 ○下达任务完成"
    set_row_cell(table, 5, 1, dev_mode, "开发方式", qa)
    set_row_cell(table, 7, 1, meta["owner"], "著作权人", qa)
    set_row_cell(table, 7, 2, meta["owner_category"], "著作权人", qa)
    set_row_cell(table, 7, 3, meta["certificate_type"], "著作权人", qa)
    set_row_cell(table, 7, 4, meta["certificate_no"], "著作权人", qa)
    set_row_cell(table, 7, 5, meta["nationality"], "著作权人", qa)
    set_row_cell(table, 7, 6, meta["province_city"], "著作权人", qa)
    set_row_cell(table, 8, 2, "●原始取得 ○继续取得（受让 承受 继承）", "权利取得方式", qa)
    set_row_cell(table, 9, 2, "●全部 ○部分", "权利范围", qa)
    set_row_cell(table, 10, 1, "☑应用软件 □嵌入式软件 □中间件 □操作系统", "软件分类", qa)
    set_row_cell(table, 11, 2, "●一般交存：提交源程序鉴别材料；提交一种软件文档（操作说明书）", "一般交存", qa)
    set_row_cell(table, 13, 2, truncate(meta["dev_hardware"], 50), "开发的硬件环境", qa)
    set_row_cell(table, 14, 2, truncate(meta["runtime_hardware"], 50), "运行的硬件环境", qa)
    set_row_cell(table, 15, 2, truncate(meta["dev_os"], 50), "操作系统", qa)
    set_row_cell(table, 16, 2, truncate(meta["dev_tools"], 50), "开发环境", qa)
    set_row_cell(table, 17, 2, truncate(meta["runtime_os"], 50), "运行平台", qa)
    set_row_cell(table, 18, 2, truncate(meta["support_env"], 50), "运行支撑环境", qa)
    set_row_cell(table, 19, 2, meta["language"], "编程语言", qa)
    set_row_cell(table, 19, 4, only_digits_or_text(meta["source_lines"]), "源程序量", qa)
    industry = strip_terminal_punct(meta["industry"])
    set_row_cell(table, 20, 2, truncate(f"用于{industry}的工程计算、风险筛查和报告生成。", 50), "开发目的", qa)
    set_row_cell(table, 21, 2, truncate(industry, 50), "面向领域", qa)
    set_row_cell(table, 22, 2, main_functions, "主要功能", qa)
    set_row_cell(table, 23, 2, "○APP ○游戏软件 ○教育软件 ○金融软件 ○医疗软件 ○地理信息软件 ○云计算软件 ○信息安全软件 ○大数据软件 ○人工智能软件 ○物联网软件 ●其他", "技术类别", qa)
    set_row_cell(table, 24, 2, truncate(technical, 100), "技术特点", qa)
    set_row_cell(table, 25, 2, "●由著作权人申请 ○由代理人申请（待确认）", "申请方式", qa)
    set_row_cell(table, 26, 2, meta["contact_name"], "姓名或名称", qa)
    set_row_cell(table, 26, 4, meta["contact_phone"], "电话", qa)
    set_row_cell(table, 27, 2, meta["contact_address"], "详细地址", qa)
    set_row_cell(table, 27, 4, meta["contact_postcode"], "邮编", qa)
    set_row_cell(table, 28, 2, meta["contact_name"], "联系人", qa)
    set_row_cell(table, 28, 4, meta["contact_mobile"], "手机", qa)
    set_row_cell(table, 29, 2, meta["contact_email"], "Email", qa)
    set_row_cell(table, 29, 4, "", "传真", qa)


def truncate(text: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def only_digits_or_text(text: str) -> str:
    match = re.search(r"\d+", text)
    if match:
        return match.group(0)
    return text


def create_simple_application_doc(meta: dict[str, str], business: dict[str, str]) -> Document:
    doc = Document()
    setup_normal_style(doc)
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("计算机软件著作权登记申请表")
    run.font.name = "宋体"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    run.font.size = Pt(18)
    run.bold = True
    table = doc.add_table(rows=0, cols=2)
    table.style = "Table Grid"
    for label, value in [
        ("软件名称", meta["software_name"]),
        ("软件简称", meta["short_name"]),
        ("版本号", meta["version"]),
        ("著作权人", meta["owner"]),
        ("开发者", meta["developer"]),
        ("开发完成日期", meta["completion_date"]),
        ("首次发表日期", meta["first_publish"]),
        ("主要功能", compose_main_function_text(meta, business)),
        ("技术特点", compose_technical_text(meta, business)),
    ]:
        row = table.add_row()
        set_cell_text(row.cells[0], label, bold=True)
        set_cell_text(row.cells[1], value)
    return doc


def verify_application_docx(path: Path, meta: dict[str, str]) -> list[str]:
    qa: list[str] = []
    doc = Document(str(path))
    all_text = "\n".join(p.text for p in doc.paragraphs)
    for table in doc.tables:
        for row in table.rows:
            all_text += "\n" + "\t".join(cell.text for cell in unique_cells(row))
    for label, value in [
        ("软件名称", meta["software_name"]),
        ("版本号", meta["version"]),
        ("著作权人", meta["owner"]),
    ]:
        if value and value not in all_text:
            qa.append(f"FAIL: application field not found after save: {label}={value}")
    leaked = [
        term.strip()
        for term in os.environ.get("SOFTWARE_CP_CCH_LEAK_TERMS", "").split("|")
        if term.strip()
    ]
    for item in leaked:
        if item in all_text and item not in {meta["software_name"], meta["short_name"], meta["contact_name"], meta["contact_phone"], meta["contact_email"]}:
            qa.append(f"WARN: sample value still present in application form: {item}")
    return qa or ["PASS: application key fields found after save"]


def setup_normal_style(doc: Document) -> None:
    style = doc.styles["Normal"]
    style.font.name = "宋体"
    style._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    style.font.size = Pt(10.5)
    for section in doc.sections:
        section.top_margin = Cm(2.0)
        section.bottom_margin = Cm(2.0)
        section.left_margin = Cm(2.3)
        section.right_margin = Cm(2.0)


def add_heading_cn(doc: Document, text: str, level: int = 1) -> None:
    para = doc.add_paragraph()
    para.style = f"Heading {min(level, 3)}"
    run = para.add_run(text)
    run.font.name = "黑体"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")
    run.font.size = Pt(16 if level == 1 else 13 if level == 2 else 11)
    run.bold = True


def set_header_footer(doc: Document, title: str) -> None:
    for section in doc.sections:
        header = section.header.paragraphs[0]
        header.text = title
        header.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in header.runs:
            run.font.name = "宋体"
            run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
            run.font.size = Pt(9)
        footer = section.footer.paragraphs[0]
        footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
        add_page_field(footer)


def add_page_field(paragraph) -> None:
    run = paragraph.add_run("第 ")
    run.font.size = Pt(9)
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    r = OxmlElement("w:r")
    t = OxmlElement("w:t")
    t.text = "1"
    r.append(t)
    fld.append(r)
    paragraph._p.append(fld)
    run2 = paragraph.add_run(" 页")
    run2.font.size = Pt(9)


def load_code_manifest(workdir: Path) -> dict:
    manifest_path = workdir / "草稿" / "代码提取清单.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"missing code manifest: {manifest_path}")
    return json.loads(read_text(manifest_path))


def read_code_lines(project_root: Path, manifest: dict) -> list[tuple[str, int, str]]:
    lines: list[tuple[str, int, str]] = []
    for item in manifest.get("files", []):
        rel = item["path"]
        path = project_root / rel
        if not path.exists():
            continue
        file_lines = read_text(path).splitlines()
        start = int(item.get("start_line") or 1)
        end = item.get("end_line") or len(file_lines)
        for idx in range(start, int(end) + 1):
            text = file_lines[idx - 1] if 0 <= idx - 1 < len(file_lines) else ""
            lines.append((rel, idx, text))
    return lines


def select_code_lines(lines: list[tuple[str, int, str]]) -> tuple[str, list[tuple[str, int, str]]]:
    if len(lines) <= FRONT_LINES + BACK_LINES:
        return "all-source-under-threshold", lines
    return "front-back-general-deposit", lines[:FRONT_LINES] + lines[-BACK_LINES:]


def build_source_docx(workdir: Path, out_dir: Path, meta: dict[str, str]) -> tuple[GeneratedFile, list[str]]:
    qa: list[str] = []
    manifest = load_code_manifest(workdir)
    project_root = Path(manifest.get("project_root") or workdir)
    lines = read_code_lines(project_root, manifest)
    mode, selected = select_code_lines(lines)
    out_path = out_dir / f"02 软件源代码 — {safe_filename(meta['short_name'])} {safe_filename(meta['version'])}.docx"

    doc = Document()
    setup_normal_style(doc)
    for section in doc.sections:
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)
        section.top_margin = Cm(1.7)
        section.bottom_margin = Cm(1.7)
        section.left_margin = Cm(1.8)
        section.right_margin = Cm(1.6)
    set_header_footer(doc, f"{meta['software_name']}{meta['version']} 源程序鉴别材料")
    add_cover(doc, meta, "软件源代码", f"生成方式：{'全量提交' if mode.startswith('all') else '前后连续段提交'}；真实源码行数：{len(lines)}；本文件代码行数：{len(selected)}")

    current_file = None
    code_line_count = 0
    page_no = 1
    add_heading_cn(doc, f"第 {page_no} 页", 1)
    add_code_meta_line(doc, f"软件名称：{meta['software_name']}    版本号：{meta['version']}")
    for rel, line_no, text in selected:
        if rel != current_file:
            current_file = rel
            add_code_meta_line(doc, f"// FILE: {rel} lines from {line_no}", bold=True)
        add_code_line(doc, text)
        code_line_count += 1
        if code_line_count % LINES_PER_PAGE == 0 and code_line_count < len(selected):
            doc.add_page_break()
            page_no += 1
            add_heading_cn(doc, f"第 {page_no} 页", 1)
            add_code_meta_line(doc, f"软件名称：{meta['software_name']}    版本号：{meta['version']}")
    doc.save(str(out_path))
    qa.append(f"PASS: source doc generated, mode={mode}, real_lines={len(lines)}, selected_lines={len(selected)}, target_pages={max(1, (len(selected)+LINES_PER_PAGE-1)//LINES_PER_PAGE)}")
    if len(lines) < 3000:
        qa.append("WARN: real source code is under 3000 lines; generated all-source document rather than padding or fabricating code")
    return GeneratedFile("源代码", out_path), qa


def add_cover(doc: Document, meta: dict[str, str], doc_type: str, subtitle: str) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(60)
    run = p.add_run(f"{meta['software_name']}{meta['version']}")
    run.font.name = "宋体"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    run.font.size = Pt(20)
    run.bold = True
    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run2 = p2.add_run(doc_type)
    run2.font.name = "黑体"
    run2._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")
    run2.font.size = Pt(22)
    run2.bold = True
    p3 = doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run3 = p3.add_run(subtitle)
    run3.font.size = Pt(10.5)
    doc.add_page_break()


def add_code_meta_line(doc: Document, text: str, *, bold: bool = False) -> None:
    para = doc.add_paragraph()
    para.paragraph_format.space_after = Pt(0)
    para.paragraph_format.line_spacing = 1.0
    run = para.add_run(text)
    run.font.name = "Courier New"
    run.font.size = Pt(9)
    run.bold = bold


def add_code_line(doc: Document, text: str) -> None:
    para = doc.add_paragraph()
    para.paragraph_format.space_after = Pt(0)
    para.paragraph_format.line_spacing = 1.0
    run = para.add_run(text if text else " ")
    run.font.name = "Courier New"
    run.font.size = Pt(8.5)


def find_screenshots(workdir: Path, explicit_dir: Path | None) -> list[Path]:
    dirs = []
    if explicit_dir:
        dirs.append(explicit_dir)
    dirs.append(workdir / "正式资料" / "word" / "screenshots")
    dirs.append(workdir / "截图")
    seen = set()
    files: list[Path] = []
    for directory in dirs:
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*.png")):
            if path.resolve() in seen:
                continue
            seen.add(path.resolve())
            files.append(path)
    preferred_terms = ["word_", "desktop", "batch", "history", "report", "mobile", "curve"]
    files.sort(key=lambda p: (min([p.name.find(t) if t in p.name else 999 for t in preferred_terms]), p.name))
    return files


def build_manual_docx(workdir: Path, out_dir: Path, meta: dict[str, str], business: dict[str, str], screenshots_dir: Path | None) -> tuple[GeneratedFile, list[str]]:
    qa: list[str] = []
    out_path = out_dir / f"03 {safe_filename(meta['software_name'] + meta['version'])} 操作说明书.docx"
    screenshots = find_screenshots(workdir, screenshots_dir)
    manual_text = read_text(workdir / "草稿" / "操作手册.md")

    doc = Document()
    setup_normal_style(doc)
    set_header_footer(doc, f"{meta['software_name']}{meta['version']} 操作说明书")
    add_cover(doc, meta, "操  作  说  明  书", f"编制人：{meta['developer']}    版本：{meta['version']}    日期：{datetime.now().strftime('%Y年%m月%d日')}")

    add_heading_cn(doc, "一、软件简介", 1)
    add_paragraphs(doc, compose_intro(meta, business))
    add_heading_cn(doc, "二、运行环境", 1)
    add_paragraphs(doc, business.get("environment") or "本软件运行于可使用 Python 3.10 以上环境的个人计算机，并通过本地浏览器访问 Web 操作界面。")
    add_heading_cn(doc, "三、软件启动与主界面总览", 1)
    add_paragraphs(doc, "用户进入软件目录后运行本地服务，在浏览器中访问 127.0.0.1 地址即可进入主界面。主界面由导航区、工况录入区、评估结果区、模型曲线区、批量评估区和历史记录区组成。")
    insert_screenshot_block(doc, screenshots[:1], "主界面总览", qa)

    modules = [
        ("四、单点评估操作", "在工况录入区域填写案例编号、项目名称、海拔、气隙、系统电压、安全系数和备注，点击“计算裕度”后，软件返回风险等级、安全裕度、气压、击穿电压、临界气隙上界和工程建议。"),
        ("五、模型曲线查看", "模型曲线区域用于查看不同海拔下安全裕度曲线、当前海拔帕邢曲线和系统电压热力图，帮助用户判断当前工况在参数空间中的风险位置。"),
        ("六、批量评估操作", "用户可粘贴 CSV 格式的多条工况数据，点击“运行批量评估”后软件逐行计算并显示总工况数、负裕度数量、临界数量和最低裕度，并导出结果文件。"),
        ("七、记录管理与导出", "软件将评估结果保存到本地 SQLite 数据库，并在记录表中展示最近案例。用户可导出 CSV 记录，用于项目评审、试验记录和复盘材料归档。"),
        ("八、报告生成", "完成单点评估后，用户点击“生成报告”，软件生成包含案例参数、计算结果、风险建议和适用边界说明的 HTML 报告。"),
    ]
    screenshot_cursor = 1
    for title, body in modules:
        add_heading_cn(doc, title, 1)
        add_paragraphs(doc, body)
        chunk = screenshots[screenshot_cursor : screenshot_cursor + 2]
        insert_screenshot_block(doc, chunk, title.split("、", 1)[-1], qa)
        screenshot_cursor += 2

    add_heading_cn(doc, "九、输出结果字段说明", 1)
    add_output_table(doc)
    add_heading_cn(doc, "十、计算方法和技术特点", 1)
    add_paragraphs(doc, compose_technical_text(meta, business))
    add_heading_cn(doc, "十一、常见问题与处理建议", 1)
    add_faq(doc)
    add_heading_cn(doc, "十二、使用边界与注意事项", 1)
    notes = business.get("notes") or "软件结果用于工程筛查和研究分析参考，不替代现场检测、实验认证、设备厂家设计规范或适用标准。输入气隙应来自明确的设计假设、检测数据或工程估计。"
    add_paragraphs(doc, notes)

    if manual_text:
        add_heading_cn(doc, "附录：原始操作手册草稿摘要", 1)
        add_paragraphs(doc, clean_markdown(manual_text)[:2500])

    doc.save(str(out_path))
    qa.append(f"{'PASS' if len(screenshots) >= 7 else 'WARN'}: manual screenshot count={len(screenshots)}")
    return GeneratedFile("操作说明书", out_path), qa


def compose_intro(meta: dict[str, str], business: dict[str, str]) -> str:
    industry = strip_terminal_punct(meta["industry"])
    return (
        f"{meta['software_name']}（简称：{meta['short_name']}，版本：{meta['version']}）是一款面向{industry}的本地运行软件。"
        f"{business.get('positioning') or ''}\n\n"
        "本软件针对目标业务中数据录入、过程处理、结果查看、记录保存和报告生成等需求，"
        "提供与项目实际功能相匹配的操作入口和输出能力。"
        "软件的工程价值在于把原本依赖经验和分散脚本的风险判断，组织成可输入、可复算、可导出、可归档的操作流程。"
    )


def add_paragraphs(doc: Document, text: str) -> None:
    for raw in re.split(r"\n{1,2}", text.strip()):
        line = raw.strip()
        if not line:
            continue
        para = doc.add_paragraph()
        para.paragraph_format.first_line_indent = Cm(0.74)
        para.paragraph_format.space_after = Pt(6)
        run = para.add_run(line)
        run.font.name = "宋体"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
        run.font.size = Pt(10.5)


def insert_screenshot_block(doc: Document, screenshots: list[Path], label: str, qa: list[str]) -> None:
    if not screenshots:
        para = doc.add_paragraph()
        run = para.add_run(f"【待补充截图：{label}】")
        run.font.color.rgb = RGBColor(180, 60, 40)
        qa.append(f"WARN: missing screenshot for {label}")
        return
    for path in screenshots:
        caption = doc.add_paragraph()
        caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap_run = caption.add_run(f"图：{label}（{path.name}）")
        cap_run.font.name = "宋体"
        cap_run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
        cap_run.font.size = Pt(9)
        try:
            width = Inches(6.2)
            if Image:
                with Image.open(path) as img:
                    if img.width < img.height:
                        width = Inches(4.0)
            doc.add_picture(str(path), width=width)
            doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        except Exception as exc:
            qa.append(f"WARN: failed to insert screenshot {path}: {exc}")


def add_output_table(doc: Document) -> None:
    rows = [
        ("pressure_kpa", "当前海拔下的标准大气压力，用于后续击穿电压计算。"),
        ("breakdown_voltage_v", "根据帕邢模型计算得到的空气气隙击穿电压。"),
        ("adjusted_voltage_v", "按安全系数修正后的击穿电压。"),
        ("safety_margin_pct", "系统电压相对于修正击穿电压的安全裕度百分比。"),
        ("critical_gap_upper_um", "指定海拔和电压下右支危险气隙上界。"),
        ("risk_label", "软件根据裕度阈值给出的风险等级。"),
        ("recommendation", "面向工程复核和试验验证的处理建议。"),
    ]
    table = doc.add_table(rows=1, cols=2)
    table.style = "Table Grid"
    table.rows[0].cells[0].text = "字段"
    table.rows[0].cells[1].text = "含义"
    for field, meaning in rows:
        row = table.add_row()
        row.cells[0].text = field
        row.cells[1].text = meaning
    for row in table.rows:
        for cell in row.cells:
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            for para in cell.paragraphs:
                for run in para.runs:
                    run.font.name = "宋体"
                    run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
                    run.font.size = Pt(9.5)


def add_faq(doc: Document) -> None:
    items = [
        ("输入海拔后结果异常怎么办？", "检查海拔单位是否为米，避免把千米或毫米误填入海拔字段。"),
        ("气隙数据不确定时如何使用？", "建议先按设计假设或失效复盘范围设置多个气隙值，通过批量评估观察风险变化。"),
        ("风险等级为负裕度是否等于现场必然击穿？", "不是。该结果表示模型筛查下裕度不足，应结合低压舱试验、现场检测和设备规范复核。"),
        ("批量评估无法运行怎么办？", "检查 CSV 表头是否包含 case_id、site_name、altitude_m、gap_um、system_voltage_v 和 note。"),
        ("生成报告后在哪里查看？", "报告文件默认保存到软件输出目录的 reports 子目录，可用本地浏览器打开。"),
        ("软件能否替代商业仿真软件？", "不能。V1.0 定位为气隙击穿裕度筛查和报告工具，不替代完整结构、电热耦合或电弧全过程仿真。"),
    ]
    for q, a in items:
        para = doc.add_paragraph()
        run = para.add_run(q)
        run.bold = True
        run.font.name = "宋体"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
        run.font.size = Pt(10.5)
        add_paragraphs(doc, a)


def collect_pending(meta: dict[str, str]) -> list[str]:
    return [f"{key}: {value}" for key, value in meta.items() if is_pending(value)]


def write_report(out_dir: Path, generated: list[GeneratedFile], meta: dict[str, str], qa_sections: dict[str, list[str]]) -> Path:
    path = out_dir / "word_generation_report.md"
    lines = [
        "# Word 三件套生成报告",
        "",
        f"- 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 软件：{meta['software_name']}",
        f"- 版本：{meta['version']}",
        "",
        "## 生成文件",
        "",
    ]
    for item in generated:
        lines.append(f"- {item.label}：`{item.path}`")
    pending = collect_pending(meta)
    lines.extend(["", "## 待确认字段", ""])
    if pending:
        lines.extend(f"- {item}" for item in pending)
    else:
        lines.append("- 无")
    lines.extend(["", "## QA 记录", ""])
    for name, items in qa_sections.items():
        lines.append(f"### {name}")
        lines.extend(f"- {item}" for item in items)
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def build_all(args: argparse.Namespace) -> int:
    workdir = Path(args.workdir).resolve()
    template_dir = Path(args.template_dir).resolve() if args.template_dir else None
    out_dir = Path(args.out_dir).resolve() if args.out_dir else workdir / "正式资料" / "word"
    out_dir.mkdir(parents=True, exist_ok=True)

    meta = load_metadata(workdir, args)
    business = extract_business_paragraphs(workdir)
    screenshots_dir = Path(args.screenshots_dir).resolve() if args.screenshots_dir else None

    generated: list[GeneratedFile] = []
    qa_sections: dict[str, list[str]] = {}

    app, app_qa = build_application_docx(workdir, out_dir, meta, business, template_dir)
    generated.append(app)
    qa_sections["申请表"] = app_qa

    source, source_qa = build_source_docx(workdir, out_dir, meta)
    generated.append(source)
    qa_sections["源代码"] = source_qa

    manual, manual_qa = build_manual_docx(workdir, out_dir, meta, business, screenshots_dir)
    generated.append(manual)
    qa_sections["操作说明书"] = manual_qa

    report_path = write_report(out_dir, generated, meta, qa_sections)
    print(f"OK generated {len(generated)} DOCX files")
    print(report_path)
    for item in generated:
        print(item.path)
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workdir", required=True, help="软件著作权申请资料目录")
    parser.add_argument("--template-dir", help="代理样本文档或申请表模板目录")
    parser.add_argument("--out-dir", help="DOCX 输出目录，默认 <workdir>/正式资料/word")
    parser.add_argument("--screenshots-dir", help="优先使用的截图目录")
    parser.add_argument("--software-name")
    parser.add_argument("--short-name")
    parser.add_argument("--version")
    parser.add_argument("--owner")
    parser.add_argument("--developer")
    parser.add_argument("--completion-date")
    parser.add_argument("--first-publish")
    parser.add_argument("--rights-acquire")
    parser.add_argument("--development-mode")
    parser.add_argument("--source-lines")
    parser.add_argument("--classification-code")
    parser.add_argument("--owner-category")
    parser.add_argument("--certificate-type")
    parser.add_argument("--certificate-no")
    parser.add_argument("--nationality")
    parser.add_argument("--province-city")
    parser.add_argument("--contact-name")
    parser.add_argument("--contact-phone")
    parser.add_argument("--contact-mobile")
    parser.add_argument("--contact-email")
    parser.add_argument("--contact-address")
    parser.add_argument("--contact-postcode")
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(build_all(parse_args()))
