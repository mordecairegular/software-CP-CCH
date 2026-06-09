# 模板与数据结构

## 输出目录

```text
软件著作权申请资料/
├── analysis/
│   ├── project_audit.md
│   └── project_audit.json
├── 草稿/
│   ├── 业务理解.md
│   ├── 业务理解.json
│   ├── 权属与AI辅助审计.md
│   ├── 申请表信息.md
│   ├── 代码文件选择.json
│   ├── 代码提取清单.md
│   ├── 代码提取清单.json
│   ├── 代码-前30页.md
│   ├── 代码-后30页.md
│   ├── 操作手册.md
│   └── 操作手册自检记录.md
├── 截图/
├── 正式资料/
│   ├── word/
│   │   ├── 01 计算机软件著作权登记申请表 — <软件全称><版本号>.docx
│   │   ├── 02 软件源代码 — <软件简称或英文名> <版本号>.docx
│   │   ├── 03 <软件全称><版本号> 操作说明书.docx
│   │   └── word_generation_report.md
│   └── qa/
└── 交付自检记录.md
```

## 业务理解 JSON

```json
{
  "software_name": "软件全称",
  "version": "V1.0",
  "product_positioning": "",
  "industry": "",
  "target_users": [],
  "business_objects": [],
  "core_value": "",
  "main_functions": [
    {
      "name": "",
      "purpose": "",
      "user_action": "",
      "system_feedback": "",
      "evidence": []
    }
  ],
  "operation_flow": [],
  "technical_characteristics": [],
  "manual_sections": [],
  "pending_user_confirmations": []
}
```

## 代码选择 JSON

```json
{
  "software_name": "软件全称",
  "version": "V1.0",
  "files": [
    {
      "path": "src/main.ts",
      "selected": true,
      "start_line": 1,
      "end_line": null,
      "model_reason": "入口文件，体现软件启动逻辑"
    }
  ]
}
```

## 申请表信息

```text
➤软件全称：
➤软件简称：
➤版本号：
➤著作权人：
➤开发完成日期：
➤首次发表日期：
➤权利取得方式：
➤开发方式：
➤开发硬件环境：
➤运行硬件环境：
➤开发操作系统：
➤运行平台/操作系统：
➤软件开发环境/开发工具：
➤软件运行支撑环境/支持软件：
➤编程语言：
➤源程序量：
➤软件分类：
➤开发目的：
➤主要功能：
➤技术特点：
➤AI辅助开发说明：
```

## 自检记录

```text
# 交付自检记录

- 案件：
- 软件：
- 版本：
- 时间：
- 结论：PASS / WARN / FAIL

## 完整性

## 真实性

## 一致性

## 待补充
```
