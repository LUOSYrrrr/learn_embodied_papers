# Canonical Keywords Library

这份词库用于后续人工筛选与收敛。

原则：

- 只收录在具身智能、机器人学习、机器人控制中具有方法共性、任务共性或系统共性的关键词。
- 尽量避免纯实验资源词、纯背景词、纯修饰词。
- 同义词后续统一到一个 canonical label。
- 后续每篇论文优先从这份词库中选 `3-5` 个关键词。

---

## 1. Contribution Theme

每篇论文先选一个主题标签。

- `model architecture`（论文的主要贡献是提出新的模型结构、模块组织方式或表示架构，而不是主要改进训练流程或硬件系统。）
- `training algorithm`（论文的主要贡献是提出新的训练目标、优化流程、学习范式或训练阶段设计。）
- `inference / test-time method`（论文的主要贡献是改进测试时的决策、推理、规划、检索、记忆调用或闭环执行机制。）
- `benchmark`（论文的主要贡献是提出新的评测任务集、评测协议、基准环境或系统化评估框架。）
- `dataset`（论文的主要贡献是提出新的数据集、数据采集流程或数据标注/构建体系。）
- `control method`（论文的主要贡献是提出控制器、控制律、状态估计、轨迹优化、动力学建模或安全约束方法。）
- `hardware system`（论文的主要贡献是提出机械结构、末端执行器、传感器、遥操作接口或机器人平台。）
- `survey / review`（论文的主要贡献是综述、分类、梳理现有研究，而不是提出新的核心技术方法。）

---

## 2. Model Family

- `VLA`（Vision-Language-Action model；输入视觉观测与语言指令，直接输出动作或动作 token 的模型家族。）
- `world model`（显式学习环境状态转移、未来观测或潜在动力学的模型，用于预测、规划或策略学习。）
- `world action model`（同时建模环境演化与动作生成的统一模型，强调世界建模与动作决策的耦合。）
- `VA`（Video-Action model；主要从视频观测映射到动作，不一定显式建模语言。）
- `diffusion policy`（用扩散生成过程建模动作分布或动作序列的策略模型。）
- `latent action / dynamics model`（在潜在空间中建模动作表示或动力学演化，而不是直接在原始动作空间操作。）
- `tokenizer`（将动作、状态、视觉片段或轨迹离散化/压缩为 token 以便序列建模的模块或方法。）
- `other model`（不属于上述主流范式，但核心贡献仍明确是新模型结构。）

---

## 3. Learning Paradigm

- `imitation learning`（通过专家演示学习策略，核心是从 demonstration 到 policy 的映射学习。）
- `reinforcement learning`（通过最大化累计回报学习策略，核心是 reward-driven policy improvement。）
- `pretraining`（先在大规模通用数据上学习表征或策略，再迁移到下游机器人任务。）
- `post-training`（在已有基础模型上进行后续强化、对齐或任务化训练，而不是从头训练。）
- `co-training`（联合使用多种来源、模态或任务的数据进行共同训练，使不同监督信号相互促进。）
- `inverse reinforcement learning`（从专家行为反推潜在 reward 或偏好结构，再据此学习策略。）
- `skill learning`（学习可复用、可组合的技能单元、option 或技能表示，而非单一任务策略。）

---

## 4. Reasoning and Decision-Making

- `reasoning`（模型在动作输出前显式或隐式进行中间推理，而不是纯直接映射。）
- `planning`（模型在时间上前瞻多个动作或子目标，以优化长期任务完成效果。）
- `model predictive control`（基于动力学模型滚动优化未来有限时域动作，并在每一步重规划。）
- `test-time`（在推理阶段动态调整行为，如在线检索、适应、再规划或自校正。）
- `chain-of-thought`（以中间推理链或显式步骤序列辅助最终决策的机制。）
- `autoregressive decoding`（按时间步或 token 顺序逐步生成动作、轨迹或中间表示的解码方式。）
- `action chunking`（将长动作序列切成短块进行预测或执行，以提高效率和稳定性。）

---

## 5. Perception and Representation

- `3D`（核心方法显式利用三维几何、三维结构或空间表征，而不只是二维图像。）
- `point cloud`（以点云作为主要几何输入或中间表示，用于感知、规划或控制。）
- `multi-view`（利用多个视角的观测联合推理场景、物体或动作。）
- `object tracking`（连续估计目标物体随时间的位置、姿态或身份。）
- `object detection`（识别并定位图像或场景中的目标物体。）
- `neural rendering`（用可学习的渲染模型表示和生成场景外观或视角变化。）
- `Gaussian splatting`（用高斯基元显式表示三维场景，以进行高效渲染或几何建模。）

---

## 6. Manipulation Setting

