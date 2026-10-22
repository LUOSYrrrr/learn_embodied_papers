import fs from 'node:fs';
import tables from '../content/egohumanoid-v2/tables.mjs';
const file='papers/egohumanoid-v2.html';
let html=fs.readFileSync(file,'utf8');
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const read=name=>fs.readFileSync(`content/egohumanoid-v2/${name}.html`,'utf8').trim();
function inject(name,content,anchor){
 const start=`<!-- EGOV2-${name}:START -->`,end=`<!-- EGOV2-${name}:END -->`,block=`${start}\n${content}\n${end}\n`;
 if(html.includes(start)){const a=html.indexOf(start),b=html.indexOf(end,a);if(b<0)throw Error(`Missing ${end}`);html=html.slice(0,a)+block+html.slice(b+end.length).replace(/^\n/,'');}
 else {if(!html.includes(anchor))throw Error(`Missing anchor ${anchor}`);html=html.replace(anchor,block+'\n'+anchor);}
}
const tableHTML=t=>`<div class="eval-table-wrap"><table class="eval-table"><caption>${esc(t.caption)}</caption><thead><tr>${t.head.map(h=>`<th scope="col">${esc(h)}</th>`).join('')}</tr></thead><tbody>${t.rows.map(row=>`<tr>${row.map((v,i)=>`<${i?'td':'th scope="row"'}>${esc(v)}</${i?'td':'th'}>`).join('')}</tr>`).join('\n')}</tbody></table></div>`;
const allTables=`<section class="deep-reading" id="table-index"><h2>全部 12 张表：原表、逐项数据、读法与边界</h2><p>以下数据按论文原编号完整转录；必要时拆开子表或转成长表以便阅读。原表保留供核对。没有把缺失值当零，也没有用加粗排名代替统计显著性。正文 1–4、附录 5–12 均在这里。</p><nav class="reading-path" aria-label="全部论文表格">${tables.map(t=>`<a href="#table-${t.n}">Table ${t.n} · ${esc(t.title.split('：')[0])}</a>`).join('')}</nav>${tables.map(t=>`<section class="table-reading" id="table-${t.n}" data-paper-table="${t.n}"><h3>Table ${t.n} · ${esc(t.title)}</h3><p class="source">论文 p.${t.page} · ${esc(t.source)} · <a href="https://arxiv.org/pdf/2609.37181v1#page=${t.page}">原文定位</a></p>${t.tables.map(tableHTML).join('\n')}<ol>${t.notes.map(n=>`<li>${esc(n)}</li>`).join('')}</ol><details class="table-source"${t.open?' open':''}><summary>查看 Table ${t.n} 论文原表（含原 caption）</summary><figure><a href="../assets/figures/egohumanoid-v2/table-${t.n}.png" target="_blank" rel="noopener"><img src="../assets/figures/egohumanoid-v2/table-${t.n}.png" alt="论文 Table ${t.n} 原表：${esc(t.title)}；上方有完整文字数据与解读" loading="lazy" decoding="async"></a><figcaption>原文 Table ${t.n} · p.${t.page} · 400 DPI 从固定版本裁出；点击放大。</figcaption></figure></details></section>`).join('\n')}</section>`;
inject('GUIDE',read('guide'),'\n<h2 id="figure-index">');
inject('PIPELINE',read('pipeline'),'\n<h2 id="figure-index">');
inject('METHOD',read('method'),'\n<h2 id="vision">');
inject('METRICS',read('metrics'),'\n<h2 id="evaluation">');
inject('TABLES',allTables,'\n<h3 id="online-ik">');
inject('ONLINE',read('online-ik'),'\n<h3 id="online-ik">');
inject('RESEARCH',read('research'),'\n<h2 id="connection">');
html=html.replace(/<title>[^<]*<\/title>/,'<title>EgoHumanoid-V2 · 全文与附录精读：9 公式、10 图、12 表</title>');
html=html.replace(/<meta name="description" content="[^"]*">/,'<meta name="description" content="EgoHumanoid-V2 全文与附录 A–D 中文精读：9 个公式逐符号和算例、10 张原图、12 张原表、完整 pipeline 与 online IK 专图、训练部署与全部实验协议。">');
if(!html.includes('egov2-deep-reading.css'))html=html.replace('</head>','<link rel="stylesheet" href="../assets/css/egov2-deep-reading.css"></head>');
html=html.replaceAll('../pdfs/loco-manipulation/egohumanoid-v2.pdf','https://arxiv.org/pdf/2609.37181v1');
html=html.replace('真实仿真 rollout','仿真中的实际 rollout');
html=html.replace('默认一轮 K、七轮常规 D、一轮保守 D，每轮 400 Adam steps。','默认一轮 K、七轮常规 D、一轮保守 D；每轮 D 的局部优化做 400 Adam steps。');
html=html.replace('2026-10-23 修订：补齐此前缺失的 Figure 1、2、4–10，并将 Figure 3 从“配图”改为逐步解读。','2026-10-23 全文修订：全部 10 张图均保留逐图解读，并补齐公式、表格、附录与两张明确标注的教学流程图。');
const nav=[['overview','结论先行'],['reading-guide','正文 / 附录覆盖地图'],['full-pipeline','完整 pipeline 图'],['offline-online-ik','Online vs Offline IK 图'],['figure-index','全部 10 张论文图'],['figure-2','为什么还需要 GoPro'],['deep-method','目标 / 参考 / 命令 / 执行'],['eq-1','Eq.1 · 29/43/64/76 维'],['eq-5','Eq.5 · 坐标与骨盆高度'],['eq-2','Eq.2 · Offline K'],['eq-3','Eq.3–6 · D 与梯度'],['response-training','A.3 · 响应网络怎样训练'],['selection-deep','A.4 · 数据验收'],['policy-training','B.1–2 · VLA 训练'],['vision','视觉对齐'],['metrics-deep','Eq.7–9 · 评分与选优'],['evaluation','真机 / ID–OOD / 仿真'],['table-index','全部 12 张表'],['table-2','Table 2 · 初始化对照'],['table-8','Table 8 · 计算成本'],['figure-8','Appendix D · 三组失败图'],['research-context','相关工作 / 局限 / 声明'],['connection','与 VLA / Embodied AI']];
html=html.replace(/<aside class="docs-sidebar-left"[\s\S]*?<\/aside>/,`<aside class="docs-sidebar-left" aria-label="章节导航"><div class="ds-title">EgoHumanoid-V2 · 全文精读</div>${nav.map(([id,label])=>`<a class="ds-leaf-top" href="#${id}">${label}</a>`).join('')}</aside>`);
html=html.replace(/<div class="eval-table-wrap"([^>]*)>/g,(match,attrs)=>attrs.includes('tabindex=')?match:`<div class="eval-table-wrap"${attrs} tabindex="0" aria-label="可横向滚动的表格">`);
fs.writeFileSync(file,html);
console.log(`Built ${file}: ${tables.length} complete tables, 9 numbered formula tutorials, 10 original figures, 2 explanatory diagrams.`);
