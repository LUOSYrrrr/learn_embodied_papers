// Scoped, idempotent integration into the existing Fast-WAM and VPP2 notes.
import fs from 'node:fs';
const fastPath='papers/fast-wam.html';
let fast=fs.readFileSync(fastPath,'utf8');
fast=fast.replaceAll('延迟约 190ms（因为是并行去噪，比 IDM 快）','延迟约 580ms（联合去噪，比 IDM 的 810ms 快）');
fast=fast.replaceAll('Fast-WAM-Joint<span class="verdict-tag fast">190ms</span>','Fast-WAM-Joint<span class="verdict-tag fast">580ms</span>');
fast=fast.replaceAll('单次前向直出动作','当前帧表征只提取一次，再进行 10 步动作去噪');
fast=fast.replaceAll('跳过视频生成，单次前向，190ms','跳过未来视频生成，当前帧一次前向加动作去噪，190ms');
fast=fast.replaceAll('实机成功率约 80%+，完成时间约 160s','实机成功率约 75%，完成时间约 150s（原图估读，非原始计数）');
fast=fast.replaceAll('在没有 embodied pretraining 的变体中表现最佳，且延迟最低','相较 Joint / IDM 延迟更低，但 IDM 的任务成功率更高；预训练 π₀.₅ 是这项真机实验最强对照');
fast=fast.replaceAll('Fast-WAM-IDM 在实机任务上成功率最高（～88%）','Fast-WAM-IDM 在 Fast-WAM 家族中真机成功率最高（图示约 90%；预训练 π₀.₅ 仍更高）');
// Three variants are alternatives, not an executable three-stage pipeline.
fast=fast.replaceAll('变体 A：Fast-WAM-Joint（推理最重）','变体 A：Fast-WAM-Joint（联合去噪）');
fast=fast.replaceAll('这个结果会交给下一步“变体 B：Fast-WAM-IDM（推理最慢）”继续处理。','该变体直接输出动作；IDM 是另一套对照方法，不是它的下游。');
fast=fast.replaceAll('图中下一环节是“变体 B：Fast-WAM-IDM（推理最慢）”。','图中 B、C 是并列对照，不是执行顺序。');
fast=fast.replaceAll('来自上一步“变体 B：Fast-WAM-IDM（推理最慢）”的产物：一个或多个候选未来、动作或轨迹，以及必要的中间状态。本步骤还会按论文设置读取当前条件、时间步或训练信号。','当前观测和语言条件；Fast-WAM 不接收 IDM 的输出，也不读取未来视频 token。');
fast=fast.replaceAll('这个结果会交给下一步“对照组：w.o. video co-train（训练缺失）”继续处理。','该变体输出动作；w.o. video co-train 是训练消融，不是下游步骤。');
fast=fast.replaceAll('图中下一环节是“对照组：w.o. video co-train（训练缺失）”。','该对照只移除训练期视频损失。');
if(!fast.includes('id="vpp2-comparison"')){
  fast=fast.replace('<link href="../assets/css/style.css" rel="stylesheet"/>','<link href="../assets/css/style.css" rel="stylesheet"/><link href="../assets/css/humanoid-reading.css" rel="stylesheet"/>');
  const fragment=`<section class="series-audit" id="vpp2-comparison">
<div class="kicker">2026-10-23 · 固定 v2 的补充核读</div><h2>与 VPP2 对照：到底删掉了哪条信息通路？</h2>
<p>Fast-WAM 主变体的 action tokens 在<strong>训练与推理时都看不到 future-video tokens</strong>。当前 clean frame 也不能从未来组读取信息，避免绕路泄漏。推理无需实例化未来视频，但动作仍要做 10 步去噪，不能写成“整个策略一步直出动作”。</p>
<div class="eval-table-wrap"><table class="eval-table"><caption>paper · 2603.16666v2，§3–4</caption><thead><tr><th>设置</th><th>视频和动作如何交互</th><th>同文延迟</th></tr></thead><tbody><tr><td>Joint</td><td>未来视频与动作共同去噪</td><td>580 ms</td></tr><tr><td>IDM</td><td>先生成未来视频，再条件化动作</td><td>810 ms</td></tr><tr><td>Fast-WAM</td><td>当前帧表征一次提取 + 10 步动作去噪</td><td>190 ms</td></tr><tr><td>VPP2（另一篇）</td><td>保留一步未来预测，动作读取未来 KV</td><td>约 220 ms；硬件信息不足，不与此表同机排名</td></tr></tbody></table></div>
<div class="eval-table-wrap"><table class="eval-table"><caption>仿真协议</caption><thead><tr><th>Benchmark</th><th>训练与评测</th><th>结果与边界</th></tr></thead><tbody><tr><td>RoboTwin 2.0 Full</td><td>2,500 Clean + 25,000 Random 训练；每任务每条件 100 trials</td><td>Clean 91.88%，Random 91.78%；Random 已在训练分布内。</td></tr><tr><td>LIBERO</td><td>4 suites、40 tasks、共 2,000 评测试验</td><td>平均 97.6%；Joint 98.5、IDM 98.0，Fast-WAM 不是每项最高。</td></tr></tbody></table></div>
<div class="eval-table-wrap"><table class="eval-table"><caption>分维度 OOD：不要把数据增强评测当零样本迁移</caption><thead><tr><th>维度</th><th>原文支持</th><th>未支持</th></tr></thead><tbody><tr><td>环境随机化</td><td>Full 训练同时包含 Clean 与 Random</td><td>不能代替 Clean-only → Random 的泛化成绩。</td></tr><tr><td>未见任务 / 本体</td><td>评测适配后的基准策略与 R1-Lite 毛巾任务</td><td>没有仅凭这些结果证明任意未见任务或全身人形零样本迁移。</td></tr></tbody></table></div>
<div class="eval-table-wrap"><table class="eval-table"><caption>真机与部署</caption><thead><tr><th>设置</th><th>证据</th><th>限制</th></tr></thead><tbody><tr><td>Galaxea R1-Lite 叠毛巾</td><td>60 h 遥操作；Figure 4 中预训练 π₀.₅ 最强，Fast-WAM 比无 video co-train 的 10% 好得多</td><td>除正文明确数字外，其余点为原图估读；未提供完整 trial 数，不推算成功计数。</td></tr><tr><td>延迟</td><td>RTX 5090；190 ms vs IDM 810 ms，约 4.26 倍</td><td>推理延迟不是关节控制周期，也不是端到端闭环安全性证明。</td></tr></tbody></table></div>
<p><strong>结论范围：</strong>视频辅助训练在本配方中很有价值，不等于所有 WAM 都不需要未来预测。VPP2 改变了视频预训练、数据、模型规模与蒸馏配方，不能把它和这里的消融当成只有一个变量不同。</p>
<p class="source"><a href="vpp2.html#comparison">VPP2 信息通路对照</a> · <a href="humanoid-data-to-wam.html">返回六篇串读</a> · <a href="https://arxiv.org/abs/2603.16666v2">固定论文版本</a></p></section>\n`;
  const marker='<div class="section" id="vla-link">';
  if(!fast.includes(marker))throw Error('Fast-WAM marker changed');
  fast=fast.replace(marker,fragment+marker);
}
fs.writeFileSync(fastPath,fast);
const vppPath='papers/vpp2.html';
let vpp=fs.readFileSync(vppPath,'utf8');
if(!vpp.includes('id="humanoid-chain-audit"')){
  const marker='<section class="reading-section" aria-labelledby="connections">';
  if(!vpp.includes(marker))throw Error('VPP2 marker changed');
  vpp=vpp.replace(marker,`<section class="reading-section" id="humanoid-chain-audit"><h2>补充核读 · 与人体数据—控制链路的连接</h2><p>2026-10-23 复核完整 21 页 PDF：VPP2 的事件视频先验、未来条件与动作专家可作为高层策略参考，但本文主要操控证据不能直接外推成人形全身控制。若动作改成 SONIC token，必须重新定义时间窗口、状态输入、目标 controller 与监督标签。</p><p><strong>保留四条边界：</strong>大规模训练的总小时数未在本版充分披露；ALOHA 的零目标任务微调不等于未见本体；58.5% 缺完整 trial 数，不能倒推样本量；0.22 s 的部署硬件说明不足，不能与 Fast-WAM 的 RTX 5090 190 ms 作严格速度排名。</p><p>“保护视频先验”是训练设计目标；早期冻结、LoRA 与后续训练阶段要分别看，不应写成 backbone 全程完全冻结。五任务高层规划实验的 27.6→57.6 也不是所有 RoboDojo 任务的统一增益。</p><div class="source-links"><a href="humanoid-data-to-wam.html">六篇链路总览</a><a href="fast-wam.html#vpp2-comparison">Fast-WAM 补充核读</a><a href="sonic.html#interface-audit">SONIC 控制接口</a></div></section>`+marker);
}
fs.writeFileSync(vppPath,vpp);
console.log('Integrated Fast-WAM corrections and VPP2 chain audit.');
