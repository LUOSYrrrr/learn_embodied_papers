#!/usr/bin/env python3
"""Add a mechanism/reproduction appendix to concise WAM-route notes."""

from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parents[1]

GROUPS = {
"latent": dict(rep="未来观测先被压到 latent；动作不是人工标签，而是解释相邻状态变化的低维变量。", signal="重建/预测未来提供自监督，action bottleneck、量化或先验决定 latent 是否真的可控。", deploy="预训练学出的 latent action 必须再对齐机器人动作，或作为规划/策略的中间接口。", metric="不能只看视频重建；还要测 action 可分性、可组合性和下游控制成功率。", checks=["latent 维度或 codebook 大小时是否出现坍缩", "前向模型和逆向模型是否偷看目标帧信息", "latent-to-robot 对齐用了多少标注动作", "开环预测误差如何传到闭环策略", "不同 embodiment 是否共享同一 action space"]),
"cascaded": dict(rep="第一阶段先产生未来图像/latent 或轨迹候选，第二阶段再由 inverse dynamics、planner 或 controller 提取动作。", signal="视频生成损失负责‘未来像不像’，动作损失负责‘控制能否取回’，两种目标通常分开训练。", deploy="模块可以复用强视频模型，但推理要串行经过预测与动作解码，延迟和误差累积是主要代价。", metric="同时报告未来预测、动作误差和闭环成功率；只展示漂亮视频不足以证明控制有效。", checks=["预测器是否使用动作条件或纯观察条件", "IDM 输入了几帧、是否存在信息泄漏", "视频候选采样数量与推理延迟", "两阶段误差是否分别消融", "失败来自视觉幻觉还是动作解码"]),
"joint_ar": dict(rep="同一自回归序列中交织视觉/状态 token 与动作 token，让世界预测和控制共享上下文。", signal="next-token loss 同时监督未来状态与动作；token 顺序、mask 和损失权重决定两个任务谁主导。", deploy="统一模型便于长上下文和语言条件推理，但逐 token 解码会限制实时控制频率。", metric="除动作成功率外，应测未来 token 质量、长程一致性及不同解码顺序的消融。", checks=["图像、语言、动作 token 的排列与 attention mask", "动作量化误差和词表占用率", "状态/动作损失权重是否平衡", "teacher forcing 与闭环推理的分布差", "KV cache 后的真实控制延迟"]),
"joint_diff": dict(rep="未来视觉 latent 与连续动作在一次 diffusion/flow 过程中联合生成，或共享噪声时间与 Transformer。", signal="去噪/速度场目标同时约束状态和动作；cross-modal conditioning 保证二者描述同一个未来。", deploy="耦合更紧、动作一致性更好，但视频 latent 昂贵，常需少步采样、蒸馏或缓存。", metric="要拆开报告视觉、动作、state-action consistency 与端到端成功率。", checks=["视觉与动作是否共享噪声时间表", "两种模态的尺度归一化与 loss 权重", "动作 chunk 在去噪链中的 mask", "采样步数对延迟和成功率的影响", "未来视频失败时动作是否仍可执行"]),
"efficiency": dict(rep="核心 world/action model 不变，主要修改 token、缓存、记忆、蒸馏或跨模态输入，让 rollout 更快或信息更全。", signal="训练通常保留原任务损失，再增加 cache consistency、蒸馏、记忆压缩或模态对齐约束。", deploy="收益必须落到端到端延迟、吞吐、显存和闭环频率，而不是只报单个网络 FLOPs。", metric="同一硬件、同一预测长度、同一采样步数下比较质量—速度 Pareto。", checks=["缓存命中率与失效条件", "蒸馏教师和学生是否使用相同条件", "多模态缺失时的退化策略", "长程记忆增长与显存上界", "端到端延迟是否包含视觉编码和动作解码"]),
"real2sim": dict(rep="真实视频/图像被重建成可渲染场景，再补几何、碰撞、机器人和物理参数形成 simulator。", signal="视觉重建优化外观；系统辨识、接触或策略回报约束物理可用性，两者不是同一目标。", deploy="Gaussian Splatting 适合照片级观测，但接触通常仍依赖 mesh、proxy geometry 或独立 physics engine。", metric="需要分开测渲染逼真、几何误差、动力学偏差与 sim-to-real 策略成功率。", checks=["相机位姿和尺度如何标定", "GS 到碰撞几何如何转换", "动态物体和遮挡怎样建模", "物理参数是否通过真实轨迹辨识", "策略是否只适配了视觉而非动力学"]),
"evaluation": dict(rep="评测对象不是单帧画质，而是生成世界在时间、物体身份、物理规律、动作条件和下游控制上的一致性。", signal="自动指标、VLM judge、人类偏好和任务执行各自覆盖不同误差，任何单一分数都有盲区。", deploy="指标要能定位模型失败并指导迭代，否则高相关性但不可解释的总分价值有限。", metric="至少分视觉质量、时间一致、物理合理、可控性与动作可译性五层报告。", checks=["评分器是否见过被评模型的数据分布", "VLM judge 与人类标注的一致性", "物理题是否存在文本捷径", "长视频评分是否被短片段平均掩盖", "指标提升是否对应下游控制提升"]),
"video": dict(rep="视频 DiT 在压缩 latent 上建模时空 token，并用文本、首帧或其他条件控制生成。", signal="训练目标可能是 diffusion noise、velocity 或 flow matching；时空 attention 决定运动和身份如何传播。", deploy="WAM 会在此基础上额外加入动作条件或动作头，因此先要理解视频 backbone 的 tokenization 与采样成本。", metric="画质、文本一致、运动幅度、长程身份和采样速度要分开测。", checks=["3D VAE 的空间与时间压缩率", "时空 patch 与 positional encoding", "全注意力、分解注意力或窗口注意力", "条件注入与 CFG 方式", "采样器、步数和实际吞吐"]),
}

