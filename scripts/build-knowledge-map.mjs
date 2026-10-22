import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

// One semantic/layout source, two native representations: SVG and draw.io XML.
// The SVG is authored here, not presented as a draw.io CLI export.
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const out = path.join(root, 'assets/diagrams');
fs.mkdirSync(out, { recursive: true });
const esc = s => String(s).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
const groups = [
  ['routes', '专题路线与训练指南', '入口页面，不计作独立论文。', 'wam-roadmap vla-rl-roadmap real-robot-rl-roadmap embodied-icl-roadmap pi-series-training-guide'],
  ['policy', '动作策略 · VLA', '按主要学习用途归档，不是互斥分类。π₀.₇ 等同时连接预测与规划；Diffusion Policy 不必以语言为条件。', 'rt1 rt2 rt-2 openvla pi0-vla-flow-model pi05-open-world pi07-steerable-generalist diffusion-policy bagelvla'],
  ['wm', '世界预测 · World Model', '学习状态、表征或观测怎样变化；是否接受动作、是否生成像素，要看具体模型。', 'dreamer-v1 vjepa vjepa2 vjepa21 leworldmodel cosmos-predict2 cosmos3 dreamdojo genie'],
  ['wam', '预测与动作的结合 · WAM 及相邻路线', '同时覆盖级联、联合与预测表征辅助策略。并非每篇都自称 WAM，也不是每篇推理时都生成未来视频。', 'unipi avdc vidar vpp gr-1 gr-2 worldvla cot-vla vla-jepa pad uwm uva dreamzero lingbot-va dit4dit motionwam tau0-wm being-m07 villa-x motus flare fast-wam flash-wam efficient-wam c3ache himem-wam omnivta fawam'],
  ['learning', '学习、适应与策略改进', 'BC/SFT、DAgger、RL、ICL 和测试时训练属于不同机制；QGF 等是推理引导，不等于部署时更新策略权重。', 'iql awac hil-serl pi06-recap-rl rl-vla-generalization expo-ft rl-token bora rankq dygro-vla learning-while-deploying rl-vla3 chi0 arfm co-rft flowpro dppo dsrl-latent-policy-rl reinflow sac-flow pi-rl sa-vla qgf self-improving-vla stare-vla rise-compositional-world-model wam-ttt'],
  ['foundation', '表征与生成模型基础', '共享工具箱：可用于世界预测，也可用于动作生成。I-JEPA 是图像表征方法，不自动等于动作条件动力学模型。', 'vlm-collection ijepa-self-supervised dit consistency-models generation/ddpm generation/ddim generation/classifier-free-guidance generation/vae generation/latent-diffusion generation/flow-matching generation/sora-world-simulators generation/cogvideox generation/open-sora generation/wan'],
  ['data', '数据、表征对齐与实现', '数据管线、质量检查和 latent action 预训练为多种模型服务，不是某一个模型的专属子类。', 'pi0-data-pipeline pi0-code-reading datasets-analysis qwen-robotmanip wb-quality-vs-qwen ego2robot lapa'],
  ['sim', '场景重建、仿真与迁移', 'GS 是表示／渲染技术；可交互仿真还需要碰撞、动力学、控制和任务定义。', '4d-gaussian-splatting simfoundry splatsim gsworld gaussgym'],
  ['control', '运动、全身控制与 Loco-Manipulation', '策略输出还要在具体本体上落地；此处包括学习式运动策略与全身控制系统。', 'sonic deepwbc vbc-loco-manipulation humanoid-gpt psi0 vlk humi openhlm'],
  ['evaluation', '评测与证据边界', '视觉质量、物理一致性、动作可用性和真机闭环是不同层次，不能互相代替。', 'videophy vbench-2 worldmodelbench physics-iq worldscore worldsimbench'],
  ['theory', '自主智能与认知背景', '理论组织与认知启发，不是某个机器人系统必须运行的组件。', 'lecun-autonomous-intelligence infant-cognition-timeline'],
];
function walk(dir) { return fs.readdirSync(dir, {withFileTypes:true}).flatMap(e => e.isDirectory() ? walk(path.join(dir,e.name)) : [path.join(dir,e.name)]); }
const all = walk(path.join(root,'papers')).filter(f=>f.endsWith('.html') && !f.endsWith('/_template.html') && !f.endsWith('/embodied-knowledge-map.html'));
const membership = new Map();
const catalog = groups.map(([id,title,note,slugs]) => ({id,title,note,papers:slugs.split(' ').map(slug=>{
  if(membership.has(slug)) throw Error(`Duplicate primary assignment: ${slug}`);
  membership.set(slug,id);
  const file=path.join(root,'papers',slug+'.html');
  if(!fs.existsSync(file)) throw Error(`Missing note: ${file}`);
  const html=fs.readFileSync(file,'utf8');
  const title=(html.match(/<title>([^<]+)<\/title>/i)?.[1] || slug).replace(/\s*·\s*(Paper Notes|VLA\+RL 详细精读|中文精读|精读)$/, '');
  return {slug,title};
})}));
const missing=all.filter(f=>!membership.has(path.relative(path.join(root,'papers'),f).replace(/\.html$/,'')));
if(missing.length) throw Error('Unmapped notes:\n'+missing.join('\n'));

