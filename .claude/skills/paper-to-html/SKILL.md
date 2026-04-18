---
name: paper-to-html
version: 1.0.0
description: |
  把学术论文 PDF 整理成中文交互式 HTML 笔记页面。三栏 docs 布局（左章节树/中正文/右页内目录），
  原图嵌入（自动从 PDF 裁剪），中英对照（可折叠原文引用），交互组件（Step Walker 步骤导览、
  Image Hotspot 图上热点、Quiz 理解检查、Mermaid 流程图、Tab 切换）。暗/亮主题切换。
  适合个人精读笔记。Use when 用户说"整理论文/写论文笔记/把这篇 paper 做成网页/embodied/VLA 论文解读"。
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Grep
  - Glob
---

# paper-to-html

把论文 PDF 转成可交互的中文 HTML 精读页面。这个 skill 抓住的核心痛点是：**论文太长不想读、读了记不住、图表看不懂**——通过中文导读+原图+点击式交互来解决。

## 触发场景

- "帮我把这篇 paper 整理成 HTML"
- "做成那种 docs 网站的样式"
- "把论文做成可以交互的笔记"
- 用户已有 paper-notes 类项目，往里加新论文

## 工作流（必须按顺序）

### 0. 检查项目结构

如果项目根目录没有以下结构，先建立：

```
project-root/
├── index.html
├── assets/css/style.css
├── assets/js/theme.js
├── assets/js/interactive.js
├── assets/figures/<paper-slug>/
├── papers/<paper-slug>.html
└── pdfs/<category>/<paper-slug>.pdf
```

把 `assets/css/style.css`、`assets/js/theme.js`、`assets/js/interactive.js`、`templates/paper-template.html` 从本 skill 的 `assets/` 拷过去（如果用户项目里没有同名同等功能的版本）。

### 1. 读 PDF —— 不要凭印象写

**铁律：从来不要凭对作者/领域的"了解"写内容**。具体来说：

- 用 `Read` 工具读 PDF（pages 参数分批，每批 5-15 页）
- 边读边记关键术语原文 + 图编号 + 页码
- 写每节前必须有对应 PDF 段落作为依据
- 引用原文时**短引用 + 标 §章节 p.页码**

### 2. 提取并裁剪图

```bash
# a. 找出每张图所在页（论文里标注 Figure X 的页）
pdfinfo <pdf>  # 看总页数

# b. 单页导出 PNG（150 DPI 够清晰）
pdftoppm -png -r 150 -f <page> -l <page> <pdf> assets/figures/<slug>/page

# c. 必须裁剪（这是关键，不裁剪百分比坐标会偏）
#    用 sips 裁掉页眉/页脚/正文，只留图 + caption
sips --cropToHeightWidth <h> <w> --cropOffset <y> <x> <input> --out <output>

# 或更简单：用 Python + PIL（如果 sips 偏移不好算）
python3 -c "
from PIL import Image
img = Image.open('assets/figures/<slug>/page-XX.png')
# 估计图区域 (left, top, right, bottom)，裁掉
img.crop((50, 100, img.width-50, int(img.height*0.65))).save('assets/figures/<slug>/fig-X.png')
"
```

**裁剪后命名**：`fig-2.png`、`fig-3.png`...（不是 page-XX.png）。这样图和论文 Figure 编号对应。

### 3. 搭页面骨架

复制 `templates/paper-template.html` 到 `papers/<slug>.html`，填入：

- `<title>`
- breadcrumb 路径
- 论文标题/作者/年份/版本
- 左章节树（按论文目录结构，用 `<details>` 折叠）

**布局默认 2 栏（左章节树 + 中正文）**。右侧页内 TOC 和左章节树在精读笔记场景下高度重复，不要默认加。只有当论文特别长、单章内还要小目录定位时才 opt-in 加 `.has-right` 类。对应 CSS：