ITEMS = {
"motus":("latent","把 latent action 作为可组合运动单位，重点检查动作瓶颈是否跨视频保持语义。"), "flare":("latent","把表征预测与动作发现结合，关键是 latent 是否同时服务未来预测和控制。"), "villa-x":("latent","从大规模无标注视频发现动作，再迁移到具身策略；数据分布和对齐成本是阅读重点。"), "vla-jepa":("latent","JEPA 表征空间中的动作条件预测应与像素生成路线分开理解。"),
"unipi":("cascaded","先规划未来视觉，再用逆动力学得到动作，是 cascaded WAM 的标准参照。"), "avdc":("cascaded","视频扩散负责生成目标一致的未来，动作解码器承担从视觉计划到控制的落地。"), "vidar":("cascaded","关注视觉规划和动作恢复的接口，以及长时域误差如何累积。"), "vpp":("cascaded","把视频预测作为 policy prior；关键对照是直接策略与视觉规划器的闭环差异。"),
"gr-1":("joint_ar","视觉、语言与动作 token 在一个序列中共同建模，是 joint autoregressive 路线的早期代表。"), "gr-2":("joint_ar","在 GR-1 基础上扩大视频数据与生成能力，阅读时重点看预训练数据如何转成动作收益。"), "worldvla":("joint_ar","把世界建模 token 纳入 VLA 推理，重点看视觉预测是否真正改善动作而非仅作辅助损失。"), "cot-vla":("joint_ar","用视觉 chain-of-thought 产生中间未来表征；要检查中间推理带来的延迟与因果贡献。"),
"pad":("joint_diff","动作与感知预测共同去噪；核心是联合目标能否保持物理一致而不牺牲动作精度。"), "uwm":("joint_diff","统一生成未来和动作，需关注论文元数据为技术报告，以及视觉—动作 loss 的真实耦合方式。"), "uva":("joint_diff","联合动作与未来 latent 的扩散路线，重点检查多模态尺度和采样步数。"), "dreamzero":("joint_diff","用生成式世界/动作模型实现更少真机数据的策略学习，想象质量与控制收益要分别验证。"), "lingbot-va":("joint_diff","面向真实机器人视频—动作联合生成，阅读重点是实时性和长程一致性。"),
"flash-wam":("efficiency","目标是降低 WAM rollout 成本；必须同时看速度、预测质量和策略成功率。"), "efficient-wam":("efficiency","围绕更少计算的 world-action generation，注意理论 FLOPs 与端到端延迟的差别。"), "c3ache":("efficiency","缓存复用是主贡献；关键是哪些 token 可复用、状态变化何时让缓存失效。"), "himem-wam":("efficiency","层次记忆支持长程 WAM；要追踪写入、检索、压缩与遗忘机制。"), "omnivta":("efficiency","把视觉、触觉与动作放进统一时序模型；多模态时间同步和缺失模态退化比单纯加输入更重要。"), "fawam":("efficiency","力/触觉增强 WAM，重点是接触信号如何与视觉 latent 对齐并改善动作后果预测。"),
"splatsim":("real2sim","用 Gaussian Splatting 缩小视觉 sim-to-real gap，但策略是否依赖正确接触仍要单独验证。"), "gsworld":("real2sim","照片级闭环操作 simulator，核心是渲染表示与物理碰撞层如何衔接。"), "gaussgym":("real2sim","把 GS 场景用于从像素学习 locomotion；关注动态相机、地面接触和真实部署校准。"), "4d-gaussian-splatting":("real2sim","4DGS 是动态渲染层而非完整 world model；动作因果和接触物理需要额外模块。"),
"videophy":("evaluation","物理常识评测强调动作与物体状态变化，而非单纯 FVD。"), "vbench-2":("evaluation","把视频内在一致性拆成多维指标；阅读时检查评分器是否存在语义捷径。"), "worldmodelbench":("evaluation","直接把视频生成器当 world model 审核，重点是长程物理和交互后果。"), "physics-iq":("evaluation","用物理原则问题检查生成模型理解，需区分视觉识别、文本知识和真实动力学。"), "worldscore":("evaluation","统一评测世界生成质量、动态和可控性；总分之外更应看分维度失败。"), "worldsimbench":("evaluation","动作可译性是亮点：生成未来若无法恢复正确控制，就不能算好 simulator。"),
"generation/open-sora":("video","开源 Video DiT 系统适合学习数据、VAE、时空 attention 与训练工程如何组合。"),
}