const C={ink:'#202a35',muted:'#596674',line:'#d5dcd9',paper:'#faf9f5',white:'#ffffff',green:'#eaf4ef',greenLine:'#a8c8b9',greenInk:'#27684f',blue:'#eaf2fb',blueLine:'#a8bfd8',blueInk:'#335b83',purple:'#f0ecf8',purpleLine:'#bdafd8',purpleInk:'#665089',amber:'#fbf2e1',amberLine:'#d9c69f',amberInk:'#87672f'};
const nodes=[]; const labels=[]; const edges=[];
function box(id,parent,x,y,w,h,fill,stroke,link='',radius=16) { nodes.push({id,parent,x,y,w,h,fill,stroke,link,radius}); }
function label(id,parent,x,y,w,h,text,size=18,color=C.ink,bold=false,link='') { labels.push({id,parent,x,y,w,h,text,size,color,bold,link}); }
function edge(id,parent,x1,y1,x2,y2,color=C.muted,dash=false){edges.push({id,parent,x1,y1,x2,y2,color,dash});}
function lines(prefix,parent,x,y,w,texts,size=17,color=C.muted,step=27) {texts.forEach((t,i)=>label(prefix+i,parent,x,y+i*step,w,step,t,size,color));}
box('canvas','1',0,0,1600,1430,C.paper,C.paper,'',0);
label('eyebrow','canvas',45,27,1200,25,'PAPER NOTES  /  EMBODIED AI ATLAS',14,C.greenInk,true);
label('title','canvas',43,60,1150,60,'具身智能：把我们学过的内容放回一张图',36,C.ink,true);
label('subtitle','canvas',45,120,1480,30,'先看包含关系，再看能力组合；学习方法与数据环境是横向维度，不是模型的下一级。',19,C.muted);
box('field','canvas',30,175,1540,1210,C.white,C.line,'',25);
label('field-title','field',25,15,900,32,'具身智能研究版图  /  系统 · 模型 · 方法 · 环境 · 证据',23,C.ink,true);
label('legend','field',25,54,1460,25,'大框＝研究范围或系统组成　内框＝局部组成／子类　箭头＝作用或执行关系　并列栏不是严格互斥集合',16,C.muted);

box('runtime','field',25,100,1070,650,'#f6f8f7',C.line);
label('runtime-title','runtime',24,18,1010,32,'01  执行系统：具身 Agent / Harness',25,C.greenInk,true);
label('runtime-note','runtime',24,57,1010,25,'可选组成示意：不是每个 Agent 都包含下方所有模型；模型也可单独训练与评测。',16,C.muted);
box('orchestrator','runtime',25,97,1020,88,C.green,C.greenLine);
label('orchestrator-title','orchestrator',20,13,980,28,'任务理解与规划  ·  上下文／记忆  ·  工具调用  ·  验证与恢复',23,C.greenInk,true);
label('orchestrator-detail','orchestrator',20,48,980,27,'Astra / Jev 是可用的决策模型；GPT-Policy / RPent 是组织这些能力的系统〔本轮讨论扩展〕',16,C.muted);
label('toolkit-caption','runtime',25,202,1015,25,'模型与策略工具箱：看“输出什么、怎样参与决策”，不要只按名字分家',17,C.muted);

box('wm','runtime',25,242,315,288,C.blue,C.blueLine,'#catalog-wm');
label('wm-title','wm',18,15,285,34,'World Model',25,C.blueInk,true);
label('wm-cn','wm',18,51,285,26,'世界模型：预测状态／观测如何变化',16,C.blueInk);
box('wm-latent','wm',17,93,281,71,C.white,C.blueLine);
label('wm-latent-title','wm-latent',13,10,258,25,'在 latent / 表征中预测',18,C.ink,true);
label('wm-latent-eg','wm-latent',13,40,258,22,'Dreamer · V-JEPA 2 · LeWorldModel',14,C.muted);
box('wm-video','wm',17,179,281,70,C.white,C.blueLine);
label('wm-video-title','wm-video',13,9,255,25,'在视频／可见状态中预测',18,C.ink,true);
label('wm-video-eg','wm-video',13,39,255,23,'Cosmos · DreamDojo · Genie',15,C.muted);
label('wm-role','wm',18,258,280,23,'预测可供规划、训练或评测调用',15,C.blueInk);

