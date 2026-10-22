import fs from 'node:fs';
import path from 'node:path';

// Shared geometry for an editable native draw.io document and an independent SVG preview.
// The preview is not a CLI export and does not claim to embed the editable source.
const dir='assets/diagrams/egohumanoid-v2';
fs.mkdirSync(dir,{recursive:true});
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll('\n','&#xa;');
const groups=[
  {id:'capture',x:25,y:95,w:1150,h:175,title:'01 人体采集 · 没有机器人遥操作',color:'#eaf3ff'},
  {id:'offline',x:25,y:300,w:1150,h:610,title:'02 离线制作训练数据',color:'#fff6e5'},
  {id:'training',x:25,y:935,w:1150,h:280,title:'03 训练任务专用 VLA',color:'#f0eefe'},
  {id:'deployment',x:25,y:1240,w:1150,h:295,title:'04 真机部署 · 闭环执行',color:'#eaf7f0'},
];
const nodes=[
  {id:'raw',parent:'capture',x:60,y:155,w:1080,h:80,lines:['人完成任务：PICO 记录身体 / 手部运动，GoPro 记录第一人称 RGB','同步记录 → 人体运动、手姿态、RGB；再配任务语言指令'],color:'#ffffff'},
  {id:'H',parent:'offline',x:60,y:395,w:650,h:70,lines:['H · 人体运动 → SONIC 仿真 rollout','得到初始机器人关节轨迹、token 与骨盆高度'],color:'#ffffff'},
  {id:'K',parent:'offline',x:60,y:505,w:650,h:85,lines:['构造固定手 / 脚目标（含骨盆高度配准）','K · offline IK 改关节参考 → 编码为 SONIC token'],color:'#fff1d8'},
  {id:'D',parent:'offline',x:60,y:630,w:650,h:95,lines:['D · 冻结 decoder + MLP，优化 SONIC token','仿真 replay → 测执行残差 → 更新 context → 再优化','默认：7 轮常规 D + 1 轮保守 D'],color:'#fff1d8'},
  {id:'select',parent:'offline',x:60,y:765,w:650,h:85,lines:['历史候选选择 + 独立 replay 验收','保留通过验证的 token / 机器人状态；失败候选不直接入库'],color:'#ffffff'},
  {id:'vision',parent:'offline',x:760,y:395,w:380,h:145,lines:['RGB 视觉对齐','遮掉人体前臂与腕部 tracker','补全背景 → 渲染机器人臂','训练时再做图像增强'],color:'#eaf3ff'},
  {id:'hands',parent:'offline',x:760,y:630,w:380,h:95,lines:['手姿态重定向','人体手 → 左右 Revo2 手命令','每手 6 维'],color:'#eaf3ff'},
  {id:'dataset',parent:'training',x:60,y:990,w:1080,h:75,lines:['同步成监督样本：图像 + 43 维机器人状态 + 语言 → 76 维动作','动作 = 64 维 SONIC token + 左手 6 维 + 右手 6 维；状态来自验收 replay'],color:'#ffffff'},
  {id:'train',parent:'training',x:60,y:1110,w:1080,h:70,lines:['以预训练 π₀.₅ 为起点，每个任务各自 post-train 一份策略','训练 VLA 参数；不把 SONIC / 响应 MLP 当作一起端到端训练的新模型'],color:'#f0eefe'},
  {id:'obs',parent:'deployment',x:60,y:1330,w:260,h:105,lines:['真实观测','机器人 GoPro RGB','机器人状态 + 指令'],color:'#ffffff'},
  {id:'policy',parent:'deployment',x:365,y:1330,w:210,h:105,lines:['训练好的 VLA','预测动作序列','token + 双手命令'],color:'#f0eefe'},
  {id:'decode',parent:'deployment',x:620,y:1330,w:250,h:105,lines:['身体 token → SONIC','双手命令 → Revo2','不是运行 K + 8D'],color:'#fff1d8'},
  {id:'robot',parent:'deployment',x:915,y:1330,w:225,h:105,lines:['G1 实际执行','身体 + 双手','与环境交互'],color:'#eaf7f0'},
];
const edges=[
  ['raw','H',[[385,235],[385,395]]],
  ['raw','vision',[[950,235],[950,395]]],
  ['H','K',[[385,465],[385,505]]],
  ['K','D',[[385,590],[385,630]]],
  ['D','select',[[385,725],[385,765]]],
  ['raw','hands',[[1140,195],[1160,195],[1160,677],[1140,677]]],
  ['select','dataset',[[385,850],[385,990]]],
  ['vision','dataset',[[950,540],[735,540],[735,890],[950,890],[950,990]]],
  ['hands','dataset',[[950,725],[950,990]]],
  ['dataset','train',[[600,1065],[600,1110]]],
  ['train','policy',[[470,1180],[470,1330]]],
  ['obs','policy',[[320,1382],[365,1382]]],
  ['policy','decode',[[575,1382],[620,1382]]],
  ['decode','robot',[[870,1382],[915,1382]]],
  ['robot','obs',[[1028,1435],[1028,1490],[190,1490],[190,1435]],'下一次观测 / 自身状态反馈'],
];
const text=(x,y,lines,size=21,weight=400,anchor='middle')=>`<text x="${x}" y="${y}" text-anchor="${anchor}" font-size="${size}" font-weight="${weight}">${lines.map((s,i)=>`<tspan x="${x}" dy="${i?29:0}">${esc(s)}</tspan>`).join('')}</text>`;
const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1675" viewBox="0 0 1200 1675" role="img" aria-labelledby="title desc">
<title id="title">EgoHumanoid-V2 全流程：采集、离线制数、训练、部署</title><desc id="desc">解释图，非论文原图。离线制数也执行 SONIC 仿真；最终部署不运行 K 加八轮 D。附录 online IK 是独立对照而非主方法。</desc>
<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 Z" fill="#64748b"/></marker></defs>
<rect width="1200" height="1675" fill="#ffffff"/><g font-family="PingFang SC,Noto Sans CJK SC,Arial,sans-serif" fill="#152334">
${text(45,43,['EgoHumanoid-V2：四个阶段，不是一个网络端到端包办'],29,700,'start')}
${text(45,76,['解释图，非论文原图 · 来源 §3、Appendices A–B、D · 同一 SONIC checkpoint 用于对齐与部署'],17,400,'start')}
${groups.map(g=>`<rect x="${g.x}" y="${g.y}" width="${g.w}" height="${g.h}" rx="15" fill="${g.color}" stroke="#cbd5e1"/>${text(g.x+24,g.y+34,[g.title],23,700,'start')}`).join('')}
${edges.map((e,i)=>`<path d="${e[2].map((p,j)=>`${j?'L':'M'}${p[0]} ${p[1]}`).join(' ')}" fill="none" stroke="#64748b" stroke-width="2.4" marker-end="url(#arrow)"/>${e[3]?text(600,1478,[e[3]],18):''}`).join('')}
${nodes.map(n=>`<rect x="${n.x}" y="${n.y}" width="${n.w}" height="${n.h}" rx="9" fill="${n.color}" stroke="#94a3b8" stroke-width="1.5"/>${text(n.x+n.w/2,n.y+n.h/2-(n.lines.length-1)*14.5+7,n.lines,n.w<300?20:21)}`).join('')}
${text(950,570,['准备：SONIC 已预训练','MLP 用仿真干预数据另训'],17)}
<rect x="25" y="1560" width="1150" height="90" rx="12" fill="#fff3f2" stroke="#e5aaa4"/>
${text(600,1594,['附录 D 的独立对照（不是上面的主部署流程）'],22,700)}
${text(600,1626,['SONIC 关节命令 → online IK 覆盖 / 叠加部分关节 → 仿真执行；比较精度与稳定性'],20)}
</g></svg>`;
const mxStyle='rounded=1;whiteSpace=wrap;html=0;fontSize=21;spacing=12;strokeColor=#94a3b8;fontColor=#152334;';
let cells='<mxCell id="0"/><mxCell id="1" parent="0"/>';
cells+=`<mxCell id="title" value="${esc('EgoHumanoid-V2 完整流程（解释图，非论文原图）')}" style="text;html=0;fontSize=29;align=left;" vertex="1" parent="1"><mxGeometry x="45" y="15" width="1110" height="55" as="geometry"/></mxCell>`;
for(const g of groups)cells+=`<mxCell id="${g.id}" value="${esc(g.title)}" style="swimlane;html=0;startSize=58;horizontal=1;fontSize=23;rounded=1;fillColor=${g.color};strokeColor=#cbd5e1;" vertex="1" parent="1"><mxGeometry x="${g.x}" y="${g.y}" width="${g.w}" height="${g.h}" as="geometry"/></mxCell>`;
for(const n of nodes){const g=groups.find(g=>g.id===n.parent);cells+=`<mxCell id="${n.id}" value="${esc(n.lines.join('\n'))}" style="${mxStyle}fillColor=${n.color};" vertex="1" parent="${n.parent}"><mxGeometry x="${n.x-g.x}" y="${n.y-g.y}" width="${n.w}" height="${n.h}" as="geometry"/></mxCell>`;}
edges.forEach((e,i)=>{const interior=e[2].slice(1,-1);const a=nodes.find(n=>n.id===e[0]),b=nodes.find(n=>n.id===e[1]);const first=e[2][0],last=e[2].at(-1);cells+=`<mxCell id="edge${i}" value="${esc(e[3]||'')}" edge="1" parent="1" source="${e[0]}" target="${e[1]}" style="edgeStyle=orthogonalEdgeStyle;rounded=0;endArrow=block;strokeColor=#64748b;fontSize=18;exitX=${(first[0]-a.x)/a.w};exitY=${(first[1]-a.y)/a.h};entryX=${(last[0]-b.x)/b.w};entryY=${(last[1]-b.y)/b.h};"><mxGeometry relative="1" as="geometry">${interior.length?`<Array as="points">${interior.map(p=>`<mxPoint x="${p[0]}" y="${p[1]}"/>`).join('')}</Array>`:''}</mxGeometry></mxCell>`;});
cells+=`<mxCell id="note" value="${esc('预先准备：已有 SONIC；响应 MLP 另行训练并冻结。\n附录 D 独立对照：SONIC 命令 → online IK 覆盖/叠加部分关节 → 仿真；不是主部署流程。')}" style="${mxStyle}fillColor=#fff3f2;" vertex="1" parent="1"><mxGeometry x="25" y="1560" width="1150" height="90" as="geometry"/></mxCell>`;
const xml=`<mxGraphModel adaptiveColors="auto" page="1" pageWidth="1200" pageHeight="1675"><root>${cells}</root></mxGraphModel>`;
fs.writeFileSync(path.join(dir,'full-pipeline.svg'),svg+'\n');
fs.writeFileSync(path.join(dir,'full-pipeline.drawio'),xml+'\n');
console.log('Generated editable .drawio + same-geometry SVG preview.');
