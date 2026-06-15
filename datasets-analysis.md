# MotionWAM 数据集分析

> **背景**：MotionWAM 使用 2,136 小时 egocentric 视频进行 Stage 1 视频预训练（动作标签忽略），
> 旨在学习动作感知的视觉表征。数据集分三大类：Human 30%、G1 类人形机器人 50%、Other Real Robots 20%。

---

![image-20260614150434535](/Users/siyuanluo/STUDY/paper/learn_embodied_papers/assets/image-20260614150434535.png)

## 一、Human 类（~30%，~641h）

### 1. EgoDex
**Apple Research, ICLR 2026 | arXiv:2505.11709**

| 属性 | 详情 |
|------|------|
| **规模** | **829h**，338K episode，90M 帧，194 tasks，500+ objects |
| **存储** | 2 TB左右 |
| **采集设备** | Apple Vision Pro（头戴式，第一人称） |
| **分辨率/频率** | 1080p，**30 FPS** |
| **本体** | 人类双手（非机器人） |
| **任务类型** | 日常灵巧操作（厨房/工具/家务），全为 in-the-wild |
| **骨骼标注** | 完整**上半身运动链** 3D 位姿（30 Hz）：camera（6-DoF）+ neck×4 + spine×7 + shoulders×2 + arms×2 + forearms×2 + **每手 25 关节** |
| **语言标注** | GPT-4 清洗后的任务描述 |
| **置信度** | 每关节逐帧 ARKit 遮挡置信值（0-1） |
| **格式** | MP4（1080p 30fps）+ **HDF5**（骨骼 SE(3) 位姿 N×4×4） |
| **开源** | https://github.com/apple/ml-egodex |
| **MotionWAM 用途** | **Stage 1 only**（权重 30%）：纯视频预训练，所有骨骼标注强制忽略 |

![image-20260614151758526](/Users/siyuanluo/STUDY/paper/learn_embodied_papers/assets/image-20260614151758526.png)

> 上图：EgoDex 完整上半身骨骼结构（ARKit 标注）。注意 spine1–7 / neck1–4 全部有 3D 位姿，不只是手部。

![image-20260614151707728](/Users/siyuanluo/STUDY/paper/learn_embodied_papers/assets/image-20260614151707728.png)

> 上图：EgoDex 灵巧操作行为示例（3×3 九宫格）。任务包括拉 Ziploc 袋、从书架取书、拧螺丝、折叠 T 恤、整理杂物、打开箱子、拧瓶盖、系鞋带、清洗杯子。

#### 数据格式详解：HDF5 + MP4 配对

> **HDF5 **  
> HDF5（Hierarchical Data Format version 5）是一种**层级化二进制数据格式**，类似于"文件系统嵌在一个文件里"——可以在单个 `.hdf5` 文件内存储多维数组（如 N×4×4 变换矩阵）、元数据（语言标注）和分组（按关节名分文件夹）。特点：随机访问快（不需要读完整文件就能取第 k 帧）、支持压缩、PyTorch/NumPy 原生支持（`h5py` 库）。

EgoDex 每条 episode 由一个 `.mp4` + 一个 `.hdf5` 组成，帧级对齐（N = 30 × T 秒）：

```
part1/
└── task_name/
    ├── 0.mp4          # 原始 1080p 视频（T 秒）
    ├── 0.hdf5         # 骨骼标注（N = 30×T 帧）
    ├── 1.mp4
    ├── 1.hdf5
    ...

0.hdf5 内部结构：
├── camera/
│   └── intrinsic          # 3×3 相机内参（每文件固定不变）
├── transforms/            # 所有关节的 SE(3) 变换矩阵，shape [N, 4, 4]
│   ├── camera             # 头部位姿（=相机外参，ARKit 世界坐标系）
│   ├── leftHand / rightHand
│   ├── leftIndexFingerTip / leftIndexFingerKnuckle
│   ├── leftMiddleFingerTip / ...（共 68 个关节）
│   └── ...
└── confidences/           # 可选，每关节标量置信度 [N]
    ├── leftHand / rightHand
    └── ...（共 68 个关节）

# 语言标注在 HDF5 属性里，Python 读取：
f.attrs['llm_description']   # 任务描述
f.attrs['llm_description2']  # 可逆任务的反向描述（如"插上充电器"和"拔掉充电器"）
f.attrs['which_llm_description']  # 1 或 2，指示当前 episode 用哪条描述
```