box('policy','runtime',360,242,330,288,C.purple,C.purpleLine,'#catalog-policy');
label('policy-title','policy',18,15,290,34,'Action Policy',25,C.purpleInk,true);
label('policy-cn','policy',18,51,296,26,'动作策略：现在应该怎样行动',17,C.purpleInk);
box('vla','policy',17,93,296,116,C.white,C.purpleLine,'#catalog-policy');
label('vla-title','vla',14,10,266,27,'VLA 是其中一类',21,C.purpleInk,true);
label('vla-function','vla',14,42,266,26,'视觉 + 语言等条件 → 动作',17,C.ink);
lines('vla-ex','vla',14,72,266,['RT-1 / RT-2 · OpenVLA · π 系列'],15,C.muted);
label('other-policy','policy',18,226,291,25,'其他策略：Diffusion Policy 等',17,C.ink);
label('other-policy-note','policy',18,255,291,23,'生成动作，不必显式预测未来世界',15,C.muted);

box('wam','runtime',710,242,335,288,'#f0f3ef',C.greenLine,'#catalog-wam');
label('wam-title','wam',18,15,300,34,'WAM',27,C.greenInk,true);
label('wam-cn','wam',18,51,300,26,'World Action Model · 世界动作模型',16,C.greenInk);
box('wam-predict','wam',17,94,135,57,C.blue,C.blueLine);
label('wam-predict-title','wam-predict',10,16,120,27,'世界预测能力',17,C.blueInk,true);
box('wam-action','wam',183,94,135,57,C.purple,C.purpleLine);
label('wam-action-title','wam-action',10,16,120,27,'动作生成能力',17,C.purpleInk,true);
edge('wam-bridge','wam',153,122,180,122,C.greenInk);
lines('wam-route','wam',18,168,300,['级联：先预测未来，再提取动作','联合：未来与动作共同建模'],17,C.ink,30);
label('wam-ex','wam',18,239,300,23,'UniPi · DreamZero · MotionWAM',15,C.muted);
label('wam-foot','wam',18,263,300,22,'能力组合示意，不限定为两个独立网络',13,C.muted);

edge('policy-exec','runtime',525,531,525,566,C.purpleInk);
edge('wam-exec','runtime',877,531,877,566,C.greenInk);
label('wm-not-equal','runtime',26,541,450,25,'WM ≠ WAM；VLA 与 WAM 也不是互斥标签。',16,C.blueInk);
box('execution','runtime',25,569,1020,59,C.white,C.line,'#catalog-control');
label('execution-title','execution',17,8,985,24,'动作落地与反馈：IK / 运动规划 / 安全约束 / 全身控制 / 真实观测',19,C.ink,true);
label('execution-eg','execution',17,34,985,20,'SONIC · DeepWBC · VBC · Ψ₀ · HuMI · OpenHLM　｜　执行闭环不自动等于学习闭环',14,C.muted);

box('learning','field',1120,100,395,650,C.amber,C.amberLine,'#catalog-learning');
label('learning-title','learning',20,18,357,32,'02  学习与适应：改变了什么？',23,C.amberInk,true);
label('learning-note','learning',20,57,357,25,'横跨不同模型，不是 VLA 的内部结构',16,C.muted);
box('icl','learning',18,98,359,84,C.white,C.amberLine,'#catalog-routes');
label('icl-title','icl',14,9,329,25,'ICL  →  上下文变化，权重不变',20,C.amberInk,true);
label('icl-eg','icl',14,44,330,26,'GEN-1.5 · S1 · HOST · Zero-WAM',16,C.muted);
box('il','learning',18,198,359,101,C.white,C.amberLine);
label('il-title','il',14,10,330,26,'模仿学习  →  更新策略参数',20,C.amberInk,true);
lines('il-detail','il',14,43,330,['BC / SFT：拟合专家示范','DAgger：聚合学习者状态上的专家标注'],15,C.muted,25);
box('rl','learning',18,315,359,139,C.white,C.amberLine,'#catalog-learning');
label('rl-title','rl',14,9,330,27,'RL  →  利用奖励改进策略',20,C.amberInk,true);
lines('rl-detail','rl',14,45,330,['离线：IQL / AWAC　在线：HIL-SERL','VLA 后训练：RECAP / RL Token / DPPO','想象 rollout：Dreamer / RISE'],16,C.muted,28);
box('ttt','learning',18,470,359,63,C.white,C.amberLine,'#catalog-learning');
label('ttt-title','ttt',14,8,330,23,'测试时训练 TTT → 参数／快权重更新',17,C.amberInk,true);
label('ttt-detail','ttt',14,35,330,22,'WAM-TTT：与严格“固定权重 ICL”分开',15,C.muted);
box('improve','learning',18,549,359,78,C.white,C.amberLine,'#catalog-learning');
label('improve-title','improve',14,9,330,26,'自改进是外环目标，不是单一算法',18,C.amberInk,true);
label('improve-detail','improve',14,42,330,23,'可更新：记忆 · 代码 · 策略 · 训练流程',15,C.muted);

