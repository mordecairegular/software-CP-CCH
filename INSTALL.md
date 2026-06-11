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

## Git clone 全局安装

如果对方也使用 Codex，推荐直接安装到当前 Windows 用户的全局 skill 目录：

```powershell
git clone https://github.com/mordecairegular/software-CP-CCH.git "$env:USERPROFILE\.codex\skills\software-CP-CCH"
```

已有旧版本时，先备份或在目录内执行：

```powershell
cd "$env:USERPROFILE\.codex\skills\software-CP-CCH"
git pull
```

“全局安装”的含义是：目录位于 `%USERPROFILE%\.codex\skills\software-CP-CCH`，新开的 Codex 线程可以直接通过 `$software-CP-CCH` 触发。

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

如果有已认可的历史 Word 三件套母版，优先传入：

```bash
python tools/word_material_builder.py --workdir <目录> --reference-word-dir <已认可三件套目录>
```

生成后查看：

```text
正式资料/word/word_generation_report.md
```

## 注意

- 不要把他人的样本文档、联系人、电话、证件号当成本案事实。
- 权属、日期、开发方式、证件和联系人未确认时，只能输出待确认版。
- 源代码必须来自真实项目；源码不足页数时全量提交，不得伪造代码凑页数。
- 本轮新开发软件时，不要默认生成粗糙裸 UI；应先完成候选挖掘、产品设计 brief、UI 技术栈选择和截图验收。

## 发布/替换检查清单

- 运行 `python -m py_compile tools/*.py`。
- 确认 `git status --short` 干净。
- 排除 `__pycache__`、案件输出、`.venv`、临时 Word 锁文件。
- 抽查 `README.md`、`INSTALL.md`、`SKILL.md` 版本和规则一致。
- 对比本地安装目录与发布 clone 的关键文件哈希。
- 确认无历史案件名称、联系人、手机号、证件号、模板样本残留。