**坐标系说明**：所有 `transforms` 均在 **ARKit origin frame** 下表达（录制开始时设定的地面固定坐标系）。同一 session 内帧间一致，但**跨 episode 不保证一致**（设备重新初始化时原点会漂移）。

**EgoDex 定义的 Action 表示**（用于其 benchmark，非 MotionWAM 使用的格式）：  
每时刻动作 = 2 只手 × (腕部 3D 位置 + 腕部 6D 朝向 + 5 指尖 3D 位置) = **48 维**。  
注意：EgoDex 自己的 benchmark 只用这 48 维，而完整 HDF5 里有 68 个关节的完整 SE(3) 位姿。

**MotionWAM 怎么用 EgoDex**：

**只有 Stage 1 使用 EgoDex，Stage 2/3 完全不用。**

Stage 1 的 Video DiT 做的事是：给定当前帧 + 语言，预测下一帧（flow-matching）：

$$\mathcal{L}_{\text{video}} = \mathbb{E}\left[\left\| v_\theta(z_{t+1}^{\tau_v}, \tau_v \mid z_t^0,\, l) - (\epsilon_v - z_{t+1}^0) \right\|^2\right]$$

从 EgoDex 实际读取的内容：

| 读取 | 来源 | 用途 |
|------|------|------|
| ✅ 视频帧 $z_t^0$ | `.mp4` | 当前帧 condition |
| ✅ 下一帧（加噪） $z_{t+1}^{\tau_v}$ | `.mp4` | 待去噪目标 |
| ✅ 语言描述 $l$ | `f.attrs['llm_description']`（HDF5 属性） | 语言 condition |
| ❌ 骨骼 `transforms/`（68 关节 SE(3)） | HDF5 | **完全不读** |
| ❌ 置信度 `confidences/` | HDF5 | **完全不读** |
| ❌ 相机内参 `camera/intrinsic` | HDF5 | **完全不读** |

注意：语言标注虽然存在 HDF5 属性里，但读取成本极低（不需要加载骨骼数组）。HDF5 文件中真正昂贵的部分（N×4×4 的关节变换矩阵）在 Stage 1 训练时从未被打开。

Stage 2 不用 EgoDex 的原因：Stage 2 需要机器人关节命令作为监督（29-DoF G1 动作），EgoDex 只有人类上半身骨骼，无法直接 retarget，因此被排除在外。

**亮点**：

- **被动可扩展**：用户正常佩戴 AVP 操作即可积累数据，边际成本极低
- **标注最完整**：完整上半身运动链（camera + spine + 手部 25 关节），比 EgoMimic 只有腕部位置丰富得多
- **规模最大**：829h，是 EgoMimic 的 200×

**局限**：
- 纯人类数据，无机器人动作标签（但这正是它能被 Stage 1 大量使用的原因）
- 跨 episode 坐标系不统一（ARKit 初始化漂移），无法直接做轨迹跨 episode 对齐

  

---

## 二、G1 类人形机器人（~50%，~1,068h）

### 2. GR00T-X-Embodiment-Sim（仿真生成）
**NVIDIA, arXiv:2503.14734**

| 属性 | 详情 |
|------|------|
| **采集方式** | Isaac Lab 仿真 + DexMimicGen 自动扩增 |
| **动作标注** | 仿真 GT 动作（joint positions + EEF poses） |
| **语言标注** | 自动生成任务描述 |
| **格式** | LeRobot 兼容，HDF5 |
| **开源** | https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-GR00T-X-Embodiment-Sim |
| **MotionWAM 用途** | 主力仿真预训练数据（权重 25.5%） |

**数据集实际结构（HuggingFace 页面）**