```css
.docs-layout { grid-template-columns: 240px minmax(0, 1fr); max-width: 1280px; }
.docs-layout.has-right { grid-template-columns: 240px minmax(0, 1fr) 220px; max-width: 1400px; }
```

**如果删掉右 TOC，同时把 JS 里 `document.getElementById('page-toc')` 相关的生成/IntersectionObserver 代码一起删掉**。否则 `null.querySelectorAll` 会把同 `<script>` 块里的 Tab / Mermaid 逻辑一起搞挂。

### 4. 逐节写内容（每节都要这五样）

#### 叙事流（★★★ 每节必须承上启下 · 跟着作者思路走）

**铁律：笔记不是原论文章节的翻译搬运，是重构后的一条"思想链"**。每一节 `.cn-read` 必须做三件事：

1. **承上**：一句话说"上一节讲到这里，留了什么问题没解决"
2. **启下**：一句话说"作者为什么接下来要讲这个，是在回答什么问题"
3. **小结**：读完本节你能知道什么

这不是凑字数——是把论文作者**隐藏的 reasoning chain** 显式写出来。论文为了正式性常常跳过动机句（"We now introduce X"），笔记必须把"为什么是 X、不是 Y"讲清楚。

**反例警告**：这是真实犯过的错。在写 LeCun paper 时，§3.3 讲"四种架构坍缩类型"（概念图），§3.4 讲"对比 vs 正则两种防坍缩思路"（概念图），§3.5 直接跳到 JEPA 架构。读者反馈"章节之间没关联"——因为中间跳过了关键一步：**每种架构对应哪种正则器？loss 公式具体长什么样？** 必须补一个 §3.4b 桥段，把"坍缩分类 → 每架构的正则器 → JEPA 架构设计决定"这条链显式写出来。

**自查信号**：如果你能把本节标题和上一节标题的连接词写成一句话（"因为上节 X，所以本节 Y"），说明链是通的。如果写不出来——要么缺了 bridge section，要么本节位置不对。

常见要补的 bridge 类型：
- **从概念到公式**：概念章（e.g. "EBM 的两种训练思路"）后面必须有公式章（"loss 具体长什么样"），不然读者不会写 loss
- **从公式到具体架构**：公式章（e.g. "防坍缩正则器的通用形式"）后面要有"每架构对应哪条正则"的映射章
- **从架构到实现**：架构图（e.g. "JEPA"）后面要有"工业实现怎么做"（e.g. "VICReg"）
- **章节转场**：每个 h2 之间至少一句话 recap 前一章 + 预告本章要回答什么

**在 `.cn-read` 里怎么写**：开头直接写"上一节讲了 X、但漏了 Y 没讲——这一节补上"。不要写"本节介绍 X"（那是论文腔，不是笔记腔）。

#### A. `.cn-read` 中文导读块（每节开头必须有）

```html
<div class="cn-read">
  <div class="cn-label">这一节解决什么</div>
  <p>用最白话告诉小白：这一节<strong>在解决什么问题</strong>，结论<strong>是什么</strong>。
  避免直接堆术语，先建立直觉。</p>
</div>
```

#### B. `.en-quote` 原文引用（关键论点必须配）

```html
<details class="en-quote">
  <summary>展开原文 · <段落主题></summary>
  <div class="quote-body">
    <p>"短段引用，1-3 句话，**不要整段照抄**"</p>
    <div class="quote-cite">— §X.Y, p.N</div>
  </div>
</details>
```

#### C. `.fig-block` + Image Hotspot（每张图都要）

**必须用 `.fig-interactive` 把图和 panel 包成 2 栏并排**。否则图在上、panel 在下，用户点完要滚下去看讲解，再滚回图——体验极差（来自用户直接反馈）。

