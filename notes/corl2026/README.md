# CoRL 2026 论文精读交付

整理日期：2026-11-17。

- 已完成十六篇 PDF 正文与所附附录精读，并制作独立 HTML：WB-WAM、Long-WAM、PanTact、Workhorse、OCLO、HULK、ECoMEM、MemJEPA、SimpleARM、EmbodiedSWE、BATCH、RoSHI、CARD、FORCA、Gated Memory Policy、Blind Dexterity。原有新增四篇分别为 21、23、32、61 页。
- 按用户指定的世界模型、Agentic、Memory、人形与接触控制五方向组织；另接入既有 AW-0 精读，共十七个阅读入口。AW-0 本次只核验 Workshop 归属，没有重复全文精读。
- 新增三篇记忆论文来自 Memory Workshop 官方非归档论文列表；EmbodiedSWE 与 AW-0 为 Agentic Robotics Workshop Best Paper。Workshop 论文身份不等同于主会录用。
- 四篇接触控制论文为 Workshop Spotlight。WB-WAM 的 TAG Workshop Oral 归属沿用既有笔记核验，本次 OpenReview 遇验证码未复核；Long-WAM 的会议归属未核实。
- 主会另按官方 OpenReview 链接去重收录 687 篇。21 Oral、72 Spotlight、其余 594 为仅 Poster，全部 687 均列于海报名单。此目录没有逐篇摘要，不能标为已精读。

## 阅读入口

- [Notion 专题](https://app.notion.com/p/41bbb2b96e9d816ba5c7c52aa669dc53)
- [论文网站 · CoRL 阅读室](https://www.siyuanluoembodied.xin/papers/corl2026.html)
- [论文网站 · 后续 Workshop 与候选](https://www.siyuanluoembodied.xin/papers/corl2026-workshops.html)
- [本地阅读室](../../papers/corl2026.html)
- [主会目录](../../papers/corl2026-catalog.html)
- `reading/`：十六篇 Markdown 源；`exports/`：内嵌原图的独立 HTML 与已计算区间的 Markdown。
- `notion-publication.json`：Notion 页与最终附件的对应关系。Notion 中早期附件保留并明确标注，优先使用“最终版”。连接器无法直接替换已有文件块，本次没有删除原笔记。
- `focus-publication.json`：新增四篇的页面与附件记录；`focus-created-pages.json`：四篇及既有 AW-0 的 ID；`focus-notion-create.json` 与 `focus-collection-update.json` 保存写入内容。

## 内容标准

每篇首段简短说明，随后包含问题、思路、方法、实验、反例与一周计划、口述版。事实、阅读者推断和待验证假设分开。包括数据谱系、一个公式算例、仿真/OOD/真机三表、计数可用时的 Wilson 95% 区间、原文位置和预算边界。

论文图从本地 PDF 直接以 300–650 DPI 裁出，共二十四幅均检查过图与 caption，短边至少 800 px。原始 PDF 保留在 `pdfs/corl2026/`；本次未审核代码，不将原文未报告的字段补成事实。EmbodiedSWE 独立 HTML 使用同分辨率、质量 92 的 JPEG 副本，约 3.6 MB；站点与原图仍保留 PNG。

## 构建

`scripts/corl2026/build.py` 使用 PyMuPDF 与 markdown-it-py。当前机器运行：

```sh
/opt/homebrew/bin/python3 scripts/corl2026/build.py
```

脚本优先复用本机 uv 缓存包；其他机器需先安装对应依赖。所有页面 CSS/JS 内联；普通站点页引用项目原图，独立导出将图片嵌入 HTML。没有 CDN、远程字体、外部 JS 或正文懒加载依赖。基础正文与表格在禁用 JavaScript 时仍可读。

## 已做的交付检查

- 十个论文页、阅读室和 687 项目录：本地引用与章节锚点均可解析，无未替换的区间占位符。
- 1280 px 桌面及 390 px 手机布局；页面无横向溢出，宽表在容器内滚动，手机目录折叠。
- 深浅主题、逐步导读上一/下一步、理解题正确答案反馈。
- 目录搜索（humanoid 68 项）与 Oral 筛选（21 项），按官方场次识别展示类型。
- 独立 HULK HTML 经 `file://` 打开，无远程图/脚本/样式依赖；原图页内放大、Esc 关闭和焦点返回已实测。
- 移除所有脚本后，9 个二级标题、5 张表、四步流程与可展开答案仍在 DOM。
- HULK A4 打印产出 6 页；首屏视觉检查通过，PDF 文本包含口述版、计数、区间与展开答案。
- 新增四篇分别检查 390 px 布局与离线资源；EmbodiedSWE 检查桌面、深色主题、逐步导读、测验、放大/关闭/焦点返回。A4 打印 8 页，文本含末尾章节与展开答案。

## 新增四篇的关键边界

- ECoMEM 的真机合计为 68/79；按任务平均与合并次数结果不同。Writer 感知工程、真机全参数微调、初始化开销均单独记录。
- MemJEPA 仅有仿真证据。移动遮挡与长时间隐藏的失败、开环基线、隐藏外物尚未测试等附录结果已纳入。
- SimpleARM 的免训练只针对新增层；底座此前经过微调。计数任务平均更差，StopCube 为 0/150，没有真机实验。
- EmbodiedSWE 固定采用 arXiv v2，未混入项目页不同版本的规模数字。完整拆灯为 2/10，部分得分、分阶段成功与完整成功分开；模型检查点按真机表现选择，不能视作独立盲测。

上一轮已从隔离检出发布到现有论文网站，当时首页最近更新与全站搜索接入 CoRL：13 个入口由十篇论文、阅读室、主会目录和 Workshop 选题页组成；全站目录为 147 个页面。保留原工作区其他未提交修改，没有将 Notion 写入载荷或上传记录放入发布提交。

网站交付补充检查：复用主站主题偏好；390 / 768 / 1280 px 布局；十篇各有五段中文章节导读与四格证据总览；逐步导读 Home / End 与方向键、禁用按钮焦点恢复；深色主题打印使用浅色背景。隔离检出重建生成页面与提交一致。

## 本轮九篇 Workshop 处理结果

- 六篇全文精读完成，共85个PDF页；版本、页数、SHA-256、公开来源与三篇待全文原因见 `workshop-reading-manifest.json`。
- VETO未找到可读全文；UMI控制器选择与Beyond Fixed Delays的OpenReview PDF返回403。只保留官方元信息，不写推测的方法/性能总结。
- 六页各有开头简述、五段中文导读、数据谱系、公式微例、三类评测协议表、原图、四步导读、理解题、一周实验建议与口述版。CARD的模型权限、数据源及评分冲突逐项保留。
- 本轮网站总计16篇精读加既有AW-0；首页19个CoRL入口，全站153个页面。Notion发布记录仍对应此前十篇，本轮六篇交付在论文网站及本地独立HTML。
- 六页390px无横向页面溢出、原图加载正常；CARD另测1280/768px、深色、键盘Home/End、测验与图片Esc返回焦点，A4打印7页且包含末尾来源与答案。移除GMP全部脚本后正文、5张表、4步流程、原图及答案仍可用。
- 19个CoRL站点页的本地链接、章节锚点及内联JS语法通过检查；9幅新增原图均直接从PDF高DPI裁剪，短边至少800px。