| 子集 | 本体 | 轨迹数 | 任务数 | MotionWAM 使用？ |
|------|------|--------|--------|-----------------|
| **Humanoid robot tabletop manipulation** | Fourier GR1（gr1_arms_waist）| **240k** | 24 | ✅ **主力** |
| Humanoid robot tabletop manipulation - downsampled | Fourier GR1（gr1_unified）| 24k | 24 | ❌（是 240k 的 10% 子集，调试用）|
| Cross-embodied bimanual manipulation | Panda 双臂 + GR1 变体 | 9k | 9 | 未知 |
| Robot Arm Kitchen Manipulation | Panda 单臂（非人形）| 72k | 24 | ❌（非人形，与 G1 形态不符）|
| Unitree G1 Loco-Manipulation | **Unitree G1**（真实目标本体）| **102** | 1 | 未知 |

**关键澄清**：
- HuggingFace 上总计约 **321k 唯一轨迹**（240k+9k+72k+102，下采样版不算）
- MotionWAM 重点用的可能是 **Humanoid 240k**（24 个 pick-and-place 任务，每任务 10k 条）
- Panda 单臂的 72k 轨迹对 G1 全身人形意义有限，MotionWAM 可能未使用

**240k 子集任务结构（`gr1_arms_waist.*`，每任务 10,000 条）**

全部是 **pick-from-A-to-B** 框架，24 种 source × target 组合：

```
CanToDrawer / CupToDrawer / CuttingboardToBasket / CuttingboardToCardboardBox
CuttingboardToPan / CuttingboardToPot / CuttingboardToTieredBasket
PlaceBottleToCabinet / PlaceMilkToMicrowave / PlacematToBasket
PlacematToBowl / PlacematToPlate / PlacematToTieredShelf
PlateToBowl / PlateToCardboardBox / PlateToPan / PlateToPlate
PotatoToMicrowave / TrayToCardboardBox / TrayToPlate
TrayToPot / TrayToTieredBasket / TrayToTieredShelf / WineToCabinet
```

**MotionWAM 怎么用 GR00T-Sim**：

- **Stage 1**：读视频帧，忽略动作标签，Video DiT 学习 GR1 机器人视角的视觉动力学先验
- **Stage 2**（参与）：240k 轨迹是 Stage 2 最大体量的有标签数据源，提供 Fourier GR1 本体（gr1_arms_waist = 上肢+腰部）的仿真动作分布，驱动 Motion DiT trunk 学习跨任务的机器人手臂运动表示
- sim-to-real gap 由 Stage 3 的少量真实遥操作数据弥补

**亮点**：
- **规模大**：240k 轨迹，24 种 pick-place 组合，任务覆盖广
- **动作标签完整**：仿真直接记录 GT 关节轨迹，无需 retargeting
- **DexMimicGen 扩增**：少量人工 demo → 自动生成 10k 变体/任务

**局限**：
- sim-to-real gap 明显（纹理、物理、接触）
- 全部是桌面 pick-place，无 locomotion，任务多样性低
- GR1 本体（傅利叶智能）≠ Unitree G1，动作空间需 per-embodiment projector 对齐

---

### 3. RoboCOIN


| 属性 | 详情 |
|------|------|
| **规模** | **180K+ 轨迹**，421 tasks，16 scenarios |
| **本体** | **15 种本体**（双臂 / 半人形 / 全人形）：G1edu, Galbot, Leju RMC, R1 Lite, RMC-AIDA-L 等 |
| **采集方式** | 遥操作（CoRobot 采集流水线，基于 LeRobot） |
| **任务标注层级** | 轨迹级 / 片段级 / 帧级三层标注（Capability Pyramid） |
| **语言标注** | 自然语言指令 |
| **格式** | **LeRobot 格式**（Parquet + video MP4），统一动作空间 |
| **开源** | https://flagopen.github.io/RoboCOIN-DataManager/ |

#### MotionWAM 对 RoboCOIN 的拆分使用

