# Step 5 代码证据选择

## 目标

选择最能体现软件功能和运行逻辑的真实源码，生成源程序鉴别材料。代码选择要可解释、可回溯、可确认。

## 选择原则

- 优先入口、路由、页面、核心组件、业务服务、数据处理、状态管理、导出/报表、权限和配置逻辑。
- 不抽取 `node_modules`、构建产物、压缩文件、minified 文件、lock 文件、图片、字体、自动生成文件。
- 可抽取指定行段，但必须连续并记录原因。
- 不改写源码，不用 AI 补齐代码，不把伪代码当源代码。
- 小项目不足 60 页时提交全部可用源程序；不要为了凑页制造无意义代码。

## 选择清单格式

在 `草稿/代码文件选择.json` 写入：

```json
{
  "software_name": "待确认软件全称",
  "version": "V1.0",
  "files": [
    {
      "path": "src/main.ts",
      "selected": true,
      "start_line": 1,
      "end_line": null,
      "model_reason": "入口文件，体现软件启动和模块挂载逻辑"
    }
  ]
}
```

## 用户确认

生成选择清单后停止，让用户确认或修改。确认后运行：

```bash
python tools/confirm_stage.py --workdir 软件著作权申请资料 --stage code-selection --note "<用户确认内容>"
```

## 生成代码材料

确认后运行：

```bash
python tools/source_extract.py --project <项目路径> --selection 软件著作权申请资料/草稿/代码文件选择.json --software-name "<软件全称>" --version "<版本号>" --out-dir 软件著作权申请资料/草稿
```

输出：

- `代码-前30页.md` 与 `代码-后30页.md`，或 `代码-全部.md`
- `代码提取清单.md/json`