for rel, (group, position) in ITEMS.items():
    path = ROOT / "papers" / f"{rel}.html"
    text = path.read_text()
    if 'id="deep-dive"' in text:
        continue
    g = GROUPS[group]
    checks = ''.join(f'<li>{escape(x)}</li>' for x in g['checks'])
    appendix = f'''<h2 id="deep-dive">补充精读：从模块图走到可复现系统</h2><div class="cn-read"><div class="cn-label">为什么还要再往下一层</div><p>前面的主体已经说明论文做了什么，这一节把它放回整条 WAM 路线，补上表示、训练信号、部署代价和评测闭环。{escape(position)}</p></div><div class="module-grid"><div class="module-card"><div class="module-card-name">REPRESENTATION</div><div class="module-card-title">模型到底表示什么</div><div class="module-card-desc">{escape(g['rep'])}</div></div><div class="module-card"><div class="module-card-name">LEARNING SIGNAL</div><div class="module-card-title">监督怎样进入</div><div class="module-card-desc">{escape(g['signal'])}</div></div><div class="module-card"><div class="module-card-name">DEPLOYMENT</div><div class="module-card-title">闭环时付出什么</div><div class="module-card-desc">{escape(g['deploy'])}</div></div><div class="module-card"><div class="module-card-name">EVALUATION</div><div class="module-card-title">什么证据才算数</div><div class="module-card-desc">{escape(g['metric'])}</div></div></div><h3>复现时必须回答的五个问题</h3><ul style="color:var(--text2);line-height:1.8">{checks}</ul><div class="callout blue"><div class="callout-label">在路线中的位置</div><p>{escape(position)}</p></div>'''
    path.write_text(text.replace('</main>', appendix + '</main>', 1))
    print(path)