RoboCOIN 在 MotionWAM 的 Table 5 里被**拆成两个条目**，分属不同 domain：

| Table 5 条目 | 本体子集 | Domain | 权重 |
|-------------|---------|--------|------|
| `RoboCOIN (G1edu/Galbot/Leju)` | 人形机器人子集 | **G1-class humanoid（50%域内）** | **0.080** |
| `RoboCOIN (R1 Lite + RMC-AIDA-L)` | 非人形机械臂子集 | **Other real robots（20%域内）** | **0.200** |

筛选(G1edu/Galbot/Leju)显示有1.2tb

![image-20260615093332313](/Users/siyuanluo/STUDY/paper/learn_embodied_papers/assets/image-20260615093332313.png)

---

### 4. GR00T-Teleop-GR1（真实遥操作）
**NVIDIA, HuggingFace**

| 属性 | 详情 |
|------|------|
| **规模** | **88h 真实遥操作** |
| **本体** | Fourier GR-1 真实人形机器人 |
| **采集设备** | VIVE Ultimate Tracker（手腕） + Xsens Metagloves（手指）|
| **频率** | **20Hz** 控制，RGB + 本体感知 |
| **标注层级** | 细粒度（grasping/moving/placing）+ 粗粒度任务级 |
| **语言标注** | 是的 |
| **格式** | HDF5，joint positions + EEF poses |
| **开源** | https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-GR00T-Teleop-GR1 |
| **MotionWAM 用途** | 真实 G1 本体预训练（7.1%），质量最高的 real-world 数据 |

**MotionWAM 用 GR00T-Teleop**：  

- **Stage 1**（权重 7.1%）：视频帧训练 Video DiT  
- **Stage 2**（参与）：**真实动作锚点**——VIVE tracker + Metagloves 采集的精密动作，让 Motion DiT 学到高精度 Fourier GR1 本体的真实动作分布

**亮点**：
- **质量最高**：精密 MoCap 设备 + IK retargeting，动作精度高
- **层级标注**：同时支持底层运动学习和高层任务规划
- **NVIDIA GR00T N1 训练核心**：作为 data pyramid 顶层

**局限**：
- 规模相对小（88h），人工成本高
- 场景集中于桌面操作，locomotion 覆盖有限

---

### 5. Humanoid-Everyday
**USC PSI-Lab + Toyota Research Institute, arXiv:2510.08807**

| 属性 | 详情 |
|------|------|
| **规模** | ~500 GB (across 250 tasks), over 100,000 time-step recorded |
| **本体** | Unitree **G1**（29-DoF, Dex3-1 手）+ **H1**（27-DoF, INSPIRE 手）|
| **采集设备** | Apple Vision Pro（手腕/手指 keypoints）+ IK |
| **频率** | **30 Hz** |
| **感知模态** | 9 种：RGB / 深度 / LiDAR / 触觉 / IMU / 关节状态 / 人类动作 / EEF |
| **任务类别** | 260 diverse scenarios (loco-manipulation, basic manipulation, tool use, deformables, articulated objects, human–robot interaction) |
| **语言标注** | 自然语言任务描述 |
| **格式** | 自定义多模态包（RGB+Depth+LiDAR+Tactile 同步）|
| **说明网站** | https://humanoideveryday.github.io |
| **开源** | https://huggingface.co/datasets/USC-PSI-Lab/humanoid-everyday |
| **MotionWAM 用途** | Unitree G1 预训练（4.7%），最接近 MotionWAM 目标本体 |

task summary 表格：https://docs.google.com/spreadsheets/d/158Wzf8Xywky3aHJSCfp3OZxf4bkhzAJdcG94eHf8gVc/edit?gid=1307250382#gid=1307250382



**Full Dataset Link:** https://www.dropbox.com/scl/fo/r6xwxxuiwmnypzprzqza7/ANRXMBbSz0b33q9ohX5PCrY?rlkey=42llsh52wfq47r77m05mkikus&st=kk7a20xl&dl=0

**MotionWAM 怎么用 Humanoid-Everyday**：  

