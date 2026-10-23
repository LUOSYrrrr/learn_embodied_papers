import fs from 'node:fs';
const dir='content/wam-frontier-20261023';
const manifest=JSON.parse(fs.readFileSync(`${dir}/manifest.json`,'utf8'));
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const requested=process.argv.slice(2);
for(const slug of requested.length?requested:manifest.order){
 if(!fs.existsSync(`${dir}/${slug}.html`))continue;
 const m=JSON.parse(fs.readFileSync(`${dir}/${slug}.json`,'utf8'));
 for(const f of m.figures)if(f.crop&&!f.dpi)f.dpi=Math.max(350,25*Math.ceil(800*(m.previewDpi||85)/Math.min(...f.crop.slice(2))/25));
 if(m.kind==='blog'&&m.visualizationRoot){
  const sources={model:'natura-1-diagram-v4.html',experience:'egocentric-data-demo.html?embed=1',data:'natura-data-bench.html',infra:'natura-infra-diagram-latest.html',benchmark:'score-embed.html',scaling:'scaling-embed.html'};
  for(const f of m.figures)f.source=m.visualizationRoot+sources[f.n];
  fs.writeFileSync(`assets/figures/${slug}/source-manifest.json`,JSON.stringify({source:m.source,reviewed:'2026-10-23',kind:'Official interactive diagrams captured through gstack browse',figures:m.figures},null,2)+'\n');
 }
 let body=fs.readFileSync(`${dir}/${slug}.html`,'utf8');
 const fig=f=>`<section class="figure-reading" id="figure-${f.n}"><h3>${m.kind==='blog'?'官方图':'Figure'} ${esc(f.n)} · ${esc(f.title)}</h3><figure><a href="../assets/figures/${slug}/fig-${f.n}.png" target="_blank" rel="noopener"><img src="../assets/figures/${slug}/fig-${f.n}.png" alt="${esc(f.alt||f.title)}" loading="lazy" decoding="async"></a><figcaption>${m.kind==='blog'?'官方交互图截图 · 2026-10-23 · 非论文编号':`论文原图 · Figure ${esc(f.n)} · p.${f.page} · ${f.dpi||350} DPI 裁剪`} · <a href="${esc(f.source||m.source)}${m.kind==='blog'?'':`#page=${f.page}`}">核对原文</a> · 点击原图放大。</figcaption></figure><ol>${f.notes.map(n=>`<li>${n}</li>`).join('')}</ol></section>`;
 for(const f of m.figures)body=body.replace(`<!-- FIGURE:${f.n} -->`,fig(f));
 if(/<!-- FIGURE:/.test(body))throw Error(`${slug}: unresolved figure`);
 const headings=[...body.matchAll(/<h2 id="([^"]+)">([\s\S]*?)<\/h2>/g)].map(x=>[x[1],x[2].replace(/<[^>]+>/g,'')]);
 body=body.replace(/<table\b/g,'<table').replace(/<div class="eval-table-wrap">/g,'<div class="eval-table-wrap" tabindex="0" aria-label="可横向滚动的证据表">');
 const html=`<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${esc(m.title)} · 中文精读</title><meta name="description" content="${esc(m.insight)}"><link rel="stylesheet" href="../assets/css/style.css"><link rel="stylesheet" href="../assets/css/humanoid-reading.css"><link rel="stylesheet" href="../assets/css/frontier-readings.css"><script src="../assets/js/theme.js"></script><script defer src="../assets/js/interactive.js"></script><script defer src="../assets/js/frontier-readings.js"></script></head><body class="series frontier"><a class="skip" href="#content">跳到正文</a><nav class="nav"><a class="nav-logo" href="../index.html">~/paper-notes</a><div class="nav-links"><a href="../index.html#frontier-reading">本组索引</a><a href="${esc(m.source)}" target="_blank" rel="noopener">${m.kind==='blog'?'官方长文':'论文 PDF'}</a></div></nav><div class="page"><div class="docs-layout"><aside class="docs-sidebar-left" aria-label="章节导航"><div class="ds-title">${esc(m.short)}</div><a class="ds-leaf-top" href="#overview">核心洞见 / 证据范围</a>${headings.map(([id,label])=>`<a class="ds-leaf-top" href="#${id}">${esc(label)}</a>`).join('')}</aside><main class="docs-content" id="content"><div class="kicker">${esc(m.category)} · OCTOBER 2026 READING SERIES</div><h1>${esc(m.title)}</h1><p class="paper-meta">${esc(m.subtitle)}<br>${esc(m.version)} · 核读：2026-10-23</p><section class="core-insight" id="overview"><div class="core-label">一句话核心洞见</div><p>${m.insight}</p></section><section class="eval-overview" aria-label="证据总览">${m.overview.map(([a,b])=>`<article class="eval-card"><div class="eval-card-title">${esc(a)}</div><div class="eval-card-value">${b}</div></article>`).join('')}</section><aside class="evidence-note" data-evidence="paper">${m.coverage}</aside>${body}<footer class="reading-footer"><h2>本组六项 / 继续阅读</h2><nav class="reading-links" aria-label="本组阅读">${manifest.order.map(s=>`<a href="${s}.html">${esc({onewm:'OneWM','agentic-wam':'AW-0','natura-1':'Natura-1','internw0-delta':'InternW0-Δ',uniwam:'UniWAM',flora:'FLORA'}[s])}</a>`).join('')}</nav><p>事实定位到原文；解释性推断和教学算例单独标记。未报告不等于不存在。图为论文或官方发布的原始证据，不由教学示意替代。</p></footer></main></div></div></body></html>`;
 fs.writeFileSync(`papers/${slug}.html`,html);
 console.log(`Built ${slug}: ${headings.length} sections, ${m.figures.length} figures`);
}
