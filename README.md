# learn_embodied_papers · 具身智能学习笔记

面向具身智能（Embodied AI）方向的个人学习记录，不限于论文精读——也包含**源码精读**、工程实践、认知科学背景。
每篇笔记聚焦：核心贡献/设计、架构拆解、关键公式或代码、与研究/工程实践的联系。

**[→ 在线访问](https://www.siyuanluoembodied.xin/)**

## 已收录

### 📄 论文精读

| 论文 | 方向 | 状态 |
|------|------|------|
| [A Path Towards Autonomous Machine Intelligence](papers/lecun-autonomous-intelligence.html) · LeCun (2022) | 世界模型 / JEPA | ✅ 完成 |
| [π₀: A Vision-Language-Action Flow Model](papers/pi0-vla-flow-model.html) · Black et al. (2024) | VLA / Flow Matching | ✅ 完成 |
| [婴儿认知发育时间线](papers/infant-cognition-timeline.html) · Dupoux | 认知科学背景 | ✅ 完成 |

### 🔧 源码精读

| 笔记 | 对应 | 状态 |
|------|------|------|
| [π₀ / π₀.5 代码阅读笔记](papers/pi0-code-reading.html) | [openpi](https://github.com/Physical-Intelligence/openpi) · `pi0_pytorch.py` | ✅ 完成 |

## 内容组织方式

每条方向按 "① 开山/主模型 → ② 横向扩展/基础组件 → ③ 改进/延伸" 三层组织。当前覆盖：

- **世界模型 · JEPA 路线**（LeCun → I-JEPA / V-JEPA / H-JEPA）
- **VLA · 视觉-语言-动作**（π₀ → RT-2 / OpenVLA，配套 Flow Matching / PaliGemma / SigLIP）
- **控制 · Policy & Planning**（Diffusion Policy / ACT / MPC / TD-MPC2）
- **认知科学 · 参考背景**（婴儿认知发育 / Core Knowledge / IntPhys）

## 本地运行

直接用浏览器打开 `index.html`，或启动本地服务器：

```bash
# Python
python -m http.server 8000

# Node.js
npx serve .
```

## 部署到 GitHub Pages

1. 推送到 GitHub 仓库
2. Settings → Pages → Source 选 `main` 分支 `/root`
3. 几分钟后即可通过 `https://your-username.github.io/learn_embodied_papers` 访问

## 项目结构

```
learn_embodied_papers/
├── index.html                          # 首页导航（方向分列）
├── assets/
│   ├── css/style.css                   # 共享样式（深色主题）
│   └── js/
│       ├── theme.js                    # 主题切换
│       └── interactive.js              # Step walker / Hotspot / Quiz
├── papers/                             # 渲染页（HTML）
│   ├── _template.html                  # 新笔记模板
│   ├── lecun-autonomous-intelligence.html
│   ├── pi0-vla-flow-model.html
│   ├── pi0-code-reading.html           # 源码精读（运行时渲染下面的 MD）
│   └── infant-cognition-timeline.html
├── notes/                              # 源笔记（Markdown）
│   └── pi0-code-reading.md
├── CLAUDE.md                           # AI 上下文（新对话时贴给 Claude）
└── README.md
```

## 写作规范

- 中文正文 + 英文术语对照（首次出现时加括号）
- 核心公式/架构要有直观类比
- 每篇尽量有"与 VLA / Embodied AI 的联系"一节
- 交互组件：tab 切换、图像热点、可视化 SVG / Mermaid 优先

## 贡献

欢迎通过 Issues 指出错误，或 PR 补充新的笔记（论文、代码或其他形式均可）。

## License

MIT
