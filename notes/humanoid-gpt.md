# Humanoid-GPT: Scaling Data and Structure for Zero-Shot Motion Tracking

> Qi, Chen, Liu, Lin et al. · 清华 + Galbot + SJTU + PKU · arXiv:2606.03985 · 2026-06
> 代码：https://github.com/GalaxyGeneralRobotics/Humanoid-GPT/
> 平台：Unitree G1（29 DoF）· 对比对象：SONIC（NVIDIA GEAR, arXiv:2511.07820，笔记见 `papers/sonic.html`）

---

## 一句话

把人形动作跟踪（motion tracking）当成 **GPT 式序列建模问题**：用 2B 帧动作语料训 ~300 个 PPO 专家，再用 DAgger 并行蒸馏进一个 causal Transformer，得到既敏捷（agile）又能零样本泛化（zero-shot）的单一跟踪器——并给出这个领域的 scaling law。

**它直接回应的问题**：之前的跟踪器都是浅层 MLP + 千万帧级数据，存在"敏捷性 vs 泛化性"的 trade-off（BeyondMimic/ASAP 敏捷但不零样本；TWIST/UniTracker 泛化但跟不动高动态动作）。论文主张这不是本质矛盾，而是**规模不够 + 架构不匹配**的症状。

---

## 核心配方（三个问题三个答案）

### ① 数据：2B 帧从哪来

- 聚合 AMASS + LAFAN1 + MotionMillion + PHUMA + 自采数据（含视频估计动作）
- GMR retarget 到 G1 的 29 DoF 关节空间；过滤掉物体交互类动作（坐椅子/游泳/爬楼梯）
- **时间扭曲增广（time-warping）**：每条序列统一加速/减速，数据量 ×5
- 最终 2B 帧 ≈ 此前跟踪器训练集（~7.2M 帧）的 **200 倍以上**

> ⚠️ 注意：2B 里含 ×5 增广，"净"动作量约 400M 帧量级；但首次系统性证明了**视频估计动作**（噪声大）在模型和数据都足够大时确实能帮助跟踪。

### ② 架构：causal Transformer 替代 MLP

- 每个时间步的 token = 当前本体感知状态 s_t ⊕ 参考姿态 q_ref_t
- 12 层 Transformer + **时间因果掩码（causal mask）**，历史窗口 H=32 帧（消融显示 64 帧还在涨，但计算量二次增长，取 32）
- 输出 per-joint PD target，50 Hz 控制环
- 三个尺寸：S=5.7M / B=22.1M / L=80.4M 参数

为什么 causal？在线跟踪**本来就看不到未来**——causal attention 与部署约束天然对齐。而且不同位置的 token 看到的历史长度不同，模型隐式学会了"位置不变的时序预测"，episode 开头历史稀缺时也稳。

### ③ 训练：专家 RL → DAgger 并行蒸馏（两阶段）

1. **HME 聚类**：用 Periodic Autoencoder 提取每关节的周期幅值/频率，聚合成 Harmonic Motion Embedding，K-Means 分 ~300-384 个 cluster（每个 1k–2k 序列）
2. **专家训练**：每个 cluster 训一个 PPO 专家（MuJoCo，keypoint 级 reward：位置/旋转/速度的指数惩罚 + 自碰撞/平滑度惩罚），只保留高保真专家
3. **蒸馏**：DAgger 框架，student 的整段历史输出被 teacher 的对应历史动作**并行监督**（一次前向监督 H 个位置，SmoothL1 loss）——这正是 Transformer 相对 MLP 的训练效率优势（HumanPlus 用了 Transformer 却拿标准 PPO 训，浪费了并行性）

**类比**：像 LLM 的"专家标注 → 监督微调"流水线——RL 专家相当于领域标注员，各自只精通自己的 cluster；Transformer 学生把 300 个偏科老师的知识合并成一个通才。也可以类比成 300 门课的 distillation-based 联合毕业考。

### 关键洞察：多样性和均衡缺一不可

HME 不只是聚类工具，还用来做 **diversity-aware、distribution-balanced 采样**。论文的结论很干净：
- 只有多样性、没有均衡 → 仍然过拟合高频动作模式
- 只有均衡、没有多样性 → 能力上限被锁死

---

## 实验结论速记

| 发现 | 证据 |
|---|---|
| Transformer 有 scaling law，MLP/TCN 早饱和 | Tab.2：GPT-L@2B 帧 SR=92.58%，MPKPE=40.99mm；TCN-L 同数据 SR=89.05% 但 MPKPE 差 30%+ |
| 大模型在小数据上会过拟合 | MLP-L@2M 帧（75.25%）反而不如 MLP-S（76.89%） |
| 数据边际收益 200M→2B 开始变小 | 当前模型容量下进入 data-limited regime |
| 真机零样本 | G1 上零微调跟未见过的舞蹈/功夫/打篮球/翻身起立，真机指标与仿真接近（Tab.3） |
| 大模型也能实时 | ONNX+TensorRT+C++ 流水线，RTX 4090 上端到端 <1.5ms（比 TWIST 快 ~5 倍） |
| 计算成本 | 共 ~15,000 GPU 时：专家 RL 12,000（4090）+ 蒸馏 3,000（H100）；部署只需学生模型 |

---

## 与 SONIC 的对比（同任务、同机器人、相反的押注）

两篇都是"把 motion tracking 当作 humanoid control 的基础任务来 scale"，都用 Unitree G1，都做了真机零样本验证——但在**怎么 scale**上押了相反的方向。Humanoid-GPT 在 Related Work 里直接点名：*"SONIC scales to 100M frames with an MLP controller, yet MLP capacity saturates as data grows."*