```html
<div class="fig-interactive">
  <div class="fig-block">
    <div class="hotspot-wrap" data-hotspot-group="figN">
      <img src="../assets/figures/<slug>/fig-N.png" alt="Figure N: ...">
      <div class="hotspot" data-id="elem1" style="left:50%; top:30%;"
           data-title="元素名 · English Name"
           data-body="这个元素是什么、为什么重要、怎么和别的元素连接"></div>
      <!-- 重复 5-8 个 hotspot -->
    </div>
    <div class="fig-cap">
      <span class="fig-num">Fig N · p.X</span>
      论文原文 caption（英文）
      <span class="fig-cn">中文翻译/解释</span>
    </div>
  </div>
  <div class="hotspot-panel"></div>
</div>
```

`.fig-interactive` 在 ≥1200px 屏幕上是 `minmax(0,1fr) 260px` 两栏（panel 右侧 sticky 跟随滚动），窄屏自动降级为单列堆叠。样式已在 `style.css` 里，直接用。

**热点视觉平衡**：默认 `opacity: 0.55`、size 20px；hover/active 全不透明放大。不要把 dot 做大做实心——图缩小后会把图本身盖住（用户直接反馈过）。

##### 热点坐标 SOP（★★★ 关键）

**不要再凭 `Read` 看图瞎估坐标**。每个新 paper 的新图必须用浏览器里的 edit mode 当场取点。已经在 `interactive.js` 里实装：

1. 页面加 `?edit-hotspots=1` query，所有 `.hotspot-wrap` 进入 edit mode
2. 点图任意位置 → 右上角 toast 显示 `left:X.X%; top:Y.Y%;`，同时写入剪贴板
3. 直接粘进 HTML `style="..."`，去掉 `?edit-hotspots=1` 刷新验证

工作流：先写好所有 hotspot 的 `data-title` / `data-body`，坐标先填占位 `left:50%; top:50%;`，然后开 edit mode 一个个取坐标替换。

**别再走"估一轮 → 用户指出错 → 再估一轮"的老路**。LeCun 那篇 Fig 8/9/10/11/12 五张图的热点坐标全部一次估偏（panel 区域被当成图，caption 被当成子图），改回来比一次取对贵得多。

#### D. `.step-walker` 步骤导览（复杂图必配，关联 hotspot）

```html
<div class="step-walker" data-hotspot-group="figN">
  <div class="sw-header">
    <div class="sw-title">🪜 跟着信号走一遍</div>
    <div class="sw-controls">
      <button class="sw-btn prev">◀</button>
      <span class="sw-counter">1 / 5</span>
      <button class="sw-btn next">▶</button>
    </div>
  </div>
  <div class="sw-progress">
    <div class="sw-dot"></div><!-- N 个，对应 N 步 -->
  </div>
  <div class="sw-body">
    <div class="sw-step active" data-hotspot="elem1">
      <h4>第 1 步：标题</h4>
      <p>这一步在做什么、看图哪个地方</p>
    </div>
    <!-- 每步都有 data-hotspot，会自动激活图上对应热点 -->
  </div>
</div>
```

#### E. `.quiz` 理解检查（每章/每节末尾配 1-2 道）

```html
<div class="quiz"
     data-correct="b"
     data-explain="解释为什么 b 对，引用论文证据"
     data-explain-wrong="解释为什么用户选的不对（点错时显示）">
  <div class="q-label">🧠 理解检查</div>
  <div class="q-text">问题文本？</div>
  <div class="q-options">
    <button class="q-opt" data-k="a">选项 A</button>
    <button class="q-opt" data-k="b">选项 B（正确）</button>
    <button class="q-opt" data-k="c">选项 C</button>
    <button class="q-opt" data-k="d">选项 D</button>
  </div>
  <div class="q-feedback"></div>
</div>
```

**Quiz 设计原则**：
- 错的选项要"看似合理"，不能明显错（否则没意义）
- 正确答案的解释要引用论文具体段落
- 测概念理解，不测细节背诵

### 5. 其他可用组件

