# paper-notes · 具身智能论文精读

面向具身智能（Embodied AI）方向的中文论文解析网站。每篇笔记包含：核心贡献、架构拆解、关键公式、与工程实践的联系。

**[→ 在线访问](https://www.siyuanluoembodied.xin/)**

## 已收录

| 论文 | 方向 | 状态 |
|------|------|------|
| [A Path Towards Autonomous Machine Intelligence](papers/lecun-autonomous-intelligence.html) · LeCun (2022) | 世界模型 / 架构 | ✅ 完成 |
| [婴儿认知发育时间线](papers/infant-cognition-timeline.html) · Dupoux | 认知科学背景 | ✅ 完成 |
| π₀: A Vision-Language-Action Flow Model · Black et al. (2024) | VLA | 🚧 进行中 |

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
3. 几分钟后即可通过 `https://your-username.github.io/paper-notes` 访问

## 项目结构

```
paper-notes/
├── index.html                          # 首页导航
├── assets/
│   └── css/
│       └── style.css                   # 共享样式
├── papers/
│   ├── lecun-autonomous-intelligence.html
│   ├── infant-cognition-timeline.html
│   └── ...                             # 后续论文
└── README.md
```

## 贡献

欢迎通过 Issues 指出错误，或 PR 补充新的论文笔记。每篇笔记尽量做到：
- 中文正文 + 英文术语对照
- 核心公式/架构有直观解释
- 与 VLA / embodied AI 研究实践有明确连接

## License

MIT