MORE = {
"latent": dict(flow=["从视频采样上下文帧与目标帧，先固定观测时间间隔。", "inverse model 把状态变化压成 latent action，瓶颈必须阻止逐像素复制。", "forward predictor 接收上下文与 latent，重建未来表征或图像。", "用量化、先验或一致性约束让 latent 可复用，而非每段视频一个私有编码。", "迁移阶段再用少量机器人轨迹把 latent 映射到真实控制。"], wrong=[("重建越好，动作越好","模型可能把外观细节塞进 latent，却没有可执行语义。"),("无标签视频等于免费动作数据","它只提供状态变化，动作方向和机器人坐标仍需对齐。"),("latent 越小越可控","过小会丢技能，过大则容易绕过动作瓶颈。")]),
"cascaded": dict(flow=["给当前观测、语言目标或目标图像建立规划条件。", "视频/latent 预测器采样一个或多个未来候选。", "用目标一致性、价值或可达性筛掉坏候选。", "IDM/控制器把相邻预测状态翻译成 action chunk。", "真实环境执行后重新观测并滚动规划，限制开环漂移。"], wrong=[("视频逼真就能控制","视觉合理不代表动作可达或接触正确。"),("两阶段更易解释所以一定更稳","模块接口会叠加分布偏移与延迟。"),("IDM 只是小解码头","它承担从视觉差分到机器人动力学的关键落地。")]),
"joint_ar": dict(flow=["把图像压成视觉 token，把连续动作量化为动作 token。", "按设计好的序列顺序拼入语言、历史、未来与动作。", "attention mask 决定哪些 token 能看见真实未来，避免训练泄漏。", "next-token loss 同时更新视觉预测与动作分布。", "部署时自回归生成动作，并选择是否同时滚出未来 token。"], wrong=[("统一 token 就自动统一语义","量化尺度和 loss 权重仍可能让模态彼此割裂。"),("未来 token 是可解释思维链","它可能只是提高动作预测的辅助隐变量。"),("参数共享一定降低延迟","自回归长度可能抵消网络共享带来的收益。")]),
"joint_diff": dict(flow=["视觉与动作各自归一化并编码到联合 latent。", "随机采样噪声时间，对两种模态同时加噪或构造插值。", "共享 Transformer 通过跨模态 attention 预测噪声/速度。", "损失权重协调高维视觉 latent 与低维动作，防止视觉主导。", "采样得到一致的未来与动作，再在闭环中执行 action chunk。"], wrong=[("联合生成一定比级联准确","耦合能提高一致性，也会让优化和采样更重。"),("视频 loss 大就该给更大权重","高维视觉天然数值大，需按语义重要性校准。"),("减少采样步只影响画质","动作精度和闭环稳定性也会随之变化。")]),
"efficiency": dict(flow=["先固定原模型、输入长度、预测长度和采样器作为基线。", "定位主要成本属于视觉编码、attention、去噪还是动作解码。", "加入缓存、蒸馏、记忆压缩或多模态适配模块。", "逐层核对近似是否改变条件信息或时间依赖。", "在相同硬件上同时测延迟、吞吐、显存、质量与成功率。"], wrong=[("FLOPs 下降等于机器人更快","数据搬运、VAE 与控制接口可能才是瓶颈。"),("缓存越多越好","环境变化会让旧特征失效并引入陈旧预测。"),("多模态输入总会提升","时间不同步或噪声传感器可能让性能更差。")]),
"real2sim": dict(flow=["从真实视频估计相机轨迹、尺度和静态/动态区域。", "重建 Gaussian/NeRF 外观，先确保新视角渲染稳定。", "生成或拟合 mesh/proxy collider，补齐不可见几何。", "通过轨迹或系统辨识估计摩擦、质量、关节和接触参数。", "在模拟器训练策略，再用相同相机与控制接口回到真实环境验证。"], wrong=[("照片级渲染等于数字孪生","渲染只覆盖观测分布，不自动给出物理。"),("视觉 sim-to-real 好就够了","接触任务常由几何和摩擦偏差决定。"),("4D 表示就是 world model","它表示动态外观，但未必能预测动作因果。")]),
"evaluation": dict(flow=["先定义 world model 的目标用途：生成、预测、规划还是控制。", "构造只改变一个物理或动作因素的对照样本。", "分别运行像素指标、感知模型、VLM judge 与人类标注。", "对长视频分阶段定位身份、时间和物理错误。", "把评分与动作恢复、规划或真实任务成功率做相关性验证。"], wrong=[("一个总分能代表 world model","不同能力可能在加权平均中相互抵消。"),("VLM judge 客观且免费","judge 有自身训练偏差和提示敏感性。"),("FVD 低说明懂物理","分布相似不能证明单个交互遵守因果。")]),
"video": dict(flow=["先用 3D VAE 把视频压到时空 latent，记录压缩率。", "把 latent 切成时空 patch，并加入文本或首帧条件。", "DiT 在噪声时间上预测 noise、velocity 或 flow field。", "时空 attention 传播运动与身份，mask 决定可见上下文。", "采样器积分回干净 latent，再由 VAE 解码视频。"], wrong=[("Video DiT 就是 WAM","没有动作条件与闭环接口时仍只是视频生成模型。"),("更大 VAE 压缩只影响画质","它也会抹掉接触和微小运动信号。"),("长视频靠增加帧数即可","attention 成本和误差累积会快速放大。")]),
}

