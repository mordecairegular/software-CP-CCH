# 安装到 Codex

## 接收方安装

1. 解压收到的 `software-CP-CCH_*.zip`。
2. 确认解压后的目录中直接包含 `SKILL.md`、`prompts/`、`references/`、`tools/`。
3. 将整个目录改名或放置为：

```text
C:\Users\<你的用户名>\.codex\skills\software-CP-CCH
```

4. 重新打开 Codex，或新开一个 Codex 线程。
5. 在对话中输入：

```text
[$software-CP-CCH](C:\Users\<你的用户名>\.codex\skills\software-CP-CCH\SKILL.md) 帮我做软著材料
```

也可以直接说：

```text
使用 software-CP-CCH 为这个项目做软著申请材料
```

## 依赖

- 基础扫描、审计、自检脚本使用 Python 标准库。
- Word 三件套生成需要 `python-docx` 和 `Pillow`。
- 如果 Codex 自带 Documents 运行时可用，通常已包含这些库。
- 如果使用系统 Python，需要安装：

```bash
pip install -r requirements.txt
```

## Word 三件套

本 skill 的正式交付不是 Markdown 草稿，而是：

- 申请表 `.docx`
- 软件源代码 `.docx`
- 操作说明书 `.docx`

可运行：

```bash
python tools/word_material_builder.py --workdir <软件著作权申请资料目录>
```

如果有代理提供的申请表模板或样本文档目录，传入：

```bash
python tools/word_material_builder.py --workdir <目录> --template-dir <模板目录>
```

生成后查看：

```text
正式资料/word/word_generation_report.md
```

## 注意

- 不要把他人的样本文档、联系人、电话、证件号当成本案事实。
- 权属、日期、开发方式、证件和联系人未确认时，只能输出待确认版。
- 源代码必须来自真实项目；源码不足页数时全量提交，不得伪造代码凑页数。
