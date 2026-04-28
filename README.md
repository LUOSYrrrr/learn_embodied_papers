# learn_embodied_papers · 具身智能学习笔记

面向具身智能（Embodied AI）方向的个人学习记录，不限于论文精读——也包含**源码精读**、**数据流 / Pipeline 剖析**、工程实践、认知科学背景。
每篇笔记聚焦：核心贡献 / 设计、架构拆解、关键公式或代码、与研究 / 工程实践的联系。

**[→ 在线访问](https://www.siyuanluoembodied.xin/)**

---

## 已收录（9 篇）

### 📄 论文精读

| 论文 | 方向 | 状态 |
|------|------|------|
| [A Path Towards Autonomous Machine Intelligence](papers/lecun-autonomous-intelligence.html) · LeCun (2022) | 世界模型 / JEPA | ✅ 完成 |
| [I-JEPA · Self-Supervised Learning from Images](papers/ijepa-self-supervised.html) · Assran et al. (2023) | JEPA / 自监督 | ✅ 完成 |
| [π₀: A Vision-Language-Action Flow Model](papers/pi0-vla-flow-model.html) · Black et al. (2024) | VLA / Flow Matching | ✅ 完成 |
| [π₀.₅: Open-World Generalization](papers/pi05-open-world.html) · Black et al. (2025) | VLA / Open-World | ✅ 完成 |
| [π*₀.₆: RECAP · Learns from Experience](papers/pi06-recap-rl.html) · Physical Intelligence (2025) | VLA / RL | ✅ 完成 |
| [π₀.₇: Steerable Generalist](papers/pi07-steerable-generalist.html) · Physical Intelligence (2026) | VLA / Steerable / Cross-Embodiment | ✅ 完成 |
| [婴儿认知发育时间线](papers/infant-cognition-timeline.html) · Dupoux | 认知科学背景 | ✅ 完成 |

### 🔧 源码 / Pipeline 精读

| 笔记 | 对应 | 焦点 | 状态 |
|------|------|------|------|
| [π₀ / π₀.5 代码阅读笔记](papers/pi0-code-reading.html) | [openpi](https://github.com/Physical-Intelligence/openpi) · `pi0_pytorch.py` | 模型前向 / 训练 / 推理 | ✅ 完成 |
| [π₀ 数据 Pipeline · Transform 设计](papers/pi0-data-pipeline.html) | openpi · `data_loader.py` + `transforms.py` | 数据流 / transform 链 | ✅ 完成 |

---

## 内容组织方式

每条方向按 "① 开山 / 主模型 → ② 横向扩展 / 基础组件 → ③ 改进 / 延伸" 三层组织。当前覆盖六个方向：

- **世界模型 · JEPA 路线**（LeCun 2022 → I-JEPA → V-JEPA / V-JEPA 2 / LeWorldModel ···）
- **VLA · 视觉-语言-动作**（π₀ → π₀.₅ → π*₀.₆ → π₀.₇ / OpenVLA，配套 Flow Matching / PaliGemma）
- **生成式基础 · 从 VAE 到 Flow**（VAE → DDPM → Score SDE → Flow Matching）
- **控制 · Policy & Planning**（Diffusion Policy / ACT / TD-MPC2）
- **WAM · 世界-动作模型**（SuSIE / UniPi / Dreamer v1-v3 / Genie / RT-1 / RT-2）
- **认知科学 · 参考背景**（婴儿认知发育 / Core Knowledge / IntPhys）

详细清单及阅读状态见 [首页](https://www.siyuanluoembodied.xin/) "By Direction" 栏。

---

## 笔记页的两种模式

为了兼顾 "交互富 / 可视化强" 和 "长文写作、后续好改"，笔记页分两种写法：

### 模式 A · 手写 HTML（交互富）

论文精读页走这条路。页面里嵌有：

- SVG 交互图（hotspot、step walker）
- 内嵌的 Tab 切换、可折叠原文引用
- Quiz / Mermaid 流程图

代表：[pi0-vla-flow-model.html](papers/pi0-vla-flow-model.html)、[lecun-autonomous-intelligence.html](papers/lecun-autonomous-intelligence.html)。
新开页从 `papers/_template.html` 复制。

### 模式 B · Markdown + marked.js 客户端渲染（长文）

源码精读 / Pipeline 剖析走这条路。页面是一个极薄的 HTML 壳：

```text
papers/pi0-data-pipeline.html     ← HTML 壳（head + marked + highlight.js + mermaid）
      └─ fetch('../notes/pi0-data-pipeline.md')   ← 读源 MD
      └─ marked.parse()                           ← 客户端渲染
      └─ renderMermaid()                          ← 把 ```mermaid 块转 SVG
      └─ 自动按 h2/h3 生成左侧目录

notes/pi0-data-pipeline.md         ← 真正的内容源
```

好处：

- 长笔记直接写 MD，VSCode 里带实时预览，写作心智负担小
- 可以用 `mermaid` 代码块画流程图（HTML 壳里有 Mermaid.js + 主题联动）
- 代码块走 `highlight.js` 自动高亮
- 改内容只改 MD，不碰 HTML；HTML 壳可跨页面复用

复用这个模式的方法：复制一份现有 `pi0-*.html`，改 title / 面包屑 / `fetch(...)` 路径。

---

## 项目结构

```text
learn_embodied_papers/
├── index.html                          # 首页导航（Recent + 按方向浏览）
├── assets/
│   ├── css/style.css                   # 共享样式（深色 / 浅色主题）
│   └── js/
│       ├── theme.js                    # 主题切换
│       └── interactive.js              # Step walker / Hotspot / Quiz
├── papers/                             # 渲染页（HTML）
│   ├── _template.html                  # 新论文页模板（模式 A）
│   ├── lecun-autonomous-intelligence.html   # 模式 A · 世界模型
│   ├── ijepa-self-supervised.html           # 模式 A · JEPA
│   ├── pi0-vla-flow-model.html              # 模式 A · VLA
│   ├── pi05-open-world.html                 # 模式 A · VLA
│   ├── pi06-recap-rl.html                   # 模式 A · VLA + RL
│   ├── pi07-steerable-generalist.html       # 模式 A · VLA + Steerable
│   ├── infant-cognition-timeline.html       # 模式 A · 认知科学
│   ├── pi0-code-reading.html                # 模式 B（壳 + marked）
│   └── pi0-data-pipeline.html               # 模式 B（壳 + marked + mermaid）
├── notes/                              # 源笔记（Markdown，模式 B 的内容源）
│   ├── pi0-code-reading.md
│   └── pi0-data-pipeline.md
├── CLAUDE.md                           # AI 上下文（新对话时贴给 Claude）
└── README.md
```

---

## 待读清单 · Reading List

按推荐阅读顺序排列，📄 = 已下载 PDF。

### 第一优先：生成式基础（理解 π₀ 的 flow matching）

| # | 论文 | PDF 路径 | 一句话 |
|---|------|---------|--------|
| 1 | **Diffusion Policy** · Chi et al. 2024 | 📄 `pdfs/world-model/WAM/Chi 等 - 2024 - Diffusion Policy...pdf` | π₀ action expert 的前身，DDPM 做机器人策略 |
| 2 | VAE · Kingma & Welling 2014 | 待下载 | latent space + reparameterization，Dreamer 的基础 |
| 3 | DDPM · Ho et al. 2020 | 待下载 | 前向加噪→反向去噪，Diffusion Policy 的基础 |
| 4 | Flow Matching · Lipman et al. 2023 | 待下载 | ODE 直线路径替代 SDE，π₀ 的核心 |
| 5 | Score SDE · Song et al. 2021 | 待下载（或读博客替代） | 统一 DDPM 为连续 SDE，DDPM→Flow 的桥梁 |

### 第二优先：WAM · 世界-动作模型

| # | 论文 | PDF 路径 | 一句话 |
|---|------|---------|--------|
| 6 | **SuSIE** · Black et al. 2023 | 待下载 | 图编辑模型生成 subgoal，π₀.₇ world model 的直接来源 |
| 7 | **RT-1** · Brohan et al. 2023 | 📄 `pdfs/world-model/WAM/Brohan 等 - 2023 - RT-1...pdf` | VLA 鼻祖，Robotics Transformer |
| 8 | **RT-2** · Brohan et al. 2023 | 📄 `pdfs/world-model/WAM/Brohan 等 - 2023 - RT-2...pdf` | VLM 当策略，π₀ 的直接前身 |
| 9 | **Genie** · Bruce et al. 2024 | 📄 `pdfs/world-model/WAM/Bruce 等 - 2024 - Genie...pdf` | 从单张图生成可交互环境 |

### 第三优先：Dreamer 系列（latent world model）

| # | 论文 | PDF 路径 | 一句话 |
|---|------|---------|--------|
| 10 | World Models · Ha & Schmidhuber 2018 | 📄 `pdfs/world-model/Ha和Schmidhuber - 2018 - World Models.pdf` | VAE+RNN 开山之作 |
| 11 | PlaNet / RSSM · Hafner 2019 | 📄 `pdfs/world-model/Hafner 等 - 2019 - Learning Latent Dynamics...pdf` | Latent dynamics for planning |
| 12 | Dreamer v1 · Hafner 2020 | 📄 `pdfs/world-model/dreamer/Hafner 等 - 2020 - Dream to Control...pdf` | 从 latent 想象中学策略 |
| 13 | Dreamer v2 · Hafner 2022 | 📄 `pdfs/world-model/dreamer/Hafner 等 - 2022 - Mastering Atari...pdf` | 离散表征 + Atari |
| 14 | Dreamer v3 · Hafner 2024 | 📄 `pdfs/world-model/dreamer/Hafner 等 - 2024 - Mastering Diverse Domains...pdf` | 跨域通用世界模型 |

### 第四优先：JEPA 延续（已有基础）

| # | 论文 | PDF 路径 | 一句话 |
|---|------|---------|--------|
| 15 | V-JEPA · Bardes et al. 2024 | 📄 `pdfs/world-model/Bardes 等 - 2024 - Revisiting Feature Prediction...pdf` | JEPA 从图片到视频 |
| 16 | V-JEPA 2 · Assran et al. 2025 | 📄 `pdfs/world-model/Assran 等 - 2025 - V-JEPA 2...pdf` | 加上规划能力 |
| 17 | V-JEPA 2.1 · Mur-Labadia et al. 2026 | 📄 `pdfs/world-model/Mur-Labadia 等 - 2026 - V-JEPA 2.1...pdf` | Dense feature 改进 |
| 18 | LeWorldModel · Maes et al. 2026 | 📄 `pdfs/world-model/Maes 等 - 2026 - LeWorldModel...pdf` | 端到端 pixel→action JEPA |

---

## 本地运行

客户端 `fetch('../notes/*.md')` 不能走 `file://`，必须用 HTTP server：

```bash
# Python
python -m http.server 8000

# Node.js
npx serve .
```

然后浏览器打开 `http://localhost:8000`。

---

## 部署到 GitHub Pages

1. 推送到 GitHub 仓库
2. Settings → Pages → Source 选 `main` 分支 `/` (root)
3. 几分钟后通过 `https://<username>.github.io/learn_embodied_papers/` 访问

---

## 写作规范

- 中文正文 + 英文术语对照（首次出现时加括号）
- 核心公式 / 架构要有直观类比
- 每篇尽量有 "与 VLA / Embodied AI 的联系" 一节
- 图优先级：SVG 交互图 > Mermaid > ASCII 图 > 纯文字描述
- 源码引用走 markdown 链接；Mermaid 主题随站点主题切换
- Callout 颜色语义：绿 = 核心结论，amber = 注意 / 提示，red = 批评 / 局限，blue = 类比 / 联系，purple = 对应 VLA

---

## 贡献

欢迎通过 Issues 指出错误，或 PR 补充新的笔记（论文、代码精读、数据流剖析等形式均可）。

## License

MIT
