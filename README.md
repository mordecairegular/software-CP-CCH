# software-CP-CCH

面向中国计算机软件著作权登记的 Codex skill。它把“软著材料生成”升级为一个完整案件流程：已有软件可以扫描、审计和出材料；没有软件时，先帮用户收敛真实可运行的最小软件，再走申请材料链路。

## 设计重点

- 软著不是专利：重点是软件表达、真实源码、文档鉴别材料、权属和一致性。
- 不伪造代码：源程序鉴别材料必须来自真实项目或本轮实际开发的软件。
- 不堆 AI 味文案：说明书必须能回溯到真实界面、真实对象、真实操作和真实反馈。
- 交付 Word 三件套：最终应生成申请表、源程序鉴别材料、操作说明书 `.docx`，并做表格回读与版式核验。
- 有 AI 参与时留证据：记录人工需求定义、修改、整合、测试、提交和版本管理。
- 试用期修订留痕：每轮影响 skill/agent 自身的反馈先写入 `docs/trial-revision-log.md`，再改规则、prompt 或脚本。
- 先草稿后确认再正式输出：关键口径让用户确认，避免材料写偏。

## 文件结构

```text
.
├── SKILL.md
├── prompts/
├── references/
├── tools/
├── docs/
└── INSTALL.md
```

本技能的可执行入口是根目录 `SKILL.md`；通用规则和模板说明放在 `references/`。

## 试用修订

试用过程中请把反馈分成两类：

- 某个软著案件材料要改：写入该案件目录的 `草稿/修订记录.md`。
- 这个 skill/agent 本身要改：先按 [prompts/trial_revision_loop.md](prompts/trial_revision_loop.md) 追加 [docs/trial-revision-log.md](docs/trial-revision-log.md)，再修改 skill。

## 快速使用

在 Codex 中打开目标软件项目，或说明只有软件方向但还没有项目，然后说：

```text
使用 software-CP-CCH 为这个项目做软著申请材料
```

如果目标项目已经存在，可先运行：

```bash
python tools/project_audit.py --project <项目路径> --out-dir 软件著作权申请资料/analysis
```

随后按 `SKILL.md` 的主流程逐步推进。

Word 最终交付阶段可运行：

```bash
python tools/word_material_builder.py --workdir 软件著作权申请资料
```

如有代理提供的样本文档或模板，使用 `--template-dir <样本文档目录>`，生成后查看 `正式资料/word/word_generation_report.md`。

## 分发给其他 Codex 用户

把整个 `software-CP-CCH` 目录打包发给对方，而不是只发 `SKILL.md`。接收方解压到：

```text
C:\Users\<用户名>\.codex\skills\software-CP-CCH
```

然后新开 Codex 线程，使用：

```text
[$software-CP-CCH](C:\Users\<用户名>\.codex\skills\software-CP-CCH\SKILL.md) 帮我做软著材料
```

详细步骤见 [INSTALL.md](INSTALL.md)。