- `dexterous hand`（论文聚焦多指灵巧手系统或高自由度手部操作。）
- `mobile manipulation`（同时涉及底盘移动与机械臂/末端执行器操作的任务设置。）
- `loco-manipulation`（机器人一边运动一边操作，行走/移动与操作耦合。）
- `whole-body control`（控制机器人全身多个关节或肢体协同完成动作，而非单臂局部控制。）

---

## 7. Data and Demonstration Regime

- `real robot data`（来自真实机器人执行过程的传感器、动作或轨迹数据。）
- `human data`（来自人类演示、人类动作、人类视频或人类标注的数据。）
- `egocentric video`（第一人称视角视频数据，常用于学习人类操作先验。）
- `synthetic data`（由仿真、渲染或程序生成得到的数据，而非真实采集。）
- `web data`（来自互联网图文或视频资源的数据，用于补充视觉语义或通识知识。）
- `dataset`（核心贡献是提出新的数据资源时使用；若只是使用数据集做实验，则不应默认打该标签。）
- `benchmark`（核心贡献是提出新的评测基准时使用；若只是用 benchmark 做实验，则不应默认打该标签。）
- `simulation`（核心贡献是提出新的仿真环境或者优化仿真环境评测或建模；若只是普通实验环境，则不应默认打该标签。）

---

## 8. Embodiment and Transfer

- `sim-to-real`（方法核心关注从仿真训练迁移到真实机器人执行。）
- `real-to-sim`（从真实数据反哺仿真建模、重建或校准，以提升后续学习与评测。）
- `cross-embodiment`（方法核心关注跨机器人形态、自由度或平台的迁移与共享。）
- `zero-shot generalization`（不经过目标任务再训练，直接泛化到新任务、新物体或新环境。）
- `open-world generalization`（在开放环境中面对未见对象、指令、场景或扰动时保持可用。）
- `sample efficiency`（用更少真实交互、演示或训练样本达到给定性能。）
- `real-time control`（模型或控制器满足在线执行时延约束，能够实时闭环运行。）

---

## 9. Hardware and Interface

- `gripper-design`（主要贡献是末端夹爪、手爪或抓取机构设计。）
- `dexterous hand`（主要贡献是多指灵巧手硬件系统、结构设计或手部执行平台。）
- `teleoperation`（通过人机接口远程操控机器人，并常用于数据采集或共享控制。）
- `tactile`（核心依赖触觉观测、触觉传感或触觉表征进行感知与决策。）
- `force`（核心依赖力/力矩测量、估计或调节，而不只是普通位置控制。）
- `soft robotics`（采用柔性、顺应性材料或软体结构实现机器人机构与交互。）
- `human-robot interaction`（研究机器人与人的协作、交互、沟通或共同任务执行。）

---

## 10. Control Method Family

这一层用于 `control method` 主题下的进一步分类。

优先保留控制理论中具有共性的“问题类型”和“方法家族”，不优先保留过细的工程实现词。

- `feedback control`（根据当前或估计状态实时修正控制输入的闭环控制方法总类。）
- `impedance control`（通过规定位置/速度误差与力响应之间的等效阻抗关系实现顺应交互。）
- `admittance control`（根据外力输入调节期望运动响应，本质上实现力到运动的动态映射。）
- `force control`（直接将接触力/力矩作为主要控制目标进行调节的控制方法。）
- `visual servoing`（利用视觉反馈闭环控制机器人运动，使视觉误差收敛到目标值。）
- `optimal control`（通过优化代价函数求解状态和控制序列，以获得最优控制策略。）
- `model predictive control`（利用系统模型在有限预测时域内反复求解优化问题并滚动执行。）
- `trajectory optimization`（直接优化整条状态/动作轨迹，使其满足动力学与约束并优化目标函数。）
- `adaptive control`（在线调整控制器参数以应对系统参数不确定性或环境变化。）
- `robust control`（在模型误差、外部扰动和不确定性存在时仍保证性能或稳定性的控制方法。）
- `safe control`（显式考虑安全约束、碰撞风险或稳定边界，保证系统不进入危险区域。）
- `Lyapunov-based control`（基于 Lyapunov 函数构造控制律，以证明或保证系统稳定性。）
- `control barrier function`（通过障碍函数约束系统状态保持在安全集合内的安全控制方法。）
- `system identification`（从观测数据估计系统动力学模型或参数的过程。）
- `dynamics modeling`（显式建立系统状态转移、接触动力学或环境演化模型。）
- `state estimation`（从不完全或有噪声观测中估计系统潜在状态。）
- `calibration`（校正传感器、相机、机械结构或坐标系参数以减少系统误差。）
- `motion planning`（在几何和动力学约束下规划一条可执行的运动路径或轨迹。）
- `task and motion planning`（联合高层任务决策与低层几何运动规划的分层规划框架。）
- `contact-rich manipulation`（以频繁接触、摩擦、插入、推挤、装配等复杂接触为核心难点的操作场景。）
- `whole-body control`（对机器人全身自由度统一建模和协调控制，以满足多任务与约束。）