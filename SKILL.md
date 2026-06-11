---
name: software-CP-CCH
description: "中国计算机软件著作权申请全流程 agent：从已有软件扫描、真实性/权属/AI辅助开发审计、材料生成，到必要时协助定义并开发最低可申请软件。Use when users mention 软著、软件著作权、计算机软件著作权登记、软著申请材料、源代码鉴别材料、操作手册、软件说明书、AI生成软件申请、软著补正。"
version: "0.1.0"
user-invocable: true
argument-hint: "[可选：项目路径、软件名称、申请阶段或补正意见]"
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, WebSearch
---

# 软件著作权申请全流程

本技能面向中国计算机软件著作权登记材料准备。它不是“文档堆料器”，而是按证据链推进：软件真实存在、申请主体有权、源码可回溯、功能说明可验证、材料口径一致、AI 辅助开发有人工组织与修改记录。

软著登记主管线是国家版权局 / 中国版权保护中心；不要把专利审查的新颖性、创造性标准硬套到软著。软著重点是程序和文档的表达、独立开发、权属与鉴别材料合规。本技能不替代律师、代理机构或官方系统要求。

## 路由

- **已有软件申请**：用户已有项目、源码、说明文档、截图或补正意见。
- **先开发再申请**：用户只有方向，需要先沟通确定一个真实、可运行、有最低材料支撑的软件，再生成软著材料。
- **迭代/补正**：用户已有草稿、退回意见、代理反馈或上一轮输出，优先按迭代流程处理，不要默认从头重跑。
- **试用修订**：用户在试用本 skill/agent 时指出流程、提示词、脚本、质量门槛或输出体验问题，先 `Read prompts/trial_revision_loop.md`，记录后再改 skill。

## 主流程

1. `Read prompts/intake.md`：确认路线、申请主体、项目输入、是否已有软件。
2. 如无软件，`Read prompts/software_ideation_mvp.md`：收敛可申请 MVP，开发前设质量门槛。
3. `Read prompts/project_scan.md`：扫描源码、文档、截图和运行证据；可运行 `tools/project_audit.py`。
4. `Read prompts/rights_ai_audit.md`：检查独立开发、权属、开源依赖、AI 辅助开发和敏感信息风险。
5. `Read prompts/business_understanding.md`：形成业务理解和申请口径；必要时做外部行业调研，但不能编造项目不存在的功能。
6. `Read prompts/code_evidence_selection.md`：选择可回溯源码，生成并确认代码抽取清单。
7. `Read prompts/application_fields.md`：整理申请表填报辅助信息。
8. `Read prompts/manual_builder.md`：生成操作手册/说明书草稿，插入真实截图或可见占位。
9. `Read prompts/source_material_builder.md`：生成源程序鉴别材料；可运行 `tools/source_extract.py`。
10. `Read prompts/word_final_builder.md`：生成最终 Word 三件套：申请表、源程序鉴别材料、操作说明书；如用户提供代理认可或历史已通过的三件套目录，必须优先用 `tools/word_material_builder.py --reference-word-dir <参考word目录>` 复制母版并回填本案字段，再做表格回读、截图和版式核验。
11. `Read prompts/delivery_self_check.md`：三轮自检；可运行 `tools/material_check.py`。正式交付前必须同时检查 Markdown 草稿和 Word 文件。
12. 如用户反馈的是 skill/agent 自身改进，`Read prompts/trial_revision_loop.md`：追加试用修订记录；可运行 `tools/revision_log.py`。

## 输出目录

默认在当前项目或用户指定目录下创建：

```text
软件著作权申请资料/
├── analysis/
├── 草稿/
├── 截图/
├── 正式资料/
│   ├── word/
│   └── qa/
└── 交付自检记录.md
```

正式交付文件需保留历史版本，不要默认覆盖旧稿。推荐文件名包含软件名、版本号和本地时间戳。

## 硬门禁

- **权属门禁**：申请主体、开发者、委托/合作/职务开发、开源许可和第三方素材未澄清前，不得输出“可直接提交”的结论。
- **真实性门禁**：源代码材料必须来自真实项目或本轮实际开发项目；禁止 AI 编造“源代码鉴别材料”。
- **AI 辅助门禁**：AI 参与开发时，必须记录人工需求定义、选择、修改、整合、测试和责任承担证据；不得伪称全人工开发。
- **代码质量门禁**：若软件尚未开发，必须先完成可运行、可截图、可解释、可测试的最小软件；禁止为凑页数生成低质冗余代码。
- **一致性门禁**：软件全称、简称、版本号、著作权人、日期、页眉、手册标题、申请表辅助信息必须一致。
- **Word 交付门禁**：最终不能只交 Markdown。申请表、源程序鉴别材料、操作说明书必须生成 `.docx`；申请表模板填充要按标签/合并单元格定位并写后回读，不能盲填坐标；源代码页数/行数必须来自真实源码；操作说明书截图必须真实、完整、清晰。
- **Word 母版门禁**：用户指定参考 Word 三件套时，不得自行退化生成简化申请表或任意改写版式。应复制参考申请表母版，按标签/合并单元格回填；操作说明书要对齐参考标题风格、截图数量和填报口径。过程版目录可保留，但默认 `正式资料/word` 必须指向最终对标版。
- **编码与乱码门禁**：所有中文草稿、生成脚本、QA 脚本和 Word 生成过程必须使用 UTF-8 或显式编码回退读取；不得通过 PowerShell 管道/here-string 直接执行含大量中文常量的临时脚本来生成 DOCX。最终 `.docx` 必须检查连续问号、替换字符、中文字符数量异常和页眉页脚乱码；一旦出现 `???`、`�` 或正文中文明显丢失，交付结论必须为 FAIL。
- **跨项目残留门禁**：通用生成器不得保留某一历史项目的专用技术术语、模型、输出字段或截图关键词作为默认正文。申请表“主要功能、技术特点、开发目的”和操作说明书正文必须优先来自本项目业务理解、操作手册和真实源码证据；缺省文本只能使用通用业务处理表述。
- **用户确认门禁**：业务理解、申请字段、代码选择、截图方式、Markdown 草稿进入正式资料前都应停下让用户确认。
- **试用修订门禁**：不得把一次试用反馈直接改成隐形规则；先记录触发场景、问题、决策、改动文件、验证结果和待回归场景，再更新 skill。

## 参考资料

- 法规和官方规则：`references/legal_sources.md`
- 质量与反低质 AI 规则：`references/quality_rules.md`
- 字段、清单和文档模板：`references/templates.md`
- Word 三件套交付规则：`references/word_delivery_rules.md`
- 外部项目调研摘记：`references/external_research_notes.md`
- 试用修订沉淀规则：`prompts/trial_revision_loop.md`
