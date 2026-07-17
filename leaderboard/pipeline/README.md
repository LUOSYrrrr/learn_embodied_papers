# Embodied AI Paper Leaderboard

个人向具身智能论文排行榜，覆盖四个方向：

| 方向 | arXiv query id | 说明 |
|------|----------------|------|
| **World Model / WAM** | `world-action-model` `robot-world-model` | 机器人世界模型、世界-动作模型、视频-动作联合建模 |
| **Humanoid & Legged Loco-Manipulation** | `loco-manipulation` `humanoid-whole-body` | 全身控制、动作跟踪/重定向、人形与腿足 loco-manipulation |
| **Dexterous Manipulation & Grasping** | `dexterous-manipulation` | 灵巧手、in-hand、双手操作、抓取 |
| **VLA** | `vla` `robot-foundation-policy` | VLA 架构、机器人基础模型、通用策略 |

基于 [DreamFallenFlowers/Paper-Leaderboard-For-You](https://github.com/DreamFallenFlowers/Paper-Leaderboard-For-You) 模板搭建（模板文档见 [docs/UPSTREAM-README.zh-CN.md](docs/UPSTREAM-README.zh-CN.md)）。

> 本目录是 learn_embodied_papers 仓库的子目录：前端在上一级 `leaderboard/`
> （随主站 GitHub Pages 部署，访问路径 `/leaderboard/`），本目录只放 pipeline。
> 以下命令均在本目录（`leaderboard/pipeline/`）下执行。

## 日常使用

```bash
# 1. 增量抓取 arXiv + 重算排名（无 key 时引用量记 missing，热榜≈新鲜度榜）
python3 scripts/pipeline.py run

# 2. 重新打关键词标签（自举版：短语匹配，无需任何 API key）
python3 scripts/bootstrap_keywords.py

# 3. 生成前端数据（写到 ../data/）
python3 scripts/build_site_data.py

# 4. 本地预览（在仓库根目录起服务，访问 /leaderboard/）
cd ../.. && python3 -m http.server 8321
```

## 接入引用量（待办）

排名的核心信号是 Google Scholar 引用量，需要 Serper API key：

1. 到 [serper.dev](https://serper.dev) 注册（免费送 2500 次查询）
2. `export SERPER_API_KEY=<你的key>`（写进 `~/.zshrc`）
3. 运行：

```bash
python3 scripts/pipeline.py refresh-citations   # 逐篇查 Scholar，结果缓存在 data/raw/scholar/
python3 scripts/build_site_data.py              # 重建前端数据
```

引用量有本地缓存，之后每次 `run` 只会补查新论文。论文数量多时注意 2500 次免费额度——可以先用 `data/processed/hot_ranked.csv` 里靠前的论文分批刷。

## 关键词精修（可选）

`bootstrap_keywords.py` 是短语匹配的自举版。正式流程是用 LLM 按
[config/keyword_extraction_policy.md](config/keyword_extraction_policy.md) 做
theme-first、受 [config/canonical_keywords_library.yaml](config/canonical_keywords_library.yaml)
约束的抽取，输出覆盖 `data/processed/model_keywords/keywords_latest.jsonl` 即可
（`scripts/extract_model_keywords.py` 需要 `OPENAI_API_KEY`，也可以直接让 Claude 批量做）。

## 部署 + 每日自动更新

前端随主站 GitHub Pages 部署（无需额外设置），访问路径 `/leaderboard/`。

主仓库的 `.github/workflows/leaderboard-update.yml` 已配置每天
19:30 UTC（墨尔本清晨）自动：增量抓 arXiv → 排名 → 打标签 → 重建
`leaderboard/data` → 提交推送（Pages 随之更新）。push 后自动生效，无需本机开机。

- 每日 cron **不调 Serper**（零额度消耗），只更新论文池和新鲜度
- 补引用量：Settings → Secrets 添加 `SERPER_API_KEY`，然后 Actions 页面手动
  Run workflow 并勾选 `refresh_citations`。scholar 缓存已入 git，只有新论文消耗额度
- ⚠️ 首次全量刷引用量约 3500+ 次查询，超过免费 2500 额度，建议先本地分批跑

`data/raw/scholar/` 特意不进 .gitignore：它是消耗 API 额度换来的缓存，
入库后 CI 和本机共享，不会重复扣费。

## 目录结构

```text
config/     query、taxonomy、关键词、评分配置
scripts/    pipeline.py（抓取/排名）、bootstrap_keywords.py（自举标签）、build_site_data.py（前端数据）
site/       静态前端（index.html + data/*.json）
data/       本地缓存与输出（不入库）
topics/     生成的 markdown 榜单页
```
