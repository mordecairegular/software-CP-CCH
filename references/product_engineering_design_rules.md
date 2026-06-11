# 工程实践与 UI 设计规则

## 公开资料吸收

本 skill 使用公开可查的通用经验作为质量约束，但不把它们机械套成形式主义清单：

- IEEE/ISO/IEC 29148 强调需求工程要贯穿软件生命周期，要求需求具备可理解、可管理、可追踪的特征。落到软著场景，就是候选软件必须说清用户任务、输入输出、约束和证据来源。
- SWEBOK 将软件需求、设计、构造、测试、维护等作为软件工程知识域。落到软著场景，就是不能只有“能运行的脚本”，还要有结构、测试、说明、版本和维护线索。
- NIST SSDF 强调把安全开发实践纳入 SDLC。落到软著场景，就是扫描密钥、样例数据、第三方依赖和 AI 辅助开发证据，避免材料提交前暴露风险。
- WCAG 2.2 的四个基础原则是可感知、可操作、可理解、健壮。落到软著截图和说明书，就是界面文字、状态、控件和错误反馈要让普通用户看得懂、用得动。
- Nielsen Norman Group 的可用性启发式强调系统状态、真实世界语言、一致性、错误预防、审美与极简、帮助文档等。落到本 skill，就是 UI 不是“摆控件”，而要支撑真实任务。
- Material Design、Apple HIG、Microsoft Fluent 等成熟设计系统的共同经验是：使用一致的组件、层级、间距、状态和反馈，减少用户学习成本。落到本 skill，就是优先复用成熟组件库，不手搓低质 UI。

参考链接：

- W3C WCAG 2.2: https://www.w3.org/TR/WCAG22/
- Nielsen Norman Group 10 Usability Heuristics: https://www.nngroup.com/articles/ten-usability-heuristics/
- Material Design 3: https://m3.material.io/
- Apple Human Interface Guidelines: https://developer.apple.com/design/human-interface-guidelines
- Microsoft Fluent 2: https://fluent2.microsoft.design/
- IEEE/ISO/IEC 29148-2018: https://standards.ieee.org/ieee/29148/6937/
- IEEE Computer Society SWEBOK: https://www.computer.org/education/bodies-of-knowledge/software-engineering
- NIST SSDF SP 800-218: https://csrc.nist.gov/pubs/sp/800/218/final

## 对本 skill 的落地规则

### 需求不清时不开发

必须先形成候选矩阵和推荐理由。候选不得只写“数据处理工具”“管理系统”，必须具体到业务对象和任务节点。

### 工程实践必须可映射

每个功能模块都要映射到至少一种工程实践价值：

- 数据质量检查。
- 格式转换和标准化。
- 规则计算或比对。
- 异常定位与整改建议。
- 结果导出、申报包生成或归档。
- 操作日志和复核证据。
- 批量处理与人工复核协作。

### UI 必须服务任务

UI 不能只证明“有窗口”。它要让截图直接回答：软件处理什么对象、用户做了什么、系统反馈什么、输出能用于哪里。

### 不造轮子

能用成熟库解决的基础问题不要手写：

- 表格、表单、弹窗、导航、图标、日期、上传、导出等，用组件库。
- 地图、图表、流程图、文档、Excel、PDF 等，用成熟库。
- 规则引擎、格式解析、坐标转换、CAD/GIS 处理等，优先使用行业常用库。

### 截图不是装饰

截图应覆盖真实流程：入口、导入/配置、处理、结果、异常/日志、导出。每张截图都要能进入操作说明书并支撑申请表功能描述。
