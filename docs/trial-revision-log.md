# software-CP-CCH 试用修订记录

本文件记录 skill/agent 在真实试用中的成长轨迹。案件材料修订写入案件目录；只有影响本 skill 规则、提示词、脚本或安装方式的反馈写入这里。

## 2026-06-09 初始化试用修订协议

- 试用场景或案件阶段：安装前准备。
- 用户原始反馈摘要：用户希望在试用过程中进行多轮修订，并认为修订记录对 skill/agent 成型很重要，要求安装前先沉淀这条建议。
- 观察到的问题：原 skill 已有案件迭代和补正记录，但缺少专门记录 agent 自身试用反馈、修订决策、验证与回归场景的协议。
- 影响范围：`SKILL.md`、`prompts/trial_revision_loop.md`、`tools/revision_log.py`、`docs/trial-revision-log.md`、`README.md`。
- 修订决策：新增“试用修订”路线和门禁，区分案件材料修订与 skill/agent 自身修订；skill 自身修订必须先记录再修改。
- 改动文件：`SKILL.md`、`README.md`、`prompts/trial_revision_loop.md`、`docs/trial-revision-log.md`、`tools/revision_log.py`。
- 验证方式和结果：`python -m py_compile tools\\project_audit.py tools\\source_extract.py tools\\confirm_stage.py tools\\material_check.py tools\\revision_log.py` 通过；`rg` 确认入口、README、prompt、日志和脚本均包含试用修订路线。
- 回归场景：用户在试用中反馈“这个流程不合理”“这个 prompt 不够好”“脚本输出不符合代理口径”时，agent 应先追加试用修订记录，再改 skill。
- 未决问题：后续可根据试用密度决定是否按日期拆分 `docs/trial-revisions/`。
## 2026-06-09 11:51:53 试用反馈

- 用户反馈摘要：用户反馈 software-CP-CCH 工作流不够彻底，最终应提供格式正确的 Word 三件套；需吸收本地 ruanzhu skill 与代理样本文档经验，避免申请表表格填错单元格。
- 影响范围：未归类
- 修订决策：新增 Word 最终交付阶段：基于样本文档/模板生成申请表、源代码、操作说明书 DOCX；要求模板定位、写后回读、截图数量、源码页数、渲染视觉 QA 与待确认字段标识。
- 改动文件：SKILL.md,README.md,requirements.txt,prompts/word_final_builder.md,references/templates.md,references/word_delivery_rules.md,tools/word_material_builder.py
- 验证方式和结果：`py_compile` 通过 `material_check.py` 与 `word_material_builder.py`；已为一个真实试用案件生成 Word 三件套；申请表关键字段回读通过；DOCX 结构检查未发现代理样本值残留；`material_check.py` 返回 WARN，警告来自用户待确认字段和确认记录；尝试 DOCX 渲染时本机缺少 LibreOffice/`soffice`，已记录结构 QA fallback。
- 回归场景：有代理样本模板时，申请表不得填错合并单元格；没有 Word 三件套时，交付自检应提示缺失；源码不足阈值时应全量提交并提示真实行数，不得伪造代码页数；说明书截图不足 7 张时应给出警告。
- 未决问题：如后续安装 LibreOffice，应补一次 PNG 视觉渲染回归。
## 2026-06-09 12:09:30 试用反馈

- 用户反馈摘要：用户强调 Word 生成不是可选增强，而是 software-CP-CCH 工作流完整性的基本要求。
- 影响范围：未归类
- 修订决策：将 Word 三件套明确沉淀为主流程必经阶段，并同步 PRD、申请表、源码材料、操作说明书和交付自检 prompt，规定 Markdown 仅为过程稿。
- 改动文件：SKILL.md,docs/PRD.md,prompts/application_fields.md,prompts/manual_builder.md,prompts/source_material_builder.md,prompts/word_final_builder.md,prompts/delivery_self_check.md,tools/word_material_builder.py,tools/material_check.py
- 验证方式和结果：rg 检查流程文档包含 Word 三件套；py_compile 检查新增/修改脚本；生成可分享 zip 包前排除本机绝对路径。
- 回归场景：待补充
- 未决问题：无