- **`.term`**：行内术语 hover 出英文。`<span class="term" data-en="model-predictive control">模型预测控制</span>`
- **`.tab-switcher`**：多个并列概念切换（如六大模块定义）
- **Mermaid**：自定义流程图。`<pre class="mermaid">flowchart LR\n A --> B</pre>`
- **`.module-grid` + `.module-card`**：2 列卡片网格，列举多个并列示例

### 6. 工作节奏（重要）

**绝对不要一次写完整篇 60 页论文**。会失控、会瞎编、用户没法验证。

正确节奏：

1. 先读 §1-§2（前 10-15 页），建立全文结构理解
2. 写出**布局骨架** + **§1 总览**给用户看
3. 用户确认方向 → 写 §2，**先做一节当样板**
4. 用户确认样板 OK → 按同样模式扩到其他章节
5. 每写完 1-2 节就停下让用户看效果
6. 改交互细节（热点位置、步骤数、quiz 难度）时**只改一个地方测**，不要批量

### 7. 提交粒度

每完成一个有意义的单元就 `git commit`：

- "feat(<slug>): 三栏布局骨架 + §1 总览"
- "feat(<slug>): §2 架构 + Fig 2 hotspot + step walker"
- "feat(<slug>): §3 JEPA + Fig 8/9/10"
- "fix(<slug>): Fig 2 热点坐标修正"

## 反模式（不要做）

- ❌ 凭对作者/领域的"印象"写内容，没读 PDF
- ❌ 一次性写完所有章节再给用户看
- ❌ 自己用 SVG 重画论文图（用户原话："会不准确"）
- ❌ 长段引用论文原文（短引 + 页码）
- ❌ 中文导读用术语堆砌，没有"小白能秒懂的类比"
- ❌ Step Walker 没关联 hotspot，纯文字流程
- ❌ Quiz 答案明显，没有迷惑性
- ❌ 不裁图直接用整页 PNG（百分比坐标会全错）
- ❌ 图和 `.hotspot-panel` 上下堆（用户点热点要滚下去看讲解，体验崩）——必须 `.fig-interactive` 并排
- ❌ 凭 `Read` 看裁剪图瞎估热点坐标——用 `?edit-hotspots=1` edit mode 当场取
- ❌ 热点 dot 做大做实心——图缩小后会遮图，默认半透明 + hover 放大
- ❌ 默认开三栏布局（左 tree + 右 TOC）——右 TOC 和左 tree 重复，默认两栏就够
- ❌ 删右 TOC aside 时漏删 `#page-toc` 的 JS（会 `null.querySelectorAll` 把同 script 块其他功能搞挂）

## 验证清单（每节写完自查）

- [ ] 中文导读 `.cn-read` 在最前面
- [ ] 关键论点配了 `.en-quote` 短引
- [ ] 每张图都有 hotspot（5-8 个，覆盖主要元素）
- [ ] **每张图都用 `.fig-interactive` 把图+panel 并排**
- [ ] **每张图的热点都用 `?edit-hotspots=1` 当场取过坐标，不是瞎估**
- [ ] **本节的 `.cn-read` 写了"承上"——和上一节的连接是否一句话能说清**
- [ ] **章与章之间没有"断层"——概念后有公式，公式后有架构映射，架构后有实现**
- [ ] 复杂图配了 step walker，且步骤关联 hotspot
- [ ] 章末有 quiz
- [ ] 术语首现用 `.term` 标了英文
- [ ] 引用都标了 §x.y, p.N

## 项目脚手架（首次用）

如果用户项目还没建立基础，按本 skill 同目录 `assets/` 和 `templates/` 拷贝以下文件：

- `style.css`（含三栏布局 + 暗亮主题 + 所有交互组件样式）
- `theme.js`（暗亮主题切换 + localStorage 持久化）
- `interactive.js`（Step Walker / Hotspot / Quiz 逻辑）
- `paper-template.html`（论文页骨架）
- `index-template.html`（首页骨架，按方向分组）

之后每篇新论文只需复制 `paper-template.html` 改内容。
