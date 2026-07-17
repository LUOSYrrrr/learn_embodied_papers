---
name: zotero
description: "查询本机 Zotero 文献库（~/Zotero/zotero.sqlite）——按作者/年份/关键词/collection 搜论文、找 PDF 路径、读摘要和批注、验证引用。Use when 用户说：\"从 Zotero 找 XX 论文\"、\"我 Zotero 里有没有 XX\"、\"用 Zotero 里的 PDF 做笔记\"、\"我最近读了什么\"、\"我在 XX 上画了什么高亮\"，或 /paper-to-html 需要 PDF 而用户只给了论文名。"
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
---

# Zotero Skill（本机定制版）

> 基于 [dougwyu/claude-zotero-skills](https://github.com/dougwyu/claude-zotero-skills) 的 zotero-skill.md，
> 已针对本机环境定制（2026-07）。

## 本机环境事实（定制段，过期请重新查库更新）

- **数据库**：`/Users/siyuanluo/Zotero/zotero.sqlite`
- **PDF 存储**：`/Users/siyuanluo/Zotero/storage/<attachmentKey>/<filename>.pdf`
- **只有个人库**（`groups` 表为空，libraryID = 1），约 880 条条目、154 个 PDF 附件
- **相关 collections**（部分）：`world model`(22)、`VLA`(23)、`loco-manipulation`(42)、`Dreamer 系列`(26)、`grasp`(39)、`sim`(34)、`dataset`(40)、`end_to_end`(35)、`LLM`(10/21)、`CV`(12) —— collectionID 仅供参考，**用名字现查**
- **已装工具**：`pdftotext` ✓、`uv` ✓；**未装**：`pdfplumber` ✗、`litmap` ✗（Tier 4 语义搜索不可用，见文末）
- schema 存在 `itemAnnotations`、`retractedItems`、`itemAttachments.lastRead`（新版 schema 特性可用）

**计数、collection 列表、fieldID 一律现场查询，不要信本文件里的硬编码数字。**

## 连接方式

```python
import sqlite3, os

db_path = os.path.expanduser('~/Zotero/zotero.sqlite')
zotero_dir = os.path.dirname(db_path)

# Zotero 运行时持有写锁：mode=ro 会报 "database is locked"，
# immutable=1 可在 Zotero 开着时读一致性快照。绝不写库、绝不复制库文件
# （文件可能 >1 GB）。immutable=1 会忽略 -wal，刚在 Zotero 里做的改动
# 可能要等 WAL checkpoint（空闲/关闭时）才可见。
conn = sqlite3.connect(f"file:{db_path}?immutable=1", uri=True)
cur = conn.cursor()

# fieldID 跨大版本会变，必须运行时按名解析，禁止硬编码数字：
fids = dict(cur.execute("SELECT fieldName, fieldID FROM fields").fetchall())
# fids['title'], fids['abstractNote'], fids['date'],
# fids['publicationTitle'], fids['url'], fids['DOI']
```

下文 SQL 中 `{title}` 等占位符均指 `fids['title']`，执行前用 f-string 代入。
`date` 值形如 `"YYYY-MM-DD …"`，取年份用 `substr(value,1,4)`。

**每个查询都要排除回收站条目**：

```sql
AND i.itemID NOT IN (SELECT itemID FROM deletedItems)
```

## 搜索分层

```
明确作者/年份/标题，或指定 collection？   → Tier 1（元数据）
某个关键词在全文里出现？                  → Tier 2（全文索引）
要核对具体论断/提取引文/读图？            → Tier 3（打开 PDF）
概念式/同义改写/"找相似"？               → Tier 4（litmap，本机未装）
```

**Tier 1 — 元数据**（即时）：查 `itemData`/`itemDataValues`/`creators`。

**Tier 2 — 全文索引**（快）：

```sql
SELECT i.itemID, tv.value AS title
FROM fulltextWords fw
JOIN fulltextItemWords fiw ON fw.wordID = fiw.wordID
JOIN items i ON fiw.itemID = i.itemID
JOIN itemData td ON i.itemID = td.itemID AND td.fieldID = {title}
JOIN itemDataValues tv ON td.valueID = tv.valueID
WHERE fw.word = 'keyword'   -- 小写单词，不支持短语；短语用多词取交集
  AND i.itemID NOT IN (SELECT itemID FROM deletedItems)
```

**Tier 3 — 读 PDF**：
- 纯文本（论断、引文、数字）→ `pdftotext -q <pdf> -`（快、无页数限制）
- 理解图表 → **Read 工具 + pages 参数**（只有它能真正"看"图；≤20 页/次）
- pdfplumber 本机未装；扫描版 PDF pdftotext 输出为空时，可 `uv run --with pdfplumber python ...` 临时用
- 长文本用 `re.finditer` 定位段落，不要整篇打印

## 核心查询模板

### 按作者 + 年份找条目

```sql
SELECT DISTINCT i.itemID, i.key,
       tv.value AS title, dv.value AS date, jv.value AS journal,
       GROUP_CONCAT(c.lastName || ', ' || c.firstName, '; ') AS authors
FROM items i
JOIN itemCreators ic ON i.itemID = ic.itemID AND ic.orderIndex = 0
JOIN creators c ON ic.creatorID = c.creatorID
JOIN itemData td ON i.itemID = td.itemID AND td.fieldID = {title}
JOIN itemDataValues tv ON td.valueID = tv.valueID
LEFT JOIN itemData dd ON i.itemID = dd.itemID AND dd.fieldID = {date}
LEFT JOIN itemDataValues dv ON dd.valueID = dv.valueID
LEFT JOIN itemData jd ON i.itemID = jd.itemID AND jd.fieldID = {publicationTitle}
LEFT JOIN itemDataValues jv ON jd.valueID = jv.valueID
WHERE c.lastName LIKE '%LastName%' AND dv.value LIKE '%YEAR%'
  AND i.itemID NOT IN (SELECT itemID FROM deletedItems)
GROUP BY i.itemID
```

按标题关键词找：把 WHERE 换成 `tv.value LIKE '%keyword%'`。

### 按名字找 collection，再列其中条目

```sql
SELECT collectionID, collectionName FROM collections
WHERE collectionName LIKE '%search_term%'
```

```sql
SELECT DISTINCT i.itemID, i.key, tv.value AS title, dv.value AS date
FROM collectionItems ci
JOIN items i ON ci.itemID = i.itemID
JOIN itemData td ON i.itemID = td.itemID AND td.fieldID = {title}
JOIN itemDataValues tv ON td.valueID = tv.valueID
LEFT JOIN itemData dd ON i.itemID = dd.itemID AND dd.fieldID = {date}
LEFT JOIN itemDataValues dv ON dd.valueID = dv.valueID
WHERE ci.collectionID = ?
  AND i.itemID NOT IN (SELECT itemID FROM deletedItems)
ORDER BY dv.value DESC
```

### 取条目摘要

```sql
SELECT v.value FROM itemData d
JOIN itemDataValues v ON d.valueID = v.valueID
WHERE d.itemID = ? AND d.fieldID = {abstractNote}
```

### 找 PDF 路径（含补充材料）

```sql
SELECT ia.path, ia.contentType, i.key AS attachmentKey
FROM itemAttachments ia
JOIN items i ON ia.itemID = i.itemID
WHERE ia.parentItemID = ?
  AND ia.path IS NOT NULL AND ia.path != ''
ORDER BY ia.itemID   -- 注意：新版无 orderIndex 列，不要 ORDER BY ia.orderIndex
```

实际路径 = `~/Zotero/storage/<attachmentKey>/<ia.path 去掉 'storage:' 前缀>`。
文件名含 `supplement`/`appendix`/`SI`/`S1` 等的是补充材料；核对论断时主文 + SI 都要读。

### 最近读过什么（`lastRead`，Unix 秒）

```sql
SELECT datetime(ia.lastRead,'unixepoch') AS read_at, idv.value AS title
FROM itemAttachments ia
JOIN items parent ON ia.parentItemID = parent.itemID
JOIN itemData id_t ON parent.itemID = id_t.itemID AND id_t.fieldID = {title}
JOIN itemDataValues idv ON id_t.valueID = idv.valueID
WHERE ia.lastRead IS NOT NULL
ORDER BY ia.lastRead DESC LIMIT 20
```

### 我的高亮/批注（`itemAnnotations`，parentItemID = 附件的 itemID）

```sql
SELECT ia.type, ia.text, ia.comment, ia.color, ia.pageLabel
FROM itemAnnotations ia
WHERE ia.parentItemID = ?
ORDER BY ia.sortIndex
```

问"我在 XX 上高亮了什么"优先查这个表，比解析 PDF 快且准。

### 撤稿检查（做引用核对时先跑）

```sql
SELECT itemID, flag FROM retractedItems
```

## 与 /paper-to-html 的配合（本项目专用）

用户说"把 Zotero 里的 XX 论文做成笔记"时：

1. 用上面 Tier 1 按标题/作者找到条目，再查附件拿到
   `~/Zotero/storage/<key>/<file>.pdf` 的真实路径
2. 把 PDF **复制**（不要移动/软链）到本项目 `pdfs/<category>/<paper-slug>.pdf`
   —— 保持 Zotero storage 不被改动，同时项目内 PDF 可随 git 之外的流程留档
3. 之后按 `/paper-to-html` 原工作流进行（读 PDF → 裁图 → 写页面）
4. 顺手查一下 `itemAnnotations`：如果用户在 Zotero 里已有高亮，把高亮内容
   作为"用户关注点"参考，优先在笔记里展开这些段落

## 任务模式：引用核对（citation faithfulness）

1. 先查 `retractedItems`，撤稿论文置顶警告
2. Tier 1 按作者+年份定位每篇被引论文
3. 先读摘要快筛，明显不符直接标记
4. Tier 3 打开 PDF，用 `re.finditer` 找相关段落
5. 逐条论断给结论：**Faithful / Overstated / Misattributed（数字其实出自被引论文引用的另一篇，综述常见）/ Unsupported**，附原文短引
6. 涉及具体数字（%、计数）时必须在原文中找到该数字本身

## Tier 4 — litmap 语义搜索（本机未装，可选）

概念式搜索（"找讲 XX 思想的论文"，关键词搜不到同义改写）需要
[litmap](https://github.com/dougwyu/litmap)。启用步骤：

```bash
git clone https://github.com/dougwyu/litmap.git ~/src/litmap
cd ~/src/litmap && uv pip install -e .
litmap sync          # 嵌入摘要+元数据（分钟级；首次下载 ~570MB 模型）
# litmap sync-fulltext  # 全文嵌入，慢（小时~天级），效果更好
```

装好后：`uv run --project ~/src/litmap litmap search --query "..." --top-k 10 --format json`。
注意 litmap 返回的 `authors` **不保证作者顺序**，引用信息一律回 Zotero 库按
`zotero_key` + `orderIndex` 解析。

## 红线

- **绝不写 zotero.sqlite**，绝不复制/快照它（>1 GB），一律 `immutable=1` 原地读
- "database is locked" 的解法是 `immutable=1`，不是复制数据库
- fieldID 一律运行时解析，禁止硬编码
- 从 Zotero storage 拿 PDF 只做**复制**，不动原文件