for rel, (group, position) in ITEMS.items():
    path = ROOT / "papers" / f"{rel}.html"
    text = path.read_text()
    if 'id="engineering-notes"' in text:
        continue
    m = MORE[group]
    flow = ''.join(f'<li><strong>第 {i} 步：</strong>{escape(x)}</li>' for i, x in enumerate(m['flow'], 1))
    wrong = ''.join(f'<tr><th>{escape(a)}</th><td>{escape(b)}</td></tr>' for a, b in m['wrong'])
    section = f'''<h2 id="engineering-notes">工程化拆解：完整信息流与常见误读</h2><div class="cn-read"><div class="cn-label">把论文变成实现清单</div><p>这一节不增加新名词，而是把方法还原成从输入到闭环评测的五步流水线。逐步核对后，才能判断论文的增益来自模型、数据、计算预算还是评测口径。</p></div><ol style="color:var(--text2);line-height:1.85">{flow}</ol><h3>三种最容易踩的认知坑</h3><table style="width:100%;border-collapse:collapse;font-size:13px"><tbody>{wrong}</tbody></table><div class="quiz" data-correct="d" data-explain="世界/动作模型需要同时闭合表示、训练信号、推理成本和下游任务四条证据链。" data-explain-wrong="单一画质或单一成功率都不足以解释整个系统。"><div class="q-label">理解检查 · 系统</div><div class="q-text">判断这篇工作是否真正推进 WAM，最完整的证据是什么？</div><div class="q-options"><button class="q-opt" data-k="a">只看生成视频</button><button class="q-opt" data-k="b">只看模型参数量</button><button class="q-opt" data-k="c">只看离线动作误差</button><button class="q-opt" data-k="d">表示、训练、效率与闭环任务共同成立</button></div><div class="q-feedback"></div></div>'''
    path.write_text(text.replace('</main>', section + '</main>', 1))