- **Stage 1**（权重 4.7%）：视频帧训练 Video DiT  
- **Stage 2**（参与）：**接近 MotionWAM 目标本体（Unitree G1）的开源真实数据**，直接提供 29-DoF G1 的动作分布；9 种模态中 Stage 2 只用 RGB + 关节状态

**亮点**：
- **模态最丰富**：9 种传感器同步，业界最全面的人形数据集之一
- **含 Loco-Manip**：少数包含移动操作（locomotion + manipulation）的数据集
- **云评估**：提供标准化在线评测平台，支持跨机构公平比较
- **两种 DoF 配置**：G1（29-DoF）和 H1（27-DoF）覆盖不同手部设计

**局限**：

- 10.3K 轨迹对 260 任务来说平均每任务约 40 轨迹，密度略低
- 多模态存储开销大，pipeline 复杂

![image-20260615093703029](/Users/siyuanluo/STUDY/paper/learn_embodied_papers/assets/image-20260615093703029.png)

---

### 6. UnifoLM-WBT（全身遥操作）
**Unitree Robotics, HuggingFace Collection**

| 属性 | 详情 |
|------|------|
| **规模** | 170g左右，14个huggingface库一共 |
| **本体** | Unitree **G1** （whole-body） |
| **采集方式** | 全身遥操作（WBT = Whole-Body Teleoperation） |
| **频率** | **50 Hz**（高频控制，MotionWAM Stage 3 标准） |
| **动作空间** | **29-DoF**，SMPL-24 骨骼对齐 |
| **格式** | **LeRobot 格式**，与 MotionWAM Stage 2/3 直接兼容 |
| **开源** | https://huggingface.co/collections/unitreerobotics/unifolm-wbt-dataset |
| **MotionWAM 用途** | 宇树 G1 WBT 预训练（2.3%），**格式与 Stage 3 完全一致** |

![image-20260615094301817](/Users/siyuanluo/STUDY/paper/learn_embodied_papers/assets/image-20260615094301817.png)

**MotionWAM 怎么用 UnifoLM-WBT**：  

- **Stage 1**（权重 2.3%）：视频帧训练 Video DiT，此数据集的全身运动视频正是 Stage 1 需要的"机器人第一人称全身运动视觉先验"  
- **Stage 2**（参与）：**格式兼容**——LeRobot 格式 + 50Hz + 29-DoF 与 MotionWAM Stage 3 标准完全一致，无需格式转换；提供全身协调运动（行走+操作）的动作分布，是 Stage 2 中极少数包含 locomotion 的数据

**亮点**：

- **格式零迁移成本**：官方 LeRobot 格式，50Hz，29-DoF，与 MotionWAM 完全匹配
- **全身运动**：覆盖腰部旋转、腿部步态、手臂协同，Stage 1/2 中唯一强调全身的开源数据集
- 与硬件深度绑定，action retargeting 误差最小

**局限**：
- 公开规模较小（2.3%），内部数据占比更高
- 任务多样性相对有限

---

## 三、Other Real Robots（~20%）

**MotionWAM Table 5 中明确标注的唯一来源：`RoboCOIN (R1 Lite + RMC-AIDA-L)`，权重 0.200。**

这个 domain 里没有其他数据集，大概700多g

| 条目 | 本体 | 权重 | 说明 |
|------|------|------|------|
| RoboCOIN (R1 Lite + RMC-AIDA-L) | 非人形机械臂 | **0.200** | RoboCOIN 数据集中的非人形子集，与 §3 的人形子集同一数据源但不同本体 |

R1 Lite 和 RMC-AIDA-L 是 RoboCOIN 数据集里的非人形机械臂配置，形态上更接近桌面操作臂而非全身人形机器人。把它们单独归入"other real robots" domain，是为了在 Stage 1 视频预训练时引入更多样的视觉动力学先验，同时在 Stage 2 中通过 per-embodiment projector 接入不同动作空间。

![image-20260615094400233](/Users/siyuanluo/STUDY/paper/learn_embodied_papers/assets/image-20260615094400233.png)

