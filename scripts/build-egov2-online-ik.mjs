import fs from 'node:fs';
const dir='assets/diagrams/egohumanoid-v2';
fs.mkdirSync(dir,{recursive:true});
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll('\n','&#xa;');
const nodes=[
 ['token',60,110,310,95,['给定运动轨迹的','SONIC token zₜ'],'#eaf3ff'],
 ['state',440,110,310,95,['当前机器人反馈','姿态 / 控制状态'],'#eaf3ff'],
 ['target',820,110,320,95,['当前帧的','手 / 脚目标'],'#eaf3ff'],
 ['sonic',60,285,500,100,['SONIC 控制器','结合 token 与自身反馈，产生协调身体命令'],'#f0eefe'],
 ['ik',680,285,460,100,['在线 IK 求解','根据末端目标与几何，求指定关节目标'],'#fff1d8'],
 ['su',60,445,500,85,['SONIC 原本要发送的','身体关节目标 uˢ'],'#f0eefe'],
 ['iu',680,445,460,85,['IK 给出的替代关节目标 uᴵᴷ','不是重新编码得到的新 SONIC token'],'#fff1d8'],
 ['mix',220,620,760,105,['关键：按 A / B / C 规则组合关节命令','部分关节用 IK，其他关节保留 SONIC；B 再加平衡贡献'],'#ffe5df'],
 ['sim',220,820,760,85,['发送组合后的关节目标 → 仿真机器人执行','这里已经不是原封不动的 SONIC 输出'],'#eaf7f0'],
 ['measure',220,990,760,95,['测量实际身体状态与手 / 脚位置','记录末端误差、身体倾角、初始化摔倒与 fall events'],'#eaf7f0'],
];
const edges=[
 ['token','sonic',[[215,205],[215,285]]],
 ['state','sonic',[[595,205],[595,335],[560,335]]],
 ['state','ik',[[595,205],[595,335],[680,335]]],
 ['target','ik',[[980,205],[980,245],[910,245],[910,285]]],
 ['sonic','su',[[310,385],[310,445]]],
 ['ik','iu',[[910,385],[910,445]]],
 ['su','mix',[[310,530],[310,575],[400,575],[400,620]]],
 ['iu','mix',[[910,530],[910,575],[800,575],[800,620]]],
 ['mix','sim',[[600,725],[600,820]]],
 ['sim','measure',[[600,905],[600,990]]],
 ['measure','state',[[980,1037],[1170,1037],[1170,85],[595,85],[595,110]]],
];
const txt=(x,y,lines,size=23,weight=400,anchor='middle')=>`<text x="${x}" y="${y}" text-anchor="${anchor}" font-size="${size}" font-weight="${weight}">${lines.map((l,i)=>`<tspan x="${x}" dy="${i?32:0}">${esc(l)}</tspan>`).join('')}</text>`;
const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1465" viewBox="0 0 1200 1465" role="img" aria-labelledby="title desc"><title id="title">附录 D：online IK 如何接入 SONIC 执行环</title><desc id="desc">解释图，非论文原图。两条命令分支在发送前组合，不是修改参考后重新编码 token。机器人执行反馈回到后续控制；三种组合未能稳定跟踪。</desc><defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10Z" fill="#64748b"/></marker></defs><rect width="1200" height="1465" fill="white"/><g font-family="PingFang SC,Noto Sans CJK SC,Arial,sans-serif" fill="#152334">
${txt(45,43,['Online IK：在执行当下，组合两套关节命令'],30,700,'start')}${txt(45,73,['解释性接线图 · 对应 Appendix D，不是 VLA 推理图；完整软件调度与反馈字段未逐项公开'],17,400,'start')}
${edges.map(e=>`<path d="${e[2].map((p,i)=>`${i?'L':'M'}${p[0]} ${p[1]}`).join(' ')}" fill="none" stroke="#64748b" stroke-width="2.5" marker-end="url(#a)"/>`).join('')}
${nodes.map(([id,x,y,w,h,lines,color])=>`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="12" fill="${color}" stroke="#94a3b8" stroke-width="1.5"/>${txt(x+w/2,y+h/2-16+8,lines,w<400?23:21)}`).join('')}
${txt(630,778,['直接改变发送的关节目标'],20,600,'start')}${txt(630,955,['物理响应 ≠ IK 数学解'],20,600,'start')}
${txt(1136,680,['反馈进入下一时刻'],18,400,'end')}
<rect x="60" y="1145" width="1080" height="200" rx="12" fill="#f5f7fa" stroke="#cbd5e1"/>
${txt(85,1181,['三种接法（Table 11）'],23,700,'start')}
${txt(85,1225,['A：手任务 IK 改手臂+腰；脚任务改双腿；其他关节用 SONIC。'],21,400,'start')}
${txt(85,1270,['B：与 A 相同，再加入 SONIC 的 balance contribution。'],21,400,'start')}
${txt(85,1315,['C：手任务只改手臂；脚任务只改右腿；其他关节用 SONIC。'],21,400,'start')}
${txt(60,1386,['与 offline K 的分叉：K 改参考 → 编码 token → 经 SONIC 执行；这里改的是执行命令。'],21,700,'start')}
${txt(60,1423,['注意：仍有反馈不代表必然稳定；这是 60 次仿真诊断，并非论文主方法的真机部署链。'],20,400,'start')}
</g></svg>`;
let cells='<mxCell id="0"/><mxCell id="1" parent="0"/>';
for(const [id,x,y,w,h,lines,color] of nodes)cells+=`<mxCell id="${id}" value="${esc(lines.join('\n'))}" style="rounded=1;whiteSpace=wrap;html=0;fontSize=21;fillColor=${color};strokeColor=#94a3b8;fontColor=#152334;" vertex="1" parent="1"><mxGeometry x="${x}" y="${y}" width="${w}" height="${h}" as="geometry"/></mxCell>`;
edges.forEach(([s,t,pts],i)=>{const a=nodes.find(n=>n[0]===s),b=nodes.find(n=>n[0]===t),first=pts[0],last=pts.at(-1);cells+=`<mxCell id="e${i}" edge="1" parent="1" source="${s}" target="${t}" style="edgeStyle=orthogonalEdgeStyle;endArrow=block;strokeColor=#64748b;exitX=${(first[0]-a[1])/a[3]};exitY=${(first[1]-a[2])/a[4]};entryX=${(last[0]-b[1])/b[3]};entryY=${(last[1]-b[2])/b[4]};"><mxGeometry relative="1" as="geometry"><Array as="points">${pts.slice(1,-1).map(p=>`<mxPoint x="${p[0]}" y="${p[1]}"/>`).join('')}</Array></mxGeometry></mxCell>`;});
for(const [id,y,h,label] of [['title',10,70,'Online IK：执行当下组合关节命令（解释图，非论文原图）'],['variants',1145,200,'Table 11：A 手臂+腰 / 双腿由 IK 控制；B 在 A 上加 SONIC balance contribution；C 仅手臂 / 右腿由 IK 控制。其余关节由 SONIC 控制。'],['boundary',1370,75,'附录 D 的独立仿真诊断，不是 VLA 推理流程。K 改参考再经 SONIC；online IK 改发送的关节命令。']])cells+=`<mxCell id="${id}" value="${esc(label)}" style="rounded=1;whiteSpace=wrap;html=0;fontSize=23;fillColor=#f5f7fa;" vertex="1" parent="1"><mxGeometry x="60" y="${y}" width="1080" height="${h}" as="geometry"/></mxCell>`;
fs.writeFileSync(`${dir}/online-ik-loop.svg`,svg+'\n');
fs.writeFileSync(`${dir}/online-ik-loop.drawio`,`<mxGraphModel adaptiveColors="auto" page="1" pageWidth="1200" pageHeight="1465"><root>${cells}</root></mxGraphModel>\n`);
console.log('Generated online IK loop, native draw.io + SVG preview.');