label('cross-caption','field',26,771,1460,29,'共享支撑层  ┄┄  下面的基础、数据和评测服务于上方多条路线，并非某个模型独占',18,C.muted);
box('foundation','field',25,820,500,249,'#f6f8fb',C.blueLine,'#catalog-foundation');
label('foundation-title','foundation',20,15,460,30,'03  表征与生成基础',24,C.blueInk,true);
lines('foundation-text','foundation',20,59,460,['Transformer / VLM / 图像与视频表征','DDPM · DDIM · CFG','VAE / LDM · DiT · Flow Matching','Wan · CogVideoX · Open-Sora · Sora','同一套生成工具，也可以用来生成动作'],19,C.muted,34);

box('data','field',545,820,595,249,C.green,C.greenLine,'#catalog-data');
label('data-title','data',20,15,550,30,'04  数据、环境与迁移',24,C.greenInk,true);
lines('data-text','data',20,59,550,['机器人示范 / 人类视频 / 数据质检与坐标对齐','Latent Action：LAPA / villa-X / Motus','场景重建 + 物理仿真 + 3D / 4DGS 渲染','Real → Sim → Real：重建、练习、回到真机','SimFoundry · SplatSim · GSWorld · GaussGym'],18,C.muted,34);

box('evaluation','field',1160,820,355,249,C.purple,C.purpleLine,'#catalog-evaluation');
label('evaluation-title','evaluation',20,15,315,30,'05  评测与可信证据',24,C.purpleInk,true);
lines('eval-text','evaluation',20,59,315,['视觉：VBench / WorldScore','物理：VideoPhy / Physics-IQ','动作：WorldSimBench','闭环：成功率 / 延迟 / 安全','好看的视频 ≠ 可执行的策略'],18,C.muted,34);

box('theory','field',25,1093,1490,89,'#f8f6f0',C.line,'#catalog-theory');
label('theory-title','theory',20,12,590,30,'06  理论与认知背景',24,C.ink,true);
label('theory-desc','theory',20,50,1450,27,'LeCun 自主智能架构 · 婴儿认知发育　｜　解释为什么要感知、预测、规划与学习，不是运行时必须装入的模块。',18,C.muted);
label('footer','canvas',46,1396,1510,24,`范围：${all.length} 个现有笔记页面（不是独立论文数，也不代表掌握程度） · 按主要用途归档，跨域关系保留 · 2026-09-26`,15,C.muted);

const byId=new Map(nodes.map(n=>[n.id,n]));
function origin(id){if(id==='1')return[0,0]; const n=byId.get(id);if(!n)throw Error('Bad parent '+id);const p=origin(n.parent);return[p[0]+n.x,p[1]+n.y];}
function svgNode(n){const [x,y]=origin(n.id);return `<rect x="${x}" y="${y}" width="${n.w}" height="${n.h}" rx="${n.radius}" fill="${n.fill}" stroke="${n.stroke}" stroke-width="1.4"/>`;}
let svg=`<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 1600 1430" width="1600" height="1430" role="img" aria-labelledby="map-title map-desc"><title id="map-title">具身智能知识总图</title><desc id="map-desc">外层是具身智能研究范围。执行系统可包含规划、记忆、世界预测、动作策略与控制。VLA 嵌套于动作策略；WAM 结合预测与动作能力。学习方法、生成基础、环境和评测是独立维度。图下方有全部笔记的可访问目录。</desc><defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="context-stroke"/></marker></defs>`;
svg+=nodes.map(svgNode).join('');
svg+=edges.map(e=>{const [x,y]=origin(e.parent);return `<path d="M${x+e.x1},${y+e.y1} L${x+e.x2},${y+e.y2}" fill="none" stroke="${e.color}" stroke-width="1.8" ${e.dash?'stroke-dasharray="5 5"':''} marker-end="url(#arrow)"/>`;}).join('');
svg+=labels.map(l=>{const [x,y]=origin(l.parent);return `<text data-label-id="${l.id}" data-label-width="${l.w}" x="${x+l.x}" y="${y+l.y+l.h/2}" dominant-baseline="central" font-family="PingFang SC, Microsoft YaHei, Noto Sans CJK SC, sans-serif" font-size="${l.size}" font-weight="${l.bold?600:400}" fill="${l.color}">${esc(l.text)}</text>`;}).join('');
svg+=nodes.filter(n=>n.link).map(n=>{const [x,y]=origin(n.id);return `<a href="${n.link}" aria-label="跳到${esc(n.id)}相关笔记"><rect x="${x}" y="${y}" width="${n.w}" height="${n.h}" rx="${n.radius}" fill="transparent" class="map-hotspot"/></a>`;}).join('');
svg+='</svg>';
// Standalone SVG links back into the HTML catalog; inline SVG uses local anchors.
fs.writeFileSync(path.join(out,'embodied-knowledge-map.svg'),svg.replaceAll('href="#catalog-', 'href="../../papers/embodied-knowledge-map.html#catalog-'));

