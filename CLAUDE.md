# CLAUDE.md · paper-notes 项目上下文

> 每次新对话开始时，把这个文件的内容贴给 Claude，即可无缝继续开发。

---

## 项目概述

**名称**：paper-notes  
**目标**：一个静态 HTML 网站，提供具身智能（Embodied AI）方向的中文论文精读笔记，可直接部署到 GitHub Pages。  
**语言**：中文正文 + 英文术语对照  
**技术栈**：纯静态 HTML / CSS / JS，无框架，无构建工具

---

## 文件结构

```
paper-notes/
├── index.html                          # 首页，论文卡片列表
├── README.md                           # GitHub 仓库说明
├── CLAUDE.md                           # 本文件，AI 上下文
├── assets/
│   └── css/
│       └── style.css                   # 全站共享样式
└── papers/
    ├── _template.html                  # 新论文页面模板（复制此文件开始写新笔记）
    ├── lecun-autonomous-intelligence.html
    └── infant-cognition-timeline.html
```

---

## 设计系统

### 颜色（CSS 变量，定义在 style.css :root）

| 变量 | 用途 |
|------|------|
| `--bg` `#0d0f11` | 页面背景 |
| `--bg2` `#13161a` | 卡片/面板背景 |
| `--bg3` `#1a1e24` | 代码块/深层背景 |
| `--text` `#e8e6e0` | 主要文字 |
| `--text2` `#9a9690` | 次要文字 |
| `--text3` `#5c5a56` | 提示/标签文字 |
| `--accent` `#4ade9a` | 绿色强调（主色） |
| `--accent2` `#2ec4b6` | 青色 |
| `--accent3` `#ff6b6b` | 红色（警告/批评） |
| `--amber` `#f59e0b` | 琥珀色（注意/提示） |
| `--blue` `#60a5fa` | 蓝色（类比/联系） |
| `--purple` `#a78bfa` | 紫色（对应 VLA） |

### 字体

| 变量 | 字体 | 用途 |
|------|------|------|
| `--font-serif` | Noto Serif SC | 标题、section h2 |
| `--font-sans` | Inter | 正文 |
| `--font-mono` | JetBrains Mono | 标签、badge、代码 |

### 常用 CSS 组件类

```html
<!-- Callout 提示框（颜色变体：默认绿/amber/red/blue/purple） -->
<div class="callout [amber|red|blue|purple]">
  <div class="callout-label">标签文字</div>
  <p>内容</p>
</div>

<!-- KV 信息表格 -->
<table class="kv-table">
  <tr><td>键</td><td>值</td></tr>
</table>

<!-- 模块卡片网格（2列） -->
<div class="module-grid">
  <div class="module-card">
    <div class="module-card-name">ENGLISH · NAME</div>
    <div class="module-card-title">中文标题</div>
    <div class="module-card-desc">描述</div>
  </div>
</div>

<!-- 徽章（用于 paper-header） -->
<span class="badge badge-green">绿色</span>
<span class="badge badge-blue">蓝色</span>
<span class="badge badge-amber">琥珀</span>
<span class="badge">默认</span>

<!-- 代码块 -->
<div class="code-block"><code>代码内容</code></div>

<!-- 内联 code -->
<code>变量名</code>

<!-- SVG 图表容器 -->
<div class="diagram-wrap">
  <svg>...</svg>
  <div class="diagram-caption">图注</div>
</div>
```

### Section 标准结构

```html
<div class="section" id="section-id">
  <div class="section-num">§ 01</div>
  <h2>章节标题</h2>
  <!-- 内容 -->
</div>
```

---

## 已收录论文

### 1. lecun-autonomous-intelligence.html
- **论文**：A Path Towards Autonomous Machine Intelligence · Yann LeCun · 2022
- **方向**：世界模型 / 自主智能架构
- **内容**：六大模块（Configurator / Perception / World Model / Cost / Short-term Memory / Actor）+ Mode-1 感知-动作片段 + 与 VLA 的联系 + 批判
- **特色**：交互式标签页切换各模块详解（JS tab 切换）；内嵌 SVG 架构图

### 2. infant-cognition-timeline.html
- **论文**：婴儿认知发育时间线 · Dupoux
- **方向**：认知科学背景 / 发育心理学
- **内容**：0–14 月认知能力时间线（感知/物理/物体/社会/产出）+ 对 Embodied AI 的启示
- **特色**：SVG 绘制的时间线甘特图

---

## 占位论文（待写）

- `papers/pi0-vla-flow-model.html` — π₀: A Vision-Language-Action Flow Model · Black et al. 2024（Physical Intelligence）
- `papers/paligemma.html` — PaliGemma（SigLIP + Gemma）
- `papers/flow-matching.html` — Flow Matching for Generative Modeling

---

## Skill

新增论文笔记时使用 `/paper-to-html` skill，定义在：

```
.claude/skills/paper-to-html/SKILL.md
```

包含完整工作流：PDF 读取 → 图片裁剪 → 页面骨架 → 逐节内容（中文导读 / 热点图 / step-walker / quiz）→ 提交粒度。换电脑后 `git clone` 即可复用，无需重新配置。

---

## 新建论文页面的步骤

1. 复制 `papers/_template.html` → 新文件名（如 `papers/pi0-vla-flow-model.html`）
2. 修改 `<title>`、`paper-venue`、`paper-title`、`paper-authors`、`paper-badges`
3. 填写各 `section`（参考模板注释）
4. 在 `index.html` 的 `.papers-grid` 中添加一张 `.paper-card`：

```html
<a class="paper-card" href="papers/[文件名].html">
  <div class="card-tag">[方向标签]</div>
  <div class="card-title">[论文标题]</div>
  <div class="card-subtitle">[一两句描述]</div>
  <div class="card-meta">
    <span class="card-pill">[作者]</span>
    <span class="card-pill">[年份]</span>
    <span class="card-pill">[标签]</span>
  </div>
</a>
```

---

## 部署

```bash
# 本地预览
python -m http.server 8000

# 推送到 GitHub Pages
git add .
git commit -m "add: [论文名] 笔记"
git push

# GitHub 设置：Settings → Pages → Source: main / root
# 访问地址：https://[用户名].github.io/paper-notes
```

---

## 写作规范

- 正文用中文，英文专业术语保留并在首次出现时加括号说明，如：客体永久性（object permanence）
- 每个概念尽量有**类比**（类比生物/认知/工程已知事物）
- 每篇论文最后一节写"**与 VLA / Embodied AI 的联系**"
- Callout 颜色语义：绿=核心结论，amber=注意/提示，red=批评/局限，blue=类比/联系，purple=对应 VLA

---

## 作者上下文（给 Claude 的提示）

- 作者是墨尔本大学软件工程硕士生，正在向 VLA 算法方向转型
- 已深读：π₀ 完整架构（PaliGemma = SigLIP + Gemma，Action Expert，Flow Matching，Block-wise causal attention）
- 熟悉：Transformer（FFN/Attention/RoPE/RMSNorm），PyTorch，HPC (Spartan A100)
- 当前目标：2026 年 6 月前找到 embodied AI 方向实习
- 风格偏好：具体类比 > 抽象描述；有交互/可视化更好；中文写作
