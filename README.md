# learn_embodied_papers · 具身智能学习笔记

面向具身智能（Embodied AI）方向的个人学习记录，不限于论文精读——也包含**源码精读**、**数据流 / Pipeline 剖析**、工程实践、认知科学背景。
每篇笔记聚焦：核心贡献 / 设计、架构拆解、关键公式或代码、与研究 / 工程实践的联系。

**[→ 在线访问](https://www.siyuanluoembodied.xin/)**

---

## 已收录（33 篇）· 按方向分类

### 🟣 VLA · 视觉-语言-动作（9 篇）

把 VLM 作为 backbone，直接从感知 + 指令映射到机器人动作。当前 embodied 主流路线。

| 笔记 | 来源 | 一句话 |
|------|------|--------|
| [π₀: A Vision-Language-Action Flow Model](papers/pi0-vla-flow-model.html) | Black et al. · PI · 2024 | PaliGemma + Action Expert，flow matching 输出 50 Hz 连续动作块 |
| [π₀.₅: Open-World Generalization](papers/pi05-open-world.html) | PI · 2025 | 分层推理（高层子任务 + 低层动作）+ 异构数据 co-training，进全新家庭 |
| [π*₀.₆: RECAP · Learns from Experience](papers/pi06-recap-rl.html) | PI · 2025-11 | RECAP：advantage conditioning 让 VLA 从自身经验做 RL 改进 |
| [π₀.₇: Steerable Generalist](papers/pi07-steerable-generalist.html) | PI · 2026 | 可实时语言引导的通用策略，跨本体（cross-embodiment） |
| [π₀ 系列训练指南](papers/pi-series-training-guide.html) | 综合笔记 | 预训练 / 后训练 / HITL 全流程详解 |
| [π₀ / π₀.5 代码阅读](papers/pi0-code-reading.html) | [openpi](https://github.com/Physical-Intelligence/openpi) · `pi0_pytorch.py` | 模型前向 / 训练 / 推理源码逐行 |
| [π₀ 数据 Pipeline · Transform 设计](papers/pi0-data-pipeline.html) | openpi · `transforms.py` | 7 层 transform 适配器链 + norm_stats 粘合，LIBERO/ALOHA/DROID 对照 |
| [OpenVLA](papers/openvla.html) | Kim et al. · 2024 | 7B 开源 VLA：Llama-2 + DINOv2/SigLIP，离散 action token |
| [RT-2](papers/rt2.html) | Google DeepMind · 2023 | VLM 直接输出动作 token，VLA 范式开创者 |

### 🦿 Loco-Manipulation · 移动操作（8 篇 + 1 附属）

边走边抓：腿 / 全身参与操作，扩大工作空间。分层 RL + Sim2Real 是主流路线。

| 笔记 | 来源 | 一句话 |
|------|------|--------|
| **腿足 Legged** | | |
| [DeepWBC · 统一全身策略](papers/deepwbc.html) | Fu et al. · CoRL 2022 | Advantage Mixing + ROA，legged loco-manip 全身 RL 的前身 |
| [VBC · 视觉全身控制](papers/vbc-loco-manipulation.html) | Liu et al. · CoRL 2024 | Unitree B1+Z1 · 19 DoF · 零真机数据的视觉全身控制 |
| **人形 Humanoid** | | |
| [VLK · Vision-Language-Kinematics](papers/vlk.html) | Wang et al. · 2026 | 重建场景合成交互，预测运动学而非动作，0 遥操作 · G1 |
| [OpenHLM](papers/openhlm.html) | Hu et al. · 2026 | 全身人形 loco-manip 经验配方：13 个受控实验 · π₀.₅ · G1 |
| [MotionWAM](papers/motionwam.html) | Zheng et al. · 2026 | 实时人形 loco-manipulation 世界-动作模型 |
| └ [MotionWAM 数据集分析](papers/datasets-analysis.html) | 附属笔记 | 训练数据构成拆解 |
| [SONIC](papers/sonic.html) | Luo et al. · NVIDIA · 2026 | 超大规模 motion tracking + 通用全身控制 |
| [Humanoid-GPT](papers/humanoid-gpt.html) | Qi et al. · 清华/Galbot · 2026 | GPT 式序列建模做 motion tracking，2B 帧 scaling law，与 SONIC 对照 |
| [Ψ₀](papers/psi0.html) | Wei et al. · USC/NVIDIA · 2026 | 解耦训练：800h 人类视频预训练 VLM + 30h 真机训 MM-DiT expert，超 GR00T 40%+ |

### 🌍 WAM · 世界-动作模型（8 篇）

世界模型生成 subgoal / 模拟未来，辅助策略学习。

| 笔记 | 来源 | 一句话 |
|------|------|--------|
| [Dreamer v1](papers/dreamer-v1.html) | Hafner et al. · ICLR 2020 | latent imagination：在潜空间想象 rollout 里学策略 |
| [Cosmos-Predict2.5](papers/cosmos-predict2.html) | NVIDIA · 2026-02 | Flow Matching DiT 视频世界模型，Sim2Real 数据增强 |
| [Cosmos 3](papers/cosmos3.html) | NVIDIA · 2026-06 | Omnimodal MoT，视频 + 动作统一生成 |
| [DreamDojo](papers/dreamdojo.html) | NVIDIA · 2026 | 44k 小时人类视频 + latent action 学世界模型 |
| [DiT4DiT](papers/dit4dit.html) | Ma et al. · 2026 | Video + Action 联合建模的实时 WAM |
| [Fast-WAM](papers/fast-wam.html) | Yuan et al. · 2026 | 190 ms 实时推理 · 无 embodied 预训练 · 受控消融 |
| [τ₀-WM](papers/tau0-wm.html) | Zhou et al. · 2026 | 统一视频-动作世界模型 · Test-Time Compute · 27K 小时 |
| [WAM-TTT](papers/wam-ttt.html) | Feng et al. · 北大/Galbot · 2026 | 测试时把人类演示写进 TTT 快权重，零标注 steering，46.2% vs ICL 7.1% |

### 🧊 世界模型 · JEPA 路线（2 篇）

LeCun 倡导的非生成式联合嵌入预测架构。

| 笔记 | 来源 | 一句话 |
|------|------|--------|
| [A Path Towards Autonomous Machine Intelligence](papers/lecun-autonomous-intelligence.html) | LeCun · 2022 | 六模块自主智能架构 + H-JEPA，世界模型路线蓝图 |
| [I-JEPA](papers/ijepa-self-supervised.html) | Assran et al. · Meta · 2023 | 图像 JEPA：latent 预测替代像素重建的自监督 |

### 🌀 生成式基础 · VAE 到 Flow（3 篇）

π₀ flow matching 的上游知识链。

| 笔记 | 来源 | 一句话 |
|------|------|--------|
| [DiT](papers/dit.html) | Peebles & Xie · 2023 | Transformer 替代 U-Net 做 diffusion backbone |
| [Flow Matching](papers/generation/flow-matching.html) | Lipman et al. · 2023 | ODE 直线路径替代 SDE，π₀ 动作生成的核心 |
| [Consistency Models](papers/consistency-models.html) | Song et al. · 2023 | 1-step 生成：蒸馏 / 独立训练两条路 |

### 🎛 控制 · Policy & Planning（1 篇）

| 笔记 | 来源 | 一句话 |
|------|------|--------|
| [Diffusion Policy](papers/diffusion-policy.html) | Chi et al. · IJRR 2024 | DDPM 做机器人策略，π₀ action expert 的前身 |

### 🧠 认知科学 · 参考背景（1 篇）

| 笔记 | 来源 | 一句话 |
|------|------|--------|
| [婴儿认知发育时间线](papers/infant-cognition-timeline.html) | Dupoux | 0–14 月认知能力时间线，对 embodied AI 数据/课程设计的启示 |

> 每条方向按 "① 开山 / 主模型 → ② 横向扩展 / 基础组件 → ③ 改进 / 延伸" 三层组织，
> 完整阅读路线图（含未读占位）见 [首页](https://www.siyuanluoembodied.xin/) "按方向浏览" 栏。

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
│   ├── js/                             # theme.js 主题切换 · interactive.js 交互组件
│   └── figures/<paper-slug>/           # 从 PDF 裁出的论文原图
├── papers/                             # 渲染页（HTML），30 篇见上方分类表
│   ├── _template.html                  # 新论文页模板（模式 A）
│   ├── *.html                          # 模式 A · 手写交互 HTML（大多数论文精读）
│   ├── pi0-code-reading.html 等        # 模式 B · 壳 + marked（源码/长文笔记）
│   └── generation/flow-matching.html   # 按方向的子目录（generation / world-model / ...）
├── notes/                              # 源笔记（Markdown，模式 B 的内容源）
├── pdfs/                               # 论文 PDF（按方向分目录，不进 git）
├── .claude/skills/                     # paper-to-html / zotero skill
├── CLAUDE.md                           # AI 上下文
└── README.md
```

---

## 待读清单 · Reading List

按推荐阅读顺序排列，📄 = 已有 PDF（本仓库或 Zotero）。

### 第一优先：人形 Loco-Manipulation / WAM 新论文（Zotero `loco-manipulation` collection 已入库）

| # | 论文 | 来源 | 一句话 |
|---|------|------|--------|
| 1 | **Being-M0.7** · BeingBeyond 2026 | [项目页](https://research.beingbeyond.com/being-m07) | 人形机器人 latent 世界-动作模型 |

### 第二优先：生成式基础（补完 π₀ 的 flow matching 知识链）

| # | 论文 | PDF 路径 | 一句话 |
|---|------|---------|--------|
| 4 | VAE · Kingma & Welling 2014 | 待下载 | latent space + reparameterization，Dreamer 的基础 |
| 5 | DDPM · Ho et al. 2020 | 待下载 | 前向加噪→反向去噪，Diffusion Policy 的基础 |
| 6 | Score SDE · Song et al. 2021 | 待下载（或读博客替代） | 统一 DDPM 为连续 SDE，DDPM→Flow 的桥梁 |

### 第三优先：WAM 补课

| # | 论文 | PDF 路径 | 一句话 |
|---|------|---------|--------|
| 7 | **SuSIE** · Black et al. 2023 | 待下载 | 图编辑模型生成 subgoal，π₀.₇ world model 的直接来源 |
| 8 | **RT-1** · Brohan et al. 2023 | 📄 `pdfs/world-model/WAM/Brohan 等 - 2023 - RT-1...pdf` | VLA 鼻祖，Robotics Transformer |
| 9 | **Genie** · Bruce et al. 2024 | 📄 `pdfs/world-model/WAM/Bruce 等 - 2024 - Genie...pdf` | 从单张图生成可交互环境 |

### 第四优先：Dreamer 系列（latent world model）

| # | 论文 | PDF 路径 | 一句话 |
|---|------|---------|--------|
| 10 | World Models · Ha & Schmidhuber 2018 | 📄 `pdfs/world-model/Ha和Schmidhuber - 2018 - World Models.pdf` | VAE+RNN 开山之作 |
| 11 | PlaNet / RSSM · Hafner 2019 | 📄 `pdfs/world-model/Hafner 等 - 2019 - Learning Latent Dynamics...pdf` | Latent dynamics for planning |
| 12 | Dreamer v2 · Hafner 2022 | 📄 `pdfs/world-model/dreamer/Hafner 等 - 2022 - Mastering Atari...pdf` | 离散表征 + Atari |
| 13 | Dreamer v3 · Hafner 2024 | 📄 `pdfs/world-model/dreamer/Hafner 等 - 2024 - Mastering Diverse Domains...pdf` | 跨域通用世界模型 |

### 第五优先：JEPA 延续（已有基础）

| # | 论文 | PDF 路径 | 一句话 |
|---|------|---------|--------|
| 14 | V-JEPA · Bardes et al. 2024 | 📄 `pdfs/world-model/Bardes 等 - 2024 - Revisiting Feature Prediction...pdf` | JEPA 从图片到视频 |
| 15 | V-JEPA 2 · Assran et al. 2025 | 📄 `pdfs/world-model/Assran 等 - 2025 - V-JEPA 2...pdf` | 加上规划能力 |
| 16 | V-JEPA 2.1 · Mur-Labadia et al. 2026 | 📄 `pdfs/world-model/Mur-Labadia 等 - 2026 - V-JEPA 2.1...pdf` | Dense feature 改进 |
| 17 | LeWorldModel · Maes et al. 2026 | 📄 `pdfs/world-model/Maes 等 - 2026 - LeWorldModel...pdf` | 端到端 pixel→action JEPA |

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