let xml=`<mxfile host="app.diagrams.net" agent="paper-notes" version="24.7.17"><diagram id="embodied-atlas" name="具身智能知识总图"><mxGraphModel adaptiveColors="auto" dx="1600" dy="1430" grid="1" gridSize="10" page="1" pageScale="1" pageWidth="1600" pageHeight="1430"><root><mxCell id="0"/><mxCell id="1" parent="0"/>`;
for(const n of nodes)xml+=`<mxCell id="${n.id}" value="" vertex="1" parent="${n.parent}" style="rounded=${n.radius?1:0};arcSize=8;whiteSpace=wrap;html=0;fillColor=${n.fill};strokeColor=${n.stroke};strokeWidth=1.4;container=1;collapsible=0;recursiveResize=0;"><mxGeometry x="${n.x}" y="${n.y}" width="${n.w}" height="${n.h}" as="geometry"/></mxCell>`;
for(const e of edges)xml+=`<mxCell id="${e.id}" value="" edge="1" parent="${e.parent}" style="endArrow=block;endFill=1;strokeWidth=1.8;strokeColor=${e.color};dashed=${e.dash?1:0};"><mxGeometry relative="1" as="geometry"><mxPoint x="${e.x1}" y="${e.y1}" as="sourcePoint"/><mxPoint x="${e.x2}" y="${e.y2}" as="targetPoint"/></mxGeometry></mxCell>`;
for(const l of labels)xml+=`<mxCell id="${l.id}" value="${esc(l.text)}" vertex="1" parent="${l.parent}" style="text;html=0;align=left;verticalAlign=middle;whiteSpace=wrap;overflow=hidden;strokeColor=none;fillColor=none;fontFamily=PingFang SC;fontSize=${l.size};fontStyle=${l.bold?1:0};fontColor=${l.color};spacing=0;"><mxGeometry x="${l.x}" y="${l.y}" width="${l.w}" height="${l.h}" as="geometry"/></mxCell>`;
xml+='</root></mxGraphModel></diagram></mxfile>';
fs.writeFileSync(path.join(out,'embodied-knowledge-map.drawio'),xml);

const catalogHtml=catalog.map(g=>`<section class="catalog-group" id="catalog-${g.id}"><h3>${esc(g.title)} <span>${g.papers.length} 页</span></h3><p>${esc(g.note)}</p><div class="note-links">${g.papers.map(p=>`<a href="${esc(p.slug)}.html" data-note="${esc(p.title.toLowerCase())}">${esc(p.title)}</a>`).join('')}</div></section>`).join('\n');
const template=fs.readFileSync(path.join(root,'scripts/knowledge-map-page.template.html'),'utf8');
fs.writeFileSync(path.join(root,'papers/embodied-knowledge-map.html'),template.replace('<!-- MAP_SVG -->',svg).replace('<!-- NOTES_CATALOG -->',catalogHtml).replaceAll('{{NOTE_COUNT}}',String(all.length)));
fs.writeFileSync(path.join(out,'knowledge-map-manifest.json'),JSON.stringify({date:'2026-09-26',noteCount:all.length,groups:catalog,layout:{width:1600,height:1430},scope:'Existing note pages, not a claim of completed reading or unique paper count'},null,2)+'\n');
console.log(JSON.stringify({notePages:all.length,groups:catalog.map(g=>[g.id,g.papers.length]),nodes:nodes.length,labels:labels.length,outputs:['assets/diagrams/embodied-knowledge-map.svg','assets/diagrams/embodied-knowledge-map.drawio','papers/embodied-knowledge-map.html']},null,2));