| 维度 | SONIC（NVIDIA GEAR） | Humanoid-GPT（清华/Galbot） |
|---|---|---|
| **核心论点** | tracking 是可 scale 的任务本身，MLP + 单阶段 PPO 直接堆算力/数据就行；重点做**应用接口** | 数据要 scale，**架构也要换**——MLP 会饱和，causal Transformer 才能继续吃数据 |
| **架构** | MLP encoder-decoder + FSQ 量化的 universal token space，1.2M→42M 参数 | GPT 式 causal Transformer（12 层，H=32），5.7M→80M 参数 |
| **训练范式** | **单阶段端到端 RL**：PPO + 重建/token/cycle 四个 loss 联合优化，asymmetric actor-critic | **两阶段**：~300 个 cluster 专家 PPO → DAgger 并行蒸馏成单一学生 |
| **数据** | 100M+ 帧 = 700 小时**纯 mocap**（50fps），质量高 | 2B 帧（含视频估计动作 + ×5 时间增广），量大但更噪 |
| **算力** | 21,000 GPU 时（128 GPU × 7 天，Isaac Lab） | ~15,000 GPU 时（MuJoCo 训专家 + H100 蒸馏） |
| **数据均衡** | 未做显式的多样性均衡采样 | HME 嵌入 + 均衡采样，是论文三大贡献之一 |
| **接口/下游** | **重头戏**：universal token space 统一 VR 遥操/视频/文本/音乐/**VLA** 输入；kinematic planner 做导航；VLA 驱动 loco-manipulation 5 个真机任务 | 纯 tracker，输入只有参考姿态；VLA/语言/视觉是 future work |
| **部署** | **Jetson 板载**推理（42M 模型，多速率架构） | RTX 4090 **外置**推理 <1.5ms（板载未验证） |
| **零样本表现** | 有零样本泛化（Humanoid-GPT 的 Tab.1 也承认其 zero-shot ✓） | 声称新的性能前沿：同时保持敏捷 + 零样本 |

### 我的读法：两篇其实回答的是不同问题

- **SONIC 回答"tracking 有什么用"**：它把大量篇幅花在接口上——FSQ universal token space 让 VLA、VR、视频、音乐都能驱动同一个策略。对做 VLA 方向的人来说，SONIC 的价值是**它定义了 VLA 与 whole-body controller 之间的接口层**（VLA 输出 token → tracker 执行），并真的用它跑通了 VLA 驱动的 loco-manipulation。
- **Humanoid-GPT 回答"tracking 怎么做得更好"**：它把大量篇幅花在 scaling 科学上——数据×模型×多样性的定量关系。它的 tracker 更强（尤其零样本精度），但只是个"更好的执行器"，还没有接到任何高层模块上。

**一个自然的推论**：这两篇是互补而非互斥的——把 Humanoid-GPT 的 causal Transformer tracker 塞进 SONIC 的 universal token space 接口，才是完整故事。Humanoid-GPT 结尾的 future work（"coupling with VLA-style instruction"）等于承认了这一点。

### 对 Humanoid-GPT 的两点保留

1. **对 SONIC 的"MLP 饱和"指控证据是间接的**：Tab.2 对比的是自己训的 3 层 MLP/TCN baseline，不是 SONIC 本身（SONIC 的 42M MLP + 单阶段 RL 范式没有被复现对比）。SONIC 自己的 scaling 曲线（其 Fig. 显示 42M 仍在涨）与"饱和"结论并不完全一致——饱和点在哪里，两篇论文各说各话。
2. **2B 帧的口径**：×5 时间增广算进总帧数，和 SONIC 的 700h 纯 mocap 不是同一口径；"200× 更大"的宣传要打折扣读。

---

## 与 VLA / Embodied AI 的联系

- **和 π₀ 的结构呼应**：π₀ 用 VLM backbone + action expert 处理"语义→动作块"；Humanoid-GPT 是纯低层，但它证明了**动作控制这一层本身也服从 scaling law**——这为"VLA 的 action expert 也该 scale"提供了旁证。它的 token 设计（proprio ⊕ reference pose 逐帧成 token，causal attention，一次前向监督整段历史）和 π₀ 的 block-wise causal attention 是同一思想在不同层的应用。
- **分工图景越来越清晰**：VLA（语义、任务理解，~秒级）→ 动作/轨迹接口（SONIC 的 token space 或参考姿态）→ 大规模预训练 tracker（Humanoid-GPT/SONIC，50Hz）。这三层正在各自独立地被 scale。
- **蒸馏范式值得记住**：RL 专家 → Transformer 学生的 DAgger 并行蒸馏，本质是"把 RL 的探索成本一次性付清，换成监督学习的可扩展性"。这与 LLM 领域"RLHF 教师 → SFT 蒸馏"的降本逻辑同构，未来 VLA 的动作模块很可能也走这条路。

---

## 快速自测

1. Humanoid-GPT 为什么坚持 **causal** attention 而不是双向？（在线控制看不到未来观测；causal 与部署约束对齐，且不同位置历史长度不同带来位置不变性）
2. HME 解决什么问题？（长尾：常见动作淹没稀有动作；用周期特征嵌入做聚类 + 均衡采样，"多样性和均衡都必要"）
3. 它和 SONIC 最本质的分歧是什么？（架构是否需要随数据一起 scale：SONIC 押 MLP+单阶段 RL 够用、重点在接口；Humanoid-GPT 押 MLP 会饱和、必须换 Transformer+蒸馏）
4. 为什么不用一个大 PPO 直接训 Transformer？（RL 信号稀疏且不稳定，难以直接训大模型；先用小专家把 RL 啃下来，再用 DAgger 把监督并行化——HumanPlus 用 PPO 训 Transformer 正是反例）
